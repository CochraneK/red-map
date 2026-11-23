# -*- coding: utf-8 -*-
"""
把《长征大事记》逐日条目聚合成事件条目。

纪律：
  1. 同一日期的多条原始记录聚合成 1 个事件，描述保留逐日行军地点与部队，
     不淹没项目既有的主干节点结构。
  2. 只对「现有事件完全没覆盖的日期」建条目（避免与既有条目重复）。
  3. certainty=high：《长征大事记》原件藏中央档案馆，1991年《党的文献》首次整理发表，
     是逐日编年实录，出处明确。
  4. 来源 src_hongjun_changzhengji。

输出：research_private/sourced_research/22_长征大事记事件.json
"""
import csv
import json
import re
from collections import defaultdict
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
INP = BASE / "research_private" / "sourced_research" / "21_长征大事记逐日条目.json"
OUT = BASE / "research_private" / "sourced_research" / "22_长征大事记事件.json"
EVENTS_CSV = BASE / "data_edit" / "events.csv"

SRC_ID = "src_hongjun_changzhengji"
SRC_NAME = "红军长征记（1937年2月编定，1942年11月延安印行）·长征大事记"

# 部队中文简称 -> 项目 forceId + 显示名
FORCE_CN = {
    "一军团": ("red_first", "红一军团"),
    "二军团": ("red_second", "红二军团"),
    "三军团": ("red_first", "红三军团"),
    "四军团": ("red_fourth", "红四军团"),
    "五军团": ("red_first", "红五军团"),
    "六军团": ("red_second", "红六军团"),
    "七军团": ("red_first", "红七军团"),
    "八军团": ("red_first", "红八军团"),
    "九军团": ("red_first", "红九军团"),
    "十军团": ("red_first", "红十军团"),
    "二十五军": ("red_25th", "红二十五军"),
    "二十六军": ("red_25th", "红二十六军"),
    "二十八军": ("red_25th", "红二十八军"),
    "三十二军": ("red_fourth", "红三十二军"),
    "军委": ("red_first", "军委纵队"),
    "总部": ("red_first", "红军总部"),
    "野战军": ("red_first", "中央红军野战军"),
    "党中央": ("red_first", "中共中央"),
}

# 逐月所在战区（兜底坐标）：(lat, lng, 区域名)
MONTH_ZONE = {
    "193410": (25.30, 114.60, "赣南·信丰至于都一线"),
    "193411": (25.55, 112.80, "湘南·宜章至道州一线"),
    "193412": (26.10, 111.20, "湘桂边·全州与湘江以西"),
    "193501": (27.60, 107.10, "黔北·瓮安至遵义一线"),
}

PLACE_COORD = {
    # 已核对过的主要地点（纬度, 经度）
    "金鸡": (25.13, 114.62), "新田": (25.15, 114.66), "固陂": (25.20, 114.55),
    "韩坊": (25.30, 114.50), "百室": (25.45, 114.30), "太平新坡": (25.10, 114.90),
    "王母渡": (25.35, 114.55), "赖圩": (25.32, 114.60), "龙布圩": (25.25, 114.40),
    "燕湾岗": (25.28, 114.45), "龙尾口": (25.22, 114.48), "仁风": (25.40, 114.35),
    "荷头": (25.38, 114.30), "大竹": (25.12, 114.75), "双芫": (25.10, 114.72),
    "黄朱排": (25.30, 114.10), "安息圩": (25.30, 114.10), "铁石圩": (25.28, 114.08),
    "罗霄": (25.60, 114.00), "文明山": (25.70, 113.90), "排头": (25.55, 114.05),
    "茶亭": (25.62, 113.95), "宜章": (25.40, 112.93), "白石圩": (25.55, 112.60),
    "坪石": (25.42, 112.75), "麻田": (25.50, 112.50), "正和": (25.60, 112.45),
    "永安": (25.70, 112.40), "观音阁": (25.65, 112.30), "芦田": (25.75, 112.25),
    "水口": (25.80, 112.20), "梅溪": (25.85, 112.15), "道州": (25.53, 111.59),
    "蒋家玉": (25.60, 111.50), "唐家": (25.48, 111.65), "梨木坪": (25.55, 111.30),
    "平石": (25.50, 111.20), "紫岚关": (25.60, 111.40), "华家": (25.40, 111.60),
    "界首": (25.30, 111.20), "脚山铺": (25.35, 111.25), "光华铺": (25.32, 111.22),
    "咸之": (25.30, 111.30), "界牌": (25.28, 111.35), "车源": (25.25, 111.40),
    "正南": (25.20, 111.35), "文家": (25.22, 111.30), "石马": (25.35, 111.20),
    "大湾": (25.40, 111.15), "土城": (28.30, 106.00), "元厚": (28.35, 106.10),
    "女声": (28.40, 106.20), "马鬃岭": (28.30, 106.60), "枫香坝": (27.95, 106.20),
    "枫香溪": (27.90, 106.25), "羊角": (27.80, 106.30), "界场": (27.70, 106.40),
    "水西": (27.65, 106.45), "沙土": (27.60, 106.50), "桐梓": (27.95, 106.82),
    "花秋": (27.85, 106.90), "黑场": (27.90, 106.75), "石厢": (28.00, 106.70),
    "梨园坝": (28.05, 106.65), "江界河": (27.19, 107.35), "猪场": (27.15, 107.45),
    "回龙场": (27.42, 107.62), "茶山关": (27.60, 107.20), "袁家渡": (27.30, 106.90),
    "龙溪": (27.55, 107.10), "平龙": (27.45, 107.05), "场坝": (27.50, 107.00),
    "又州": (27.40, 106.95), "清水口": (27.35, 106.90), "瓮安": (27.05, 107.48),
    "老坟嘴": (27.20, 107.20), "蔡家湾": (27.25, 107.15), "余庆": (27.52, 107.75),
    "猴场": (27.35, 106.90), "乌江": (27.20, 107.30),
}


