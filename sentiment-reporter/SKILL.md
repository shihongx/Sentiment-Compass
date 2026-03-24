---
name: sentiment-reporter
description: 生成舆情日报、舆情报告、舆情总结。当用户说"生成日报""舆情报告""舆情总结""输出今日舆情"时使用。不用于采集或分析数据。
version: 1.0.0
author: sentiment-compass-team
---

# 舆情日报生成 Skill

读取叙事分析结果，按模板生成结构化 Markdown 格式舆情日报。

## 适用场景

- 用户说"生成舆情日报""输出今日舆情报告""生成舆情总结"
- 定时任务消息包含"生成日报"或"推送报告"

**不适用于**：采集数据（使用 sentiment-collector）、分析数据（使用 narrative-analyzer）。

## 前置检查（必须先执行）

在生成报告之前，检查全链数据是否就绪：

1. 用 `exec` 获取今日日期：`TODAY=$(date +%Y-%m-%d)`

2. **检查分析结果**：用 `read` 检查 `~/.openclaw/workspace/data/analyzed/${TODAY}_analysis.json` 是否存在。

3. 如果分析结果 **存在** → 跳到下方"执行步骤"。

4. 如果分析结果 **不存在** → 需要按顺序补链执行：

   **补链第一步：采集数据**
   - 检查 `~/.openclaw/workspace/data/cleaned/${TODAY}_collected.json` 是否存在。
   - 如果不存在：
     a. `exec` 运行：`mkdir -p ~/.openclaw/workspace/data/raw/$TODAY ~/.openclaw/workspace/data/cleaned`
     b. `exec` 运行：`python3 ~/.openclaw/workspace/skills/sentiment-collector/scripts/fetch_hotlists.py --output ~/.openclaw/workspace/data/raw/$TODAY/hotlists.json`
     c. `read` 读取 hotlists.json，取热度前 5 话题。
     d. 对每个话题调用 `web_search`：`"{话题}" 最新报道 评论`。
     e. 合并去重，用 `write` 保存到 `~/.openclaw/workspace/data/cleaned/${TODAY}_collected.json`。

   **补链第二步：叙事分析**
   - `read` 读取 cleaned 数据。
   - 按 5 种叙事框架（冲突/人情味/责任归因/经济后果/道德）分析每条来源。
   - 生成归因矩阵和态势研判。
   - `exec` 运行：`mkdir -p ~/.openclaw/workspace/data/analyzed`
   - 用 `write` 保存分析结果到 `~/.openclaw/workspace/data/analyzed/${TODAY}_analysis.json`。

   **补链第三步**：继续执行下方报告生成步骤。

## 执行步骤

### Step 1 — 读取分析结果

用 `read` 读取 `~/.openclaw/workspace/data/analyzed/${TODAY}_analysis.json`。如果不存在，尝试最近 3 天的文件。都不存在则告知用户"未找到分析结果，请先运行舆情分析"。

### Step 2 — 读取报告模板

用 `read` 读取 `{baseDir}/templates/report-template.md`。

### Step 3 — 生成报告

按模板结构填充分析数据，规则：
- 所有百分比保留整数
- 归因矩阵用 Markdown 表格展示
- 风险等级用对应 emoji 展示
- 为每个高风险（橙色/红色）事件生成行动建议
- 报告末尾添加生成时间戳和声明

### Step 4 — 保存报告

用 `exec` 确保目录存在：`mkdir -p ~/.openclaw/workspace/data/reports`

用 `write` 将 Markdown 报告保存到：`~/.openclaw/workspace/data/reports/${TODAY}_daily_report.md`

### Step 5 — 输出报告

将完整报告内容作为回复发送给用户，在末尾补充：

```
📁 报告已保存至 data/reports/{TODAY}_daily_report.md
```

## 错误处理

- 分析结果文件格式异常 → 告知用户"分析数据损坏，请重新运行舆情分析"。
- 模板文件缺失 → 使用内置默认格式生成报告（标题 + 摘要 + 事件列表 + 风险表）。
- 补链过程中任一步骤失败 → 告知用户失败原因并给出手动修复建议。
