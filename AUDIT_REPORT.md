# 项目审计报告

## 当前状态

本文件不再手工维护 subjects / sources / events / persons / museum / visual assets 的具体数量。数据表持续增长时，静态数字很容易与真实仓库状态漂移。

当前数量与一致性以以下命令的实时输出为准：

```bash
python tools/check_project.py
```

当前审计模型把几类问题分开处理：

- **工程一致性**：`data_edit/*.csv` 必须完整复现 `data/long_march_events.json`。
- **引用完整性**：事件、人物、展板、档案等引用的 source / person / event / hall id 必须存在。
- **候选材料边界**：仅由本地游戏文本抽取来源支持的公开事件必须保持 `certainty=low`。
- **第三方材料边界**：原始游戏文本与解包材料必须留在忽略的 `research_private/`。
- **图片 provenance**：外部图片如果仍只有 `see file page` 等泛化许可信息，会继续作为 provenance 警告，不会被误标为已清权。
- **史实/解释边界**：自动化检查不替代人工史料审校，也不把地图坐标或概括性路线当成精确历史重建。

更完整的状态见 [PROVENANCE_STATUS.md](PROVENANCE_STATUS.md)。

## 已建立的工程门禁

- `python tools/check_project.py`：
  - 必需文件；
  - 发布 JSON 结构；
  - CSV → JSON 可复现性；
  - Python / JavaScript 语法；
  - 后台事件绑定约束；
  - 来源登记必要字段；
  - 游戏文本候选的低确定性约束；
  - 外部图片许可/credit 完整度报告；
  - 英文占位内容提示。
- GitHub Actions `Quality`：
  - 在干净环境运行完整项目检查；
  - 确认 `research_private/` / `steam_text_dump/` 没有被 Git 跟踪；
  - 检查公开仓库中的 canonical identity。

## 历史修订摘要

已完成的主要工程重构包括：

1. 后台从 inline handler 改为事件委托。
2. 后台数据加载失败显式报错。
3. 建立表格 → JSON 的确定性构建与检查。
4. 建立数字博物馆、人物时间线、展厅/展板/档案数据层。
5. 建立本地 Steam / Unreal 文本抽取与候选导入流程。
6. 将原始第三方抽取材料隔离到 `research_private/`。
7. 为图片资产保留来源页、credit、license 字段。
8. 增加 AGENTS / HANDOFF / STATUS / DECISIONS / architecture / provenance 文档，支持跨 Agent 持续维护。

## 仍需人工推进

- 为仅有候选来源的条目逐步补入独立来源，或继续保持低确定性。
- 对外部图片逐文件补齐精确许可证、作者/机构与 attribution；无法核实的素材应在发布前替换或移除。
- 对地图坐标、概括性路线和英文策展文案继续人工复核。
- 对新增史料、解释性文案和第三方材料执行人工来源/版权审校。

工程检查通过只表示仓库契约通过，不表示历史解释、版权许可或事实核验已经全部完成。
