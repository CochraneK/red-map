#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Extract readable text candidates from a local Steam game directory.

The tool is intended for personal research and data curation. It reads local
files, does not modify the game, and exports text into formats that can be
reviewed before being structured into the red-map data tables.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

TEXT_EXTENSIONS = {
    ".txt", ".csv", ".tsv", ".json", ".jsonl", ".xml", ".html", ".htm",
    ".ini", ".cfg", ".conf", ".properties", ".yaml", ".yml", ".md",
    ".lua", ".js", ".ts", ".cs", ".shader", ".hlsl", ".glsl", ".po",
    ".pot", ".strings", ".lang", ".loc", ".asset", ".bytes",
}

SKIP_EXTENSIONS = {
    ".exe", ".dll", ".pdb", ".so", ".dylib", ".png", ".jpg", ".jpeg",
    ".webp", ".gif", ".bmp", ".tga", ".psd", ".mp3", ".wav", ".ogg",
    ".flac", ".mp4", ".mov", ".avi", ".wmv", ".zip", ".rar", ".7z",
    ".pak", ".bank", ".bundle", ".ress",
}

SKIP_DIRS = {
    ".git", ".svn", "__pycache__", "node_modules", "Library",
}

DECODINGS = ("utf-8-sig", "utf-8", "gb18030", "utf-16", "utf-16le", "utf-16be")
MEANINGFUL_RE = re.compile(r"[A-Za-z\u3400-\u4dbf\u4e00-\u9fff]")
CJK_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff]")
CONTROL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")
ASCII_BYTES_RE = re.compile(rb"[\x09\x0a\x0d\x20-\x7e]{4,}")
TEXT_RUN_RE = re.compile(
    r"[A-Za-z0-9\u3400-\u4dbf\u4e00-\u9fff\u3000-\u303f\uff00-\uffef"
    r"\s:：,，.。!?！？;；'\"“”‘’()（）<>《》\[\]【】/_\\\-.·…—]{4,}"
)
LARGE_BINARY_THRESHOLD = 32 * 1024 * 1024
CHUNK_SIZE = 4 * 1024 * 1024
CHUNK_OVERLAP = 8192


@dataclass
class ExtractedLine:
    source: str
    line: int | None
    encoding: str
    text: str


@dataclass
class FileSummary:
    path: str
    size: int
    mode: str
    encoding: str
    count: int
    note: str


def discover_steam_libraries(steam_root: Path | None) -> list[Path]:
    candidates: list[Path] = []
    if steam_root:
        candidates.append(steam_root)
    for env_name in ("ProgramFiles(x86)", "ProgramFiles"):
        env_path = os.environ.get(env_name)
        if env_path:
            candidates.append(Path(env_path) / "Steam")
    for drive in ("C", "D", "E", "F", "G"):
        candidates.extend([Path(f"{drive}:/SteamLibrary"), Path(f"{drive}:/Steam")])

    libraries: list[Path] = []
    seen: set[str] = set()
    for root in candidates:
        if not root.exists():
            continue
        add_library(root, libraries, seen)
        vdf = root / "steamapps" / "libraryfolders.vdf"
        if not vdf.exists():
            continue
        text = read_text_lenient(vdf)
        for raw_path in re.findall(r'"path"\s+"([^"]+)"', text):
            add_library(Path(raw_path.replace("\\\\", "\\")), libraries, seen)
    return libraries


def add_library(path: Path, libraries: list[Path], seen: set[str]) -> None:
    common = path / "steamapps" / "common"
    if common.exists():
        key = str(path.resolve()).lower()
        if key not in seen:
            seen.add(key)
            libraries.append(path)


def locate_game(keyword: str, steam_root: Path | None) -> Path:
    keyword_lower = keyword.lower()
    matches: list[Path] = []
    for library in discover_steam_libraries(steam_root):
        common = library / "steamapps" / "common"
        for child in common.iterdir():
            if child.is_dir() and keyword_lower in child.name.lower():
                matches.append(child)
    if not matches:
        raise FileNotFoundError(f"未在 Steam common 目录中找到包含关键词的游戏目录：{keyword}")
    if len(matches) > 1:
        print("[INFO] 找到多个候选目录，使用第一个：", file=sys.stderr)
        for match in matches:
            print(f"  - {match}", file=sys.stderr)
    return matches[0]


def read_text_lenient(path: Path) -> str:
    data = path.read_bytes()
    for encoding in DECODINGS:
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="ignore")


def iter_files(target: Path) -> list[Path]:
    if target.is_file():
        return [target]
    files: list[Path] = []
    for path in target.rglob("*"):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        files.append(path)
    return sorted(files, key=lambda p: str(p).lower())


def decode_whole_text(data: bytes) -> tuple[str, str, bool]:
    for encoding in DECODINGS:
        try:
            text = data.decode(encoding)
        except UnicodeDecodeError:
            continue
        if printable_ratio(text) >= 0.82:
            return text, encoding, True
    return data.decode("utf-8", errors="ignore"), "utf-8-ignore", False


