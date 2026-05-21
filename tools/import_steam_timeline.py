#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Import curated Steam text candidates into the editable timeline tables.

The extractor keeps the raw game text in research_private/. This importer only
adds concise, low-certainty exhibit entries so game-derived content remains a
research lead instead of being treated as verified historical evidence.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import re
from collections import Counter
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EDIT_DIR = ROOT / "data_edit"
DEFAULT_CANDIDATES = (
    ROOT
    / "research_private"
    / "steam_longmarch_unreal_text_timeline"
    / "unreal_timeline_candidates.csv"
)

STEAM_SOURCE_ID = "src_steam_longmarch_1934_1936"
STEAM_SOURCE_ROW = {
    "id": STEAM_SOURCE_ID,
    "title": "《长征1934-1936》本地游戏文本抽取",
    "publisher": "Steam 本地安装文件 / Unreal 数据资产抽取",
    "url": "docs/STEAM_TEXT_EXTRACTION.md",
    "note": "仅作线索来源；正式采用前应继续用权威党史资料复核。导入事件已压缩改写为短策展文案。",
}

RED7_SUBJECT_ID = "red_7th_advance"
RED7_SUBJECT_ROW = {
    "id": RED7_SUBJECT_ID,
    "type": "force",
    "name": "红七军团北上抗日先遣队",
    "shortName": "北上抗日先遣队",
    "color": "#8c564b",
    "leader": "寻淮洲、乐少华、粟裕等",
    "sort": "25",
    "description": "1934年由红七军团组成的北上抗日先遣队，是中央苏区战略转移前后重要的牵制作战力量。",
    "nameEn": "Red Seventh Corps Northern Anti-Japanese Advance Detachment",
    "shortNameEn": "Advance Detachment",
    "leaderEn": "Xun Huaizhou, Le Shaohua, Su Yu, etc.",
    "descriptionEn": "A Red Seventh Corps detachment active in 1934 as a related diversionary force before and during the broader strategic shift.",
    "isEnemy": "",
    "subUnits": "红七军团",
    "subUnitsEn": "Red Seventh Corps",
}

FORCE_BY_SOURCE = {
    "Script1_1Round.uexp": "shaanbei_red",
    "Script1_2Round.uexp": "shaanbei_red",
    "Script2Round.uexp": "red_first",
    "Script3Round.uexp": RED7_SUBJECT_ID,
    "Script4Round.uexp": "red_fourth",
    "Script5_1Round.uexp": "red_second",
    "Script5_2Round.uexp": "red_second",
    "Script6Round.uexp": "red_25th",
}

FORCE_SHORT = {
    "shaanbei_red": "陕甘红军",
    "red_first": "中央红军",
    RED7_SUBJECT_ID: "北上抗日先遣队",
    "red_fourth": "红四方面军",
    "red_second": "红二、红六军团",
    "red_25th": "红二十五军",
}

FORCE_ABBR = {
    "shaanbei_red": "sg",
    "red_first": "rf",
    RED7_SUBJECT_ID: "r7",
    "red_fourth": "r4",
    "red_second": "r2",
    "red_25th": "r25",
}

SOURCE_LIMITS = {
    "Script1_1Round.uexp": 18,
    "Script1_2Round.uexp": 11,
    "Script2Round.uexp": 120,
    "Script3Round.uexp": 44,
    "Script4Round.uexp": 140,
    "Script5_1Round.uexp": 110,
    "Script5_2Round.uexp": 120,
    "Script6Round.uexp": 92,
}

