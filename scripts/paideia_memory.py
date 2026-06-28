#!/usr/bin/env python3
"""Create portable five-layer project memory from LLM conversations."""

from __future__ import annotations

import argparse
import base64
import fnmatch
import getpass
import hashlib
import io
import json
import os
import re
import shutil
import sys
import unicodedata
import zipfile
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


ROLE_RE = re.compile(
    r"^\s*(?:#{1,6}\s*)?"
    r"(system|developer|assistant|user|human|ai|llm|"
    r"사용자|보스|창조주|줄리아|코덱스|어시스턴트|모델)\s*[:：]\s*(.*)$",
    re.IGNORECASE,
)
TOKEN_RE = re.compile(r"[a-z0-9_./:-]+|[가-힣]{2,}", re.IGNORECASE)
SENTENCE_RE = re.compile(r"(?<=[.!?。！？])\s+|\n+")
CORE_FILE_NAMES = [
    "01_raw_conversation.md",
    "02_major_outline.md",
    "03_minor_outline.md",
    "04_summary.md",
    "05_patterns.md",
]
PROJECT_INDEX_FILES = {
    "_project_index.md",
    "_timeline.md",
    "_pattern_registry.md",
    "_pattern_review.md",
}
PATTERN_OVERRIDES_FILE = "_pattern_overrides.json"
PATTERN_REVIEW_FILE = "_pattern_review.md"
SCAN_TARGET_SUFFIXES = {
    ".cfg",
    ".ini",
    ".json",
    ".jsonl",
    ".md",
    ".py",
    ".toml",
    ".txt",
    ".yaml",
    ".yml",
}
MOJIBAKE_MARKERS = ("\ufffd", "??", "媛", "蹂", "以", "吏", "諛", "怨", "瑜")
SECRET_PATTERNS = [
    ("openai_api_key", re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9_-]{20,}\b")),
    ("anthropic_api_key", re.compile(r"\bsk-ant-[A-Za-z0-9_-]{20,}\b")),
    ("google_api_key", re.compile(r"\bAIza[0-9A-Za-z_-]{20,}\b")),
    ("aws_access_key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("github_token", re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{30,}\b")),
    ("slack_token", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{20,}\b")),
    ("private_key", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
]


CATEGORY_DEFS = [
    (
        "north_star",
        "프로젝트의 북극성",
        [
            "개발",
            "프로젝트",
            "왜",
            "필요",
            "방향",
            "지향",
            "철학",
            "사용자 입장",
            "continuity",
            "project",
        ],
    ),
    (
        "requirements",
        "명시 요구사항",
        [
            "해야",
            "원한다",
            "저장",
            "구분",
            "대제목",
            "소제목",
            "요약",
            "패턴",
            "검색",
            "must",
            "should",
            "require",
        ],
    ),
    (
        "small_details",
        "작은 차이를 보존해야 하는 이유",
        [
            "누락",
            "빠지는",
            "작은",
            "큰 차이",
            "개성",
            "중요",
            "곁가지",
            "차이점",
            "detail",
        ],
    ),
    (
        "continuity",
        "연속성과 이식성",
        [
            "계속",
            "이어",
            "기존",
            "과거",
            "맥락",
            "다른 llm",
            "저장방법",
            "불편",
            "portable",
            "vendor",
        ],
    ),
    (
        "retrieval",
        "역추적과 검색",
        [
            "찾아보기",
            "역으로",
            "검색",
            "원본",
            "요약본",
            "패턴",
            "retrieve",
            "search",
        ],
    ),
    (
        "learning",
        "패턴 학습과 정교화",
        [
            "패턴화",
            "맞춤형",
            "강화학습",
            "발전",
            "정교",
            "사용자의",
            "개성",
            "방식",
            "learning",
            "feedback",
        ],
    ),
    (
        "privacy",
        "보안과 소유권",
        [
            "보안",
            "고유재산",
            "개인",
            "로컬",
            "비공개",
            "privacy",
            "security",
            "owner",
        ],
    ),
    (
        "verification",
        "검증과 오류 처리",
        [
            "검증",
            "오류",
            "실수",
            "숨기지",
            "바로잡",
            "장치",
            "수단",
            "test",
            "verify",
        ],
    ),
]


@dataclass
class Message:
    role: str
    content: str
    index: int
    line_start: int
    line_end: int


@dataclass
class Evidence:
    message_index: int
    role: str
    line_start: int
    line_end: int
    text: str
    score: int


@dataclass
class SecretFinding:
    kind: str
    line_number: int
    excerpt: str


def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def configure_stdio() -> None:
    for stream_name in ("stdout", "stderr"):
        stream = getattr(sys, stream_name, None)
        if hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8", errors="replace")
            except Exception:
                pass


def slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value.strip().lower())
    safe = re.sub(r"[^\w가-힣.-]+", "-", normalized, flags=re.UNICODE).strip("-._")
    return safe or "project"


