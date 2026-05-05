# 红军长征星火路线

一个以“星火铺开、分路前进、最终会师”为叙事逻辑的红军长征交互式路线项目。项目强调多路红军各自成线、全局时间顺序播放、同一路线独立连线，并通过会师红旗、人物事迹、战役会议、敌军围追堵截示意线，呈现长征过程中的艰险、牺牲与汇流。

![项目首页预览](docs/readme-home.png)

<p align="center">
  <img src="docs/readme-mobile.png" alt="手机端预览" width="260" />
</p>

## 功能特性

- **多路线并行**：红一方面军、红二十五军、红四方面军、红二方面军、陕甘红军分别独立连线，国民党军作为半透明灰色追堵线。
- **全局时间播放**：底部时间轴按事件时间顺序推进，但地图连线只连接同一路线的连续节点。
- **会师红旗特效**：凡涉及会师的事件，地图上会浮现红旗，经过淡入、轻微抖动、静止、淡出后继续播放。
- **统一军团颜色**：每一路线固定颜色，人物、战役、会议、牺牲等事件都继承所在路线颜色。
- **下属部队展示**：右侧路线面板展示各路红军下属部队，采用小型标签，不额外设置勾选项。
- **中英文版本**：中文首页 `index.html`，英文页面 `index-en.html`，也可在页面右上角切换语言。
- **手机端极简模式**：手机端只保留地图与底部播放条，避免卡片遮挡地图。
- **本地数据编辑器**：后台可编辑事件、主体、颜色、下属部队和统计字段，并支持导出 JSON。

## 数据管理界面

后台用于本地整理事件、主体、颜色、下属部队和统计字段。它不会直接写入线上文件；编辑后需要导出 JSON 并替换 `data/long_march_events.json`。

![数据管理界面预览](docs/readme-admin.png)

## 快速启动

Windows 用户直接双击：

```bat
start_server.bat
```

CMD 会显示：

```text
Chinese home page:
http://localhost:8000/

English page:
http://localhost:8000/index-en.html

Admin panel:
http://localhost:8000/admin/index.html
```

macOS / Linux 用户可运行：

```bash
./start_server.sh
```

## 数据维护方式

推荐编辑表格源文件，而不是直接手写 JSON：

```text
data_edit/events.csv      # 事件主表
data_edit/subjects.csv    # 主体、路线、颜色、下属部队
data_edit/sources.csv     # 资料来源，前台不显示
data_edit/metadata.csv    # 项目标题、时间范围等
```

编辑后运行：

```bash
python tools/build_json_from_tables.py
```

脚本会生成：

```text
data/long_march_events.json
```

## 日期格式

表格中统一使用 `YYYYMMDD`，例如：

```text
19350115
```

生成 JSON 时会自动转换为：

```text
1935-01-15
```

## 目录结构

```text
.
├── index.html                    # 中文首页
├── index-en.html                 # 英文页面
├── css/style.css                 # 前台样式
├── js/app.js                     # 前台交互逻辑
├── data/long_march_events.json   # 前台读取的数据文件
├── data_edit/                    # 人工维护表格
├── admin/                        # 本地数据编辑器
├── tools/                        # 表格转 JSON 脚本
├── docs/readme-home.png          # 首页展示图
├── docs/readme-home-en.png       # 英文首页展示图
├── docs/readme-mobile.png        # 手机端展示图
├── docs/readme-admin.png         # 数据管理展示图
└── start_server.bat              # Windows 一键启动
```

## 发布到 GitHub Pages

1. 将整个项目提交到 GitHub 仓库。
2. 在仓库设置中启用 GitHub Pages。
3. 选择 `main` 分支和根目录 `/` 作为发布源。
4. 发布后访问仓库生成的 Pages 地址即可。

如果线上页面仍显示旧样式，请清理浏览器缓存，或确认最新的 `css/style.css` 和 `docs/` 图片已经提交到仓库。

## 注意事项

- 敌军路线是概括性叙事层，用于表现围追堵截压力，不代表精确军事部署图。
- 前台不显示参考来源，但 `sourceIds` 会保留在数据中，方便后续审校。
- 手机端采用极简展示，主要用于浏览路线和播放时间轴；完整筛选与数据管理建议在桌面端使用。

---

# Long March Spark Routes

An interactive Long March route project built around the narrative logic of scattered revolutionary “sparks,” multiple marching columns, pursuit and blockade, and final convergence in the northwest. The project keeps each Red Army route visually independent while preserving a global chronological playback order.

![Desktop preview](docs/readme-home-en.png)

<p align="center">
  <img src="docs/readme-mobile.png" alt="Mobile preview" width="260" />
</p>

## Features

- **Parallel route layers**: Red First Front Army, Red Twenty-Fifth Army, Red Fourth Front Army, Red Second Front Army, and the Shaanxi-Gansu Red Army are drawn as separate routes. Nationalist pursuit and blockade are shown as a semi-transparent grey layer.
- **Global timeline, route-specific lines**: Events play in chronological order, while map lines only connect consecutive nodes within the same route.
- **Convergence flag effect**: Every convergence event triggers a red flag animation with fade-in, subtle shake, a short hold, and fade-out before playback continues.
- **Route-based color system**: Each route keeps one consistent color. Battles, meetings, sacrifices, people-related events, and other nodes inherit the color of their route.
- **Sub-unit display**: The right-side route panel lists smaller sub-units as compact tags without adding extra checkboxes.
- **Bilingual pages**: Chinese page at `index.html`, English page at `index-en.html`, plus an in-page language switcher.
- **Mobile minimal mode**: On mobile, only the map and bottom playback bar are shown so cards do not cover the route.
- **Local data editor**: The admin panel allows editing events and subjects, then exporting JSON.

## Data Editor

The data editor is designed for local curation of events, subjects, route colors, sub-units, and metrics. It does not directly write to deployed files; export JSON and replace `data/long_march_events.json` after editing.

![Data editor preview](docs/readme-admin.png)

## Quick Start

On Windows, double-click:

```bat
start_server.bat
```

The terminal will show:

```text
Chinese home page:
http://localhost:8000/

English page:
http://localhost:8000/index-en.html

Admin panel:
http://localhost:8000/admin/index.html
```

On macOS / Linux:

```bash
./start_server.sh
```

## Data Maintenance

Edit the table source files instead of manually editing JSON:

```text
data_edit/events.csv      # Event table
data_edit/subjects.csv    # Route subjects, colors, and sub-units
data_edit/sources.csv     # Sources retained for audit; not shown on the frontend
data_edit/metadata.csv    # Project title and time range
```

Then run:

```bash
python tools/build_json_from_tables.py
```

The script generates:

```text
data/long_march_events.json
```

## GitHub Pages

1. Push the project to a GitHub repository.
2. Enable GitHub Pages in repository settings.
3. Select the `main` branch and root `/` as the publishing source.
4. Open the generated Pages URL after deployment.

If the deployed page still shows old styling, clear browser cache and confirm that the latest `css/style.css` and `docs/` images have been pushed.
