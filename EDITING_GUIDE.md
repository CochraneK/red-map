# 数据编辑说明

本项目推荐使用“表格编辑 → 自动生成 JSON”的维护方式。

## 1. 前台读取哪个文件

网页只读取：

```text
data/long_march_events.json
```

## 2. 人工编辑哪些表格

建议优先编辑：

```text
data_edit/events.csv      # 事件、人物事迹、战役、会议、会师、诗句触发点
data_edit/subjects.csv    # 部队/路线/人物主体
data_edit/persons.csv     # 人物档案
data_edit/person_events.csv # 人物与事件关联
data_edit/museum_halls.csv  # 数字博物馆展厅层级
data_edit/exhibits.csv      # 展板
data_edit/artifacts.csv     # 档案、物件、纪念设施类展品
data_edit/visual_assets.csv # 线上图片 URL、来源页、署名和许可说明
data_edit/sources.csv     # 资料来源，仅用于审校，前台不显示
data_edit/metadata.csv    # 项目标题、时间范围
```

## 3. 日期格式

表格中建议统一写成 `YYYYMMDD`，例如：

```text
19350115
19361022
```

生成 JSON 时，脚本会自动转换为机器更稳定的 ISO 格式：

```text
1935-01-15
1936-10-22
```

后台添加事件时也使用 `YYYYMMDD` 输入，前台显示为中文日期。

## 4. 新增事件

在 `events.csv` 增加一行即可。常用字段如下：

| 字段 | 说明 |
|---|---|
| enabled | TRUE/FALSE，是否启用 |
| id | 可留空，脚本自动生成 |
| date | 日期，建议 YYYYMMDD |
| forceId | 所属部队/路线，必须存在于 subjects.csv |
| type | 两字类型，如 战役、会议、牺牲、会师、民族、根据 |
| title | 事件标题 |
| description | 事件说明 |
| titleEn / descriptionEn / locationNameEn | 英文页面显示字段，建议同步维护 |
| locationName / lat / lng | 地点和坐标 |
| participants | 人物，用分号分隔 |
| redJoined | 参征人数增量，可空 |
| redLosses | 损失人数估算，可空 |
| enemyDefeated | 歼俘敌估算，可空 |
| distanceLi | 中央红军里程节点，可空 |
| victory | TRUE/FALSE，是否计为胜利节点 |
| poemLine / poemTitle / poemText | 七律长征诗句触发卡片 |

## 5. 新增部队/路线或人物

在 `subjects.csv` 增加一行。若 `type=force`，该主体会出现在前台路线开关和事件编辑下拉框中；若 `type=person`，主要用于资料管理。

部队颜色由 `color` 字段控制。前台地图路线和节点统一按部队颜色显示，不再按事件类型上色。

## 6. 维护人物时间线

人物时间线由两张表组成：

```text
data_edit/persons.csv
data_edit/person_events.csv
```

先在 `persons.csv` 中维护人物基本档案，再在 `person_events.csv` 中把人物 `personId` 关联到已有事件 `eventId`。如果某个人物缺少关键节点，应先在 `events.csv` 中补充事件，再建立关联。这样路线地图、英烈墙和人物时间线会共用同一套事件数据。

常用字段：

| 表格 | 字段 | 说明 |
|---|---|---|
| persons.csv | id | 人物唯一 ID |
| persons.csv | personType | 如 `烈士`、`领导人`、`女红军` |
| persons.csv | forceId | 所属路线，必须存在于 subjects.csv 的 force |
| persons.csv | themeTags | 标签，用分号分隔 |
| person_events.csv | personId | 对应 persons.csv |
| person_events.csv | eventId | 对应 events.csv |
| person_events.csv | note | 该人物在此节点的叙事说明 |

## 7. 维护数字博物馆展板

数字博物馆页面为 `museum.html`。展厅层级在 `museum_halls.csv` 中维护；展板在 `exhibits.csv` 中维护；档案、物件、纪念设施类内容在 `artifacts.csv` 中维护。

`red-map` 路线地图作为第一展厅的展板，使用 iframe 嵌入 `index.html`。其他展板通过 `relatedEventIds` 和 `relatedPersonIds` 连接到事件与人物档案。

图片资产在 `visual_assets.csv` 中维护。`targetType` 支持 `hero`、`hall`、`exhibit`、`event`、`person`、`artifact`；`targetId` 必须对应相应表中的 ID。新增网上图片时，应同时填写 `imagePageUrl`、`credit` 和 `license`，方便上线前审校版权与来源。

建议的扩展顺序：

1. 先在 `events.csv` 补足史实节点。
2. 再在 `persons.csv` 和 `person_events.csv` 建人物时间线。
3. 在 `visual_assets.csv` 给关键展板、地点和人物补图。
4. 最后在 `exhibits.csv` 或 `artifacts.csv` 组织展板叙事。

## 8. 抽取 Steam 本地文本

在 Steam 客户端中对游戏选择“管理 → 浏览本地文件”，复制游戏目录路径，然后运行：

```cmd
python tools\extract_steam_texts.py "D:\SteamLibrary\steamapps\common\Long March 1934-1936" --include-binary
```

输出目录默认为 `steam_text_dump/`，其中 `steam_text_dump.jsonl` 是全量文本，`steam_text_dump.md` 便于人工快速浏览，`steam_text_manifest.csv` 记录扫描到的文件。导入项目之前，应先人工审校版权、来源和史实口径。

## 9. 生成 JSON

Windows 下双击：

```text
tools/build_json_from_tables.bat
```

或在项目根目录运行：

```cmd
python tools\build_json_from_tables.py
```

生成后建议继续运行：

```cmd
python tools\check_project.py
```

该命令会检查表格源文件是否能完整复现发布 JSON，并检查前后台脚本语法。

## 10. 启动网页

Windows 下双击：

```text
start_server.bat
```

CMD 会显示链接，并自动打开数字博物馆：

```text
http://localhost:8000/museum.html
```

后台地址：

```text
http://localhost:8000/admin/index.html
```
