# 红军长征星火路线 · 系统重构与持续推进路线图（ROADMAP）

> 制定时间：2026-11-24  
> 定位：摆脱“只管堆数据”的冷启惯性，转向**地理可信、考据可见、架构可维护、可持续扩张**的长期演进轨道。

---

## 一、核心原则

1. **表格为唯一真源**：所有结构化内容均维护在 `data_edit/*.csv`，经统一构建流水线 `tools/pipeline.py` 生成发布数据（`data/long_march_events.json`、`data/variant_groups.json`、`data/references.json`、`REFERENCES.md`）。
2. **行军与非行军严格分层**：只有真实的军事行军/作战/会议/渡河/会师/牺牲节点参与路线连线；里程统计、民族区域统计、生活卫生回顾与海内外文献传播史独立分层，绝不把核心行军路线拉成跨国蜘蛛网。
3. **证据分层与源透明度**：`certainty`（`high` 权威史实 / `medium` 一手见闻 / `low` 线索待证）与 `datePrecision`（`day` / `month` / `range` / `approx`）正交分离；同一史实的多源口径差异并存不合并，并在前端显性展示书名与篇目出处。
4. **硬门禁阻断脏数据**：所有历史踩过的坑（>300km 异常跳点、非法枚举、篇名当坐标、非权威源冒充 `high`、重复书目、跨表悬空引用）必须写死进 `tools/check_project.py`，CI 阻断入库。

---

## 二、分阶段推进计划与验收标准

### P0 · 止血修图与 Schema 正交化（✅ 已完成 · 2026-11-24）

- [x] **数据拆层（`layer`）**：为 `events.csv` 增加 `layer` 字段，严格区分 `march`（483，核心长征行军）、`spark_march`（70，延伸星火与前史行军）、`theme_stat`（35，里程/民族/生活统计专题，不连线）、`historiography`（19，文献编纂与海外传播史，不连线）。
- [x] **Schema 清洗**：
  - 拆分 `datePrecision`（`day` / `month` / `range` / `approx`），`certainty` 严格限定为 `high`（153） / `medium`（244） / `low`（210）（修复 18 条混填值，69 条纯亲历专著条回归 `medium`）。
  - 32 种碎片 `type` 收拢为 **8 大标准 2 字类型**：`战斗`、`行军`、`决策`、`渡险`、`会师`、`牺牲`、`民生`、`史料`。
  - 修复 `hjdet_*` 篇名误填 `locationName`、占位日期及 `forceId` 错配（单家集、榜罗镇、吴起镇归 `red_first`）及 `dashi_*` 11–12 月兜底坐标。
  - 逐条清理全部 68 处 >300km 路线异常跳点（修复 82 处错配坐标/日期/部队；禁用 11 条已证伪串台/误标重复条目并同步清理/重映射 `person_events.csv` 19 条关联）。
  - 修正 `sources.csv` 中 `src_snow_redstar` / `src_hongjun_changzhengji` 的 `sourceType=book`，消除重复书名并标注镜像关系。
  - 清理 `subjects.csv` 中 16 行历史遗留的 0 事件 `type=person` 行（28 → 12 行）。
- [x] **工程与门禁升级**：
  - `tools/build_json_from_tables.py` 透传 `layer`、`datePrecision` 及来源完整著录字段。
  - 新建 `tools/pipeline.py` 一条龙构建脚本（同步生成 `long_march_events.json` + `variant_groups.json` + `references.json` + `REFERENCES.md` + 跑全套检查）；将 17 个历史一次性脚本归档至 `tools/archive/`。
  - 修复 `js/app.js` 路线连线逻辑：仅对 `march` / `spark_march` 同部队节点连线，适配 8 大标准类型。
  - 升级 `tools/check_project.py` 硬门禁：核心行军层跳点 >300km 阻断（仅白名单 1 处 28 天横穿滇中真实跨度）、严格枚举校验、`locationName` 洁净度检查、非权威源升级门禁修正、全量 `tools/*.py` 语法编译。
- **P0 验收结果**：✅ 核心长征行军层异常跳点归零（68 → 0），`certainty`/`layer`/`datePrecision`/`type` 100% 合规，`pipeline.py` + `check_project.py` 全绿。

---

### P1 · 前端考证显性化、地图双模式滤镜与入口收拢（✅ 已完成 · 2026-11-24）

- [x] **让学术考证上屏（接入 `data/references.json` 与 `data/variant_groups.json`）**：
  - 地图详情卡（`map.html` / `index-en.html` / `js/app.js`）新增：证据等级徽章、日期精度与分层提示、具体出处胶囊（书名/机构 + 篇目定位/外链）与可展开的口径差异对比。
  - 博物馆事件卡（`museum.html` / `js/museum.js`）每条事件直接展示出处书名/篇目与可点击按来源反查，主题筛选升级为 8 大语义分组。
  - 重做「视角七 · 考证与书目」为**可检索的参考书目与史料考证中心**：展示分层占比看板、核心专著/权威官网/候选线索分类检索、GB/T 7714 关键著录、引用次数与一键按来源反查关联事件。
- [x] **地图双模式与证据滤镜**：
  - 新增时空模式切换：**核心长征 1934–36（默认，287 核实节点）** vs **全域星火（全部 606 节点）**。
  - 新增证据等级快捷滤镜（权威+一手默认 / 仅权威 / 含待证线索），并支持点击人物标签高亮地图人物轨迹与 `#place=` / 跨层 `#event=` 深链自动放宽滤镜。
