# -*- coding: utf-8 -*-
"""
从《红军长征记》署名生成人物档案。

依据：
  - manifest.json 的 byline（原刊署名，多为繁体/异体）
  - _author_map.json 的化名归一表（alias: 原刊署名→本名）
  - 各篇原文中「姓名+职务」句式，自动识别此人在长征中的职务线索

纪律：
  - 生卒年查不到一律留空（绝不臆造）
  - 已在人物库的人不重复新建，只输出补充信息
  - 原文里识别不到职务的，summary 只写"《红军长征记》署名作者"

输出：research_private/sourced_research/27_长征记作者人物.json
"""
import csv
import json
import re
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
MANIFEST = BASE / "research_private" / "ebooks" / "hongjun_changzhengji" / "manifest.json"
AMAP = BASE / "research_private" / "ebooks" / "hongjun_changzhengji" / "_author_map.json"
BOOKDIR = BASE / "research_private" / "ebooks" / "hongjun_changzhengji"
PERSONS = BASE / "data_edit" / "persons.csv"
OUT = BASE / "research_private" / "sourced_research" / "27_长征记作者人物.json"
SRC_ID = "src_hongjun_changzhengji"

# 职务 -> (personType, forceId)
ROLE_MAP = [
    ("政治委员", "政治工作", None), ("政委", "政治工作", None),
    ("总政治委员", "领导人", None), ("政治部主任", "政治工作", None),
    ("政治部", "政治工作", None),
    ("司令员", "军事指挥", None), ("总司令", "领导人", None),
    ("副司令员", "军事指挥", None),
    ("军长", "军事指挥", "red_first"), ("师长", "军事指挥", "red_first"),
    ("旅长", "军事指挥", "red_first"), ("团长", "军事指挥", "red_first"),
    ("营长", "军事指挥", "red_first"), ("连长", "军事指挥", "red_first"),
    ("指导员", "政治工作", None), ("队长", "军事指挥", None),
    ("书记", "政治工作", None),
]

# 部队线索 -> forceId
FORCE_HINT = [
    ("红二十五军", "red_25th"), ("二十五军", "red_25th"), ("二十六军", "red_25th"),
    ("红四方面军", "red_fourth"), ("四方面军", "red_fourth"),
    ("红二方面军", "red_second"), ("二方面军", "red_second"),
    ("红六军团", "red_second"), ("六军团", "red_second"),
    ("陕甘", "shaanbei_red"), ("西路军", "red_west_route"),
]


def pinyin_id(name: str) -> str:
    """用作者篇目中出现的汉字取拼音首字母近似不可靠 → 改为人工映射表 + 兜底哈希。"""
    return None


def build():
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    amap = json.loads(AMAP.read_text(encoding="utf-8"))
    alias = amap["alias"]
    counts = amap["counts"]

    # 载入各篇原文
    texts = {}
    for x in manifest:
        fp = BOOKDIR / x["file"]
        try:
            texts[x["no"]] = (x, fp.read_text(encoding="utf-8", errors="ignore"))
        except Exception:
            pass

    # 已有人物
    existing = {}
    with open(PERSONS, encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            existing[r["name"]] = r

    ROLE_RE = re.compile(
        r"([\u4e00-\u9fa5]{2,4}?)(总司令|总政治委员|政治委员|副司令员|司令员|政治部主任|政治部|指导员|"
        r"军长|师长|旅长|团长|营长|连长|队长|书记|班长)")

    # 作者姓名（含空格/异体）用于匹配"本人"
    def name_variants(real):
        v = {real, real.replace(" ", "")}
        # 从原刊署名反推本名可能的异体（逐字）
        return v

    persons = []
    updates = []
    for real, cnt in sorted(counts.items(), key=lambda x: -x[1]):
        # 该作者署名的篇目
        roles = set()
        force_hints = set()
        titles = []
        for no, (x, txt) in texts.items():
            by = (x.get("byline") or "").strip()
            realname = alias.get(by, by.replace(" ", ""))
            if realname != real:
                continue
            titles.append(x["title"])
            # 只取「本人姓名 + 职务」的模式（第一人称自述的职务）
            variants = name_variants(real)
            for m in ROLE_RE.finditer(txt):
                nm, role = m.group(1), m.group(2)
                if nm in variants or nm.replace(" ", "") in real.replace(" ", ""):
                    roles.add(role)
            for fk, fid in FORCE_HINT:
                if fk in txt:
                    force_hints.add(fid)

        role_text = "、".join(sorted(roles))[:40] if roles else ""
        ptype = "人物"
        fid = ""
        for rt, pt, f in ROLE_MAP:
            if rt in roles:
                ptype = pt
                if f:
                    fid = f
                break
        if not fid and force_hints:
            fid = sorted(force_hints)[0]

        if real in existing:
            r = existing[real]
            updates.append({
                "id": r["id"], "name": real,
                "foundRole": role_text,
                "foundForce": sorted(force_hints),
                "note": "已在库，建议补充长征时期职务与长征记署名篇目",
            })
            continue

        if role_text:
            summary = f"《红军长征记》署名作者，撰稿{len(titles)}篇；文中所记职务为{role_text}。"
        else:
            summary = f"《红军长征记》署名作者，撰稿{len(titles)}篇长征亲历记述。"
        if force_hints:
            summary += "涉及" + "、".join(sorted(force_hints)) + "方向军。"

        persons.append({
            "id": None,                     # 待人工指定
            "name": real,
            "nameEn": "",
            "birthDate": "",
            "deathDate": "",
            "hometown": "",
            "forceId": fid,
            "personType": ptype,
            "summary": summary,
            "themeTags": "长征亲历者;作者;《红军长征记》",
            "certainty": "high",
            "sourceIds": SRC_ID,
            "_titles": titles[:4],
            "_count": cnt,
        })

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"persons": persons, "existingUpdates": updates},
                               ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"新人物 {len(persons)} 位；已在库需补充 {len(updates)} 位 -> {OUT}")
    for p in persons[:8]:
        print(f"  {p['name']:8s} [{p['personType']:5s}] {p['summary'][:56]}")


if __name__ == "__main__":
    build()