def printable_ratio(text: str) -> float:
    if not text:
        return 0.0
    printable = sum(1 for ch in text if ch in "\n\r\t" or not CONTROL_RE.search(ch))
    return printable / len(text)


def normalize_line(value: str) -> str:
    value = value.replace("\ufeff", "").replace("\x00", "")
    value = re.sub(r"\s+", " ", value).strip()
    return value


def is_meaningful(value: str, min_chars: int) -> bool:
    if len(value) < min_chars:
        return False
    if not MEANINGFUL_RE.search(value):
        return False
    control_count = len(CONTROL_RE.findall(value))
    return control_count / max(len(value), 1) < 0.05


def extract_from_plain_text(path: Path, rel: str, data: bytes, min_chars: int) -> tuple[list[ExtractedLine], str, str]:
    text, encoding, decoded_cleanly = decode_whole_text(data)
    lines: list[ExtractedLine] = []
    for line_no, raw_line in enumerate(text.splitlines(), start=1):
        line = normalize_line(raw_line)
        if is_meaningful(line, min_chars):
            lines.append(ExtractedLine(rel, line_no, encoding, line))
    note = "plain text" if decoded_cleanly else "decoded with replacement"
    return lines, encoding, note


def append_candidate(
    lines: list[ExtractedLine],
    seen: set[str],
    rel: str,
    encoding: str,
    raw: str,
    min_chars: int,
    limit: int,
    chinese_only: bool,
) -> bool:
    text = normalize_line(raw)
    if len(text) > 800:
        text = text[:800].rstrip() + " ..."
    if chinese_only and not CJK_RE.search(text):
        return len(lines) >= limit
    if not is_meaningful(text, min_chars) or text in seen:
        return len(lines) >= limit
    seen.add(text)
    lines.append(ExtractedLine(rel, None, encoding, text))
    return len(lines) >= limit


def iter_decoded_runs(decoded: str) -> list[str]:
    runs: list[str] = []
    for match in TEXT_RUN_RE.finditer(decoded):
        runs.extend(re.split(r"[\r\n\x00]+", match.group(0)))
    return runs


def extract_binary_candidates(
    path: Path,
    rel: str,
    data: bytes,
    min_chars: int,
    line_limit: int,
    chinese_only: bool,
) -> list[ExtractedLine]:
    seen: set[str] = set()
    lines: list[ExtractedLine] = []
    for match in ASCII_BYTES_RE.finditer(data):
        if append_candidate(lines, seen, rel, "binary-ascii", match.group(0).decode("utf-8", errors="ignore"), min_chars, line_limit, chinese_only):
            return lines

    for encoding in ("utf-8", "utf-16le", "utf-16be", "gb18030"):
        decoded = data.decode(encoding, errors="ignore")
        for raw in iter_decoded_runs(decoded):
            if append_candidate(lines, seen, rel, f"binary-{encoding}", raw, min_chars, line_limit, chinese_only):
                return lines
    return lines


def extract_large_binary_candidates(path: Path, rel: str, min_chars: int, line_limit: int, chinese_only: bool) -> list[ExtractedLine]:
    seen: set[str] = set()
    lines: list[ExtractedLine] = []
    overlap = b""
    with path.open("rb") as f:
        while True:
            block = f.read(CHUNK_SIZE)
            if not block:
                break
            data = overlap + block
            for match in ASCII_BYTES_RE.finditer(data):
                if append_candidate(lines, seen, rel, "binary-ascii", match.group(0).decode("utf-8", errors="ignore"), min_chars, line_limit, chinese_only):
                    return lines
            for encoding in ("utf-8", "utf-16le", "utf-16be", "gb18030"):
                decoded = data.decode(encoding, errors="ignore")
                for raw in iter_decoded_runs(decoded):
                    if append_candidate(lines, seen, rel, f"binary-{encoding}", raw, min_chars, line_limit, chinese_only):
                        return lines
            overlap = data[-CHUNK_OVERLAP:]
    return lines


def scan_file(
    path: Path,
    root: Path,
    max_file_mb: float,
    min_chars: int,
    include_binary: bool,
    max_binary_lines: int,
    chinese_only: bool,
) -> tuple[list[ExtractedLine], FileSummary]:
    rel = str(path.relative_to(root)) if root.is_dir() else path.name
    size = path.stat().st_size
    if size > int(max_file_mb * 1024 * 1024):
        return [], FileSummary(rel, size, "skipped", "", 0, f"larger than {max_file_mb:g} MB")
    ext = path.suffix.lower()
    if ext in SKIP_EXTENSIONS and not include_binary:
        return [], FileSummary(rel, size, "skipped", "", 0, "binary extension")
    if include_binary and ext not in TEXT_EXTENSIONS and size >= LARGE_BINARY_THRESHOLD:
        lines = extract_large_binary_candidates(path, rel, min_chars, max_binary_lines, chinese_only)
        note = "candidate strings from binary data, streamed in chunks"
        if chinese_only:
            note += "; filtered to lines containing CJK"
        if len(lines) >= max_binary_lines:
            note += f"; capped at {max_binary_lines} lines"
        return lines, FileSummary(rel, size, "binary-candidates", "", len(lines), note)
    data = path.read_bytes()
    if ext in TEXT_EXTENSIONS:
        lines, encoding, note = extract_from_plain_text(path, rel, data, min_chars)
        return lines, FileSummary(rel, size, "text", encoding, len(lines), note)
    text, encoding, decoded_cleanly = decode_whole_text(data)
    if decoded_cleanly and printable_ratio(text) >= 0.9:
        lines, _, note = extract_from_plain_text(path, rel, data, min_chars)
        return lines, FileSummary(rel, size, "text-detected", encoding, len(lines), note)
    lines = extract_binary_candidates(path, rel, data, min_chars, max_binary_lines, chinese_only) if include_binary else []
    mode = "binary-candidates" if include_binary else "skipped"
    note = "candidate strings from binary data" if include_binary else "unknown binary"
    if include_binary and chinese_only:
        note += "; filtered to lines containing CJK"
    if include_binary and len(lines) >= max_binary_lines:
        note += f"; capped at {max_binary_lines} lines"
    return lines, FileSummary(rel, size, mode, "", len(lines), note)


