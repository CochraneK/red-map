#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Extract Unreal Engine FString text from unpacked .uasset/.uexp/.umap files.

Use this after unpacking a .pak with UnrealPak or repak. It scans for Unreal's
length-prefixed FString layout, which is much cleaner than generic binary
strings for DataTable-heavy games.
"""
from __future__ import annotations

import argparse
import csv
import fnmatch
import json
import re
import struct
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EXTENSIONS = {".uasset", ".uexp", ".umap", ".locres", ".locmeta"}
CJK_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff]")
CONTROL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")
DATE_RE = re.compile(
    r"^\d{4}\u5e74[\d\u5e74\u6708\u65e5\u81f3\u5230\-~\uff5e\u2014"
    r"\u5e95\u521d\u95f4\u524d\u540e\u5de6\u53f3\u4e0a\u4e2d\u4e0b\u65ec]*$"
)
SUSPICIOUS_RE = re.compile(r"[�\ufffd\ue000-\uf8ff]")


@dataclass
class TextItem:
    source: str
    offset: int
    encoding: str
    text: str


@dataclass
class FileSummary:
    path: str
    size: int
    count: int


@dataclass
class TimelineCandidate:
    source: str
    offset: int
    date_label: str
    summary: str
    evidence_count: int


def normalize(value: str) -> str:
    value = value.replace("\ufeff", "").replace("\x00", "")
    return re.sub(r"\s+", " ", value).strip()


def is_useful(value: str, min_chars: int, include_ascii: bool) -> bool:
    if len(value) < min_chars:
        return False
    if CONTROL_RE.search(value) or SUSPICIOUS_RE.search(value):
        return False
    if CJK_RE.search(value):
        return True
    return include_ascii and any(ch.isalpha() for ch in value)


def extract_fstrings(path: Path, root: Path, min_chars: int, max_chars: int, include_ascii: bool) -> list[TextItem]:
    data = path.read_bytes()
    rel = str(path.relative_to(root)) if root.is_dir() else path.name
    items: list[TextItem] = []
    seen: set[str] = set()

    for offset in range(0, len(data) - 4):
        (length,) = struct.unpack_from("<i", data, offset)
        if length < -1:
            chars = -length
            end = offset + 4 + chars * 2
            if chars > max_chars or end > len(data):
                continue
            if data[end - 2:end] != b"\x00\x00":
                continue
            try:
                text = data[offset + 4:end - 2].decode("utf-16le")
            except UnicodeDecodeError:
                continue
            add_item(items, seen, rel, offset, "utf-16le", text, min_chars, include_ascii)
        elif length > 1:
            chars = length
            end = offset + 4 + chars
            if chars > max_chars or end > len(data):
                continue
            if data[end - 1] != 0:
                continue
            try:
                text = data[offset + 4:end - 1].decode("utf-8")
            except UnicodeDecodeError:
                continue
            add_item(items, seen, rel, offset, "utf-8", text, min_chars, include_ascii)

    return sorted(items, key=lambda item: item.offset)


def add_item(
    items: list[TextItem],
    seen: set[str],
    source: str,
    offset: int,
    encoding: str,
    raw: str,
    min_chars: int,
    include_ascii: bool,
) -> None:
    text = normalize(raw)
    if text in seen or not is_useful(text, min_chars, include_ascii):
        return
    seen.add(text)
    items.append(TextItem(source, offset, encoding, text))


def iter_files(target: Path, extensions: set[str], exclude_globs: list[str]) -> list[Path]:
    if target.is_file():
        return [target]
    files: list[Path] = []
    for path in target.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in extensions:
            continue
        if any(fnmatch.fnmatch(path.name, pattern) or fnmatch.fnmatch(str(path), pattern) for pattern in exclude_globs):
            continue
        files.append(path)
    return sorted(
        files,
        key=lambda item: str(item).lower(),
    )


def build_timeline_candidates(items: list[TextItem]) -> list[TimelineCandidate]:
    by_source: dict[str, list[TextItem]] = {}
    for item in items:
        by_source.setdefault(item.source, []).append(item)

    candidates: list[TimelineCandidate] = []
    for source, source_items in by_source.items():
        ordered = sorted(source_items, key=lambda item: item.offset)
        for index, item in enumerate(ordered):
            if not DATE_RE.match(item.text):
                continue
            evidence: list[str] = []
            for next_item in ordered[index + 1:index + 8]:
                if DATE_RE.match(next_item.text):
                    break
                if next_item.text.count("#") >= 2:
                    continue
                if len(next_item.text) >= 8:
                    evidence.append(next_item.text)
                if len(evidence) >= 3:
                    break
            if evidence:
                candidates.append(
                    TimelineCandidate(
                        source=source,
                        offset=item.offset,
                        date_label=item.text,
                        summary=" ".join(evidence),
                        evidence_count=len(evidence),
                    )
                )
    return candidates


def write_outputs(items: list[TextItem], summaries: list[FileSummary], out_dir: Path, markdown_limit: int) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)

    with (out_dir / "unreal_text_dump.jsonl").open("w", encoding="utf-8", newline="\n") as f:
        for item in items:
            f.write(json.dumps(item.__dict__, ensure_ascii=False) + "\n")

    with (out_dir / "unreal_text_dump.csv").open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["source", "offset", "encoding", "text"])
        writer.writeheader()
        for item in items:
            writer.writerow(item.__dict__)

    with (out_dir / "unreal_asset_manifest.csv").open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["path", "size", "count"])
        writer.writeheader()
        for summary in summaries:
            writer.writerow(summary.__dict__)

    by_source: dict[str, list[TextItem]] = {}
    for item in items:
        by_source.setdefault(item.source, []).append(item)

    with (out_dir / "unreal_text_dump.md").open("w", encoding="utf-8-sig", newline="\n") as f:
        f.write("# Unreal Text Dump\n\n")
        for source in sorted(by_source):
            f.write(f"## {source}\n\n")
            for item in sorted(by_source[source], key=lambda row: row.offset)[:markdown_limit]:
                f.write(f"- `{item.encoding}` @0x{item.offset:x}: {item.text}\n")
            extra = len(by_source[source]) - markdown_limit
            if extra > 0:
                f.write(f"\n_... {extra} more lines in unreal_text_dump.jsonl_\n")
            f.write("\n")

    candidates = build_timeline_candidates(items)
    with (out_dir / "unreal_timeline_candidates.csv").open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["source", "offset", "date_label", "summary", "evidence_count"])
        writer.writeheader()
        for candidate in candidates:
            writer.writerow(candidate.__dict__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract Unreal FString text from unpacked UE assets.")
    parser.add_argument("target", help="Unpacked asset file or directory.")
    parser.add_argument("--out", default=str(ROOT / "research_private" / "unreal_text_dump"), help="Output directory.")
    parser.add_argument("--min-chars", type=int, default=2, help="Minimum text length.")
    parser.add_argument("--max-chars", type=int, default=1200, help="Maximum FString length to scan.")
    parser.add_argument("--include-ascii", action="store_true", help="Keep non-CJK strings too.")
    parser.add_argument("--exclude-glob", action="append", default=[], help="Skip files whose name/path matches this glob. Can be repeated.")
    parser.add_argument("--markdown-limit-per-file", type=int, default=300, help="Preview line limit per file.")
    parser.add_argument(
        "--extensions",
        default=",".join(sorted(DEFAULT_EXTENSIONS)),
        help="Comma-separated file extensions to scan.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    target = Path(args.target)
    if not target.exists():
        print(f"[ERROR] target does not exist: {target}")
        return 2

    extensions = {ext if ext.startswith(".") else f".{ext}" for ext in args.extensions.split(",") if ext.strip()}
    root = target if target.is_dir() else target.parent
    items: list[TextItem] = []
    summaries: list[FileSummary] = []
    for path in iter_files(target, extensions, args.exclude_glob):
        extracted = extract_fstrings(path, root, args.min_chars, args.max_chars, args.include_ascii)
        rel = str(path.relative_to(root)) if root.is_dir() else path.name
        summaries.append(FileSummary(rel, path.stat().st_size, len(extracted)))
        items.extend(extracted)

    out_dir = Path(args.out)
    write_outputs(items, summaries, out_dir, args.markdown_limit_per_file)
    print(f"[OK] scanned files={len(summaries)}, extracted strings={len(items)}")
    print(f"[OK] timeline candidates={len(build_timeline_candidates(items))}")
    print(f"[OK] output: {out_dir.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
