#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P2-1: Comprehensive, auditable adjudication of all 210 low-certainty Steam events.

Actions per low event:
  - UPGRADE_HIGH: Verified verbatim in local authoritative corpus (primarily
    曲爱国、张从田《长征记》人民网党史频道连载 `src_changzhengji_people`).
    Upgrades certainty -> high, sets authoritative sourceIds, corrects title/desc/loc/coords,
    and records exact chapter citation in notes.
  - UPGRADE_MEDIUM: Verified verbatim in firsthand 1937《红军长征记》附录《长征大事记》
    (`src_hongjun_changzhengji`). Upgrades certainty -> medium.
  - DISABLE_DUP: Exact/near duplicate of an existing authoritative/medium event or a
    cross-force clone stamped onto two forces by the Steam extractor. Sets enabled=FALSE
    and remaps any person_events rows to the canonical target eventId (deduplicating).
  - DISABLE_BROKEN: Enemy action misattributed to Red Army, truncated sentence fragment,
    wrong-force/wrong-date hallucination, or contentless generic stub. Sets enabled=FALSE
    and disables/remaps orphaned person_events rows.
  - KEEP_LOW: Genuinely distinct, non-duplicate clue not yet corroborated by local
    authoritative full text. Honestly stays certainty=low, fixes datePrecision (month)
    and cleans obvious template typos (e.g., "一带一带").