def decode_bytes(data: bytes) -> str:
    for encoding in ("utf-8-sig", "utf-8", "cp949"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")


def read_text(path: Path) -> str:
    return decode_bytes(path.read_bytes())


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def normalize_for_match(value: str) -> str:
    return unicodedata.normalize("NFKC", value).casefold()


def contains_mojibake(text: str) -> bool:
    if "\ufffd" in text:
        return True
    marker_hits = sum(text.count(marker) for marker in MOJIBAKE_MARKERS if marker != "??")
    question_runs = len(re.findall(r"\?{3,}", text))
    korean_chars = len(re.findall(r"[가-힣]", text))
    return (marker_hits + question_runs >= 5) and korean_chars == 0


def mask_secret(value: str) -> str:
    compact = value.strip()
    if len(compact) <= 12:
        return "[redacted]"
    return compact[:4] + "..." + compact[-4:]


def redact_secrets(text: str) -> str:
    redacted = text
    for _, pattern in SECRET_PATTERNS:
        redacted = pattern.sub(lambda match: mask_secret(match.group(0)), redacted)
    return redacted


def scan_secrets(text: str) -> list[SecretFinding]:
    findings: list[SecretFinding] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        for kind, pattern in SECRET_PATTERNS:
            for match in pattern.finditer(line):
                excerpt = line[: match.start()] + mask_secret(match.group(0)) + line[match.end() :]
                findings.append(SecretFinding(kind=kind, line_number=line_number, excerpt=excerpt.strip()))
    return findings


def render_security_section(secret_findings: list[SecretFinding], mojibake_warning: bool) -> list[str]:
    lines = ["", "## Security and Integrity Notes"]
    if not secret_findings and not mojibake_warning:
        lines.append("- No high-confidence secret patterns or mojibake indicators were detected.")
        return lines
    if mojibake_warning:
        lines.append("- Possible mojibake was detected in the input. Verify the original export encoding before trusting summaries.")
    for finding in secret_findings[:10]:
        lines.append(f"- Secret-like pattern `{finding.kind}` detected near line {finding.line_number}: {finding.excerpt}")
    if len(secret_findings) > 10:
        lines.append(f"- {len(secret_findings) - 10} additional secret-like findings omitted from this summary.")
    return lines


def render_scan_report(secret_findings: list[SecretFinding], mojibake_warning: bool) -> str:
    lines = ["Security scan report"]
    if not secret_findings and not mojibake_warning:
        lines.append("- status: ok")
    if mojibake_warning:
        lines.append("- possible mojibake: verify source encoding")
    for finding in secret_findings:
        lines.append(f"- {finding.kind} line {finding.line_number}: {finding.excerpt}")
    return "\n".join(lines)


def normalize_role(role: str) -> str:
    role_key = role.strip().lower()
    if role_key in {"사용자", "보스", "창조주", "human", "sender", "customer", "client"}:
        return "user"
    if role_key in {"줄리아", "코덱스", "어시스턴트", "ai", "llm", "모델", "model", "bot", "bard", "gemini"}:
        return "assistant"
    if role_key in {"system", "developer"}:
        return role_key
    return role_key if role_key in {"user", "assistant"} else "unknown"


def content_to_text(content: Any) -> str:
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                parts.append(content_to_text(item.get("text") or item.get("content") or item.get("parts")))
        return "\n".join(part for part in parts if part)
    if isinstance(content, dict):
        if "parts" in content:
            return content_to_text(content["parts"])
        if "text" in content:
            return content_to_text(content["text"])
        if "content" in content:
            return content_to_text(content["content"])
        if "message" in content:
            return content_to_text(content["message"])
        if "body" in content:
            return content_to_text(content["body"])
        if "value" in content:
            return content_to_text(content["value"])
    return str(content)


def messages_from_json_obj(obj: Any) -> list[Message]:
    records: list[tuple[str, str]] = []

    def normalize_author(value: Any) -> str:
        if isinstance(value, dict):
            return str(value.get("role") or value.get("name") or value.get("type") or "unknown")
        return str(value or "unknown")

    def add_record(role: Any, content: Any) -> None:
        text = content_to_text(content).strip()
        if text:
            records.append((normalize_role(normalize_author(role)), text))

    def add_record_from_dict(item: dict[str, Any]) -> bool:
        role = item.get("role") or item.get("author") or item.get("sender") or item.get("from") or item.get("speaker")
        content = (
            item.get("content")
            or item.get("text")
            or item.get("message")
            or item.get("parts")
            or item.get("body")
            or item.get("utterance")
            or item.get("prompt")
            or item.get("response")
        )
        before = len(records)
        add_record(role, content)
        return len(records) > before

    def add_mapping_records(mapping: dict[str, Any]) -> bool:
        before = len(records)
        visited: set[str] = set()

        def sort_child(child_id: Any) -> tuple[float, str]:
            child = mapping.get(str(child_id), {})
            msg = child.get("message") if isinstance(child, dict) else None
            create_time = msg.get("create_time") if isinstance(msg, dict) else 0
            return (float(create_time or 0), str(child_id))

        def visit(node_id: str) -> None:
            if node_id in visited:
                return
            visited.add(node_id)
            node = mapping.get(node_id)
            if not isinstance(node, dict):
                return
            msg = node.get("message")
            if isinstance(msg, dict):
                author = msg.get("author") or {}
                role = author.get("role") if isinstance(author, dict) else author
                add_record(role, msg.get("content"))
            for child_id in sorted(node.get("children") or [], key=sort_child):
                visit(str(child_id))

        roots = [
            str(node_id)
            for node_id, node in mapping.items()
            if isinstance(node, dict) and not node.get("parent")
        ]
        for root_id in sorted(roots, key=sort_child):
            visit(root_id)

        if len(records) == before:
            sortable = []
            for node in mapping.values():
                if not isinstance(node, dict):
                    continue
                msg = node.get("message")
                if not isinstance(msg, dict):
                    continue
                sortable.append((msg.get("create_time") or 0, msg))
            for _, msg in sorted(sortable, key=lambda item: item[0] or 0):
                author = msg.get("author") or {}
                role = author.get("role") if isinstance(author, dict) else author
                add_record(role, msg.get("content"))
        return len(records) > before

    if isinstance(obj, list):
        for item in obj:
            if isinstance(item, dict):
                if not add_record_from_dict(item):
                    records.extend((m.role, m.content) for m in messages_from_json_obj(item))
        return [
            Message(role=role, content=text, index=i + 1, line_start=0, line_end=0)
            for i, (role, text) in enumerate(records)
        ]

    if not isinstance(obj, dict):
        return []

    if isinstance(obj.get("messages"), list):
        for item in obj["messages"]:
            if isinstance(item, dict):
                add_record_from_dict(item)

    elif isinstance(obj.get("chat_messages"), list):
        for item in obj["chat_messages"]:
            if isinstance(item, dict):
                add_record_from_dict(item)

    elif isinstance(obj.get("turns"), list):
        for item in obj["turns"]:
            if isinstance(item, dict):
                add_record_from_dict(item)

    elif isinstance(obj.get("mapping"), dict):
        add_mapping_records(obj["mapping"])

    elif isinstance(obj.get("conversations"), list):
        for conversation in obj["conversations"]:
            records.extend((m.role, m.content) for m in messages_from_json_obj(conversation))

    elif isinstance(obj.get("conversation"), (dict, list)):
        records.extend((m.role, m.content) for m in messages_from_json_obj(obj["conversation"]))

    return [
        Message(role=role, content=text, index=i + 1, line_start=0, line_end=0)
        for i, (role, text) in enumerate(records)
    ]


def parse_text_messages(raw: str) -> list[Message]:
    lines = raw.splitlines()
    messages: list[Message] = []
    current_role: str | None = None
    current_lines: list[str] = []
    current_start = 1

    def flush(end_line: int) -> None:
        nonlocal current_role, current_lines, current_start
        text = "\n".join(current_lines).strip()
        if text:
            messages.append(
                Message(
                    role=current_role or "unknown",
                    content=text,
                    index=len(messages) + 1,
                    line_start=current_start,
                    line_end=end_line,
                )
            )
        current_role = None
        current_lines = []

    for line_number, line in enumerate(lines, start=1):
        match = ROLE_RE.match(line)
        if match:
            if current_lines:
                flush(line_number - 1)
            current_role = normalize_role(match.group(1))
            current_start = line_number
            first_content = match.group(2).strip()
            current_lines = [first_content] if first_content else []
        else:
            if current_role is None and not current_lines:
                current_role = "unknown"
                current_start = line_number
            current_lines.append(line)

    if current_lines:
        flush(len(lines))

    if not messages and raw.strip():
        return [Message(role="unknown", content=raw.strip(), index=1, line_start=1, line_end=len(lines))]
    return messages


def parse_messages(path: Path, raw: str) -> list[Message]:
    if path.suffix.lower() in {".json", ".jsonl"}:
        try:
            if path.suffix.lower() == ".jsonl":
                records = [json.loads(line) for line in raw.splitlines() if line.strip()]
                messages = messages_from_json_obj(records)
            else:
                messages = messages_from_json_obj(json.loads(raw))
            if messages:
                return messages
        except json.JSONDecodeError as exc:
            raise SystemExit(f"Invalid JSON conversation export: {path}: {exc}") from exc
    return parse_text_messages(raw)


def split_sentences(text: str) -> list[str]:
    chunks: list[str] = []
    for part in SENTENCE_RE.split(text):
        stripped = re.sub(r"\s+", " ", part).strip(" -\t")
        if stripped:
            chunks.append(stripped)
    if not chunks and text.strip():
        chunks.append(text.strip())
    return chunks


def keyword_score(text: str, keywords: Iterable[str]) -> int:
    lowered = text.lower()
    score = 0
    for keyword in keywords:
        if keyword.lower() in lowered:
            score += 2 if len(keyword) > 3 else 1
    if any(marker in lowered for marker in ["반드시", "꼭", "매우", "중요", "must", "never"]):
        score += 3
    if any(marker in lowered for marker in ["누락", "실수", "오류", "문제", "불편", "risk"]):
        score += 2
    return score


def collect_evidence(messages: list[Message]) -> dict[str, list[Evidence]]:
    evidence: dict[str, list[Evidence]] = {key: [] for key, _, _ in CATEGORY_DEFS}
    for message in messages:
        role_bonus = 2 if message.role == "user" else 0
        sentences = split_sentences(message.content)
        for sentence in sentences:
            for key, _, keywords in CATEGORY_DEFS:
                score = keyword_score(sentence, keywords) + role_bonus
                if score >= 3:
                    evidence[key].append(
                        Evidence(
                            message_index=message.index,
                            role=message.role,
                            line_start=message.line_start,
                            line_end=message.line_end,
                            text=sentence,
                            score=score,
                        )
                    )
    for key in evidence:
        evidence[key] = sorted(
            evidence[key],
            key=lambda item: (-item.score, item.message_index, item.line_start),
        )
    return evidence


def first_evidence(evidence: dict[str, list[Evidence]], key: str, fallback: str) -> str:
    items = evidence.get(key, [])
    return redact_secrets(items[0].text) if items else fallback


def format_evidence(item: Evidence) -> str:
    location = f"M{item.message_index}"
    if item.line_start:
        location += f", L{item.line_start}-L{item.line_end}"
    return f"- ({location}, {item.role}, score {item.score}) {redact_secrets(item.text)}"


def render_major_outline(project: str, source_name: str, messages: list[Message], evidence: dict[str, list[Evidence]]) -> str:
    lines = [
        "# 02 Major Outline",
        "",
        f"- Project: {project}",
        f"- Source: {source_name}",
        f"- Messages parsed: {len(messages)}",
        f"- Generated at: {now_utc()}",
        "",
        "이 파일은 대화 전체를 큰 제목 단위로 압축합니다. 세부 근거가 필요하면 `03_minor_outline.md`와 `01_raw_conversation.md`로 역추적합니다.",
        "",
    ]
    for key, title, _ in CATEGORY_DEFS:
        lines.append(f"## {title}")
        items = evidence.get(key, [])[:5]
        if items:
            lines.extend(format_evidence(item) for item in items)
        else:
            lines.append("- 대화에서 명시 신호가 충분히 감지되지 않았습니다.")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def render_minor_outline(project: str, messages: list[Message], evidence: dict[str, list[Evidence]]) -> str:
    lines = [
        "# 03 Minor Outline",
        "",
        f"- Project: {project}",
        f"- Generated at: {now_utc()}",
        "",
        "세부 항목은 사용자가 중요하게 여길 가능성이 높은 표현을 보존합니다. 요약에서 빠질 수 있는 작은 차이는 이 단계에 남깁니다.",
        "",
    ]
    for key, title, _ in CATEGORY_DEFS:
        lines.append(f"## {title}")
        items = evidence.get(key, [])[:12]
        if not items:
            lines.append("- 보존할 세부 신호 없음")
        else:
            for item in items:
                lines.append(f"### Detail from M{item.message_index}")
                lines.append(f"- Role: {item.role}")
                if item.line_start:
                    lines.append(f"- Raw lines: {item.line_start}-{item.line_end}")
                lines.append(f"- Evidence: {redact_secrets(item.text)}")
                lines.append(f"- Why keep it: {explain_retention_reason(key)}")
                lines.append("")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def explain_retention_reason(category: str) -> str:
    reasons = {
        "north_star": "프로젝트의 존재 이유와 방향을 결정하는 문장입니다.",
        "requirements": "향후 구현과 검증의 직접 기준이 되는 요구사항입니다.",
        "small_details": "사용자의 개성과 차별점이 요약 과정에서 사라지기 쉬운 지점입니다.",
        "continuity": "다음 세션이나 다른 LLM으로 이어갈 때 필요한 맥락입니다.",
        "retrieval": "원본 역추적과 검색 UX를 설계하는 단서입니다.",
        "learning": "사용자 맞춤 패턴으로 승격할 후보입니다.",
        "privacy": "저장, 이동, 재사용 범위를 제한해야 하는 소유권 신호입니다.",
        "verification": "오류를 숨기지 않고 바로잡기 위한 운영 규칙입니다.",
    }
    return reasons.get(category, "향후 대화 재구성에 필요한 근거입니다.")


def render_summary(
    project: str,
    messages: list[Message],
    evidence: dict[str, list[Evidence]],
    secret_findings: list[SecretFinding] | None = None,
    mojibake_warning: bool = False,
) -> str:
    north_star = first_evidence(
        evidence,
        "north_star",
        "대화를 계층화해 프로젝트 기억을 보존하고 다음 LLM 세션에서 이어갈 수 있게 한다.",
    )
    requirements = [redact_secrets(item.text) for item in evidence.get("requirements", [])[:7]]
    risks = [redact_secrets(item.text) for item in evidence.get("small_details", [])[:4]]
    continuity = [redact_secrets(item.text) for item in evidence.get("continuity", [])[:4]]
    verification = [redact_secrets(item.text) for item in evidence.get("verification", [])[:4]]

    lines = [
        "# 04 Summary",
        "",
        f"- Project: {project}",
        f"- Generated at: {now_utc()}",
        f"- Conversation messages parsed: {len(messages)}",
        "",
        "## One-paragraph context",
        "",
        (
            "이 프로젝트는 LLM과 사용자가 개발 계획에 도달하는 전 과정을 보존해, "
            "요약 과정에서 사라지기 쉬운 작은 취향, 요구, 철학, 문제의식을 다음 작업에 다시 투입하기 위한 기억 계층입니다. "
            f"핵심 신호: {north_star}"
        ),
        "",
        "## Non-negotiables",
    ]
    if requirements:
        lines.extend(f"- {item}" for item in requirements)
    else:
        lines.append("- 원본, 대제목, 소제목, 요약본, 패턴의 5개 핵심 파일을 유지합니다.")
    lines.extend(["", "## Details likely to be lost by ordinary summaries"])
    lines.extend(f"- {item}" for item in risks) if risks else lines.append("- 작은 차이를 근거와 함께 보존합니다.")
    lines.extend(["", "## Continuity notes"])
    lines.extend(f"- {item}" for item in continuity) if continuity else lines.append("- 패턴과 요약을 먼저 읽고, 필요할 때 세부 항목과 원본으로 내려갑니다.")
    lines.extend(["", "## Verification notes"])
    lines.extend(f"- {item}" for item in verification) if verification else lines.append("- 생성물은 샘플 입력과 검색으로 검증합니다.")
    lines.extend(render_security_section(secret_findings or [], mojibake_warning))
    return "\n".join(lines).rstrip() + "\n"


def render_patterns(project: str, evidence: dict[str, list[Evidence]]) -> str:
    patterns = derive_patterns(evidence)
    lines = [
        "# 05 Patterns",
        "",
        f"- Project: {project}",
        f"- Generated at: {now_utc()}",
        "",
        "이 파일은 다음 LLM 세션이 먼저 읽을 행동 패턴입니다. 이는 모델 가중치 학습이 아니라, 대화 근거에서 추출한 언어적 강화/운영 기억입니다.",
        "",
        "## Session User Patterns",
    ]
    lines.extend(f"- {pattern}" for pattern in patterns["stable"])
    lines.extend(["", "## Agent Operating Rules"])
    lines.extend(f"- {rule}" for rule in patterns["rules"])
    lines.extend(["", "## Retrieval Order"])
    lines.extend(
        [
            "- 1. 이 `05_patterns.md`를 먼저 읽어 사용자의 개발 방식과 금지선을 잡습니다.",
            "- 2. `04_summary.md`로 현재 프로젝트 맥락을 빠르게 복원합니다.",
            "- 3. 모호하거나 중요한 요구는 `03_minor_outline.md`와 `02_major_outline.md`에서 근거를 확인합니다.",
            "- 4. 사용자가 과거 표현을 찾거나 세부 차이를 물으면 `01_raw_conversation.md`를 직접 검색합니다.",
        ]
    )
    lines.extend(["", "## Pattern Refinement Loop"])
    lines.extend(
        [
            "- 새 대화가 끝나면 같은 5계층 산출물을 다시 생성합니다.",
            "- 기존 패턴과 충돌하는 새 증거는 삭제하지 말고 `changed preference`로 기록합니다.",
            "- 반복 확인된 패턴만 stable로 승격하고, 한 번 나온 취향은 candidate로 유지합니다.",
            "- 사용자가 정정한 내용은 가장 높은 우선순위의 학습 신호로 다룹니다.",
        ]
    )
    lines.extend(["", "## Candidate Signals"])
    candidate_items = []
    for key in ["small_details", "learning", "privacy", "verification"]:
        candidate_items.extend(evidence.get(key, [])[:3])
    if candidate_items:
        lines.extend(format_evidence(item) for item in candidate_items[:10])
    else:
        lines.append("아직 후보 신호가 충분하지 않습니다.")
    return "\n".join(lines).rstrip() + "\n"


def derive_patterns(evidence: dict[str, list[Evidence]]) -> dict[str, list[str]]:
    stable: list[str] = []
    if evidence.get("small_details"):
        stable.append("사용자는 요약에서 사라질 수 있는 작은 차이와 프로젝트 개성 보존을 중시합니다.")
    if evidence.get("requirements"):
        stable.append("사용자는 원본 요구를 먼저 보존하고 구조화된 산출물로 재사용하기를 원합니다.")
    if evidence.get("continuity"):
        stable.append("사용자는 다른 세션이나 다른 LLM으로도 프로젝트 맥락이 이어지기를 원합니다.")
    if evidence.get("retrieval"):
        stable.append("사용자는 요약에서 시작하되 필요하면 원본 근거로 역추적할 수 있기를 원합니다.")
    if evidence.get("learning"):
        stable.append("사용자는 반복된 정정과 선호를 다음 작업 방식에 반영하기를 원합니다.")
    if evidence.get("privacy"):
        stable.append("사용자는 프로젝트 기억의 로컬 보존, 보안, 소유권 경계를 중시합니다.")
    if evidence.get("verification"):
        stable.append("사용자는 오류 가능성을 숨기지 않고 검증 산출물로 바로잡기를 원합니다.")
    rules = [
        "계획을 세울 때 먼저 원본 요구를 보존하고, 그다음 큰 구조와 작은 구조로 나눕니다.",
        "패턴 파일만 보고 단정하지 말고 중요한 결정은 요약 또는 원본 근거로 역추적합니다.",
        "사용자의 정정, 불만, 누락 지적은 다음 작업 방식에 반영해야 할 강화 신호로 저장합니다.",
        "개인 데이터와 프로젝트 기억은 사용자 소유물로 취급하고, 기본값은 로컬 우선으로 둡니다.",
    ]
    if evidence.get("verification"):
        rules.append("오류 가능성을 숨기지 말고 검증 산출물과 실패 흔적을 남깁니다.")
    return {"stable": stable, "rules": rules}


def section_bullets(markdown: str, heading: str) -> list[str]:
    lines = markdown.splitlines()
    capture = False
    bullets: list[str] = []
    for line in lines:
        if line.strip() == f"## {heading}":
            capture = True
            continue
        if capture and line.startswith("## "):
            break
        if capture and line.startswith("- "):
            bullets.append(line[2:].strip())
    return bullets


def normalize_pattern(pattern: str) -> str:
    cleaned = re.sub(r"`[^`]+`", "", pattern)
    cleaned = re.sub(r"\([^)]*\)", "", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" .")
    return normalize_for_match(cleaned)


def list_sessions(project_root: Path) -> list[Path]:
    if not project_root.exists():
        return []
    return sorted(
        path
        for path in project_root.iterdir()
        if path.is_dir() and not path.name.endswith(".tmp") and all((path / name).exists() for name in CORE_FILE_NAMES)
    )


def pattern_status(stable_count: int, candidate_count: int, unique_sessions: int) -> str:
    if stable_count >= 2 or unique_sessions >= 3:
        return "stable"
    if stable_count == 1 or unique_sessions >= 2:
        return "observed"
    return "candidate"


def load_pattern_overrides(project_root: Path) -> dict[str, dict[str, str]]:
    path = project_root / PATTERN_OVERRIDES_FILE
    if not path.exists():
        return {}
    try:
        data = json.loads(read_text(path))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid pattern override file: {path}: {exc}") from exc
    patterns = data.get("patterns", {}) if isinstance(data, dict) else {}
    if not isinstance(patterns, dict):
        raise SystemExit(f"Invalid pattern override file: {path}: `patterns` must be an object")
    normalized: dict[str, dict[str, str]] = {}
    for key, value in patterns.items():
        if isinstance(value, dict):
            normalized[str(key)] = {str(k): str(v) for k, v in value.items()}
    return normalized


def write_pattern_overrides(project_root: Path, overrides: dict[str, dict[str, str]]) -> None:
    data = {
        "version": 1,
        "updated_at": now_utc(),
        "patterns": dict(sorted(overrides.items())),
    }
    write_text(project_root / PATTERN_OVERRIDES_FILE, json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def apply_pattern_override(auto_status: str, override: dict[str, str] | None) -> str:
    if not override:
        return auto_status
    status = override.get("status", "").strip().lower()
    if status in {"candidate", "observed", "stable", "rejected"}:
        return status
    return auto_status


def rebuild_project_indexes(project_root: Path, project: str) -> None:
    sessions = list_sessions(project_root)
    if not sessions:
        return
    overrides = load_pattern_overrides(project_root)

    timeline_lines = [
        "# Project Timeline",
        "",
        f"- Project: {project}",
        f"- Sessions: {len(sessions)}",
        f"- Rebuilt at: {now_utc()}",
        "",
    ]
    index_lines = [
        "# Project Index",
        "",
        f"- Project: {project}",
        f"- Sessions: {len(sessions)}",
        f"- Rebuilt at: {now_utc()}",
        "",
        "## Retrieval Contract",
        "",
        "- Start with `_pattern_registry.md` for accumulated user/project patterns.",
        "- Use the latest session `05_patterns.md` and `04_summary.md` for immediate continuation.",
        "- Use older session outlines when the user asks where an idea came from.",
        "",
        "## Sessions",
    ]
    pattern_records: dict[str, dict[str, Any]] = {}

    for session in sessions:
        summary = read_text(session / "04_summary.md")
        patterns = read_text(session / "05_patterns.md")
        one_line = extract_section(summary, "One-paragraph context", max_lines=1) or "(no summary)"
        index_lines.append(f"- `{session.name}`: {one_line}")
        timeline_lines.append(f"## {session.name}")
        timeline_lines.append(f"- Summary: {one_line}")
        timeline_lines.append(f"- Path: `{session}`")
        timeline_lines.append("")

        for source, section in [
            ("stable", "Session User Patterns"),
            ("stable", "Stable User Patterns"),
            ("candidate", "Candidate Signals"),
        ]:
            for bullet in section_bullets(patterns, section):
                key = normalize_pattern(bullet)
                if not key:
                    continue
                record = pattern_records.setdefault(
                    key,
                    {"text": bullet, "stable_count": 0, "candidate_count": 0, "sessions": []},
                )
                if source == "stable":
                    record["stable_count"] += 1
                else:
                    record["candidate_count"] += 1
                record["sessions"].append(session.name)

    registry_lines = [
        "# Pattern Registry",
        "",
        f"- Project: {project}",
        f"- Rebuilt at: {now_utc()}",
        "- Status rule: candidate=seen in one session, observed=seen across two sessions or once as stable, stable=confirmed across three sessions or twice as stable.",
        "",
        "## Patterns",
    ]
    sorted_records = sorted(
        pattern_records.values(),
        key=lambda r: (
            pattern_status(r["stable_count"], r["candidate_count"], len(set(r["sessions"]))) != "stable",
            -len(set(r["sessions"])),
            -r["stable_count"],
            -r["candidate_count"],
            r["text"],
        ),
    )
    rejected_lines: list[str] = []
    seen_override_keys: set[str] = set()
    for record in sorted_records:
        key = normalize_pattern(record["text"])
        override = overrides.get(key)
        if override:
            seen_override_keys.add(key)
        unique_session_count = len(set(record["sessions"]))
        auto_status = pattern_status(record["stable_count"], record["candidate_count"], unique_session_count)
        status = apply_pattern_override(auto_status, override)
        sessions_text = ", ".join(sorted(set(record["sessions"]))[:5])
        human_note = ""
        if override:
            note = override.get("note", "").strip()
            human_note = f", human={status}" + (f", note={note}" if note else "")
        line = (
            f"- [{status}] {record['text']} "
            f"(stable={record['stable_count']}, candidate={record['candidate_count']}, "
            f"unique_sessions={unique_session_count}, sessions={sessions_text}{human_note})"
        )
        if status == "rejected":
            rejected_lines.append(line)
        else:
            registry_lines.append(line)

    for key, override in sorted(overrides.items()):
        if key in seen_override_keys:
            continue
        status = apply_pattern_override("candidate", override)
        if status == "rejected":
            rejected_lines.append(f"- [rejected] {override.get('text', key)} (human=rejected)")
            continue
        note = override.get("note", "").strip()
        note_text = f", note={note}" if note else ""
        registry_lines.append(f"- [{status}] {override.get('text', key)} (stable=0, candidate=0, unique_sessions=0, sessions=manual, human={status}{note_text})")

    if rejected_lines:
        registry_lines.extend(["", "## Rejected Patterns"])
        registry_lines.extend(rejected_lines)

    write_text(project_root / "_project_index.md", "\n".join(index_lines).rstrip() + "\n")
    write_text(project_root / "_timeline.md", "\n".join(timeline_lines).rstrip() + "\n")
    write_text(project_root / "_pattern_registry.md", "\n".join(registry_lines).rstrip() + "\n")


def copy_raw(raw_bytes: bytes, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(raw_bytes)


def ingest(args: argparse.Namespace) -> int:
    source = Path(args.input).resolve()
    if not source.exists():
        raise SystemExit(f"Input not found: {source}")
    raw_bytes = source.read_bytes()
    raw = decode_bytes(raw_bytes)
    secret_findings = scan_secrets(raw)
    mojibake_warning = contains_mojibake(raw)
    if secret_findings and args.fail_on_secret:
        print(render_scan_report(secret_findings, mojibake_warning))
        raise SystemExit(2)
    messages = parse_messages(source, raw)
    evidence = collect_evidence(messages)

    project_slug = slugify(args.project)
    digest = hashlib.sha256(raw_bytes).hexdigest()[:10]
    base_session_id = f"{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')}-{digest}"
    project_root = Path(args.vault).resolve() / project_slug
    session_id = base_session_id
    session_dir = project_root / session_id
    counter = 1
    while session_dir.exists() or session_dir.with_name(session_dir.name + ".tmp").exists():
        session_id = f"{base_session_id}-{counter}"
        session_dir = project_root / session_id
        counter += 1
    tmp_dir = session_dir.with_name(session_dir.name + ".tmp")

    try:
        tmp_dir.mkdir(parents=True)
        copy_raw(raw_bytes, tmp_dir / "01_raw_conversation.md")
        write_text(tmp_dir / "02_major_outline.md", render_major_outline(args.project, source.name, messages, evidence))
        write_text(tmp_dir / "03_minor_outline.md", render_minor_outline(args.project, messages, evidence))
        write_text(tmp_dir / "04_summary.md", render_summary(args.project, messages, evidence, secret_findings, mojibake_warning))
        write_text(tmp_dir / "05_patterns.md", render_patterns(args.project, evidence))
        tmp_dir.rename(session_dir)
        rebuild_project_indexes(project_root, args.project)
    except Exception:
        if tmp_dir.exists():
            shutil.rmtree(tmp_dir)
        raise

    if secret_findings or mojibake_warning:
        print(render_scan_report(secret_findings, mojibake_warning), file=sys.stderr)
    print(str(session_dir))
    return 0


def iter_memory_files(vault: Path, project: str | None = None) -> Iterable[Path]:
    root = vault / slugify(project) if project else vault
    if not root.exists():
        return []
    return sorted(
        path
        for path in root.rglob("*.md")
        if path.name.startswith(("01_", "02_", "03_", "04_", "05_")) or path.name in PROJECT_INDEX_FILES
    )


def tokenize(text: str) -> list[str]:
    tokens: set[str] = set()
    for match in TOKEN_RE.finditer(text):
        token = match.group(0).lower()
        tokens.add(token)
        if re.fullmatch(r"[가-힣]{3,}", token):
            for size in (2, 3):
                tokens.update(token[i : i + size] for i in range(0, len(token) - size + 1))
    return sorted(tokens)


def memory_file_priority(name: str) -> int:
    priority = {
        "_pattern_registry.md": 7,
        "_project_index.md": 6,
        "_timeline.md": 5,
        "05_patterns.md": 5,
        "04_summary.md": 4,
        "03_minor_outline.md": 3,
        "02_major_outline.md": 2,
        "01_raw_conversation.md": 1,
    }
    return priority.get(name, 0)


def score_text(text: str, query: str, query_tokens: set[str], priority: int) -> int:
    lowered = normalize_for_match(text)
    normalized_query = normalize_for_match(query.strip())
    score = priority
    if normalized_query and normalized_query in lowered:
        score += 12
    for token in query_tokens:
        if token in lowered:
            score += 3 if len(token) >= 3 else 1
    return score


def search(args: argparse.Namespace) -> int:
    vault = Path(args.vault).resolve()
    query_tokens = set(tokenize(args.query))
    if not query_tokens:
        raise SystemExit("Query must contain at least one searchable token.")

    results: list[tuple[int, Path, str]] = []
    for path in iter_memory_files(vault, args.project):
        text = read_text(path)
        priority = memory_file_priority(path.name)
        score = score_text(text, args.query, query_tokens, priority)
        if score <= priority:
            continue
        snippet = best_snippet(text, query_tokens)
        results.append((score, path, snippet))

    results.sort(key=lambda item: (-item[0], str(item[1])))
    for score, path, snippet in results[: args.limit]:
        print(f"[score={score}] {path}")
        print(snippet)
        print()
    return 0 if results else 1


def semantic_features(text: str) -> Counter[str]:
    normalized = normalize_for_match(text)
    features: Counter[str] = Counter()
    for token in tokenize(normalized):
        features[token] += 3
    for word in re.findall(r"[a-z0-9가-힣]{2,}", normalized):
        compact = re.sub(r"\s+", "", word)
        for size in (2, 3, 4):
            if len(compact) >= size:
                for index in range(0, len(compact) - size + 1):
                    features[f"ng{size}:{compact[index:index + size]}"] += 1
    return features


def cosine_score(left: Counter[str], right: Counter[str]) -> float:
    if not left or not right:
        return 0.0
    overlap = set(left) & set(right)
    numerator = sum(left[key] * right[key] for key in overlap)
    left_norm = sum(value * value for value in left.values()) ** 0.5
    right_norm = sum(value * value for value in right.values()) ** 0.5
    if not left_norm or not right_norm:
        return 0.0
    return numerator / (left_norm * right_norm)


def semantic_search(args: argparse.Namespace) -> int:
    vault = Path(args.vault).resolve()
    query_vector = semantic_features(args.query)
    if not query_vector:
        raise SystemExit("Query must contain at least one searchable token.")

    results: list[tuple[float, int, Path, str]] = []
    query_tokens = set(tokenize(args.query))
    for path in iter_memory_files(vault, args.project):
        text = read_text(path)
        score = cosine_score(query_vector, semantic_features(text))
        if score < args.min_score:
            continue
        priority = memory_file_priority(path.name)
        snippet = best_snippet(text, query_tokens)
        results.append((score, priority, path, snippet))

    results.sort(key=lambda item: (-item[0], -item[1], str(item[2])))
    for score, _, path, snippet in results[: args.limit]:
        print(f"[similarity={score:.3f}] {path}")
        print(snippet)
        print()
    return 0 if results else 1


def iter_scan_targets(target: Path) -> list[Path]:
    if target.is_file():
        return [target]
    if not target.exists():
        raise SystemExit(f"Scan target not found: {target}")
    return sorted(
        path
        for path in target.rglob("*")
        if path.is_file() and path.suffix.lower() in SCAN_TARGET_SUFFIXES
    )


def scan_command(args: argparse.Namespace) -> int:
    target = Path(args.target).resolve()
    all_findings: list[tuple[Path, SecretFinding]] = []
    mojibake_paths: list[Path] = []
    for path in iter_scan_targets(target):
        text = read_text(path)
        if contains_mojibake(text):
            mojibake_paths.append(path)
        for finding in scan_secrets(text):
            all_findings.append((path, finding))

    if not all_findings and not mojibake_paths:
        print("Security scan report")
        print("- status: ok")
        return 0

    print("Security scan report")
    for path in mojibake_paths:
        print(f"- possible mojibake: {path}")
    for path, finding in all_findings:
        print(f"- {finding.kind} {path}:{finding.line_number}: {finding.excerpt}")
    return 1


def iter_share_files(project_root: Path, include_raw: bool) -> list[Path]:
    allowed_project_files = PROJECT_INDEX_FILES | {PATTERN_OVERRIDES_FILE}
    files: list[Path] = []
    for path in sorted(project_root.rglob("*")):
        if not path.is_file():
            continue
        if path.name in allowed_project_files:
            files.append(path)
            continue
        if path.name in CORE_FILE_NAMES:
            if path.name == "01_raw_conversation.md" and not include_raw:
                continue
            files.append(path)
    return files


def build_share_zip_bytes(project_root: Path, project: str, include_raw: bool) -> bytes:
    files = iter_share_files(project_root, include_raw)
    manifest_lines = [
        "# Share Export Manifest",
        "",
        f"- Project: {project}",
        f"- Generated at: {now_utc()}",
        f"- Raw transcripts included: {str(include_raw).lower()}",
        "- Derived Markdown files are redacted again during export.",
        "",
        "## Files",
    ]
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in files:
            rel = path.relative_to(project_root).as_posix()
            manifest_lines.append(f"- `{rel}`")
            if path.name == "01_raw_conversation.md" and include_raw:
                archive.writestr(rel, path.read_bytes())
            else:
                archive.writestr(rel, redact_secrets(read_text(path)))
        archive.writestr("SHARE_MANIFEST.md", "\n".join(manifest_lines).rstrip() + "\n")
    return buffer.getvalue()


def export_share_command(args: argparse.Namespace) -> int:
    vault = Path(args.vault).resolve()
    project_root = vault / slugify(args.project)
    if not list_sessions(project_root):
        raise SystemExit(f"No complete sessions found for project: {args.project}")
    rebuild_project_indexes(project_root, args.project)
    output = Path(args.output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(build_share_zip_bytes(project_root, args.project, args.include_raw))
    print(output)
    return 0


def get_password(password_env: str) -> str:
    password = os.environ.get(password_env)
    if password:
        return password
    if sys.stdin.isatty():
        password = getpass.getpass(f"Password from {password_env} or prompt: ")
        if password:
            return password
    raise SystemExit(f"Password required. Set environment variable {password_env}.")


def derive_fernet_key(password: str, salt: bytes) -> bytes:
    try:
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    except ImportError as exc:
        raise SystemExit("Install crypto support first: pip install 'preserve-project-conversations[crypto]'") from exc
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=480_000)
    return base64.urlsafe_b64encode(kdf.derive(password.encode("utf-8")))


def seal_payload(payload: bytes, password: str) -> bytes:
    try:
        from cryptography.fernet import Fernet
    except ImportError as exc:
        raise SystemExit("Install crypto support first: pip install 'preserve-project-conversations[crypto]'") from exc
    salt = os.urandom(16)
    metadata = {
        "version": 1,
        "kdf": "pbkdf2-sha256",
        "iterations": 480_000,
        "salt": base64.b64encode(salt).decode("ascii"),
    }
    token = Fernet(derive_fernet_key(password, salt)).encrypt(payload)
    return b"PPCM-SEAL-v1\n" + json.dumps(metadata, sort_keys=True).encode("utf-8") + b"\n" + token


def unseal_payload(payload: bytes, password: str) -> bytes:
    try:
        from cryptography.fernet import Fernet, InvalidToken
    except ImportError as exc:
        raise SystemExit("Install crypto support first: pip install 'preserve-project-conversations[crypto]'") from exc
    try:
        header, metadata_raw, token = payload.split(b"\n", 2)
    except ValueError as exc:
        raise SystemExit("Invalid sealed vault format.") from exc
    if header != b"PPCM-SEAL-v1":
        raise SystemExit("Invalid sealed vault header.")
    metadata = json.loads(metadata_raw.decode("utf-8"))
    salt = base64.b64decode(metadata["salt"])
    try:
        return Fernet(derive_fernet_key(password, salt)).decrypt(token)
    except InvalidToken as exc:
        raise SystemExit("Invalid password or corrupted sealed vault.") from exc


def seal_vault_command(args: argparse.Namespace) -> int:
    vault = Path(args.vault).resolve()
    project_root = vault / slugify(args.project)
    if not list_sessions(project_root):
        raise SystemExit(f"No complete sessions found for project: {args.project}")
    rebuild_project_indexes(project_root, args.project)
    password = get_password(args.password_env)
    sealed = seal_payload(build_share_zip_bytes(project_root, args.project, args.include_raw), password)
    output = Path(args.output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(sealed)
    print(output)
    return 0


def unseal_vault_command(args: argparse.Namespace) -> int:
    password = get_password(args.password_env)
    payload = unseal_payload(Path(args.input).resolve().read_bytes(), password)
    output = Path(args.output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(payload)
    print(output)
    return 0


def rebuild_index_command(args: argparse.Namespace) -> int:
    vault = Path(args.vault).resolve()
    project_root = vault / slugify(args.project)
    if not list_sessions(project_root):
        raise SystemExit(f"No complete sessions found for project: {args.project}")
    rebuild_project_indexes(project_root, args.project)
    print(project_root / "_project_index.md")
    print(project_root / "_timeline.md")
    print(project_root / "_pattern_registry.md")
    return 0


def review_patterns_command(args: argparse.Namespace) -> int:
    vault = Path(args.vault).resolve()
    project_root = vault / slugify(args.project)
    if not list_sessions(project_root):
        raise SystemExit(f"No complete sessions found for project: {args.project}")
    rebuild_project_indexes(project_root, args.project)
    registry_path = project_root / "_pattern_registry.md"
    registry = read_text(registry_path)
    pattern_lines = [line for line in registry.splitlines() if line.startswith("- [")]
    review_lines = [
        "# Pattern Review",
        "",
        f"- Project: {args.project}",
        f"- Generated at: {now_utc()}",
        f"- Source: `{registry_path}`",
        "",
        "Check a pattern manually, then run `promote-pattern` with the exact pattern text and desired status.",
        "",
        "## Review Queue",
    ]
    if not pattern_lines:
        review_lines.append("- No pattern candidates found yet.")
    else:
        for line in pattern_lines:
            review_lines.append("- [ ] " + line[2:])
    review_path = project_root / PATTERN_REVIEW_FILE
    write_text(review_path, "\n".join(review_lines).rstrip() + "\n")
    print(review_path)
    return 0


def promote_pattern_command(args: argparse.Namespace) -> int:
    vault = Path(args.vault).resolve()
    project_root = vault / slugify(args.project)
    if not list_sessions(project_root):
        raise SystemExit(f"No complete sessions found for project: {args.project}")
    pattern = args.pattern.strip()
    if not pattern:
        raise SystemExit("Pattern text must not be empty.")
    overrides = load_pattern_overrides(project_root)
    overrides[normalize_pattern(pattern)] = {
        "text": pattern,
        "status": args.status,
        "note": args.note.strip() if args.note else "",
        "updated_at": now_utc(),
    }
    write_pattern_overrides(project_root, overrides)
    rebuild_project_indexes(project_root, args.project)
    print(project_root / PATTERN_OVERRIDES_FILE)
    print(project_root / "_pattern_registry.md")
    return 0


def best_snippet(text: str, tokens: set[str]) -> str:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    best_line = ""
    best_score = -1
    for line in lines:
        lowered = normalize_for_match(line)
        score = sum(1 for token in tokens if token in lowered)
        if score > best_score:
            best_score = score
            best_line = line
    if len(best_line) > 260:
        return best_line[:257] + "..."
    return best_line


def latest_session(project_root: Path) -> Path | None:
    if not project_root.exists():
        return None
    sessions = [path for path in project_root.iterdir() if path.is_dir() and not path.name.endswith(".tmp")]
    return sorted(sessions)[-1] if sessions else None


def context(args: argparse.Namespace) -> int:
    vault = Path(args.vault).resolve()
    project_root = vault / slugify(args.project)
    session = latest_session(project_root)
    if not session:
        raise SystemExit(f"No memory sessions found for project: {args.project}")
    registry_path = project_root / "_pattern_registry.md"
    patterns = read_text(session / "05_patterns.md")
    summary = read_text(session / "04_summary.md")
    print("# Portable Context Packet")
    print()
    print(f"- Project: {args.project}")
    print(f"- Session: {session}")
    if registry_path.exists():
        print(f"- Pattern registry: {registry_path}")
        print()
        print("## Accumulated Patterns")
        registry = read_text(registry_path)
        print(extract_section(registry, "Patterns", max_lines=8))
    print()
    print("## Latest Session Patterns")
    latest_patterns = extract_section(patterns, "Session User Patterns", max_lines=12)
    if not latest_patterns:
        latest_patterns = extract_section(patterns, "Stable User Patterns", max_lines=12)
    print(latest_patterns)
    print()
    print("## Summary")
    print(extract_section(summary, "One-paragraph context", max_lines=8))
    if args.query:
        print()
        print("## Search Hints")
        search_args = argparse.Namespace(vault=str(vault), project=args.project, query=args.query, limit=args.limit)
        search(search_args)
    return 0


def extract_section(markdown: str, heading: str, max_lines: int) -> str:
    lines = markdown.splitlines()
    capture = False
    output: list[str] = []
    for line in lines:
        if line.strip() == f"## {heading}":
            capture = True
            continue
        if capture and line.startswith("## "):
            break
        if capture and line.strip():
            output.append(line)
        if len(output) >= max_lines:
            break
    return "\n".join(output).strip()


def doctor(args: argparse.Namespace) -> int:
    skill_root = Path(__file__).resolve().parents[1]
    check_paths = [
        skill_root / "scripts" / "paideia_memory.py",
        skill_root / "tests" / "test_paideia_memory.py",
        skill_root / "examples" / "project-memory-conversation.md",
    ]
    bad_paths = [path for path in check_paths if path.exists() and contains_mojibake(read_text(path))]
    print("preserve-project-conversations doctor")
    print(f"python={sys.version.split()[0]}")
    print(f"script={Path(__file__).resolve()}")
    if bad_paths:
        print("status=encoding-warning")
        for path in bad_paths:
            print(f"possible_mojibake={path}")
        return 1
    print("encoding=ok")
    print("status=ok")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Preserve LLM project conversations as raw, outline, summary, and pattern memory."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    ingest_parser = subparsers.add_parser("ingest", help="Create a five-file memory session.")
    ingest_parser.add_argument("--project", required=True, help="Project name used for the vault folder.")
    ingest_parser.add_argument("--input", required=True, help="Conversation file: markdown, txt, json, or jsonl.")
    ingest_parser.add_argument("--vault", default="memory-vault", help="Output memory vault directory.")
    ingest_parser.add_argument("--fail-on-secret", action="store_true", help="Abort ingest when high-confidence secrets are detected.")
    ingest_parser.set_defaults(func=ingest)

    scan_parser = subparsers.add_parser("scan", help="Scan a file or folder for high-confidence secrets and encoding issues.")
    scan_parser.add_argument("--target", required=True, help="File or folder to scan.")
    scan_parser.set_defaults(func=scan_command)

    export_parser = subparsers.add_parser("export-share", help="Create a redacted zip bundle for sharing project memory.")
    export_parser.add_argument("--vault", default="memory-vault", help="Memory vault directory.")
    export_parser.add_argument("--project", required=True, help="Project name.")
    export_parser.add_argument("--output", required=True, help="Output .zip path.")
    export_parser.add_argument("--include-raw", action="store_true", help="Include raw transcripts. Off by default for safety.")
    export_parser.set_defaults(func=export_share_command)

    seal_parser = subparsers.add_parser("seal-vault", help="Create an encrypted share bundle using the optional crypto extra.")
    seal_parser.add_argument("--vault", default="memory-vault", help="Memory vault directory.")
    seal_parser.add_argument("--project", required=True, help="Project name.")
    seal_parser.add_argument("--output", required=True, help="Output sealed file path.")
    seal_parser.add_argument("--include-raw", action="store_true", help="Include raw transcripts. Off by default for safety.")
    seal_parser.add_argument("--password-env", default="PPCM_SEAL_PASSWORD", help="Environment variable containing the seal password.")
    seal_parser.set_defaults(func=seal_vault_command)

    unseal_parser = subparsers.add_parser("unseal-vault", help="Decrypt a sealed vault bundle into a zip file.")
    unseal_parser.add_argument("--input", required=True, help="Input sealed file path.")
    unseal_parser.add_argument("--output", required=True, help="Output .zip path.")
    unseal_parser.add_argument("--password-env", default="PPCM_SEAL_PASSWORD", help="Environment variable containing the seal password.")
    unseal_parser.set_defaults(func=unseal_vault_command)

    index_parser = subparsers.add_parser("rebuild-index", help="Rebuild project-level index, timeline, and pattern registry.")
    index_parser.add_argument("--vault", default="memory-vault", help="Memory vault directory.")
    index_parser.add_argument("--project", required=True, help="Project name.")
    index_parser.set_defaults(func=rebuild_index_command)

    review_parser = subparsers.add_parser("review-patterns", help="Create a human review checklist for accumulated patterns.")
    review_parser.add_argument("--vault", default="memory-vault", help="Memory vault directory.")
    review_parser.add_argument("--project", required=True, help="Project name.")
    review_parser.set_defaults(func=review_patterns_command)

    promote_parser = subparsers.add_parser("promote-pattern", help="Manually approve, downgrade, or reject a pattern.")
    promote_parser.add_argument("--vault", default="memory-vault", help="Memory vault directory.")
    promote_parser.add_argument("--project", required=True, help="Project name.")
    promote_parser.add_argument("--pattern", required=True, help="Exact pattern text to override.")
    promote_parser.add_argument(
        "--status",
        required=True,
        choices=["candidate", "observed", "stable", "rejected"],
        help="Human-reviewed pattern status.",
    )
    promote_parser.add_argument("--note", default="", help="Optional reviewer note stored with the override.")
    promote_parser.set_defaults(func=promote_pattern_command)

    search_parser = subparsers.add_parser("search", help="Search generated memory files.")
    search_parser.add_argument("--vault", default="memory-vault", help="Memory vault directory.")
    search_parser.add_argument("--project", help="Optional project name to restrict search.")
    search_parser.add_argument("--query", required=True, help="Search query.")
    search_parser.add_argument("--limit", type=int, default=8, help="Maximum number of results.")
    search_parser.set_defaults(func=search)

    semantic_parser = subparsers.add_parser("semantic-search", help="Run local n-gram similarity search over memory files.")
    semantic_parser.add_argument("--vault", default="memory-vault", help="Memory vault directory.")
    semantic_parser.add_argument("--project", help="Optional project name to restrict search.")
    semantic_parser.add_argument("--query", required=True, help="Search query.")
    semantic_parser.add_argument("--limit", type=int, default=8, help="Maximum number of results.")
    semantic_parser.add_argument("--min-score", type=float, default=0.05, help="Minimum cosine similarity.")
    semantic_parser.set_defaults(func=semantic_search)

    context_parser = subparsers.add_parser("context", help="Print a compact context packet for another LLM.")
    context_parser.add_argument("--vault", default="memory-vault", help="Memory vault directory.")
    context_parser.add_argument("--project", required=True, help="Project name.")
    context_parser.add_argument("--query", help="Optional query for extra retrieval hints.")
    context_parser.add_argument("--limit", type=int, default=5, help="Maximum search hints.")
    context_parser.set_defaults(func=context)

    doctor_parser = subparsers.add_parser("doctor", help="Verify the script can run.")
    doctor_parser.set_defaults(func=doctor)

    return parser


def main(argv: list[str] | None = None) -> int:
    configure_stdio()
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
