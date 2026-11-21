#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从 research_private/sourced_research/04_extended_events.json 合并权威事件到表格。
JSON 承载所有中文文案，本脚本只做通用合并，幂等（按 id 去重）。
"""
import csv
import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
EDIT = BASE / "data_edit"
DEFAULT_DATA = BASE / "research_private" / "sourced_research" / "04_extended_events.json"
DATA = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_DATA


def read(name):
    with open(EDIT / name, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write(name, rows):
    with open(EDIT / name, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)


def main():
    d = json.loads(DATA.read_text(encoding="utf-8"))

    rows = read("sources.csv"); have = {r["id"] for r in rows}; n = 0
    for s in d["sources"]:
        if s["id"] in have: continue
        r = {k: "" for k in rows[0].keys()}; r.update(s); rows.append(r); have.add(s["id"]); n += 1
    write("sources.csv", rows); print("新增来源", n)

    rows = read("persons.csv"); have = {r["id"] for r in rows}; n = 0
    for p in d["persons"]:
        if p["id"] in have: continue
        r = {k: "" for k in rows[0].keys()}
        r.update(enabled="TRUE", nameEn="", hometownEn="", summaryEn="", portrait="",
                 personType="人物", certainty="high")
        r.update(p); rows.append(r); have.add(p["id"]); n += 1
    write("persons.csv", rows); print("新增人物", n)

    rows = read("events.csv"); have = {r["id"] for r in rows}; n = 0
    for e in d["events"]:
        if e["id"] in have: continue
        r = {k: "" for k in rows[0].keys()}
        r.update(enabled="TRUE", displayDate=e["date"], sequence="1", importance="3")
        r.update(e); rows.append(r); have.add(e["id"]); n += 1
    write("events.csv", rows); print("新增事件", n)

    persons = {r["id"] for r in read("persons.csv")}
    events = {r["id"] for r in read("events.csv")}
    rows = read("person_events.csv")
    have = {(r["personId"], r["eventId"]) for r in rows}
    maxs = {}
    for r in rows:
        try: maxs[r["personId"]] = max(maxs.get(r["personId"], 0), int(r.get("sort") or 0))
        except ValueError: pass
    n = 0
    for pid, items in d["links"].items():
        if pid not in persons: continue
        for eid, role, note, srcs in items:
            if eid not in events or (pid, eid) in have: continue
            s = maxs.get(pid, 0) + 10; maxs[pid] = s
            r = {k: "" for k in rows[0].keys()}
            r.update(enabled="TRUE", personId=pid, eventId=eid, role=role,
                     note=note, sourceIds=srcs, sort=str(s))
            rows.append(r); have.add((pid, eid)); n += 1
    write("person_events.csv", rows); print("新增关联", n)


if __name__ == "__main__":
    main()
