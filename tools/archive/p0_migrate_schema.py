#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P0-2 一次性数据结构清洗与纠偏脚本（归档留痕，幂等可重跑）。

执行内容：
1. events.csv：
   - 新增 layer（march / spark_march / theme_stat / historiography）与 datePrecision（day / month / range / approx）
   - 将 18 条混填的 certainty（month / range / approximate / 口径有差异）拆分归位，certainty 严守 high / medium / low
   - 将 32 种碎片 type 收拢为 8 大标准 2 字类型：战斗、行军、决策、渡险、会师、牺牲、民生、史料
   - 清理全部核心行军层 >300km 异常跳点（修复错配坐标/日期/部队，禁用已证伪串台条目并同步清理 person_events.csv）
   - 修复 hjdet_* 篇名当坐标、占位日期与 forceId 错配（单家集/榜罗镇/吴起镇归 red_first）
   - 修复 dashi_* 1934年11–12月兜底坐标与过长 locationName
   - 非权威专著（红军长征记/红星照耀中国）单独支撑的事件由 high 回归 medium（一手见闻）
2. sources.csv：
   - 修正 src_snow_redstar / src_hongjun_changzhengji 的 sourceType=book
   - 消除重复标题并标注镜像转载关系
3. subjects.csv：
   - 清理 16 行历史遗留的 0 事件 type=person 行