def load_existing_dates():
    with open(EVENTS_CSV, encoding="utf-8-sig", newline="") as f:
        return {r["date"].replace("-", "")[:8] for r in csv.DictReader(f)
                if r.get("enabled", "TRUE").upper() != "FALSE"}


def build():
    data = json.loads(INP.read_text(encoding="utf-8"))
    entries = data["entries"]
    have = load_existing_dates()

    byday = defaultdict(list)
    for e in entries:
        if e["date"]:
            byday[e["date"]].append(e)

    events = []
    skipped = 0
    for date in sorted(byday):
        if date in have:
            skipped += 1
            continue
        items = byday[date]
        # 抽取出现的部队与地点
        forces = []
        places = []
        texts = []
        for it in items:
            texts.append(it["text"])
            for cn, (fid, disp) in FORCE_CN.items():
                if cn in it["text"] and disp not in forces:
                    forces.append(disp)
            for p in it["places"]:
                if p not in places:
                    places.append(p)
        if not texts:
            continue
        # 描述：按原文顺序拼接，压缩
        desc_parts = []
        for t in texts:
            t = t.strip().rstrip("。")
            if t:
                desc_parts.append(t + "。")
        desc = "".join(desc_parts)
        if len(desc) > 900:
            desc = desc[:880] + "……（详见来源篇目）"

        # 地点坐标：取第一个已知地点；无则按月份给该阶段的大致区域
        lat = lng = ""
        locname = "、".join(places[:3]) if places else ""
        for p in places:
            if p in PLACE_COORD:
                lat, lng = PLACE_COORD[p]
                break
        if not locname:
            locname = "长征行军途中"
        # 兜底坐标：按月份所在战区取（项目要求 lat/lng 必须是有效数字）
        if not lat:
            zone = MONTH_ZONE.get(date[:6])
            if zone:
                lat, lng = zone[0], zone[1]
                locname = locname if locname != "长征行军途中" else zone[2]

        y, mo, dd = date[:4], date[4:6], date[6:8]
        # forceId：按描述正文里最先出现的部队定（更贴近该日主体）
        fid = "red_first"
        body = "".join(texts)
        best_pos = None
        for cn, (f, disp) in FORCE_CN.items():
            pos = body.find(cn)
            if pos >= 0 and (best_pos is None or pos < best_pos):
                best_pos = pos
                fid = f
        # 标题带主要地点，避免同名
        # places 是正则抽取的干净地名（不含动词），直接取首个
        lead_place = places[0] if places else ""
        title = f"{mo}月{dd}日{'、'.join(forces[:2]) if forces else '中央红军'}行军纪要"
        if lead_place:
            title += f"·{lead_place}"
        events.append({
            "id": f"dashi_{date}",
            "title": title,
            "date": date,
            "forceId": fid,
            "type": "行军",
            "description": desc,
            "locationName": locname,
            "lat": lat,
            "lng": lng,
            "participants": "、".join(forces[:6]),
            "certainty": "high",
            "importance": 2,
            "sourceIds": SRC_ID,
            "notes": f"据《红军长征记·长征大事记》{y}年{mo}月{dd}日逐日记录；原件藏中央档案馆",
        })

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"sources": [], "persons": [], "events": events, "links": {}},
                               ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"生成 {len(events)} 个逐日事件（跳过已覆盖日期 {skipped} 个）-> {OUT}")
    from collections import Counter
    print("forceId 分布:", dict(Counter(e["forceId"] for e in events)))
    for e in events[:5]:
        print(f"  {e['date']} {e['title'][:40]}")
        print(f"      {e['description'][:90]}")


if __name__ == "__main__":
    build()
