# Status

## State

**Active digital-curation prototype with explicit source/provenance debt.**

## Current strengths

- table-first canonical data;
- deterministic JSON generation;
- source ids carried into publication data;
- separate map, museum, immersive museum and local editor;
- ignored private research/extraction area;
- repeatable project checker.

## Current gates

- raw third-party extracted text must stay private;
- game-only candidate material must not silently become high-certainty;
- external image licenses/attribution still need per-file completion where the current registry says only “see file page”;
- route coordinates and some interpretive visual layers are approximate;
- historical/source review is an editorial/research gate separate from code correctness.

## Canonical state

Current data counts should be read from `python tools/check_project.py`, not copied manually into status documents.

## 2026-11-22 structural feedback pass (v9)

Applied structural changes from the 2026-05-28 meeting feedback (see `docs/FEEDBACK_ACTION_PLAN.md`):

- **Route grouping (frontend + data)**: `subjects.csv` now carries `group` / `groupEn`; route panel groups forces into 红军主线 / 星星之火 / 敌军. Added 5 missing subjects as **skeleton only** (红西路军, 琼崖纵队, 东北抗联, 东江纵队, 日军) — no invented events; each marked "events pending sourced review".
- **Colors**: main Red Army routes moved to a red-dominant palette (国旗红 for 红一方面军, darker/lighter reds for others); KMT enemy → black; Japan → dark slate. Interpretive layer, not historical claim.
- **Time range**: `timeRange.end` extended to 1936-12-12 (西安事变) per feedback; `start` already covered 第五次反围剿.
- **Museum navigation**: hall labels reframed as "视角" (viewpoints) instead of "第X展厅"; added a "新长征" placeholder section with the public 论述 quote and an explicit "权威素材待补" note — no fabricated itinerary or speeches.
- **Local consolidation**: reverse-engineering artifacts (pak parse tools, 211MB unpacked game assets, legacy datasets, martyrs reference) moved under ignored `research_private/`; feedback transcript + Steam URL copied into `docs/`.

Gates unchanged: game-only events remain low-certainty (246), raw extraction stays outside Git, visual-asset licenses still unresolved (34/38). All structural additions are candidate/skeleton and must not be presented as verified history without independent sourcing.

Validation: `python tools/check_project.py` passes (subjects=28, events=386, persons=67). Browser smoke test confirmed grouping labels, viewpoint nav, and new-longmarch section render without runtime errors (only favicon 404).

## 2026-11-22 sourced-research pass (v10)

Authorized historical research added with authoritative sources; see `research_private/sourced_research/*.md` for full source URLs and ⚠️ doubtful items.

- **Sources** 38→59, **events** 386→411, **persons** 67→79. All 25 new events are `certainty=high` with resolvable source ids; 12 new persons added.
- **西路军** (7 events, force `red_west_route`): 渡河/组建/永昌山丹/高台/倪家营子/石窝/星星峡. **东北抗联** (5, `spark_dongbei`), **琼崖纵队** (8, `spark_qiongya`), **东江纵队** (5, `spark_dongjiang`).
- Correction applied: 董振堂 title is 红五军军长 (not 军团军团长); 杨克明 is 红五军政治部主任 (not 董振堂政委). Rejected as unverifiable: "熊炳林" (查无此人), "陈荣香/陈文香断肠" (无权威来源, likely confused with 陈树湘).
- **新长征**: quote corrected to 2016-10-21 长征胜利80周年讲话原文, with explicit note that "一代人有一代人的长征..." is from 2019-04-30 五四讲话; both official gov.cn links added.
- **Memorial layer**: `data/memorial_sites.geojson` — 16 长征-related memorial sites with GCJ-02 coordinates sourced from 腾讯地图 POI / government sites. Toggle button `#memorial-toggle` on map page shows/hides `L.circleMarker` layer (no external API key). Browser test: marker count 1→17 on toggle.
- **Game-content audit** (`docs/GAME_CONTENT_AUDIT.md`): game text extraction yields 5,905 strings / 1,028 timeline candidates, but only 246 events + 32 persons were imported (all `low` certainty). Game content is NOT fully in the project.
- New tool `tools/import_sourced_research.py` (idempotent, by id) reproduces the table additions.

