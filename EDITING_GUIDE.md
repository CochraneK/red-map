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

## 6. 生成 JSON

Windows 下双击：

```text
tools/build_json_from_tables.bat
```

或在项目根目录运行：

```cmd
python tools\build_json_from_tables.py
```

## 7. 启动网页

Windows 下双击：

```text
start_server.bat
```

CMD 会显示链接，并自动打开：

```text
http://localhost:8000/
```

后台地址：

```text
http://localhost:8000/admin/index.html
```
