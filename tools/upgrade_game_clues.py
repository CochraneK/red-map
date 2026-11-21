#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Low→High 升级工具：读取核查结果 JSON，把确认为 UPGRADE 的游戏线索
升级为 certainty=high、追加权威 sourceIds（保留原游戏来源作为参考）；
DUPLICATE 的条目禁用（enabled=FALSE）并在 note 标明对应事件。
KEEP_LOW 不动。

用法：python tools/upgrade_game_clues.py research_private/sourced_research/upgrade_results.json
核查结果 JSON 格式见文件内注释。幂等。
"""
import csv
import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
EDIT = BASE / "data_edit"
GAME_SRC = "src_steam_longmarch_1934_1936"

# 期望 JSON:
# {
#   "sources": [{"id":..,"title":..,"publisher":..,"url":..,"note":..}],
#   "upgrades": [{"eventId":..,"sourceIds":"src_x;src_y","note":"核实说明"}],
#   "duplicates": [{"eventId":..,"of":"对应事件id","note":..}],
#   "keep_low": [{"eventId":..,"reason":..}]
# }


def read(name):
    with open(EDIT / name, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write(name, rows):
    with open(EDIT / name, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)


def main():
    if len(sys.argv) < 2:
        print("用法: python tools/upgrade_game_clues.py <核查结果.json>", file=sys.stderr)
        return 1
    result = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))

    # 新增来源
    src_rows = read("sources.csv"); have = {r["id"] for r in src_rows}; ns = 0
    for s in result.get("sources", []):
        if s["id"] in have: continue
        r = {k: "" for k in src_rows[0].keys()}; r.update(s)
        src_rows.append(r); have.add(s["id"]); ns += 1
    write("sources.csv", src_rows)

    # 校验来源引用
    valid_src = {r["id"] for r in src_rows}
    upgrades = {u["eventId"]: u for u in result.get("upgrades", [])}
    dups = {d["eventId"]: d for d in result.get("duplicates", [])}
    keeps = {k["eventId"]: k for k in result.get("keep_low", [])}

    rows = read("events.csv")
    nu = nd = nk = 0
    for r in rows:
        eid = r["id"]
        if eid in upgrades:
            u = upgrades[eid]
            # 用权威来源替换游戏来源：核实后的事件是史实条目，游戏源仅作线索出处记录
            add = [s.strip() for s in u["sourceIds"].split(";") if s.strip()]
            bad = [s for s in add if s not in valid_src]
            if bad:
                print(f"[WARN] {eid} 引用未登记来源 {bad}，跳过升级", file=sys.stderr)
                continue
            r["sourceIds"] = ";".join(add)
            r["certainty"] = "high"
            note = (r.get("notes", "") + f" | low→high：经权威史料核实，游戏文本线索升级；{u.get('note','')}").strip(" |")
            r["notes"] = note
            nu += 1
        elif eid in dups:
            d = dups[eid]
            r["enabled"] = "FALSE"
            r["notes"] = (r.get("notes", "") + f" | 重复于{d.get('of','')}（游戏线索去重）").strip(" |")
            nd += 1
        elif eid in keeps:
            k = keeps[eid]
            r["notes"] = (r.get("notes", "") + f" | 核查保留low：{k.get('reason','')}").strip(" |")
            nk += 1
    write("events.csv", rows)

    # 禁用事件的关联必须同步清理，否则 build 脚本校验 eventId 未定义
    pe_rows = read("person_events.csv")
    dup_ids = set(dups.keys())
    before = len(pe_rows)
    pe_rows = [r for r in pe_rows if r.get("eventId") not in dup_ids]
    if before != len(pe_rows):
        write("person_events.csv", pe_rows)

    print(f"新增来源 {ns}，升级 {nu}，去重禁用 {nd}（清理关联 {before-len(pe_rows)}），保留low标注 {nk}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