All new time-extended events (1927-1950) are marked as 延伸视角 in notes; they enlarge the timeline beyond 1934-1936 by design (西路军 is the Long March epilogue; 琼崖/东江/抗联 are the "星星之火" follow-on). Check passes with 0 errors (1 pre-existing visual-asset license warning).

## 2026-11-22 evidence-model + multi-source + explore UI (v11)

- **Evidence model**: `sources.csv` gained `sourceType` (authoritative/game_text/book/subtitle/oral_history/public_narrative). `check_project.py` now enforces a non-authoritative certainty ceiling — non-authoritative-backed events cannot be `certainty=high` (246 game events verified). Extend via `tools/extend_evidence_model.py`.
- **Input pipelines** (candidates only, never auto-imported): `tools/extract_book_candidates.py` (PDF text layer / TXT / OCR text → anchored snippets with page + date hints; scanned PDFs require external OCR — no engine bundled), `tools/extract_subtitle_candidates.py` (srt/vtt/ass, timeline-block merge, ASR transcript entry point → public_narrative candidates). Both output to `research_private/`.
- **Explore UI**: new `explore.html` + `js/explore.js` + `css/explore.css` — data-driven thematic entry (person/force/place/event cards), replaces index.html's direct jump to museum. `museum.html?person=<id>` deep-link selects a person automatically. Index now points to explore.html. check_project.py covers the new files.
- Browser verified: 8 person / 12 force / 10 place / 6 event cards render; `?person=dongzhengtang` selects 董振堂 correctly. No runtime errors (favicon 404 only).

Local scanned gazetteers (绥德州志 etc., PDF, 39-154MB) have NO text layer — need OCR before the book pipeline can use them. No OCR engine installed locally at time of writing.

**UI decision (user, same day)**: keep the previous museum-first UI. `index.html` and both start scripts point back to `museum.html`. `explore.html` remains in the repo as an optional, non-default entry. Evidence-model and input-pipeline changes from v11 are unaffected.

## 2026-11-22 data densification (v12/v13)

Addressed the "is the data sufficient?" audit (main route was sufficient; person links + credibility were not):

- **v12 — person-event links**: `tools/link_zero_person_events.py` added 33 evidence-based links (zero orphans 19→0); `tools/add_key_persons.py` added 5 key missing figures (博古/李德/林彪/方志敏/程世才) from authoritative sources + 2 红十军团 events + 10 links.
- **v13 — extended routes**: `tools/import_extended_events.py` (data in `research_private/sourced_research/04_extended_events.json`) added 31 authoritative events + 10 persons + 29 links: 西路军 15, 琼崖 15, 抗联 13, 东江 13 — each route now 13-15 nodes, enough for a continuous story. All with source URLs; doubtful items (镜泊湖 disputed figures, 琼崖 renaming, 孙玉清 exact date) marked medium or excluded.
- **Result**: events 411→444, persons 79→94, links 348→420, high-certainty 32→63, low share 60%→55%, zero person orphans.
- Browser verified: 444 events, timeline 1927-1950, 12 forces, 3 groups, no runtime errors. check_project.py passes.

**Remaining gap**: low-certainty (game-text) events still 246 — the single biggest credibility debt. Next priority is upgrading high-importance game clues with authoritative sources.

## 2026-11-22 low→high upgrade pass

Method: authoritative-source verification, NOT relabeling. `tools/upgrade_game_clues.py` reads a result JSON, replaces the game source with the authoritative source (so the "non-authoritative cannot be high" gate holds), disables duplicates + cleans their person-event links, and annotates keep-low items. All upgrade sources verified as 中国共产党新闻网 / 人民网.

