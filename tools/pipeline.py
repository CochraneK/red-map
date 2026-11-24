#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""红军长征星火路线 · 统一构建与验收流水线。

用法：
    python tools/pipeline.py          # 全套：反推引用 -> 生成 JSON 与口径差异 -> 生成 REFERENCES.md -> 硬门禁验收
    python tools/pipeline.py --skip-check  # 仅构建不验收（开发调试用）
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run_step(title: str, script: str, *extra: str) -> None:
    print(f"\n=== [{title}] python {script} {' '.join(extra)} ===".rstrip())
    res = subprocess.run([sys.executable, script, *extra], cwd=ROOT)
    if res.returncode != 0:
        raise SystemExit(f"[PIPELINE FAILED] {title} exited with code {res.returncode}")


def main() -> int:
    parser = argparse.ArgumentParser(description="统一构建发布数据、参考书目与运行全套硬门禁检查")
    parser.add_argument("--skip-check", action="store_true", help="跳过 check_project.py 硬门禁检查")
    args = parser.parse_args()

    run_step("1/5 反向汇总来源引用位置与频次", "tools/build_cited_details.py")
    run_step("2/5 更新县镇级历史地名词典 gazetteer.csv", "tools/build_gazetteer.py")
    run_step("3/5 构建发布 JSON 与口径差异组", "tools/build_json_from_tables.py")
    run_step("4/5 生成学术规范参考书目 REFERENCES.md", "tools/build_references_md.py")
    if not args.skip_check:
        run_step("5/5 运行全套硬门禁与一致性验收", "tools/check_project.py")

    print("\n[PIPELINE OK] 全流程构建与验收通过。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
