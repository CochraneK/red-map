# data_edit 表格源文件

这里的 CSV 是人工编辑源文件。

- `events.csv`：事件主表。
- `subjects.csv`：路线/主体表。
- `persons.csv`：人物档案表，用于英烈墙和人物时间线。
- `person_events.csv`：人物与事件的关联表，用于生成每个角色的发展时间线。
- `museum_halls.csv`：数字博物馆展厅层级。
- `exhibits.csv`：展板内容，`red-map` 路线地图也是其中一个展板。
- `artifacts.csv`：档案、物件、纪念设施等可继续扩展的展品。
- `visual_assets.csv`：线上图片资产，保留图片 URL、来源页、署名和许可说明。
- `sources.csv`：来源表。前台不显示来源，但用于史实审计。
- `metadata.csv`：项目标题、版本、时间范围。
- `lookups.csv`：可参考的事件类型、路线 ID 等。

修改后运行：

```bash
python ../tools/build_json_from_tables.py
```

生成 `../data/long_march_events.json`。

发布前回到项目根目录运行：

```bash
python tools/check_project.py
```

检查会确认表格重新生成的 JSON 与 `data/long_march_events.json` 完全一致。