- **batch1 (红一方面军, 20 checked)**: 10 UPGRADE (道县/四道封锁线/施秉黄平/猴场会议/遵义会议/二渡赤水/四渡赤水/金沙江/大渡河/夹金山), 3 DUP disabled, 4 KEEP_LOW (bad dates/game invention).
- **batch2 (data-quality errors)**: 4 游戏文本拼接错点 disabled — "到达莫斯科"×2 ("在贵州遵义一带到达莫斯科"), "占领西宁"×2 ("在四川松潘毛儿盖占领西宁"); also cleaned 8 bogus person-event links these errors had polluted.
- **batch3 (other routes, 12 checked)**: 6 UPGRADE (阆中/红六军团占新田/渡湘江/红25军北上宣言/独树镇/陕甘反围剿), 5 KEEP_LOW (张冠李戴/日期错位: 红四渡金沙江, 会宁占领, 红二渡金沙江, 川南游击纵队, 金沙江日期).
- **Net**: high 63→79 (+16), game-only low 246→223 (-23: 16 upgraded + 7 disabled). No event carries both game source and high certainty. check_project.py passes; browser verified 437 events render.

**Key finding**: game-text extraction has systematic place/event splicing errors (Moscow/Xining) — these were silently polluting the person timelines. Recommend always cross-checking game-derived location against the event description before import.

## 2026-11-22 multi-source capture experiments + literature extraction

User asked to add classic films (四渡赤水/长征/古田会议), books, video subtitles, and B站 subtitles. See `research_private/sourced_research/06_多源采集实验报告.md` for full findings.

- **Toolchain built & tested** (all in `tools/`, outputs stay in git-ignored `research_private/media_capture/`): `asr_to_srt.py` (local faster-whisper-base, 534s→351 srt lines in ~4.5min), `correct_asr_terms.py` (domain-term correction, 157 lines fixed), `extract_subtitle_candidates.py` (existing, now also handles ASR transcripts). yt-dlp 2026.10.21 + ffmpeg available; faster-whisper 1.2.1 installed in `envs/default` Python.
- **Blockers found (honest limits)**: B站 videos have NO CC subtitles (only danmaku) in all 3 tested → ASR is mandatory; base-model ASR error rate too high for military/proper-noun content ("四渡赤水"→"事都刺水", 351 lines→only 2 usable candidates even after correction); small-model download blocked by proxy 502 + direct timeout; film-subtitle sites require Turnstile verification. Result: subtitle/ASR route is technically working but low-yield at current model quality.
- **Higher-value alternative proven**: WebFetch structured extraction from authoritative党史 text (中国共产党新闻网《一百年大事记》) yielded 31 reliable facts in one pass. `05_权威文献抽取示范.md` documents the method.
- **Authoritative gaps filled** (verified by research agent, `07_文献抽取补录.json`): +3 events (南方三年游击战争部署1934.10 / 扎西张闻天负总责1935-02-05 / 苟坝三人军事小组1935-03-12), +3 persons (项英/陈毅/瞿秋白), +9 links, +3 sources. Corrected `r25_19350918_yongping_meeting` to add 程子华 as 政治委员 (was missing). Note: 红十五军团合编 and 红二方面军成立 were already in data — not duplicated.
- Totals: events 437→440, persons 94→97, sources 98→101. check_project.py passes; browser verified 440 events render.

**If better subtitles arrive** (user-provided srt / film subtitle files / larger whisper model): pipeline is ready — drop into `research_private/media_capture/`, run correct_asr_terms.py if ASR-generated, then extract_subtitle_candidates.py with `--source-type public_narrative`.

## 2026-11-22 ebooks + 斯诺一手细节 (v15)

- Downloaded 《红星照耀中国》中文版 PDF (9.3MB/407p, OCR text layer) from a public GitHub Pages source; main long-march chapter (p162-183) exported to `research_private/ebooks/red_star_longmarch_chapter.md`; 400 book candidates extracted.
- Platform reality: Gutenberg official 503 (maintenance), pglaf mirror works; Internet Archive/Anna's Archive/LibGen/Z-Lib unreachable or copyright-restricted — did NOT bypass paywalls/DRM. Details in `research_private/sourced_research/06`.
- Research agent distilled 12 unique first-hand details from 斯诺's chapter (石达开之鉴/歃血结盟/泸定桥30勇士/18088里之辨/每天71华里/草地一条人命买头羊...), all marked `certainty=medium` with new source `src_snow_redstar`, notes state "一手见闻·非权威定论". Sensitive/unsourced items (彭德怀徐海东口述、兵力数字与张国焘分歧) deliberately excluded.
- `09_斯诺细节补录.json` → +12 events. `import_extended_events.py` hardened: all JSON keys optional (selective imports no longer KeyError).
- Totals: events 440→452, sources 101→102. check passes; browser verified 12 snow events load as medium.

