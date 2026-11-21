#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""扩展证据等级体系：sources 加 sourceType；certainty 增加 public_narrative。
幂等，可重复运行。所有原有行保持兼容（空 sourceType 视为 authoritative）。
"""
import csv
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
EDIT = BASE / "data_edit"

def read(path):
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.reader(f))
    return rows[0], [r for r in rows[1:] if r and any(r)]

def write(path, header, rows):
    # 去掉行尾多余空列，保证与表头等长
    n = len(header)
    fixed = []
    for r in rows:
        r = (r + [""] * n)[:n]
        fixed.append(r)
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f); w.writerow(header); w.writerows(fixed)

def add_source_type():
    p = EDIT / "sources.csv"
    h, rows = read(p)
    if "sourceType" in h:
        return "sources.csv 已有 sourceType，跳过"
    h.append("sourceType")
    # 依据 id/title 推断默认类型
    guess = {
        "src_steam_longmarch_1934_1936": "game_text",
    }
    for r in rows:
        d = dict(zip(h[:-1], r))
        sid = d.get("id", "")
        r.append(guess.get(sid, "authoritative"))
    write(p, h, rows)
    return f"sources.csv 加 sourceType，共 {len(rows)} 条（默认 authoritative）"

def update_build_script():
    p = BASE / "tools" / "build_json_from_tables.py"
    s = p.read_text(encoding="utf-8")
    if "sourceType" in s:
        return "build 脚本已支持 sourceType，跳过"
    old = "sources.append({'id':sid,'title':row.get('title',''),'publisher':row.get('publisher',''),'url':row.get('url',''),'note':row.get('note','')})"
    new = "sources.append({'id':sid,'title':row.get('title',''),'publisher':row.get('publisher',''),'url':row.get('url',''),'note':row.get('note',''),'sourceType':row.get('sourceType','') or 'authoritative'})"
    if old not in s:
        return "警告：build 脚本 sources 构造行未找到，需手工检查"
    s = s.replace(old, new)
    p.write_text(s, encoding="utf-8")
    return "build 脚本 sources 输出增加 sourceType"

def update_check_script():
    p = BASE / "tools" / "check_project.py"
    s = p.read_text(encoding="utf-8")
    if "check_non_authoritative_certainty" in s:
        return "check 脚本已含非权威源检查，跳过"
    marker = "def check_visual_asset_provenance() -> None:"
    fn = '''def check_non_authoritative_certainty() -> None:
    """非权威源（游戏/书籍/字幕/口述/公众叙事）不得支撑 certainty=high 的事件。"""
    print("[CHECK] non-authoritative source certainty ceiling")
    src_types: dict[str, str] = {}
    for row in read_csv_rows("data_edit/sources.csv"):
        sid = str(row.get("id", "")).strip()
        if sid:
            src_types[sid] = str(row.get("sourceType", "") or "authoritative").strip().lower()
    non_auth = {"game_text", "book", "subtitle", "oral_history", "public_narrative"}
    violations: list[str] = []
    checked = 0
    for row in read_csv_rows("data_edit/events.csv"):
        if str(row.get("enabled", "TRUE")).strip().lower() in {"false", "0", "no", "n", "否", "禁用"}:
            continue
        refs = split_refs(row.get("sourceIds", ""))
        if not refs:
            continue
        types = {src_types.get(r, "authoritative") for r in refs}
        if not (types & non_auth):
            continue
        checked += 1
        if str(row.get("certainty", "")).strip().lower() == "high":
            violations.append(row.get("id") or row.get("title") or "<unnamed>")
    if violations:
        sample = ", ".join(violations[:10])
        raise RuntimeError(
            f"{len(violations)} 个非权威来源事件错误地标为 certainty=high。示例：{sample}"
        )
    print(f"[OK] non-authoritative source events avoid high certainty: {checked} checked")


'''
    if marker not in s:
        return "警告：check 脚本插入点未找到，需手工检查"
    s = s.replace(marker, fn + marker, 1)
    # 在 main 里注册调用（找到 check_source_provenance_policy() 调用点）
    call_marker = "    check_source_provenance_policy()"
    if call_marker in s:
        s = s.replace(call_marker, call_marker + "\n        check_non_authoritative_certainty()", 1)
    p.write_text(s, encoding="utf-8")
    return "check 脚本增加非权威源确定性上限检查"

if __name__ == "__main__":
    print(add_source_type())
    print(update_build_script())
    print(update_check_script())
