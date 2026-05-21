# Steam 游戏文本抽取流程

本流程用于从本机 Steam 游戏《长征1934-1936》中抽取文本线索，辅助丰富 `red-map` 长征时间线。原始游戏文本属于第三方内容，应保留在 `research_private/`，不要直接发布到公开站点；进入 `data_edit/events.csv` 前，应先用党史资料、地方志、纪念馆页面或权威文献复核，并改写为策展条目。

## 已确认的游戏结构

本机路径：

```powershell
D:\Software\Steam\steamapps\common\长征1934-1936\长征1934-1936
```

这是 Unreal Engine 4 项目，核心内容在：

```powershell
ChangZheng\Content\Paks\ChangZheng-WindowsNoEditor.pak
```

已用 `repak` 确认该 PAK：

- `version: V11`
- `encrypted index: false`
- `2265 file entries`
- 重点数据文件在 `ChangZheng/Content/Data/`

## 解包 PAK

如果 `research_private/tools/repak/repak.exe` 不存在，先下载开源工具：

```powershell
$tools = 'D:\Software\codex\red-map\research_private\tools'
New-Item -ItemType Directory -Force -Path $tools | Out-Null
$zip = Join-Path $tools 'repak_cli-x86_64-pc-windows-msvc.zip'
Invoke-WebRequest -Uri 'https://github.com/trumank/repak/releases/download/v0.2.2/repak_cli-x86_64-pc-windows-msvc.zip' -OutFile $zip
Expand-Archive -LiteralPath $zip -DestinationPath (Join-Path $tools 'repak') -Force
```

只解包与文本相关的数据资产：

```powershell
D:\Software\codex\red-map\research_private\tools\repak\repak.exe unpack -f -q `
  -o "D:\Software\codex\red-map\research_private\steam_longmarch_unpacked" `
  -i "ChangZheng/Content/Data" `
  -i "ChangZheng/Config" `
  -i "ChangZheng/Content/HUD/UI/scene/certainEvent" `
  "D:\Software\Steam\steamapps\common\长征1934-1936\长征1934-1936\ChangZheng\Content\Paks\ChangZheng-WindowsNoEditor.pak"
```

## 抽取 Unreal 文本

优先使用专门的 FString 抽取脚本，而不是普通二进制 `strings`。普通扫描会混入大量引擎资源名和压缩噪声。

```powershell
python tools\extract_unreal_text_assets.py `
  "D:\Software\codex\red-map\research_private\steam_longmarch_unpacked\ChangZheng\Content\Data" `
  --exclude-glob "StopWords.*" `
  --out "D:\Software\codex\red-map\research_private\steam_longmarch_unreal_text_timeline" `
  --markdown-limit-per-file 500
```

本次抽取结果：

- 扫描数据资产：36 个
- 抽取中文字符串：5905 条
- 生成时间线候选：1028 条
- 主要内容来源：`Script*.uexp`、`Army.uexp`、`Map.uexp`、`CertainEvent.uexp`、`End.uexp`

输出文件：

- `unreal_text_dump.jsonl`：完整抽取文本，适合程序处理。
- `unreal_text_dump.csv`：完整抽取文本，适合表格查看。
- `unreal_text_dump.md`：人工预览。
- `unreal_asset_manifest.csv`：每个资产抽取数量。
- `unreal_timeline_candidates.csv`：按“日期行 + 后续叙述”生成的时间线候选。

## 已融入 red-map 的批次

当前仓库已通过 `tools/import_steam_timeline.py` 筛选 `unreal_timeline_candidates.csv`，并把 `246` 条候选改写为短策展事件，写入 `data_edit/events.csv`：

- 这些事件统一使用来源 `src_steam_longmarch_1934_1936`。
- `certainty` 统一为 `low`，用于提醒后续还需要权威资料复核。
- 原始游戏文本仍留在 `research_private/`，公开数据只保留压缩改写后的短条目。
- 本批次覆盖中央红军、红二十五军、红四方面军、红二/六军团、陕甘红军和红七军团北上抗日先遣队。
- 同一脚本还补入 `32` 个 Steam 文本人物、`253` 条人物-事件自动关联，并为可确认公开来源的 `18` 个人物补入 Wikimedia Commons 图片。

复用流程：

```powershell
python tools\import_steam_timeline.py
python tools\import_steam_timeline.py --apply
python tools\build_json_from_tables.py
python tools\check_project.py
```

## 进入 red-map 前的处理规则

1. 先打开 `unreal_timeline_candidates.csv`，筛选具体时间、地点、人物、部队、行动结果明确的条目。
2. 用权威资料复核日期与事实。游戏文本只作为线索，不作为唯一来源。
3. 改写为短策展文案，避免直接长段复制游戏原文。
4. 补齐 `data_edit/events.csv` 需要的字段：`id`、`date`、`displayDate`、`forceId`、`type`、`title`、`description`、`locationName`、经纬度、`sourceIds`、`certainty`。
5. 对涉及人物的条目，再补 `data_edit/person_events.csv`，把人物角色和事件关联起来。

## 相关脚本

- `tools/extract_steam_texts.py`：通用 Steam 文本/二进制候选扫描。
- `tools/extract_unreal_text_assets.py`：Unreal `.uasset/.uexp/.umap` FString 抽取，适合本项目。
- `tools/import_steam_timeline.py`：将抽取候选筛选、匹配地点、压缩改写并导入 `data_edit/events.csv`。