**Value note**: 斯诺 is a 1936 first-hand witness — these add the "detail layer" (numbers, dialogue, scenes) missing from authoritative党史 entries, but are explicitly NOT treated as high-certainty fact.

## 2026-11-22 book inventory + 长征记 facts (v16)

- **Book inventory**: ~125 titles across 7 categories (一手回忆录31/通史7/专题史17/军史9/学术20/地方史26/纪实文学~15). Full lists in `research_private/sourced_research/11`~`14` (git-ignored). Each with author/year/value/copyright status/source URL.
- **Download strategy (3 zones)**: green=公版/官方公开可下载; yellow=受版权但官方连载→只抽事实; red=受版权→只登记不下载. Key nuance: 公版原著≠公版译本 (斯诺原著2023公版 but 董乐山译本 protected to 2049).
- **Platform reality**: 人民网/党史网 fetchable (via curl -k + GBK decode); archive.org/Anna's/LibGen/Z-Lib unreachable; Gutenberg official 503 (pglaf mirror OK). No paywall/DRM bypass.
- **人民网《长征记》全29章抓取** (~100k chars, 曲爱国/张从田, 华夏出版社授权): `tools/fetch_changzhengji.py`. Page says 请勿转载 → facts-only extraction, no full text published.
- **20 authoritative facts extracted** from 长征记 (`15_长征记事实补录.json`), all certainty=high: 蒋介石五路追堵/桂军让道/新圩光华铺脚山铺阻击/土城决策/扎西整编/红9伪装/17勇士/泸定桥22勇士/嘉陵江/剑门关/陕南/龙日坝/包座/庾家河/板桥/红2巩固苏区/石鼓渡江/甘孜会师/山城堡(原缺口). Agent verified each absent from existing 452 events.
- **口径冲突 handled by coexistence**: 斯诺线索(30勇士/16铁索, medium) vs 军事科学院(22勇士/13铁索, high) — both kept with notes stating the difference, not force-merged.
- Totals: events 452→472, sources 102→103. check passes; browser verified 20 facts load + 山城堡 gap filled.

## 2026-11-23 《红军长征记》全文 + 口径差异呈现 (v18)

- **《红军长征记》全135篇原文获取**（1937年2月编定/1942年11月延安印行，百余位亲历者亲笔）：超星学习通专题逐篇抓取，存 `research_private/ebooks/hongjun_changzhengji/`（git忽略）。**三重交叉验证通过**：与中央党史和文献研究院原文逐字比对（陈云两篇完全一致）、与刘统整理注释本12-gram Jaccard 0.876–0.949、与《红军长征纪实丛书》ISBN 9787509845960 篇目表 135/135 一致。
- **6 篇核心长稿 14.5 万字**：陈云4篇（关于长征和遵义会议情况的报告/随军西行见闻录/英勇的西征/红军二万五千里西引记，署名廉臣·施平·幽谷）+ 邓发2篇（雪山草地行军记/从甘肃到陕西）。
- **《长征大事记》逐日实录**（原件藏中央档案馆，1991年《党的文献》首次整理发表）文本层完整，含逐日部队/地点/战斗。
- **18088里里程硬数据**：三个统计表为扫描图，但表前说明含"统计长征行程共为一万八千零八十八里"与逐月行军天数——与斯诺口径完全一致，两份互不相干文献互证。
- **化名归一**：原始署名多化名（廉臣/施平/幽谷/加伦/小朋/艾平/觉哉等），已建映射表 `_author_map.json`，归一后 51 位作者。
- **来源 `src_hongjun_changzhengji` 已建**，底本公版（1937/1942 集体作品+作者多数逝世逾50年），现代整理本受保护；处理口径同人民网版：只提事实要素、不转载原文。
- **口径差异呈现（新功能）**：`tools/build_variant_groups.py` 识别同一史实的多种来源记载（21组），前端目录卡显示「N 种记载」按钮，点击并排展开各来源说法+证据等级+原文链接。已收录关键案例：十七勇士（军科院22 vs 斯诺30）、庾家河战斗（5种说法）、遵义会议、红25军先遣队。
- **红四/红25 low 线索核实升级**：+11 条 low→high 并补权威史实（广昭战役18个团/绥崇丹懋战役计划/西南局成立/红四渡金沙江/通渭/将台堡/青江驿/会宁/会师大会/红25第二先遣队/庾家河战斗）；禁用4条重复low并同步禁用其 person_events；**修正3处地点硬错误**（绥崇丹懋 湖南通道→四川丹巴、渡澧河 →河南罗山、双石铺 四川若尔盖→陕西凤县）；标注红七军团先遣队(1934.7)≠红25军第二先遣队(1934.11)。
- **OA 学术文献**：7 篇 cc 许可论文下载，整理为 `18_OA论文学术综述.md`，明确标注"当代学术研究≠史料"，供研究综述/观众研究/技术方法参照。
- Totals: events 495→502, sources 110→111, persons 101。check 通过；浏览器验证 43 个口径差异按钮、面板展开正常。