def write_outputs(lines: list[ExtractedLine], summaries: list[FileSummary], out_dir: Path, markdown_limit: int) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    jsonl_path = out_dir / "steam_text_dump.jsonl"
    md_path = out_dir / "steam_text_dump.md"
    manifest_path = out_dir / "steam_text_manifest.csv"

    with jsonl_path.open("w", encoding="utf-8", newline="\n") as f:
        for item in lines:
            f.write(json.dumps(item.__dict__, ensure_ascii=False) + "\n")

    by_file: dict[str, list[ExtractedLine]] = {}
    for item in lines:
        by_file.setdefault(item.source, []).append(item)

    with md_path.open("w", encoding="utf-8", newline="\n") as f:
        f.write("# Steam Text Dump\n\n")
        f.write("JSONL contains all extracted lines. This Markdown file is a readable preview.\n\n")
        for source in sorted(by_file):
            f.write(f"## {source}\n\n")
            for item in by_file[source][:markdown_limit]:
                prefix = f"L{item.line}: " if item.line else ""
                f.write(f"- `{item.encoding}` {prefix}{item.text}\n")
            extra = len(by_file[source]) - markdown_limit
            if extra > 0:
                f.write(f"\n_... {extra} more lines in steam_text_dump.jsonl_\n")
            f.write("\n")

    with manifest_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["path", "size", "mode", "encoding", "count", "note"])
        writer.writeheader()
        for item in summaries:
            writer.writerow(item.__dict__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract readable text candidates from a local Steam game directory.")
    parser.add_argument("target", nargs="?", help="Game directory or one file to scan.")
    parser.add_argument("--game-keyword", help="Find a Steam game folder whose name contains this keyword.")
    parser.add_argument("--steam-root", help="Steam install root, for example C:\\Program Files (x86)\\Steam.")
    parser.add_argument("--out", default=str(ROOT / "steam_text_dump"), help="Output directory.")
    parser.add_argument("--max-file-mb", type=float, default=25.0, help="Skip files larger than this size.")
    parser.add_argument("--min-chars", type=int, default=4, help="Minimum extracted line length.")
    parser.add_argument("--include-binary", action="store_true", help="Also scan unknown binary files for readable strings.")
    parser.add_argument("--markdown-limit-per-file", type=int, default=300, help="Preview line limit per file in Markdown.")
    parser.add_argument("--max-binary-lines-per-file", type=int, default=80000, help="Safety cap for candidate strings from one binary file.")
    parser.add_argument("--chinese-only", action="store_true", help="For binary scans, keep only candidate strings containing CJK characters.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.target:
        target = Path(args.target)
    elif args.game_keyword:
        target = locate_game(args.game_keyword, Path(args.steam_root) if args.steam_root else None)
    else:
        print("[ERROR] 请提供游戏目录，或使用 --game-keyword 自动查找。", file=sys.stderr)
        return 2
    if not target.exists():
        print(f"[ERROR] 路径不存在：{target}", file=sys.stderr)
        return 2

    root = target if target.is_dir() else target.parent
    all_lines: list[ExtractedLine] = []
    summaries: list[FileSummary] = []
    files = iter_files(target)
    for path in files:
        try:
            lines, summary = scan_file(
                path,
                root,
                args.max_file_mb,
                args.min_chars,
                args.include_binary,
                args.max_binary_lines_per_file,
                args.chinese_only,
            )
        except Exception as exc:
            rel = str(path.relative_to(root)) if root.is_dir() else path.name
            lines = []
            summary = FileSummary(rel, path.stat().st_size, "error", "", 0, str(exc))
        all_lines.extend(lines)
        summaries.append(summary)

    out_dir = Path(args.out)
    write_outputs(all_lines, summaries, out_dir, args.markdown_limit_per_file)
    print(f"[OK] scanned files={len(files)}, extracted lines={len(all_lines)}")
    print(f"[OK] output: {out_dir.resolve()}")
    print("[OK] files: steam_text_dump.jsonl, steam_text_dump.md, steam_text_manifest.csv")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
