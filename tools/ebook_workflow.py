#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ebook_workflow.py — 电子书自动检索与下载工作流

原则（合规优先）：
  - 只从开放/授权源检索；明确允许下载的自动下载；不破解 DRM、不绕过付费墙。
  - 版权状态分级：public_domain / open_license / authorized / borrow_only / unknown / copyrighted
  - 仅 public_domain / open_license / authorized 自动下载；其余记录在线入口，单独列出。
  - 一切产物（下载文件 / SQLite 索引 / 报告）都落在 research_private/（git 忽略）。

源适配器：Project Gutenberg(pglaf镜像) / Standard Ebooks / Wikisource / DOAB(OAI)
          / OAPEN / Internet Archive（后两者当前网络不可达则优雅降级，仅给在线入口）

用法：
  python tools/ebook_workflow.py sources
  python tools/ebook_workflow.py search "long march china" --sources gutenberg,wikisource
  python tools/ebook_workflow.py download "china" --max 8 --formats txt,epub
  python tools/ebook_workflow.py index --search china
  python tools/ebook_workflow.py report --out research_private/ebooks/workflow/report.md
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sqlite3
import subprocess
import sys
import time
import unicodedata
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional

BASE = Path(__file__).resolve().parents[1]
WORK = BASE / "research_private" / "ebooks" / "workflow"
DB_PATH = WORK / "catalog.sqlite3"
CACHE = WORK / "cache"
DOWNLOADS = WORK / "downloads"
UA = "RedMapEbookWorkflow/1.0 (research; contact: local-user)"

# ---------------------------------------------------------------- 版权状态
DOWNLOADABLE = {"public_domain", "open_license", "authorized"}


class Rights:
    PUBLIC_DOMAIN = "public_domain"       # 公有领域
    OPEN_LICENSE = "open_license"         # 开放许可(CC/GFDL)，需署名
    AUTHORIZED = "authorized"             # 明确授权下载(OA/出版社授权)
    BORROW_ONLY = "borrow_only"           # 仅在线借阅(需登录/DRM)
    UNKNOWN = "unknown"                   # 版权状态不明
    COPYRIGHTED = "copyrighted"           # 明确受版权保护

    LABEL = {
        PUBLIC_DOMAIN: "公有领域",
        OPEN_LICENSE: "开放许可",
        AUTHORIZED: "授权下载",
        BORROW_ONLY: "仅在线借阅",
        UNKNOWN: "版权不明",
        COPYRIGHTED: "受版权保护",
    }


# ---------------------------------------------------------------- 数据模型
@dataclass
class Book:
    source: str                     # 源标识
    source_id: str                  # 源内 ID
    title: str
    author: str = ""
    year: Optional[int] = None
    language: str = ""
    isbn: str = ""
    doi: str = ""                   # 学术来源用
    rights_status: str = Rights.UNKNOWN
    rights_basis: str = ""          # 版权依据（必须写清）
    source_url: str = ""            # 书页/原始来源
    download_url: str = ""          # 直接下载链接（如有）
    format: str = ""                # epub/pdf/txt
    online_read_url: str = ""       # 在线阅读/借阅入口
    note: str = ""
    # 运行期字段（不入库）
    score: float = 0.0

    def dedup_key(self) -> str:
        """去重键：规范化标题 + 作者（忽略大小写/标点/空格）"""
        return hashlib.sha256(
            (norm_key(self.title) + "|" + norm_key(self.author)).encode("utf-8")
        ).hexdigest()[:16]


def norm_key(s: str) -> str:
    s = unicodedata.normalize("NFKD", s or "").lower()
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "", s)
    return s


def clean_title(s: str) -> str:
    s = re.sub(r"\[.*?\]|\(.*?\)", "", s or "")
    s = re.sub(r"\s+", " ", s).strip(" ,.;:-")
    return s


def clean_author(s: str) -> str:
    s = (s or "").strip()
    m = re.match(r"^(.+),\s*(.+)$", s)      # "Doe, John" -> "John Doe"
    if m:
        s = f"{m.group(2)} {m.group(1)}"
    return re.sub(r"\s+", " ", s).strip()


def guess_lang(text: str) -> str:
    if re.search(r"[\u4e00-\u9fff]", text or ""):
        return "zh"
    return "en"


