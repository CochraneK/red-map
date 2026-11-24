#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
视频字幕候选抽取器（srt / vtt / ass）＋ ASR 转写接入点。

设计原则：
1. 字幕属于"公众叙事"层，不是史料：输出 sourceType=subtitle、certainty=public_narrative。
2. 按时间轴切段：把相邻字幕行合并成"语义块"，命中人物/事件锚点才产出候选。
3. 保留 start/end 时间戳，方便回到视频复核。
4. ASR：可选传入已转写的 srt（由外部 whisper/ASR 生成），本脚本不内置引擎。

用法：
  python tools/extract_subtitle_candidates.py <字幕文件或目录> --out research_private/subtitle_candidates \\
      --source-name "某纪录片" --source-type subtitle|public_narrative
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path

ANCHORS = [
    r"长征", r"红军", r"苏区", r"根据地", r"会师", r"渡河", r"渡江", r"雪山", r"草地",
    r"遵义", r"于都", r"湘江", r"赤水", r"泸定", r"会宁", r"西路军", r"抗联",
    r"毛泽东", r"周恩来", r"朱德", r"刘志丹", r"谢子长", r"杨靖宇", r"赵一曼",
    r"董振堂", r"徐向前", r"李先念", r"冯白驹", r"曾生", r"方志敏", r"寻淮洲",
    r"起义", r"战役", r"牺牲", r"烈士", r"围剿", r"突围", r"转移",
]
ANCHOR_RE = re.compile("|".join(ANCHORS))
DATE_RE = re.compile(r"(?:19[0-4]\d)年(?:\d{1,2}月)?(?:\d{1,2}日)?")

TS_SRT = re.compile(r"(\d{2}:\d{2}:\d{2}[,.]\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}[,.]\d{3})")
TS_VTT = TS_SRT
TS_ASS = re.compile(r"Dialogue:\s*[^,]+,\s*(\d+:\d{2}:\d{2}\.\d{2}),\s*(\d+:\d{2}:\d{2}\.\d{2})")


def parse_srt_vtt(text: str) -> list[tuple[str, str, str]]:
    items: list[tuple[str, str, str]] = []
    blocks = re.split(r"\n\s*\n", text.replace("\r", ""))
    for b in blocks:
        m = TS_SRT.search(b)
        if not m:
            continue
        lines = [ln.strip() for ln in b.split("\n") if ln.strip()]
        # 去掉序号行
        content = [ln for ln in lines if not re.fullmatch(r"\d+", ln) and TS_SRT.search(ln) is None]
        body = " ".join(content)
        body = re.sub(r"\{[^}]*\}", "", body)  # 去内联样式
        if body:
            items.append((m.group(1).replace(",", "."), m.group(2).replace(",", "."), body))
    return items


def parse_ass(text: str) -> list[tuple[str, str, str]]:
    items: list[tuple[str, str, str]] = []
    for line in text.replace("\r", "").split("\n"):
        if not line.startswith("Dialogue:"):
            continue
        m = TS_ASS.search(line)
        if not m:
            continue
        parts = line.split(",", 9)
        if len(parts) < 10:
            continue
        body = re.sub(r"\{[^}]*\}", "", parts[9]).strip().replace("\\N", " ")
        if body:
            items.append((m.group(1), m.group(2), body))
    return items


def merge_blocks(items: list[tuple[str, str, str]], gap_sec: int, max_chars: int):
    """把时间上接近的字幕行合并成语义块。"""
    def to_sec(ts: str) -> float:
        p = ts.split(":")
        try:
            return int(p[0]) * 3600 + int(p[1]) * 60 + float(p[2])
        except Exception:
            return 0.0

    blocks: list[dict] = []
    cur_start = cur_end = 0.0
    cur_texts: list[str] = []
    for s, e, t in items:
        st, en = to_sec(s), to_sec(e)
        if cur_texts and st - cur_end > gap_sec:
            blocks.append({"start": cur_start, "end": cur_end, "text": " ".join(cur_texts)})
            cur_texts = []
        if not cur_texts:
            cur_start = st
        cur_end = en
        cur_texts.append(t)
        if sum(len(x) for x in cur_texts) > max_chars:
            blocks.append({"start": cur_start, "end": cur_end, "text": " ".join(cur_texts)})
            cur_texts = []
    if cur_texts:
        blocks.append({"start": cur_start, "end": cur_end, "text": " ".join(cur_texts)})
    return blocks


