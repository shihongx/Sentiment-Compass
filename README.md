# 舆情罗盘（Sentiment Compass）

基于 OpenClaw 的 AI 舆情叙事分析系统，从“发生了什么”进一步追问“媒体和平台为什么这样讲述”。

## 项目亮点

- 多平台采集：百度热搜、微博热搜、知乎热榜、头条热榜
- 三层去重：单平台聚类、跨平台合并、多次采集间追加去重
- 入池有上限：每轮只把 RRF 排序后的 TOP5 事件写入当天事件池，避免把低热度长尾全部塞入库中
- 全量分析：分析和日报都覆盖当天累计事件池里的全部事件，而不是只看某一轮的 TOP5
- 叙事分析：五类媒体框架、八类归因主体、冲突度评估、态势研判
- 自动运行：10:00 与 18:00 采集，23:00 先采集再分析再生成日报

## 架构示意

```text
用户 / Cron 定时任务
    ↓ 自然语言指令
OpenClaw Agent → 触发 sentiment-compass Skill
    ↓
Phase 1: 多源采集 + 三层去重 + RRF TOP5 入池
    ↓
cleaned/{date}_events.json  当天累计事件池（只增不减）
    ↓
Phase 2: web_search 多源摘要 + LLM 叙事框架分析
    ↓
analyzed/{date}_analysis.json  当天覆盖更新
    ↓
Phase 3: 日报生成
    ↓
reports/{date}_daily_report.md  当天覆盖更新
```

## 工作原理

本项目把“一天的舆情”视为逐步积累的过程，而不是单次快照。

示例：

```text
10:00 采集 → 本轮 TOP5：A B C D E → 事件池：A B C D E
18:00 采集 → 本轮 TOP5：A B D F G → 事件池：A B C D E F G
23:00 采集 → 本轮 TOP5：A F G H I → 事件池：A B C D E F G H I
```

其中：

- 每轮先从四个平台各抓取 15 条热榜标题
- 先做单平台聚类，再做跨平台合并
- 用 `score = Σ(1/(10 + rank_i))` 计算 RRF，取本轮前 5 个事件入池
- 入池时与当天已有事件做语义合并：重复则更新，不重复则追加，旧事件不删除
- 分析与日报始终面向当天事件池中的全部事件

## 目录结构

```text
sentiment-compass/
├── sentiment-compass-skill/
│   ├── SKILL.md
│   ├── scripts/
│   │   └── fetch_hotlists.py
│   ├── references/
│   │   └── framework-guide.md
│   └── templates/
│       ├── collect-output.md
│       ├── analyze-output.md
│       └── report-template.md
├── setup.sh
├── cron-setup.sh
└── README.md
```

## 环境要求

- 阿里云轻量应用服务器或无影云电脑
- Linux 环境，已安装 OpenClaw 最新版
- Python 3，仅依赖标准库
- 已启用 Tools：`read`、`write`、`exec`、`web_search`、`web_fetch`
- 已配置可用的 `web_search` 提供商
- 推荐模型：通义千问 `qwen-plus` 或 DeepSeek 系列

## 快速开始

```bash
git clone <your-repo>
cd sentiment-compass
bash setup.sh
bash cron-setup.sh
```

## Skill 触发示例

- `采集今日舆情`
- `看看今天有什么热点`
- `分析今日舆情`
- `做一份叙事分析`
- `生成今日舆情日报`

## 执行逻辑

- 采集任务：仅执行 Phase 1，展示本轮采集 TOP5 和本次新增事件
- 分析任务：始终先执行 Phase 1，再对当天累计全部事件执行 Phase 2
- 日报任务：始终先执行 Phase 1，再执行 Phase 2，最后生成 Phase 3 日报

分析文件与日报文件都是“同日单文件覆盖更新”，不会因为文件已存在就跳过重新生成。

## 数据文件说明

- `raw/{date}/hotlists_HHMM.json`
  原始热榜抓取结果，每轮一份
- `cleaned/{date}_events.json`
  当天累计事件池，追加合并去重
- `analyzed/{date}_analysis.json`
  当天分析结果，覆盖更新
- `reports/{date}_daily_report.md`
  当天日报，覆盖更新

## 设计取舍

- 为什么不把一轮采集的全部事件都入池：
  因为比赛场景更关注“当轮跨平台共同凸显的热点”，所以先用 RRF 聚合，再只保留本轮 TOP5 入池，减少长尾噪声。
- 为什么分析和日报要全量：
  因为一天不同时间段的热点可能完全不同，既然事件池采用追加机制，就应让分析和日报覆盖全部累计事件，避免遗漏。
- 为什么分析和日报每次都先采集：
  因为上一次采集之后，热搜可能已经变化。先采一轮，才能把最新热点补进当天事件池。

## Token 粗估

- Phase 1：约 2,500 tokens
- Phase 2：按 8 个事件估算约 8,000 tokens
- Phase 3：约 4,000 tokens
- 每日总量：约 25,000 tokens

## License

MIT
