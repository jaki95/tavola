#!/usr/bin/env python3
"""Find documentation lines that may describe deferred tech debt."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path


DEFAULT_INCLUDE = ("AGENTS.md", "CONTEXT.md", "docs/**/*.md", "docs/**/*.mdx")
SKIP_PARTS = {
    ".git",
    ".venv",
    "node_modules",
    "dist",
    "build",
    ".mypy_cache",
    ".pytest_cache",
    "__pycache__",
}

PATTERNS = {
    "explicit_debt": re.compile(r"\b(tech debt|technical debt|debt)\b", re.I),
    "deferred": re.compile(
        r"\b(defer(?:red)?|future work|follow-?up (?:note|task|work)|later (?:upgrade|repair)|revisit|phase \d+)\b",
        re.I,
    ),
    "known_gap": re.compile(
        r"\b(known (?:issue|limitation|gap)|not yet (?:implemented|present|available|covered|supported)|unsupported|missing (?:coverage|tests?|metadata|thumbnails?|mappings?|state|behavior|implementation|integration|assets?|labels?))\b",
        re.I,
    ),
    "temporary": re.compile(r"\b(temporary|shortcut|workaround|stub|placeholder|fake)\b", re.I),
    "needs_work": re.compile(
        r"\b(todo|fixme|needs? to (?:be )?(?:proven|revisited|validated|hardened|implemented|wired|tested|added|repaired|replaced)|should eventually|should later)\b",
        re.I,
    ),
}


@dataclass
class Finding:
    path: str
    line: int
    category: str
    text: str


def iter_doc_files(root: Path, include_globs: tuple[str, ...]) -> list[Path]:
    files: set[Path] = set()
    for pattern in include_globs:
        for path in root.glob(pattern):
            if path.is_file() and not any(part in SKIP_PARTS for part in path.parts):
                files.add(path)
    return sorted(files)


def scan_file(root: Path, path: Path) -> list[Finding]:
    findings: list[Finding] = []
    rel_path = path.relative_to(root).as_posix()
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()

    for index, line in enumerate(lines, start=1):
        stripped = line.strip()
        if not stripped:
            continue
        for category, pattern in PATTERNS.items():
            if pattern.search(stripped):
                findings.append(
                    Finding(
                        path=rel_path,
                        line=index,
                        category=category,
                        text=stripped,
                    )
                )
                break
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="Repository root to scan.")
    parser.add_argument(
        "--include",
        action="append",
        help="Glob to include. Can be repeated. Defaults to Tavola docs.",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON findings.")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    include_globs = tuple(args.include) if args.include else DEFAULT_INCLUDE
    findings: list[Finding] = []
    for path in iter_doc_files(root, include_globs):
        findings.extend(scan_file(root, path))

    if args.json:
        print(json.dumps([asdict(finding) for finding in findings], indent=2))
        return 0

    if not findings:
        print("No documentation debt candidates found.")
        return 0

    for finding in findings:
        print(f"{finding.path}:{finding.line}: [{finding.category}] {finding.text}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