## 2026-11-23 《长征大事记》逐日实录入库 (v19)

- **《红军长征记》135 篇公开全文已获取**（1937年2月编定/1942年11月延安印行，百余位亲历者亲笔）：超星学习通专题逐篇抓取，存 `research_private/ebooks/hongjun_changzhengji/`（git忽略）。
  - **三重交叉验证通过**：与中央党史和文献研究院原文逐字比对（陈云两篇完全一致）／与刘统整理注释本 12-gram Jaccard 0.876–0.949／与《红军长征纪实丛书》篇目表 135/135 一致。
  - 6 篇核心长稿 14.5 万字：陈云 4 篇（关于长征和遵义会议情况的报告／随军西行见闻录／英勇的西征／红军二万五千里西引记，署名廉臣·施平·幽谷）+ 邓发 2 篇（雪山草地行军记／从甘肃到陕西）。
  - 里程表说明含硬数据：**总行程 18088 里** + 逐月行军天数——与斯诺口径完全一致，两份互不相干的文献互证。
  - **化名归一**：原刊多化名（廉臣/施平/幽谷/加伦/小朋/艾平/觉哉等），已建 `_author_map.json`，归一后 **51 位作者**。
  - 新来源 `src_hongjun_changzhengji`；底本公版（集体作品 + 作者多数逝世逾 50 年），现代整理本受保护；处理口径同人民网版：只提事实要素、不转载原文。
- **《长征大事记》逐日实录**（原件藏中央档案馆，1991年《党的文献》首次整理发表）文本层完整：
  - `tools/extract_dashi_from_changzhengji.py`：解析中文年月日、按部队切分、地名白名单匹配 → 465 条覆盖 74 个日期（1934-10-12 至 1935-01-01）
  - `tools/build_dashi_events.py`：按日聚合成事件，只对现有事件**未覆盖**的日期建条目 → **+35 条 high 逐日行军纪要**
  - 内容示例：10月23日一军团主力在安息圩激战、俘敌三百余缴轻机枪二挺；三军团先头第五师在大塘铺消灭粤敌两个连
- Totals: events 502→537, sources 110→111。check 通过。

## 2026-11-23 《红军长征记》深度利用：文献史+人物库 (v24)

