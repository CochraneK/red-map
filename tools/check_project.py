#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Run the lightweight project checks used before publishing.

The project intentionally has no package manager setup. This script keeps the
repeatable checks in one place so GitHub Pages data and the table source stay in
sync.
"""
from __future__ import annotations

import csv
import json
import math
import re
import shutil
import subprocess
import sys
import tempfile
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


GAME_SOURCE_ID = "src_steam_longmarch_1934_1936"
VALID_CERTAINTIES = {"high", "medium", "low"}
VALID_LAYERS = {"march", "spark_march", "theme_stat", "historiography"}
VALID_DATE_PRECISIONS = {"day", "month", "range", "approx"}
VALID_EVENT_TYPES = {"战斗", "行军", "决策", "渡险", "会师", "牺牲", "民生", "史料"}
# 经人工考据核验的真实长距离跨越（>300km）白名单：(prev_event_id, next_event_id)
ALLOWED_MARCH_JUMPS = {
    ("r2_19360328_wumeng", "r2_19360425_shigu"),  # 红二、六军团1936年3月28日至4月25日横穿滇中至石鼓（28天392km）
}
GENERIC_LICENSE_VALUES = {
    "",
    "see file page",
    "see source page",
    "unknown",
    "tbd",
    "todo",
}


def read_csv_rows(relative: str) -> list[dict[str, str]]:
    path = ROOT / relative
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [
            {str(key or "").strip(): str(value or "").strip() for key, value in row.items() if key is not None}
            for row in csv.DictReader(handle)
        ]


def split_refs(value: str) -> list[str]:
    return [part.strip() for part in re.split(r"[;；,，|｜]+", value or "") if part.strip()]


def check_source_provenance_policy() -> None:
    print("[CHECK] candidate-source certainty policy")
    violations: list[str] = []
    game_only = 0
    for row in read_csv_rows("data_edit/events.csv"):
        if str(row.get("enabled", "TRUE")).strip().lower() in {"false", "0", "no", "n", "否", "禁用"}:
            continue
        refs = split_refs(row.get("sourceIds", ""))
        if refs == [GAME_SOURCE_ID]:
            game_only += 1
            if row.get("certainty", "").strip().lower() != "low":
                violations.append(row.get("id") or row.get("title") or "<unnamed>")
    if violations:
        sample = ", ".join(violations[:10])
        raise RuntimeError(
            f"{len(violations)} 个仅由游戏文本来源支持的事件未保持 certainty=low。示例：{sample}"
        )
    print(f"[OK] game-only candidate events keep low certainty: {game_only}")


def check_non_authoritative_certainty() -> None:
    """certainty=high 的事件必须至少有一条 sourceType=authoritative 的权威来源支撑。"""
    print("[CHECK] non-authoritative source certainty ceiling")
    src_types: dict[str, str] = {}
    for row in read_csv_rows("data_edit/sources.csv"):
        sid = str(row.get("id", "")).strip()
        if sid:
            src_types[sid] = str(row.get("sourceType", "") or "authoritative").strip().lower()
    violations: list[str] = []
    checked = 0
    for row in read_csv_rows("data_edit/events.csv"):
        if str(row.get("enabled", "TRUE")).strip().lower() in {"false", "0", "no", "n", "否", "禁用"}:
            continue
        if str(row.get("certainty", "")).strip().lower() != "high":
            continue
        refs = split_refs(row.get("sourceIds", ""))
        checked += 1
        if not refs:
            violations.append(row.get("id") or row.get("title") or "<unnamed>")
            continue
        types = {src_types.get(r, "authoritative") for r in refs}
        if "authoritative" not in types:
            violations.append(row.get("id") or row.get("title") or "<unnamed>")
    if violations:
        sample = ", ".join(violations[:10])
        raise RuntimeError(
            f"{len(violations)} 个无权威来源支撑的事件错误地标为 certainty=high。示例：{sample}"
        )
    print(f"[OK] all {checked} certainty=high events have authoritative source support")


def _haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = math.radians(lat2 - lat1), math.radians(lng2 - lng1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(min(1.0, a)))


def check_event_schema_and_cleanliness() -> None:
    """严格校验 certainty/layer/datePrecision/type 枚举与 locationName 洁净度。"""
    print("[CHECK] event schema enums & locationName cleanliness")
    enum_errors: list[str] = []
    dirty_locs: list[str] = []
    enabled_count = 0
    for row in read_csv_rows("data_edit/events.csv"):
        if str(row.get("enabled", "TRUE")).strip().lower() in {"false", "0", "no", "n", "否", "禁用"}:
            continue
        enabled_count += 1
        eid = row.get("id") or "<unnamed>"
        cert = row.get("certainty", "").strip().lower()
        layer = row.get("layer", "").strip()
        prec = row.get("datePrecision", "").strip().lower()
        etype = row.get("type", "").strip()
        if cert not in VALID_CERTAINTIES:
            enum_errors.append(f"{eid}: certainty={cert!r}")
        if layer not in VALID_LAYERS:
            enum_errors.append(f"{eid}: layer={layer!r}")
        if prec not in VALID_DATE_PRECISIONS:
            enum_errors.append(f"{eid}: datePrecision={prec!r}")
        if etype not in VALID_EVENT_TYPES:
            enum_errors.append(f"{eid}: type={etype!r}")
        loc = row.get("locationName", "").strip()
        if not loc or len(loc) > 24 or any(ch in loc for ch in ('"', "《", "》", "——")):
            dirty_locs.append(f"{eid}: {loc!r}")
    if enum_errors:
        raise RuntimeError(f"事件枚举值违规（{len(enum_errors)}处）：" + "; ".join(enum_errors[:8]))
    if dirty_locs:
        raise RuntimeError(f"locationName 不洁净（{len(dirty_locs)}处）：" + "; ".join(dirty_locs[:8]))
    print(f"[OK] {enabled_count} enabled events pass strict enum & locationName checks")


def check_march_route_jumps(data: dict) -> None:
    """核心长征行军层（layer=march，非敌军）相邻节点跨度 >300km 硬门禁。"""
    print("[CHECK] core march route geographic continuity (>300km gate)")
    enemy_ids = {s["id"] for s in data.get("subjects", []) if s.get("isEnemy")}
    by_force: dict[str, list[dict]] = defaultdict(list)
    for ev in data.get("events", []):
        if ev.get("layer", "march") != "march":
            continue
        if ev.get("forceId") in enemy_ids:
            continue
        by_force[ev["forceId"]].append(ev)

    bad: list[str] = []
    whitelisted = 0
    for fid, evs in sorted(by_force.items()):
        evs.sort(key=lambda e: (e["date"], int(e.get("sequence") or 0), e["id"]))
        for a, b in zip(evs, evs[1:]):
            c1 = a["location"]["coordinates"]
            c2 = b["location"]["coordinates"]
            dist = _haversine_km(float(c1[0]), float(c1[1]), float(c2[0]), float(c2[1]))
            if dist > 300.0:
                if (a["id"], b["id"]) in ALLOWED_MARCH_JUMPS:
                    whitelisted += 1
                    continue
                bad.append(
                    f"{fid} {dist:.0f}km: {a['id']}({a['date']},{a['location']['name']}) -> "
                    f"{b['id']}({b['date']},{b['location']['name']})"
                )
    if bad:
        raise RuntimeError(f"核心行军层存在 {len(bad)} 处未授权 >300km 异常跳点：\n  " + "\n  ".join(bad[:10]))
    print(f"[OK] core march layer has 0 abnormal jumps (>300km); whitelisted genuine spans: {whitelisted}")


def check_subjects_and_sources_hygiene() -> None:
    """禁止 subjects.csv 残留 type=person 行；禁止 sources.csv 出现重复标题。"""
    print("[CHECK] subjects & sources hygiene")
    legacy_persons = [
        r.get("id") or "<unnamed>"
        for r in read_csv_rows("data_edit/subjects.csv")
        if r.get("type", "").strip().lower() == "person"
    ]
    if legacy_persons:
        raise RuntimeError(f"subjects.csv 残留 {len(legacy_persons)} 行 type=person：{', '.join(legacy_persons[:6])}")

    seen_titles: dict[str, str] = {}
    dups: list[str] = []
    for r in read_csv_rows("data_edit/sources.csv"):
        t = r.get("title", "").strip()
        sid = r.get("id", "").strip()
        if t in seen_titles:
            dups.append(f"{t!r} ({seen_titles[t]} & {sid})")
        elif t:
            seen_titles[t] = sid
    if dups:
        raise RuntimeError(f"sources.csv 存在重复标题：" + "; ".join(dups[:6]))
    print("[OK] subjects has no legacy person rows; sources titles are unique")


def check_visual_asset_provenance() -> None:
    print("[CHECK] visual asset provenance metadata")
    unresolved: list[str] = []
    missing_page: list[str] = []
    external = 0
    for row in read_csv_rows("data_edit/visual_assets.csv"):
        if str(row.get("enabled", "TRUE")).strip().lower() in {"false", "0", "no", "n", "否", "禁用"}:
            continue
        page = row.get("imagePageUrl", "").strip()
        license_value = row.get("license", "").strip()
        credit = row.get("credit", "").strip()
        if not page:
            # Project-authored/local screenshots may intentionally have no external source page.
            if license_value.lower() != "project asset":
                missing_page.append(row.get("id") or "<unnamed>")
            continue
        external += 1
        if not credit or license_value.lower() in GENERIC_LICENSE_VALUES:
            unresolved.append(row.get("id") or "<unnamed>")
    if missing_page:
        sample = ", ".join(missing_page[:8])
        print(
            f"[WARN] {len(missing_page)} visual assets have no source page and are not marked project asset. "
            f"Sample: {sample}"
        )
    if unresolved:
        sample = ", ".join(unresolved[:8])
        print(
            f"[WARN] {len(unresolved)}/{external} external visual assets still have unresolved exact "
            f"credit/license metadata. Sample: {sample}"
        )
    else:
        print(f"[OK] exact credit/license metadata present for {external} external visual assets")


def check_source_registry_metadata() -> None:
    print("[CHECK] source registry metadata")
    missing: list[str] = []
    for row in read_csv_rows("data_edit/sources.csv"):
        sid = row.get("id", "") or "<unnamed>"
        absent = [field for field in ("id", "title", "publisher", "url") if not row.get(field, "").strip()]
        if absent:
            missing.append(f"{sid}({','.join(absent)})")
    if missing:
        sample = ", ".join(missing[:8])
        raise RuntimeError(f"来源登记缺少必要元数据：{sample}")
    print("[OK] source registry has id/title/publisher/url metadata")


def check_required_files() -> None:
    print("[CHECK] required project files")
    required = [
        "AGENTS.md",
        "HANDOFF.md",
        "STATUS.md",
        "DECISIONS.md",
        "PROVENANCE_STATUS.md",
        "docs/architecture.md",
        "index.html",
        "explore.html",
        "map.html",
        "index-en.html",
        "museum.html",
        "museum-immersive.html",
        "css/style.css",
        "css/museum.css",
        "css/immersive.css",
        "css/explore.css",
        "js/app.js",
        "js/museum.js",
        "js/immersive.js",
        "js/explore.js",
        "admin/index.html",
        "data_edit/sources.csv",
        "data_edit/events.csv",
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
    run([node, "--check", "js/explore.js"])


def check_python_syntax() -> None:
    py_files = sorted(str(p.relative_to(ROOT)) for p in (ROOT / "tools").glob("*.py"))
    run([sys.executable, "-m", "py_compile", *py_files])


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
        check_source_registry_metadata()
        check_subjects_and_sources_hygiene()
        check_event_schema_and_cleanliness()
        check_march_route_jumps(data)
        check_source_provenance_policy()
        check_non_authoritative_certainty()
        check_visual_asset_provenance()
        check_translation_placeholders(data)
    except Exception as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1
    print("[OK] project checks completed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
