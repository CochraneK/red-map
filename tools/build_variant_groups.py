# -*- coding: utf-8 -*-
"""
构建「同一事件的不同来源版本」关联组。

背景：项目里同一史实常常有多条来源不同的记录，例如
  - 泸定桥：军科院口径「22 勇士」(high) vs 斯诺口径「30 名志愿战士」(medium)
  - 突破第一道封锁线：长征记细节版(high) vs 概略版(medium)
  - 遵义会议：细节版(high) vs 概略版(medium) vs 游戏线索(low)
这些并存是有意保留的「源透明度」，但观众需要一个入口看到「同一件事的不同说法」。

算法（保守，宁可漏不可错）：
  1. 同一天 + 同一 forceId（同一部队线）
  2. 标题去掉泛化后缀后，二字词组 Jaccard 相似度 >= 阈值
  3. 至少有一条非 low（low 只是候选线索，不构成"口径差异"）
  4. 组内 certainty 种类 > 1 才算口径差异组

输出：data/variant_groups.json
  [{ "key": "1935-05-29|luding", "date": "1935-05-29",
     "title": "泸定桥夺桥", "variants": [{eventId, certainty, sourceIds, label, summary}] }]
"""
import json
import re
from collections import defaultdict
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
DATA = BASE / "data" / "long_march_events.json"
OUT = BASE / "data" / "variant_groups.json"

# 泛化词：剥离后只留事件专名核心
GENERIC = re.compile(
    r"(出发|开始|会议|召开|发布|占领|攻击|进攻|战斗|战役|成立|会师|成立|部队|红军|"
    r"中共中央|军委|军团|纵队|方面军|军委|决定|通过|纪念|活动|到达|抵达|进入|举行|"
    r"胜利|胜利会师|的|了|在|与|和|及|等|共|约)"
)

STOP_CHARS = set("的了在与和及等共约年月日")

# 数字（含中文数字）——口径差异最常体现在数字上
NUM = re.compile(r"[0-9]+|[一二三四五六七八九十百千万]+")


def core_tokens(title: str) -> set:
    """提取标题核心二字词组（去掉泛化词与单字）。"""
    t = re.sub(r"[（(].*?[）)]", "", title or "")
    t = GENERIC.sub("", t)
    t = re.sub(r"[\s·、,，。;；:：!！?？\"'“”‘’]", "", t)
    chars = [c for c in t if c not in STOP_CHARS]
    if len(chars) < 2:
        return set()
    grams = {chars[i] + chars[i + 1] for i in range(len(chars) - 1)}
    return grams


def numbers_in(text: str) -> set:
    """抽取数字集合（含中文数字），用于口径对比。"""
    return {n for n in NUM.findall(text or "") if len(n) >= 1 and n not in {"一", "二"}} or set()


def jaccard(a: set, b: set) -> float:
    if not a or not b:
        return 0.0
    inter = len(a & b)
    return inter / len(a | b)


def similarity(a: dict, b: dict) -> float:
    """标题词组相似度 + 描述词组相似度 的加权，再给地点/类型 bonus。"""
    ta, tb = core_tokens(a.get("title")), core_tokens(b.get("title"))
    ts = jaccard(ta, tb)
    da, db = core_tokens(a.get("description")), core_tokens(b.get("description"))
    ds = jaccard(da, db)
    score = ts * 0.55 + ds * 0.45
    # 同地点 bonus
    la = (a.get("location") or {}).get("name") or a.get("locationName") or ""
    lb = (b.get("location") or {}).get("name") or b.get("locationName") or ""
    if la and lb and la == lb:
        score += 0.12
    # 同类型 bonus
    if a.get("type") and a.get("type") == b.get("type"):
        score += 0.04
    # 数字一致说明是同一事件的不同计数口径
    na, nb = numbers_in(a.get("title")), numbers_in(b.get("title"))
    if na and nb and (na & nb):
        score += 0.06
    # 专名地名强信号：两条描述里出现的同一批"战役/渡口/关隘"专名
    key_a = proper_places(a.get("title") + " " + (a.get("description") or ""))
    key_b = proper_places(b.get("title") + " " + (b.get("description") or ""))
    if key_a and key_b:
        shared = key_a & key_b
        if len(shared) >= 2:
            score += 0.30
        elif len(shared) == 1:
            score += 0.20
    return score


# 长征专名（渡口/关隘/战役/地名），用于识别"同一地点同一事件"
PROPER_PLACE = re.compile(
    r"[一-龥]{2,4}(?:桥|渡|关|口|山|岭|河|江|寨|堡|城|镇|村|铺|寺|庙|梁|坡|沟|)"
    r"|[一-龥]{2,4}战役|[一-龥]{2,4}会战"
)


def proper_places(text: str) -> set:
    """抽取文本中的专名地点/战役名。"""
    out = set()
    for m in PROPER_PLACE.finditer(text or ""):
        w = m.group(0)
        if len(w) >= 3 and w not in {"红军", "国民", "国民革命"}:
            out.add(w)
    return out