"""
from __future__ import annotations

import argparse
import csv
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

# 1) Verified verbatim upgrades to HIGH (authoritative src_changzhengji_people / existing authoritative)
UPGRADE_HIGH: dict[str, dict[str, str]] = {
    # --- red_7th_advance ---
    "steam_r7_19340706_bc42d0bf": {
        "sourceIds": "src_changzhengji_people",
        "title": "红七军团组成北上抗日先遣队从瑞金出发",
        "description": "1934年7月6日，中共中央和中革军委以红七军团为基础组成北上抗日先遣队（寻淮洲任军团长、乐少华任政委、粟裕任参谋长、刘英任政治部主任），六千余名将士从江西瑞金出发北上闽浙赣皖边。",
        "locationName": "江西瑞金",
        "lat": "25.8856", "lng": "116.0270",
        "notes": "【P2权威核实】曲爱国、张从田《长征记》引子（人民网党史频道）明载7月6日红7军团六千余名将士从瑞金出发北上抗日。",
    },
    # --- shaanbei_red ---
    "steam_sg_19321201_8f7ac593": {
        "sourceIds": "src_changzhengji_people",
        "datePrecision": "month",
        "displayDate": "1932年12月",
        "title": "陕甘游击队改编为中国工农红军第二十六军",
        "description": "1932年12月，陕甘游击队在陕西耀县照金一带改编为中国工农红军第二十六军（初编第二团），开始创建陕甘边革命根据地。",
        "notes": "【P2权威核实】曲爱国、张从田《长征记》第十九章（人民网党史频道）明载1932年12月陕甘游击队改编为红26军。",
    },
    # --- red_25th ---
    "steam_r25_19341128_bb9dcee8": {
        "sourceIds": "src_changzhengji_people",
        "title": "红二十五军孤石滩强渡澧河进入伏牛山",
        "description": "1934年11月28日，红二十五军前卫抵达拐河镇东北孤石滩强渡澧河，徐海东指挥红223、225团协力打退国民党军骑步兵南北夹击，杀开进入伏牛山区的通道。",
        "notes": "【P2权威核实】曲爱国、张从田《长征记》第六章（人民网党史频道）详载11月28日孤石滩强渡澧河战斗。",
    },
    "steam_r25_19350409_9f547535": {
        "sourceIds": "src_changzhengji_people",
        "title": "红二十五军九间房伏击战歼灭陕军警三旅",
        "description": "1935年4月9日，东返蓝田县的红二十五军在葛牌镇以南九间房设伏，一举打垮追击的陕军警备第三旅两个团，歼灭一个团又一个营，俘旅长以下官兵千余人。",
        "locationName": "陕西蓝田九间房",
        "lat": "33.9160", "lng": "109.5380",
        "notes": "【P2权威核实并纠偏】曲爱国、张从田《长征记》第六章明载4月9日蓝田葛牌镇以南九间房设伏；原Steam线索误标地点为山阳袁家沟口。",
    },
    "steam_r25_19350610_947d6726": {
        "sourceIds": "src_changzhengji_people",
        "title": "红二十五军跳出合围转向东南奔袭荆紫关",
        "description": "1935年6月上旬，红二十五军由郧西二天门北上商洛庾家河跳至外线，打乱国民党军合围部署后，于6月10日前后掉头向东南大踏步外线机动，奔袭鄂豫陕边要地荆紫关。",
        "notes": "【P2权威核实】曲爱国、张从田《长征记》第六章详载红25军6月上旬北上庾家河跳至外线、随后掉头东南奔袭荆紫关。",
    },
    "steam_r25_19350907_0bb1fca6": {
        "sourceIds": "src_changzhengji_people",
        "title": "中共鄂豫陕省委豹子川会议部署会师陕北",
        "description": "1935年9月7日，红二十五军走出子午岭山区抵达合水东北豹子川（今属甘肃华池县）进入陕甘根据地，中共鄂豫陕省委在此召开会议，决定程子华代省委书记兼政委、徐海东任军长，动员全军迎接会师。",
        "locationName": "甘肃华池豹子川",
        "notes": "【P2权威核实】曲爱国、张从田《长征记》第十九章明载9月7日到达豹子川（今属华池县）并召开省委会议决定领导分工。",
    },
    # --- red_second ---
    "steam_r2_19340807_8d478d0b": {
        "sourceIds": "src_changzhengji_people;src_liulangzhigu_cpc",
        "title": "红六军团突围开始西征探路",
        "description": "1934年8月7日，遵照中共中央和中革军委命令，由任弼时、萧克、王震率领的红六军团从江西遂川五斗江等地突围西征，作为中央红军长征的先遣探路部队转战湘黔边。",
        "notes": "【P2权威核实】曲爱国、张从田《长征记》引子及中国共产党新闻网《红六军团西征》明载红6军团西征部署与出发。",
    },
    "steam_r2_19341026_bed31daa": {
        "sourceIds": "src_changzhengji_people",
        "date": "19341028",
        "displayDate": "1934年10月28日",
        "title": "红二、红六军团由南腰界出发向湘西北进军",
        "description": "1934年10月28日，木黄会师整编后的红二、红六军团从川黔交界的酉阳南腰界出发向湘西北进军，30日顺利进入酉阳城，拉开湘西攻势序幕。",
        "locationName": "重庆酉阳南腰界",
        "notes": "【P2权威核实并校日】曲爱国、张从田《长征记》第三章明载10月28日红2、红6军团由南腰界出发向湘西北进军。",
    },
    "steam_r2_19341117_f6e8ba98": {
        "sourceIds": "src_changzhengji_people",
        "date": "19341124",
        "displayDate": "1934年11月24日",
        "title": "红二、红六军团攻占大庸、桑植形成新苏区雏形",
        "description": "1934年11月24日，红二、红六军团放弃南渡酉水计划果断转向东北，攻占湖南大庸，继占桑植，与已解放的永顺连为一体，构成湘鄂川黔新苏区雏形。",
        "notes": "【P2权威核实并校日】曲爱国、张从田《长征记》第三章明载11月24日攻占大庸并继占桑植（原Steam线索误记11月17日）。",
    },
    "steam_r2_19341215_7a340c8f": {
        "sourceIds": "src_changzhengji_people",
        "title": "红二、红六军团雨夜奔袭桃源梧溪河大捷",
        "description": "1934年12月15日夜，红二、红六军团冒大雨急行军百余里，16日拂晓突袭湖南桃源以北梧溪河，击溃国民党军独立第34旅第701团并冲散援敌第700团，湘西攻势胜利结束。",
        "locationName": "湖南桃源梧溪河",
        "notes": "【P2权威核实】曲爱国、张从田《长征记》第三章详载12月15日雨夜急行军与16日拂晓梧溪河战斗。",
    },
    "steam_r2_19350415_0cfa8218": {
        "sourceIds": "src_changzhengji_people",
        "title": "红二、红六军团陈家河战斗告捷",
        "description": "1935年4月中旬，红二、红六军团采取外线机动与内线防御结合的战法，在湖南桑植陈家河、两河口一带发起猛攻，连获陈家河、桃子溪等战斗胜利，挫败敌军“围剿”。",
        "notes": "【P2权威核实】曲爱国、张从田《长征记》第二十四章明载陈家河、桃子溪等反“围剿”战斗胜利。",
    },
    "steam_r2_19351104_cacf9fff": {
        "sourceIds": "src_changzhengji_people",
        "title": "湘鄂川黔边省委与军委分会刘家坪联席会议",
        "description": "1935年11月4日，中共湘鄂川黔边省委和军委分会在湖南桑植刘家坪召开联席会议，讨论红二、红六军团主力突围转移的三个行动方案，为11月19日战略大转移奠定决策基础。",
        "notes": "【P2权威核实】曲爱国、张从田《长征记》第二十四章《刘家坪决策》明载11月4日桑植刘家坪联席会议。",
    },
    "steam_r2_19360808_73d67866": {
        "sourceIds": "src_changzhengji_people",
        "title": "红二方面军走出草地到达四川包座地区",
        "description": "1936年7月底至8月上旬，红二方面军历经近一个月艰难跋涉走出川西北草地，8月8日前后抵达四川若尔盖上包座地区，随即准备北进甘南。",
        "notes": "【P2权威核实】曲爱国、张从田《长征记》第二十六章明载红二方面军7月底至8月上旬先后走出草地抵达包座地区。",
    },
    "steam_r2_19360901_c8da8719": {
        "sourceIds": "src_changzhengji_people",
        "title": "红二方面军到达甘南哈达铺致电中央拥护团结",
        "description": "1936年8月底至9月初，红二方面军由包座北进抵达甘肃宕昌哈达铺，贺龙、任弼时、关向应联名致电党中央与毛泽东，强调全党团结一致、建立统一集中领导的迫切性。",
        "notes": "【P2权威核实】曲爱国、张从田《长征记》第二十六章明载8月底红二方面军到达哈达铺并致电党中央。",
    },
    "steam_r2_19360907_b93d8d48": {
        "sourceIds": "src_changzhengji_people",
        "title": "红二方面军哈达铺会议制定成徽两康战役计划",
        "description": "1936年9月7日，贺龙、任弼时、关向应等在甘肃宕昌哈达铺召开会议制定战役计划，次日发布《第二方面军基本命令》，决定东出陕甘边界夺取成县、徽县、两当、康县。",
        "notes": "【P2权威核实】曲爱国、张从田《长征记》第二十七章明载9月7日哈达铺会议与次日基本命令。",
    },
    # --- red_fourth ---
    "steam_r4_19341101_625c61d6": {
        "sourceIds": "src_changzhengji_people",
        "date": "19341115",
        "datePrecision": "month",
        "displayDate": "1934年11月中旬",
        "title": "红四方面军巴中清江渡军事会议",
        "description": "1934年11月中旬，反“六路围攻”后川陕苏区物力极端匮乏，西北革命军事委员会在四川巴中清江渡召开红四方面军军事会议，研究下一步战略出路。",
        "locationName": "四川巴中清江渡",
        "notes": "【P2权威核实】曲爱国、张从田《长征记》第十三章明载11月中旬巴中清江渡军事会议。",
    },
    "steam_r4_19350101_d0e44738": {
        "sourceIds": "src_changzhengji_people",
        "datePrecision": "month",
        "displayDate": "1935年1月",
        "title": "红四方面军发起广昭战役",
        "description": "1935年1月，红四方面军在四川广元、昭化、剑阁一带发起广昭战役，其间接到中共中央政治局与中革军委1月22日关于两军协同作战的指示电。",
        "notes": "【P2权威核实】曲爱国、张从田《长征记》第十三章明载广昭战役期间接中央1月22日电示。",
    },
    "steam_r4_19350128_1bddcb38": {
        "sourceIds": "src_changzhengji_people",
        "date": "19350201",
        "datePrecision": "month",
        "displayDate": "1935年2月初",
        "title": "红四方面军旺苍坝紧急会议决定策应中央红军",
        "description": "1935年2月初，红四方面军接到中共中央电报后在四川旺苍坝召开紧急会议，决定以迎接中央红军为当务之急，先行出击陕南调动敌人，再集中主力强渡嘉陵江。",
        "locationName": "四川旺苍坝",
        "notes": "【P2权威核实】曲爱国、张从田《长征记》第十三章明载2月初旺苍坝紧急会议决策出击陕南与强渡嘉陵江。",
    },
    "steam_r4_19350618_8fd3e588": {
        "sourceIds": "src_changzhengji_people",
        "title": "红一、红四方面军懋功会师与干部联欢会",
        "description": "1935年6月18日，中央纵队与红二师翻越夹金山到达四川懋功县城，红三十军政委李先念率部迎候；当晚总政治部召开两军干部联欢会庆祝两大主力胜利会师。",
        "notes": "【P2权威核实】曲爱国、张从田《长征记》第十五章明载6月18日懋功会师与两军干部联欢会。",
    },
    "steam_r4_19350630_e0834dad": {
        "sourceIds": "src_changzhengji_people",
        "date": "19350629",
        "displayDate": "1935年6月29日",
        "title": "中革军委颁布《松潘战役计划》部署北上翻雪山",
        "description": "1935年6月29日，中革军委颁布《松潘战役计划》，统一将红一、红四方面军划分为左、中、右三路军，随后红军陆续翻越梦笔山、长板山等大雪山向松潘、毛儿盖北进。",
        "notes": "【P2权威核实】曲爱国、张从田《长征记》第十六章明载6月29日颁布《松潘战役计划》并开始翻越雪山北进。",
    },
    "steam_r4_19350810_87e82638": {
        "sourceIds": "src_changzhengji_people",
        "title": "中革军委发布夏洮战役计划与右路军北进部署",
        "description": "1935年8月上旬，中革军委发布夏洮战役计划，将红一、红四方面军混合编为左、右两路军分别经阿坝与毛儿盖北穿草地，向包座、班佑和甘南进军。",
        "locationName": "四川松潘毛儿盖",
        "lat": "32.6810", "lng": "103.0580",
        "notes": "【P2权威核实】曲爱国、张从田《长征记》第十七章详载夏洮战役计划与左右路军编成及行动部署。",
    },
    "steam_r4_19351112_3e860ed8": {
        "sourceIds": "src_changzhengji_people",
        "title": "红四方面军打响名山百丈关决战",
        "description": "1935年11月12日，红四方面军南下后的百丈决战在四川名山百丈关拉开帷幕，中纵队与右纵队红四军由雅安、芦山北部向名山、邛崃、大邑方向猛攻，与川军主力展开七昼夜血战。",
        "notes": "【P2权威核实】曲爱国、张从田《长征记》第二十三章明载11月12日百丈决战打响。",
    },
    "steam_r4_19360201_96c83098": {
        "sourceIds": "src_changzhengji_people",
        "date": "19360205",
        "datePrecision": "month",
        "displayDate": "1936年2月上旬",
        "title": "红四方面军下达《康道炉战役计划》转进川康边",
        "description": "1936年2月上旬，面对国民党中央军薛岳部与川军主力大举进犯天全、芦山，红四方面军下达《康道炉战役计划》，决定撤离天芦宝地区，翻越夹金山向道孚、炉霍、甘孜转移。",
        "locationName": "四川宝兴天全一带",
        "lat": "30.3690", "lng": "102.8150",
        "notes": "【P2权威核实并纠偏】曲爱国、张从田《长征记》第二十三章明载2月上旬下达《康道炉战役计划》并撤离天芦宝地区。",
    },
    "steam_r4_19360301_b3951370": {
        "sourceIds": "src_changzhengji_people",
        "title": "红四方面军先头红三十军攻占道孚、炉霍",
        "description": "1936年3月1日，红四方面军先头部队红三十军攻占西康省道孚，15日占领炉霍，随后乘胜攻占甘孜等重镇，为迎接红二、红六军团会师开辟川康边立足点。",
        "locationName": "四川道孚",
        "lat": "30.9800", "lng": "101.1250",
        "notes": "【P2权威核实并纠偏】曲爱国、张从田《长征记》第二十三章明载3月1日攻占道孚、15日占炉霍（原Steam误标懋功/小金）。",
    },
    "steam_r4_19360625_7791aca4": {
        "sourceIds": "src_changzhengji_people",
        "date": "19360626",
        "displayDate": "1936年6月26日",
        "title": "红四方面军部署北上先遣队赴阿坝筹粮",
        "description": "1936年6月下旬，甘孜会师前夕红四方面军全面展开北上准备，26日派李先念率红八十九师及骑兵师先遣经西倾寺赴阿坝筹粮，28日电示各部北上创建西北抗日根据地。",
        "notes": "【P2权威核实】曲爱国、张从田《长征记》第二十六章明载6月26日派先遣队赴阿坝筹粮及28日北上电示。",
    },
    "steam_r4_19360805_a714d9cb": {
        "sourceIds": "src_changzhengji_people",
        "title": "红四方面军出草地率先北进甘南攻占腊子口",
        "description": "1936年8月5日起，已经走出草地的红四方面军率先向甘南挺进，9日前锋红八十八师攻占天险腊子口，红八十九师继克大草滩、哈达铺，打开红二、四方面军进入甘南的通道。",
        "notes": "【P2权威核实】曲爱国、张从田《长征记》第二十六章明载8月5日起红四方面军率先北进甘南、9日攻占腊子口。",
    },
    "steam_r4_19360819_b05b0eed": {
        "sourceIds": "src_changzhengji_people",
        "title": "红四方面军红八十九师攻克甘肃漳县",
        "description": "1936年8月中旬，岷洮西战役进行期间，红四方面军红八十九师攻克甘肃漳县，震撼甘南敌军防线，随后红军乘胜攻克渭源、临潭旧城与通渭等地。",
        "locationName": "甘肃漳县",
        "lat": "34.8490", "lng": "104.4670",
        "notes": "【P2权威核实并纠偏】曲爱国、张从田《长征记》第二十六章明载岷洮西战役期间红89师攻克漳县（原Steam误标坐标为四川若尔盖包座）。",
    },
    "steam_r4_19360918_d283ec43": {
        "sourceIds": "src_changzhengji_people",
        "date": "19360928",
        "displayDate": "1936年9月28日",
        "title": "红四方面军发布《通庄静会战役计划》保障会师",
        "description": "1936年9月下旬，为粉碎胡宗南等部截断西兰大道的企图、保障红军三大主力会师，朱德等发布《通庄静会战役计划》，部署红四方面军迅速进出通渭、庄浪、会宁、静宁地域。",
        "notes": "【P2权威核实】曲爱国、张从田《长征记》第二十七章明载9月28日发布《通庄静会战役计划》。",
    },
    # --- red_first ---
    "steam_rf_19340401_fbf8e3d3": {
        "sourceIds": "src_changzhengji_people",
        "date": "19340428",
        "displayDate": "1934年4月28日",
        "title": "广昌保卫战失利与中央苏区战略转移酝酿",
        "description": "1934年4月28日，持续十八天的广昌保卫战以红军遭受重大伤亡撤离而告终，中央苏区丧失外围屏障与游击区，第五次反“围剿”形势急转直下，战略转移渐成必然。",
        "notes": "【P2权威核实】曲爱国、张从田《长征记》引子明载1934年4月28日广昌保卫战失利及中央苏区危局。",
    },
    "steam_rf_19341204_26d6a580": {
        "sourceIds": "src_changzhengji_people",
        "date": "19341205",
        "displayDate": "1934年12月5日",
        "title": "中央红军翻越长征第一座高山——老山界",
        "description": "1934年12月5日，中央红军放弃北出城步计划继续西进，深入越城岭山区翻越长征后的第一座高山老山界，进入广西龙胜县境，暂时摆脱追敌。",
        "locationName": "广西兴安龙胜老山界",
        "lat": "25.8820", "lng": "110.4190",
        "notes": "【P2权威核实并纠偏】曲爱国、张从田《长征记》第四章明载12月5日翻越老山界入广西龙胜（原Steam误标湖南通道）。",
    },
    "steam_rf_19341211_bf7cff3c": {
        "sourceIds": "src_changzhengji_people",
        "title": "中央红军走出越城岭抵达湖南通道地区",
        "description": "1934年12月11日，中央红军走出越城岭山区进抵湖南通道县境；面临蒋介石在湘西布下的口袋阵，毛泽东次日在通道紧急会议上力主西进敌兵力薄弱的贵州。",
        "notes": "【P2权威核实】曲爱国、张从田《长征记》第四章明载12月11日红军走出越城岭抵达湖南通道。",
    },
    "steam_rf_19341228_0d4feabe": {
        "sourceIds": "src_changzhengji_people",
        "title": "中央红军左纵队进占贵州黄平直扑乌江",
        "description": "1934年12月底，执行黎平会议决议与中革军委12月19日通电部署的中央红军昼夜兼程西进，右纵队进占施秉，左纵队进占贵州黄平，逼近乌江防线。",
        "locationName": "贵州黄平",
        "lat": "26.8970", "lng": "107.9010",
        "notes": "【P2权威核实并纠偏】曲爱国、张从田《长征记》第四章明载12月底左纵队进占黄平（原Steam误标瓮安猴场）。",
    },
    "steam_rf_19350106_3bd576b4": {
        "sourceIds": "src_changzhengji_people",
        "title": "中央红军全线突破乌江天险全部北渡",
        "description": "1935年1月6日，随着江界河、回龙场、茶山关各渡口架桥渡江完成，中央红军全部渡过乌江天险，尾追的国民党军薛岳部望江兴叹，聚歼红军于乌江南岸的图谋破产。",
        "notes": "【P2权威核实】曲爱国、张从田《长征记》第五章明载1月6日中央红军全部渡过乌江。",
    },
    "steam_rf_19350108_c54bd2a5": {
        "sourceIds": "src_changzhengji_people",
        "title": "红四团追击黔军夺占娄山关与桐梓",
        "description": "1935年1月初解放遵义后，突破乌江的英雄团红四团乘胜北追向桐梓撤退的黔军，一举夺占黔北险隘娄山关并进占桐梓县城，打开遵义北翼通道。",
        "locationName": "贵州桐梓娄山关",
        "notes": "【P2权威核实】曲爱国、张从田《长征记》第五章明载遵义解放后红4团夺占娄山关并追击黔军占领桐梓。",
    },
    "steam_rf_19350112_ac6c45bc": {
        "sourceIds": "src_changzhengji_people",
        "title": "中央红军在遵义召开群众大会成立革命委员会",
        "description": "1935年1月12日，中央红军在遵义省立第三中学操场召开群众大会，毛泽东、朱德、李富春等出席演说宣传党和红军宗旨，宣布正式成立由25人组成的遵义县革命委员会。",
        "notes": "【P2权威核实】曲爱国、张从田《长征记》第七章明载1月12日遵义省立三中操场群众大会与革命委员会成立。",
    },
    "steam_rf_19350208_b9f42420": {
        "sourceIds": "src_changzhengji_people",
        "title": "中共中央政治局威信大河滩会议通过《遵义会议决议》",
        "description": "1935年2月8日，中共中央政治局常委在云南威信大河滩举行会议，正式审查通过张闻天起草的《中共中央关于反对敌人五次“围剿”的总结决议》（即《遵义会议决议》），随即在全军传达。",
        "locationName": "云南威信大河滩",
        "lat": "27.8480", "lng": "105.0500",
        "notes": "【P2权威核实并纠偏】曲爱国、张从田《长征记》第七、八章明载2月8日在云南威信大河滩正式通过《遵义会议决议》（原Steam误标贵州遵义）。",
    },
    "steam_rf_19350211_7d71a0ce": {
        "sourceIds": "src_changzhengji_people",
        "title": "中央红军由扎西挥师东进拉开二渡赤水序幕",
        "description": "1935年2月11日，完成扎西整编的中央红军各军团遵照中革军委部署，出敌不意地由云南威信扎西地区回师东进，直指敌人兵力空虚的黔北，拉开二渡赤水序幕。",
        "notes": "【P2权威核实】曲爱国、张从田《长征记》第八章明载2月11日中央红军各军团由扎西开始东进。",
    },
    "steam_rf_19350227_20de8032": {
        "sourceIds": "src_changzhengji_people",
        "title": "中革军委电令红一、红三军团夜袭攻占遵义城",
        "description": "1935年2月27日，中革军委电示红一、红三军团当晚解决遵义城中之敌并准备迎击吴奇伟援军，红军迅速再克遵义，随后在遵义城南老鸦山等地大败敌增援两个师。",
        "notes": "【P2权威核实】曲爱国、张从田《长征记》第八章明载2月27日中革军委攻打遵义及迎击援敌部署。",
    },
    "steam_rf_19350301_65c158f9": {
        "sourceIds": "src_changzhengji_people",
        "date": "19350210",
        "datePrecision": "month",
        "displayDate": "1935年2月上旬",
        "title": "中共中央在扎西组建川南特委与红军川南游击纵队",
        "description": "1935年2月扎西集结期间，中共中央决定由徐策、余泽鸿等组成川南特委，并从红军抽调数百人在云南威信石坎子组建中国工农红军川南游击纵队，在川滇黔边开展游击战策应主力。",
        "locationName": "云南威信扎西石坎子",
        "lat": "27.8450", "lng": "105.0480",
        "notes": "【P2权威核实并去重合并】曲爱国、张从田《长征记》第八章明载扎西整编期间于石坎子组建川南游击纵队；并归并原2月1日重复条 steam_rf_19350201_92b3b59c。",
    },
    "steam_rf_19350319_56029670": {
        "sourceIds": "src_changzhengji_people",
        "title": "中央红军西进古蔺击溃镇龙山川军巧布疑兵",
        "description": "1935年3月19日，三渡赤水入川南的中央红军进至古蔺镇龙山，击溃川军廖九甫团后进抵铁厂、两河口一带，进一步加深蒋介石红军将北渡长江的错觉，为秘密四渡赤水创造战机。",
        "notes": "【P2权威核实】曲爱国、张从田《长征记》第九章明载3月19日镇龙山战斗与巧布疑兵。",
    },
    "steam_rf_19350328_b3c4099f": {
        "sourceIds": "src_changzhengji_people",
        "title": "中央红军冒暴雨穿越鸭溪、白腊坎封锁线",
        "description": "1935年3月28日，四渡赤水后的中央红军主力乘敌错判之机，冒着狂风暴雨从鸭溪、白腊坎之间国民党军封锁线的空隙秘密南穿，进抵乌江北岸沙土、安底地区。",
        "locationName": "贵州遵义鸭溪白腊坎",
        "lat": "27.5580", "lng": "106.7180",
        "notes": "【P2权威核实】曲爱国、张从田《长征记》第九章明载3月28日红军主力冒暴雨穿越鸭溪、白腊坎封锁线。",
    },
    "steam_rf_19350418_0daf060c": {
        "sourceIds": "src_changzhengji_people",
        "title": "中央红军渡过北盘江连克贞丰、兴仁、兴义",
        "description": "1935年4月18日，中央红军主力在白层、者坪渡过北盘江，随即分两路疾进，北路连克广顺、贞丰、兴仁，南路攻克安龙、兴义，逼近滇黔边境，彻底摆脱贵州追敌。",
        "notes": "【P2权威核实】曲爱国、张从田《长征记》第十章明载4月18日渡北盘江及两路克贞丰、兴仁、安龙、兴义。",
    },
    "steam_rf_19350527_848551db": {
        "sourceIds": "src_changzhengji_people",
        "title": "中央红军沿大渡河两岸急行军奔向泸定桥",
        "description": "1935年5月27日拂晓，为解决安顺场渡船稀少难题，中央红军两路部队经短暂休息后沿大渡河两岸百余公里悬崖栈道急行军昼夜兼程奔袭泸定桥。",
        "notes": "【P2权威核实】曲爱国、张从田《长征记》第十二章明载5月27日拂晓红军两路部队急行军奔向泸定桥。",
    },
    "steam_rf_19350608_e864a72e": {
        "sourceIds": "src_changzhengji_people",
        "title": "红一团里应外合夜克芦山，中央部署迅取懋功会师",
        "description": "1935年6月8日，红一团侦察队化装潜入四川芦山城与城外主力里应外合夜克芦山；同日中共中央、中革军委明确战略任务为以主力迅取懋功，用一切努力与红四方面军直接会合。",
        "locationName": "四川芦山",
        "lat": "30.1440", "lng": "102.9270",
        "notes": "【P2权威核实并纠偏】曲爱国、张从田《长征记》第十四章明载6月8日夜克芦山及中央关于迅取懋功会师的指示（原Steam误标懋功/小金）。",
    },
    "steam_rf_19350623_a6870c49": {
        "sourceIds": "src_changzhengji_people",
        "title": "军委纵队离开懋功北上到达两河口",
        "description": "1935年6月23日，中革军委纵队离开四川懋功，沿商旅古道经双柏、八角、木坡、抚边北上，24日抵达两河口准备召开决定北上战略方针的两河口政治局会议。",
        "notes": "【P2权威核实】曲爱国、张从田《长征记》第十五章明载6月23日军委纵队离开懋功赴两河口。",
    },
    "steam_rf_19350911_0527e5da": {
        "sourceIds": "src_changzhengji_people",
        "title": "党中央率军委纵队与红三军抵甘肃俄界会合红一军",
        "description": "1935年9月11日，党中央、军委纵队及红三军走过四川境内最后村寨下黄寨进入甘肃省境，沿包座河经迭部县达拉乡岗岭村抵达俄界，与先期北上的红一军胜利会合。",
        "notes": "【P2权威核实】曲爱国、张从田《长征记》第十八章明载9月11日中央与红3军到达俄界会合红1军。",
    },
    "steam_rf_19350918_643ef3c2": {
        "sourceIds": "src_changzhengji_people",
        "title": "红一军先头部队突破腊子口后进占甘南哈达铺",
        "description": "1935年9月18日，突破天险腊子口的红一军团主力甩开岷州国民党军挥师东进，进占甘肃宕昌哈达铺；红军在此获取陕北红军与苏区存在的报纸消息并整编为陕甘支队。",
        "notes": "【P2权威核实】曲爱国、张从田《长征记》第二十章明载9月18日进占哈达铺及后续整编。",
    },
    "steam_rf_19350928_e08cd64f": {
        "sourceIds": "src_changzhengji_people",
        "title": "中共中央政治局常委榜罗镇会议定策落脚陕北",
        "description": "1935年9月28日，中共中央政治局在甘肃通渭榜罗镇召开常委会议，根据新获得的陕北形势与全国抗日救亡动向，正式改变俄界会议原定方案，决定把中央和红军长征落脚点放在陕北。",
        "locationName": "甘肃通渭榜罗镇",
        "lat": "35.1620", "lng": "105.0510",
        "notes": "【P2权威核实并纠偏】曲爱国、张从田《长征记》第二十章明载9月28日政治局常委榜罗镇会议决断落脚陕北（原Steam误标宕昌哈达铺）。",
    },
    "steam_rf_19350929_0930da67": {
        "sourceIds": "src_changzhengji_people",
        "title": "陕甘支队离开榜罗镇继续北进通渭",
        "description": "1935年9月29日，陕甘支队离开通渭榜罗镇地区继续北进，随即占领通渭城并在城中休整，国民党西北各路守军划地自保未能形成有效拦阻。",
        "notes": "【P2权威核实】曲爱国、张从田《长征记》第二十章明载9月29日陕甘支队离开榜罗镇继续北进。",
    },
}

# 2) Verified verbatim upgrades to MEDIUM (firsthand 1937《红军长征记》附录《长征大事记》)
UPGRADE_MEDIUM: dict[str, dict[str, str]] = {
    "steam_rf_19341215_77b32a71": {
        "sourceIds": "src_hongjun_changzhengji",
        "title": "中央红军进抵黎平、锦屏一带",
        "description": "1934年12月15日，中央红军各军团向黔东南黎平、老锦屏推进，据1937年《红军长征记》附录《长征大事记》载，红九军团继续向锦屏前进，红一军团抵八漂、红三军团抵中温平铺。",
        "notes": "【P2一手核实】1937年《红军长征记》附录《长征大事记》1934年12月15日逐日条目确证各军团向黎平、锦屏推进。",
    },
    "steam_rf_19341231_79ca4187": {
        "sourceIds": "src_hongjun_changzhengji",
        "title": "中央红军进抵猴场、瓮安并侦察乌江渡口",
        "description": "1934年12月31日，中央红军军委纵队抵达瓮安猴场，红三军团第四师攻占瓮安，红一军团第二师进至水老给及其东北地域侦察江界河乌江渡河点，准备强渡乌江。",
        "notes": "【P2一手核实】1937年《红军长征记》附录《长征大事记》1934年12月31日逐日条目确证。",
    },
}

# 3) Duplicates & cross-force clones -> disable and remap person_events to canonical eventId
# Mapping: old_steam_id -> (canonical_target_id, reason)
DISABLE_DUP: dict[str, tuple[str, str]] = {
    # --- red_25th duplicates ---
    "steam_r25_19341111_6bb7d2f0": ("ev_red25_19341111_declare", "与权威条目 ev_red25_19341111_declare（11月11日红25军发布出发宣言）完全重复"),
    "steam_r25_19341209_63652e47": ("ev_czj_19341210_yujiahe", "与权威条目 ev_czj_19341210_yujiahe（12月10日庾家河会议与战斗）近重复"),
    "steam_r25_19341210_9defdcc6": ("ev_red25_19341116_yujiahe", "与权威条目 ev_red25_19341116_yujiahe（12月10日庾家河第十八次常委会议）完全重复"),
    "steam_r25_19350701_0d09cb91": ("r25_19350702_yuanjiagou", "与权威条目 r25_19350702_yuanjiagou（袁家沟口战斗）重复"),
    "steam_r25_19350715_989523ae": ("r25_19350716_fengyukou", "与已有条目 r25_19350716_fengyukou（沣峪口会议及西征北上）近重复"),
    "steam_r25_19350904_cb1e11f2": ("ev_czj_19350904_banqiao", "残缺标题“红二十五军出发时”且与权威条目 ev_czj_19350904_banqiao（9月4日板桥战斗）重复"),
    # --- red_second duplicates / clones ---
    "steam_r2_19341216_c361ccb1": ("steam_r2_19341215_7a340c8f", "与已核实升级条目 12月15-16日梧溪河战斗重复（且把红12团短暂受挫误写为全军后撤）"),
    "steam_r2_19351101_02b16718": ("r2_19351119_sangzhi_start", "泛化条目“转移前的各种准备”，已有 r2_19351119_sangzhi_start 与刘家坪决策覆盖"),
    "steam_r2_19351120_61a7cbc3": ("r2_19351120_lishui", "与已有条目 r2_19351120_lishui（11月20日渡过澧水）完全重复"),
    "steam_r2_19360714_c77f41eb": ("r2_19360710_northward", "泛化标题“出发”且与权威条目 r2_19360710_northward 重复并跨部队克隆"),
    "steam_r2_19360801_5231f9b1": ("steam_r2_19360808_73d67866", "与已核实升级条目 1936年8月上旬红二方面军抵包座北进重复"),
    "steam_r2_19360805_fc5a9936": ("steam_r4_19360805_a714d9cb", "跨部队克隆（与红四方面军8月5日出草地北进腊子口重录，当时红二方面军尚未抵腊子口）"),
    "steam_r2_19360911_698af2f2": ("r2_19360915_chenghuiliangkang", "泛化标题“出发”且错标地点甘肃会宁，与权威条目成徽两康战役衔接重复"),
    # --- red_fourth duplicates / cross-force clones ---
    "steam_r4_19350203_b2abd803": ("ev_czj_19350203_shaanan", "与权威条目 ev_czj_19350203_shaanan（2月3日陕南战役）完全重复"),
    "steam_r4_19350601_361cce9b": ("steam_r4_19350618_8fd3e588", "残缺句子且与已核实升级条目 6月18日懋功会师联欢会重复"),
    "steam_r4_19350612_c2405efb": ("r4_19350612_davi_meeting", "与已有条目 r4_19350612_davi_meeting（6月12日达维会师）完全重复"),
    "steam_r4_19350617_c225f981": ("r4_19350612_davi_meeting", "实为中央领导翻夹金山抵达维（非红四方面军行动），且与达维会师集群重复"),
    "steam_r4_19350623_be9f5ab0": ("steam_rf_19350623_a6870c49", "跨部队克隆（6月23日系中央军委纵队离懋功赴两河口）"),
    "steam_r4_19350625_ac761650": ("r4_19350626_lianghekou", "跨部队克隆且与两河口会议条目 r4_19350626_lianghekou 近重复"),
    "steam_r4_19350710_0e7cbd6c": ("r4_19350815_maoergai", "跨部队克隆（与红一方面军同日抵达毛儿盖重录）"),
    "steam_r4_19350716_b268a97c": ("r4_19350815_maoergai", "跨部队克隆（与 steam_rf_19350716_19abfe08 占领毛儿盖重录）"),
    "steam_r4_19350728_1ef1ae52": ("r4_19350815_maoergai", "跨部队克隆（与 steam_rf_19350728_d52faa6a 到达毛儿盖重录）"),
    "steam_r4_19350804_85acb4ce": ("rf_19350804_shawo", "跨部队克隆且与已有沙窝会议条目重复"),
    "steam_r4_19350813_8ac3c24d": ("r4_19350815_maoergai", "跨部队克隆且与毛儿盖会议条目近重复"),
    "steam_r4_19350818_e2a6765c": ("r4_19350815_maoergai", "泛化标题“出发”且跨部队克隆"),
    "steam_r4_19350819_86dfae3a": ("r4_19350815_maoergai", "跨部队克隆且与8月20日毛儿盖政治局会议重复"),
    "steam_r4_19350820_a4366fdb": ("r4_19350815_maoergai", "与已有毛儿盖会议条目 r4_19350815_maoergai 重复"),
    "steam_r4_19350826_4441212e": ("rfour_19350829_baozuo", "泛化标题“北上”且与包座战斗重复"),
    "steam_r4_19350827_3a82e56d": ("rfour_19350829_baozuo", "残缺标题且与包座战斗 rfour_19350829_baozuo 重复"),
    "steam_r4_19350831_eb3b93c0": ("rfour_19350829_baozuo", "与包座战斗 rfour_19350829_baozuo 重复"),
    "steam_r4_19351007_509f379b": ("ev_red4_19351007_suichong", "与权威条目 ev_red4_19351007_suichong（绥崇丹懋战役）完全重复且错写地点湖南通道"),
    "steam_r4_19360701_f441f9e0": ("rfour_19360703_ganzi_meeting", "残缺短语且与权威条目甘孜会师会议重复"),
    "steam_r4_19360714_25149dc1": ("r4_19360710_northward", "泛化标题“出发”且与权威条目 r4_19360710_northward 重复"),
    "steam_r4_19360730_4557afac": ("steam_r4_19360805_a714d9cb", "与8月初红四方面军出草地抵包座北进甘南近重复"),
    "steam_r4_19360907_d3ee222a": ("ev_red4_19360907_tongwei", "与权威条目 ev_red4_19360907_tongwei（红四方面军占领通渭）完全重复"),
    "steam_r4_19360914_37586873": ("ev_red4_19360914_jiangtaibao", "与权威条目 ev_red4_19360914_jiangtaibao（红四方面军占领将台堡）完全重复"),
    "steam_r4_19360930_91576ac3": ("ev_red4_19360930_qingjiangyi", "与权威条目 ev_red4_19360930_qingjiangyi（占领青江驿、翟家所）完全重复"),
    "steam_r4_19361002_f447cac2": ("ev_red4_19361002_huining", "与权威条目 ev_red4_19361002_huining（进占会宁县城）完全重复"),
    "steam_r4_19361010_86a05ab4": ("ev_red4_19361010_meeting", "与权威条目 ev_red4_19361010_meeting（三大主力会宁会师庆祝大会）完全重复"),
    # --- red_first duplicates / near-duplicates ---
    "steam_rf_19341007_fce7998a": ("rf_19341010_ruijin", "与已有条目 rf_19341010_ruijin（中央红军瑞金/于都集结出发）近重复"),
    "steam_rf_19341016_6cb371a0": ("rf_19341017_yudu", "与已有条目 rf_19341017_yudu（于都集结并渡于都河）近重复"),
    "steam_rf_19341025_2e33bd01": ("dashi_19341024", "与已有1934年10月逐日大事记条目及信丰突破第一道封锁线重复"),
    "steam_rf_19341124_8fd68573": ("dashi_19341123", "与已有1934年11月逐日大事记条目重复"),
    "steam_rf_19350102_2c6c33dd": ("czj_19350102_wujiang_jiangjiehe", "与权威条目 czj_19350102_wujiang_jiangjiehe（1月2日强渡乌江）近重复"),
    "steam_rf_19350105_99e9e135": ("rf_19350107_zunyi_city", "与已有条目 rf_19350107_zunyi_city（攻占遵义）近重复"),
    "steam_rf_19350124_1cc588e8": ("rf_19350128_tucheng", "与已有土城战斗集群近重复"),
    "steam_rf_19350125_6290b47a": ("rf_19350128_tucheng", "与已有土城战斗集群近重复"),
    "steam_rf_19350128_205c4223": ("ev_czj_19350128_tucheng", "与权威条目 ev_czj_19350128_tucheng（1月28日土城战斗与一渡赤水紧急会议）完全重复"),
    "steam_rf_19350201_92b3b59c": ("steam_rf_19350301_65c158f9", "与已核实升级条目“扎西组建川南游击纵队”重复"),
    "steam_rf_19350207_a720e66b": ("steam_rf_19350208_b9f42420", "与已核实升级条目 2月8日威信大河滩会议近重复"),
    "steam_rf_19350210_24f02cba": ("ev_czj_19350210_zhaxi", "与权威条目 ev_czj_19350210_zhaxi（2月10日扎西整编会议）重复且错标地点贵州遵义"),
    "steam_rf_19350315_f98945c3": ("rf_19350316_maotai_chishui3", "与三渡赤水条目 rf_19350316_maotai_chishui3 近重复"),
    "steam_rf_19350326_bda4a11f": ("ev_czj_193503_r9", "与权威条目 ev_czj_193503_r9（红9军团在马鬃岭、干溪伪装主力牵敌）完全重复"),
    "steam_rf_19350331_91d3a546": ("rf_19350331_guiyang", "与同日条目 rf_19350331_guiyang（南渡乌江佯逼贵阳）重复"),
    "steam_rf_19350429_4b7f9aa3": ("rf_19350429_jiaopingdu_start", "与同日条目 rf_19350429_jiaopingdu_start（巧渡金沙江开始）完全重复"),
    "steam_rf_19350511_05133c0d": ("rf_19350512_huili", "与次日条目 rf_19350512_huili（会理会议）近重复且错标地点云南皎平渡"),
    "steam_rf_19350625_600648e4": ("rf_19350626_lianghekou", "与次日条目 rf_19350626_lianghekou（两河口会议）重复"),
    "steam_rf_19350701_14d2a1a8": ("steam_rf_19350630_f1f50f21", "与前日权威条目（翻越梦笔山北进毛儿盖）近重复"),
    "steam_rf_19350710_b3a76e11": ("rf_19350804_shawo", "与一、四方面军进抵毛儿盖/沙窝集群重复"),
    "steam_rf_19350716_19abfe08": ("rf_19350804_shawo", "与红军进驻毛儿盖集群重复"),
    "steam_rf_19350728_d52faa6a": ("rf_19350804_shawo", "与毛儿盖/沙窝会议前集结重复"),
    "steam_rf_19350801_4e5f4183": ("rf_19350829_baozuo", "日期错标8月1日（描述却称8月底占领包座后计划），与包座战斗重复"),
    "steam_rf_19350804_e6705bd9": ("rf_19350804_shawo", "与同日已有条目 rf_19350804_shawo（沙窝会议）完全重复"),
    "steam_rf_19350810_6fd1c6a4": ("steam_r4_19350810_87e82638", "与已核实升级条目 8月上旬夏洮战役与右路军计划跨部队重复"),
    "steam_rf_19350813_c37cc3de": ("rf_19350820_maoergai", "与毛儿盖会议集群重复"),
    "steam_rf_19350819_3539c722": ("rf_19350820_maoergai", "与次日毛儿盖政治局会议 rf_19350820_maoergai 重复"),
    "steam_rf_19350827_b8fbb8d7": ("rf_19350829_baozuo", "残缺标题且与包座战斗 rf_19350829_baozuo 重复"),
    "steam_rf_19350831_e91c2d1a": ("rf_19350829_baozuo", "与包座战斗 rf_19350829_baozuo 重复"),
    "steam_rf_19350906_80ea8a31": ("rf_19350912_ejie", "时间错前（9月6日中央尚在巴西，11日方抵俄界），与俄界条目重复"),
    "steam_rf_19350910_6eedebf7": ("rf_19350909_baxi", "与巴西会议单独北上 rf_19350909_baxi 近重复"),
    "steam_rf_19350914_6a9837b9": ("rf_19350912_ejie", "北上途中致电争取红四方面军，与俄界会议后续衔接，人物关联归并至俄界会议"),
    "steam_rf_19350922_c028f45a": ("rf_19350923_minshan", "泛化标题“北上抗日”且与哈达铺/翻越岷山重录"),
}

# 4) Broken / enemy-misattributed / truncated / wrong-force hallucinations / contentless generic stubs
# Mapping: old_steam_id -> (optional_remap_target_or_None, reason)
DISABLE_BROKEN: dict[str, tuple[str | None, str]] = {
    # --- red_7th_advance ---
    "steam_r7_19340807_76e0c820": (None, "泛化无信息标题“发起攻击”"),
    "steam_r7_19340815_90b9a1a5": (None, "泛化无信息标题“出发”"),
    # --- red_25th ---
    "steam_r25_19331002_e8a39e9a": (None, "残缺短语“占领的根据地空隙地区”"),
    "steam_r25_19340701_4735e2b7": (None, "主语倒置错误（系国民党军围剿鄂豫皖，非红二十五军发起围剿）"),
    "steam_r25_19340701_e7b44271": (None, "残缺抽象碎片“转移暂时被搁置”"),
    "steam_r25_19341108_ff2e539b": (None, "严重截断残句“北上抗日的通知、7月29日中央书记处关于”"),
    # --- red_second ---
    "steam_r2_19340812_8c9582bf": (None, "残缺空壳标题“红二、红六军团成立”（且当时红六军团尚未与红三军会师）"),
    "steam_r2_19341125_303e8b71": (None, "残缺空壳标题“红二、红六军团成立”"),
    "steam_r2_19341126_b6d97637": (None, "残缺空壳标题“红二、红六军团成立”"),
    "steam_r2_19341205_f39cbe8b": ("steam_r2_19341215_7a340c8f", "泛化空壳标题“出发”，将8条湘西攻势人物关联重映射至已核实梧溪河战役"),
    "steam_r2_19350208_2f22ec7e": (None, "截断残句“红二、红六军团开始”"),
    "steam_r2_19350315_83fcc6d9": (None, "主语严重倒置错误（“集结兵力与红军主力决战”实为国民党军围剿行动）"),
    "steam_r2_19350405_bc5ceb4f": (None, "截断电文碎片“转移才得以保存部队有生力量或渡江困难不大”"),
    "steam_r2_19350412_d6065517": (None, "泛化空壳标题“转移”"),
    "steam_r2_19350416_d9802f0c": (None, "残缺句“开始的战略反攻”"),
    "steam_r2_19351010_e82fe7cd": (None, "主语严重倒置错误（宜昌行辕系国民党军设置，误套红二、红六军团）"),
    "steam_r2_19360214_9cb42d29": (None, "主语倒置错误（“占领打鼓新场后进行反扑”将敌军反扑误套红军）"),
    # --- red_fourth ---
    "steam_r4_19350601_ea1bdb51": (None, "泛化空壳标题“出发西进”"),
    "steam_r4_19350621_8523be9c": ("r4_19350626_lianghekou", "泛化空壳标题“北上”，重映射人物关联至两河口会议"),
    "steam_r4_19350701_3c9731fc": (None, "主语严重倒置错误（系敌薛岳部召开师以上将领军事会议，误套红四方面军）"),
    "steam_r4_19350701_b5d05eb4": (None, "敌情错套或残缺（松潘一带系胡宗南部集结阻截红军）"),
    "steam_r4_19350906_e68a7685": ("rf_19350912_ejie", "部队串台错误（红四方面军未赴俄界，系中央红军北上行程误标）"),
    "steam_r4_19350910_861d25a1": ("rf_19350909_baxi", "部队串台错误（拉界系中央红军单独北上经过地，误标红四方面军）"),
    "steam_r4_19350911_fe6fa941": ("steam_rf_19350911_0527e5da", "部队串台错误（9月11日抵俄界系中央与红三军，误标红四方面军）"),
    "steam_r4_19350912_7570bd63": ("rf_19350912_ejie", "部队串台错误（9月12日俄界政治局扩大会议系中央红军召开，误标红四方面军）"),
    "steam_r4_19351015_c52687db": (None, "泛化空壳标题“发起进攻”"),
    # --- red_first ---
    "steam_rf_19341220_d3104c4f": ("rf_19341218_liping", "泛化空壳标题“出发”，人物关联归并至黎平会议"),
    "steam_rf_19350103_1a9e8b5e": (None, "截断残句“中央红军开始”"),
    "steam_rf_19350109_3f215920": (None, "泛化空壳标题“开始进攻”"),
    "steam_rf_19350119_0b0af7cc": (None, "泛化空壳标题“开始北上”"),
    "steam_rf_19350126_f406083d": ("ev_czj_19350128_tucheng", "截断半句“到达离赤水城15公里的黄陂洞时”，人物关联归并至土城战斗"),
    "steam_rf_19350205_7274f529": ("ev_zhaxi_19350205", "史实地点严重错误（2月5日中央红军已抵云南威信水田寨，绝非“在遵义集结”）"),
    "steam_rf_19350224_cfc285f2": (None, "泛化空壳标题“发起突袭”且次日已有娄山关战斗"),
    "steam_rf_19350228_c8057ffe": (None, "泛化空壳标题“发起反攻”且同日已有娄山关大捷条目"),
    "steam_rf_19350311_0b6e9300": ("rf_19350310_gouba", "史实日期错误（3月11日处于苟坝会议期间，并非“占领遵义”）"),
    "steam_rf_19350313_9baa5690": (None, "泛化空壳标题“转移”"),
    "steam_rf_19350501_2249f1a5": (None, "泛化空壳标题“北上”"),
    "steam_rf_19350701_f7c6a4b0": (None, "主语严重倒置错误（“召开了敌薛岳部师以上将领参加的军事会议”系敌军会议误套红军）"),
    "steam_rf_19350818_973df4a8": (None, "泛化空壳标题“出发”"),
    "steam_rf_19350826_5a51264a": (None, "泛化空壳标题“北上”"),
    "steam_rf_19350913_4fff86dd": (None, "泛化空壳标题“出发”"),
}

# 5) Honest KEEP_LOW (distinct non-duplicate historical clues not yet corroborated locally)
# We also fix obvious Steam template typos ("一带一带", unclosed parens, wrong desc province, month precision).
KEEP_LOW_CLEANUPS: dict[str, dict[str, str]] = {
    # red_7th_advance (5 clean clues)
    "steam_r7_19340701_16c8ca65": {"datePrecision": "month", "displayDate": "1934年7月下旬"},
    "steam_r7_19340729_630232e8": {},
    "steam_r7_19340730_5bfff113": {},
    "steam_r7_19340801_b4ee853f": {},
    "steam_r7_19340903_da1e617f": {},
    # shaanbei_red (14 clean clues; most are 1933-1935 regional spark_march)
    "steam_sg_19330301_0f21f603": {"datePrecision": "month", "displayDate": "1933年3月"},
    "steam_sg_19330405_a46bd176": {},
    "steam_sg_19330501_ca6bb3b9": {"datePrecision": "month", "displayDate": "1933年5月"},
    "steam_sg_19330701_5ee074e8": {"datePrecision": "month", "displayDate": "1933年7月", "description": "1933年7月，陕甘红军在陕西安定一带召开扩大会议。"},
    "steam_sg_19330801_8f0303e3": {"datePrecision": "range", "displayDate": "1933年8月—1934年7月", "description": "1933年8月至1934年7月间，陕北党组织在陕西安定一带成立陕北红军游击队总指挥部。"},
    "steam_sg_19331001_6ab9782a": {"datePrecision": "month", "displayDate": "1933年10月上旬"},
    "steam_sg_19331017_7b950220": {"locationName": "甘肃合水", "lat": "35.8190", "lng": "108.0200", "description": "1933年10月17日，陕甘红军占领甘肃合水县城。"},
    "steam_sg_19331101_06c92b80": {"datePrecision": "month", "displayDate": "1933年11月上旬"},
    "steam_sg_19340101_8772074b": {"datePrecision": "month", "displayDate": "1934年1月"},
    "steam_sg_19340801_9fe35e4a": {"datePrecision": "month", "displayDate": "1934年8月"},
    "steam_sg_19350101_97c6888f": {"datePrecision": "month", "displayDate": "1935年1月", "description": "1935年1月，陕甘红军在陕西安定一带成立革命委员会。"},
    "steam_sg_19350205_d51d7e65": {"description": "1935年2月5日，陕甘红军在陕西安定一带召开联席会议。"},
    "steam_sg_19350501_dfa53298": {"datePrecision": "month", "displayDate": "1935年5月", "description": "1935年5月，陕甘边与陕北红军主力在陕西安定一带会师。"},
    "steam_sg_19350504_f02abc6a": {"description": "1935年5月4日，陕甘红军在陕西安定一带成立西北军委前敌总指挥部。"},
    # red_25th (4 clean clues)
    "steam_r25_19331016_9f961614": {},
    "steam_r25_19340301_990d0ad0": {"datePrecision": "month", "displayDate": "1934年3月中旬"},
    "steam_r25_19340416_76209add": {},
    "steam_r25_19350731_f058c9b5": {
        "title": "红二十五军占领川陕公路要地凤县双石铺",
        "description": "1935年7月31日，红二十五军西征北上途中占领陕西凤县双石铺（川陕边界公路要地）。",
        "notes": "【P2文本纠偏】修正原Steam标题缺右括号及正文误写“四川若尔盖草地”错误；仍保留待权威文献核实。",
    },
    # red_second (11 clean clues)
    "steam_r2_19340811_ce75b747": {},
    "steam_r2_19340917_4cab873f": {},
    "steam_r2_19341004_8265f303": {},
    "steam_r2_19341207_300041ab": {},
    "steam_r2_19341217_8b3ec24f": {},
    "steam_r2_19341226_a0af7683": {},
    "steam_r2_19350127_38a6ab31": {},
    "steam_r2_19350211_360892c2": {},
    "steam_r2_19350228_35e56b9a": {},
    "steam_r2_19350401_2a5f812d": {"datePrecision": "month", "displayDate": "1935年4月"},
    # red_fourth (11 clean clues)
    "steam_r4_19341101_9eb18f46": {"datePrecision": "month", "displayDate": "1934年11月"},
    "steam_r4_19350202_9eec714b": {},
    "steam_r4_19350605_ad22b854": {},
    "steam_r4_19350606_fee8f869": {},
    "steam_r4_19350624_b8804b0e": {},
    "steam_r4_19350913_74eef5fc": {
        "locationName": "四川阿坝",
        "lat": "32.9030", "lng": "101.7060",
        "description": "1935年9月13日，张国焘在四川阿坝召开川康省委及红军中党的活动分子会议（阿坝会议）。",
        "notes": "【P2地理纠偏】原Steam线索错标地点为甘肃迭部腊子口，已校订至四川阿坝；待补权威出处。",
    },
    "steam_r4_19350915_17f118d4": {},
    "steam_r4_19350917_11d161db": {"datePrecision": "range", "displayDate": "1935年9月17日至18日"},
    "steam_r4_19351019_d2540a62": {},
    "steam_r4_19351020_b30acd89": {},
    "steam_r4_19360810_bd8166e4": {},
    # red_first (2 clean clues)
    "steam_rf_19341005_63faf30f": {},
    "steam_rf_19350516_9df15d5c": {},
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="Write changes to data_edit/events.csv & person_events.csv")
    args = parser.parse_args()

    events_path = ROOT / "data_edit/events.csv"
    pe_path = ROOT / "data_edit/person_events.csv"

    with events_path.open("r", encoding="utf-8-sig", newline="") as f:
        ev_reader = csv.DictReader(f)
        ev_fields = list(ev_reader.fieldnames or [])
        events = list(ev_reader)

    with pe_path.open("r", encoding="utf-8-sig", newline="") as f:
        pe_reader = csv.DictReader(f)
        pe_fields = list(pe_reader.fieldnames or [])
        pes = list(pe_reader)

    active_low_ids = {
        e["id"] for e in events
        if str(e.get("enabled", "")).upper() == "TRUE" and e.get("certainty") == "low"
    }

    buckets = [
        ("UPGRADE_HIGH", set(UPGRADE_HIGH)),
        ("UPGRADE_MEDIUM", set(UPGRADE_MEDIUM)),
        ("DISABLE_DUP", set(DISABLE_DUP)),
        ("DISABLE_BROKEN", set(DISABLE_BROKEN)),
        ("KEEP_LOW", set(KEEP_LOW_CLEANUPS)),
    ]
    # Check disjointness and exact coverage
    seen: set[str] = set()
    for name, s in buckets:
        overlap = seen & s
        if overlap:
            raise RuntimeError(f"Bucket overlap in {name}: {overlap}")
        seen |= s

    missing = active_low_ids - seen
    extra = seen - active_low_ids
    if missing or extra:
        raise RuntimeError(f"Coverage mismatch! missing={sorted(missing)}, extra={sorted(extra)}")

    # Verify all remap targets exist & will remain enabled
    disabled_ids = set(DISABLE_DUP) | set(DISABLE_BROKEN)
    active_ids_after = {
        e["id"] for e in events
        if str(e.get("enabled", "")).upper() == "TRUE" and e["id"] not in disabled_ids
    }
    remap_map: dict[str, str | None] = {}
    for eid, (target, _reason) in DISABLE_DUP.items():
        if target not in active_ids_after:
            raise RuntimeError(f"DISABLE_DUP target not active after update: {eid} -> {target}")
        remap_map[eid] = target
    for eid, (target, _reason) in DISABLE_BROKEN.items():
        if target is not None and target not in active_ids_after:
            raise RuntimeError(f"DISABLE_BROKEN target not active after update: {eid} -> {target}")
        remap_map[eid] = target

    # Apply event edits in memory
    for e in events:
        eid = e["id"]
        if eid in UPGRADE_HIGH:
            e["certainty"] = "high"
            for k, v in UPGRADE_HIGH[eid].items():
                e[k] = v
        elif eid in UPGRADE_MEDIUM:
            e["certainty"] = "medium"
            for k, v in UPGRADE_MEDIUM[eid].items():
                e[k] = v
        elif eid in DISABLE_DUP:
            e["enabled"] = "FALSE"
            target, reason = DISABLE_DUP[eid]
            prev = e.get("notes", "").strip()
            e["notes"] = f"{prev} | 【P2去重禁用→{target}】{reason}".strip(" |")
        elif eid in DISABLE_BROKEN:
            e["enabled"] = "FALSE"
            target, reason = DISABLE_BROKEN[eid]
            prev = e.get("notes", "").strip()
            tag = f"→{target}" if target else ""
            e["notes"] = f"{prev} | 【P2纠错禁用{tag}】{reason}".strip(" |")
        elif eid in KEEP_LOW_CLEANUPS:
            for k, v in KEEP_LOW_CLEANUPS[eid].items():
                e[k] = v

    # Apply person_events remapping / disabling (deduplicating (personId, eventId))
    existing_active_pairs = {
        (r["personId"], r["eventId"])
        for r in pes
        if str(r.get("enabled", "")).upper() == "TRUE" and r["eventId"] not in disabled_ids
    }
    pe_remapped = 0
    pe_dedup_disabled = 0
    pe_broken_disabled = 0
    pe_source_upgraded = 0

    for r in pes:
        if str(r.get("enabled", "")).upper() != "TRUE":
            continue
        eid = r["eventId"]
        if eid in UPGRADE_HIGH:
            r["sourceIds"] = UPGRADE_HIGH[eid]["sourceIds"]
            pe_source_upgraded += 1
        elif eid in UPGRADE_MEDIUM:
            r["sourceIds"] = UPGRADE_MEDIUM[eid]["sourceIds"]
            pe_source_upgraded += 1
        elif eid in remap_map:
            target = remap_map[eid]
            if target is None:
                r["enabled"] = "FALSE"
                r["note"] = (r.get("note", "") + " | 【P2禁用】原事件为错乱/残缺Steam碎片").strip(" |")
                pe_broken_disabled += 1
            else:
                pair = (r["personId"], target)
                if pair in existing_active_pairs:
                    r["enabled"] = "FALSE"
                    r["note"] = (r.get("note", "") + f" | 【P2去重】已存在与{target}的关联").strip(" |")
                    pe_dedup_disabled += 1
                else:
                    r["eventId"] = target
                    r["note"] = (r.get("note", "") + f" | 【P2重映射】原自{eid}").strip(" |")
                    existing_active_pairs.add(pair)
                    pe_remapped += 1

    active_after = [e for e in events if str(e.get("enabled", "")).upper() == "TRUE"]
    certs = Counter(e["certainty"] for e in active_after)
    low_pct = certs["low"] / len(active_after) * 100

    print("=== P2-1 Adjudication Summary ===")
    for name, s in buckets:
        print(f"  {name:16s}: {len(s):3d}")
    print(f"  Total handled   : {len(seen):3d} (exact match with 210 active low)")
    print(f"\nActive events after: {len(active_after)}")
    print(f"  high  : {certs['high']:3d} ({certs['high']/len(active_after)*100:.1f}%)")
    print(f"  medium: {certs['medium']:3d} ({certs['medium']/len(active_after)*100:.1f}%)")
    print(f"  low   : {certs['low']:3d} ({low_pct:.1f}%)  <-- target <10%")
    print(f"\nperson_events updates:")
    print(f"  sourceIds upgraded : {pe_source_upgraded}")
    print(f"  remapped to canon  : {pe_remapped}")
    print(f"  dedup disabled     : {pe_dedup_disabled}")
    print(f"  broken disabled    : {pe_broken_disabled}")

    if args.apply:
        with events_path.open("w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=ev_fields)
            w.writeheader()
            w.writerows(events)
        with pe_path.open("w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=pe_fields)
            w.writeheader()
            w.writerows(pes)
        print("\n[APPLIED] Wrote updated data_edit/events.csv and data_edit/person_events.csv")
    else:
        print("\n[DRY RUN] Re-run with --apply to commit changes.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
