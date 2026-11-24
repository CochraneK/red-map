#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
书籍 / 回忆录 / 地方志 候选线索抽取器。

设计原则：
1. 只产出"候选线索"，输出到 research_private/，绝不直接写入 data_edit 正式表。
2. 支持三种输入：有文本层的 PDF、纯 TXT、已 OCR 的逐页文本 (.txt，每页一段)。
3. 按"人物/地点/事件"关键词窗口切段，保留页码/字符位置，便于人工溯源。
4. 扫描件 PDF 无文本层时会明确提示需要先 OCR（本脚本不内置 OCR 引擎）。

用法：
  python tools/extract_book_candidates.py <输入文件或目录> --out research_private/book_candidates \\
      --source-name "绥德州志" --source-type book
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path

# 事件/人物/地点线索锚点：命中后取其上下文窗口作为候选
ANCHORS = [
    r"长征", r"红军", r"苏区", r"根据地", r"游击", r"起义", r"战役", r"战斗",
    r"会师", r"渡河", r"渡江", r"会议", r"牺牲", r"烈士", r"围剿", r"讨伐",
    r"毛泽东", r"周恩来", r"朱德", r"刘志丹", r"谢子长", r"习仲勋", r"冯白驹",
    r"杨靖宇", r"董振堂", r"张国焘", r"徐向前", r"李先念", r"程世才",
    r"绥德", r"米脂", r"佳县", r"吴堡", r"清涧", r"子长", r"延长", r"延川",
    r"照金", r"南梁", r"反'围剿'", r"肃反", r"扩红", r"支前",
]
ANCHOR_RE = re.compile("|".join(ANCHORS))

# 日期锚点：民国纪年/干支/农历不易解析，这里只抓明确公元年份与"年月"
DATE_RE = re.compile(r"(?:19[0-4]\d|民国\d{1,2})年(?:\d{1,2}月)?(?:\d{1,2}日)?")


def read_pdf_text(path: Path) -> tuple[list[str], str]:
    try:
        import fitz  # PyMuPDF
    except ImportError:
        return [], "缺少 PyMuPDF，无法读取 PDF 文本层"
    doc = fitz.open(path)
    pages: list[str] = []
    empty = 0
    for i, page in enumerate(doc):
        text = page.get_text().strip()
        if not text:
            empty += 1
        pages.append(text)
    note = ""
    if empty > len(pages) * 0.8:
        note = f"扫描件：{empty}/{len(pages)} 页无文本层，需先 OCR"
    return pages, note


def read_txt_pages(path: Path) -> tuple[list[str], str]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    # 支持以空行分段（OCR 常按页分段）
    pages = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    if not pages:
        pages = [text]
    return pages, ""


def extract_candidates(pages: list[str], source_name: str, source_type: str,
                       window: int, max_per_file: int) -> list[dict]:
    out: list[dict] = []
    for pno, text in enumerate(pages, start=1):
        if not text:
            continue
        for m in ANCHOR_RE.finditer(text):
            s = max(0, m.start() - window // 2)
            e = min(len(text), m.end() + window // 2)
            snippet = re.sub(r"\s+", " ", text[s:e]).strip()
            if len(snippet) < 12:
                continue
            dates = DATE_RE.findall(snippet)
            out.append({
                "id": f"cand_{source_type}_{len(out)+1:05d}",
                "sourceName": source_name,
                "sourceType": source_type,
                "page": pno,
                "anchor": m.group(0),
                "dateHints": ";".join(dates[:3]),
                "snippet": snippet,
                "certaintySuggestion": "medium",  # 书籍需人工复核后才升 high
                "reviewStatus": "pending",
            })
            if len(out) >= max_per_file:
                return out
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="书籍/地方志候选线索抽取")
    ap.add_argument("target", help="输入文件或目录")
    ap.add_argument("--out", required=True, help="输出目录（应在 research_private 下）")
    ap.add_argument("--source-name", default="", help="来源显示名")
    ap.add_argument("--source-type", default="book",
                    choices=["book", "memoir", "gazetteer", "ocr_text"],
                    help="来源类型")
    ap.add_argument("--window", type=int, default=160, help="上下文窗口字符数")
    ap.add_argument("--max-per-file", type=int, default=3000, help="每个文件最多候选数")
    args = ap.parse_args()

    target = Path(args.target)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    files: list[Path] = []
    if target.is_dir():
        for p in sorted(target.rglob("*")):
            if p.suffix.lower() in {".pdf", ".txt"}:
                files.append(p)
    elif target.is_file():
        files = [target]
    else:
        print(f"[ERROR] 输入不存在：{target}", file=sys.stderr)
        return 1

    all_candidates: list[dict] = []
    for f in files:
        name = args.source_name or f.stem
        if f.suffix.lower() == ".pdf":
            pages, note = read_pdf_text(f)
        else:
            pages, note = read_txt_pages(f)
        if note:
            print(f"[SKIP] {f.name}: {note}")
            continue
        cands = extract_candidates(pages, name, args.source_type,
                                   args.window, args.max_per_file)
        all_candidates.extend(cands)
        print(f"[OK] {f.name}: {len(pages)} 页 → {len(cands)} 条候选")

    if not all_candidates:
        print("[WARN] 无候选产出。若是扫描件 PDF，请先 OCR 后以 TXT 输入。")
        return 0

    csv_path = out_dir / "book_candidates.csv"
    with open(csv_path, "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(all_candidates[0].keys()))
        w.writeheader(); w.writerows(all_candidates)

    md_path = out_dir / "book_candidates_preview.md"
    with open(md_path, "w", encoding="utf-8") as fh:
        fh.write(f"# {args.source_name or target.name} 候选线索（{len(all_candidates)} 条）\n\n")
        fh.write("> 候选线索，非史实。人工复核并补权威来源后方可进入 data_edit 正式表。\n\n")
        for c in all_candidates[:200]:
            fh.write(f"- **[{c['id']}]** p{c['page']} · 锚点「{c['anchor']}」· 日期提示：{c['dateHints'] or '无'}\n")
            fh.write(f"  {c['snippet'][:200]}\n")
    print(f"[OK] 输出 {csv_path}（{len(all_candidates)} 条）")
    print(f"[OK] 预览 {md_path}")
    print("[NOTE] 候选不自动入库；复核后经 import_sourced_research.py 类似流程写入。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
