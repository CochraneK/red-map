# -*- coding: utf-8 -*-
"""
把《红军长征记》51 位署名作者档案并入人物库。

规则：
  - 已在库的（陈云 chenyun、任弼时 ren_bishi）→ 更新 summary/themeTags/sourceIds，不重复新建
  - 其余 → 新建，字段按 persons.csv 的列名规范化
  - 额外字段（aliasBylines/articleCount/articleFiles）不写入 CSV，但写入 notes 之外的信息保留在
    research_private 的档案 JSON 里
"""
import csv
import json
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
SRC = BASE / "research_private" / "sourced_research" / "28_长征记作者人物档案_详版.json"
PERSONS = BASE / "data_edit" / "persons.csv"

CSV_FIELDS = ["enabled", "id", "name", "nameEn", "personType", "birthDate", "deathDate",
              "hometown", "hometownEn", "forceId", "summary", "summaryEn", "portrait",
              "themeTags", "sourceIds", "certainty", "sort"]


def main():
    d = json.loads(SRC.read_text(encoding="utf-8"))
    with open(PERSONS, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    by_id = {r["id"]: r for r in rows}

    added = updated = 0
    for p in d["persons"]:
        pid = p["id"]
        srcids = p.get("sourceIds") or []
        if isinstance(srcids, str):
            srcids = [s for s in srcids.split(";") if s]
        srcids = ";".join(srcids)
        tags = p.get("themeTags") or ""
        if pid in by_id:
            r = by_id[pid]
            # 合并来源（保留原有 sourceIds）
            old = [s for s in (r.get("sourceIds") or "").split(";") if s]
            merged = ";".join(dict.fromkeys(old + ([srcids] if srcids else [])))
            r["sourceIds"] = merged
            if p.get("summary") and len(p["summary"]) > len(r.get("summary") or ""):
                r["summary"] = p["summary"]
            # 追加长征记标签
            oldtags = r.get("themeTags") or ""
            add = [t for t in tags.split(";") if t and t not in oldtags]
            if add:
                r["themeTags"] = ";".join([x for x in (oldtags + ";" + ";".join(add)).split(";") if x])
            updated += 1
            continue
        r = {k: "" for k in CSV_FIELDS}
        r.update({
            "enabled": "TRUE", "id": pid, "name": p.get("name", ""),
            "nameEn": p.get("nameEn", ""), "personType": p.get("personType", "") or "人物",
            "birthDate": str(p.get("birthDate") or ""), "deathDate": str(p.get("deathDate") or ""),
            "hometown": p.get("hometown", ""), "forceId": p.get("forceId", ""),
            "summary": p.get("summary", ""), "themeTags": tags,
            "sourceIds": srcids, "certainty": p.get("certainty", "") or "high",
        })
        rows.append(r)
        by_id[pid] = r
        added += 1

    with open(PERSONS, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        w.writeheader(); w.writerows(rows)
    print(f"新增人物 {added} 位，更新 {updated} 位，总数 {len(rows)}")

    # 补充项
    for s in d.get("existingPersonSupplement") or []:
        r = by_id.get(s["personId"])
        if not r:
            continue
        print(f"  补充 {s['name']}：themeTags -> {s.get('suggestedThemeTags')}")


if __name__ == "__main__":
    main()
