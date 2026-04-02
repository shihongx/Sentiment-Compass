# 舆情罗盘（Sentiment Compass）

> 一个面向 OpenClaw 的舆情叙事分析 Skill。  
> 用来自动采集多平台热点、聚合重复事件、补充搜索上下文，并生成可直接阅读或归档的舆情分析日报。

## 项目简介

`Sentiment Compass`（舆情罗盘）是一个为 OpenClaw 设计的中文舆情分析 Skill。

它不只回答“今天发生了什么”，还进一步关注：

- 不同平台在如何讲述同一件事
- 责任被归因给了谁
- 舆论冲突和风险可能如何演化

项目适合用于品牌公关、内容研究、热点观察、信息整理、日报生成等场景，也适合把 OpenClaw 部署为一名可持续工作的 AI 舆情分析助手。

## 它可以做什么

| 能力 | 说明 |
| --- | --- |
| 多平台热点采集 | 自动抓取百度热搜、微博热搜、知乎热榜、头条热榜 |
| 热点聚合去重 | 合并同一事件在不同平台或不同表述下的重复条目 |
| 叙事框架识别 | 识别事件在搜索结果与报道摘要中的主要叙事方式 |
| 归因与态势分析 | 判断责任指向、冲突强度、风险等级与趋势走向 |
| 日报自动生成 | 输出结构化分析结果，并生成 Markdown 舆情日报 |
| 定时运行 | 可结合 OpenClaw Cron 按固定时间自动采集与生成报告 |

## 仓库结构

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

部署本项目前，请先确保运行环境具备以下条件：

- 已安装并可正常使用 `OpenClaw`
- 具备 `bash` 运行环境
- 已安装 `Python 3`
- 运行环境可以访问互联网
- OpenClaw 已启用 `read`、`write`、`exec`、`web_search`、`web_fetch`
- OpenClaw 已配置可用的大模型与 `web_search` 提供能力

如果你希望自动定时运行，还需要 OpenClaw 的 `cron` 能力可用。

## 安装部署

```bash
git clone https://github.com/shihongx/Sentiment-Compass.git sentiment-compass
cd sentiment-compass
bash setup.sh
```

`setup.sh` 会完成以下工作：

- 将 Skill 部署到 `~/.openclaw/workspace/skills/`
- 初始化数据目录
- 检查 `openclaw` 与 `python3`
- 测试热榜采集脚本是否可运行

## 快速使用

在 OpenClaw 中安装完成后，可以直接使用自然语言触发 Skill，例如：

- `采集今日舆情`
- `看看今天有什么热点`
- `分析今日舆情`
- `做一份舆情叙事分析`
- `生成今日舆情日报`

## 定时任务

如果你希望让它自动运行，可以执行：

```bash
bash cron-setup.sh
```

默认会创建 3 个定时任务：

| 时间 | 任务 |
| --- | --- |
| `10:00` | 上午采集 |
| `18:00` | 傍晚采集 |
| `23:00` | 采集 + 分析 + 生成日报 |

常用管理命令：

```bash
openclaw cron list
openclaw cron run <job-id>
openclaw cron runs --id <job-id>
openclaw cron edit <job-id> --enabled false
openclaw cron remove <job-id>
```

## 输出文件

运行过程中会在 OpenClaw 工作目录下生成数据文件：

| 路径 | 说明 |
| --- | --- |
| `~/.openclaw/workspace/data/raw/{date}/hotlists_HHMM.json` | 原始热榜抓取结果 |
| `~/.openclaw/workspace/data/cleaned/{date}_events.json` | 当日聚合后的事件池 |
| `~/.openclaw/workspace/data/analyzed/{date}_analysis.json` | 当日事件分析结果 |
| `~/.openclaw/workspace/data/reports/{date}_daily_report.md` | 当日 Markdown 舆情日报 |
```