STEAM_PERSON_ROWS = [
    {"id": "du_heng", "name": "杜衡", "personType": "争议人物", "forceId": "shaanbei_red", "summary": "补充材料中出现的陕甘边早期组织和军事行动相关人物，用于补足西北根据地前史线索。", "themeTags": "陕甘边;根据地前史;补充线索", "sort": "801"},
    {"id": "wang_shitai", "name": "王世泰", "personType": "军事指挥", "forceId": "shaanbei_red", "summary": "补充材料中作为陕甘边早期红军干部出现，关联红二十六军与照金、南梁等根据地建设线索。", "themeTags": "陕甘边;红二十六军;补充线索", "sort": "802"},
    {"id": "jin_like", "name": "金理科", "personType": "政治工作", "forceId": "shaanbei_red", "summary": "补充材料中出现于照金和陕甘边特委相关叙述，用于呈现根据地组织层面的前史。", "themeTags": "照金;陕甘边特委;补充线索", "sort": "803"},
    {"id": "zhou_dongzhi", "name": "周冬至", "personType": "根据地建设", "forceId": "shaanbei_red", "summary": "补充材料中出现于陕甘边革命委员会相关叙述，补充根据地政权建设人物线索。", "themeTags": "陕甘边;革命委员会;补充线索", "sort": "804"},
    {"id": "wang_taiji", "name": "王泰吉", "personType": "军事指挥", "forceId": "shaanbei_red", "summary": "补充材料中出现于陕甘边红军临时总指挥部和红二十六军相关叙述。", "themeTags": "陕甘边;红二十六军;补充线索", "sort": "805"},
    {"id": "gao_gang", "name": "高岗", "personType": "根据地建设", "forceId": "shaanbei_red", "summary": "补充材料中多次出现于陕甘边、陕北根据地统一领导和军事组织相关叙述。", "themeTags": "西北根据地;政治工作;补充线索", "sort": "806"},
    {"id": "guo_hongtao", "name": "郭洪涛", "personType": "政治工作", "forceId": "shaanbei_red", "summary": "补充材料中出现于陕北红军游击队总指挥部等组织建设线索。", "themeTags": "陕北红军;组织建设;补充线索", "sort": "807"},
    {"id": "he_jinnian", "name": "贺晋年", "personType": "军事指挥", "forceId": "shaanbei_red", "summary": "补充材料中出现于陕北游击队和西北红军相关叙述，补充落脚点形成前的地方武装线索。", "themeTags": "陕北游击队;西北红军;补充线索", "sort": "808"},
    {"id": "yang_qi", "name": "杨琪", "personType": "军事指挥", "forceId": "shaanbei_red", "summary": "补充材料中出现于红二十七军第八十四师相关叙述，是陕北根据地武装整编线索人物。", "themeTags": "红二十七军;整编;补充线索", "sort": "809"},
    {"id": "zhang_dazhi", "name": "张达志", "personType": "政治工作", "forceId": "shaanbei_red", "summary": "补充材料中出现于陕北红军整编与根据地建设相关叙述。", "themeTags": "陕北根据地;整编;补充线索", "sort": "810"},
    {"id": "ma_mingfang", "name": "马明方", "personType": "根据地建设", "forceId": "shaanbei_red", "summary": "补充材料中出现于陕北苏维埃政府成立等根据地政权建设线索。", "themeTags": "陕北苏维埃;根据地建设;补充线索", "sort": "811"},
    {"id": "pan_hannian", "name": "潘汉年", "personType": "政治工作", "forceId": "red_first", "summary": "补充材料中以潘健行、潘汉年等称谓出现，关联中央红军战略转移前的秘密谈判线索。", "themeTags": "寻乌会谈;战略转移;补充线索", "sort": "812"},
    {"id": "he_changgong", "name": "何长工", "personType": "政治工作", "forceId": "red_first", "summary": "补充材料中出现于中央红军转移前后秘密接洽和行动准备线索。", "themeTags": "战略转移;谈判;补充线索", "sort": "813"},
    {"id": "chen_jitang", "name": "陈济棠", "personType": "相关对手", "forceId": "enemy_kmt", "summary": "补充材料中作为粤军方面人物出现，关联中央红军转移前的秘密谈判与借道线索。", "themeTags": "粤军;寻乌会谈;补充线索", "sort": "814"},
    {"id": "bai_chongxi", "name": "白崇禧", "personType": "相关对手", "forceId": "enemy_kmt", "summary": "补充材料中作为桂军方面人物出现，用于说明湘江前后敌军部署和封锁压力。", "themeTags": "桂军;湘江;补充线索", "sort": "815"},
    {"id": "he_jian", "name": "何键", "personType": "相关对手", "forceId": "enemy_kmt", "summary": "补充材料中多次出现于湘军追堵、湖南封锁和红二、红六军团牵制行动叙述。", "themeTags": "湘军;追堵;补充线索", "sort": "816"},
    {"id": "xue_yue", "name": "薛岳", "personType": "相关对手", "forceId": "enemy_kmt", "summary": "补充材料中出现于中央红军和红二、红六军团周边追堵部署线索。", "themeTags": "追堵;国民党军;补充线索", "sort": "817"},
    {"id": "zhang_xueliang", "name": "张学良", "personType": "相关对手", "forceId": "enemy_kmt", "summary": "补充材料中出现于鄂豫皖和红二十五军所处军事压力背景。", "themeTags": "鄂豫皖;东北军;补充线索", "sort": "818"},
    {"id": "dai_jiying", "name": "戴季英", "personType": "政治工作", "forceId": "red_25th", "summary": "补充材料中出现于红二十五军鄂豫皖根据地和战略转移前后叙述。", "themeTags": "红二十五军;鄂豫皖;补充线索", "sort": "819"},
    {"id": "zheng_weisan", "name": "郑位三", "personType": "政治工作", "forceId": "red_25th", "summary": "补充材料中出现于鄂东北道委和红二十五军行动决策相关叙述。", "themeTags": "鄂东北;红二十五军;补充线索", "sort": "820"},
    {"id": "xun_huaizhou", "name": "寻淮洲", "personType": "军事指挥", "forceId": "red_7th_advance", "summary": "补充材料中出现于红七军团北上抗日先遣队叙述，是先遣队人物线索的核心之一。", "themeTags": "红七军团;北上抗日先遣队;补充线索", "sort": "821"},
    {"id": "le_shaohua", "name": "乐少华", "personType": "政治工作", "forceId": "red_7th_advance", "summary": "补充材料中出现于红七军团北上抗日先遣队相关战斗和转移叙述。", "themeTags": "红七军团;北上抗日先遣队;补充线索", "sort": "822"},
    {"id": "su_yu", "name": "粟裕", "personType": "军事指挥", "forceId": "red_7th_advance", "summary": "补充材料中出现于红七军团北上抗日先遣队战斗叙述，连接先遣队与后续革命军事人物线索。", "themeTags": "红七军团;北上抗日先遣队;补充线索", "sort": "823"},
    {"id": "li_xiannian", "name": "李先念", "personType": "军事指挥", "forceId": "red_fourth", "summary": "补充材料和项目路线中均可关联红四方面军行动，用于补足红四方面军人物层。", "themeTags": "红四方面军;北上;补充线索", "sort": "824"},
    {"id": "liu_xiang", "name": "刘湘", "personType": "相关对手", "forceId": "enemy_kmt", "summary": "补充材料中出现于川军与红四方面军作战背景，补充川陕苏区和嘉陵江前后的军事压力。", "themeTags": "川军;川陕苏区;补充线索", "sort": "825"},
    {"id": "liu_wenhui", "name": "刘文辉", "personType": "相关对手", "forceId": "enemy_kmt", "summary": "补充材料中出现于四川地方军政背景，用于说明红四方面军长征前后的区域压力。", "themeTags": "川军;四川地方势力;补充线索", "sort": "826"},
    {"id": "xia_xi", "name": "夏曦", "personType": "政治工作", "forceId": "red_second", "summary": "补充材料中出现于湘鄂川黔边临时省委和红二、红六军团早期行动叙述。", "themeTags": "湘鄂川黔;红二、红六军团;补充线索", "sort": "827"},
    {"id": "zhang_ziyi", "name": "张子意", "personType": "政治工作", "forceId": "red_second", "summary": "补充材料中出现于湘鄂川黔边临时省委相关叙述，补充红二、红六军团组织层人物。", "themeTags": "湘鄂川黔;组织建设;补充线索", "sort": "828"},
    {"id": "chen_quzhen", "name": "陈渠珍", "personType": "相关对手", "forceId": "enemy_kmt", "summary": "补充材料中出现于红二、红六军团湘西攻势和沅陵、常德周边军事压力。", "themeTags": "湘西;红二、红六军团;补充线索", "sort": "829"},
    {"id": "liao_huaizhong", "name": "廖怀中", "personType": "相关对手", "forceId": "enemy_kmt", "summary": "补充材料中出现于沅陵防守和红二、红六军团攻势相关叙述。", "themeTags": "沅陵;湘军;补充线索", "sort": "830"},
    {"id": "dai_jitao", "name": "戴季韬", "personType": "相关对手", "forceId": "enemy_kmt", "summary": "补充材料中出现于沅陵周边布防线索，作为红二、红六军团湘西行动的对照人物。", "themeTags": "沅陵;湘西攻势;补充线索", "sort": "831"},
    {"id": "zhou_xieqing", "name": "周燮卿", "personType": "相关对手", "forceId": "enemy_kmt", "summary": "补充材料中出现于沅陵周边布防线索，补充红二、红六军团行动的地方军事背景。", "themeTags": "沅陵;湘西攻势;补充线索", "sort": "832"},
]

