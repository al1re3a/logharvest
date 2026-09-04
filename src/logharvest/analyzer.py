from __future__ import annotations

import hashlib
import re
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from typing import Iterable

LEVEL = re.compile(r"\b(TRACE|DEBUG|INFO|NOTICE|WARN(?:ING)?|ERROR|FATAL|CRITICAL|PANIC)\b", re.I)
ERROR_HINT = re.compile(r"\b(?:exception|traceback|panic|fatal|segmentation fault|timed? out|connection refused|denied|failed|error)\b", re.I)
STACK_LINE = re.compile(r"^\s*(?:at\s+|File \"|Caused by:|\.\.\. \d+ more|[A-Za-z_.]+(?:Error|Exception):)")
REPLACEMENTS = [
    (re.compile(r"\b[0-9a-f]{8}-[0-9a-f-]{27,}\b", re.I), "<uuid>"),
    (re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"), "<ip>"),
    (re.compile(r"\b0x[0-9a-f]+\b", re.I), "<hex>"),
    (re.compile(r"\b\d+(?:\.\d+)?(?:ms|s|m|h|kb|mb|gb)?\b", re.I), "<n>"),
    (re.compile(r"(?:[A-Za-z]:)?[/\\](?:[^\s:/\\]+[/\\])+[^\s:]+"), "<path>"),
    (re.compile(r"https?://[^\s]+"), "<url>"),
]


@dataclass(frozen=True)
class Group:
    fingerprint: str
    level: str
    count: int
    signature: str
    first_line: int
    last_line: int
    sample: str


@dataclass(frozen=True)
class Report:
    total_lines: int
    matched_events: int
    groups: tuple[Group, ...]
    levels: dict[str, int]

    def to_dict(self):
        return {"total_lines": self.total_lines, "matched_events": self.matched_events, "levels": self.levels, "groups": [asdict(group) for group in self.groups]}


def normalize_message(message: str) -> str:
    result = message.lower()
    result = re.sub(r"^.*?\b(?:trace|debug|info|notice|warn(?:ing)?|error|fatal|critical|panic)\b[:\s-]*", "", result, flags=re.I)
    for pattern, replacement in REPLACEMENTS:
        result = pattern.sub(replacement, result)
    result = re.sub(r"\s+", " ", result).strip(" :-\t")
    return result[:240] or "unknown event"


def _level(line: str) -> str:
    match = LEVEL.search(line)
    if match:
        value = match.group(1).upper()
        return "WARN" if value == "WARNING" else value
    return "ERROR" if ERROR_HINT.search(line) else "INFO"


def analyze_lines(lines: Iterable[str], include_warnings: bool = True) -> Report:
    source = [line.rstrip("\r\n") for line in lines]
    events: list[tuple[int, str, str]] = []
    current_index = -1
    current_level = "INFO"
    current_parts: list[str] = []

    def flush() -> None:
        if current_index >= 0 and current_parts:
            events.append((current_index, current_level, "\n".join(current_parts)))

    for number, line in enumerate(source, 1):
        level = _level(line)
        starts = level in {"ERROR", "FATAL", "CRITICAL", "PANIC"} or (include_warnings and level == "WARN") or (ERROR_HINT.search(line) and not STACK_LINE.match(line))
        if starts:
            flush()
            current_index, current_level, current_parts = number, level, [line]
        elif current_index >= 0 and (STACK_LINE.match(line) or line.startswith((" ", "\t"))):
            if len(current_parts) < 12:
                current_parts.append(line)
        elif current_index >= 0:
            flush()
            current_index, current_parts = -1, []
    flush()

    buckets: dict[str, list[tuple[int, str, str]]] = defaultdict(list)
    for event in events:
        signature = normalize_message(event[2].splitlines()[0])
        digest = hashlib.sha256(signature.encode()).hexdigest()[:12]
        buckets[digest].append(event)

    rank = {"PANIC": 6, "CRITICAL": 5, "FATAL": 4, "ERROR": 3, "WARN": 2, "INFO": 1}
    groups = []
    for fingerprint, items in buckets.items():
        level = max((item[1] for item in items), key=lambda value: rank.get(value, 0))
        signature = normalize_message(items[0][2].splitlines()[0])
        groups.append(Group(fingerprint, level, len(items), signature, items[0][0], items[-1][0], items[0][2][:700]))
    groups.sort(key=lambda group: (-rank.get(group.level, 0), -group.count, group.fingerprint))
    return Report(len(source), len(events), tuple(groups), dict(Counter(event[1] for event in events)))
