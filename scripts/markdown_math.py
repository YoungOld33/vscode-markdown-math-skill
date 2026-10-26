#!/usr/bin/env python3
"""Audit and safely migrate Markdown math delimiters for VS Code preview."""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path


FENCE_RE = re.compile(r"^ {0,3}(`{3,}|~{3,})")
DISPLAY_RE = re.compile(r"^(\s*)\\([\[\]])\s*$")
INLINE_CODE_RE = re.compile(r"(`+)(.*?)(\1)")


@dataclass
class Finding:
    line: int
    kind: str
    message: str


@dataclass
class Audit:
    findings: list[Finding] = field(default_factory=list)
    changed: int = 0

    def add(self, line: int, kind: str, message: str) -> None:
        self.findings.append(Finding(line, kind, message))


def markdown_files(paths: list[Path]) -> list[Path]:
    result: set[Path] = set()
    for path in paths:
        if path.is_dir():
            result.update(p for p in path.rglob("*.md") if p.is_file())
        elif path.is_file() and path.suffix.lower() == ".md":
            result.add(path)
        else:
            print(f"warning: skipped non-Markdown path: {path}", file=sys.stderr)
    return sorted(result)


def outside_inline_code(line: str) -> list[tuple[int, int, str]]:
    """Return non-code spans as (start, end, text)."""
    spans: list[tuple[int, int, str]] = []
    cursor = 0
    for match in INLINE_CODE_RE.finditer(line):
        if match.start() > cursor:
            spans.append((cursor, match.start(), line[cursor : match.start()]))
        cursor = match.end()
    if cursor < len(line):
        spans.append((cursor, len(line), line[cursor:]))
    return spans


def replace_outside_inline_code(line: str) -> tuple[str, int]:
    pieces: list[str] = []
    cursor = 0
    changes = 0
    for start, end, span in outside_inline_code(line):
        pieces.append(line[cursor:start])
        converted = span.replace(r"\(", "$").replace(r"\)", "$")
        changes += converted.count("$") - span.count("$")
        pieces.append(converted)
        cursor = end
    pieces.append(line[cursor:])
    return "".join(pieces), changes


def scan_line(line: str, number: int, audit: Audit) -> None:
    for _, _, span in outside_inline_code(line):
        for token, label in ((r"\(", "legacy inline opener"), (r"\)", "legacy inline closer")):
            if token in span:
                audit.add(number, "legacy-delimiter", f"{label}: {token}")
        if re.search(r"\\\\[()\[\]]", span):
            audit.add(number, "double-escape", "doubled formula escape; inspect raw source before changing it")
        if r"\_" in span:
            audit.add(number, "escaped-underscore", r"suspicious \_ outside inline code")


def brace_balance(math: str) -> int:
    math = re.sub(r"\\[{}]", "", math)
    return math.count("{") - math.count("}")


def audit_canonical_math(lines: list[str], audit: Audit) -> None:
    in_fence: str | None = None
    in_display = False
    display_start = 0
    display_parts: list[str] = []

    for number, line in enumerate(lines, 1):
        fence = FENCE_RE.match(line)
        if fence:
            marker = fence.group(1)[0]
            if in_fence is None:
                in_fence = marker
            elif marker == in_fence:
                in_fence = None
            continue
        if in_fence:
            continue

        stripped = line.strip()
        if stripped == "$$":
            if not in_display:
                in_display = True
                display_start = number
                display_parts = []
            else:
                if brace_balance("\n".join(display_parts)) != 0:
                    audit.add(display_start, "unbalanced-braces", "display formula has unbalanced grouping braces")
                in_display = False
            continue
        if in_display:
            display_parts.append(line)
            continue

        for _, _, span in outside_inline_code(line):
            singles = list(re.finditer(r"(?<!\$)\$(?!\$)", span))
            if len(singles) % 2:
                audit.add(number, "unbalanced-dollar", "odd number of inline $ delimiters")
                continue
            for index in range(0, len(singles), 2):
                content = span[singles[index].end() : singles[index + 1].start()]
                if brace_balance(content) != 0:
                    audit.add(number, "unbalanced-braces", "inline formula has unbalanced grouping braces")
                if line.lstrip().startswith("|") and re.search(r"(?<!\\)\|", content):
                    audit.add(number, "table-pipe", r"literal | inside table math; consider \lvert and \rvert")

    if in_display:
        audit.add(display_start, "unclosed-display", "display formula opened with $$ but was not closed")


def audit_lines(lines: list[str]) -> Audit:
    audit = Audit()
    in_fence: str | None = None
    for number, line in enumerate(lines, 1):
        fence = FENCE_RE.match(line)
        if fence:
            marker = fence.group(1)[0]
            if in_fence is None:
                in_fence = marker
            elif marker == in_fence:
                in_fence = None
            continue
        if in_fence:
            continue
        display = DISPLAY_RE.match(line)
        if display:
            audit.add(number, "legacy-delimiter", f"legacy display delimiter: \\{display.group(2)}")
        else:
            scan_line(line, number, audit)
    audit_canonical_math(lines, audit)
    return audit


def fix_lines(lines: list[str]) -> tuple[list[str], int]:
    output: list[str] = []
    changes = 0
    in_fence: str | None = None
    for line in lines:
        fence = FENCE_RE.match(line)
        if fence:
            marker = fence.group(1)[0]
            if in_fence is None:
                in_fence = marker
            elif marker == in_fence:
                in_fence = None
            output.append(line)
            continue
        if in_fence:
            output.append(line)
            continue
        display = DISPLAY_RE.match(line)
        if display:
            output.append(f"{display.group(1)}$$")
            changes += 1
        else:
            converted, count = replace_outside_inline_code(line)
            output.append(converted)
            changes += count
    return output, changes


def process(path: Path, fix: bool) -> Audit:
    text = path.read_text(encoding="utf-8")
    newline = "\r\n" if "\r\n" in text else "\n"
    had_final_newline = text.endswith(("\n", "\r"))
    lines = text.splitlines()
    changes = 0

    if fix:
        lines, changes = fix_lines(lines)
        if changes:
            rendered = newline.join(lines) + (newline if had_final_newline else "")
            path.write_text(rendered, encoding="utf-8", newline="")

    audit = audit_lines(lines)
    audit.changed = changes
    return audit


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", type=Path, help="Markdown files or directories")
    parser.add_argument("--fix", action="store_true", help="safely migrate legacy delimiters in place")
    args = parser.parse_args()

    files = markdown_files(args.paths)
    if not files:
        print("No Markdown files found.", file=sys.stderr)
        return 2

    total_findings = 0
    total_changes = 0
    for path in files:
        audit = process(path, args.fix)
        total_findings += len(audit.findings)
        total_changes += audit.changed
        print(f"{path}: {len(audit.findings)} finding(s), {audit.changed} change(s)")
        for finding in audit.findings:
            print(f"  L{finding.line} [{finding.kind}] {finding.message}")

    print(f"Summary: {len(files)} file(s), {total_findings} finding(s), {total_changes} change(s)")
    return 1 if total_findings else 0


if __name__ == "__main__":
    raise SystemExit(main())

