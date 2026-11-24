# -*- coding: utf-8 -*-
"""
从《长征大事记》（《红军长征记》第132篇，陆定一撰）逐日编年中提取结构化条目。

依据：
- 文本层完整（超星抓取），原文格式为：
      一九三四年
      十月份
      十二日
      红一方面军改编为野战军，开始向西南移动。
      二十一日 晴
      一军团第二师先头占领金鸡，主力在大竹、双芫、金鸡地域，当晚向新田前进。
      ...
      三军团先头占领百室，固守堡垒之铲匪第二中队百余人，全部被我消灭。

处理：
  1. 识别「年」「月份」「日」三层标记，日期用中文数字转阿拉伯
  2. 每个日期下的段落按「行首部队关键词」切分为独立条目
  3. 提取地点（战役/地名模式）、人物、部队
  4. 跳过天气标记（晴/阴/雨/雪）与纯议论段

输出：research_private/sourced_research/21_长征大事记逐日条目.json
"""
import json
import re
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
SRC = BASE / "research_private" / "ebooks" / "hongjun_changzhengji" / "1.132_长征大事记.txt"
OUT = BASE / "research_private" / "sourced_research" / "21_长征大事记逐日条目.json"

CN_NUM = {"零": 0, "一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7,
          "八": 8, "九": 9, "十": 10, "廿": 20, "卅": 30}
CN_MONTH = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7,
            "八": 8, "九": 9, "十": 10, "冬": 11, "腊": 12}

WEATHER = {"晴", "阴", "雨", "雪", "风", "雾", "霜", "雷"}

# 部队标志（行首出现的即视为该条属于此部队）
FORCE_PAT = [
    (r"^(红?[一二三四五六七八九]?军团)", "red_first"),
    (r"^(红?二?十?五?军)", "red_25th"),
    (r"^(红?四?方面军)", "red_fourth"),
    (r"^(红?二?方面军)", "red_second"),
    (r"^(军委)", "red_first"),
    (r"^(军委纵队|军委第二纵队|军委二纵队)", "red_first"),
    (r"^(总部|野战军司令部|党中央政治局|中共中央)", "red_first"),
    (r"^(红?九军团)", "red_first"),
    (r"^(红?六军团)", "red_second"),
    (r"^(红?七军团)", "red_first"),
    (r"^(红?十军团)", "red_first"),
    (r"^(红?三?十?二?军|红?二十六?军)", "red_25th"),
    (r"^(红?二?十?八?军)", "red_25th"),
]

# 地点抽取：用「已知长征地名」白名单，避免把动词短语当地名
KNOWN_PLACES = [
    "金鸡", "新田", "固陂", "韩坊", "百室", "太平新坡", "王母渡", "赖圩",
    "龙布圩", "燕湾岗", "龙尾口", "仁风", "荷头", "大竹", "双芫", "黄朱排",
    "安息圩", "铁石圩", "石材圩", "罗霄", "文明山", "排头", "茶亭", "宜章",
    "白石圩", "坪石", "麻田", "正和", "永安", "观音阁", "芦田", "水口",
    "梅溪", "道州", "唐家", "梨木坪", "平石", "紫岚关", "华家", "界首",
    "脚山铺", "光华铺", "车源", "正南", "文家", "石马", "大湾", "土城",
    "元厚", "马鬃岭", "枫香坝", "枫香溪", "羊角", "界场", "水西", "沙土",
    "桐梓", "花秋", "黑场", "石厢", "梨园坝", "江界河", "猪场", "回龙场",
    "茶山关", "袁家渡", "龙溪", "平龙", "场坝", "又州", "清水口", "瓮安",
    "老坟嘴", "蔡家湾", "余庆", "猴场", "乌江", "大塘铺", "小河圩",
    "大江圩", "九渡水", "潭塘坑", "凹头", "大坪", "大庾河", "南溪",
    "青龙江", "新溪", "大摆坑", "杨眉寺", "三江口", "石门口", "大龙山",
    "义安圩", "下坑", "石头坝", "崇义城", "稳下", "横断", "小溪", "乌径",
    "九渡", "江口", "大塘", "磨盘", "罗家", "梅关", "大余", "新城",
    "章贡", "沙洲", "赣州", "瑞金", "于都", "长汀", "会昌", "武夷",
    "长安", "铅口", "临江", "青原", "沙田", "马鞍岭", "黄田", "兴国",
    "高兴", "南坑", "上犹", "崇义", "赤水", "扎西", "威信", "水田",
    "大河滩", "镇雄", "毕节", "镇西", "黔大", "箭场", "磨沙", "石棉",
    "安顺场", "冕宁", "西昌", "会理", "大凉", "盐边", "会泽", "巧家",
    "洪溪", "会泽", "宣威", "盘县", "沾益", "曲靖", "马龙", "嵩明",
    "柯渡", "丹桂", "龙街", "洪门", "皎平渡", "元谋", "武定", "禄劝",
    "白沙驿", "大凉", "礼丰", "盐源", "藏北", "懋功", "两河口", "芦花",
    "黑水", "毛儿盖", "松潘", "腊子口", "巴西", "班佑", "包座", "巴西",
    "吴起镇", "吴起", "志丹", "靖边", "保安", "洛川", "麻洞", "直罗镇",
]
PLACE_RE = re.compile("(" + "|".join(sorted(set(KNOWN_PLACES), key=len, reverse=True)) + ")")

