#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Run the lightweight project checks used before publishing.

The project intentionally has no package manager setup. This script keeps the
repeatable checks in one place so GitHub Pages data and the table source stay in
sync.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def check_required_files() -> None:
    print("[CHECK] required project files")
    required = [
        "index.html",
        "index-en.html",
        "museum.html",
        "museum-immersive.html",
        "css/style.css",
        "css/museum.css",
        "css/immersive.css",
        "js/app.js",
        "js/museum.js",
        "js/immersive.js",
        "admin/index.html",
        "data_edit/persons.csv",
        "data_edit/person_events.csv",
        "data_edit/museum_halls.csv",
        "data_edit/exhibits.csv",
        "data_edit/artifacts.csv",
        "data_edit/visual_assets.csv",
        "tools/extract_steam_texts.py",
        "tools/extract_unreal_text_assets.py",
        "tools/import_steam_timeline.py",
    ]
    missing = [rel for rel in required if not (ROOT / rel).exists()]
    if missing:
        raise RuntimeError("缺少必要文件：" + ", ".join(missing))
    print("[OK] required files exist")


def run(cmd: list[str]) -> None:
    print(f"[CHECK] {' '.join(cmd)}")
    completed = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True)
    if completed.stdout:
        print(completed.stdout.strip())
    if completed.stderr:
        print(completed.stderr.strip(), file=sys.stderr)
    if completed.returncode:
        raise RuntimeError(f"命令失败：{' '.join(cmd)}")


def check_json() -> dict:
    path = ROOT / "data" / "long_march_events.json"
    print(f"[CHECK] JSON parse: {path.relative_to(ROOT)}")
    data = json.loads(path.read_text(encoding="utf-8"))
    for key in ("subjects", "sources", "events", "persons", "personEvents", "museum"):
        if not isinstance(data.get(key), list):
            if key == "museum" and isinstance(data.get(key), dict):
                continue
            raise RuntimeError(f"{path} 缺少字段或字段类型错误：{key}")
    museum = data.get("museum", {})
    for key in ("halls", "exhibits", "artifacts", "visualAssets"):
        if not isinstance(museum.get(key), list):
            raise RuntimeError(f"{path} 缺少 museum.{key} 数组")
    print(
        "[OK] data counts: "
        f"subjects={len(data['subjects'])}, sources={len(data['sources'])}, events={len(data['events'])}, "
        f"persons={len(data['persons'])}, halls={len(museum['halls'])}, visuals={len(museum['visualAssets'])}"
    )
    return data


def check_generated_json_matches() -> None:
    with tempfile.TemporaryDirectory(prefix="red-map-check-") as tmp:
        out = Path(tmp) / "long_march_events.json"
        run([sys.executable, "tools/build_json_from_tables.py", "--out", str(out)])
        generated = json.loads(out.read_text(encoding="utf-8"))
    current = json.loads((ROOT / "data" / "long_march_events.json").read_text(encoding="utf-8"))
    if generated != current:
        raise RuntimeError("data_edit/*.csv 生成的 JSON 与 data/long_march_events.json 不一致")
    print("[OK] table source reproduces published JSON")


def check_js_syntax() -> None:
    node = shutil.which("node")
    if not node:
        print("[WARN] 未找到 node，跳过 JS 语法检查")
        return
    run([node, "--check", "js/app.js"])
    run([node, "--check", "admin/admin.js"])
    run([node, "--check", "js/museum.js"])
    run([node, "--check", "js/immersive.js"])


def check_python_syntax() -> None:
    run([
        sys.executable,
        "-m",
        "py_compile",
        "tools/build_json_from_tables.py",
        "tools/check_project.py",
        "tools/extract_steam_texts.py",
        "tools/extract_unreal_text_assets.py",
        "tools/import_steam_timeline.py",
    ])


def check_inline_handlers_removed() -> None:
    print("[CHECK] admin inline event handlers")
    offenders: list[str] = []
    for rel in ("admin/index.html", "admin/admin.js"):
        path = ROOT / rel
        text = path.read_text(encoding="utf-8")
        for pattern in ("onclick=", "window.openEventModal", "window.deleteEvent", "window.openSubjectModal", "window.deleteSubject"):
            if pattern in text:
                offenders.append(f"{rel}: contains {pattern}")
    if offenders:
        raise RuntimeError("\n".join(offenders))
    print("[OK] admin actions use delegated listeners")


def check_translation_placeholders(data: dict) -> None:
    print("[CHECK] English placeholder fields")
    placeholders = [
        event["id"]
        for event in data.get("events", [])
        if "This node marks" in str(event.get("descriptionEn", ""))
    ]
    if placeholders:
        sample = ", ".join(placeholders[:8])
        print(f"[WARN] {len(placeholders)} events still use generated English placeholders. Sample: {sample}")
    else:
        print("[OK] no generated English placeholder descriptions")


def main() -> int:
    try:
        check_required_files()
        data = check_json()
        check_generated_json_matches()
        check_python_syntax()
        check_js_syntax()
        check_inline_handlers_removed()
        check_translation_placeholders(data)
    except Exception as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1
    print("[OK] project checks completed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
