#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
补关键缺席人物：博古、李德、林彪、方志敏、程世才。
依据权威来源（中国共产党新闻网等），幂等。
- 博古/李德/林彪/程世才：补档案 + 关联到已有事件
- 方志敏：补档案 + 新增红十军团事件 + 关联
"""
import csv
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
EDIT = BASE / "data_edit"

SRC_BOGU = "src_cpc_century"
SRC_LIN = "src_lin_biao_cpc"
SRC_FANG = "src_fangzhimin_cpc"
SRC_LIXIANNIAN = "src_wxyj_dswxyjy"

NEW_SOURCES = [
    (SRC_LIN, "林彪（中国共产党新闻网）", "中国共产党新闻网",
     "https://cpc.people.com.cn/GB/64162/126778/126780/7490123.html", "林彪任红一军团军团长、长征指挥经历"),
    (SRC_FANG, "方志敏（中国共产党新闻网）", "中国共产党新闻网/人民日报",
     "https://cpc.people.com.cn/BIG5/n1/2021/0516/c64387-32104494.html", "方志敏红十军团、北上抗日先遣队、被俘与就义"),
]

# persons.csv 字段
P_HEADER = ["enabled","id","name","nameEn","personType","birthDate","deathDate","hometown","hometownEn","forceId","summary","summaryEn","portrait","themeTags","sourceIds","certainty","sort"]
NEW_PERSONS = [
    dict(id="bogu", name="博古", nameEn="Bo Gu", personType="人物", birthDate="1907", deathDate="1946", hometown="江苏无锡", hometownEn="Wuxi, Jiangsu", forceId="red_first",
         summary="秦邦宪，化名博古。中共中央主要负责人之一，长征初期推行错误军事路线；遵义会议后交出最高领导权，后任中央组织部部长等职，1946年因飞机失事遇难。",
         summaryEn="Bo Gu (Qin Bangxian), a principal CCP leader at the start of the Long March; after the Zunyi Meeting he stepped down from top military leadership.",
         portrait="", themeTags="中央领导;遵义会议", sourceIds=SRC_BOGU, certainty="high", sort="115"),
    dict(id="lide", name="李德", nameEn="Otto Braun", personType="人物", birthDate="1900", deathDate="1974", hometown="德国", hometownEn="Germany", forceId="red_first",
         summary="德国人，化名李德，共产国际派驻中国的军事顾问。长征初期参与军事指挥，其错误指挥导致湘江战役重大损失，遵义会议后不再拥有军事指挥权。",
         summaryEn="Otto Braun (Li De), a Comintern military adviser in China; his command contributed to heavy losses at the Xiang River; relieved after Zunyi.",
         portrait="", themeTags="军事顾问;遵义会议", sourceIds=SRC_BOGU, certainty="high", sort="116"),
    dict(id="linbiao", name="林彪", nameEn="Lin Biao", personType="人物", birthDate="1907", deathDate="1971", hometown="湖北黄冈", hometownEn="Huanggang, Hubei", forceId="red_first",
         summary="红一军团军团长。1934年10月率部参加长征，指挥突破国民党军四道封锁线、强渡乌江；遵义会议后指挥四渡赤水、强渡大渡河、夺占泸定桥等作战。",
         summaryEn="Commander of the First Red Army Corps; led the breakout through four blockade lines and major crossings during the Long March.",
         portrait="", themeTags="红一军团;指挥员", sourceIds=SRC_LIN, certainty="high", sort="117"),
    dict(id="fangzhimin", name="方志敏", nameEn="Fang Zhimin", personType="人物", birthDate="1899", deathDate="1935-08-06", hometown="江西弋阳", hometownEn="Yiyang, Jiangxi", forceId="red_7th_advance",
         summary="红十军团军政委员会主席，闽浙赣革命根据地创建人。1934年11月率北上抗日先遣队（红十军团）北上，1935年1月在怀玉山被俘，狱中写下《可爱的中国》，8月6日在南昌就义，时年36岁。",
         summaryEn="Chairman of the Red Tenth Army Corps; led the Northern Anti-Japanese Advance Force, captured in January 1935 and executed in Nanchang.",
         portrait="", themeTags="北上抗日先遣队;英烈", sourceIds=SRC_FANG, certainty="high", sort="118"),
    dict(id="chengshicai", name="程世才", nameEn="Cheng Shicai", personType="人物", birthDate="1912", deathDate="1990", hometown="湖北大悟", hometownEn="Dawu, Hubei", forceId="red_west_route",
         summary="红四方面军将领。西路军失败后，与李先念率红30军余部编成左支队，穿越祁连山到达星星峡进入新疆。",
         summaryEn="Red Fourth Front Army commander; co-led the left detachment across the Qilian Mountains to Xingxingxia in 1937.",
         portrait="", themeTags="西路军;左支队", sourceIds=SRC_LIXIANNIAN, certainty="high", sort="119"),
]

# 新事件：方志敏 红十军团（forceId=red_7th_advance，与先遣队同线）
NEW_EVENTS = [
    dict(enabled="TRUE", id="ev_fang_193411", date="19341101", displayDate="19341101", sequence="1",
         forceId="red_7th_advance", type="整编", title="红十军团组成继续北上",
         description="1934年11月，以红七军团组成的北上抗日先遣队到达闽浙皖赣边区，与红十军会合组成红十军团，方志敏任军政委员会主席，刘畴西任军团长，继续挥师北上抗日。",
         locationName="江西赣东北", locationNameEn="Northeastern Jiangxi", lat="28.9", lng="117.6",
         participants="方志敏; 刘畴西", importance="4", sourceIds=SRC_FANG, certainty="high",
         notes="延伸叙事：北上抗日先遣队后续"),
    dict(enabled="TRUE", id="ev_fang_19350129", date="19350129", displayDate="19350129", sequence="1",
         forceId="red_7th_advance", type="牺牲", title="方志敏怀玉山被俘",
         description="1935年1月，方志敏、刘畴西率红十军团在怀玉山区与敌英勇搏斗，终因寡不敌众、弹尽援绝，大部壮烈牺牲，方志敏于1月29日在江西玉山被俘。在狱中写下《可爱的中国》《清贫》等，8月6日在南昌就义，时年36岁。",
         locationName="江西玉山怀玉山", locationNameEn="Huaiyu Mountain, Yushan, Jiangxi", lat="28.7", lng="118.2",
         participants="方志敏; 刘畴西", importance="5", sourceIds=SRC_FANG, certainty="high",
         notes="延伸叙事：北上抗日先遣队结局"),
]

# 新增关联：personId -> [(eventId, role, note, srcs)]
NEW_LINKS = {
    "bogu": [
        ("rf_19341010_ruijin", "中央领导", "长征初期主要负责人", SRC_BOGU),
        ("rf_19350115_zunyi_meeting", "被批评方", "遵义会议批评其军事路线，会后交出领导权", SRC_BOGU),
        ("rf_19350820_maoergai", "参与者", "毛儿盖会议前后参与中央决策", SRC_BOGU),
    ],
    "lide": [
        ("rf_19341010_ruijin", "军事顾问", "参与长征初期军事指挥", SRC_BOGU),
        ("rf_19350115_zunyi_meeting", "被批评方", "遵义会议批评其错误军事指挥", SRC_BOGU),
    ],
    "linbiao": [
        ("rf_19341010_ruijin", "军团长", "率红一军团开始长征", SRC_LIN),
        ("rf_19350115_zunyi_meeting", "参与者", "参加遵义会议", SRC_LIN),
    ],
    "fangzhimin": [
        ("ev_fang_193411", "军政委员会主席", "组成红十军团继续北上", SRC_FANG),
        ("ev_fang_19350129", "被俘/就义", "怀玉山被俘，南昌就义", SRC_FANG),
    ],
    "chengshicai": [
        ("ev_wxyj_19370430", "指挥员", "与李先念率左支队到达星星峡", SRC_LIXIANNIAN),
    ],
}


def read(name):
    with open(EDIT / name, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

def write(name, header, rows):
    with open(EDIT / name, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=header); w.writeheader(); w.writerows(rows)

def add_sources():
    rows = read("sources.csv"); exist = {r["id"] for r in rows}
    n = 0
    for s in NEW_SOURCES:
        if s[0] not in exist:
            rows.append(dict(zip(rows[0].keys(), s))); n += 1
    write("sources.csv", list(rows[0].keys()), rows)
    return n

def add_persons():
    rows = read("persons.csv"); exist = {r["id"] for r in rows}
    n = 0
    for p in NEW_PERSONS:
        if p["id"] in exist:
            continue
        row = {k: "" for k in rows[0].keys()}
        row.update(p)
        rows.append(row); n += 1
    write("persons.csv", list(rows[0].keys()), rows)
    return n

def add_events():
    rows = read("events.csv"); exist = {r["id"] for r in rows}
    n = 0
    for e in NEW_EVENTS:
        if e["id"] in exist:
            continue
        row = {k: "" for k in rows[0].keys()}
        row.update(e)
        rows.append(row); n += 1
    write("events.csv", list(rows[0].keys()), rows)
    return n

def add_links():
    rows = read("person_events.csv")
    exist = {(r["personId"], r["eventId"]) for r in rows}
    maxsort = {}
    for r in rows:
        try: maxsort[r["personId"]] = max(maxsort.get(r["personId"], 0), int(r.get("sort") or 0))
        except ValueError: pass
    n = 0
    for pid, links in NEW_LINKS.items():
        for eid, role, note, srcs in links:
            if (pid, eid) in exist:
                continue
            s = maxsort.get(pid, 0) + 10; maxsort[pid] = s
            row = {k: "" for k in rows[0].keys()}
            row.update(enabled="TRUE", personId=pid, eventId=eid, role=role, note=note, sourceIds=srcs, sort=str(s))
            rows.append(row); exist.add((pid, eid)); n += 1
    write("person_events.csv", list(rows[0].keys()), rows)
    return n

if __name__ == "__main__":
    print("新增来源", add_sources())
    print("新增人物", add_persons())
    print("新增事件", add_events())
    print("新增关联", add_links())