NAME_RE = re.compile(r"([一-龥]{2,4}(?:军|师|旅|团|纵队|政委|司令|总司令|总政治委员|政治委员|军长|师长|团长|旅长|营长|队长))")


def cn2num(s: str) -> int:
    """中文数字转阿拉伯（支持 一~九十九 的常见写法）。"""
    s = s.strip()
    if not s:
        return 0
    if s.isdigit():
        return int(s)
    total = 0
    cur = 0
    for ch in s:
        if ch not in CN_NUM:
            continue
        v = CN_NUM[ch]
        if v == 10:
            if cur == 0:
                cur = 1
            total += cur * 10
            cur = 0
        elif v == 20:
            total += 20
            cur = 0
        elif v == 30:
            total += 30
            cur = 0
        else:
            cur = v
    total += cur
    return total


def parse():
    raw = SRC.read_text(encoding="utf-8", errors="ignore")
    lines = [l.strip() for l in raw.split("\n")]
    # 去掉头部元信息（书名/来源/图片链接）与脚注块
    start = 0
    for i, l in enumerate(lines):
        if l.startswith("长征大事记"):
            start = i
            break
    lines = lines[start:]
    cut = len(lines)
    for i, l in enumerate(lines):
        if l.startswith("(1)") or l.startswith("（1）"):
            cut = i
            break
    lines = lines[:cut]

    year = None
    month = None
    day = None
    buf = []
    entries = []

    def flush(day, month, year, buf):
        if not buf:
            return
        cur_force = None
        for para in buf:
            para = para.strip()
            if not para or para in WEATHER:
                continue
            # 判断是否含部队标志（行首或段中）
            force = None
            for pat, fid in FORCE_PAT:
                if re.search(pat, para):
                    force = fid
                    break
            # 若该段不含任何部队标志，则归入当前 force（延续上文）
            if force is None:
                force = cur_force or "red_first"
            cur_force = force
            places = sorted({m.group(0) for m in PLACE_RE.finditer(para)})
            units = sorted({m.group(0) for m in NAME_RE.finditer(para)})
            if not places and not units and len(para) < 12:
                continue
            entries.append({
                "date": f"{year}{month:02d}{day:02d}" if year and month and day else None,
                "dateText": f"{year}年{month}月{day}日" if year and month and day else "",
                "forceId": force,
                "text": para,
                "places": places[:6],
                "units": units[:6],
            })

    for l in lines:
        if not l:
            continue
        # 年（含"一九三四年完"这类收尾行）
        m = re.match(r"^一九([三四五六])([三四五六])年(?:完)?$", l)
        if m:
            if day:
                flush(day, month, year, buf); buf = []
            # "一九三X年" → 193X；"一九XX年" → 19XX
            if m.group(2):
                year = 1900 + cn2num(m.group(1)) * 10 + cn2num(m.group(2))
            else:
                year = 1900 + cn2num(m.group(1))
            month = None; day = None
            continue
        # 月（支持「十一月份」「十二月份」等多字写法）
        m = re.match(r"^([一二三四五六七八九十]{1,3}|冬|腊)月份$", l)
        if m:
            if day:
                flush(day, month, year, buf); buf = []
            token = m.group(1)
            if token in ("冬", "腊"):
                month = CN_MONTH[token]
            else:
                month = cn2num(token)
            day = None
            continue
        # 日
        m = re.match(r"^([一二三四五六七八九十廿卅]{1,3})日\s*(.*)$", l)
        if m:
            if day:
                flush(day, month, year, buf); buf = []
            day = cn2num(m.group(1))
            continue
        # 正文行
        buf.append(l)

    if day:
        flush(day, month, year, buf)

    # 去重（同日同文本）
    seen = set()
    out = []
    for e in entries:
        k = (e["date"], e["text"][:40])
        if k in seen:
            continue
        seen.add(k)
        out.append(e)
    return out


def main():
    entries = parse()
    dates = sorted({e["date"] for e in entries if e["date"]})
    print(f"提取条目 {len(entries)} 条，覆盖 {len(dates)} 个日期")
    if dates:
        print(f"日期范围 {dates[0]} → {dates[-1]}")
    # 按月统计
    from collections import Counter
    mc = Counter(e["date"][:6] for e in entries if e["date"])
    print("逐月条目数:", dict(sorted(mc.items())))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"entries": entries}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"-> {OUT}")
    print("\n=== 抽样 ===")
    for e in entries[:5]:
        print(f"  {e['date']} [{e['forceId']}] {e['text'][:70]}")


if __name__ == "__main__":
    main()