PERSON_ALIASES = {"潘健行": "pan_hannian"}

STEAM_VISUAL_ROWS = [
    ("vis_person_xiezichang", "xie_zichang", "谢子长照片", "谢子长历史照片", "Xie_ZiChang_1935.jpg", "File:Xie_ZiChang_1935.jpg", "Wikimedia Commons", "see file page", "181"),
    ("vis_person_zhangwentian", "zhang_wentian", "张闻天照片", "张闻天历史照片", "Zhang_Wentian-2.jpg", "File:Zhang_Wentian-2.jpg", "Wikimedia Commons", "see file page", "182"),
    ("vis_person_wangjiaxiang", "wang_jiaxiang", "王稼祥照片", "王稼祥历史照片", "Wang_Jiaxiang.jpg", "File:Wang_Jiaxiang.jpg", "Wikimedia Commons", "see file page", "183"),
    ("vis_person_lijianzhen", "li_jianzhen", "李坚真照片", "李坚真历史照片", "%E6%9D%8E%E5%A0%85%E7%9C%9F.jpg", "File:%E6%9D%8E%E5%A0%85%E7%9C%9F.jpg", "Wikimedia Commons", "see file page", "184"),
    ("vis_person_chengzihua", "cheng_zihua", "程子华照片", "程子华历史照片", "Cheng_Zihua.jpg", "File:Cheng_Zihua.jpg", "Wikimedia Commons", "see file page", "185"),
    ("vis_person_chenchanghao", "chen_changhao", "陈昌浩照片", "陈昌浩历史照片", "Chen_Changhao.jpg", "File:Chen_Changhao.jpg", "Wikimedia Commons", "see file page", "186"),
    ("vis_person_zhangguotao", "zhang_guotao", "张国焘照片", "张国焘历史照片", "Zhang_Guotao.jpg", "File:Zhang_Guotao.jpg", "Wikimedia Commons", "see file page", "187"),
    ("vis_person_xiaoke", "xiao_ke", "萧克照片", "萧克历史照片", "Xiaoke1955.jpg", "File:Xiaoke1955.jpg", "Wikimedia Commons", "see file page", "188"),
    ("vis_person_wangzhen", "wang_zhen", "王震照片", "王震历史照片", "Wangzhen1955.jpg", "File:Wangzhen1955.jpg", "Wikimedia Commons", "see file page", "189"),
    ("vis_person_guanxiangying", "guan_xiangying", "关向应照片", "关向应历史照片", "Guan_Xiangying.jpg", "File:Guan_Xiangying.jpg", "Wikimedia Commons", "see file page", "190"),
    ("vis_person_xizhongxun", "xi_zhongxun", "习仲勋照片", "习仲勋历史照片", "Xi_Zhongxun.jpg", "File:Xi_Zhongxun.jpg", "Wikimedia Commons", "see file page", "191"),
    ("vis_person_pan_hannian", "pan_hannian", "潘汉年照片", "潘汉年历史照片", "Pan_Hannian.jpg", "File:Pan_Hannian.jpg", "Wikimedia Commons", "see file page", "192"),
    ("vis_person_he_changgong", "he_changgong", "何长工照片", "何长工历史照片", "He_Changgong.jpg", "File:He_Changgong.jpg", "Wikimedia Commons", "see file page", "193"),
    ("vis_person_dai_jiying", "dai_jiying", "戴季英照片", "戴季英历史照片", "Dai_Jiying.jpg", "File:Dai_Jiying.jpg", "Wikimedia Commons", "see file page", "194"),
    ("vis_person_li_xiannian", "li_xiannian", "李先念照片", "李先念历史照片", "Li_Xiannian.jpg", "File:Li_Xiannian.jpg", "Wikimedia Commons", "see file page", "195"),
    ("vis_person_bai_chongxi", "bai_chongxi", "白崇禧照片", "白崇禧历史照片", "Bai_Chongxi.jpg", "File:Bai_Chongxi.jpg", "Wikimedia Commons", "see file page", "196"),
    ("vis_person_xue_yue", "xue_yue", "薛岳照片", "薛岳历史照片", "Xue_Yue.jpg", "File:Xue_Yue.jpg", "Wikimedia Commons", "see file page", "197"),
    ("vis_person_liu_xiang", "liu_xiang", "刘湘照片", "刘湘历史照片", "Liu_Xiang.jpg", "File:Liu_Xiang.jpg", "Wikimedia Commons", "see file page", "198"),
]


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        return list(reader.fieldnames or []), [dict(row) for row in reader]


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def normalize_date_label(label: str) -> str | None:
    m = re.search(r"(19\d{2})年\s*(?:(\d{1,2})月)?\s*(?:(\d{1,2})日)?", label or "")
    if not m:
        return None
    y = int(m.group(1))
    month = int(m.group(2) or 1)
    day = int(m.group(3) or 1)
    if not (1 <= month <= 12):
        return None
    if not (1 <= day <= 31):
        day = 1
    try:
        return date(y, month, day).strftime("%Y%m%d")
    except ValueError:
        return date(y, month, 1).strftime("%Y%m%d")


