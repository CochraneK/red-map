# -*- coding: utf-8 -*-
"""
从 references.json 生成人可读的学术规范参考书目（REFERENCES.md，可对外发布）。

按「证据强度分层」排序：
  A. 专著与原始文献（最核心的「参考了哪几本书」）
  B. 权威机构网页（人民网/新华网/军网/党史网）
  C. 数据库与其他
每条按 GB/T 7714-2015 格式著录：
  作者. 书名[M/EB/OL]. 出版地: 出版者, 年份. 引用位置. 访问日期. URL.
"""
import json
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
SRC = BASE / "data" / "references.json"
OUT = BASE / "REFERENCES.md"

HEAD = """# 参考书目与数据来源说明

> 本文档记录"红军长征星火路线"数字博物馆所参考的全部文献与资料来源。
> 项目以 **来源分层** 为原则：不同来源承载不同性质的信息，不做混淆。
> 每条史实条目（事件/人物）都可反查到具体来源与引用位置；项目数据库中
> `sources.csv` / `references.json` 保存机器可读版本，此处为人可读汇总。
>
> 访问/抓取日期统一为 2026-11-23。

---

## 来源分层原则

| 层级 | certainty | 来源性质 | 用途 |
|------|-----------|----------|------|
| 权威史实 | `high` | 中共中央党史和文献研究院、军事科学院、人民网党史频道、中国军网等权威出版物与官网 | 可作为史实依据直接展示 |
| 一手见闻 | `medium` | 亲历者回忆录（《红军长征记》135篇、斯诺《红星照耀中国》） | 补充细节层（数字、对话、场景），与权威战史可能出入 |
| 线索待证 | `low` | 游戏文本抽取 | 仅作候选线索，**不作为史实**，需独立权威来源佐证 |

**重要**：公版原著 ≠ 公版译本。斯诺原著 2023 年进入公有领域，但董乐山译本仍受保护到 2049 年；
《红军长征记》底本（1937/1942）已公有，刘统整理注释本仍受保护。项目只提取事实要素并注明出处，
**不转载任何受保护文本到前端**。

---
"""

SECTION_A = """## A. 专著与原始文献（核心参考）

以下是最重要的"参考了哪几本书"。项目对这类来源的引用，均标注到**具体篇名/章节/位置**。
"""

SECTION_B = """## B. 权威机构网页

以下来源均为政府机构、权威媒体官网发布的可访问文章（含人民网党史频道、新华网、
中国军网、共产党员网、中共中央党史和文献研究院官网等），按使用频率降序。
"""

SECTION_C = """## C. 候选线索来源

游戏文本**不是史料**，仅作为候选线索来源（certainty=low），独立核实后才升级。
"""

FOOTER = """
---

## 数据文件

| 文件 | 说明 |
|---|---|
| `data_edit/sources.csv` | 111 条来源完整著录（含 author/year/mediaType/citedDetail/usageCount） |
| `data/references.json` | 机器可读版参考书目 |
| `data/long_march_events.json` | 617 条事件，每条 `sourceIds` 可反查上述来源 |

## 引用位置统计（摘选）

| 来源 | 被引用次数 | 具体位置 |
|---|---|---|
"""


def fmt_gbt(r: dict) -> str:
    """生成一条 GB/T 7714 风格的引用串。"""
    parts = []
    author = (r.get("author") or "").strip()
    title = (r.get("title") or "").strip()
    year = (r.get("year") or "").strip()
    publisher = (r.get("publisher") or "").strip()
    edition = (r.get("edition") or "").strip()
    cited = (r.get("citedDetail") or "").strip()
    url = (r.get("url") or "").strip()
    media = (r.get("mediaType") or "").strip()
    acc = (r.get("accessed") or "").strip()

    if author:
        parts.append(author)
    if title:
        mt = {"专著": "[M]", "网页": "[EB/OL]", "数据库": "[DB/OL]", "档案": "[A]"}.get(media, "")
        parts.append(f"{title}{mt}" if mt else title)
    if publisher:
        parts.append(publisher)
    if year:
        parts.append(year)
    if edition:
        parts.append(f"({edition})")
    if cited:
        parts.append(f"引用位置：{cited}")
    if url:
        parts.append(url)
    if acc:
        parts.append(f"访问日期：{acc}")
    return ". ".join(parts) + "."


def main():
    data = json.loads(SRC.read_text(encoding="utf-8"))
    refs = data["references"]

    books = [r for r in refs if (r.get("mediaType") in ("专著", "档案"))]
    webs = [r for r in refs if r.get("mediaType") == "网页"]
    dbase = [r for r in refs if r.get("mediaType") == "数据库"]

    def usage(r):
        try:
            return -int(r.get("usageCount") or 0)
        except ValueError:
            return 0

    webs.sort(key=usage)
    books.sort(key=usage)

    lines = [HEAD]

    lines.append(SECTION_A)
    if books:
        lines.append("")
        lines.append("| # | 引用格式（GB/T 7714 风格） | 被引用次数 |")
        lines.append("|---|---|---|")
        for i, r in enumerate(books, 1):
            lines.append(f"| {i} | {fmt_gbt(r)} | {r.get('usageCount',0)} |")
    else:
        lines.append("（无）")

    lines.append("")
    lines.append(SECTION_B)
    lines.append("")
    lines.append("| # | 来源 | 年份 | 引用次数 |")
    lines.append("|---|---|---|---|")
    for i, r in enumerate(webs, 1):
        title = (r.get("title") or "")[:48]
        org = (r.get("author") or "")[:16]
        year = (r.get("year") or "—")
        cnt = r.get("usageCount", 0)
        lines.append(f"| {i} | [{title}]({r.get('url','')}) — {org} | {year} | {cnt} |")

    lines.append("")
    lines.append(SECTION_C)
    lines.append("")
    for r in dbase:
        lines.append(f"- **{r.get('title','')}** — {r.get('author','')}。{r.get('note','')}")
        lines.append(f"  - 项目纪律：此来源的事件 certainty=low，仅作候选线索。")

    # 引用位置统计
    lines.append(FOOTER)
    top = sorted(refs, key=usage)[:14]
    for r in top:
        cited = (r.get("citedDetail") or "—")[:72]
        lines.append(f"| {r.get('title','')[:30]} | {r.get('usageCount',0)} | {cited} |")

    lines.append("")
    lines.append(f"*生成日期：2026-11-23；共 {len(refs)} 条来源，其中专著 {len(books)}、网页 {len(webs)}、数据库 {len(dbase)}。*")
    lines.append("")

    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"已生成 {OUT}（{len(lines)} 行）")


if __name__ == "__main__":
    main()
