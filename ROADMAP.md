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

### P2 · 存量信用清债与史料纵深开采

- [ ] **清理 219 条 `low` 游戏线索**：批量对照权威党史网核验——重复归并、错点下线、真事件补出处升级 `high`，目标 `low` 占比降至 **<10%**。
- [ ] **开采《红军长征记》剩余 ~90 篇**：基于 `29_红军长征记篇目索引.md`，采用统一 JSON Schema 批量抽取（强制带篇名、人物、县镇地名、原句定位），同步清零 31 位零关联人物。
- [ ] **视觉资产版权清债**：逐条核清 `visual_assets.csv` 中 34 张 `see file page` 图片的精确协议或替换为可验证公版素材。
- [ ] **县镇级历史地名词典（`data_edit/gazetteer.csv`）**：沉淀已核验的长征历史地名与坐标库，防止未来新增数据再次出现同名异地错配。
- **P2 硬验收标准**：`high + medium` 占比 ≥ 90%；零关联人物归零；未核清版权图片归零。

---

### P3 · 平台化持续运营与多专题扩展

- [ ] 接入扫描件/地方志现成 OCR 批处理管线（如 PaddleOCR / MinerU 转 Markdown 后结构化抽取），补全陕北地方志与红军标语档案。
- [ ] 补全敌军（国民党军围堵体系、抗联对日军节点）与烈士纪念设施坐标精校。
- [ ] 完善英文化覆盖与无障碍访问，支撑长期公开展示与外部研究者协作贡献。