def canonical_location_map(event_rows: list[dict[str, str]]) -> dict[str, tuple[str, str]]:
    locs: dict[str, tuple[str, str]] = {}
    for row in event_rows:
        name = (row.get("locationName") or "").strip()
        lat = (row.get("lat") or "").strip()
        lng = (row.get("lng") or "").strip()
        if name and lat and lng:
            locs[name] = (lat, lng)
    return locs


def existing_tuple(
    locs: dict[str, tuple[str, str]], name: str
) -> tuple[str, str, str] | None:
    coords = locs.get(name)
    if not coords:
        return None
    return (name, coords[0], coords[1])


def location_aliases(locs: dict[str, tuple[str, str]]) -> dict[str, tuple[str, str, str]]:
    aliases: dict[str, tuple[str, str, str] | None] = {
        "照金": ("陕西耀县照金", "35.08", "108.82"),
        "耀县": ("陕西耀县照金", "35.08", "108.82"),
        "合水": ("甘肃合水", "35.82", "108.02"),
        "包家寨": ("甘肃合水包家寨", "35.95", "108.05"),
        "南梁": existing_tuple(locs, "甘肃华池南梁"),
        "华池": existing_tuple(locs, "甘肃华池南梁"),
        "安定": existing_tuple(locs, "陕西安定一带"),
        "白庙岔": existing_tuple(locs, "陕西安定一带"),
        "赤源县": existing_tuple(locs, "陕西安定一带"),
        "子长": existing_tuple(locs, "陕西子长瓦窑堡"),
        "清涧": ("陕西清涧", "37.09", "110.12"),
        "河口镇": ("陕西清涧河口镇", "37.02", "110.22"),
        "吴起镇": existing_tuple(locs, "陕西吴起镇"),
        "吴起": existing_tuple(locs, "陕西吴起镇"),
        "直罗镇": existing_tuple(locs, "陕西富县直罗镇"),
        "瓦窑堡": existing_tuple(locs, "陕西子长瓦窑堡"),
        "广昌": ("江西广昌", "26.84", "116.33"),
        "寻邬": ("江西寻乌", "24.95", "115.65"),
        "寻乌": ("江西寻乌", "24.95", "115.65"),
        "瑞金": existing_tuple(locs, "江西瑞金/于都一带"),
        "雩都": existing_tuple(locs, "江西于都"),
        "于都": existing_tuple(locs, "江西于都"),
        "信丰": existing_tuple(locs, "江西信丰百石村"),
        "赣南": existing_tuple(locs, "赣南安远/信丰一带"),
        "全州": existing_tuple(locs, "广西全州湘江一线"),
        "兴安": existing_tuple(locs, "广西兴安/全州湘江一线"),
        "黄沙河": existing_tuple(locs, "广西兴安/全州湘江一线"),
        "通道": existing_tuple(locs, "湖南通道"),
        "黎平": existing_tuple(locs, "贵州黎平"),
        "猴场": existing_tuple(locs, "贵州瓮安猴场"),
        "乌江": existing_tuple(locs, "贵州乌江一线"),
        "遵义老城": existing_tuple(locs, "贵州遵义老城"),
        "遵义": existing_tuple(locs, "贵州遵义"),
        "娄山关": existing_tuple(locs, "贵州娄山关"),
        "苟坝": existing_tuple(locs, "贵州遵义苟坝"),
        "土城": existing_tuple(locs, "贵州习水土城"),
        "赤水": existing_tuple(locs, "贵州土城/赤水河"),
        "二郎滩": existing_tuple(locs, "贵州二郎滩"),
        "太平渡": existing_tuple(locs, "贵州习水太平渡"),
        "茅台": existing_tuple(locs, "贵州茅台"),
        "扎西": existing_tuple(locs, "云南威信扎西"),
        "威信": existing_tuple(locs, "云南威信扎西"),
        "皎平渡": existing_tuple(locs, "云南皎平渡"),
        "金沙江": existing_tuple(locs, "云南皎平渡"),
        "会理": existing_tuple(locs, "四川会理"),
        "安顺场": existing_tuple(locs, "四川石棉安顺场"),
        "大渡河": existing_tuple(locs, "四川安顺场—泸定桥一线"),
        "泸定桥": existing_tuple(locs, "四川泸定桥"),
        "懋功": existing_tuple(locs, "四川懋功/小金"),
        "达维": existing_tuple(locs, "四川小金达维"),
        "两河口": existing_tuple(locs, "四川小金两河口"),
        "毛儿盖": existing_tuple(locs, "四川松潘毛儿盖"),
        "沙窝": existing_tuple(locs, "四川松潘沙窝一带"),
        "包座": existing_tuple(locs, "四川若尔盖包座"),
        "巴西": existing_tuple(locs, "四川若尔盖巴西"),
        "草地": existing_tuple(locs, "四川若尔盖草地"),
        "俄界": existing_tuple(locs, "甘肃迭部俄界"),
        "腊子口": existing_tuple(locs, "甘肃迭部腊子口"),
        "哈达铺": existing_tuple(locs, "甘肃宕昌哈达铺"),
        "榜罗镇": existing_tuple(locs, "甘肃通渭榜罗镇"),
        "会宁": existing_tuple(locs, "甘肃会宁"),
        "将台堡": existing_tuple(locs, "宁夏西吉将台堡"),
        "长汀": ("福建长汀", "25.83", "116.36"),
        "连城": ("福建连城", "25.71", "116.75"),
        "永安": ("福建永安", "25.98", "117.36"),
        "大田": ("福建大田", "25.69", "117.85"),
        "尤溪口": ("福建尤溪口", "26.17", "118.19"),
        "尤溪": ("福建尤溪", "26.17", "118.19"),
        "樟湖板": ("福建南平樟湖", "26.57", "118.55"),
        "水口": ("福建闽侯水口", "26.38", "118.82"),
        "福州": ("福建福州", "26.08", "119.30"),
        "罗源县": ("福建罗源", "26.49", "119.55"),
        "罗源": ("福建罗源", "26.49", "119.55"),
        "通江": ("四川通江", "31.91", "107.25"),
        "南江": ("四川南江", "32.35", "106.84"),
        "巴中": ("四川巴中", "31.86", "106.75"),
        "毛裕镇": ("四川通江毛裕镇", "32.05", "107.05"),
        "清江渡": ("四川巴中清江", "31.72", "106.72"),
        "广元": existing_tuple(locs, "四川广元/剑阁一带"),
        "昭化": ("四川广元昭化", "32.32", "105.97"),
        "旺苍": ("四川旺苍", "32.23", "106.29"),
        "万源": ("四川万源", "32.08", "108.03"),
        "宁羌": ("陕西宁强", "32.83", "106.25"),
        "宁强": ("陕西宁强", "32.83", "106.25"),
        "沔县": ("陕西勉县", "33.15", "106.68"),
        "勉县": ("陕西勉县", "33.15", "106.68"),
        "阳平关": ("陕西宁强阳平关", "32.96", "106.03"),
        "嘉陵江": existing_tuple(locs, "四川苍溪嘉陵江"),
        "苍溪": existing_tuple(locs, "四川苍溪嘉陵江"),
        "衙前": ("江西遂川衙前", "26.45", "114.42"),
        "五斗江": ("江西遂川五斗江", "26.43", "114.37"),
        "遂川": ("江西遂川", "26.33", "114.52"),
        "寨前圩": ("湖南桂东寨前圩", "26.08", "113.91"),
        "桂东": ("湖南桂东", "26.08", "113.94"),
        "新田县": ("湖南新田", "25.91", "112.22"),
        "新田": ("湖南新田", "25.91", "112.22"),
        "灌阳": ("广西灌阳", "25.49", "111.16"),
        "界首": existing_tuple(locs, "广西兴安/全州湘江一线"),
        "湘江": existing_tuple(locs, "广西兴安/全州湘江一线"),
        "大庸": ("湖南大庸/张家界", "29.13", "110.48"),
        "永定镇": ("湖南大庸永定镇", "29.13", "110.48"),
        "永顺塔卧": ("湖南永顺塔卧", "29.13", "109.85"),
        "塔卧": ("湖南永顺塔卧", "29.13", "109.85"),
        "沅陵": ("湖南沅陵", "28.45", "110.40"),
        "鸳鸯山": ("湖南沅陵鸳鸯山", "28.45", "110.40"),
        "常德": ("湖南常德", "29.03", "111.69"),
        "桃源": ("湖南桃源", "28.90", "111.48"),
        "慈利": ("湖南慈利", "29.43", "111.13"),
        "浯溪河": ("湖南桃源浯溪河", "28.86", "111.35"),
        "桑植": existing_tuple(locs, "湖南桑植刘家坪/洪家关"),
        "刘家坪": existing_tuple(locs, "湖南桑植刘家坪/洪家关"),
        "洪家关": existing_tuple(locs, "湖南桑植刘家坪/洪家关"),
        "黄安": ("湖北红安", "31.29", "114.62"),
        "红安": ("湖北红安", "31.29", "114.62"),
        "紫云寨": ("湖北红安紫云寨", "31.29", "114.62"),
        "商城": ("河南商城", "31.80", "115.40"),
        "豹子岩": ("河南商城豹子岩", "31.73", "115.45"),
        "卡房": ("河南新县卡房", "31.58", "114.91"),
        "鄂豫皖": ("鄂豫皖根据地", "31.60", "115.40"),
        "葛藤山": ("河南罗山葛藤山", "31.78", "114.55"),
        "何家冲": existing_tuple(locs, "河南罗山何家冲"),
        "独树镇": existing_tuple(locs, "河南方城独树镇"),
        "伏牛山": existing_tuple(locs, "河南伏牛山一带"),
        "庾家河": existing_tuple(locs, "陕西商洛庾家河"),
        "袁家沟口": existing_tuple(locs, "陕西山阳袁家沟口"),
        "山阳": existing_tuple(locs, "陕西山阳紫荆关一带"),
    }
    return {key: value for key, value in aliases.items() if value}


