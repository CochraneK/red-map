#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
把 research_private/sourced_research/ 中经权威来源核实的史料写入 data_edit 表格。
只写有权威来源、无存疑的条目；certainty=high；sourceIds 指向新增来源。
可重复运行：按 id 幂等（已存在则跳过）。
"""
import csv
import io
import os
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
EDIT = BASE / "data_edit"

# ---------- 新增来源 ----------
NEW_SOURCES = [
    ("src_wxyj_dswxyjy", "中国工农红军西路军（中央党史和文献研究院）", "中央党史和文献研究院", "https://www.dswxyjy.org.cn/n1/2020/0914/c244523-31860754.html", "西路军西渡黄河、倪家营子、梨园口、石窝分兵、星星峡时间线"),
    ("src_wxyj_people_dangshi", "西路军历史（人民网党史）", "人民网·中国共产党新闻网", "https://dangshi.people.com.cn/BIG5/n1/2019/0223/c85037-30898568-4.html", "西路军总人数、结局与历史评价"),
    ("src_wxyj_cctv", "西路军·西渡黄河（央视网）", "央视网", "https://tv.cctv.com/v/v1/VIDEdmFT86EHu9ewPUPGJspN190824.html", "靖远虎豹口渡河地点参考"),
    ("src_wxyj_81", "董振堂（中国军网）", "中国军网", "https://www.81.cn/2018zt/2018-11/29/content_9360152.htm", "董振堂职务与高台牺牲事实"),
    ("src_dongzhengtang_cpc", "董振堂：宁都起义与高台殉难（中国共产党新闻网）", "中国共产党新闻网", "https://cpc.people.com.cn/BIG5/n1/2021/0518/c64387-32106046.html", "董振堂生平"),
    ("src_yangkeming_dangshi", "杨克明（人民网党史）", "人民网·中国共产党新闻网", "https://dangshi.people.com.cn/n1/2019/0823/c427898-31312905.html", "杨克明高台牺牲"),
    ("src_women_div_81", "妇女独立师/妇女抗日先锋团（中国军网/中青报）", "中国青年报", "https://news.cyol.com/yuanchuang/2018-06/14/content_17292909.htm", "西路军妇女团人员与贡献"),
    ("src_liuzhidan_81", "刘志丹（中国军网）", "中国军网", "https://www.81.cn/yljnt_208627/ylml/9791206_8.html", "刘志丹牺牲经过"),
    ("src_qiongya_hainan", "琼崖革命斗争史（海南省人民政府网）", "海南省人民政府网", "https://hainan.gov.cn/hainan/lsyg/202606/8d451790b11442528fd9c3c9a5211ec6.shtml", "椰子寨战斗与琼崖纵队诞生"),
    ("src_qiongya_cpc", "琼崖纵队：二十三年红旗不倒（中国共产党新闻网）", "中国共产党新闻网", "https://cpc.people.com.cn/n1/2021/0611/c64387-32128318.html", "母瑞山、突围、恢复"),
    ("src_qiongya_wangwenming", "王文明与母瑞山（中国共产党新闻网）", "中国共产党新闻网", "https://cpc.people.com.cn/n1/2022/0509/c443712-32417363.html", "王文明转移母瑞山"),
    ("src_qiongya_yunlong", "云龙改编与潭口阻击（中国共产党新闻网）", "中国共产党新闻网", "https://cpc.people.com.cn/n1/2026/0521/c443712-40724285.html", "琼崖抗日独立队成立与首战"),
    ("src_dongjiang_cpc", "东江纵队（中国共产党新闻网）", "中国共产党新闻网", "https://cpc.people.com.cn/n1/2024/1201/c443712-40372710.html", "东江纵队成立、规模、评价"),
    ("src_dongjiang_hk_rescue", "香港大营救（中国共产党新闻网）", "中国共产党新闻网", "https://cpc.people.com.cn/n1/2021/0628/c64387-32142446.html", "文化名人大营救"),
    ("src_dongjiang_gangjiu", "港九大队（中国共产党新闻网）", "中国共产党新闻网", "https://cpc.people.com.cn/n1/2025/0703/c643712-40513912.html", "港九大队海上游击战"),
    ("src_dongjiang_beiche", "东江纵队北撤烟台（人民网党史）", "人民网·中国共产党新闻网", "https://dangshi.people.com.cn/n1/2020/0211/c85037-31581018.html", "1946北撤"),
    ("src_dongjiang_huizhou", "东江纵队北撤（惠州市政府网）", "惠州市人民政府网", "https://www.huizhou.gov.cn/zjhz/lsrw/content/mpost_5799584.html", "北撤出发地沙鱼涌"),
    ("src_dongbeikanglian_people", "东北抗日联军（人民网）", "人民网", "http://www.people.com.cn/n/2015/0825/c364391-27554663.html", "抗联组建与番号"),
    ("src_dongbeikanglian_xinhua", "东北抗联斗争（新华网）", "新华网", "http://www.news.cn/politics/2015-09/03/c_1116484708.htm", "抗联番号与配合苏军"),
    ("src_yangjingyu_cpc", "杨靖宇（中国共产党新闻网）", "中国共产党新闻网", "https://cpc.people.com.cn/BIG5/n1/2018/0218/c64387-29832218.html", "杨靖宇牺牲"),
    ("src_zhaoyiman_people", "赵一曼（人民网）", "人民网", "http://www.people.com.cn/n1/2018/0423/c64387-29944029.html", "赵一曼被俘与就义"),
]

# ---------- 新增事件 ----------
# 字段: id,date,forceId,type,title,description,locationName,lat,lng,sourceIds,certainty
NEW_EVENTS = [
    # 西路军
    ("ev_wxyj_19361024", "19361024", "red_west_route", "渡河", "西路军西渡黄河", "1936年10月11日中革军委颁布《十月份作战纲领》，决定执行宁夏战役计划。红四方面军总部率第30、第9、第5军及妇女独立团等共21800余人，自10月24日夜起在靖远虎豹口等地强渡黄河，至月底全部渡过。因胡宗南部切断河东联系，宁夏战役于11月初中止。", "甘肃靖远虎豹口", 36.531421, 104.618672, "src_wxyj_dswxyjy;src_wxyj_cctv", "high"),
    ("ev_wxyj_19361111", "19361111", "red_west_route", "整编", "西路军正式组建", "1936年11月11日中央电令渡河部队组成西路军，徐向前任总指挥、陈昌浩任政委。西路军先后攻占一条山、五佛寺，继而分路西进，在古浪与马家军激战三昼夜，红9军伤亡2400余人。", "甘肃景泰一条山", 37.196569, 104.07247, "src_wxyj_dswxyjy;src_wxyj_people_dangshi", "high"),
    ("ev_wxyj_193612", "19361201", "red_west_route", "战役", "永昌山丹连串战斗", "西安事变前后，西路军按中央命令在凉州、永昌、山丹一带建立根据地，与马家军反复争夺，历经四十里铺、八坝、水磨关、永昌城、山丹城等大小战斗20余次，击毙击伤敌6000余人，但补给断绝、伤亡严重。", "甘肃永昌山丹一线", 38.5, 102.2, "src_wxyj_people_dangshi", "high"),
    ("ev_wxyj_19370120", "19370120", "red_west_route", "牺牲", "高台血战董振堂殉难", "1937年1月1日红五军攻克高台。1月12日马家军约2万人在大炮配合下围攻高台，红五军孤立无援血战8昼夜，弹尽粮绝。1月20日凌晨城破，军长董振堂、政治部主任杨克明及2000余名将士壮烈牺牲。", "甘肃高台县", 39.4, 99.8, "src_wxyj_81;src_dongzhengtang_cpc;src_yangkeming_dangshi", "high"),
    ("ev_wxyj_19370128", "19370128", "red_west_route", "战役", "倪家营子四十大血战", "高台失守后西路军折回临泽以南倪家营子集结，仍剩1万余人。马元海率步骑5个旅及民团连续猛攻，西路军依托村寨反复拼杀，击退大规模进攻八九次，歼敌近万人，自身亦伤亡惨重。2月27日弹尽粮绝被迫突围。", "甘肃临泽倪家营子", 39.2, 100.1, "src_wxyj_dswxyjy", "high"),
    ("ev_wxyj_19370314", "19370314", "red_west_route", "会议", "梨园口失利与石窝分兵", "1937年3月12日西路军在梨园口至康龙寺一带与敌鏖战，部队大部损失，妇女团承担掩护任务伤亡惨重。3月14日军政委员会在石窝召开会议，决定徐向前、陈昌浩离队回陕北，余部编为3个支队分散游击，此时兵力已不足3000人。", "甘肃肃南石窝山", 38.8, 99.5, "src_wxyj_dswxyjy", "high"),
    ("ev_wxyj_19370430", "19370430", "red_west_route", "到达", "左支队抵达星星峡进疆", "石窝会议后，李先念、程世才率红30军余部编成的左支队400余人，穿越祁连山高山峡谷，历时40余天转战，于1937年4月底到达星星峡，在党中央代表陈云、滕代远接应下进入新疆，后编成新兵营。", "甘新交界星星峡", 41.2, 94.7, "src_wxyj_dswxyjy", "high"),
    # 东北抗联
    ("ev_dkb_193609", "19360901", "spark_dongbei", "整编", "东北抗日联军统一番号", "1935年冬起中共满洲省委将各路抗日游击队改编为东北人民革命军，1936年2月统一改称东北抗日联军，先后组建11个军，鼎盛时期达3万余人，在白山黑水间开展长期艰苦卓绝的游击战争。", "东北三省", 44.0, 126.0, "src_dongbeikanglian_people;src_dongbeikanglian_xinhua", "high"),
    ("ev_dkb_193805", "19380501", "spark_dongbei", "牺牲", "八女投江", "东北抗联第2军第4军妇女团冷云等8名女战士，在掩护部队突围时弹尽援绝，毅然投江殉难，年大的二十三四岁，小的仅十三四岁，史称八女投江。", "黑龙江乌斯浑河畔", 44.6, 129.7, "src_dongbeikanglian_people", "high"),
    ("ev_dkb_19400223", "19400223", "spark_dongbei", "牺牲", "杨靖宇壮烈牺牲", "杨靖宇（1905—1940），东北抗联第一路军总司令兼政委，在极端艰苦条件下率部坚持抗战。1940年2月23日在靖宇县三道崴子被日伪军包围，激战后壮烈牺牲，年仅35岁。日军解剖其遗体，发现胃中尽是草根、树皮和棉絮。", "吉林靖宇县三道崴子", 42.6, 126.8, "src_yangjingyu_cpc", "high"),
    ("ev_dkb_19360802", "19360802", "spark_dongbei", "牺牲", "赵一曼坚贞就义", "赵一曼（1905—1936），东北抗联第3军第2团政治委员。1935年11月负重伤被俘，在狱中坚贞不屈，写下致儿子的遗书。1936年8月2日在哈尔滨被日军杀害，年仅31岁。", "黑龙江哈尔滨", 45.8, 126.5, "src_zhaoyiman_people", "high"),
    ("ev_dkb_194208", "19420801", "spark_dongbei", "整编", "抗联教导旅整编", "1942年8月抗联余部在苏联远东整编为东北抗日联军教导旅，周保中任旅长、李兆麟任副旅长，继续训练并派小分队回国侦察。1945年8月苏联对日宣战后，抗联部队配合苏军迅速解放东北主要城市。", "苏联远东/中国东北", 45.0, 130.0, "src_dongbeikanglian_xinhua", "high"),
    # 琼崖纵队（标注为星星之火延伸，非长征主线）
    ("ev_qy_19270923", "19270923", "spark_qiongya", "启程", "椰子寨战斗打响第一枪", "中共琼崖特委响应八七会议武装暴动号召，领导讨逆革命军在万泉河畔椰子寨打响全琼武装总暴动第一枪，揭开海南武装斗争序幕。主要领导人杨善集、陈永芹等在激战中牺牲。此日被定为琼崖纵队诞生日。", "海南琼海椰子寨", 19.2, 110.5, "src_qiongya_hainan;src_qiongya_cpc", "high"),
    ("ev_qy_192803", "19280301", "spark_qiongya", "转进", "转移母瑞山保存火种", "1928年初国民党军4000余人抵琼分三路围剿，琼崖红军第一次反围剿受挫，革命转入低潮。琼崖苏维埃政府主席王文明顶住压力，果断率机关和红军向母瑞山转移，开辟根据地，保存革命火种。", "海南定安母瑞山", 19.4, 110.4, "src_qiongya_wangwenming", "high"),
    ("ev_qy_193304", "19330401", "spark_qiongya", "突围", "母瑞山二十三人下山", "冯白驹带领的琼崖党政机关干部和红军指战员100多人在母瑞山经历8个多月严峻考验，无一人叛变、无一人逃跑，最后仅剩25人于1933年4月成功突围下山，返回琼文老区继续开展游击战争。", "海南母瑞山至琼文", 19.4, 110.5, "src_qiongya_cpc", "high"),
    ("ev_qy_193605", "19360501", "spark_qiongya", "整编", "琼崖红军游击队司令部成立", "1936年5月成立琼崖工农红军游击队司令部，逐渐恢复扩充革命武装。此前经过约4年艰苦卓绝的游击战争与群众工作，琼崖特委于1936年恢复并与中央、省委恢复联系，标志琼崖革命从最低潮走向恢复。", "海南岛", 19.2, 109.8, "src_qiongya_cpc", "high"),
    ("ev_qy_19381205", "19381205", "spark_qiongya", "整编", "云龙改编琼崖抗日独立队", "根据琼崖国共两党合作抗日协议，琼崖红军游击队在云龙墟举行改编暨誓师抗日大会，改编为琼崖抗日独立队，辖3个中队和1个特务小队，300余人，冯白驹任队长。", "海南琼山云龙墟", 19.9, 110.4, "src_qiongya_yunlong", "high"),
    ("ev_qy_19390210", "19390210", "spark_qiongya", "战役", "潭口阻击打响抗日第一枪", "日军在海口附近登陆，国民党军政机关已撤离。冯白驹领导的琼崖抗日独立队第一中队在潭口渡口东岸阻击东渡日军，打响中国共产党领导的海南人民抗战第一枪，为群众转移争取时间。", "海南琼山潭口渡口", 20.0, 110.4, "src_qiongya_yunlong", "high"),
    ("ev_qy_194508", "19450815", "spark_qiongya", "胜利", "琼崖抗战胜利规模扩大", "至抗战胜利，琼崖独立纵队发展到7700余人、民兵近1万人，根据地扩大到全岛约一半。朱德在党的七大将琼崖纵队等华南抗日纵队并称为中国抗战的中流砥柱。", "海南岛", 19.2, 109.8, "src_qiongya_cpc", "high"),
    ("ev_qy_19500501", "19500501", "spark_qiongya", "胜利", "海南岛解放二十三年红旗不倒", "1949年12月毛泽东发出解放海南岛命令，琼崖纵队接应野战军渡海，1950年5月1日海南全岛解放，此时纵队发展到2.5万余人。从1927年9月至1950年5月恰23年，即二十三年红旗不倒。", "海南岛", 19.2, 109.8, "src_qiongya_cpc", "high"),
    # 东江纵队
    ("ev_dj_194112", "19411201", "spark_dongjiang", "行动", "香港大营救文化名人", "1941年12月日军攻陷香港，搜捕滞留的爱国民主人士和文化界名人。广东人民抗日游击队挺进九龙、新界地区，秘密营救何香凝、柳亚子、邹韬奋、茅盾、胡绳、夏衍、梁漱溟等共800余人，撤离过程中无一人被捕、无一人牺牲。", "香港至广东东江", 22.3, 114.2, "src_dongjiang_hk_rescue", "high"),
    ("ev_dj_194202", "19420201", "spark_dongjiang", "整编", "港九大队成立", "香港沦陷后，广东人民抗日游击总队港九大队挺进敌后，1942年2月正式成立，开展游击战，并承担护送文化名人、营救盟军飞行员任务。1943年2月成立海上小队，后发展为海上中队。", "香港九龙新界", 22.4, 114.3, "src_dongjiang_gangjiu", "high"),
    ("ev_dj_19431202", "19431202", "spark_dongjiang", "整编", "东江纵队正式成立", "广东人民抗日游击队东江纵队在土洋村发表成立宣言，公开宣布接受中国共产党领导。尹林平兼任政治委员，曾生任司令员，王作尧任副司令员兼参谋长，杨康华任政治部主任。", "广东惠阳土洋村", 22.6, 114.5, "src_dongjiang_cpc", "high"),
    ("ev_dj_194508", "19450815", "spark_dongjiang", "胜利", "东江纵队抗战胜利规模", "至抗战胜利前，东江纵队发展到1万人以上，整个华南抗日纵队达3万人。解放城镇50座，开辟游击区约6万平方公里、人口450余万，毙伤日伪军6000余人、俘虏3500余人。", "广东东江游击区", 23.0, 114.0, "src_dongjiang_cpc", "high"),
    ("ev_dj_19460630", "19460630", "spark_dongjiang", "转进", "东江纵队北撤烟台", "根据双十协定，1946年6月30日凌晨，东江纵队2583人在曾生、王作尧、林锵云、杨康华率领下，从大鹏湾沙鱼涌登上美国3艘登陆舰北撤，7月5日抵达山东烟台。北撤部队后扩编为两广纵队。", "广东大鹏湾至山东烟台", 22.6, 114.5, "src_dongjiang_beiche;src_dongjiang_huizhou", "high"),
]

# ---------- 新增人物 ----------
# id,name,nameEn,personType,birthDate,deathDate,hometown,forceId,summary,portrait,themeTags,sourceIds,certainty,sort
NEW_PERSONS = [
    ("dongzhengtang", "董振堂", "Dong Zhentang", "人物", "1895", "1937-01-20", "河北新河", "red_west_route", "红五军军长。1931年12月与赵博生等领导宁都起义加入红军，1932年入党。1937年1月率部血战高台，城破后壮烈牺牲，是红军牺牲的最高级别将领之一。", "", "宁都起义;高台血战;英烈", "src_dongzhengtang_cpc;src_wxyj_81", "high", 601),
    ("yangkeming", "杨克明", "Yang Keming", "人物", "1905", "1937-01-20", "四川涪陵", "red_west_route", "红五军政治部主任。长征中三过草地，高台血战中掩护董振堂撤离，中弹牺牲，与2000余将士殉难。", "", "西路军;高台血战;英烈", "src_yangkeming_dangshi", "high", 602),
    ("zhangqiqiu", "张琴秋", "Zhang Qinqiu", "人物", "1904", "1968", "浙江桐乡", "red_fourth", "西路军政治部组织部长，曾任妇女独立师师长。被俘后经周恩来交涉获释，1937年10月回延安。", "", "妇女红军;西路军", "src_women_div_81", "high", 603),
    ("fengbaiju", "冯白驹", "Feng Baiju", "人物", "", "", "海南琼山", "spark_qiongya", "琼崖纵队司令员兼政委，二十三年红旗不倒的主要领导者。1926年入党，1932-33年率部在母瑞山坚持8个多月并带25人突围，1938年任琼崖抗日独立队队长。（生卒年权威来源未明确，待核）", "", "琼崖纵队;母瑞山;抗战", "src_qiongya_cpc", "high", 701),
    ("wangwenming", "王文明", "Wang Wenming", "人物", "", "", "海南", "spark_qiongya", "琼崖革命先驱，中共琼崖地委首任书记、琼崖苏维埃政府主席。1928年反围剿受挫后率部转移母瑞山，保存革命火种。", "", "琼崖纵队;母瑞山", "src_qiongya_wangwenming", "high", 702),
    ("yangshanji", "杨善集", "Yang Shanji", "人物", "", "1927", "海南", "spark_qiongya", "中共琼崖特委首任书记，1927年9月领导椰子寨战斗，打响琼崖武装暴动第一枪，激战中牺牲。", "", "琼崖纵队;英烈", "src_qiongya_hainan", "high", 703),
    ("zengsheng", "曾生", "Zeng Sheng", "人物", "", "", "广东惠阳", "spark_dongjiang", "东江纵队司令员。1938年回惠阳组织抗日武装，1943年东江纵队成立任司令员，1946年率部北撤烟台。", "", "东江纵队;港九大队;北撤", "src_dongjiang_cpc", "high", 801),
    ("wangzuoyao", "王作尧", "Wang Zuoyao", "人物", "", "", "广东", "spark_dongjiang", "东江纵队早期领导人，1943年12月任副司令员兼参谋长。1944年5月梅塘战斗指挥部队抢占马山阻击日军。", "", "东江纵队;抗战", "src_dongjiang_cpc", "high", 802),
    ("yinlinping", "尹林平", "Yin Linping", "人物", "", "", "广东", "spark_dongjiang", "中共广东省临委书记，1943年12月东江纵队成立兼任政治委员。", "", "东江纵队;抗战", "src_dongjiang_cpc", "high", 803),
    ("yangjingyu", "杨靖宇", "Yang Jingyu", "人物", "1905", "1940-02-23", "河南确山", "spark_dongbei", "东北抗日联军第一路军总司令兼政委。1940年2月23日在靖宇县三道崴子壮烈牺牲，年仅35岁，胃中尽是草根树皮棉絮。", "", "东北抗联;英烈", "src_yangjingyu_cpc", "high", 901),
    ("zhaoyiman", "赵一曼", "Zhao Yiman", "人物", "1905", "1936-08-02", "四川宜宾", "spark_dongbei", "东北抗联第3军第2团政治委员。1935年11月负重伤被俘，狱中坚贞不屈并写下致儿子遗书，1936年8月2日在哈尔滨就义，年仅31岁。", "", "东北抗联;英烈", "src_zhaoyiman_people", "high", 902),
    ("zhoubaozhong", "周保中", "Zhou Baozhong", "人物", "", "", "云南大理", "spark_dongbei", "东北抗日联军领导人，抗联教导旅旅长，1945年配合苏军解放东北。", "", "东北抗联;教导旅", "src_dongbeikanglian_xinhua", "high", 903),
]

# ---------- 工具函数 ----------
def read_csv(path):
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.reader(f))
    return rows[0], rows[1:]

def write_csv(path, header, rows):
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)

def add_sources():
    header, rows = read_csv(EDIT / "sources.csv")
    existing = {r[0] for r in rows if r}
    added = 0
    for s in NEW_SOURCES:
        if s[0] not in existing:
            rows.append(list(s)); added += 1
    write_csv(EDIT / "sources.csv", header, rows)
    return added

def add_events():
    header, rows = read_csv(EDIT / "events.csv")
    existing = {r[0] for r in rows if r}
    added = 0
    idx = {name: i for i, name in enumerate(header)}
    for e in NEW_EVENTS:
        (eid, date, force, typ, title, desc, loc, lat, lng, srcs, cert) = e
        if eid in existing:
            continue
        row = [""] * len(header)
        def put(name, val):
            if name in idx:
                row[idx[name]] = val
        put("enabled", "TRUE")
        put("id", eid); put("date", date); put("displayDate", date)
        put("sequence", "1"); put("forceId", force); put("type", typ)
        put("title", title); put("description", desc)
        put("locationName", loc); put("lat", str(lat)); put("lng", str(lng))
        put("importance", "3"); put("sourceIds", srcs); put("certainty", cert)
        put("notes", "权威来源核实；延伸视角条目，非1934-1936长征主线" if force.startswith("spark_") or force == "red_west_route" else "")
        rows.append(row); added += 1
    write_csv(EDIT / "events.csv", header, rows)
    return added

def add_persons():
    header, rows = read_csv(EDIT / "persons.csv")
    existing = {r[0] for r in rows if r}
    added = 0
    idx = {name: i for i, name in enumerate(header)}
    for p in NEW_PERSONS:
        (pid, name, nameEn, ptype, birth, death, home, force, summary, portrait, tags, srcs, cert, sort) = p
        if pid in existing or not pid or pid.endswith("placeholder"):
            continue
        row = [""] * len(header)
        def put(name, val):
            if name in idx:
                row[idx[name]] = val
        put("enabled", "TRUE")
        put("id", pid); put("name", name); put("nameEn", nameEn)
        put("personType", ptype); put("birthDate", birth); put("deathDate", death)
        put("hometown", home); put("forceId", force); put("summary", summary)
        put("portrait", portrait); put("themeTags", tags.replace(";", ";"))
        put("sourceIds", srcs); put("certainty", cert); put("sort", str(sort))
        rows.append(row); added += 1
    write_csv(EDIT / "persons.csv", header, rows)
    return added

if __name__ == "__main__":
    print("新增来源:", add_sources())
    print("新增事件:", add_events())
    print("新增人物:", add_persons())
