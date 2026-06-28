#!/usr/bin/env python3
"""Verify release artifacts include public docs and agent skill assets."""

from __future__ import annotations

import sys
import tarfile
import zipfile
from pathlib import Path


WHEEL_REQUIRED_FRAGMENTS = [
    "share/preserve-project-conversations/SKILL.md",
    "share/preserve-project-conversations/README.md",
    "share/preserve-project-conversations/agents/openai.yaml",
    "share/preserve-project-conversations/agents/claude.md",
    "share/preserve-project-conversations/agents/openclaw.yaml",
    "share/preserve-project-conversations/agents/hermes.yaml",
    "share/preserve-project-conversations/docs/SKILLPACKS.md",
    "share/preserve-project-conversations/skillpacks/anthropic-claude/preserve-project-conversations/SKILL.md",
    "share/preserve-project-conversations/skillpacks/anthropic-claude/preserve-project-conversations/agents/openai.yaml",
    "share/preserve-project-conversations/skillpacks/openclaw-hermes/preserve-project-conversations/SKILL.md",
    "share/preserve-project-conversations/skillpacks/openclaw-hermes/preserve-project-conversations/agents/openai.yaml",
    "share/preserve-project-conversations/skillpacks/chatgpt-gpt/instructions.md",
    "share/preserve-project-conversations/skillpacks/chatgpt-gpt/knowledge.md",
]


SDIST_REQUIRED_FRAGMENTS = [
    "SKILL.md",
    "README.md",
    "agents/openai.yaml",
    "agents/claude.md",
    "agents/openclaw.yaml",
    "agents/hermes.yaml",
    "docs/SKILLPACKS.md",
    "skillpacks/anthropic-claude/preserve-project-conversations/SKILL.md",
    "skillpacks/anthropic-claude/preserve-project-conversations/agents/openai.yaml",
    "skillpacks/openclaw-hermes/preserve-project-conversations/SKILL.md",
    "skillpacks/openclaw-hermes/preserve-project-conversations/agents/openai.yaml",
    "skillpacks/chatgpt-gpt/instructions.md",
    "skillpacks/chatgpt-gpt/knowledge.md",
]


def find_artifacts(path_arg: str) -> list[Path]:
    path = Path(path_arg)
    if path.is_dir():
        artifacts = sorted([*path.glob("*.whl"), *path.glob("*.tar.gz")])
        if not artifacts:
            raise SystemExit(f"No release artifacts found in {path}")
        return artifacts
    if not path.exists():
        raise SystemExit(f"Release artifact not found: {path}")
    return [path]


def artifact_names(path: Path) -> set[str]:
    if path.suffix == ".whl":
        with zipfile.ZipFile(path) as archive:
            return set(archive.namelist())
    if path.name.endswith(".tar.gz"):
        with tarfile.open(path, "r:gz") as archive:
            return set(archive.getnames())
    raise SystemExit(f"Unsupported artifact type: {path}")


def required_fragments(path: Path) -> list[str]:
    if path.suffix == ".whl":
        return WHEEL_REQUIRED_FRAGMENTS
    if path.name.endswith(".tar.gz"):
        return SDIST_REQUIRED_FRAGMENTS
    raise SystemExit(f"Unsupported artifact type: {path}")


def check_artifact(path: Path) -> list[str]:
    names = artifact_names(path)
    return [
        fragment
        for fragment in required_fragments(path)
        if not any(name.endswith(fragment) for name in names)
    ]


def main(argv: list[str] | None = None) -> int:
    args = argv or sys.argv[1:]
    failed = False
    for artifact in find_artifacts(args[0] if args else "dist"):
        missing = check_artifact(artifact)
        if missing:
            failed = True
            print(f"Package asset check failed: {artifact}")
            for fragment in missing:
                print(f"- missing: {fragment}")
        else:
            print(f"Package asset check passed: {artifact}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
