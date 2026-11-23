# -*- coding: utf-8 -*-
"""
把 sources.csv 的 6 字段扩展为学术规范著录字段，并生成参考文献总表。

新增字段（不破坏现有字段，只在后方追加）：
  author       责任者（个人或机构）
  year         出版/发布年（4 位）
  pubDate      完整日期（YYYY-MM-DD，能确定才填）
  mediaType    载体类型：专著 / 期刊 / 网页 / 档案 / 数据库
  citedDetail  本书引用到的具体位置（篇名/章节/页码）
  accessed     访问日期（网页类必填，本项目统一为抓取日）
  edition      版次（专著用）

纪律：
  - 只从已有信息推断，**不臆造**作者与年份；推不出的留空
  - 机构来源的责任者用机构名（人民网/新华社/共产党员网…），不硬套个人
  - 生成 REFERENCES.md 时，缺项如实标注「（待补）」

输出：
  data_edit/sources.csv（扩展字段）
  data/references.json（结构化参考书目）
  REFERENCES.md（人可读的学术规范参考书目，可对外发布）
"""
import csv
import json
import re
from pathlib import Path
from urllib.parse import urlparse

BASE = Path(__file__).resolve().parents[1]
SRC = BASE / "data_edit" / "sources.csv"
OUT_JSON = BASE / "data" / "references.json"
OUT_MD = BASE / "REFERENCES.md"

ACCESSED = "2026-11-23"

# 域名 -> 责任机构（权威机构，非个人）
DOMAIN_ORG = {
    "cpc.people.com.cn": "中国共产党新闻网",
    "dangshi.people.com.cn": "人民网·党史频道",
    "media.people.com.cn": "人民网",
    "www.people.com.cn": "人民网",
    "www.xinhuanet.com": "新华网",
    "www.81.cn": "中国军网",
    "photo.81.cn": "中国军网",
    "www.12371.cn": "共产党员网",
    "www.cppcc.gov.cn": "中国政协网",
    "www.dswxyjy.org.cn": "中共中央党史和文献研究院",
    "www.spp.gov.cn": "最高人民检察院（转载新华社）",
    "www.mva.gov.cn": "退役军人事务部",
    "www.gov.cn": "中国政府网",
}

# 书名类来源（专著/文献集）-> (作者, 年份, 出版社, 版次)
BOOK_META = {
    "src_hongjun_changzhengji": (
        "红军长征记（集体创作，1936年征稿，丁玲、徐特立、成仿吾等编辑）",
        "1937（编定）/ 1942（延安印行）",
        "延安：总政治部（内部印行）；今据刘统整理注释本，生活·读书·新知三联书店",
        "1942年延安内部印行本",
    ),
    "src_changzhengji_people": (
        "曲爱国、张从田",
        "2016",
        "北京：华夏出版社（人民网党史频道授权连载）",
        "授权连载版",
    ),
    "src_snow_redstar": (
        "斯诺（Edgar Snow）著",
        "1937（英文初版）/ 中文译本",
        "伦敦：Gollancz（英文）；中文版据公开电子版",
        "",
    ),
    "src_cpc_century": (
        "中共中央党史和文献研究院",
        "2021",
        "北京：人民出版社（《人民日报》2021年6月28-30日分三次刊发）",
        "",
    ),
    "src_100years_cpc": (
        "中共中央党史和文献研究院",
        "2021",
        "《中国共产党一百年大事记》，人民出版社",
        "",
    ),
    "src_steam_longmarch_1934_1936": (
        "游戏《长征 1934-1936》文本",
        "—",
        "商业游戏作品（**候选线索来源，非史料**）",
        "",
    ),
}


def guess_year(url: str) -> str:
    """只匹配 URL 中「以 / 或 - 分隔的独立 4 位年份段」（20xx），
    避免误把文章 id（如 js_208592/2076572658）里的数字当年份。"""
    if not url:
        return ""
    # 典型模式：/2021/0628/ 、/2021-06/ 、/2021/0413/ 等
    m = re.search(r"[/-](20[0-2]\d)[/-]", url)
    if m:
        return m.group(1)
    m = re.search(r"/(20[0-2]\d)(\d{2})(\d{2})?/", url)
    if m and 1 <= int(m.group(2)) <= 12:
        return m.group(1)
    return ""


def guess_pubdate(url: str) -> str:
    m = re.search(r"/(20\d{2})(\d{2})(\d{2})/", url or "")
    if m:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    m = re.search(r"/(20\d{2})(\d{2})/", url or "")
    if m:
        return f"{m.group(1)}-{m.group(2)}"
    return ""


def main():
    with open(SRC, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    old_fields = list(rows[0].keys())

    NEW = ["author", "year", "pubDate", "mediaType", "citedDetail", "accessed", "edition"]
    fields = old_fields + [x for x in NEW if x not in old_fields]

    for r in rows:
        sid = r["id"]
        url = (r.get("url") or "").strip()
        dom = urlparse(url).netloc

        # ---- 书名类：用 BOOK_META ----
        if sid in BOOK_META:
            author, year, pub, edition = BOOK_META[sid]
            r["author"] = author
            r["year"] = year[:4] if year[:4].isdigit() else year
            r["mediaType"] = "专著" if "游戏" not in pub else "数据库"
            r["edition"] = edition
            r.setdefault("citedDetail", "")
            if "游戏" in pub:
                r["sourceType"] = "game_text"
            else:
                r["sourceType"] = "authoritative"
        else:
            # ---- 网页类 ----
            r["author"] = DOMAIN_ORG.get(dom, "")
            r["year"] = guess_year(url)
            r["pubDate"] = guess_pubdate(url)
            r["mediaType"] = "网页"
            r.setdefault("edition", "")

        r["accessed"] = ACCESSED if url.startswith("http") else ""

        # ---- sourceType 兜底 ----
        if not (r.get("sourceType") or "").strip():
            r["sourceType"] = "authoritative"

    with open(SRC, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    print(f"已扩展 sources.csv 字段：{old_fields} → {fields}")

    # ---- 生成 references.json ----
    refs = []
    for r in rows:
        refs.append({
            "id": r["id"],
            "author": r.get("author") or "",
            "title": r.get("title") or "",
            "publisher": r.get("publisher") or "",
            "year": r.get("year") or "",
            "pubDate": r.get("pubDate") or "",
            "edition": r.get("edition") or "",
            "mediaType": r.get("mediaType") or "",
            "url": r.get("url") or "",
            "accessed": r.get("accessed") or "",
            "sourceType": r.get("sourceType") or "",
            "note": r.get("note") or "",
        })
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps({"accessedDate": ACCESSED, "count": len(refs), "references": refs},
                                   ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"已生成 {OUT_JSON}（{len(refs)} 条）")


if __name__ == "__main__":
    main()
