#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""用本地 faster-whisper 把音频转写成 srt 字幕（供 extract_subtitle_candidates.py 消费）。
模型用 whisper-openai-shim 自带的 faster-whisper-base。
用法: python tools/asr_to_srt.py <音频> --out <srt> [--model base|small] [--duration 秒]
"""
import argparse
import sys
from pathlib import Path

MODEL_DIR = Path("C:/Users/cunyi/.workbuddy/skills/whisper-openai-shim/models")


def ts(sec: float) -> str:
    h = int(sec // 3600); m = int((sec % 3600) // 60); s = sec % 60
    return f"{h:02d}:{m:02d}:{s:06.3f}".replace(".", ",")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("audio")
    ap.add_argument("--out", required=True)
    ap.add_argument("--model", default="base")
    ap.add_argument("--duration", type=int, default=0, help="只转写前N秒，0=全部")
    ap.add_argument("--language", default="zh")
    args = ap.parse_args()

    try:
        from faster_whisper import WhisperModel
    except ImportError:
        print("[ERROR] 需要 faster-whisper，请用 envs/default 的 python 运行", file=sys.stderr)
        return 1

    model_path = MODEL_DIR / f"faster-whisper-{args.model}"
    if not model_path.exists():
        print(f"[ERROR] 模型不存在：{model_path}", file=sys.stderr)
        return 1

    print(f"[INFO] 加载模型 {model_path.name} ...")
    model = WhisperModel(str(model_path), device="cpu", compute_type="int8")

    kw = {"language": args.language} if args.language != "auto" else {}
    if args.duration:
        kw["clip_timestamps"] = f"0,{args.duration}"
    segments, info = model.transcribe(args.audio, beam_size=5, **kw)
    print(f"[INFO] 检测语言 {info.language}，时长 {info.duration:.0f}s")

    lines = []
    for i, seg in enumerate(segments, 1):
        text = seg.text.strip()
        if not text:
            continue
        lines.append(f"{i}\n{ts(seg.start)} --> {ts(seg.end)}\n{text}\n")

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"[OK] {len(lines)} 条字幕 -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
