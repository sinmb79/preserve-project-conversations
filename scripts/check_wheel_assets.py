#!/usr/bin/env python3
"""Verify release wheels include public docs and agent skill assets."""

from __future__ import annotations

import sys
import zipfile
from pathlib import Path


REQUIRED_FRAGMENTS = [
    "share/preserve-project-conversations/SKILL.md",
    "share/preserve-project-conversations/README.md",
    "share/preserve-project-conversations/agents/openai.yaml",
    "share/preserve-project-conversations/agents/claude.md",
    "share/preserve-project-conversations/agents/openclaw.yaml",
    "share/preserve-project-conversations/agents/hermes.yaml",
    "share/preserve-project-conversations/docs/SKILLPACKS.md",
    "share/preserve-project-conversations/skillpacks/anthropic-claude/preserve-project-conversations/SKILL.md",
    "share/preserve-project-conversations/skillpacks/openclaw-hermes/preserve-project-conversations/SKILL.md",
    "share/preserve-project-conversations/skillpacks/chatgpt-gpt/instructions.md",
    "share/preserve-project-conversations/skillpacks/chatgpt-gpt/knowledge.md",
]


def find_wheel(path_arg: str) -> Path:
    path = Path(path_arg)
    if path.is_dir():
        wheels = sorted(path.glob("*.whl"))
        if not wheels:
            raise SystemExit(f"No wheel found in {path}")
        return wheels[-1]
    if not path.exists():
        raise SystemExit(f"Wheel not found: {path}")
    return path


def main(argv: list[str] | None = None) -> int:
    args = argv or sys.argv[1:]
    wheel = find_wheel(args[0] if args else "dist")
    with zipfile.ZipFile(wheel) as archive:
        names = set(archive.namelist())
    missing = [fragment for fragment in REQUIRED_FRAGMENTS if not any(name.endswith(fragment) for name in names)]
    if missing:
        print(f"Wheel asset check failed: {wheel}")
        for fragment in missing:
            print(f"- missing: {fragment}")
        return 1
    print(f"Wheel asset check passed: {wheel}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