# ---------------------------------------------------------------- 网络
def fetch(url: str, binary: bool = False, timeout: int = 25) -> Optional[bytes | str]:
    """统一取数：curl -k 优先（本环境 requests 走代理易 hang），requests 仅作后备。
    清掉代理环境变量，走直连（实测直连比本机代理稳定）。"""
    env = {k: v for k, v in __import__("os").environ.items()
           if k.lower() not in ("http_proxy", "https_proxy", "all_proxy")}
    try:
        r = subprocess.run(
            ["curl", "-sL", "-k", "--max-time", str(timeout), "-A", UA, url],
            capture_output=True, timeout=timeout + 5, env=env,
        )
        if r.returncode == 0 and len(r.stdout) > 200:
            return r.stdout if binary else r.stdout.decode("utf-8", errors="ignore")
    except Exception:
        pass
    try:
        import requests
        import urllib3
        urllib3.disable_warnings()
        r = requests.get(url, headers={"User-Agent": UA}, timeout=8, verify=False,
                         proxies={"http": None, "https": None})
        if r.status_code == 200 and len(r.content) > 200:
            return r.content if binary else r.text
    except Exception:
        pass
    return None


def fetch_text(url: str, timeout: int = 30) -> Optional[str]:
    """按站点编码解码：人民网/ Gutenberg 老页多为 GBK，先 UTF-8 试探再 GBK。"""
    raw = fetch(url, binary=True, timeout=timeout)
    if raw is None:
        return None
    try:
        t = raw.decode("utf-8")
        if "\ufffd" in t or "Ķ" in t[:800]:
            t = raw.decode("gbk", errors="ignore")
        return t
    except UnicodeDecodeError:
        return raw.decode("gbk", errors="ignore")


