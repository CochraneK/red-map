#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P2-1b: Second-pass cleanup of the residual 46 `low` events.

Removes exact/near duplicates that survived the first adjudication pass,
plus residual Steam template artifacts ("一带一带", truncated phrases,
same-day same-place clones) that would otherwise inflate the map with
duplicate or meaningless nodes.
"""
from __future__ import annotations

import csv
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

# low_id -> (canonical target id, reason)
DISABLE_EXTRA: dict[str, tuple[str | None, str]] = {
    # Exact title duplicates with an already-present event
    "steam_sg_19350205_d51d7e65": (
        "steam_sg_19331101_06c92b80",
        "标题与1933年11月“陕甘红军召开联席会议”完全重复，且无独立人物关联，予以归并",
    ),
    "steam_sg_19340801_9fe35e4a": (
        "steam_sg_19350221_6b3da244",
        "标题与权威条目“陕甘红军反围剿”完全重复",
    ),
    # Same-day same-place clones within the same force (identical forceId/date/location)
    "steam_r4_19351020_b30acd89": (
        "steam_r4_19350605_ad22b854",
        "与“红四方面军占领懋功”同条同地重复，仅日期不同且内容无增量",
    ),
    "steam_r4_19350915_17f118d4": (
        "steam_r4_19350917_11d161db",
        "与次日“红四方面军发布了南下命令”同指红四方面军南下部署，重复",
    ),
    "steam_r2_19350401_2a5f812d": (
        "steam_r2_19341226_a0af7683",
        "与“占领慈利县城”内容重叠（1935年4月占领慈利、石门），归并至慈利条目",
    ),
    "steam_sg_19350101_97c6888f": (
        "steam_sg_19330405_a46bd176",
        "与1933年4月“陕甘红军成立了陕甘边革命委员会”同类同地重复（1935年1月应为陕甘边省、革命委员会两级机构），归并",
    ),
}

# Residual text artifacts to repair in place (id -> field patches)
TEXT_FIXES: dict[str, dict[str, str]] = {
    "steam_sg_19350205_d51d7e65": {},  # disabled
    "steam_sg_19330701_5ee074e8": {
        "description": "1933年7月，陕甘红军在陕西安定一带召开扩大会议。",
    },
    "steam_sg_19330801_8f0303e3": {
        "description": "1933年8月至1934年7月间，陕北党组织在陕西安定一带成立陕北红军游击队总指挥部。",
    },
    "steam_sg_19350101_97c6888f": {},
    "steam_sg_19350501_dfa53298": {
        "description": "1935年5月，陕甘边与陕北红军主力在陕西安定一带会师。",
    },
    "steam_sg_19350504_f02abc6a": {
        "description": "1935年5月4日，陕甘红军在陕西安定一带成立西北军委前敌总指挥部。",
    },
    "steam_r2_19350211_360892c2": {
        "description": "1935年2月11日，红二、红六军团在湖南永顺、大庸一线突破国民党军的围攻线。",
    },
    "steam_r25_19340301_990d0ad0": {
        "description": "1934年3月中旬，红二十五军由大别山转移至豫鄂边界以西桐柏山区，开辟新的根据地。",
    },
}


def main() -> int:
    events_path = ROOT / "data_edit/events.csv"
    with events_path.open("r", encoding="utf-8-sig", newline="") as f:
        er = csv.DictReader(f)
        efields = list(er.fieldnames or [])
        events = list(er)

    rowmap = {e["id"]: e for e in events}
    disabled_ids = set(DISABLE_EXTRA)

    for eid, (target, reason) in DISABLE_EXTRA.items():
        row = rowmap[eid]
        row["enabled"] = "FALSE"
        prev = (row.get("notes") or "").strip()
        tag = f"→{target}" if target else ""
        row["notes"] = f"{prev} | 【P2二轮去重禁用{tag}】{reason}".strip(" |")

    # Repair residual text artifacts
    for eid, patches in TEXT_FIXES.items():
        row = rowmap.get(eid)
        if not row:
            continue
        for k, v in patches.items():
            row[k] = v

    with events_path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=efields)
        w.writeheader()
        w.writerows(events)

    # person_events: remap or drop links of newly disabled events
    pe_path = ROOT / "data_edit/person_events.csv"
    with pe_path.open("r", encoding="utf-8-sig", newline="") as f:
        pr = csv.DictReader(f)
        pefields = list(pr.fieldnames or [])
        pes = list(pr)

    active_pairs = {
        (r["personId"], r["eventId"])
        for r in pes
        if str(r.get("enabled", "")).upper() == "TRUE" and r["eventId"] not in disabled_ids
    }
    remapped = dropped = 0
    for r in pes:
        if str(r.get("enabled", "")).upper() != "TRUE":
            continue
        eid = r["eventId"]
        if eid not in disabled_ids:
            continue
        target = DISABLE_EXTRA[eid][0]
        if target is None:
            r["enabled"] = "FALSE"
            r["note"] = (r.get("note", "") + " | 【P2二轮禁用】原事件为重复/无信息量条目").strip(" |")
            dropped += 1
            continue
        pair = (r["personId"], target)
        if pair in active_pairs:
            r["enabled"] = "FALSE"
            r["note"] = (r.get("note", "") + f" | 【P2二轮去重】已存在与{target}的关联").strip(" |")
            dropped += 1
        else:
            r["eventId"] = target
            r["note"] = (r.get("note", "") + f" | 【P2二轮重映射】原自{eid}").strip(" |")
            active_pairs.add(pair)
            remapped += 1

    with pe_path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=pefields)
        w.writeheader()
        w.writerows(pes)

    active = [e for e in events if str(e.get("enabled", "")).upper() == "TRUE"]
    c = Counter(e["certainty"] for e in active)
    total = len(active)
    print("=== P2-1b second-pass cleanup ===")
    print(f"  newly disabled events : {len(DISABLE_EXTRA)}")
    print(f"  person links remapped : {remapped}")
    print(f"  person links dropped  : {dropped}")
    print(f"  active events         : {total}")
    print(f"  high/medium/low       : {c['high']} / {c['medium']} / {c['low']}  (low={c['low']/total*100:.1f}%)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
