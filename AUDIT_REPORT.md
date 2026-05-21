# 项目审计报告

## 当前状态

- subjects：22 个，其中包含 `enemy_kmt` 敌军动向叙事层。
- sources：37 个，来源保留在数据中用于审校，前台不展示。
- events：140 条。
- persons：35 个种子人物档案。
- personEvents：95 条人物-事件关联。
- museum：10 个展厅、10 个展板、5 个档案/物件类展品、22 条图片资产。
- `data_edit/*.csv` 可以完整复现 `data/long_march_events.json`。
- 英文模式已补齐 `titleEn`、`descriptionEn`、`location.nameEn`，不再使用混入中文地名的模板英文。

## 本轮修订

1. 后台移除 inline `onclick`，改为 `data-action` 加事件委托。
2. 后台加载数据失败时显示明确错误页，不再静默空白。
3. 新增 `tools/check_project.py`，统一校验 JSON、CSV 生成一致性、JS 语法和后台 inline 事件绑定。
4. 新增 `tools/check_project.bat` 与 `tools/check_project.sh`，方便本地一键检查。
5. 批量补齐 138 条事件地点英文名，并替换 103 条模板英文标题/描述。
6. 从 `css/style.css` 中移除 v13-v18 旧事件卡覆盖块，保留 v19-v21 当前设计层，减少样式覆盖链。
7. 新增 `museum.html`、`css/museum.css`、`js/museum.js`，形成线上数字博物馆入口。
8. 新增 `persons.csv`、`person_events.csv`、`museum_halls.csv`、`exhibits.csv`、`artifacts.csv`，将人物时间线和展馆层级纳入数据生成流程。
9. 新增 `tools/extract_steam_texts.py` 及启动脚本，用于从本机 Steam 游戏目录导出可审校文本。
10. 新增并扩展 `visual_assets.csv`，为数字博物馆接入 Commons 图片和本地运行截图，并保留来源页、署名和许可说明。
11. 补充洪超、谢子长、罗南辉、程翠林、蔡中等牺牲人物，以及女红军、各路指挥员、政治工作和根据地建设人物。
12. 数字博物馆新增“策展路径”“暗线代价”“策展方法”和人物类型筛选，按“明线路线、人物透镜、暗线代价、证据层”组织。
13. 删除未引用的旧截图 `docs/screenshot.png` 和 `docs/screenshot-en.png`。

## 已验证

- `python tools/check_project.py` 通过。
- `node --check js/app.js` 通过。
- `node --check js/museum.js` 通过。
- `node --check admin/admin.js` 通过。
- `python tools/build_json_from_tables.py` 可重新生成发布 JSON。
- `python -m py_compile tools/build_json_from_tables.py tools/check_project.py tools/extract_steam_texts.py` 通过。
- `python -m json.tool data/long_march_events.json` 通过。

## 仍需人工审校

- 敌军路线仍是概括性叙事层，不代表精确军事部署图。
- 地点经纬度是可视化近似点，建议后续按史料逐点复核。
- 英文文案已消除模板占位和中英混杂，但部分事件仍适合继续做人工润色。
- 可继续补充女性红军、卫生队、宣传队、少数民族向导、地方群众支援等微观叙事节点。
- 数字博物馆目前使用种子人物和展板结构，后续应继续按来源补充烈士、地方群众、纪念设施和实物档案。
- Steam 游戏抽取出的文本只应作为个人整理线索，正式入库前仍需核对版权、来源和史实准确性。