def find_location(
    text: str, aliases: dict[str, tuple[str, str, str]]
) -> tuple[str, str, str] | None:
    for alias in sorted(aliases, key=len, reverse=True):
        if alias in text:
            return aliases[alias]
    return None


def action_phrase(text: str) -> str | None:
    compact = re.sub(r"\s+", "", text or "")
    compact = re.sub(r"[“”《》]", "", compact)
    patterns = [
        r"(召开[^。；，]{0,18}会议)",
        r"(成立[^。；，]{0,22})",
        r"(改编为[^。；，]{0,24})",
        r"(合编为[^。；，]{0,24})",
        r"(进行[^。；，]{0,14}会谈)",
        r"(达成[^。；，]{0,20}协议)",
        r"(发布[^。；，]{0,22})",
        r"(主力集中[^。；，]{0,20})",
        r"(集结[^。；，]{0,18})",
        r"(开始[^。；，]{0,24})",
        r"(发起[^。；，]{0,24})",
        r"(攻占[^。；，]{0,18})",
        r"(占领[^。；，]{0,18})",
        r"(突破[^。；，]{0,18})",
        r"(渡过[^。；，]{0,18})",
        r"(抢渡[^。；，]{0,18})",
        r"(抵达[^。；，]{0,18})",
        r"(到达[^。；，]{0,18})",
        r"(出发[^。；，]{0,18})",
        r"(北上[^。；，]{0,18})",
        r"(西征[^。；，]{0,18})",
        r"(转移[^。；，]{0,18})",
        r"(会师[^。；，]{0,18})",
        r"(反[^。；，]{0,18}围剿)",
        r"(粉碎[^。；，]{0,18})",
        r"(逝世)",
        r"(牺牲)",
    ]
    for pattern in patterns:
        m = re.search(pattern, compact)
        if m:
            phrase = m.group(1)[:28]
            if phrase.endswith("后") or any(
                bad in phrase
                for bad in ["意图", "得知", "蒋介石派", "蒋介石命令", "凌晨"]
            ):
                return None
            return phrase
    return None


