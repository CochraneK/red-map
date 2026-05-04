# data_edit 表格源文件

这里的 CSV 是人工编辑源文件。

- `events.csv`：事件主表。
- `subjects.csv`：路线/主体表。
- `sources.csv`：来源表。前台不显示来源，但用于史实审计。
- `metadata.csv`：项目标题、版本、时间范围。
- `lookups.csv`：可参考的事件类型、路线 ID 等。

修改后运行：

```bash
python ../tools/build_json_from_tables.py
```

生成 `../data/long_march_events.json`。
