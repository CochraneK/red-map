#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build and maintain the county/township-level Long March historical gazetteer:
data_edit/gazetteer.csv

Consolidates all active event locations with canonical coordinates, province,
historical-to-modern name aliases, and homonym disambiguation rules to prevent
future geocoding drift or cross-province misattribution during data ingestion.
"""
from __future__ import annotations

import csv
import re
from collections import defaultdict
from pathlib import Path
from statistics import median

ROOT = Path(__file__).resolve().parents[1]
EVENTS_CSV = ROOT / "data_edit" / "events.csv"
OUT_CSV = ROOT / "data_edit" / "gazetteer.csv"

PROVINCE_PREFIXES = [
    "江西", "湖南", "广西", "贵州", "四川", "云南", "陕西", "甘肃", "宁夏",
    "河南", "湖北", "安徽", "福建", "浙江", "广东", "海南", "青海", "西康",
    "山西", "重庆", "吉林", "辽宁", "黑龙江", "新疆", "北京", "上海",
    "东北", "湘鄂川黔", "湘赣", "湘桂", "鄂豫皖", "鄂豫陕", "陕甘宁", "川陕", "川滇", "滇黔", "川甘", "桂湘黔",
]

# Curated historical <-> modern name aliases & homonym disambiguation rules
# Matched by substring key against locationName
CURATED_NOTES: list[tuple[str, str, str, str]] = [
    # (match_substr, historicalNames, modernName, disambiguationNote)
    ("于都", "雩都", "江西赣州市于都县", "旧称“雩都”，1957年简化为“于都”，中央红军集结出发第一渡口。"),
    ("大庸", "大庸", "湖南张家界市永定区", "旧称“大庸县”，1994年更名张家界市。"),
    ("道县", "道州", "湖南永州市道县", "历史文献（如《由临武至道州》）常称“道州”，即今湖南道县。"),
    ("道州", "道州", "湖南永州市道县", "历史文献常称“道州”，即今湖南道县。"),
    ("老山界", "越城岭老山界", "广西桂林市兴安/龙胜交界", "【消歧】老山界位于广西兴安、龙胜越城岭山区，切勿误标为湖南通道。"),
    ("懋功", "懋功", "四川阿坝州小金县", "旧称“懋功县”，1953年更名小金县，红一、红四方面军会师地。"),
    ("小金两河口", "两河口（川西北）", "四川阿坝州小金县两河口镇", "【同名消歧】1935年6月两河口会议在四川小金两河口；区别于湖南桑植两河口（红二、六军团陈家河战区）与四川古蔺两河口。"),
    ("陈家河、两河口", "桑植两河口", "湖南张家界市桑植县两河口乡", "【同名消歧】红二、六军团1935年4月陈家河/两河口战区在湖南桑植，区别于四川小金两河口。"),
    ("越嶲", "越嶲", "四川凉山州越西县", "旧称“越嶲（xī）厅/县”，1959年改写为“越西县”。"),
    ("越西", "越嶲", "四川凉山州越西县", "旧称“越嶲”，《红军长征记》多篇作“越嶲”。"),
    ("定番", "定番", "贵州黔南州惠水县", "旧称“定番县”，1941年更名惠水县。"),
    ("宁强", "宁羌", "陕西汉中市宁强县", "旧称“宁羌县”，1942年更名宁强县。"),
    ("舟曲", "西固", "甘肃甘南州舟曲县", "旧称“西固县”，1954年更名舟曲县。"),
    ("临潭", "洮州", "甘肃甘南州临潭县", "历史文献称“洮州旧城/新城”，即今甘肃临潭县。"),
    ("岷县", "岷州", "甘肃定西市岷县", "古称及民国文献常称“岷州”，即今甘肃岷县。"),
    ("中甸", "中甸", "云南迪庆州香格里拉市", "旧称“中甸县”，2001年更名香格里拉。"),
    ("志丹", "保安", "陕西延安市志丹县", "旧称“保安县”，1936年6月为纪念刘志丹改名志丹县。"),
    ("子长", "安定", "陕西延安市子长市", "旧称“安定县”，1942年为纪念谢子长改名子长县。"),
    ("安定", "安定", "陕西延安市子长市", "【消歧】陕甘红军文献中“安定”指今陕西子长，区别于甘肃定西安定区。"),
    ("双石铺", "双石铺", "陕西宝鸡市凤县双石铺镇", "今陕西凤县县城所在地，红25军1935年7月西征占领之川陕公路要地；切勿误标川西北草地。"),
    ("九间房", "蓝田九间房", "陕西西安市蓝田县九间房镇", "【消歧】1935年4月9日红25军九间房伏击战在陕西蓝田葛牌镇以南，切勿误标为山阳袁家沟口。"),
    ("豹子川", "保安豹子川", "甘肃庆阳市华池县豹子川", "1935年原属保安县合水东北，今属甘肃华池县，红25军9月7日省委会议召开地。"),
    ("大河滩", "威信大河滩/庄子上", "云南昭通市威信县水田镇", "【消歧】1935年2月8日通过《遵义会议决议》的政治局会议在云南威信大河滩，非贵州遵义。"),
    ("漳县", "漳县", "甘肃定西市漳县", "【消歧】1936年8月红四方面军岷洮西战役攻克甘肃漳县，切勿误标四川若尔盖包座。"),
    ("阿坝", "阿坝", "四川阿坝州阿坝县", "【消歧】1935年9月13日红四方面军阿坝会议在四川阿坝，区别于中央红军同期的甘肃迭部俄界/腊子口。"),
    ("俄界", "俄界", "甘肃甘南州迭部县达拉乡高吉村", "【消歧】1935年9月11-12日系红一方面军/中央纵队抵俄界并召开俄界会议，红四方面军未至俄界。"),
    ("百丈关", "百丈", "四川雅安市名山区百丈镇", "1935年11月红四方面军南下百丈关决战发生地。"),
    ("道孚", "道孚（西康）", "四川甘孜州道孚县", "民国时期属西康省，1936年3月红四方面军康道炉战役率先攻占。"),
    ("炉霍", "炉霍（西康）", "四川甘孜州炉霍县", "民国时期属西康省，1936年3月15日红四方面军攻占并以此迎接红二、六军团。"),
    ("吴起镇", "吴起镇/吴旗", "陕西延安市吴起县", "旧亦作“吴旗镇”，1935年10月19日中央红军长征落脚点。"),
    ("榜罗镇", "榜罗镇", "甘肃定西市通渭县榜罗镇", "1935年9月27-28日中共中央政治局常委榜罗镇会议最终确定落脚陕北。"),
    ("将台堡", "将台堡", "宁夏固原市西吉县将台堡镇", "1936年10月22日红一、红二方面军会师，标志三大主力长征胜利结束。"),
    ("哈达铺", "哈达铺", "甘肃陇南市宕昌县哈达铺镇", "1935年9月中央红军在此获取陕北红军报纸并整编为陕甘支队；1936年8-9月红二方面军亦抵此决策成徽两康战役。"),
    ("沙窝", "沙窝", "四川阿坝州松潘县毛儿盖/血洛一带", "1935年8月4-6日中共中央政治局沙窝会议召开地。"),
    ("卓克基", "卓克基", "四川阿坝州马尔康市卓克基镇", "1935年7月初红军翻越梦笔山后驻扎卓克基土司官寨与休养连。"),
    ("芦山", "芦山", "四川雅安市芦山县", "1935年6月8日红1团夜克芦山；1935年底红四方面军南下亦转战天全、芦山、宝兴一带。"),
    ("古陂圩", "古陂圩", "江西赣州市信丰县古陂镇", "1934年10月下旬红三军团突破第一道封锁线重要战斗地。"),
    ("江界河", "江界河渡口", "贵州黔南州瓮安县江界河镇", "1935年1月红四团强渡乌江主渡口之一。"),
]


def infer_province(name: str) -> str:
    for p in PROVINCE_PREFIXES:
        if name.startswith(p):
            return p
    if name in ("巴黎", "莫斯科", "上海", "北平", "延安", "南京", "重庆", "西安"):
        return "跨区/海外" if name in ("巴黎", "莫斯科") else name
    return "跨省/综合"


def match_curated(name: str) -> tuple[str, str, str]:
    for key, hist, mod, note in CURATED_NOTES:
        if key in name:
            return hist, mod, note
    return "", "", ""


def main() -> int:
    with EVENTS_CSV.open("r", encoding="utf-8-sig", newline="") as f:
        events = [r for r in csv.DictReader(f) if str(r.get("enabled", "")).upper() == "TRUE"]

    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for e in events:
        loc = e.get("locationName", "").strip()
        if loc:
            grouped[loc].append(e)

    out_rows = []
    for idx, (loc, items) in enumerate(sorted(grouped.items(), key=lambda kv: (infer_province(kv[0]), kv[0])), start=1):
        lats = [float(x["lat"]) for x in items if x.get("lat")]
        lngs = [float(x["lng"]) for x in items if x.get("lng")]
        lat_med = f"{median(lats):.4f}" if lats else ""
        lng_med = f"{median(lngs):.4f}" if lngs else ""
        forces = sorted({x.get("forceId", "") for x in items if x.get("forceId")})
        hist, mod, note = match_curated(loc)
        out_rows.append({
            "id": f"gaz_{idx:03d}",
            "name": loc,
            "province": infer_province(loc),
            "historicalNames": hist,
            "modernName": mod,
            "lat": lat_med,
            "lng": lng_med,
            "eventCount": str(len(items)),
            "forces": ";".join(forces),
            "disambiguationNote": note,
        })

    fields = [
        "id", "name", "province", "historicalNames", "modernName",
        "lat", "lng", "eventCount", "forces", "disambiguationNote",
    ]
    with OUT_CSV.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(out_rows)

    curated_hits = sum(1 for r in out_rows if r["disambiguationNote"])
    print(f"[OK] 已生成历史地名词典 {OUT_CSV}：{len(out_rows)} 个规范地名（含 {curated_hits} 条古今对照与同名消歧注释）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