def short_location_label(locname: str) -> str:
    label = re.sub(r"^(江西|福建|湖南|广西|贵州|云南|四川|甘肃|陕西|河南|湖北|宁夏)", "", locname)
    label = label.replace("一带", "").replace("周边", "")
    return label[:10] or locname[:10]


def clean_action(action: str, locname: str, summary: str = "") -> str | None:
    replacements = {
        "开始考虑撤离中央苏区的问题": "筹划撤离中央苏区",
        "进行会谈": "寻乌会谈" if "寻乌" in locname else "进行会谈",
        "主力集中瑞金、雩都地区": "主力向瑞金、于都集结",
        "集结完毕": f"在{short_location_label(locname)}完成集结",
        "集结": f"在{short_location_label(locname)}集结",
        "突破": f"在{short_location_label(locname)}突破封锁",
    }
    action = replacements.get(action, action)
    if action == "成立":
        action = "成立陕甘边特委" if "陕甘边特委" in summary else f"在{short_location_label(locname)}成立组织"
    if "进剿" in action and ("敌军" in summary or "陕军" in summary):
        action = "应对进剿压力"
    if action.startswith("到达国民党") or "告群众书" in action:
        return None
    if len(action) > 28:
        action = action[:27] + "…"
    return action


def infer_type(text: str) -> str:
    if any(k in text for k in ["会议", "决定", "电令", "训令", "指示", "谈判"]):
        return "决策"
    if any(k in text for k in ["战斗", "战役", "攻占", "占领", "歼灭", "击溃", "突破", "围剿", "进剿"]):
        return "战斗"
    if any(k in text for k in ["渡过", "抢渡", "渡江", "湘江", "乌江", "金沙江", "大渡河", "嘉陵江"]):
        return "渡河"
    if any(k in text for k in ["会师", "合编", "改编", "成立", "组建"]):
        return "整编"
    if any(k in text for k in ["出发", "转移", "进军", "北上", "西征", "到达", "抵达", "进抵"]):
        return "行军"
    if any(k in text for k in ["逝世", "牺牲", "中弹"]):
        return "人物"
    return "事件"


def infer_importance(text: str, locname: str) -> str:
    score = 2
    if any(k in text for k in ["会议", "会师", "合编", "改编", "成立", "突破", "抢渡", "渡过", "战役", "攻占", "占领"]):
        score = 3
    if any(
        k in (text + locname)
        for k in ["遵义", "金沙江", "大渡河", "泸定桥", "嘉陵江", "会宁", "吴起", "瓦窑堡", "直罗镇", "何家冲", "湘江", "桑植"]
    ):
        score = 4
    if any(k in text for k in ["逝世", "牺牲"]):
        score = max(score, 3)
    return str(score)


def existing_person_names() -> list[str]:
    _, rows = read_csv(EDIT_DIR / "persons.csv")
    return [r["name"] for r in rows if r.get("name")]


def curated_person_names() -> list[str]:
    return [row["name"] for row in STEAM_PERSON_ROWS if row.get("name")]


def event_id_for(date_text: str, force_id: str, locname: str, action: str) -> str:
    digest = hashlib.sha1(f"{date_text}|{force_id}|{locname}|{action}".encode("utf-8")).hexdigest()[:8]
    return f"steam_{FORCE_ABBR.get(force_id, 'x')}_{date_text}_{digest}"


