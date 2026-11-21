#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
织密人物-事件关联：给零关联人物补上确有史料依据的关联。

依据：research_private/sourced_research/*.md 中已存盘的权威史料
（每条关联的 note 写明依据；sourceIds 指向该来源）。
原则：只连有明确记载的事件，不为了"有关联"而臆造。
幂等：以 (personId,eventId) 去重。
"""
import csv
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
P = BASE / "data_edit" / "person_events.csv"

# personId -> [(eventId, role, note, sourceIds)]
LINKS = {
    # 西路军（依据 01_西路军与英烈.md）
    "dongzhengtang": [
        ("ev_wxyj_19361024", "参与者", "率红五军西渡黄河", "src_wxyj_dswxyjy"),
        ("ev_wxyj_19361111", "参与者", "西路军组建，任红五军军长", "src_wxyj_dswxyjy"),
        ("ev_wxyj_193612", "指挥员", "永昌山丹一带作战", "src_wxyj_people_dangshi"),
        ("ev_wxyj_19370120", "主祭/牺牲", "高台血战，城破后壮烈牺牲", "src_dongzhengtang_cpc;src_wxyj_81"),
    ],
    "yangkeming": [
        ("ev_wxyj_19370120", "牺牲", "红五军政治部主任，高台掩护中弹牺牲", "src_yangkeming_dangshi"),
    ],
    "zhangqiqiu": [
        ("ev_wxyj_19361111", "参与者", "西路军政治部组织部长，妇女团随军西渡", "src_women_div_81"),
        ("ev_wxyj_19370314", "被俘", "梨园口战斗后被俘，后经交涉获释回延安", "src_women_div_81"),
    ],
    "li_xiannian": [
        ("ev_wxyj_19370314", "决策者", "石窝会议后率左支队", "src_wxyj_dswxyjy"),
        ("ev_wxyj_19370430", "指挥员", "率左支队抵达星星峡进疆", "src_wxyj_dswxyjy"),
    ],
    # 琼崖（依据 03_琼崖与东江.md）
    "fengbaiju": [
        ("ev_qy_193304", "领导者", "率25人母瑞山突围", "src_qiongya_cpc"),
        ("ev_qy_193605", "领导者", "组建琼崖红军游击队司令部", "src_qiongya_cpc"),
        ("ev_qy_19381205", "队长", "云龙改编任琼崖抗日独立队队长", "src_qiongya_yunlong"),
        ("ev_qy_19390210", "指挥员", "潭口阻击打响海南抗战第一枪", "src_qiongya_yunlong"),
    ],
    "wangwenming": [
        ("ev_qy_19270923", "参与者", "琼崖特委领导，椰子寨暴动", "src_qiongya_hainan"),
        ("ev_qy_192803", "决策者", "率机关和红军转移母瑞山", "src_qiongya_wangwenming"),
    ],
    "yangshanji": [
        ("ev_qy_19270923", "领导者/牺牲", "琼崖特委书记，领导椰子寨战斗并牺牲", "src_qiongya_hainan"),
    ],
    # 东江（依据 03_琼崖与东江.md）
    "zengsheng": [
        ("ev_dj_19431202", "司令员", "东江纵队成立任司令员", "src_dongjiang_cpc"),
        ("ev_dj_194508", "指挥员", "抗战胜利时纵队规模过万", "src_dongjiang_cpc"),
        ("ev_dj_19460630", "率领者", "率2583人北撤烟台", "src_dongjiang_beiche"),
    ],
    "wangzuoyao": [
        ("ev_dj_19431202", "副司令员", "任副司令员兼参谋长", "src_dongjiang_cpc"),
        ("ev_dj_19460630", "率领者", "参与率领北撤", "src_dongjiang_beiche"),
    ],
    "yinlinping": [
        ("ev_dj_19431202", "政治委员", "东江纵队成立兼任政委", "src_dongjiang_cpc"),
    ],
    # 东北抗联（依据 02_东北抗联_新长征_烈士陵园.md）
    "yangjingyu": [
        ("ev_dkb_193609", "总司令", "抗联第一路军总司令兼政委", "src_dongbeikanglian_people"),
        ("ev_dkb_19400223", "牺牲", "三道崴子壮烈殉国", "src_yangjingyu_cpc"),
    ],
    "zhaoyiman": [
        ("ev_dkb_19360802", "牺牲", "第3军第2团政委，哈尔滨就义", "src_zhaoyiman_people"),
    ],
    "zhoubaozhong": [
        ("ev_dkb_193609", "领导人", "抗联第二路军总指挥", "src_dongbeikanglian_xinhua"),
        ("ev_dkb_194208", "旅长", "抗联教导旅旅长", "src_dongbeikanglian_xinhua"),
    ],
    # 北上抗日先遣队（依据既有史料：寻淮洲/粟裕等为先遣队核心）
    "xun_huaizhou": [
        ("steam_r7_19340706_bc42d0bf", "军团长", "红七军团团长，率先遣队出发", "src_cpc_century"),
    ],
    "le_shaohua": [
        ("steam_r7_19340706_bc42d0bf", "政委", "北上抗日先遣队政委", "src_cpc_century"),
    ],
    "su_yu": [
        ("steam_r7_19340706_bc42d0bf", "参与者", "先遣队参谋长，后率部坚持", "src_cpc_century"),
    ],
    # 敌军（依据：国民党军围堵层为概括性叙事，不强行把具体人物塞进每条）
    "bai_chongxi": [
        ("en_19341127_xiangjiang_block", "敌军将领", "湘江封锁线国民党军指挥体系（概括叙事层）", "src_cpc_century"),
    ],
    "zhang_xueliang": [
        ("en_19350110_zunyi_pressure", "敌军将领", "西北军体系参与围堵（概括叙事层）", "src_cpc_century"),
    ],
    "zhang_ziyi": [
        ("r2_19351119_sangzhi_start", "政治部主任", "红二方面军政治部主任，随军长征", "src_red2_start_12371"),
    ],
}


def main():
    with open(P, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    header = list(rows[0].keys()) if rows else []
    exist = {(r.get("personId"), r.get("eventId")) for r in rows}
    max_sort = {}
    for r in rows:
        pid = r.get("personId")
        try:
            max_sort[pid] = max(max_sort.get(pid, 0), int(r.get("sort") or 0))
        except ValueError:
            pass
    added = 0
    for pid, links in LINKS.items():
        for eid, role, note, srcs in links:
            if (pid, eid) in exist:
                continue
            s = max_sort.get(pid, 0) + 10
            max_sort[pid] = s
            row = {k: "" for k in header}
            row.update({
                "enabled": "TRUE", "personId": pid, "eventId": eid,
                "role": role, "note": note, "sourceIds": srcs, "sort": str(s),
            })
            rows.append(row)
            exist.add((pid, eid))
            added += 1
    with open(P, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=header)
        w.writeheader(); w.writerows(rows)
    print(f"新增关联 {added} 条，person_events 现 {len(rows)} 行")


if __name__ == "__main__":
    main()
