# 电子书自动检索与下载工作流

`tools/ebook_workflow.py` —— 合规优先的多源电子书检索/下载/归档工具。

## 原则
- 只从开放/授权源检索；**明确允许下载**的自动下载，**不破解 DRM、不绕过付费墙**。
- 版权分级：`public_domain` / `open_license` / `authorized` / `borrow_only` / `unknown` / `copyrighted`。
- 仅前三档自动下载；其余记录在线入口，单独列出，不阻塞已授权任务。
- 一切产物落在 `research_private/ebooks/workflow/`（git 忽略）：下载文件、SQLite 索引、缓存、报告。

## 源与可达性（本机实测 2026-11-22）
| 源 | 状态 | 默认版权判定 |
|---|---|---|
| Project Gutenberg（pglaf 镜像） | 可检索+可下载 | 公有领域 |
| Wikisource（zh/en MediaWiki API） | 可检索+可抓取 | 开放许可 |
| Standard Ebooks | 可检索（搜索页） | 公有领域 |
| DOAB（OAI-PMH） | 视网络 | 开放获取 |
| OAPEN / Internet Archive | 当前网络不可达 → 仅在线入口 | 授权/不明 |

> Gutenberg 用 pglaf 镜像绕开官方站 503；检索依赖 `cache/gutindex.all.txt`（首次自动下载 425KB+，若失败可手动放入）。

## 用法
```bash
# 1. 查看各源可达性
python tools/ebook_workflow.py sources

# 2. 多源检索（--register 登记候选到索引）
python tools/ebook_workflow.py search "long march" --sources gutenberg,wikisource --register

# 3. 检索并下载合法资源
python tools/ebook_workflow.py download "China" --sources gutenberg --max 5 --formats txt,epub

# 4. 查询本地书目索引
python tools/ebook_workflow.py index --search China
python tools/ebook_workflow.py index --rights unknown

# 5. 生成 Markdown 报告（含版权依据、不明项入口）
python tools/ebook_workflow.py report
```

## 索引字段
规范化后的书名/作者/年份/语言/ISBN/来源，加版权状态、版权依据、原始 URL、下载 URL、在线入口、本地路径、SHA256、下载时间。按「规范化标题+作者」哈希去重。

## 合规说明
- 公版原著 ≠ 公版译本：如斯诺原著已公版，但董乐山译本仍受保护——本工具只按源站声明判定，使用前请核对具体版本。
- Internet Archive 混合公有领域与受版权借阅，工具一律标 `unknown` 不自动下载。
- “版权不明”项只在报告里列出在线阅读/购买入口，供人工判断。