def selected_event_records(candidates_path: Path, event_rows: list[dict[str, str]], include_existing: bool = False) -> list[dict]:
    locs = canonical_location_map(event_rows)
    aliases = location_aliases(locs)
    people_names = sorted(set(existing_person_names() + curated_person_names()), key=len, reverse=True)
    existing_ids = {row.get("id", "") for row in event_rows}
    existing_keys = {
        (row.get("date", ""), row.get("forceId", ""), row.get("locationName", ""))
        for row in event_rows
    }
    source_counter: Counter[str] = Counter()
    seen: set[tuple[str, str, str, str]] = set()
    proposals: list[dict[str, str]] = []

    with candidates_path.open("r", encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            source_file = row.get("source", "")
            force_id = FORCE_BY_SOURCE.get(source_file)
            if not force_id or source_counter[source_file] >= SOURCE_LIMITS.get(source_file, 0):
                continue

            date_text = normalize_date_label(row.get("date_label", ""))
            if not date_text or date_text < "19320101" or date_text > "19361231":
                continue

            summary = (row.get("summary") or "").strip()
            location = find_location(summary, aliases)
            if not location:
                continue
            locname, lat, lng = location

            action = action_phrase(summary)
            if not action:
                continue
            action = clean_action(action, locname, summary)
            if not action:
                continue
            fingerprint = (date_text, force_id, locname, action[:12])
            if fingerprint in seen:
                continue
            seen.add(fingerprint)
            source_counter[source_file] += 1

            event_id = event_id_for(date_text, force_id, locname, action)
            if not include_existing and (event_id in existing_ids or (date_text, force_id, locname) in existing_keys):
                continue

            force_short = FORCE_SHORT[force_id]
            title = f"{force_short}{action}"
            title = re.sub(rf"^({re.escape(force_short)})\1", r"\1", title)
            if len(title) > 34:
                title = title[:33] + "…"

            people = [name for name in people_names if name in summary]
            participants = list(dict.fromkeys([force_short, *people[:4]]))
            description = (
                f"{row.get('date_label', date_text)}，{force_short}在{locname}一带形成"
                f"“{action}”条目。该条由 补充材料抽取后压缩改写，作为补充路线线索。"
            )

            event_row = {
                    "enabled": "TRUE",
                    "id": event_id,
                    "date": date_text,
                    "displayDate": row.get("date_label", date_text),
                    "sequence": str(9000 + len(proposals) + 1),
                    "forceId": force_id,
                    "type": infer_type(summary),
                    "title": title,
                    "description": description,
                    "locationName": locname,
                    "lat": lat,
                    "lng": lng,
                    "participants": "; ".join(participants),
                    "importance": infer_importance(summary, locname),
                    "sourceIds": STEAM_SOURCE_ID,
                    "certainty": "low",
                    "notes": "Steam《长征1934-1936》本地文本抽取线索，已压缩改写，需继续校订。",
                    "result": "",
                    "casualties": "",
                    "redJoined": "",
                    "redLosses": "",
                    "enemyDefeated": "",
                    "distanceLi": "",
                    "victory": "",
                    "poemLine": "",
                    "poemTitle": "",
                    "poemText": "",
                    "titleEn": "",
                    "descriptionEn": "",
                    "locationNameEn": "",
            }
            proposals.append({"event": event_row, "summary": summary, "source": source_file, "dateLabel": row.get("date_label", date_text)})

    return proposals


def build_proposals(candidates_path: Path, event_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return [record["event"] for record in selected_event_records(candidates_path, event_rows, include_existing=False)]


def ensure_source(rows: list[dict[str, str]]) -> bool:
    if any(row.get("id") == STEAM_SOURCE_ID for row in rows):
        return False
    rows.append(STEAM_SOURCE_ROW.copy())
    return True


def ensure_red7_subject(rows: list[dict[str, str]]) -> bool:
    if any(row.get("id") == RED7_SUBJECT_ID for row in rows):
        return False
    rows.append(RED7_SUBJECT_ROW.copy())
    return True


def ensure_steam_persons(rows: list[dict[str, str]], fieldnames: list[str]) -> int:
    existing = {row.get("id") for row in rows}
    added = 0
    for person in STEAM_PERSON_ROWS:
        if person["id"] in existing:
            continue
        row = {field: "" for field in fieldnames}
        row.update(
            {
                "enabled": "TRUE",
                "id": person["id"],
                "name": person["name"],
                "nameEn": "",
                "personType": person["personType"],
                "birthDate": "",
                "deathDate": "",
                "hometown": "",
                "hometownEn": "",
                "forceId": person["forceId"],
                "summary": person["summary"],
                "summaryEn": "",
                "portrait": "",
                "themeTags": person["themeTags"],
                "sourceIds": STEAM_SOURCE_ID,
                "certainty": "low",
                "sort": person["sort"],
            }
        )
        rows.append(row)
        existing.add(person["id"])
        added += 1
    return added


def split_semicolon(value: str) -> list[str]:
    return [part.strip() for part in re.split(r"[;；]+", value or "") if part.strip()]


def person_id_by_name(person_rows: list[dict[str, str]]) -> dict[str, str]:
    mapping = {row.get("name", ""): row.get("id", "") for row in person_rows if row.get("name") and row.get("id")}
    for alias, person_id in PERSON_ALIASES.items():
        if any(row.get("id") == person_id for row in person_rows):
            mapping[alias] = person_id
    return mapping


def infer_person_role(name: str, text: str) -> str:
    if re.search(re.escape(name) + r".{0,8}(牺牲|逝世|中弹)", text):
        return "牺牲或伤亡线索"
    m = re.search(re.escape(name) + r".{0,4}担任([^。；，]{1,18})", text)
    if m:
        return "担任" + m.group(1)
    if re.search(re.escape(name) + r".{0,6}(率|带领|指挥)", text):
        return "率部或指挥行动"
    if re.search(re.escape(name) + r".{0,8}(决定|提出|报告|致电|命令|会谈)", text):
        return "决策或组织活动"
    return "Steam文本提及"


def enrich_event_participants(event_rows: list[dict[str, str]], person_rows: list[dict[str, str]], candidates_path: Path) -> int:
    id_to_event = {row.get("id"): row for row in event_rows if row.get("id")}
    name_to_id = person_id_by_name(person_rows)
    changed = 0
    for record in selected_event_records(candidates_path, event_rows, include_existing=True):
        event_id = record["event"]["id"]
        event = id_to_event.get(event_id)
        if not event:
            continue
        names = [name for name in name_to_id if name and name in record["summary"]]
        if not names:
            continue
        participants = split_semicolon(event.get("participants", ""))
        before = tuple(participants)
        for name in names:
            canonical = next((row.get("name") for row in person_rows if row.get("id") == name_to_id[name]), name)
            if canonical and canonical not in participants:
                participants.append(canonical)
        if tuple(participants) != before:
            event["participants"] = "; ".join(participants)
            changed += 1
    return changed


def ensure_person_event_links(
    rows: list[dict[str, str]],
    fieldnames: list[str],
    event_rows: list[dict[str, str]],
    person_rows: list[dict[str, str]],
    candidates_path: Path,
) -> int:
    existing = {(row.get("personId"), row.get("eventId")) for row in rows}
    event_ids = {row.get("id") for row in event_rows}
    name_to_id = person_id_by_name(person_rows)
    added = 0
    sort_base = 9000 + len(rows)
    for record in selected_event_records(candidates_path, event_rows, include_existing=True):
        event_id = record["event"]["id"]
        if event_id not in event_ids:
            continue
        for name, person_id in name_to_id.items():
            if not name or name not in record["summary"]:
                continue
            key = (person_id, event_id)
            if key in existing:
                continue
            row = {field: "" for field in fieldnames}
            row.update(
                {
                    "enabled": "TRUE",
                    "personId": person_id,
                    "eventId": event_id,
                    "role": infer_person_role(name, record["summary"]),
                    "note": "由 补充材料候选自动关联，需继续校订。",
                    "sourceIds": STEAM_SOURCE_ID,
                    "sort": str(sort_base + added + 1),
                }
            )
            rows.append(row)
            existing.add(key)
            added += 1
    return added


def ensure_visual_assets(rows: list[dict[str, str]], fieldnames: list[str], person_rows: list[dict[str, str]]) -> int:
    existing_ids = {row.get("id") for row in rows}
    existing_targets = {(row.get("targetType"), row.get("targetId")) for row in rows}
    person_ids = {row.get("id") for row in person_rows}
    added = 0
    for asset_id, person_id, title, alt, file_name, file_page, credit, license_text, sort in STEAM_VISUAL_ROWS:
        if asset_id in existing_ids or ("person", person_id) in existing_targets or person_id not in person_ids:
            continue
        row = {field: "" for field in fieldnames}
        row.update(
            {
                "enabled": "TRUE",
                "id": asset_id,
                "targetType": "person",
                "targetId": person_id,
                "title": title,
                "alt": alt,
                "imageUrl": f"https://commons.wikimedia.org/wiki/Special:FilePath/{file_name}?width=700",
                "imagePageUrl": f"https://commons.wikimedia.org/wiki/{file_page}",
                "credit": credit,
                "license": license_text,
                "sort": sort,
            }
        )
        rows.append(row)
        existing_ids.add(asset_id)
        existing_targets.add(("person", person_id))
        added += 1
    return added


def update_metadata(rows: list[dict[str, str]], proposal_rows: list[dict[str, str]]) -> bool:
    changed = False
    min_date = min((row["date"] for row in proposal_rows), default="")
    if not min_date:
        return False

    values = {row.get("key"): row for row in rows}
    if "timeRange.start" in values:
        current = re.sub(r"\D", "", values["timeRange.start"].get("value", ""))
        if current and min_date < current:
            values["timeRange.start"]["value"] = min_date
            changed = True
    if "description" in values and "Steam" not in values["description"].get("value", ""):
        values["description"]["value"] = values["description"].get("value", "").rstrip("。") + "，并融入Steam文本抽取线索。"
        changed = True
    if "version" in values:
        values["version"]["value"] = "v8-steam-entities"
        changed = True
    return changed


def print_summary(proposals: list[dict[str, str]]) -> None:
    print(f"candidate events to add: {len(proposals)}")
    print("by force:")
    for force_id, count in Counter(row["forceId"] for row in proposals).most_common():
        print(f"  {force_id}: {count}")
    print("by type:")
    for kind, count in Counter(row["type"] for row in proposals).most_common():
        print(f"  {kind}: {count}")
    if proposals:
        print(f"date range: {min(r['date'] for r in proposals)} - {max(r['date'] for r in proposals)}")
        print("sample:")
        for row in proposals[:12]:
            print(f"  {row['date']} {row['forceId']} {row['locationName']} {row['title']}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidates", type=Path, default=DEFAULT_CANDIDATES)
    parser.add_argument("--apply", action="store_true", help="write changes into data_edit CSV files")
    args = parser.parse_args()

    if not args.candidates.exists():
        raise SystemExit(f"missing candidates CSV: {args.candidates}")

    event_fields, event_rows = read_csv(EDIT_DIR / "events.csv")
    source_fields, source_rows = read_csv(EDIT_DIR / "sources.csv")
    subject_fields, subject_rows = read_csv(EDIT_DIR / "subjects.csv")
    metadata_fields, metadata_rows = read_csv(EDIT_DIR / "metadata.csv")
    person_fields, person_rows = read_csv(EDIT_DIR / "persons.csv")
    person_event_fields, person_event_rows = read_csv(EDIT_DIR / "person_events.csv")
    visual_fields, visual_rows = read_csv(EDIT_DIR / "visual_assets.csv")

    proposals = build_proposals(args.candidates, event_rows)
    print_summary(proposals)
    pending_persons = [row for row in STEAM_PERSON_ROWS if row["id"] not in {p.get("id") for p in person_rows}]
    pending_visuals = [row for row in STEAM_VISUAL_ROWS if row[1] not in {v.get("targetId") for v in visual_rows if v.get("targetType") == "person"}]
    print(f"curated persons to add: {len(pending_persons)}")
    print(f"person visuals to add: {len(pending_visuals)}")

    if not args.apply:
        print("dry run only; pass --apply to update CSV tables")
        return 0

    changed_sources = ensure_source(source_rows)
    changed_subjects = ensure_red7_subject(subject_rows)
    changed_metadata = update_metadata(metadata_rows, proposals)
    event_rows.extend(proposals)
    added_persons = ensure_steam_persons(person_rows, person_fields)
    changed_participants = enrich_event_participants(event_rows, person_rows, args.candidates)
    added_person_links = ensure_person_event_links(person_event_rows, person_event_fields, event_rows, person_rows, args.candidates)
    added_visuals = ensure_visual_assets(visual_rows, visual_fields, person_rows)

    if proposals or changed_participants:
        write_csv(EDIT_DIR / "events.csv", event_fields, event_rows)
    if changed_sources:
        write_csv(EDIT_DIR / "sources.csv", source_fields, source_rows)
    if changed_subjects:
        write_csv(EDIT_DIR / "subjects.csv", subject_fields, subject_rows)
    if changed_metadata:
        write_csv(EDIT_DIR / "metadata.csv", metadata_fields, metadata_rows)
    if added_persons:
        write_csv(EDIT_DIR / "persons.csv", person_fields, person_rows)
    if added_person_links:
        write_csv(EDIT_DIR / "person_events.csv", person_event_fields, person_event_rows)
    if added_visuals:
        write_csv(EDIT_DIR / "visual_assets.csv", visual_fields, visual_rows)

    print(
        "applied: "
        f"{len(proposals)} events, "
        f"{added_persons} persons, "
        f"{added_person_links} person-event links, "
        f"{added_visuals} visuals, "
        f"participant_rows_changed={changed_participants}, "
        f"source_added={changed_sources}, "
        f"subject_added={changed_subjects}, "
        f"metadata_changed={changed_metadata}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