"""
from __future__ import annotations

import csv
import math
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EDIT = ROOT / "data_edit"


def read_csv(name: str) -> tuple[list[str], list[dict[str, str]]]:
    p = EDIT / name
    with p.open("r", encoding="utf-8-sig", newline="") as f:
        r = csv.DictReader(f)
        return list(r.fieldnames or []), [dict(row) for row in r]


def write_csv(name: str, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    p = EDIT / name
    with p.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def append_note(row: dict[str, str], msg: str) -> None:
    cur = (row.get("notes") or "").strip()
    if msg in cur:
        return
    row["notes"] = f"{cur}；{msg}" if cur else msg


def haversine(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lng2 - lng1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(min(1.0, a)))


# ---------------------------------------------------------------------------
# 1. Sources cleanup
# ---------------------------------------------------------------------------
def migrate_sources() -> dict[str, str]:
    fields, rows = read_csv("sources.csv")
    source_types: dict[str, str] = {}

    for r in rows:
        sid = r["id"].strip()
        if sid in ("src_snow_redstar", "src_hongjun_changzhengji"):
            r["sourceType"] = "book"
            r["mediaType"] = "专著"
        elif sid == "src_cpc_century":
            r["title"] = "中国共产党一百年大事记（最高检转载版）"
            r["sourceType"] = "authoritative"
            r["mediaType"] = "专著"
            if "同源镜像" not in (r.get("note") or ""):
                r["note"] = ((r.get("note") or "").strip() + "；与 src_party_chronology_xinhua / src_100years_cpc 为同源官方大事记镜像").lstrip("；")
        elif sid == "src_party_chronology_xinhua":
            r["title"] = "中国共产党一百年大事记（新华网发布版）"
            r["sourceType"] = "authoritative"
            if "同源镜像" not in (r.get("note") or ""):
                r["note"] = ((r.get("note") or "").strip() + "；与 src_cpc_century / src_100years_cpc 为同源官方大事记镜像").lstrip("；")
        elif sid == "src_100years_cpc":
            r["title"] = "中国共产党一百年大事记（中国共产党新闻网版）"
            r["sourceType"] = "authoritative"
            r["mediaType"] = "专著"
            if "同源镜像" not in (r.get("note") or ""):
                r["note"] = ((r.get("note") or "").strip() + "；与 src_cpc_century / src_party_chronology_xinhua 为同源官方大事记镜像").lstrip("；")
        elif sid in ("src_qiongya_cpc", "src_red25_cpc"):
            if "同页专题" not in (r.get("note") or ""):
                r["note"] = ((r.get("note") or "").strip() + "；同页专题文章不同章节引用").lstrip("；")
        elif sid == "src_dongjiang_hk_rescue":
            if "同源大事记" not in (r.get("note") or ""):
                r["note"] = ((r.get("note") or "").strip() + "；摘自中国共产党新闻网《中国共产党一百年大事记》香港大营救条目").lstrip("；")
        elif sid in ("src_dkb_yiyongjun", "src_dkb_1945"):
            if "同页图集" not in (r.get("note") or ""):
                r["note"] = ((r.get("note") or "").strip() + "；同页抗联专题图集不同时期条目").lstrip("；")
        elif sid in ("src_dj_meitang", "src_dj_wangzuoyao"):
            if "同页地方史志" not in (r.get("note") or ""):
                r["note"] = ((r.get("note") or "").strip() + "；同页惠阳党史专题不同条目").lstrip("；")

        source_types[sid] = (r.get("sourceType") or "authoritative").strip().lower()

    write_csv("sources.csv", fields, rows)
    print(f"[P0] sources.csv updated: {len(rows)} rows")
    return source_types


# ---------------------------------------------------------------------------
# 2. Subjects cleanup (drop 16 legacy 0-event person rows)
# ---------------------------------------------------------------------------
def migrate_subjects() -> None:
    fields, rows = read_csv("subjects.csv")
    before = len(rows)
    kept = [r for r in rows if (r.get("type") or "").strip().lower() != "person"]
    write_csv("subjects.csv", fields, kept)
    print(f"[P0] subjects.csv cleaned: {before} -> {len(kept)} rows (removed {before - len(kept)} legacy person rows)")


# ---------------------------------------------------------------------------
# 3. Events & person_events cleanup
# ---------------------------------------------------------------------------
# Events to disable because of proven historical/cross-contamination errors or exact mislocated duplicates
DISABLE_EVENTS = {
    "steam_r7_19340801_46719b01": "已证伪串台：1934年8月红七军团在福建作战，湖南桃源系红二/六军团活动区",
    "steam_rf_19341030_79a2d2a5": "已证伪错位：1934年10月30日中央红军尚在赣南，不可能在广西湘江集结",
    "steam_rf_19350115_62273c6e": "重复且误标贵州黎平，已合并权威来源至 rf_19350115_zunyi_meeting",
    "steam_r4_19341001_d1182b92": "已证伪串台：红四方面军1932年已离开鄂豫皖，1934年10月在川陕苏区",
    "steam_r4_19341201_987b598b": "已证伪串台：红四方面军1934年12月在川陕苏区，未到贵州遵义",
    "steam_r4_19360128_6960ab2a": "重复且误标陕西瓦窑堡，已有权威条目 ev_red4_19360128_xinanju",
    "ev_red4_19360426_jinsha": "史实串台：1936年4月渡金沙江为红二、六军团（石鼓），红四方面军未于此时渡金沙江",
    "steam_r4_19360427_fe081696": "史实串台：1936年4月渡金沙江为红二、六军团，非红四方面军",
    "steam_r2_19360303_ca3604b9": "日期地点错位：红二、六军团1936年4月底在丽江石鼓渡金沙江，非3月3日皎平渡",
    "steam_r2_19360701_ce6c61d5": "重复串台：内容为红四方面军炉霍集结，与 steam_r4_19360701_f441f9e0 重复",
    "steam_r2_19360914_26cdb46d": "日期错位：红二方面军1936年10月22日会师将台堡，9月14日尚在甘南",
}

# Remap person_events from disabled duplicate to canonical event ID (avoid duplicate pairs)
PERSON_EVENT_REMAP = {
    "steam_rf_19350115_62273c6e": "rf_19350115_zunyi_meeting",
    "steam_r4_19360128_6960ab2a": "ev_red4_19360128_xinanju",
}

# Targeted coordinate / date / force / location / title / description fixes
EVENT_PATCHES: dict[str, dict[str, str]] = {
    # --- red_25th ---
    "steam_r25_19341128_bb9dcee8": {
        "locationName": "河南方城、叶县澧河",
        "lat": "33.50",
        "lng": "113.25",
        "description": "1934年11月28日，红二十五军独树镇战斗后向西北转进，在河南方城、叶县一带渡过澧河进入伏牛山区。",
        "_note": "P0校正：原误标湖南通道/河南罗山，实为河南方城叶县澧河",
    },
    "steam_r25_19341210_9defdcc6": {
        "locationName": "陕西商洛庾家河",
        "lat": "33.62",
        "lng": "110.00",
        "description": "1934年12月10日，鄂豫皖省委在陕西商洛庾家河召开第十八次常委会议，决定创建鄂豫陕革命根据地。",
        "_note": "P0校正：原误标鄂豫皖根据地，实为陕西商洛庾家河会议",
    },
    "ev_red25_19341116_yujiahe": {
        "locationName": "陕西商洛庾家河",
        "lat": "33.70",
        "lng": "110.22",
        "_note": "P0校正坐标：庾家河位于陕西商洛（丹凤）境内",
    },
    "r25_19341210_funiushan": {
        "date": "19341204",
        "displayDate": "1934-12-04",
        "datePrecision": "range",
        "_note": "P0校正日期：红二十五军于1934年12月上旬（4日前后）翻越伏牛山，随后于9日抵庾家河",
    },
    "steam_r25_19350715_989523ae": {
        "locationName": "陕西长安沣峪口",
        "lat": "34.02",
        "lng": "108.78",
        "description": "1935年7月15日，鄂豫陕省委在陕西长安沣峪口召开紧急会议，决定主力西征北上迎接党中央和中央红军。",
        "_note": "P0校正：原误标鄂豫皖根据地，实为陕西长安沣峪口省委紧急会议",
    },
    # --- red_7th_advance ---
    "steam_r7_19340701_16c8ca65": {
        "date": "19340723",
        "displayDate": "1934-07-23",
        "_note": "P0校正日期：红七军团7月6日由瑞金出发，7月23日攻占闽中大田",
    },
    "steam_r7_19340903_da1e617f": {
        "locationName": "福建崇安闽北苏区",
        "lat": "27.75",
        "lng": "118.03",
        "description": "1934年9月3日，北上抗日先遣队转战进入福建崇安一带的闽北苏区。",
        "_note": "P0校正：原误标瑞金/于都，实为闽北苏区（崇安一带）",
    },
    # --- red_first ---
    "ev_czj_19341112_wulu": {
        "forceId": "enemy_kmt",
        "_note": "P0校正归属：系国民党军五路追堵部署，归入 enemy_kmt",
    },
    "steam_rf_19341124_8fd68573": {
        "locationName": "湖南江华水口",
        "lat": "25.15",
        "lng": "111.75",
        "description": "1934年11月24日，中央红军先头部队占领湖南江华水口一带，向湘江挺进。",
        "_note": "P0校正同名地名：原误标福建闽侯水口，实为湖南江华水口",
    },
    "steam_rf_19341125_0e8a2a67": {
        "locationName": "广西兴安、全州湘江一线",
        "lat": "25.82",
        "lng": "111.05",
        "description": "1934年11月25日，中革军委下达抢渡湘江命令，中央红军在广西兴安、全州湘江一线展开突破第四道封锁线作战。",
        "_note": "P0校正同名地名：原误标福建闽侯水口，实为湘江一线",
    },
    "steam_rf_19341219_e8d427e9": {
        "date": "19341226",
        "displayDate": "1934-12-26",
        "locationName": "贵州黄平、施秉",
        "lat": "26.90",
        "lng": "107.90",
        "description": "1934年12月下旬，中央红军占领贵州施秉、黄平一带，向乌江南岸推进。",
        "_note": "P0校正日期与坐标：原误标12月19日贵州遵义，实为12月下旬贵州黄平、施秉",
    },
    "rf_19350115_zunyi_meeting": {
        "certainty": "high",
        "_add_source": "src_zunyi_cpc",
        "_note": "P0合并权威来源 src_zunyi_cpc 并升级为权威史实",
    },
    "steam_rf_19350315_f98945c3": {
        "title": "中央红军到达枫香坝",
        "locationName": "贵州仁怀枫香坝",
        "lat": "27.55",
        "lng": "106.48",
        "description": "1935年3月15日，中央红军在贵州仁怀枫香坝一带集结调整部署。",
        "_note": "P0校正：原误标四川小金两河口且字形误作“枫得坝”，实为贵州仁怀枫香坝",
    },
    "steam_rf_19350319_56029670": {
        "locationName": "四川古蔺镇龙山",
        "lat": "28.05",
        "lng": "105.78",
        "description": "1935年3月19日，中央红军三渡赤水后占领四川古蔺镇龙山一带。",
        "_note": "P0校正：原误标四川小金两河口，实为四川古蔺镇龙山",
    },
    "rf_19350409_kunming": {
        "date": "19350428",
        "displayDate": "1935-04-28",
        "_note": "P0校正日期：红军威逼昆明发生于1935年4月下旬（28日前后），非4月9日",
    },
    "steam_rf_19350418_0daf060c": {
        "locationName": "贵州兴义、贞丰一带",
        "lat": "25.09",
        "lng": "104.90",
        "description": "1935年4月18日前后，中央红军占领贵州贞丰、安龙、兴仁、兴义等城镇，向云南急进。",
        "_note": "P0校正坐标：原误标云南皎平渡，实为黔西南兴义、贞丰一带",
    },
    "steam_rf_19350514_1e69d87f": {
        "date": "19350525",
        "displayDate": "1935-05-25",
        "_note": "P0校正日期：强渡大渡河为1935年5月25日，修正原游戏线索5月14日早标",
    },
    "ev_czj_19350702_longriba": {
        "locationName": "四川红原龙日坝",
        "lat": "32.65",
        "lng": "102.30",
        "_note": "P0精校坐标：龙日坝位于今四川红原县",
    },
    "steam_rf_19350710_b3a76e11": {
        "locationName": "四川松潘毛儿盖",
        "lat": "32.67",
        "lng": "103.60",
        "description": "1935年7月10日，中央红军到达四川松潘以西的毛儿盖地区。",
        "_note": "P0校正坐标：原误标四川小金两河口，实为四川松潘毛儿盖",
    },
    "steam_rf_19350804_e6705bd9": {
        "title": "中央红军召开沙窝政治局扩大会议",
        "locationName": "四川松潘沙窝",
        "lat": "32.58",
        "lng": "103.25",
        "description": "1935年8月4日至6日，中共中央政治局在四川松潘毛儿盖以南沙窝召开扩大会议。",
        "_note": "P0校正坐标：原误标四川小金两河口，实为四川松潘沙窝会议",
    },
    # --- red_fourth ---
    "steam_r4_19350710_0e7cbd6c": {
        "locationName": "四川松潘毛儿盖",
        "lat": "32.67",
        "lng": "103.60",
        "description": "1935年7月10日，红四方面军部分主力推进至四川松潘毛儿盖地区。",
        "_note": "P0校正坐标：原误标四川小金两河口，实为四川松潘毛儿盖",
    },
    "steam_r4_19350804_85acb4ce": {
        "title": "红四方面军参与沙窝政治局扩大会议",
        "locationName": "四川松潘沙窝",
        "lat": "32.58",
        "lng": "103.25",
        "description": "1935年8月4日至6日，在四川松潘沙窝召开中共中央政治局扩大会议，明确北上创建川陕甘根据地方针。",
        "_note": "P0校正坐标：原误标四川小金两河口，实为四川松潘沙窝",
    },
    "steam_r4_19351112_3e860ed8": {
        "locationName": "四川名山百丈关",
        "lat": "30.18",
        "lng": "103.10",
        "description": "1935年11月12日前后，红四方面军在四川名山百丈关一带发起猛烈攻击。",
        "_note": "P0校正坐标：原误标陕西子长瓦窑堡，实为四川名山百丈关战役",
    },
    "steam_r4_19360625_7791aca4": {
        "locationName": "四川甘孜、炉霍一带",
        "lat": "31.50",
        "lng": "100.35",
        "description": "1936年6月25日，红四方面军在四川甘孜、炉霍一带部署与红二、六军团会师后的北上行动。",
        "_note": "P0校正坐标：原误标四川若尔盖包座，实为四川甘孜、炉霍一带",
    },
    "steam_r4_19360701_f441f9e0": {
        "locationName": "四川炉霍",
        "lat": "31.39",
        "lng": "100.68",
        "description": "1936年7月上旬，红四方面军第九军、第四军等部在四川炉霍地区集结准备共同北上。",
        "_note": "P0校正坐标：原误标四川松潘毛儿盖，标题明载炉霍地区",
    },
    # --- red_second ---
    "steam_r2_19341026_bed31daa": {
        "locationName": "重庆酉阳南腰界猫洞大田",
        "lat": "28.57",
        "lng": "108.58",
        "description": "1934年10月26日，红二、红六军团出发前往酉阳县南腰界猫洞大田会师整编。",
        "_note": "P0校正同名地名：原误标福建大田，实为四川（今重庆）酉阳南腰界猫洞大田",
    },
    "steam_r2_19350211_360892c2": {
        "locationName": "湖南永顺、大庸一带",
        "lat": "29.10",
        "lng": "110.15",
        "description": "1935年2月11日，红二、红六军团在湘鄂川黔边区（湖南永顺、大庸一带）反围剿作战中突破敌军围攻线。",
        "_note": "P0校正坐标：原误标贵州乌江一线，实为湘鄂川黔根据地永顺、大庸一带",
    },
    "steam_r2_19350415_0cfa8218": {
        "locationName": "湖南桑植陈家河、两河口",
        "lat": "29.38",
        "lng": "109.95",
        "description": "1935年4月15日，红二、红六军团在湖南桑植陈家河、两河口一带发起猛攻，取得陈家河、桃子溪战役大捷。",
        "_note": "P0校正同名地名：原误标四川小金两河口，实为湖南桑植两河口/陈家河",
    },
    # --- shaanbei_red & red_west_route ---
    "ev_south_guerrilla_193410": {
        "forceId": "red_first",
        "layer": "spark_march",
        "_note": "P0校正归属与分层：系中央苏区留守部队南方三年游击战争，非陕甘红军",
    },
    "ev_wxyj_193703_sun": {
        "date": "19370501",
        "displayDate": "1937-05-01",
        "datePrecision": "month",
        "layer": "theme_stat",
        "_note": "P0校正日期与分层：孙玉清梨园口后被俘押往西宁，1937年5月被害；属被俘就义专题节点，不拉扯左支队星星峡路线",
    },
    "ev_wxyj_19370227": {
        "layer": "theme_stat",
        "_note": "P0分层：援西军组建于陕甘后方，归入专题层以免西路军河西走廊航线折返",
    },
    "ev_wxyj_1937_rescue": {
        "layer": "theme_stat",
        "_note": "P0分层：被俘将士分批营救返延安为战后历史专题，不参与行军连线",
    },
    # --- dashi_* fallback coordinates (1934.10.31 - 1934.12.29) ---
    "dashi_19341031": {"locationName": "江西崇义聂都、沙溪", "lat": "25.60", "lng": "114.15"},
    "dashi_19341102": {"locationName": "广东仁化城口、湖南汝城", "lat": "25.45", "lng": "113.70"},
    "dashi_19341103": {"locationName": "湖南汝城、三江口", "lat": "25.55", "lng": "113.68"},
    "dashi_19341104": {"locationName": "广东仁化城口、湖南汝城", "lat": "25.52", "lng": "113.72"},
    "dashi_19341105": {"locationName": "湖南汝城文明司、新田", "lat": "25.48", "lng": "113.55"},
    "dashi_19341106": {"locationName": "湖南汝城文明司一带", "lat": "25.42", "lng": "113.40"},
    "dashi_19341118": {"locationName": "湖南蓝山、临武一带", "lat": "25.37", "lng": "112.20"},
    "dashi_19341119": {"locationName": "湖南嘉禾、宁远一带", "lat": "25.55", "lng": "112.35"},
    "dashi_19341120": {"locationName": "湖南蓝山、江华一带", "lat": "25.35", "lng": "112.00"},
    "dashi_19341121": {"locationName": "湖南宁远天堂圩一带", "lat": "25.48", "lng": "111.88"},
    "dashi_19341213": {"locationName": "湖南通道平茶所一带", "lat": "26.18", "lng": "109.75"},
    "dashi_19341214": {"locationName": "贵州黎平", "lat": "26.23", "lng": "109.13"},
    "dashi_19341221": {"locationName": "贵州剑河", "lat": "26.73", "lng": "108.45"},
    "dashi_19341222": {"locationName": "贵州剑河、台江清水江沿岸", "lat": "26.85", "lng": "108.30"},
    "dashi_19341223": {"locationName": "贵州台拱（今台江）", "lat": "26.67", "lng": "108.32"},
    "dashi_19341224": {"locationName": "贵州台拱偏寨", "lat": "26.75", "lng": "108.28"},
    "dashi_19341225": {"locationName": "贵州施秉施洞口", "lat": "26.83", "lng": "108.12"},
    "dashi_19341227": {"locationName": "贵州黄平新城、施秉", "lat": "26.92", "lng": "108.05"},
    "dashi_19341229": {"locationName": "贵州瓮安、新黄平", "lat": "27.05", "lng": "107.48"},
    # --- hjdet_* fixes (essay title as locationName, placeholder dates, forceId errors) ---
    "hjdet_01": {"locationName": "贵州黔东南苗山", "lat": "26.40", "lng": "108.60", "date": "19341218", "displayDate": "1934-12-18", "datePrecision": "month"},
    "hjdet_02": {"locationName": "广西全州文市", "lat": "25.75", "lng": "111.08", "date": "19341128", "displayDate": "1934-11-28", "datePrecision": "month"},
    "hjdet_03": {"locationName": "广西兴安老山界", "lat": "25.90", "lng": "110.20", "date": "19341205", "displayDate": "1934-12-05", "datePrecision": "day"},
    "hjdet_04": {"locationName": "广西兴安、资源瑶区", "lat": "25.95", "lng": "110.45", "date": "19341204", "displayDate": "1934-12-04", "datePrecision": "month"},
    "hjdet_05": {"locationName": "四川越嶲（今越西）", "lat": "28.64", "lng": "102.51", "date": "19350520", "displayDate": "1935-05-20", "datePrecision": "month"},
    "hjdet_06": {"locationName": "四川越嶲（今越西）", "lat": "28.64", "lng": "102.51", "date": "19350521", "displayDate": "1935-05-21", "datePrecision": "month"},
    "hjdet_07": {"locationName": "四川冕宁彝海", "lat": "28.78", "lng": "102.17"},
    "hjdet_08": {"locationName": "四川冕宁", "lat": "28.55", "lng": "102.18", "date": "19350520", "displayDate": "1935-05-20"},
    "hjdet_09": {"locationName": "四川黑水打鼓山", "lat": "32.22", "lng": "102.77", "date": "19350712", "displayDate": "1935-07-12", "datePrecision": "month"},
    "hjdet_10": {"locationName": "四川马尔康卓克基", "lat": "31.90", "lng": "102.31", "date": "19350703", "displayDate": "1935-07-03", "datePrecision": "month"},
    "hjdet_11": {"locationName": "四川马尔康卓克基", "lat": "31.90", "lng": "102.31", "date": "19350705", "displayDate": "1935-07-05", "datePrecision": "month"},
    "hjdet_12": {"locationName": "四川夹金山一线", "lat": "30.85", "lng": "102.75", "date": "19350612", "displayDate": "1935-06-12", "datePrecision": "month", "layer": "theme_stat"},
    "hjdet_13": {"locationName": "四川松潘毛儿盖", "lat": "32.67", "lng": "103.60", "date": "19350810", "displayDate": "1935-08-10", "datePrecision": "month", "layer": "theme_stat"},
    "hjdet_14": {"date": "19350824", "displayDate": "1935-08-24", "datePrecision": "range"},
    "hjdet_15": {"locationName": "中央红军长征沿线", "lat": "31.50", "lng": "106.00", "date": "19351019", "displayDate": "1935-10-19", "datePrecision": "range", "layer": "theme_stat"},
    "hjdet_16": {"locationName": "中央红军长征沿线", "lat": "31.50", "lng": "106.00", "date": "19351019", "displayDate": "1935-10-19", "datePrecision": "range", "layer": "theme_stat"},
    "hjdet_17": {"locationName": "中央红军长征沿线", "lat": "31.50", "lng": "106.00", "date": "19351019", "displayDate": "1935-10-19", "datePrecision": "range", "layer": "theme_stat"},
    "hjdet_18": {"forceId": "red_first", "locationName": "宁夏西吉单家集", "lat": "35.80", "lng": "105.62", "title": "过单家集：回民夹道送水", "_note": "P0校正：原篇为《红军长征记》红一方面军（陕甘支队）10月5日过单家集，归 red_first"},
    "hjdet_19": {"locationName": "贵州仁怀猿猴场", "lat": "28.27", "lng": "106.10", "date": "19350321", "displayDate": "1935-03-21", "datePrecision": "month"},
    "hjdet_20": {"locationName": "四川越嶲（今越西）", "lat": "28.64", "lng": "102.51", "date": "19350520", "displayDate": "1935-05-20", "datePrecision": "month"},
    "hjdet_21": {"locationName": "四川石棉安顺场", "lat": "29.23", "lng": "102.35", "layer": "theme_stat"},
    "hjdet_22": {"locationName": "广西全州文市", "lat": "25.75", "lng": "111.08", "date": "19341201", "displayDate": "1934-12-01", "datePrecision": "month"},
    "hjdet_23": {"forceId": "red_first", "_note": "P0校正：吴起镇切尾巴打骑兵系中央红军（陕甘支队）作战，归 red_first"},
    "hjdet_24": {"forceId": "red_first", "date": "19350927", "displayDate": "1935-09-27", "_note": "P0校正：榜罗镇会议为1935年9月27日中央红军（陕甘支队）会议，归 red_first"},
    "hjdet_25": {"locationName": "贵州黔东南苗山", "lat": "26.40", "lng": "108.60", "date": "19341218", "displayDate": "1934-12-18", "datePrecision": "month"},
    "hjdet_27": {"locationName": "四川小金两河口", "lat": "31.02", "lng": "102.50"},
    # --- Clean overly long locationName entries ---
    "hj3_193503_wo_shi_lianluo": {"locationName": "贵州习水、四川古蔺一带"},
    "minzu_1934_tibetan_region": {"locationName": "川西北与康东藏区"},
    "minzu_1934_miao_region": {"locationName": "黔南桂北苗族区域"},
    "minzu_1934_yao_region": {"locationName": "桂北黔边瑶族区域"},
    "minzu_1935_total_days": {"locationName": "中央红军长征全程"},
}

# Canonical 8-type mapping
BASE_TYPE_MAP = {
    "战斗": "战斗", "战役": "战斗", "围堵": "战斗", "追堵": "战斗",
    "封锁": "战斗", "突围": "战斗", "起义": "战斗",
    "行军": "行军", "整编": "行军", "转进": "行军", "根据": "行军",
    "到达": "行军", "胜利": "行军", "启程": "行军", "行动": "行军",
    "决策": "决策", "会议": "决策", "分歧": "决策", "转折": "决策",
    "渡河": "渡险", "险阻": "渡险", "雪山": "渡险", "草地": "渡险",
    "会师": "会师",
    "牺牲": "牺牲", "被俘": "牺牲",
    "民族": "民生", "生活": "民生", "医疗": "民生", "诞生": "民生",
    "里程": "史料", "传播": "史料", "史料": "史料", "渡险": "渡险", "民生": "民生",
}

GENERIC_EVENT_TYPE_OVERRIDE = {
    "steam_rf_19340401_fbf8e3d3": "决策",
    "steam_rf_19341005_63faf30f": "决策",
    "steam_rf_19341007_fce7998a": "行军",
    "steam_rf_19341016_6cb371a0": "行军",
    "steam_rf_19341030_79a2d2a5": "行军",
    "steam_rf_19350205_7274f529": "行军",
    "steam_r4_19350630_e0834dad": "渡险",
    "steam_r25_19350701_0d09cb91": "战斗",
    "steam_rf_19350218_dab67e53": "渡险",
    "steam_rf_19350224_cfc285f2": "战斗",
    "steam_rf_19350630_f1f50f21": "渡险",
    "steam_rf_19350906_80ea8a31": "行军",
    "steam_r4_19350906_e68a7685": "行军",
    "steam_r4_19350915_17f118d4": "决策",
    "ev_snow_19350509_jinsha": "渡险",
    "ev_snow_19350524_shida kai": "决策",
    "ev_snow_193505_ymeng": "民生",
    "ev_snow_19350525_anshunchang": "渡险",
    "ev_snow_19350525_17": "渡险",
    "ev_snow_19350529_luding": "渡险",
    "ev_snow_19350612_jinshan": "渡险",
    "ev_snow_193508_grassland_trade": "民生",
    "ev_snow_193508_grassland": "渡险",
    "ev_snow_1935_18088": "史料",
    "ev_snow_1935_stats": "史料",
    "ev_snow_193504_ham": "民生",
    "ev_czj_19341122_gui": "战斗",
    "hjdet_05": "民生",
    "hjdet_07": "民生",
    "hjdet_08": "决策",
    "hjdet_12": "民生",
    "hjdet_13": "民生",
    "hjdet_14": "行军",
    "hjdet_21": "史料",
    "hjdet_27": "会师",
    "hjdet_28": "民生",
    "hj2_193503_expand_guizhou": "民生",
    "hj2_19350303_zunyi_opium": "民生",
    "hj3_193503_wo_shi_lianluo": "民生",
    "hj3_193503_kaixiao_chai": "民生",
    "hj3_19350405_kuohong_gaozhai": "民生",
    "hj3_19350407_kuohong_yajiao": "民生",
    "hj3_1927_niedu_guerrilla": "行军",
    "hj3_193504_liyi_mang_dadu": "史料",
    "hj3_19350305_zunyi_red_friends": "民生",
}

THEME_STAT_IDS = {
    "ev_snow_1935_18088", "ev_snow_1935_stats", "ev_snow_193504_ham",
    "hj3_193504_liyi_mang_dadu", "hjdet_12", "hjdet_13", "hjdet_15",
    "hjdet_16", "hjdet_17", "hjdet_21", "ev_wxyj_19370227", "ev_wxyj_1937_rescue",
}


def compute_layer(row: dict[str, str]) -> str:
    eid = row["id"]
    fid = row["forceId"]
    dt = row["date"]
    if eid.startswith(("wenxian_", "ev_prop_")):
        return "historiography"
    if eid.startswith(("mileage_", "minzu_")) or eid in THEME_STAT_IDS:
        return "theme_stat"
    if fid.startswith("spark_") or fid == "red_west_route":
        return "spark_march"
    if eid in ("ev_south_guerrilla_193410", "hj3_1927_niedu_guerrilla"):
        return "spark_march"
    if dt < "19340701" or dt > "19361231":
        return "spark_march"
    return "march"


def split_refs(val: str) -> list[str]:
    return [x.strip() for x in (val or "").replace("；", ";").split(";") if x.strip()]


def migrate_events(source_types: dict[str, str]) -> None:
    fields, rows = read_csv("events.csv")
    # Insert layer after forceId and datePrecision after date if missing
    if "datePrecision" not in fields:
        idx = fields.index("displayDate") + 1
        fields.insert(idx, "datePrecision")
    if "layer" not in fields:
        idx = fields.index("forceId") + 1
        fields.insert(idx, "layer")

    disabled_count = 0
    patched_count = 0
    cert_fixed = 0
    book_demoted = 0

    for r in rows:
        eid = r["id"].strip()
        # Default datePrecision
        if not r.get("datePrecision"):
            r["datePrecision"] = "day"

        # 1. Disable bogus/duplicate entries
        if eid in DISABLE_EVENTS:
            r["enabled"] = "FALSE"
            append_note(r, f"P0禁用：{DISABLE_EVENTS[eid]}")
            disabled_count += 1

        # 2. Apply targeted patches
        if eid in EVENT_PATCHES:
            patch = EVENT_PATCHES[eid]
            for k, v in patch.items():
                if k == "_note":
                    append_note(r, v)
                elif k == "_add_source":
                    cur = split_refs(r.get("sourceIds", ""))
                    if v not in cur:
                        cur.append(v)
                        r["sourceIds"] = "; ".join(cur)
                else:
                    r[k] = v
            patched_count += 1

        # 3. Fix non-standard certainty -> split into datePrecision + standard certainty
        cert = (r.get("certainty") or "").strip().lower()
        if cert not in ("high", "medium", "low"):
            if cert == "month":
                r["datePrecision"] = "month"
            elif cert == "range":
                r["datePrecision"] = "range"
            elif cert == "approximate":
                r["datePrecision"] = "approx"
            elif cert == "口径有差异":
                append_note(r, "日期或细节存在多源口径差异")
            # Determine authoritative support
            sids = split_refs(r.get("sourceIds", ""))
            has_auth = any(source_types.get(s, "authoritative") == "authoritative" for s in sids)
            r["certainty"] = "high" if has_auth else "medium"
            cert_fixed += 1

        # 4. Enforce non-authoritative source certainty ceiling (high requires >=1 authoritative source)
        if (r.get("enabled") or "TRUE").strip().upper() != "FALSE":
            if r["certainty"] == "high":
                sids = split_refs(r.get("sourceIds", ""))
                has_auth = any(source_types.get(s, "authoritative") == "authoritative" for s in sids)
                if not has_auth:
                    r["certainty"] = "medium"
                    book_demoted += 1

        # 5. Layer assignment (preserve explicit patch override)
        if not r.get("layer"):
            r["layer"] = compute_layer(r)
        elif eid not in EVENT_PATCHES or "layer" not in EVENT_PATCHES[eid]:
            r["layer"] = compute_layer(r)

        # 6. Canonical 8-type mapping
        old_t = (r.get("type") or "").strip()
        if eid.startswith("wenxian_"):
            r["type"] = "史料"
        elif eid in GENERIC_EVENT_TYPE_OVERRIDE:
            r["type"] = GENERIC_EVENT_TYPE_OVERRIDE[eid]
        elif old_t in BASE_TYPE_MAP:
            r["type"] = BASE_TYPE_MAP[old_t]
        else:
            r["type"] = "行军"

        # 7. Clean mileage/minzu/wenxian datePrecision
        if eid.startswith(("mileage_", "minzu_")):
            r["datePrecision"] = "range"
        elif eid.startswith("ev_prop_") and r["date"].endswith("01"):
            r["datePrecision"] = "month"
        elif eid.startswith("wenxian_") and r["date"].endswith(("30", "31", "28")):
            r["datePrecision"] = "month"

    write_csv("events.csv", fields, rows)
    enabled = [r for r in rows if (r.get("enabled") or "TRUE").strip().upper() != "FALSE"]
    print(f"[P0] events.csv migrated: {len(enabled)} enabled / {len(rows)} total")
    print(f"     disabled={disabled_count}, patched={patched_count}, cert_fixed={cert_fixed}, book_demoted={book_demoted}")
    print("     layers:", dict(Counter(r["layer"] for r in enabled)))
    print("     types :", dict(Counter(r["type"] for r in enabled)))
    print("     certs :", dict(Counter(r["certainty"] for r in enabled)))
    print("     precs :", dict(Counter(r["datePrecision"] for r in enabled)))

    # Audit march jumps > 300km (excluding enemy_kmt)
    by_f = defaultdict(list)
    for r in enabled:
        if r["layer"] == "march" and r["forceId"] != "enemy_kmt":
            by_f[r["forceId"]].append(r)
    jumps = []
    for fid, evs in sorted(by_f.items()):
        evs.sort(key=lambda x: (x["date"], int(x.get("sequence") or 0), x["id"]))
        for a, b in zip(evs, evs[1:]):
            d = haversine(float(a["lat"]), float(a["lng"]), float(b["lat"]), float(b["lng"]))
            if d > 300:
                jumps.append((fid, d, a, b))
    print(f"[P0] Remaining core march jumps >300km: {len(jumps)}")
    for fid, d, a, b in jumps:
        print(f"     {fid:15s} {d:5.0f}km | {a['id']} ({a['date']},{a['locationName']}) -> {b['id']} ({b['date']},{b['locationName']})")


def migrate_person_events() -> None:
    fields, rows = read_csv("person_events.csv")
    existing_pairs = set()
    for r in rows:
        if (r.get("enabled") or "TRUE").strip().upper() != "FALSE":
            existing_pairs.add((r["personId"].strip(), r["eventId"].strip()))

    remapped = 0
    disabled = 0
    for r in rows:
        if (r.get("enabled") or "TRUE").strip().upper() == "FALSE":
            continue
        eid = r["eventId"].strip()
        pid = r["personId"].strip()
        if eid in PERSON_EVENT_REMAP:
            target = PERSON_EVENT_REMAP[eid]
            if (pid, target) in existing_pairs:
                r["enabled"] = "FALSE"
                disabled += 1
            else:
                r["eventId"] = target
                existing_pairs.add((pid, target))
                remapped += 1
        elif eid in DISABLE_EVENTS:
            r["enabled"] = "FALSE"
            disabled += 1

    write_csv("person_events.csv", fields, rows)
    print(f"[P0] person_events.csv synced: remapped={remapped}, disabled={disabled}")


def main() -> None:
    source_types = migrate_sources()
    migrate_subjects()
    migrate_events(source_types)
    migrate_person_events()


if __name__ == "__main__":
    main()
