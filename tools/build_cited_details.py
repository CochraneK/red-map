# -*- coding: utf-8 -*-
"""
从事件与人物的反向引用，自动抽取每个来源被引用到的**具体位置**（篇名/章节/节名），
填入 sources.csv 的 citedDetail 字段。

支持模式（notes/title 常见写法）：
  据《红军长征记》第51篇《娄山关前后》…
  据《红军长征记·长征大事记》1935年1月1日逐日记录
  《红军长征记》第133篇《…里程表》说明第四项
  据《红军长征记》前言篇《集体创作的英雄史诗》
  据斯诺《红星照耀中国》第五篇
  据人民网《长征记》第13章…
  据《中国共产党一百年大事记》…

汇总到 sources.csv 的 citedDetail（分号分隔，最多 6 条），如：
  第51篇《娄山关前后》；第52篇《第二次占领遵义城》；第47篇《遵义日记》

同时统计：每个来源被多少条事件/人物引用（usageCount），一并写回。
"""
import csv
import json
import re
from collections import defaultdict
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
SRC = BASE / "data_edit" / "sources.csv"
EVENTS = BASE / "data_edit" / "events.csv"
PERSONS = BASE / "data_edit" / "persons.csv"
OUT_JSON = BASE / "data" / "references.json"

MAX_LOC = 6

# 引用位置模式：捕获（来源名, 位置描述）
PATTERNS = [
    # 据《红军长征记》第51篇《娄山关前后》 / 《红军长征记》第133篇
    (re.compile(r'据?《?红军长征记[》·]?第(\d+)篇(?:《([^》]+)》)?'),
     lambda m: f'第{m.group(1)}篇' + (f'《{m.group(2)}》' if m.group(2) else '')),
    # 据《红军长征记》前言篇
    (re.compile(r'据?《红军长征记》前言篇(?:《([^》]+)》)?'),
     lambda m: '前言篇' + (f'《{m.group(1)}》' if m.group(1) else '')),
    # 据《红军长征记·长征大事记》+ 日期
    (re.compile(r'据《红军长征记[·》]?长征大事记[》]?([0-9年月日-]*)'),
     lambda m: '第132篇《长征大事记》' + (f'（{m.group(1).strip()}）' if m.group(1).strip() else '')),
    # 据人民网《长征记》第13章
    (re.compile(r'据?人民网《长征记》第?(\d+)章'),
     lambda m: f'第{m.group(1)}章（人民网《长征记》）'),
    # 据《中国共产党一百年大事记》
    (re.compile(r'据《中国共产党一百年大事记》([0-9年月日-]*)'),
     lambda m: f'《一百年大事记》' + (f'（{m.group(1).strip()}）' if m.group(1).strip() else '')),
    # 据斯诺《红星照耀中国》
    (re.compile(r'据?斯诺《红星照耀中国》(?:第五篇(?:《([^》]+)》))?'),
     lambda m: '第五篇《长征》' + (f'《{m.group(1)}》' if m.group(1) else '')),
    # 通用：据《书名》（无回调，单独处理）
]
GENERIC_PAT = re.compile(r'据《([^》]{2,20})》')


def src_ids_of(rec):
    v = rec.get("sourceIds") or []
    if isinstance(v, list):
        return [s for s in v if s]
    return [s for s in str(v).split(";") if s.strip()]


def extract_cites(rec):
    """从一条记录的 notes/title/description 里抽取引用位置字符串列表。"""
    text = "；".join(filter(None, [rec.get("notes") or "", rec.get("title") or ""]))
    out = []
    seen = set()
    for pat, fn in PATTERNS:        # 前面带回调的模式
        for m in pat.finditer(text):
            loc = fn(m)
            if loc and loc not in seen:
                seen.add(loc)
                out.append(loc)
    # 通用模式（无回调）
    gm = GENERIC_PAT
    for m in gm.finditer(text):
        book = m.group(1)
        if book in ("红军长征记", "红星照耀中国", "中国共产党一百年大事记", "长征记"):
            continue
        loc = f'《{book}》'
        if loc not in seen:
            seen.add(loc)
            out.append(loc)
    return out


def main():
    with open(SRC, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    fields = list(rows[0].keys())
    if "citedDetail" not in fields:
        fields.append("citedDetail")
    if "usageCount" not in fields:
        fields.append("usageCount")

    with open(EVENTS, encoding="utf-8-sig", newline="") as f:
        events = [r for r in csv.DictReader(f) if (r.get("enabled") or "TRUE").upper() != "FALSE"]
    with open(PERSONS, encoding="utf-8-sig", newline="") as f:
        persons = list(csv.DictReader(f))

    # sid -> {loc: count}
    cites = defaultdict(lambda: defaultdict(int))
    usage = defaultdict(int)

    # 来源名 -> sourceId 映射（用于把 notes 里的「据《X》」精确归到对应来源）
    NAME2SID = {
        "红军长征记": "src_hongjun_changzhengji",
        "长征大事记": "src_hongjun_changzhengji",
        "红星照耀中国": "src_snow_redstar",
        "中国共产党一百年大事记": "src_cpc_century",
        "长征记": "src_changzhengji_people",
    }

    for rec in events + persons:
        sids = src_ids_of(rec)
        for sid in sids:
            usage[sid] += 1
        locs = extract_cites(rec)
        for loc in locs:
            # 精确归属：位置文本里含哪个书名，就归到那个来源
            assigned = False
            for name, sid in NAME2SID.items():
                if name in loc:
                    cites[sid][loc] += 1
                    assigned = True
                    break
            if not assigned and len(sids) == 1:
                # 多来源事件无法判断时不误配；单来源直接归
                cites[sids[0]][loc] += 1

    for r in rows:
        sid = r["id"]
        c = cites.get(sid, {})
        r["usageCount"] = str(max(0, usage.get(sid, 0)))
        locs = [k for k in sorted(c, key=lambda k: -c[k]) if k != "__count__"]
        r["citedDetail"] = "；".join(locs[:MAX_LOC])
        if len(locs) > MAX_LOC:
            r["citedDetail"] += f" 等{len(locs)}处"

    with open(SRC, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)

    # 汇总打印
    n_with_loc = sum(1 for r in rows if r.get("citedDetail"))
    print(f"来源 {len(rows)} 条；有具体引用位置 {n_with_loc} 条")
    top = sorted(rows, key=lambda r: -int(r.get("usageCount") or 0))
    for r in top[:12]:
        print(f"  [{r['usageCount']:>3s}次] {r['id'][:34]}")
        if r.get("citedDetail"):
            print(f"         引用位置: {r['citedDetail'][:80]}")

    # 同步 references.json
    refs = []
    for r in rows:
        refs.append({k: r.get(k) or "" for k in
                     ["id", "author", "title", "publisher", "year", "pubDate", "edition",
                      "mediaType", "url", "accessed", "sourceType", "citedDetail",
                      "usageCount", "note"]})
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps({"accessedDate": "2026-11-23", "count": len(refs),
                                    "references": refs}, ensure_ascii=False, indent=1),
                        encoding="utf-8")
    print(f"references.json 已更新")


if __name__ == "__main__":
    main()