# ---------------------------------------------------------------- SQLite 索引
class BookIndex:
    def __init__(self, path: Path = DB_PATH):
        WORK.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        self._init()

    def _init(self):
        self.conn.executescript("""
        CREATE TABLE IF NOT EXISTS books (
            key TEXT PRIMARY KEY,
            title TEXT, author TEXT, year INTEGER, language TEXT, isbn TEXT, doi TEXT,
            rights_status TEXT, rights_basis TEXT,
            source TEXT, source_id TEXT, source_url TEXT,
            download_url TEXT, online_read_url TEXT,
            format TEXT, local_path TEXT, sha256 TEXT,
            downloaded_at TEXT, note TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_books_title ON books(title);
        CREATE INDEX IF NOT EXISTS idx_books_author ON books(author);
        CREATE INDEX IF NOT EXISTS idx_books_rights ON books(rights_status);
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts TEXT, action TEXT, detail TEXT
        );
        """)
        # 轻量迁移：旧库补 doi 列
        cols = {r[1] for r in self.conn.execute("PRAGMA table_info(books)")}
        if "doi" not in cols:
            self.conn.execute("ALTER TABLE books ADD COLUMN doi TEXT")
        self.conn.commit()

    def log(self, action: str, detail: str):
        self.conn.execute("INSERT INTO events(ts,action,detail) VALUES(?,?,?)",
                          (datetime.now().isoformat(timespec="seconds"), action, detail))

    def upsert_candidate(self, b: Book) -> bool:
        """登记候选；返回 True 表示新插入（未重复）。已存在则不覆盖已下载记录。"""
        key = b.dedup_key()
        exists = self.conn.execute("SELECT local_path FROM books WHERE key=?", (key,)).fetchone()
        if exists:
            return False
        self.conn.execute("""INSERT INTO books
            (key,title,author,year,language,isbn,doi,rights_status,rights_basis,
             source,source_id,source_url,download_url,online_read_url,format,note)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (key, b.title, b.author, b.year, b.language, b.isbn, b.doi,
             b.rights_status, b.rights_basis, b.source, b.source_id,
             b.source_url, b.download_url, b.online_read_url, b.format, b.note))
        self.log("candidate", f"{b.source}:{b.source_id} {b.title[:50]}")
        self.conn.commit()
        return True

    def mark_downloaded(self, b: Book, local: Path, sha: str):
        key = b.dedup_key()
        row = self.conn.execute("SELECT key FROM books WHERE key=?", (key,)).fetchone()
        if not row:
            self.upsert_candidate(b)
        self.conn.execute("""UPDATE books SET local_path=?, sha256=?, downloaded_at=?,
                             format=?, rights_status=?, rights_basis=?
                             WHERE key=?""",
            (str(local), sha, datetime.now().isoformat(timespec="seconds"),
             b.format, b.rights_status, b.rights_basis, key))
        self.log("download", f"{b.title[:50]} -> {local.name}")
        self.conn.commit()

    def rows(self, where: str = "", params: tuple = ()):
        sql = "SELECT * FROM books " + (("WHERE " + where) if where else "") + " ORDER BY title"
        return [dict(r) for r in self.conn.execute(sql, params).fetchall()]

    def stats(self):
        total = self.conn.execute("SELECT COUNT(*) FROM books").fetchone()[0]
        dl = self.conn.execute("SELECT COUNT(*) FROM books WHERE local_path IS NOT NULL").fetchone()[0]
        by = {r[0]: r[1] for r in self.conn.execute(
            "SELECT rights_status,COUNT(*) FROM books GROUP BY rights_status")}
        return {"total": total, "downloaded": dl, "by_rights": by}


# ---------------------------------------------------------------- 源适配器基类
class BaseSource:
    name = "base"
    label = "Base"
    reachable = True

    def search(self, query: str, limit: int = 20) -> list[Book]:
        return []

    def availability(self) -> str:
        return "未知"


# ---------------------------------------------------------------- Project Gutenberg
class GutenbergSource(BaseSource):
    """用 pglaf 镜像的 GUTINDEX.ALL 做检索（官方站 503 时的可靠替代）。
    版权：Gutenberg 只收录在美国进入公有领域的作品 → public_domain。"""
    name = "gutenberg"
    label = "Project Gutenberg"
    INDEX_URL = "https://gutenberg.pglaf.org/GUTINDEX.ALL"
    MIRROR = "https://gutenberg.pglaf.org/cache/epub"

    def _load_index(self) -> str:
        CACHE.mkdir(parents=True, exist_ok=True)
        fp = CACHE / "gutindex.all.txt"
        if fp.exists() and fp.stat().st_size > 100_000:
            return fp.read_text(encoding="utf-8", errors="ignore")
        txt = fetch_text(self.INDEX_URL, timeout=45)
        if txt:
            fp.write_text(txt, encoding="utf-8")
            return txt
        return ""

    def availability(self) -> str:
        txt = self._load_index()
        return "可检索+可下载（pglaf镜像）" if txt else "不可达"

    def search(self, query: str, limit: int = 20) -> list[Book]:
        txt = self._load_index()
        if not txt:
            return []
        terms = [t.lower() for t in re.split(r"\s+", query.strip()) if t]
        out: list[Book] = []
        # 条目格式: "Title, by Author    12345"
        pat = re.compile(r"^\s*(?P<title>.+?),\s*by\s+(?P<author>.+?)\s+(?P<id>\d{4,6})\s*$")
        for line in txt.splitlines():
            m = pat.match(line.rstrip("\r"))
            if not m:
                continue
            title = clean_title(m.group("title"))
            author = clean_author(m.group("author"))
            gid = m.group("id")
            hay = (title + " " + author).lower()
            if not all(any(t in w for w in re.findall(r"[a-z0-9\u4e00-\u9fff]+", hay)) for t in terms):
                continue
            score = sum(hay.count(t) for t in terms)
            out.append(Book(
                source=self.name, source_id=gid, title=title, author=author,
                rights_status=Rights.PUBLIC_DOMAIN,
                rights_basis="Project Gutenberg 收录标准：在美国属公有领域（gutenberg.org/about）",
                source_url=f"https://www.gutenberg.org/ebooks/{gid}",
                download_url=f"{self.MIRROR}/{gid}/pg{gid}.txt",
                online_read_url=f"https://www.gutenberg.org/ebooks/{gid}",
                format="txt", score=float(score),
            ))
        out.sort(key=lambda b: (-b.score, b.title))
        return out[:limit]

    def download_links(self, b: Book) -> list[tuple[str, str]]:
        gid = b.source_id
        return [
            ("txt", f"{self.MIRROR}/{gid}/pg{gid}.txt"),
            ("epub", f"{self.MIRROR}/{gid}/pg{gid}.epub"),
        ]


# ---------------------------------------------------------------- Wikisource
class WikisourceSource(BaseSource):
    """MediaWiki API 检索；维基文库只收公有领域或自由许可文本。
    保守处理：标 open_license（需署名），并提供原页面在线阅读入口。"""
    name = "wikisource"
    label = "Wikisource"
    API = "https://{lang}.wikisource.org/w/api.php"

    def availability(self) -> str:
        r = fetch_text(self.API.format(lang="en") +
                       "?action=query&meta=siteinfo&format=json", timeout=15)
        return "可检索+可抓取" if r and "siteinfo" in r else "不可达"

    def search(self, query: str, limit: int = 20) -> list[Book]:
        out: list[Book] = []
        for lang in ("zh", "en"):
            url = (self.API.format(lang=lang) +
                   "?action=query&list=search&srsearch=" +
                   re.sub(r"\s+", "%20", query) + "&srlimit=20&format=json")
            raw = fetch_text(url, timeout=20)
            if not raw:
                continue
            try:
                data = json.loads(raw)
            except Exception:
                continue
            STOP = {"the", "of", "and", "a", "in", "to", "for", "de", "la"}
            core = [t for t in re.findall(r"[a-z0-9\u4e00-\u9fff]+", query.lower())
                    if t and t not in STOP]
            for it in (data.get("query", {}).get("search", []) or []):
                title = clean_title(it.get("title", ""))
                hay = title.lower()
                # 标题须命中至少一个核心检索词（MediaWiki search 会返回正文命中但标题无关者）
                if core and not any(c in hay for c in core):
                    continue
                out.append(Book(
                    source=self.name, source_id=f"{lang}:{it.get('pageid', '')}",
                    title=title, language=lang,
                    rights_status=Rights.OPEN_LICENSE,
                    rights_basis="Wikisource 收录政策：仅公有领域或自由许可文本；使用前核对页面版权模板",
                    source_url=f"https://{lang}.wikisource.org/wiki/" +
                               title.replace(" ", "_"),
                    online_read_url=f"https://{lang}.wikisource.org/wiki/" +
                                    title.replace(" ", "_"),
                    format="txt", score=float(it.get("snippet", "").lower().count(query.lower()) + 1),
                ))
        out.sort(key=lambda b: -b.score)
        return out[:limit]

    def download_links(self, b: Book) -> list[tuple[str, str]]:
        lang, _, title = b.source_id.partition(":")
        # Special:Export 导出页面 wikitext（可再清洗为纯文本）
        return [("txt", f"https://{lang}.wikisource.org/w/index.php?title=" +
                        title.replace(" ", "_") + "&action=raw")]


# ---------------------------------------------------------------- Standard Ebooks
class StandardEbooksSource(BaseSource):
    """Standard Ebooks：明确声明所有书在美国为公有领域，精细排版。
    检索页 HTML 解析 /ebooks/<作者>/<书名>/<版本> 链接。"""
    name = "standardebooks"
    label = "Standard Ebooks"
    BASEURL = "https://standardebooks.org"

    def availability(self) -> str:
        r = fetch_text(self.BASEURL + "/ebooks", timeout=20)
        return "可检索（搜索页）" if r and "/ebooks/" in r else "不可达"

    def search(self, query: str, limit: int = 20) -> list[Book]:
        url = self.BASEURL + "/ebooks?q=" + re.sub(r"\s+", "%20", query.strip())
        html = fetch_text(url, timeout=25)
        if not html:
            return []
        links = []
        for m in re.finditer(r'href="(/ebooks/[^"#?]+)"', html):
            p = m.group(1).strip("/")
            if p.count("/") >= 2 and p not in links:      # /作者/书名/版本
                links.append(p)
        out = []
        terms = [t.lower() for t in query.split() if len(t) >= 2]
        for p in links:
            parts = p.split("/")
            author = clean_author(parts[1].replace("-", " ")) if len(parts) > 1 else ""
            title = clean_title(parts[2].replace("-", " ")) if len(parts) > 2 else parts[-1]
            hay = (title + " " + author).lower()
            score = sum(hay.count(t) for t in terms)
            # 搜索页?q= 未生效返回全站列表：只保留标题/作者真实命中检索词者
            if terms and score == 0:
                continue
            out.append(Book(
                source=self.name, source_id=p, title=title.title(), author=author.title(),
                rights_status=Rights.PUBLIC_DOMAIN,
                rights_basis="Standard Ebooks 官方声明：所收录书籍均为公有领域（standardebooks.org/faq）",
                source_url=self.BASEURL + "/" + p,
                online_read_url=self.BASEURL + "/" + p,
                format="epub", score=float(score),
            ))
        out.sort(key=lambda b: -b.score)
        return out[:limit]

    def download_links(self, b: Book) -> list[tuple[str, str]]:
        # 书页中解析 epub 直链
        html = fetch_text(b.source_url, timeout=20)
        links = []
        if html:
            for m in re.finditer(r'href="([^"]+\.epub)"', html):
                u = m.group(1)
                if u.startswith("/"):
                    u = self.BASEURL + u
                if u not in [x[1] for x in links]:
                    links.append(("epub", u))
        return links or [("epub", "")]


# ---------------------------------------------------------------- DOAB (OAI-PMH)
class DOABSource(BaseSource):
    """DOAB：开放获取图书目录。用 OAI-PMH 检索（oai_dc）。OW 许可。"""
    name = "doab"
    label = "DOAB"
    OAI = "https://directory.doabooks.org/oai/request"

    def availability(self) -> str:
        r = fetch_text(self.OAI + "?verb=Identify", timeout=20)
        return "OAI可检索" if r and "OAI-PMH" in r else "OAI端点异常"

    def search(self, query: str, limit: int = 20) -> list[Book]:
        xml = fetch_text(self.OAI + "?verb=ListRecords&metadataPrefix=oai_dc", timeout=40)
        if not xml or "<record" not in xml:
            return []
        out = []
        terms = [t.lower() for t in query.split() if t]
        for rec in re.findall(r"<record>(.*?)</record>", xml, re.S)[:400]:
            def tag(t):
                m = re.search(rf"<dc:{t}[^>]*>(.*?)</dc:{t}>", rec, re.S)
                return re.sub(r"\s+", " ", m.group(1)).strip() if m else ""
            title = clean_title(tag("title"))
            author = clean_author(tag("creator"))
            hay = (title + " " + author).lower()
            if terms and not any(t in hay for t in terms):
                continue
            links = re.findall(r'<dc:identifier[^>]*>(https?://[^<]+)</dc:identifier>', rec)
            out.append(Book(
                source=self.name, source_id=tag("identifier") or hashlib.md5(title.encode()).hexdigest()[:10],
                title=title, author=author,
                year=int(tag("date")[:4]) if re.match(r"\d{4}", tag("date")) else None,
                language=tag("language") or "en", isbn=tag("identifier") if "isbn" in tag("identifier").lower() else "",
                rights_status=Rights.AUTHORIZED,
                rights_basis="DOAB 目录仅收录开放获取(OA)图书；具体许可见各书页面",
                source_url=links[0] if links else "https://directory.doabooks.org/",
                online_read_url=links[0] if links else "https://directory.doabooks.org/",
                format="pdf", score=float(sum(hay.count(t) for t in terms)),
            ))
        out.sort(key=lambda b: -b.score)
        return out[:limit]

    def download_links(self, b: Book) -> list[tuple[str, str]]:
        return [("pdf", b.source_url)]


# ---------------------------------------------------------------- OAPEN / IA（当前网络不可达：只给入口）
class OAPENSource(BaseSource):
    name = "oapen"
    label = "OAPEN"
    reachable = False

    def availability(self) -> str:
        r = fetch_text("https://library.oapen.org/rest/search", timeout=12)
        self.reachable = bool(r)
        return "可检索" if self.reachable else "当前网络不可达（仅提供在线入口）"

    def search(self, query: str, limit: int = 20) -> list[Book]:
        return [Book(
            source=self.name, source_id="entry", title=f"[OAPEN 在线检索] {query}",
            rights_status=Rights.AUTHORIZED,
            rights_basis="OAPEN 为开放获取学术图书平台（OA 许可）；当前网络不可达，未自动下载",
            online_read_url="https://library.oapen.org/",
            note="当前网络不可达；请到 OAPEN 站内检索并核对每本许可后下载",
        )]


class InternetArchiveSource(BaseSource):
    """Internet Archive：混合 PD 与受版权借阅。默认只给在线入口，不自动下载。"""
    name = "archive"
    label = "Internet Archive"
    reachable = False

    def availability(self) -> str:
        r = fetch_text("https://archive.org/advancedsearch.php?q=test&rows=1&output=json", timeout=12)
        self.reachable = bool(r)
        return "可检索（需逐本判权）" if self.reachable else "当前网络不可达（仅提供在线入口）"

    def search(self, query: str, limit: int = 20) -> list[Book]:
        url = ("https://archive.org/advancedsearch.php?q=" +
               re.sub(r"\s+", "%20", query) + "&fl[]=identifier&fl[]=title&rows=10&output=json")
        raw = fetch_text(url, timeout=20)
        out = []
        if raw:
            try:
                for d in json.loads(raw).get("response", {}).get("docs", [])[:limit]:
                    ident = d.get("identifier", "")
                    out.append(Book(
                        source=self.name, source_id=ident,
                        title=clean_title(d.get("title", ident)),
                        rights_status=Rights.UNKNOWN,
                        rights_basis="Internet Archive 混合 PD 与受版权借阅；须逐本核对 rights/访问方式，未自动下载",
                        source_url=f"https://archive.org/details/{ident}",
                        online_read_url=f"https://archive.org/details/{ident}",
                        note="版权状态不明：若标注 Public Domain 可下载，否则仅借阅",
                    ))
            except Exception:
                pass
        if not out:
            out = [Book(
                source=self.name, source_id="entry", title=f"[Internet Archive 在线检索] {query}",
                rights_status=Rights.UNKNOWN,
                rights_basis="IA 混合 PD/借阅；当前网络不可达，未自动下载",
                online_read_url="https://archive.org/search?query=" + re.sub(r"\s+", "%20", query),
            )]
        return out[:limit]

    def download_links(self, b: Book) -> list[tuple[str, str]]:
        return []      # 不自动下载：IA 需逐本判权


# ---------------------------------------------------------------- OpenAlex（开放获取学术成果）
class OpenAlexSource(BaseSource):
    """OpenAlex：开放学术成果索引，含大量 OA 论文可直接下载 PDF。
    注意：这里拿到的是**当代学术研究论文**（研究者观点），不是史料。
    适合补充"研究综述/学术观点层"，不能当史实来源入库。"""

    name = "openalex"
    label = "OpenAlex"
    API = "https://api.openalex.org/works"

    def availability(self) -> str:
        r = fetch_text(self.API + "?search=test&per-page=1", timeout=20)
        return "可检索+可下载OA论文" if r and "results" in r else "不可达"

    def search(self, query: str, limit: int = 20) -> list[Book]:
        import urllib.parse as _up
        url = self.API + "?" + _up.urlencode({
            "search": query, "filter": "is_oa:true",
            "per-page": str(min(limit * 2, 50)),
        })
        raw = fetch_text(url, timeout=35)
        if not raw:
            return []
        try:
            data = json.loads(raw)
        except Exception:
            return []
        out = []
        for w in data.get("results", []):
            loc = w.get("best_oa_location") or {}
            pdf = loc.get("pdf_url")
            title = clean_title(w.get("title") or w.get("display_name") or "")
            if not title:
                continue
            lic = (loc.get("license") or "").lower()
            # cc-* 明确开放许可；其余（None/other-oa）标不明以免误判
            rights = Rights.OPEN_LICENSE if lic.startswith("cc") else Rights.UNKNOWN
            authors = [a.get("author", {}).get("display_name", "")
                       for a in (w.get("authorships") or [])[:3]]
            out.append(Book(
                source=self.name, source_id=(w.get("id") or "").rsplit("/", 1)[-1],
                title=title, author=", ".join([a for a in authors if a]),
                year=w.get("publication_year"),
                language="zh" if re.search(r"[\u4e00-\u9fff]", title) else "en",
                doi=(w.get("doi") or "").replace("https://doi.org/", ""),
                rights_status=rights,
                rights_basis=(f"OpenAlex 标记 is_oa=true，许可 {lic}；"
                              "内容为当代学术研究论文（研究者观点），非一手史料"),
                source_url=(w.get("doi") or loc.get("landing_page_url") or ""),
                download_url=pdf or "",
                online_read_url=loc.get("landing_page_url") or "",
                format="pdf", score=1.0,
                note="学术研究论文：可用于综述/观点层，不可当史实依据",
            ))
        return out[:limit]

    def download_links(self, b: Book) -> list[tuple[str, str]]:
        return [("pdf", b.download_url)] if b.download_url else []


# ---------------------------------------------------------------- 工作流编排
SOURCES = {
    "gutenberg": GutenbergSource,
    "wikisource": WikisourceSource,
    "standardebooks": StandardEbooksSource,
    "doab": DOABSource,
    "oapen": OAPENSource,
    "archive": InternetArchiveSource,
    "openalex": OpenAlexSource,
}


def get_sources(names: list[str]) -> list[BaseSource]:
    return [SOURCES[n]() for n in names if n in SOURCES]


def cmd_sources():
    print(f"{'源':<16}{'状态':<32}{'默认版权判定'}")
    print("-" * 76)
    for name, cls in SOURCES.items():
        s = cls()
        av = s.availability()
        default = {
            "gutenberg": "公有领域", "wikisource": "开放许可", "standardebooks": "公有领域",
            "doab": "开放许可(OA)", "oapen": "开放许可(OA)", "archive": "不明/逐本判权",
            "openalex": "CC许可OA论文(学术研究)",
        }[name]
        print(f"{name:<16}{av:<32}{default}")


def cmd_search(query: str, names: list[str], limit: int, register: bool):
    idx = BookIndex()
    sources = get_sources(names)
    all_books: list[Book] = []
    for s in sources:
        try:
            books = s.search(query, limit=limit)
        except Exception as e:
            print(f"[WARN] {s.label} 检索失败: {e}", file=sys.stderr)
            books = []
        print(f"[{s.label}] {len(books)} 条")
        all_books.extend(books)
    # 全局去重（优先保留有下载链接、公共领域者）
    seen, uniq = {}, []
    for b in all_books:
        k = b.dedup_key()
        if k in seen:
            continue
        seen[k] = True
        uniq.append(b)
    uniq.sort(key=lambda b: (
        0 if b.rights_status in DOWNLOADABLE else 1,
        -b.score, b.title,
    ))
    print(f"\n共 {len(uniq)} 条（去重后）")
    for i, b in enumerate(uniq[:40], 1):
        flag = "可下载" if b.rights_status in DOWNLOADABLE else "仅登记"
        print(f"{i:>3}. [{Rights.LABEL[b.rights_status]}/{flag}] {b.title[:52]} "
              f"— {b.author[:22]} ({b.source})")
    if register:
        new = sum(1 for b in uniq if idx.upsert_candidate(b))
        print(f"\n[索引] 新登记 {new} 条候选（重复 {len(uniq)-new} 条跳过）")
        print(f"[索引] 统计 {idx.stats()}")
    return uniq


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def cmd_download(query: str, names: list[str], max_items: int, formats: list[str]):
    DOWNLOADS.mkdir(parents=True, exist_ok=True)
    idx = BookIndex()
    sources = {s.name: s for s in get_sources(names)}
    candidates = cmd_search(query, names, limit=max_items * 3, register=True)
    todo = [b for b in candidates if b.rights_status in DOWNLOADABLE][:max_items]
    print(f"\n=== 合法下载 {len(todo)} 本（格式 {','.join(formats)}）===")
    ok = fail = 0
    for b in todo:
        adapter = sources.get(b.source)
        links = adapter.download_links(b) if adapter else [(b.format, b.download_url)]
        picked = [(f, u) for f, u in links if f in formats and u]
        if not picked:
            print(f"  [SKIP] {b.title[:40]} — 无可下载直链")
            fail += 1
            continue
        fmt, url = picked[0]
        raw = fetch(url, binary=True, timeout=60)
        if raw is None or len(raw) < 500:
            print(f"  [FAIL] {b.title[:40]} — 下载失败")
            fail += 1
            continue
        safe = re.sub(r"[^A-Za-z0-9\u4e00-\u9fff._-]", "_", b.title)[:60]
        fp = DOWNLOADS / f"{b.source}_{b.source_id}_{safe}.{fmt}"
        fp.write_bytes(raw)
        b.format = fmt
        idx.mark_downloaded(b, fp, sha256_file(fp))
        print(f"  [OK]   {b.title[:40]} -> {fp.name} ({len(raw)//1024}KB, {b.rights_status})")
        ok += 1
        time.sleep(0.4)
    print(f"\n完成：成功 {ok}，失败/跳过 {fail}")
    print(f"索引统计：{idx.stats()}")


def cmd_index(search: Optional[str], rights: Optional[str]):
    idx = BookIndex()
    where, params = [], []
    if search:
        where.append("(title LIKE ? OR author LIKE ?)")
        params += [f"%{search}%", f"%{search}%"]
    if rights:
        where.append("rights_status=?")
        params.append(rights)
    rows = idx.rows(" AND ".join(where), tuple(params))
    print(f"索引记录 {len(rows)} 条：")
    for r in rows[:60]:
        dl = "已下载" if r.get("local_path") else "候选"
        print(f"  [{Rights.LABEL.get(r['rights_status'], r['rights_status'])}/{dl}] "
              f"{r['title'][:50]} — {r['author'][:20]} ({r['source']})")
    print(f"\n统计: {idx.stats()}")


def cmd_report(out: Path):
    idx = BookIndex()
    rows = idx.rows()
    dl_rows = [r for r in rows if r.get("local_path")]
    unknown = [r for r in rows if r["rights_status"] == Rights.UNKNOWN]
    borrow = [r for r in rows if r["rights_status"] == Rights.BORROW_ONLY]
    out.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# 电子书检索与下载报告",
        "",
        f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        f"- 索引总数：**{len(rows)}**",
        f"- 已下载：**{len(dl_rows)}**",
        f"- 版权不明（单独列出，不阻塞）：**{len(unknown)}**",
        f"- 仅在线借阅：**{len(borrow)}**",
        "",
        "## 版权分布",
        "",
    ]
    for k, v in sorted(idx.stats()["by_rights"].items()):
        lines.append(f"- {Rights.LABEL.get(k, k)}: {v}")
    lines += ["", "## 已下载文件", "", "| 书名 | 作者 | 版权 | 格式 | 文件 |", "|---|---|---|---|---|"]
    for r in dl_rows:
        lines.append(f"| {r['title'][:40]} | {r['author'][:20]} | "
                     f"{Rights.LABEL.get(r['rights_status'],'')} | {r['format']} | {Path(r['local_path']).name} |")
    if unknown:
        lines += ["", "## 版权状态不明（仅提供入口，未下载）", ""]
        for r in unknown[:30]:
            lines.append(f"- {r['title'][:50]} — {r['online_read_url'] or '无入口'}")
    if borrow:
        lines += ["", "## 仅在线借阅（未下载）", ""]
        for r in borrow[:30]:
            lines.append(f"- {r['title'][:50]} — {r['online_read_url'] or '无入口'}")
    lines += ["", "## 版权依据说明", ""]
    seen_basis = {}
    for r in rows:
        if r["rights_basis"] and r["source"] not in seen_basis:
            seen_basis[r["source"]] = r["rights_basis"]
    for src, basis in seen_basis.items():
        lines.append(f"- **{src}**: {basis}")
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"报告已生成: {out}")


# ---------------------------------------------------------------- CLI
def main():
    ap = argparse.ArgumentParser(description="电子书自动检索与下载工作流（合规优先）")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("sources", help="查看各开放源可达性")

    p = sub.add_parser("search", help="多源检索")
    p.add_argument("query")
    p.add_argument("--sources", default="gutenberg,wikisource,standardebooks,doab,oapen,archive")
    p.add_argument("--limit", type=int, default=20)
    p.add_argument("--register", action="store_true", help="登记候选到索引")

    p = sub.add_parser("download", help="检索并下载合法资源")
    p.add_argument("query")
    p.add_argument("--sources", default="gutenberg,standardebooks,doab")
    p.add_argument("--max", type=int, default=5)
    p.add_argument("--formats", default="txt,epub,pdf")

    p = sub.add_parser("index", help="查看/检索本地书目索引")
    p.add_argument("--search")
    p.add_argument("--rights")

    p = sub.add_parser("report", help="生成 Markdown 报告")
    p.add_argument("--out", default=str(WORK / "report.md"))

    args = ap.parse_args()
    names = [n.strip() for n in getattr(args, "sources", "").split(",") if n.strip()]

    if args.cmd == "sources":
        cmd_sources()
    elif args.cmd == "search":
        cmd_search(args.query, names, args.limit, args.register)
    elif args.cmd == "download":
        cmd_download(args.query, names, args.max, [f.strip() for f in args.formats.split(",")])
    elif args.cmd == "index":
        cmd_index(args.search, args.rights)
    elif args.cmd == "report":
        cmd_report(Path(args.out))


if __name__ == "__main__":
    main()
