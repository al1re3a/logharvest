from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .analyzer import analyze_lines


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="logharvest", description="Collapse logs into error fingerprints")
    parser.add_argument("file", nargs="?", help="Log file; stdin when omitted")
    parser.add_argument("--format", choices=("text", "json", "markdown"), default="text")
    parser.add_argument("--top", type=int, default=20)
    parser.add_argument("--errors-only", action="store_true")
    args = parser.parse_args(argv)
    if args.file:
        lines = Path(args.file).read_text(encoding="utf-8", errors="replace").splitlines()
    else:
        lines = sys.stdin.readlines()
    report = analyze_lines(lines, include_warnings=not args.errors_only)
    groups = report.groups[: max(1, args.top)]
    if args.format == "json":
        data = report.to_dict()
        data["groups"] = data["groups"][: max(1, args.top)]
        print(json.dumps(data, indent=2))
    elif args.format == "markdown":
        print(f"## LogHarvest report\n\n{report.matched_events} events collapsed into {len(report.groups)} groups.\n")
        print("| Level | Count | Fingerprint | Signature |\n|---|---:|---|---|")
        for group in groups:
            print(f"| {group.level} | {group.count} | `{group.fingerprint}` | {group.signature.replace('|', '&#124;')} |")
    else:
        print(f"LogHarvest: {report.matched_events} events -> {len(report.groups)} groups ({report.total_lines} lines)")
        for group in groups:
            print(f"{group.level:8} x{group.count:<5} {group.fingerprint}  {group.signature}")
    return 1 if any(group.level in {"PANIC", "CRITICAL", "FATAL"} for group in report.groups) else 0


if __name__ == "__main__":
    raise SystemExit(main())
