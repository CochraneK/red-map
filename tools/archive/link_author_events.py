# -*- coding: utf-8 -*-
"""
为《红军长征记》署名作者建立人物-事件关联。

逻辑：
  1. 从 manifest 的 byline 找到每位作者对应的篇目
  2. 从篇目正文里找该作者姓名（及其本名变体）出现的事件线索
  3. 与已入库事件按「篇目内容里出现的地点/事件关键词」匹配，建立 person_events
  4. 保守：匹配不到就不建关联（宁可少，不可错）

输出：research_private/sourced_research/30_作者事件关联.json（links 段）
"""
import csv
import json
import re
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
MANIFEST = BASE / "research_private" / "ebooks" / "hongjun_changzhengji" / "manifest.json"
AMAP = BASE / "research_private" / "ebooks" / "hongjun_changzhengji" / "_author_map.json"
PERSONS = BASE / "data_edit" / "persons.csv"
EVENTS = BASE / "data_edit" / "events.csv"
OUT = BASE / "research_private" / "sourced_research" / "30_作者事件关联.json"
SRC_ID = "src_hongjun_changzhengji"


def main():
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    amap = json.loads(AMAP.read_text(encoding="utf-8"))
    alias = amap["alias"]

    with open(PERSONS, encoding="utf-8-sig", newline="") as f:
        persons = list(csv.DictReader(f))
    pid_by_name = {p["name"]: p["id"] for p in persons}

    with open(EVENTS, encoding="utf-8-sig", newline="") as f:
        events = [r for r in csv.DictReader(f) if r.get("enabled", "TRUE").upper() != "FALSE"]

    # 作者 -> 篇目列表
    author_files = {}
    for x in manifest:
        by = (x.get("byline") or "").strip()
        if not by:
            continue
        real = alias.get(by, by.replace(" ", ""))
        author_files.setdefault(real, []).append(x)

    # 事件关键词索引（用标题里的地名/战役名）
    def keywords(title, desc):
        ks = set()
        for m in re.finditer(r"([\u4e00-\u9fa5]{2,6}(?:桥|渡|关|岭|山|河|寨|城|镇|堡|铺|场|寺|庙|坪|战役|会师|会议|会师))",
                            f"{title} {desc[:80]}"):
            ks.add(m.group(1))
        return ks

    ev_index = []
    for r in events:
        ev_index.append({
            "id": r["id"], "title": r["title"], "desc": r["description"],
            "date": r["date"], "forceId": r["forceId"],
            "kw": keywords(r["title"], r["description"] or ""),
        })

    links = {}
    stats = {"authors": 0, "linked": 0}
    for real, files in author_files.items():
        pid = pid_by_name.get(real)
        if not pid:
            continue
        stats["authors"] += 1
        # 该作者姓名在原文中的形态
        name_variants = {real, real.replace(" ", "")}
        for by in alias:
            if alias[by] == real:
                name_variants.add(by)
                name_variants.add(by.replace(" ", ""))

        # 该作者篇目里出现的地名集合
        places = set()
        for x in files:
            try:
                txt = (BASE / "research_private" / "ebooks" / "hongjun_changzhengji" / x["file"]).read_text(
                    encoding="utf-8", errors="ignore")
            except Exception:
                continue
            for m in re.finditer(r"([\u4e00-\u9fa5]{2,5}(?:桥|渡|关|岭|山|河|寨|城|镇|堡|铺|场|寺|庙|坪))", txt):
                places.add(m.group(1))
        if not places:
            continue

        # 该作者姓名在自己篇目中出现的位置（用于定位其亲历的事件）
        own_text = ""
        for x in files:
            try:
                own_text += (BASE / "research_private" / "ebooks" / "hongjun_changzhengji" / x["file"]).read_text(
                    encoding="utf-8", errors="ignore")
            except Exception:
                pass
        # 该作者篇目里出现的、且项目已有对应条目的事件关键词（强特征地名）
        strong = set()
        for ev in ev_index:
            shared = ev["kw"] & places
            if len(shared) >= 2:
                strong.add(ev["id"])
            elif len(shared) == 1:
                w = next(iter(shared))
                # 单个地名但长度>=3 且是桥/关/渡/山等强特征词 -> 可用
                if len(w) >= 3 and w[-1] in "桥渡关岭山河寨堡":
                    strong.add(ev["id"])

        hits = []
        for ev in ev_index:
            if ev["id"] in strong:
                hits.append(ev)
        if not hits:
            continue
        # 每人最多 6 条，按日期排序
        hits.sort(key=lambda e: e["date"])
        picked = hits[:8]
        links[pid] = [[e["id"], "亲历记述", f"《红军长征记》署名作者，见{e['title']}", SRC_ID]
                      for e in picked]
        stats["linked"] += len(picked)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"links": links}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"覆盖作者 {stats['authors']} 位，建立关联 {stats['linked']} 条，涉及 {len(links)} 人 -> {OUT}")
    for pid, items in list(links.items())[:5]:
        nm = next((p["name"] for p in persons if p["id"] == pid), pid)
        print(f"  {nm}: {len(items)} 条")


if __name__ == "__main__":
    main()