- [x] **前端性能与入口收拢**：
  - 博物馆总目录增加按需分页（每页 36 条 + 加载更多/全部展开）；人物侧栏新增实时检索框（`#person-search`）。
  - 修复 `explore.js` 7 个失效人物 ID（15/15 命中）与地点/部队深链（`map.html#place=`、`museum.html?force=`）。
  - 修正 `museum-immersive.html` 静态写死计数为动态加载并明确实验性三维展厅定位。
- **P1 验收结果**：✅ 无头浏览器（Edge/Playwright）实测 `museum.html` / `explore.html` / `map.html` / `index-en.html` 及跨页深链均 0 报错，各项交互断言全通过。

---

### P2 · 存量信用清债与史料纵深开采（✅ 已完成 · 2026-11-24）

- [x] **清债 210 条 `low` 游戏线索**（`tools/archive/p2_adjudicate_low_events.py` + `p2_second_pass_low_cleanup.py`）：
  - 逐条对照本地权威《长征记》（曲爱国/张从田，人民网党史频道 29 章）与一手《红军长征记》全文核验，产出 **49 条升级 `high`**（附具体章目出处）、**2 条升级 `medium`**（《长征大事记》逐日实录）、**78 条禁用**（72 重复/跨部队克隆 + 41 错乱/残缺/敌军行动误套红军，合计二轮 6 条）、**40 条诚实保留 `low`**。
  - 同步重映射/去重 **97 条** `person_events.csv` 关联，**0 条**人物关联指向已禁用或不存在事件。
  - 修正 20+ 处地点硬错误（老山界→广西龙胜、黄平≠瓮安猴场、威信大河滩≠贵州遵义、九间房≠袁家沟口、双石铺≠若尔盖草地、漳县≠包座、阿坝≠俄界/腊子口等）。
  - **结果**：`low` 210 → **40 条（7.6%）**，`high+medium` 占比 **92.4%**（目标 ≥90% 达成）。
- [x] **开采《红军长征记》剩余篇目并清零 31 位零关联人物**（`tools/archive/p2_harvest_hongjun_and_link_authors.py`）：
  - 从 135 篇全集中精准补采 **35 条此前完全缺失的一手纪实**（第 9/13/21/24/27/30/36/37/38/41/45/46/48/49/53/54/55/57/58/60/62/66/70/82/88/91/95/97/100/101/105/106/110/112/113/130 篇），全部 `certainty=medium` 且标注篇号与作者。
  - 建立 **59 条**作者↔事件精确关联，**31 位零关联人物全部清零**（含集体署名作者「泅水及撑排的」）。
  - 修正 `persons.csv` 中 4 处作者姓名/生平错标（艾平误记为上将应为艾平赖智山；许_陈士榘、毕武、杨成武 本名与化名归位）。
- [x] **视觉资产版权清债**（`tools/archive/p2_resolve_visual_licenses.py`）：调用 Wikimedia Commons API 逐文件抓取 `LicenseShortName` 与 `Artist/Credit`，**38 张外部图片全部写入精确协议与署名**（CC BY-SA 3.0/4.0、CC0、Public domain），`check_project.py` 的版权告警由 **34/38 降为 0**，并升级为硬门禁（未清债即 CI 阻断）。
- [x] **县镇级历史地名词典**（`tools/build_gazetteer.py` → `data_edit/gazetteer.csv`）：沉淀 **365 个规范地名**（含省份归属、古今对照、经纬度、事件数、涉及部队），其中 **53 条**附同名消歧注释（如「两河口」分四川小金／湖南桑植；「安定」指陕北子长非甘肃安定区；「俄界」为中央纵队而非红四方面军），并新增 `check_gazetteer_integrity` 硬门禁。
- **P2 硬验收结果**：✅ `python tools/pipeline.py` 五步全绿（subjects=12, sources=111, events=524, persons=150, visuals=40, gazetteer=365）；✅ Edge 无头浏览器 6 页 + 4 条深链 **0 运行时错误**；✅ `low` 占比 7.6%（<10% 达成）、零关联人物 0、未清债版权图片 0。

---

### P3 · 平台化持续运营与多专题扩展

- [x] **将 `data_edit/gazetteer.csv` 接入前端**（✅ 2026-11-24，commit 89a30de）：发布 JSON 顶层携带 gazetteer；地图新增「地名检索」面板（实时搜索、古今别名命中、同名消歧注释置顶展示、点击聚焦高亮）；`#place=` 深链升级为 gazetteer 精确命中优先。
- [ ] 接入扫描件/地方志现成 OCR 批处理管线（如 PaddleOCR / MinerU 转 Markdown 后结构化抽取），补全陕北地方志与红军标语档案。
- [ ] 补全敌军（国民党军围堵体系、抗联对日军节点）与烈士纪念设施坐标精校。
- [ ] 完善英文化覆盖与无障碍访问，支撑长期公开展示与外部研究者协作贡献。
- [ ] 剩余 40 条 `low` 线索的定点核实（多为 1933–1935 陕甘根据地建设史与红七军团闽赣转战细节，需补地方志与党史专著）。