def fmt_ts(sec: float) -> str:
    h = int(sec // 3600); m = int((sec % 3600) // 60); s = int(sec % 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def extract(blocks: list[dict], source_name: str, source_type: str, max_items: int) -> list[dict]:
    out: list[dict] = []
    for b in blocks:
        if not ANCHOR_RE.search(b["text"]):
            continue
        dates = DATE_RE.findall(b["text"])
        out.append({
            "id": f"cand_sub_{len(out)+1:05d}",
            "sourceName": source_name,
            "sourceType": source_type,
            "start": fmt_ts(b["start"]),
            "end": fmt_ts(b["end"]),
            "dateHints": ";".join(dates[:3]),
            "text": b["text"][:400],
            "certaintySuggestion": "public_narrative",
            "reviewStatus": "pending",
        })
        if len(out) >= max_items:
            break
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="字幕候选抽取（字幕=公众叙事层）")
    ap.add_argument("target")
    ap.add_argument("--out", required=True)
    ap.add_argument("--source-name", default="")
    ap.add_argument("--source-type", default="subtitle",
                    choices=["subtitle", "public_narrative", "asr_transcript"])
    ap.add_argument("--gap", type=int, default=3, help="合并字幕的时间间隔（秒）")
    ap.add_argument("--max-chars", type=int, default=240, help="单个语义块最大字符数")
    ap.add_argument("--max-items", type=int, default=2000)
    args = ap.parse_args()

    target = Path(args.target)
    out_dir = Path(args.out); out_dir.mkdir(parents=True, exist_ok=True)
    files: list[Path] = []
    if target.is_dir():
        files = [p for p in sorted(target.rglob("*"))
                 if p.suffix.lower() in {".srt", ".vtt", ".ass", ".ssa"}]
    elif target.is_file():
        files = [target]
    else:
        print(f"[ERROR] 输入不存在：{target}", file=sys.stderr); return 1

    all_out: list[dict] = []
    for f in files:
        text = f.read_text(encoding="utf-8-sig", errors="ignore")
        if f.suffix.lower() in {".ass", ".ssa"}:
            items = parse_ass(text)
        else:
            items = parse_srt_vtt(text)
        blocks = merge_blocks(items, args.gap, args.max_chars)
        cands = extract(blocks, args.source_name or f.stem, args.source_type, args.max_items)
        all_out.extend(cands)
        print(f"[OK] {f.name}: {len(items)} 条字幕 → {len(blocks)} 块 → {len(cands)} 候选")

    if not all_out:
        print("[WARN] 无候选产出（可能无匹配锚点或非字幕格式）。")
        return 0

    csv_path = out_dir / "subtitle_candidates.csv"
    with open(csv_path, "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(all_out[0].keys()))
        w.writeheader(); w.writerows(all_out)
    md_path = out_dir / "subtitle_candidates_preview.md"
    with open(md_path, "w", encoding="utf-8") as fh:
        fh.write(f"# 字幕候选线索（{len(all_out)} 条）\n\n")
        fh.write("> 字幕属公众叙事层，非史料。不得标 certainty=high；复核并补权威来源后方可入库。\n\n")
        for c in all_out[:200]:
            fh.write(f"- **[{c['id']}]** {c['start']}–{c['end']} · 日期提示：{c['dateHints'] or '无'}\n  {c['text'][:180]}\n")
    print(f"[OK] 输出 {csv_path}（{len(all_out)} 条）")
    print("[NOTE] ASR 转写：先用外部 whisper 等生成 srt，再以 --source-type asr_transcript 输入本脚本。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