- **文献史层（+11 条 high）**——《红军长征记》前言篇（刘统撰，52KB）记载了全书编纂全过程，项目此前完全没有这一层：
  - 1936-08-05 毛泽东与杨尚昆联署征稿信（原文引用）
  - 1936-10 收到来稿 200 余篇约 50 万言；编辑委员会（总政治部宣传部主编，丁玲、徐特立、成仿吾分头编辑）与选编四条方针
  - 1937-02 编成；1942-11 延安印行（草纸印、印数极少、"依本来面目，一字未改"、哈佛燕京图书馆 2002 年发现朱德签名本）
  - 1954《党史资料》重印本（95 篇）与 1955 人民出版社选本（51 篇 + 缪楚黄《中国工农红军长征概述》）
  - **"长征"一词由毛泽东命名**（1935年12月报告"长征是宣言书、宣传队、播种机"）；陈云当时称"西征"
  - **杨定华笔名考证**：杨鼎华与杨定华同音 + 邓发任陕甘支队第三纵队政治委员与原文"我从来行军都是随着第三纵队走的"契合 → 认定为邓发
  - 1935-10-15 陈云共产国际执委会报告原稿（1996 年中共中央文献研究室经俄罗斯远东研究所协助在共产国际档案发现），《党的文献》2001 年第 4 期发表
  - 1936-03《随军西行见闻录》发表于巴黎《全民月刊》；1937-07-31 廉臣与杨定华在《救国时报》第 114 期捐赠版权
- **人物库扩容：101 → 150 位**
  - 《红军长征记》51 位署名作者按本名建档，生卒年取自 1937/1942 原刊各篇脚注（46 位有生卒年），含笔名对照
  - 查证代理**纠正了原刊脚注错误**：如"艾平"并非张爱萍上将，而是艾平赖智山
  - 3 处存疑项与查不到项如实标注，未臆造；陈云、任弼时为更新已有条目而非重复新建
  - 新增 tools/build_author_persons.py + tools/import_author_persons.py
- Totals: events 588→599, persons 101→150。check 通过；浏览器验证 599 事件 / 150 人物渲染正常。

## 2026-11-23 《红军长征记》第三批开采：掉队/扩红/游击队 (v29)

- **+9 条 medium**，全部来自此前未开采的篇目，每一篇都是项目原来完全没有的**视角**：
  - **《我失联络》（第48篇）**——长征掉队—群众救护—归队的完整个案：土城战后带病掉队，营盘山顶迷路，正月初一在茅房被民团十余人持枪闯入，掏手枪击毙民团队长后夺路登山，民团带十余条狗搜山数小时；夜行至黄家沟遇八旬老妇与户主黄大（家无寸土、租地还租），藏匿五日、赠百姓衣服、初六化装拜年客护送，途中遇何姓民团队长盘查反赠铜元三吊作盘缠，经硬地街遇三军团卫生部伤兵，十日后归队。**此篇原刊无作者小传，学界至今未考出姓名——如实标注，未臆造**。
  - **同篇「开小差的下场」**——两名江西会昌炮兵连士兵各卖枪得八十银毫洋、钱被民团拿走、身虱满衣睡草堆、想归队又怕杀头。**长征文献中罕见的逃兵自述**。
  - **《扩大红军》（第56篇）**——扩红具体操作：地方工作组先于尖兵出发、路边找群众讲话；『你如嫌我太老了，把我十八岁的儿子送去同你当红军』（1935-04-05 贵州高寨）；崖脚老汉壮胆促喊、五名青年当场参军（04-07 龙里），揭示「先说服有声望老人、再带动一群人」的扩红机制。
  - **《聂都游击队的记述》（第21篇）**——粤湘赣三省交界的八年游击史、曾创造独立师团送入主力、南雄县委书记亲率夜间转移。**地方游击队视角，与主力长征形成对照**。
  - **《突围的第一仗》（第15篇，谭政撰）**——一师袭取金鸡、新田，敌溃退时放火烧街、红军忙于救火，居民称『红军呱呱叫』；次日石背遭遇一击溃粤敌两个团。
  - **《渡乌江》（第44篇，刘亚楼撰）**——乌江『水深不可测，鹅毛亦沉』、江水冷而轻浮力小不能作桥料、耗一整天才架成；三连长毛正华五人潜伏距敌仅二三十米、听见敌排长说『要怕他的水马晚上弄过来』；3月3日强渡『最先过去的只有二十二个红色英雄』。
  - **《从金沙江到大渡河》（第72篇，李一氓撰，三万余字）**——1931年在北平图书馆翻太平天国史料的个人前史，『安顺场，要是不到这个地方，也不会知道这个地方』。
- Totals: events 608→617, persons 150。check 通过；浏览器验证 617 事件 / 150 人物渲染正常。
