#!/usr/bin/env python3
"""Lint a .measui file against the empirically observed parser gotchas.

These checks cover the *mechanically detectable* subset of docs/measui-gotchas.md.
They are negative constraints (things known to break the NI UI Editor parser) that
cannot be derived from the sample files. This is a Linux-runnable lint only — passing
here does NOT guarantee the file loads; only the Windows UI Editor confirms that.

Usage:
    python scripts/validate_measui.py <file.measui> [<file.measui> ...]

Exit code 0 = no findings, 1 = findings, 2 = usage/IO error.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

# Id must be 30-32 lowercase hex, no dashes. Brace-UUID ClientId is the documented exception.
ID_RE = re.compile(r'\bId="([^"]*)"')
CLIENT_ID_RE = re.compile(r'\bClientId="(\{[^"]*\})"')
HEX_ID_RE = re.compile(r"^[0-9a-f]{30,32}$")
# Start tags (skip closing tags and the XML declaration).
START_TAG_RE = re.compile(r"<([A-Za-z][\w.:]*)\b([^>]*?)/?>")
ATTR_RE = re.compile(r'([A-Za-z_][\w.:]*)\s*=\s*"')


def check(path: Path) -> list[str]:
    findings: list[str] = []
    raw = path.read_bytes()
    # NI .measui files are UTF-8 with a leading BOM (all samples have one) — that BOM is
    # expected, so decode with utf-8-sig to strip it before the non-ASCII check.
    text = raw.decode("utf-8-sig", errors="replace")
    lines = text.splitlines()

    # 1. XML comments
    for i, line in enumerate(lines, 1):
        if "<!--" in line or "-->" in line:
            findings.append(f"{path}:{i}: XML comment found — comments are rejected by the parser")

    # 2. Non-ASCII bytes
    for i, line in enumerate(lines, 1):
        for col, ch in enumerate(line, 1):
            if ord(ch) > 127:
                findings.append(
                    f"{path}:{i}:{col}: non-ASCII character {ch!r} (U+{ord(ch):04X}) — use ASCII only"
                )
                break

    # 3. FitData adjuster
    for i, line in enumerate(lines, 1):
        if "[RangeAdjuster]FitData" in line:
            findings.append(f"{path}:{i}: Adjuster=[RangeAdjuster]FitData — use FitExactly")

    # 4. Boolean on ChannelNumericText (heuristic: type appears anywhere)
    for i, line in enumerate(lines, 1):
        if "[Type]Boolean" in line:
            findings.append(
                f"{path}:{i}: [Type]Boolean detected — ChannelNumericText cannot be Boolean; "
                f"use ChannelLED / ChannelCheckBox / ChannelSwitch"
            )

    # 5. Id format (excluding brace-UUID ClientId values)
    client_ids = set(CLIENT_ID_RE.findall(text))
    for m in ID_RE.finditer(text):
        val = m.group(1)
        if val in client_ids or val.startswith("{"):
            continue
        if not HEX_ID_RE.match(val):
            line_no = text.count("\n", 0, m.start()) + 1
            findings.append(
                f'{path}:{line_no}: Id="{val}" is not 30-32 lowercase hex chars (no dashes)'
            )

    # 6. Duplicate attributes within a single start tag
    for m in START_TAG_RE.finditer(text):
        attrs = ATTR_RE.findall(m.group(2))
        seen: set[str] = set()
        for a in attrs:
            if a in seen:
                line_no = text.count("\n", 0, m.start()) + 1
                findings.append(
                    f"{path}:{line_no}: duplicate attribute '{a}' on <{m.group(1)}> — rejected"
                )
            seen.add(a)

    return findings


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__)
        return 2

    all_findings: list[str] = []
    for arg in argv[1:]:
        path = Path(arg)
        if not path.is_file():
            print(f"error: not a file: {path}", file=sys.stderr)
            return 2
        all_findings.extend(check(path))

    if all_findings:
        for f in all_findings:
            print(f)
        print(f"\n{len(all_findings)} finding(s).")
        return 1

    print("OK — no gotchas detected (still confirm in the Windows UI Editor).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