def label_for(ev: dict, source_titles: dict) -> str:
    """给变体一个可读的来源标签（取最具代表性的一个来源）。"""
    srcs = ev.get("sourceIds") or []
    srcs = srcs if isinstance(srcs, list) else [s for s in str(srcs).split(";") if s]
    cert = ev.get("certainty")
    # 优先级：权威机构 > 经典文献 > 其他
    PRIORITY = [
        ("src_changzhengji_people", "军事科学院《长征记》"),
        ("src_snow_redstar", "斯诺《红星照耀中国》"),
        ("src_100years_cpc", "《一百年大事记》"),
        ("src_cpc_century", "《一百年大事记》"),
        ("src_prop_cpc_chuanbo", "人民网党史频道"),
    ]
    name = ""
    for sid, nice in PRIORITY:
        if sid in srcs:
            name = nice
            break
    if not name:
        steam = [s for s in srcs if s.startswith("src_steam")]
        if steam:
            name = "游戏文本线索"
        else:
            for s in srcs:
                if s in source_titles:
                    name = source_titles[s][:16]
                    break
            if not name:
                name = srcs[0].replace("src_", "") if srcs else "项目数据"
    certname = {"high": "权威史实", "medium": "一手见闻", "low": "线索待证"}.get(cert, cert)
    return f"{certname}·{name}"


def build(src: Path = None, out_path: Path = None):
    data = json.loads((src or DATA).read_text(encoding="utf-8"))
    events = data["events"]
    source_titles = {s.get("id"): (s.get("title") or "") for s in data.get("sources", [])}

    # 只保留有 location 与日期的
    buckets = defaultdict(list)
    for e in events:
        d = e.get("date") or ""
        f = e.get("forceId") or ""
        if not d or not f:
            continue
        buckets[(d, f)].append(e)

    groups = []
    seen_pairs = set()

    for (date, force), lst in buckets.items():
        if len(lst) < 2:
            continue
        # 逐对比较
        for i in range(len(lst)):
            for j in range(i + 1, len(lst)):
                a, b = lst[i], lst[j]
                pair = tuple(sorted([a["id"], b["id"]]))
                if pair in seen_pairs:
                    continue
                # 至少一条非 low
                if a.get("certainty") == "low" and b.get("certainty") == "low":
                    continue
                # 同源（同一来源）的条目不算口径差异 —— 那是重复记录，应由去重流程处理
                src_a = set(a.get("sourceIds") or [])
                src_b = set(b.get("sourceIds") or [])
                if src_a and src_b and src_a == src_b:
                    continue
                ta, tb = core_tokens(a.get("title")), core_tokens(b.get("title"))
                sim = similarity(a, b)
                if sim < 0.30:
                    continue
                seen_pairs.add(pair)
                # 成组
                grp = groups[-1] if (groups and groups[-1]["date"] == date and
                                     any(v["eventId"] in pair for v in groups[-1]["variants"])) else None
                if grp is None:
                    grp = {"key": f"{date}|{force}|{len(groups)}", "date": date,
                           "forceId": force, "title": a.get("title", ""),
                           "variants": []}
                    groups.append(grp)
                for e in (a, b):
                    if not any(v["eventId"] == e["id"] for v in grp["variants"]):
                        grp["variants"].append({
                            "eventId": e["id"],
                            "certainty": e.get("certainty"),
                            "label": label_for(e, source_titles),
                            "title": e.get("title", ""),
                            "summary": (e.get("description") or "")[:220],
                            "sourceIds": e.get("sourceIds") or [],
                        })

    # 只保留确有口径差异（certainty 种类 > 1）的组
    out = []
    for g in groups:
        certs = {v["certainty"] for v in g["variants"]}
        if len(certs) < 2:
            continue
        # 同来源去重：同一来源在组内只保留一条（避免"长征记"重复出现两次）
        seen_src = set()
        dedup = []
        for v in sorted(g["variants"], key=lambda v: {"high": 0, "medium": 1, "low": 2}.get(v["certainty"], 3)):
            sig = (v["label"], v["certainty"])
            if sig in seen_src:
                continue
            seen_src.add(sig)
            dedup.append(v)
        g["variants"] = dedup
        certs = {v["certainty"] for v in g["variants"]}
        if len(certs) < 2:
            continue
        g["certaintyKinds"] = sorted(certs)
        g["title"] = g["variants"][0]["title"]
        out.append(g)

    out.sort(key=lambda g: (g["date"], g["title"]))
    target = Path(out_path) if out_path else OUT
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps({"groups": out}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"口径差异组 {len(out)} 个 -> {target}")
    for g in out[:12]:
        print(f"  {g['date']} | {len(g['variants'])}种说法 | {g['title'][:34]}")
        for v in g["variants"]:
            print(f"      [{v['certainty']}] {v['label']}")


if __name__ == "__main__":
    build()
