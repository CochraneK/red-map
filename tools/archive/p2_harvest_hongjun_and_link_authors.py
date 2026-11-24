#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P2-2: Harvest 35 remaining high-value firsthand chapters from 1937《红军长征记》,
fix 4 corrupted author names/summaries in persons.csv, and eliminate all 31 zero-event persons.
"""
from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

NEW_EVENTS: list[dict[str, str]] = [
    {
        "id": "hj4_19341016_chufa_qian",
        "date": "19341016",
        "displayDate": "1934年10月中旬",
        "datePrecision": "month",
        "sequence": "210",
        "forceId": "red_first",
        "layer": "march",
        "type": "民生",
        "title": "董必武《出发前》：准备草鞋与未知前途的真实心境",
        "description": "1934年10月中旬主力转移前夕，董必武与徐特立闲谈决定随军长征，并自述“一天跑六十里毫无问题”。他在《出发前》坦率记下当年离开江西苏区时并无明确方向，“假使在出发前就知道要走二万五千里的程途，要经过十三个月的时间……当时不知将作何感想”。",
        "locationName": "江西瑞金于都",
        "lat": "25.9520", "lng": "115.4150",
        "participants": "董必武、徐特立、中央纵队",
        "importance": "2",
        "sourceIds": "src_hongjun_changzhengji",
        "certainty": "medium",
        "notes": "出处：《红军长征记》第9篇《出发前》（必武/董必武著）。",
    },
    {
        "id": "hj4_19341018_likai_laojia",
        "date": "19341018",
        "displayDate": "1934年10月18日",
        "datePrecision": "day",
        "sequence": "211",
        "forceId": "red_first",
        "layer": "march",
        "type": "行军",
        "title": "童小鹏《离开老家的一天》：告别中央苏区故土",
        "description": "1934年10月18日前后，红一军团政治部秘书童小鹏在行军第三天写下告别中央苏区老家的真挚感受：“从今天起，就要离开我们的老家，离开这块自由的乐土，离开数百万的兄弟姊妹……为了执行新任务，就遵命继续出发。”",
        "locationName": "江西于都",
        "lat": "25.9510", "lng": "115.4100",
        "participants": "童小鹏、红一军团",
        "importance": "2",
        "sourceIds": "src_hongjun_changzhengji",
        "certainty": "medium",
        "notes": "出处：《红军长征记》第13篇《离开老家的一天》（小朋/童小鹏著）。",
    },
    {
        "id": "hj4_19341023_gupi_wei",
        "date": "19341023",
        "displayDate": "1934年10月23日",
        "datePrecision": "day",
        "sequence": "212",
        "forceId": "red_first",
        "layer": "march",
        "type": "战斗",
        "title": "张爱萍《占领古陂圩》：红十一团猛攻突破第一道封锁线",
        "description": "1934年10月下旬，红三军团第四师先头十一团占领白石圩次日冒进五十里突击赣南要镇古陂圩，突破粤军一个团及师直属队扼守的南线第一道封锁线。",
        "locationName": "江西信丰古陂圩",
        "lat": "25.2520", "lng": "114.9560",
        "participants": "张爱萍、红三军团第四师十一团",
        "importance": "2",
        "sourceIds": "src_hongjun_changzhengji",
        "certainty": "medium",
        "notes": "出处：《红军长征记》第24篇《占领古陂圩》（艾平/张爱萍著）。",
    },
    {
        "id": "hj4_19341106_yizhang",
        "date": "19341106",
        "displayDate": "1934年11月上旬",
        "datePrecision": "month",
        "sequence": "213",
        "forceId": "red_first",
        "layer": "march",
        "type": "战斗",
        "title": "王平《占领宜章城》：红六师大雨急行一百二十里破第二道封锁线",
        "description": "1934年11月上旬，红三军团第六师在前一日急行一百二十里后冒大雨继续挺进，先头十六团击溃二百余人拦路民团并乘胜攻占湘南重镇宜章城，撕开敌人第二道封锁线。",
        "locationName": "湖南宜章",
        "lat": "25.3990", "lng": "112.9510",
        "participants": "王平、红三军团第六师",
        "importance": "2",
        "sourceIds": "src_hongjun_changzhengji",
        "certainty": "medium",
        "notes": "出处：《红军长征记》第27篇《占领宜章城》（斯顿/王平著）。",
    },
    {
        "id": "hj4_19341116_linwu_daozhou",
        "date": "19341116",
        "displayDate": "1934年11月16日",
        "datePrecision": "day",
        "sequence": "214",
        "forceId": "red_first",
        "layer": "march",
        "type": "行军",
        "title": "耿飚《由临武至道州》：红一师昼夜急行一百二十里抢占道州",
        "description": "1934年11月16日，红一军团第一师参谋长耿飚率部从临武急行八十里后，又接令连夜续行四十里赶赴雷家祠、祠堂圩抢占道州，留下昼夜急行军与突破湘南封锁线的详细行军记。",
        "locationName": "湖南临武至道县",
        "lat": "25.5260", "lng": "111.6010",
        "participants": "耿飚、红一军团第一师",
        "importance": "2",
        "sourceIds": "src_hongjun_changzhengji",
        "certainty": "medium",
        "notes": "出处：《红军长征记》第30篇《由临武至道州》（耿飚著）。",
    },
    {
        "id": "hj4_19341129_xiangshui_rear",
        "date": "19341129",
        "displayDate": "1934年11月下旬",
        "datePrecision": "month",
        "sequence": "215",
        "forceId": "red_first",
        "layer": "march",
        "type": "渡险",
        "title": "李雪三《紧急渡湘水》：红五军团十三师断后苦战掩护全军渡江",
        "description": "1934年11月底湘江战役危急关头，担任全军总后卫的红五军团仍在距湘江百余里外迎击桂系与中央军四面追击及敌机轰炸，十三师苦战大半日后连夜急行五六十里抢渡湘江。",
        "locationName": "广西兴安全州湘江一线",
        "lat": "25.7750", "lng": "110.9520",
        "participants": "李雪三、周碧泉、红五军团第十三师",
        "importance": "3",
        "sourceIds": "src_hongjun_changzhengji",
        "certainty": "medium",
        "notes": "出处：《红军长征记》第36篇《紧急渡湘水》（李雪三著）；并参第111篇《长征中走在最后头的一个师》（周碧泉著）。",
    },
    {
        "id": "hj4_19341130_zhongwei",
        "date": "19341130",
        "displayDate": "1934年11月30日",
        "datePrecision": "day",
        "sequence": "216",
        "forceId": "red_first",
        "layer": "march",
        "type": "战斗",
        "title": "莫文骅《在重围中》：三四十万敌军合围湘江下的突围亲历",
        "description": "1934年11月底，中央红军进抵道州与全州、灌阳之间时遭周浑元、薛岳及桂军等三四十万敌军合围，敌机投弹并散发劝降传单。红八军团宣传部长莫文骅详记重围突围的惊险经过。",
        "locationName": "广西全州灌阳一带",
        "lat": "25.7350", "lng": "111.0810",
        "participants": "莫文骅、红八军团",
        "importance": "2",
        "sourceIds": "src_hongjun_changzhengji",
        "certainty": "medium",
        "notes": "出处：《红军长征记》第37篇《在重围中》（莫文骅著）。",
    },
    {
        "id": "hj4_19341201_last_blockade",
        "date": "19341201",
        "displayDate": "1934年12月1日",
        "datePrecision": "day",
        "sequence": "217",
        "forceId": "red_first",
        "layer": "march",
        "type": "战斗",
        "title": "谭政《最后的一道封锁线》：血战突破湘桂第四道封锁线",
        "description": "1934年12月初，谭政记述中央红军历时一个月零八天连破三道封锁线后，在湘桂边境迎战周浑元、粤军、桂军多路夹击，血战突破国民党军第四道湘江封锁线的全景。",
        "locationName": "湘桂边境湘江一线",
        "lat": "25.7920", "lng": "110.9050",
        "participants": "谭政、红一军团",
        "importance": "3",
        "sourceIds": "src_hongjun_changzhengji",
        "certainty": "medium",
        "notes": "出处：《红军长征记》第38篇《最后的一道封锁线》（谭政著）。",
    },
    {
        "id": "hj4_19341207_fanghuozhe",
        "date": "19341207",
        "displayDate": "1934年12月上旬",
        "datePrecision": "month",
        "sequence": "218",
        "forceId": "red_first",
        "layer": "march",
        "type": "民生",
        "title": "陈明《放火者》：越老山界入苗山严守民族纪律实录",
        "description": "1934年12月上旬，中央红军翻越老山界进入越城岭苗山区域。陈明在《放火者》中记录苗寨木板屋相连的地理民俗，以及红军严守民族纪律、当场揭穿并扑灭反动分子蓄意纵火嫁祸红军的真实一幕。",
        "locationName": "桂湘黔边苗山",
        "lat": "25.9800", "lng": "110.1200",
        "participants": "陈明、干部团",
        "importance": "2",
        "sourceIds": "src_hongjun_changzhengji",
        "certainty": "medium",
        "notes": "出处：《红军长征记》第41篇《放火者》（陈明著）。",
    },
    {
        "id": "hj4_19341231_wengan_battle",
        "date": "19341231",
        "displayDate": "1934年12月31日",
        "datePrecision": "day",
        "sequence": "219",
        "forceId": "red_first",
        "layer": "march",
        "type": "战斗",
        "title": "张震《瓮安之役》：严冬攻克瓮安与贵州“干人儿”纪实",
        "description": "1934年严冬，红三军团第四师十团三营营长张震率部进抵贵州瓮安参战，他在《瓮安之役》中既记录攻克瓮安城之战，更以亲历目光写下黔军军阀统治下贵州“干人儿”赤贫无衣的凄惨实景。",
        "locationName": "贵州瓮安",
        "lat": "27.0680", "lng": "107.4790",
        "participants": "张震、红三军团第四师十团",
        "importance": "2",
        "sourceIds": "src_hongjun_changzhengji",
        "certainty": "medium",
        "notes": "出处：《红军长征记》第46篇《瓮安之役》（张震著，原署张见生）。",
    },
    {
        "id": "hj4_19350102_hong4_wujiang",
        "date": "19350102",
        "displayDate": "1935年1月2日",
        "datePrecision": "day",
        "sequence": "220",
        "forceId": "red_first",
        "layer": "march",
        "type": "渡险",
        "title": "张爱萍《红四师强渡乌江的故事》：破“鹅毛沉底”天险",
        "description": "1935年1月初，面对当地群众所称“水深流急、鹅毛沉底、无法架桥”的乌江天险，红三军团第四师在茶山关等渡口扎竹筏强渡并架通浮桥，张爱萍以亲历者身份记述强渡始末。",
        "locationName": "贵州乌江茶山关一线",
        "lat": "27.2850", "lng": "107.2650",
        "participants": "张爱萍、红三军团第四师",
        "importance": "2",
        "sourceIds": "src_hongjun_changzhengji",
        "certainty": "medium",
        "notes": "出处：《红军长征记》第45篇《红四师强渡乌江的故事》（艾平/张爱萍著）。",
    },
    {
        "id": "hj4_19350102_wujiang_heroes",
        "date": "19350102",
        "displayDate": "1935年1月2日",
        "datePrecision": "day",
        "sequence": "221",
        "forceId": "red_first",
        "layer": "march",
        "type": "渡险",
        "title": "《乌江战斗中的英雄》：泅水撑排与抢渡红星奖章名录",
        "description": "据1935年1月15日《红星报》收录的集体署名名录，江界河强渡乌江中涌现一营营长罗有保、三连连长毛振华（获红星奖章）以及王家福、王有才、唐占钦、羽辉明、赖采芬等泅水与撑排英雄。",
        "locationName": "贵州瓮安江界河渡口",
        "lat": "27.3200", "lng": "107.4500",
        "participants": "泅水及撑排战士、毛振华、红一军团第二师四团",
        "importance": "2",
        "sourceIds": "src_hongjun_changzhengji",
        "certainty": "medium",
        "notes": "出处：《红军长征记》第130篇《乌江战斗中的英雄》（集体署名“泅水及撑排的”，转录1935年1月15日《红星报》）。",
    },
    {
        "id": "hj4_19350120_chishui_advance",
        "date": "19350120",
        "displayDate": "1935年1月下旬",
        "datePrecision": "month",
        "sequence": "222",
        "forceId": "red_first",
        "layer": "march",
        "type": "行军",
        "title": "谭政《向赤水前进》：遵义会议后全军士气焕然一新",
        "description": "1935年1月下旬遵义会议闭幕后，中央红军向赤水河方向进军。谭政记述部队一扫此前沉闷情绪、喜气洋洋，黔北四乡穷苦“干人儿”成百上千涌向红军要求参军的热烈景象。",
        "locationName": "贵州遵义桐梓一带",
        "lat": "28.1320", "lng": "106.8260",
        "participants": "谭政、红一军团",
        "importance": "2",
        "sourceIds": "src_hongjun_changzhengji",
        "certainty": "medium",
        "notes": "出处：《红军长征记》第49篇《向赤水前进》（谭政著）。",
    },
    {
        "id": "hj4_19350225_tongzi_zunyi",
        "date": "19350225",
        "displayDate": "1935年2月25日",
        "datePrecision": "day",
        "sequence": "223",
        "forceId": "red_first",
        "layer": "march",
        "type": "战斗",
        "title": "黄克功《由桐梓到遵义》：红十三团仰攻娄山关与红花园激战",
        "description": "1935年2月下旬二渡赤水回师黔北，红三军团第十三团在彭雪枫指挥下仰攻柏辉章黔军扼守的娄山关与红花园阵地，连破黔军三个团，打通再克遵义城之门。",
        "locationName": "贵州桐梓娄山关",
        "lat": "28.0050", "lng": "106.8280",
        "participants": "黄克功、彭雪枫、红三军团第十三团",
        "importance": "2",
        "sourceIds": "src_hongjun_changzhengji",
        "certainty": "medium",
        "notes": "出处：《红军长征记》第55篇《由桐梓到遵义》（黄克功著）。",
    },
    {
        "id": "hj4_19350228_zunyi_day",
        "date": "19350228",
        "displayDate": "1935年2月28日",
        "datePrecision": "day",
        "sequence": "224",
        "forceId": "red_first",
        "layer": "march",
        "type": "战斗",
        "title": "徐梦秋《一天——再占遵义城》：再战遵义城一昼夜亲历",
        "description": "1935年2月底，《红军长征记》主编徐梦秋（笔名莫休）以七千余字白描记录再占遵义城那紧张的一天：清脆起床号音、密集行军队列、激战城郊与胜利回师的鲜活细节。",
        "locationName": "贵州遵义",
        "lat": "27.6940", "lng": "106.9270",
        "participants": "徐梦秋、红三军团",
        "importance": "2",
        "sourceIds": "src_hongjun_changzhengji",
        "certainty": "medium",
        "notes": "出处：《红军长征记》第54篇《一天——再占遵义城》（莫休/徐梦秋著）。",
    },
    {
        "id": "hj4_19350228_zunyi_pursuit",
        "date": "19350228",
        "displayDate": "1935年2月28日",
        "datePrecision": "day",
        "sequence": "225",
        "forceId": "red_first",
        "layer": "march",
        "type": "战斗",
        "title": "舒同《遵义追击》：再克遵义老城新城迎击吴奇伟纵队",
        "description": "1935年2月28日，红二师政治部主任舒同记述红军攻克遵义老城、围攻新城逼得守敌柏辉章连电求援，随即奉命迎击薛岳增援的吴奇伟纵队并展开猛烈追击。",
        "locationName": "贵州遵义城南",
        "lat": "27.6620", "lng": "106.9150",
        "participants": "舒同、红一军团第二师",
        "importance": "2",
        "sourceIds": "src_hongjun_changzhengji",
        "certainty": "medium",
        "notes": "出处：《红军长征记》第53篇《遵义追击》（舒同著）。",
    },
    {
        "id": "hj4_19350305_xiaomaowu",
        "date": "19350305",
        "displayDate": "1935年3月上旬",
        "datePrecision": "month",
        "sequence": "226",
        "forceId": "red_first",
        "layer": "march",
        "type": "民生",
        "title": "曙霞《小茅屋》：黔西北贫民寒冬无裤围煤炉写真诗纪",
        "description": "1935年春转战黔西北边境期间，红军作者曙霞写下《小茅屋——贵州西北边境的贫民生活写真》，记录当地贫农严冬食仅包谷、孩童无衣围煤炉取暖常致灼伤的惨状与踊跃参军呼声。",
        "locationName": "贵州遵义仁怀一带",
        "lat": "27.7850", "lng": "106.4800",
        "participants": "曙霞、中央红军",
        "importance": "2",
        "sourceIds": "src_hongjun_changzhengji",
        "certainty": "medium",
        "notes": "出处：《红军长征记》第57篇《小茅屋——贵州西北边境的贫民生活写真》（曙霞著）。",
    },
    {
        "id": "hj4_19350306_canku_hongzha",
        "date": "19350306",
        "displayDate": "1935年3月上旬",
        "datePrecision": "month",
        "sequence": "227",
        "forceId": "red_first",
        "layer": "march",
        "type": "战斗",
        "title": "童小鹏《残酷的轰炸》：遵义大捷后转进鸭溪遭敌机空袭",
        "description": "1935年3月初击溃吴奇伟纵队凯旋遵义后，红军向鸭溪方向转进寻歼周浑元部，途中遭遇国民党军飞机猛烈轰炸扫射。童小鹏在《残酷的轰炸》中记录红军防空疏散与战友抢救伤员场景。",
        "locationName": "贵州遵义鸭溪",
        "lat": "27.5600", "lng": "106.6600",
        "participants": "童小鹏、红一军团",
        "importance": "2",
        "sourceIds": "src_hongjun_changzhengji",
        "certainty": "medium",
        "notes": "出处：《红军长征记》第58篇《残酷的轰炸》（小朋/童小鹏著）。",
    },
    {
        "id": "hj4_19350331_daoliushui",
        "date": "19350331",
        "displayDate": "1935年3月31日",
        "datePrecision": "day",
        "sequence": "228",
        "forceId": "red_first",
        "layer": "march",
        "type": "战斗",
        "title": "陈士榘《倒流水四个连控制敌人三个师》：巧制封锁线护主力南下",
        "description": "1935年3月底四渡赤水南进关键时刻，红一军团教导营营长陈士榘奉命率教导营与第二团部分兵力仅以四个连扼守长干山与枫香坝之间的倒流水高地，成功牵制敌三个师，掩护主力南穿封锁线渡乌江。",
        "locationName": "贵州仁怀枫香坝倒流水",
        "lat": "27.6480", "lng": "106.4300",
        "participants": "陈士榘、红一军团教导营",
        "importance": "3",
        "sourceIds": "src_hongjun_changzhengji",
        "certainty": "medium",
        "notes": "出处：《红军长征记》第60篇《倒流水四个连控制敌人三个师》（陈士榘著）。",
    },
    {
        "id": "hj4_19350410_dingfan",
        "date": "19350410",
        "displayDate": "1935年4月10日",
        "datePrecision": "day",
        "sequence": "229",
        "forceId": "red_first",
        "layer": "march",
        "type": "战斗",
        "title": "陈士榘《夺取定番城》：穿越贵阳龙里公路急袭克定番",
        "description": "1935年4月9日至10日，中央红军佯逼贵阳令坐镇督战的蒋介石恐慌急调四路援军之际，陈士榘所在红一军团先头部队拂晓穿越贵阳至龙里公路封锁线，乘虚急袭攻克定番（今惠水）县城。",
        "locationName": "贵州惠水定番",
        "lat": "26.1330", "lng": "106.6590",
        "participants": "陈士榘、红一军团",
        "importance": "2",
        "sourceIds": "src_hongjun_changzhengji",
        "certainty": "medium",
        "notes": "出处：《红军长征记》第62篇《夺取定番城》（陈士榘著）。",
    },
    {
        "id": "hj4_19350418_beipanjiang_ai",
        "date": "19350418",
        "displayDate": "1935年4月18日",
        "datePrecision": "day",
        "sequence": "230",
        "forceId": "red_first",
        "layer": "march",
        "type": "渡险",
        "title": "张爱萍《抢渡北盘江的前后》：红十一团急行一百八十里架浮桥",
        "description": "1935年4月中旬占领广顺次夜，红三军团军团长彭德怀、政委杨尚昆直接电令红十一团作为先遣团，一昼夜急行一百八十里抢占北盘江白层渡口并架设浮桥，掩护全野战军顺利西渡入滇。",
        "locationName": "贵州贞丰白层北盘江",
        "lat": "25.5650", "lng": "105.6120",
        "participants": "张爱萍、彭德怀、杨尚昆、红三军团第十一团",
        "importance": "2",
        "sourceIds": "src_hongjun_changzhengji",
        "certainty": "medium",
        "notes": "出处：《红军长征记》第66篇《抢渡北盘江的前后》（艾平/张爱萍著）。",
    },
    {
        "id": "hj4_19350429_wuyi_jinsha",
        "date": "19350429",
        "displayDate": "1935年4月29日",
        "datePrecision": "day",
        "sequence": "231",
        "forceId": "red_first",
        "layer": "march",
        "type": "渡险",
        "title": "莫文骅《“五一”的前后》：红色干部团烈日疾行抢占金沙江渡口",
        "description": "1935年4月29日至5月初，由红军大学和步兵学校合编的红色干部团在滇北烈日炙烤下背负枪弹干粮急行军奔向金沙江皎平渡，抢占渡口并阻击川军，莫文骅生动记录干部团“五一”前后昼夜奋战。",
        "locationName": "云南禄劝皎平渡",
        "lat": "26.2980", "lng": "102.3820",
        "participants": "莫文骅、干部团",
        "importance": "2",
        "sourceIds": "src_hongjun_changzhengji",
        "certainty": "medium",
        "notes": "出处：《红军长征记》第70篇《“五一”的前后》（莫文骅著）。",
    },
    {
        "id": "hj4_19350521_yizugeming",
        "date": "19350521",
        "displayDate": "1935年5月21日",
        "datePrecision": "day",
        "sequence": "232",
        "forceId": "red_first",
        "layer": "march",
        "type": "民生",
        "title": "廖志高《一个忠实的革命“倮倮”》：越嶲发动彝汉群众与彝族战士故事",
        "description": "1935年5月下旬中央红军渡过金沙江攻占四川越嶲（今越西）后，冕宁青年廖志高亲历红军张贴取消苛捐杂税标语、买卖公平与打土豪分粮衣物，记录了一名彝族青年毅然投身革命的感人故事。",
        "locationName": "四川越西",
        "lat": "28.6410", "lng": "102.5090",
        "participants": "廖志高、中央红军总政治部",
        "importance": "2",
        "sourceIds": "src_hongjun_changzhengji",
        "certainty": "medium",
        "notes": "出处：《红军长征记》第82篇《一个忠实的革命“倮倮”》（廖志高著）。",
    },
    {
        "id": "hj4_19350615_huizhan_baoxing",
        "date": "19350615",
        "displayDate": "1935年6月中旬",
        "datePrecision": "month",
        "sequence": "233",
        "forceId": "red_first",
        "layer": "march",
        "type": "战斗",
        "title": "黄镇《回占宝兴》：红五军团回师邛崃山脉奇袭白军扩大两军会师区",
        "description": "1935年6月中旬红一、红四方面军懋功会师前后，红五军团三十七团奉命折返宝兴阻击追敌，当地群众飞报白军正在南街头庙里休息，一营二连二排端起刺刀奇袭回占宝兴。",
        "locationName": "四川宝兴",
        "lat": "30.3690", "lng": "102.8150",
        "participants": "黄镇、红五军团第三十七团",
        "importance": "2",
        "sourceIds": "src_hongjun_changzhengji",
        "certainty": "medium",
        "notes": "出处：《红军长征记》第88篇《回占宝兴》（黄镇著）。",
    },
    {
        "id": "hj4_19350710_luhua_liang",
        "date": "19350710",
        "displayDate": "1935年7月上旬",
        "datePrecision": "month",
        "sequence": "234",
        "forceId": "red_first",
        "layer": "march",
        "type": "民生",
        "title": "舒同《芦花运粮》：翻越大雪山后绝粮与马河坝、芦花筹运青稞",
        "description": "1935年7月上旬，由卓克基经大雪山向黑水、芦花推进的红军陷入粮糈断绝、茹草饮雪的极端困境，舒同详记红军官兵在海拔高寒的雪山村寨与芦花一带艰难运粮救命的经历。",
        "locationName": "四川黑水芦花",
        "lat": "32.0620", "lng": "102.9910",
        "participants": "舒同、红一军团第二师",
        "importance": "2",
        "sourceIds": "src_hongjun_changzhengji",
        "certainty": "medium",
        "notes": "出处：《红军长征记》第91篇《芦花运粮》（舒同著）。",
    },
    {
        "id": "hj4_19350718_wabuliangzi",
        "date": "19350718",
        "displayDate": "1935年7月中旬",
        "datePrecision": "month",
        "sequence": "235",
        "forceId": "red_first",
        "layer": "march",
        "type": "民生",
        "title": "贾拓夫《瓦布梁子》：芦花筹粮委员会奉命筹集六十万斤粮食",
        "description": "1935年7月中旬，一、四方面军进至黑水、芦花后首要难题即为筹粮。军委在毛儿盖与芦花分设筹粮委员会，芦花粮委担负筹集六十万斤粮食任务，贾拓夫率武装沿黑水峡谷绝壁徒步三日深入瓦布梁子筹粮。",
        "locationName": "四川黑水瓦布梁子",
        "lat": "32.1400", "lng": "103.1600",
        "participants": "贾拓夫、芦花筹粮委员会",
        "importance": "2",
        "sourceIds": "src_hongjun_changzhengji",
        "certainty": "medium",
        "notes": "出处：《红军长征记》第95篇《瓦布梁子》（拓夫/贾拓夫著）。",
    },
    {
        "id": "hj4_19350725_boluozi",
        "date": "19350725",
        "displayDate": "1935年7月下旬",
        "datePrecision": "month",
        "sequence": "236",
        "forceId": "red_first",
        "layer": "march",
        "type": "行军",
        "title": "童小鹏、王辉球双篇《波罗子》：穿荒山湿地赴波罗子筹粮备过草地",
        "description": "1935年7月下旬，为储备过草地所需大批干粮，红一军团与红二师由毛儿盖、卡龙出发翻越人烟绝迹的荒山与湿润草地赴松潘东北波罗子筹粮。童小鹏与王辉球分别以同名《波罗子》记下此段艰苦行军。",
        "locationName": "四川松潘波罗子",
        "lat": "32.6500", "lng": "103.2200",
        "participants": "童小鹏、王辉球、红一军团第二师",
        "importance": "2",
        "sourceIds": "src_hongjun_changzhengji",
        "certainty": "medium",
        "notes": "出处：《红军长征记》第96篇《波罗子》（童小鹏著）、第97篇《波罗子》（王辉球著）。",
    },
    {
        "id": "hj4_19350815_songpan_nw",
        "date": "19350815",
        "displayDate": "1935年8月中旬",
        "datePrecision": "month",
        "sequence": "237",
        "forceId": "red_first",
        "layer": "march",
        "type": "民生",
        "title": "徐梦秋《松潘的西北》：驻留毛儿盖五十天万字纪实",
        "description": "1935年夏秋，随先头团最先抵达毛儿盖又随最后掩护梯队离开的徐梦秋（莫休），以万余字详记红军在松潘西北毛儿盖驻留五十天间的作战、会议、整训教育及藏羌民族工作。",
        "locationName": "四川松潘毛儿盖",
        "lat": "32.6810", "lng": "103.0580",
        "participants": "徐梦秋、中央红军",
        "importance": "2",
        "sourceIds": "src_hongjun_changzhengji",
        "certainty": "medium",
        "notes": "出处：《红军长征记》第99篇《松潘的西北》（莫休/徐梦秋著）。",
    },
    {
        "id": "hj4_19350823_jueshi_yitian",
        "date": "19350823",
        "displayDate": "1935年8月下旬",
        "datePrecision": "month",
        "sequence": "238",
        "forceId": "red_first",
        "layer": "march",
        "type": "行军",
        "title": "何涤宙《绝食的一天》：过草地三日风霜露宿与绝粮行军",
        "description": "1935年8月下旬穿越若尔盖草地途中，干部团成员何涤宙写下《绝食的一天》，记述连续三天不见人烟房屋、忍受风吹雨淋日晒夜露及绝粮行军中“人流从南向北流着”的悲壮图景。",
        "locationName": "四川若尔盖草地",
        "lat": "33.2400", "lng": "103.0800",
        "participants": "何涤宙、干部团",
        "importance": "2",
        "sourceIds": "src_hongjun_changzhengji",
        "certainty": "medium",
        "notes": "出处：《红军长征记》第100篇《绝食的一天》（何涤宙著）。",
    },
    {
        "id": "hj4_19350825_maoergai_banyou",
        "date": "19350825",
        "displayDate": "1935年8月下旬",
        "datePrecision": "month",
        "sequence": "239",
        "forceId": "red_first",
        "layer": "march",
        "type": "行军",
        "title": "董必武《从毛儿盖到班佑》：六天穿小草地与七里桥牛房见闻",
        "description": "1935年8月下旬，年近五十的董必武随中央纵队用六天穿越毛儿盖至班佑的“小草地”，日行七八十里，细腻记述七里桥百十间涂满牛粪的低矮游牧牛房与沼泽荒原风貌。",
        "locationName": "四川若尔盖班佑",
        "lat": "33.5450", "lng": "103.0400",
        "participants": "董必武、中央纵队",
        "importance": "2",
        "sourceIds": "src_hongjun_changzhengji",
        "certainty": "medium",
        "notes": "出处：《红军长征记》第101篇《从毛儿盖到班佑》（必武/董必武著）。",
    },
    {
        "id": "hj4_19350831_fulubing",
        "date": "19350831",
        "displayDate": "1935年8月31日",
        "datePrecision": "day",
        "sequence": "240",
        "forceId": "red_first",
        "layer": "march",
        "type": "民生",
        "title": "周士第《俘虏兵的一束话》：包座歼敌后对七八百俘虏开展政治工作",
        "description": "1935年8月底包座战斗歼灭国民党军第四十九师两个整团后，总政治部派周士第与王盛荣、王观澜赴包座南端麦田，向集合起来的七八百名俘虏兵宣讲红军北上抗日政策并征求留去意愿。",
        "locationName": "四川若尔盖包座",
        "lat": "33.6900", "lng": "103.2400",
        "participants": "周士第、王盛荣、王观澜、总政治部",
        "importance": "2",
        "sourceIds": "src_hongjun_changzhengji",
        "certainty": "medium",
        "notes": "出处：《红军长征记》第105篇《俘虏兵的一束话》（周士梯/周士第著）。",
    },
    {
        "id": "hj4_19350917_lazikou_yang",
        "date": "19350917",
        "displayDate": "1935年9月17日",
        "datePrecision": "day",
        "sequence": "241",
        "forceId": "red_first",
        "layer": "march",
        "type": "战斗",
        "title": "杨成武《突破天险的腊子口》：红四团夜出莫牙寺两日强攻腊子口",
        "description": "1935年9月15日至17日，红一军团第二师第四团政委杨成武与团长王开湘奉命以两天行程从白龙江畔莫牙寺深夜出发，经正面强攻与攀登绝壁迂回，一举攻克甘南天险腊子口。",
        "locationName": "甘肃迭部腊子口",
        "lat": "34.1220", "lng": "103.8960",
        "participants": "杨成武、王开湘、红一军团第二师第四团",
        "importance": "3",
        "sourceIds": "src_hongjun_changzhengji",
        "certainty": "medium",
        "notes": "出处：《红军长征记》第106篇《突破天险的腊子口》（杨成武著）。",
    },
    {
        "id": "hj4_19351022_dao_qinjia",
        "date": "19351022",
        "displayDate": "1935年10月下旬",
        "datePrecision": "month",
        "sequence": "242",
        "forceId": "red_first",
        "layer": "march",
        "type": "民生",
        "title": "谢扶民《到了亲家》：抵达陕北吴起镇七日休整与军民联欢会餐",
        "description": "1935年10月下旬中央红军抵达陕北苏区吴起镇后休整七天，苏区群众牵牛羊、抬肥猪、担青菜与马铃薯前来慰问，各连队召开军民联欢晚会并会餐红烧肉与小米饭，官兵亲切称苏区为“到了亲家”。",
        "locationName": "陕西吴起镇",
        "lat": "36.9270", "lng": "108.1760",
        "participants": "谢扶民、红三军团、陕北苏区群众",
        "importance": "2",
        "sourceIds": "src_hongjun_changzhengji",
        "certainty": "medium",
        "notes": "出处：《红军长征记》第110篇《到了亲家》（谢扶民著）。",
    },
    {
        "id": "hj4_19351025_gansu_shaanxi",
        "date": "19351025",
        "displayDate": "1935年10月下旬",
        "datePrecision": "month",
        "sequence": "243",
        "forceId": "red_first",
        "layer": "historiography",
        "type": "史料",
        "title": "邓发《从甘肃到陕西》：近三万字纪实记录北上长征最后阶段",
        "description": "邓发（笔名方林）在《雪山草地行军记》之外另撰近三万字长篇纪实《从甘肃到陕西——抗日人民红军北上长征的最后阶段》，详述翻越岷山进入甘南直至抵达陕北苏区的沿途见闻与战略收官。",
        "locationName": "陕西吴起镇",
        "lat": "36.9270", "lng": "108.1760",
        "participants": "邓发、中央红军",
        "importance": "2",
        "sourceIds": "src_hongjun_changzhengji",
        "certainty": "medium",
        "notes": "出处：《红军长征记》第8篇《从甘肃到陕西——抗日人民红军北上长征的最后阶段》（方林/邓发著）。",
    },
    {
        "id": "hj4_19351028_red5_rearguard",
        "date": "19351028",
        "displayDate": "1935年10月",
        "datePrecision": "month",
        "sequence": "244",
        "forceId": "red_first",
        "layer": "theme_stat",
        "type": "史料",
        "title": "红五军团全军总后卫纪实：宁都起义劲旅火把夜行断后万里",
        "description": "据黄镇《长征前的红五军团》、李雪三《艰苦奋斗的五军团》与周碧泉《长征中走在最后头的一个师》三篇合证：由1931年宁都起义官兵编成的红五军团自离开中央苏区起始终承担全军总后卫，终日打火把夜行军、大路露宿掩护主力西进。",
        "locationName": "中央红军长征沿线",
        "lat": "36.9270", "lng": "108.1760",
        "participants": "黄镇、李雪三、周碧泉、红五军团",
        "importance": "3",
        "sourceIds": "src_hongjun_changzhengji",
        "certainty": "medium",
        "notes": "出处：《红军长征记》第111篇（周碧泉）、第112篇（黄镇）、第113篇（李雪三）。",
    },
]


def main() -> int:
    # 1) Fix 4 corrupted names/summaries in persons.csv & discover disk IDs of non-ASCII authors
    persons_path = ROOT / "data_edit/persons.csv"
    with persons_path.open("r", encoding="utf-8-sig", newline="") as f:
        pr = csv.DictReader(f)
        pfields = list(pr.fieldnames or [])
        persons = list(pr)

    non_ascii_ids: dict[str, str] = {}
    for p in persons:
        pid = p["id"]
        summary = p.get("summary", "")
        if pid == "bi_wu":
            p["name"] = "董必武"
            p["summary"] = (
                "原名董贤琮，字用威，号璧伍，笔名必武。1911年参加辛亥革命，1920年秋在武汉建立共产主义小组，"
                "1921年7月出席中国共产党第一次全国代表大会。长征中任中央纵队干部休养连总支部书记，"
                "在《红军长征记》留下《出发前》《从毛儿盖到班佑》《长征中的女英雄》三篇纪实。"
            )
        elif pid == "xu_sidai":
            p["name"] = "陈士榘"
            p["summary"] = (
                "1927年参加秋收起义。长征时任红一军团教导营营长，在《红军长征记》留下《倒流水四个连控制敌人三个师》"
                "《夺取定番城》两篇战斗实录；1947年任华东野战军参谋长，1955年被授予上将军衔。"
            )
        elif pid == "wang_huazheng":
            p["name"] = "张爱萍"
            p["summary"] = (
                "笔名艾平，《红军长征记》供稿最多的作者（18篇）。长征中任红三军团第四师政治部主任、第十一团及第十三团政委。"
                "1949年受命组建华东海军，1955年指挥一江山岛联合登陆作战并授上将，后组织领导“两弹一星”研制工程。"
            )
        elif pid == "yang_chengwu":
            p["name"] = "杨成武"
        elif pid == "jia_tuofu":
            p["summary"] = (
                "长征中任红军总政治部白军工作部部长，1935年10月中央红军到达陕甘地区后受中央委托负责陕北党组织与红军的联络工作。"
                "在《红军长征记》以“拓夫”署名留下《瓦布梁子》筹粮纪实。"
            )
        # Discover disk IDs for the 4 zero-event non-ASCII authors by unique summary markers
        if "《红军长征记》实际编者" in summary:
            non_ascii_ids["xu_mengqiu"] = pid
        elif "长征中任红八军团宣传部长" in summary:
            non_ascii_ids["mo_wenhua"] = pid
        elif "留下《经贵州苗山》" in summary:
            non_ascii_ids["xie_fumin"] = pid
        elif "留下《聂都游击队的记述》" in summary:
            non_ascii_ids["zhang_yunyi"] = pid

    if len(non_ascii_ids) != 4:
        raise RuntimeError(f"Expected 4 non-ASCII author IDs, got {non_ascii_ids}")

    with persons_path.open("w", encoding="utf-8-sig", newline="") as f:
        pw = csv.DictWriter(f, fieldnames=pfields)
        pw.writeheader()
        pw.writerows(persons)

    # 2) Append 35 new firsthand events (idempotent: skip if id already present)
    events_path = ROOT / "data_edit/events.csv"
    with events_path.open("r", encoding="utf-8-sig", newline="") as f:
        er = csv.DictReader(f)
        efields = list(er.fieldnames or [])
        events = list(er)

    existing_ev_ids = {e["id"] for e in events}
    added_evs = 0
    for item in NEW_EVENTS:
        if item["id"] in existing_ev_ids:
            continue
        row = {col: "" for col in efields}
        row["enabled"] = "TRUE"
        row.update(item)
        events.append(row)
        existing_ev_ids.add(item["id"])
        added_evs += 1

    with events_path.open("w", encoding="utf-8-sig", newline="") as f:
        ew = csv.DictWriter(f, fieldnames=efields)
        ew.writeheader()
        ew.writerows(events)

    # 3) Link all 31 previously zero-event authors to both new & existing events
    new_links: list[tuple[str, str, str, str]] = [
        # (personId, eventId, role, sourceIds)
        ("wang_huazheng", "hj4_19341023_gupi_wei", "亲历并著《占领古陂圩》（第24篇）", "src_hongjun_changzhengji"),
        ("wang_huazheng", "hj4_19350102_hong4_wujiang", "亲历并著《红四师强渡乌江的故事》（第45篇）", "src_hongjun_changzhengji"),
        ("wang_huazheng", "hj4_19350418_beipanjiang_ai", "率十一团先遣并著《抢渡北盘江的前后》（第66篇）", "src_hongjun_changzhengji"),
        ("wang_huazheng", "hjdet_06", "著《“倮倮”投军》（第80篇）", "src_hongjun_changzhengji"),
        ("tong_xiaopeng", "hj4_19341018_likai_laojia", "亲历并著《离开老家的一天》（第13篇）", "src_hongjun_changzhengji"),
        ("tong_xiaopeng", "hj4_19350306_canku_hongzha", "亲历并著《残酷的轰炸》（第58篇）", "src_hongjun_changzhengji"),
        ("tong_xiaopeng", "hj4_19350725_boluozi", "亲历并著《波罗子》（第96篇）", "src_hongjun_changzhengji"),
        (non_ascii_ids["xu_mengqiu"], "hj4_19350228_zunyi_day", "主编《红军长征记》并著《一天——再占遵义城》（第54篇）", "src_hongjun_changzhengji"),
        (non_ascii_ids["xu_mengqiu"], "hj4_19350815_songpan_nw", "亲历并著《松潘的西北》（第99篇）", "src_hongjun_changzhengji"),
        (non_ascii_ids["xu_mengqiu"], "hjdet_27", "亲历并著《大雨滂沱中——两河口的欢迎会》（第89篇）", "src_hongjun_changzhengji"),
        (non_ascii_ids["xu_mengqiu"], "hjdet_23", "亲历并著《吴起镇打骑兵》（第109篇）", "src_hongjun_changzhengji"),
        ("zhou_shidi", "hjdet_09", "亲历并著《吃辣椒》（第94篇）", "src_hongjun_changzhengji"),
        ("zhou_shidi", "hj4_19350831_fulubing", "赴包座开展俘虏工作并著《俘虏兵的一束话》（第105篇）", "src_hongjun_changzhengji"),
        ("shu_xia", "hj4_19350305_xiaomaowu", "目击并著《小茅屋——贵州西北边境的贫民生活写真》（第57篇）", "src_hongjun_changzhengji"),
        ("shu_xia", "rf_19350429_jiaopingdu_start", "亲历并著《渡金沙江》（第73篇）", "src_hongjun_changzhengji"),
        ("shu_xia", "hjdet_14", "亲历并著《通过草地》（第102篇）", "src_hongjun_changzhengji"),
        ("bi_wu", "hj4_19341016_chufa_qian", "随军长征并著《出发前》（第9篇）", "src_hongjun_changzhengji"),
        ("bi_wu", "hj4_19350825_maoergai_banyou", "亲历并著《从毛儿盖到班佑》（第101篇）", "src_hongjun_changzhengji"),
        ("bi_wu", "hjdet_15", "任休养连总支书记并著《长征中的女英雄》（第116篇）", "src_hongjun_changzhengji"),
        (non_ascii_ids["mo_wenhua"], "hj4_19341130_zhongwei", "亲历并著《在重围中》（第37篇）", "src_hongjun_changzhengji"),
        (non_ascii_ids["mo_wenhua"], "hj4_19350429_wuyi_jinsha", "随干部团强渡金沙江并著《“五一”的前后》（第70篇）", "src_hongjun_changzhengji"),
        (non_ascii_ids["xie_fumin"], "hjdet_01", "亲历并著《经贵州苗山》（第42篇）", "src_hongjun_changzhengji"),
        (non_ascii_ids["xie_fumin"], "hjdet_14", "亲历并著《草地行军六天缩影》（第103篇）", "src_hongjun_changzhengji"),
        (non_ascii_ids["xie_fumin"], "hj4_19351022_dao_qinjia", "亲历并著《到了亲家》（第110篇）", "src_hongjun_changzhengji"),
        ("tan_zheng", "hj3_19350225_tan_zheng_first_battle", "亲历并著《突围的第一仗》（第15篇）", "src_hongjun_changzhengji"),
        ("tan_zheng", "hj4_19341201_last_blockade", "亲历并著《最后的一道封锁线》（第38篇）", "src_hongjun_changzhengji"),
        ("tan_zheng", "hj4_19350120_chishui_advance", "亲历并著《向赤水前进》（第49篇）", "src_hongjun_changzhengji"),
        ("he_zhaochang", "hj2_19350302_zunyi_city_life", "亲历并著《遵义日记》（第47篇）", "src_hongjun_changzhengji"),
        ("he_zhaochang", "hj4_19350823_jueshi_yitian", "过草地亲历并著《绝食的一天》（第100篇）", "src_hongjun_changzhengji"),
        ("xu_sidai", "hj4_19350331_daoliushui", "率教导营四个连阻击并著《倒流水四个连控制敌人三个师》（第60篇）", "src_hongjun_changzhengji"),
        ("xu_sidai", "hj4_19350410_dingfan", "率部突袭并著《夺取定番城》（第62篇）", "src_hongjun_changzhengji"),
        ("li_xuesan", "hj4_19341129_xiangshui_rear", "亲历并著《紧急渡湘水》（第36篇）", "src_hongjun_changzhengji"),
        ("li_xuesan", "hj4_19351028_red5_rearguard", "亲历并著《艰苦奋斗的五军团》（第113篇）", "src_hongjun_changzhengji"),
        ("wang_ping_san11", "hj4_19341106_yizhang", "任红十一团政委并著《占领宜章城》（第27篇，原署斯顿）", "src_hongjun_changzhengji"),
        ("shu_tong", "hj4_19350228_zunyi_pursuit", "亲历并著《遵义追击》（第53篇）", "src_hongjun_changzhengji"),
        ("shu_tong", "hj4_19350710_luhua_liang", "亲历并著《芦花运粮》（第91篇）", "src_hongjun_changzhengji"),
        ("deng_fa", "ev_prop_19361228_dengfa", "以“方林”笔名撰《雪山草地行军记》在巴黎连载并收入全书", "src_hongjun_changzhengji"),
        ("deng_fa", "hj4_19351025_gansu_shaanxi", "亲历并著《从甘肃到陕西》（第8篇）", "src_hongjun_changzhengji"),
        ("deng_fa", "rf_19350115_zunyi_meeting", "参加遵义会议", "src_changzhengji_people"),
        ("huang_zhen", "hj4_19350615_huizhan_baoxing", "亲历并著《回占宝兴》（第88篇）", "src_hongjun_changzhengji"),
        ("huang_zhen", "hj4_19351028_red5_rearguard", "亲历并著《长征前的红五军团》（第112篇）", "src_hongjun_changzhengji"),
        ("liu_zhong", "hjdet_20", "任红一军团侦察科长并著《泸沽到大渡河》（第79篇）", "src_hongjun_changzhengji"),
        ("zhou_biquan", "hj4_19341129_xiangshui_rear", "任红十三师政治部主任随全军总后卫断后", "src_hongjun_changzhengji"),
        ("zhou_biquan", "hj4_19351028_red5_rearguard", "亲历并著《长征中走在最后头的一个师》（第111篇）", "src_hongjun_changzhengji"),
        ("liao_zhigao", "hj4_19350521_yizugeming", "冕宁参军并著《一个忠实的革命“倮倮”》（第82篇）", "src_hongjun_changzhengji"),
        (non_ascii_ids["zhang_yunyi"], "hj3_1927_niedu_guerrilla", "亲历并著《聂都游击队的记述》（第21篇）", "src_hongjun_changzhengji"),
        ("zhang_zhen", "hj4_19341231_wengan_battle", "任红十团三营营长参战并著《瓮安之役》（第46篇）", "src_hongjun_changzhengji"),
        ("li_yimang", "hj3_193504_liyi_mang_dadu", "亲历并著三万字日记体长篇《从金沙江到大渡河》（第72篇）", "src_hongjun_changzhengji"),
        ("chang_zhong", "hj3_193503_wo_shi_lianluo", "亲历并著《我失联络》（第48篇）", "src_hongjun_changzhengji"),
        ("yang_chengwu", "hj4_19350917_lazikou_yang", "任红四团政委率部攻克腊子口并著《突破天险的腊子口》（第106篇）", "src_hongjun_changzhengji"),
        ("yang_chengwu", "rf_19350529_luding_bridge", "率红四团一昼夜急行军二百四十里飞夺泸定桥", "src_changzhengji_people"),
        ("yang_chengwu", "czj_19350102_wujiang_jiangjiehe", "率红四团强渡乌江江界河渡口", "src_changzhengji_people"),
        ("swimmers_and_punters", "hj4_19350102_wujiang_heroes", "《乌江战斗中的英雄》（第130篇）集体署名抢渡英雄群体", "src_hongjun_changzhengji"),
        ("xiong_bo_tao", "hjdet_28", "亲历并著《茅台酒》（第59篇）", "src_hongjun_changzhengji"),
        ("wang_huiqiu", "hj4_19350725_boluozi", "亲历并著《波罗子》（第97篇）", "src_hongjun_changzhengji"),
        ("geng_biao", "hj4_19341116_linwu_daozhou", "任红一师参谋长率部急行并著《由临武至道州》（第30篇）", "src_hongjun_changzhengji"),
        ("jia_tuofu", "hj4_19350718_wabuliangzi", "参加芦花筹粮委并著《瓦布梁子》（第95篇）", "src_hongjun_changzhengji"),
        ("chen_ming", "hj4_19341207_fanghuozhe", "随干部团过苗山并著《放火者》（第41篇）", "src_hongjun_changzhengji"),
        ("huang_kegong", "hj4_19350225_tongzi_zunyi", "参加娄山关战役并著《由桐梓到遵义》（第55篇）", "src_hongjun_changzhengji"),
    ]

    pe_path = ROOT / "data_edit/person_events.csv"
    with pe_path.open("r", encoding="utf-8-sig", newline="") as f:
        per = csv.DictReader(f)
        pefields = list(per.fieldnames or [])
        pes = list(per)

    active_evs = {e["id"] for e in events if str(e.get("enabled", "")).upper() == "TRUE"}
    active_pids = {p["id"] for p in persons if str(p.get("enabled", "TRUE")).upper() == "TRUE"}
    existing_pairs = {
        (r["personId"], r["eventId"])
        for r in pes
        if str(r.get("enabled", "")).upper() == "TRUE"
    }
    max_sort = max((int(r.get("sort") or 0) for r in pes if str(r.get("sort") or "").isdigit()), default=9200)

    added_links = 0
    for pid, eid, role, sids in new_links:
        if pid not in active_pids:
            raise RuntimeError(f"Unknown personId: {pid}")
        if eid not in active_evs:
            raise RuntimeError(f"Unknown or disabled eventId: {eid}")
        if (pid, eid) in existing_pairs:
            continue
        max_sort += 1
        row = {col: "" for col in pefields}
        row["enabled"] = "TRUE"
        row["personId"] = pid
        row["eventId"] = eid
        row["role"] = role
        row["note"] = "P2-2补全《红军长征记》作者与亲历事件关联"
        row["sourceIds"] = sids
        row["sort"] = str(max_sort)
        pes.append(row)
        existing_pairs.add((pid, eid))
        added_links += 1

    with pe_path.open("w", encoding="utf-8-sig", newline="") as f:
        pew = csv.DictWriter(f, fieldnames=pefields)
        pew.writeheader()
        pew.writerows(pes)

    # Verify zero-event active persons count
    pe_counts = Counter(
        r["personId"] for r in pes
        if str(r.get("enabled", "")).upper() == "TRUE" and r["eventId"] in active_evs
    )
    zero_after = [pid for pid in sorted(active_pids) if pe_counts[pid] == 0]

    print(f"Added firsthand《红军长征记》events: {added_evs}")
    print(f"Added author-event links         : {added_links}")
    print(f"Zero-event active persons after  : {len(zero_after)} {zero_after}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
