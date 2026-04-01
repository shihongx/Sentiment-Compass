---
name: sentiment-compass
description: 舆情罗盘。采集多平台舆情热点、智能去重聚合、分析叙事框架和归因逻辑、生成舆情日报。当用户提到“采集舆情”“分析舆情”“舆情日报”“舆情报告”“今日热点”“叙事分析”“归因分析”“舆情罗盘”“舆情监测”“看看热搜”时使用。
version: 1.0.0
author: sentiment-compass-team
---

# 舆情罗盘

先按用户意图判定执行范围：

| 触发语义 | 执行范围 |
|---|---|
| 含“采集”“热点”“热搜”，且不含“分析”“叙事”“归因”“日报”“报告” | 仅 Phase 1 |
| 含“分析”“叙事”“归因” | Phase 1 → Phase 2 |
| 含“日报”“报告” | Phase 1 → Phase 2 → Phase 3 |

分析和日报任务都必须先重新执行 Phase 1，再处理后续阶段；不要因为今天已采集、已分析或已生成日报而跳过。

## Phase 1：采集、去重、入池

1. 用 `exec` 创建目录并执行脚本：
   ```bash
   mkdir -p ~/.openclaw/workspace/data/raw/$(date +%Y-%m-%d) ~/.openclaw/workspace/data/cleaned ~/.openclaw/workspace/data/analyzed ~/.openclaw/workspace/data/reports
   python3 {baseDir}/scripts/fetch_hotlists.py --output ~/.openclaw/workspace/data/raw/$(date +%Y-%m-%d)/hotlists_$(date +%H%M).json
   ```
2. 用 `read` 读取脚本输出。若脚本失败或有效条目少于 5 条，用 `web_search` 搜索“今日热搜 重大新闻”“微博热搜 今天”补足候选标题。
3. 先做单平台内语义聚类：同一核心事实合并，不同核心事实分开。例：“品牌被曝质量问题”与“品牌回应质量问题”合并；“外交部回应强闯事件”与“外交部回应外交等级”分开。
4. 再做跨平台语义合并，记录出现平台与原始条目。按 `score = Σ(1/(10 + rank_i))` 计算 RRF 分数并排序。
5. 只保留“本轮排序后的 TOP5 事件”作为本次入池候选。不要把本轮所有热搜或所有聚类结果都写入事件库。
6. 读取 `~/.openclaw/workspace/data/cleaned/{今日日期}_events.json`。将“本轮 TOP5 候选”与“当日已有事件库”再做同一核心事实匹配：
   - 匹配上：合并 `platforms_appeared`、`related_items`、`rrf_score`，保留原 `first_seen`
   - 没匹配上：追加为新事件
   - 旧事件本轮未出现：保留，不删除
7. 重排当日事件库并更新 `collection_runs`、`last_updated`、`total_events`，再用 `write` 覆盖保存到 `~/.openclaw/workspace/data/cleaned/{今日日期}_events.json`。顶层字段至少包含 `date,last_updated,collection_runs,total_events,events,last_batch_top5,last_batch_new_events`。每个事件至少包含 `event_id,event_name,platforms_appeared,platform_count,rrf_score,first_seen,last_seen,related_items`。
8. 输出时读取 `{baseDir}/templates/collect-output.md` 作为格式参考。展示的是“本次采集得到并入池前的 TOP5”，不是“当日累计事件库 TOP5”。`本次新增事件` 仅列出这次 TOP5 中此前不在当日事件库里的事件；若无新增可写“无新增”。
9. 若执行范围仅为 Phase 1，结束；否则继续。

## Phase 2：全量事件叙事分析

1. 先完成 Phase 1，再读取最新的 `~/.openclaw/workspace/data/cleaned/{今日日期}_events.json`。
2. 分析对象是“当日累计事件库中的全部事件”，不限 5 个，不得只按热度截断。
3. 对每个事件执行 `web_search "{event_name}"`，优先取约 5 条搜索结果的 `title/source/snippet/url`；不要用 `web_fetch` 抓取完整网页正文。
4. 对每个结果判断：`primary_frame`（冲突/人情味/责任归因/经济后果/道德）、`stance`（批评/支持/中立/观望）、`core_argument`（不超过 30 字）、`sentiment_intensity`（1-5）、`attribution_target`（政府/企业/个人/制度/技术/社会/自然/不明确）。需要细则时再 `read {baseDir}/references/framework-guide.md`。
5. 对每个事件输出归因矩阵：`frame_distribution`、`attribution_counts`、`dominant_attribution`、`conflict_level`、`conflict_reason`，并给出 `situation_assessment`：`phase`、`risk_level`、`trend_prediction`。
6. 用 `write` 覆盖保存 `~/.openclaw/workspace/data/analyzed/{今日日期}_analysis.json`。同一天始终只有这一份分析文件；即使文件已存在，也必须基于最新事件库重新生成覆盖。
7. 输出时读取 `{baseDir}/templates/analyze-output.md` 作为格式参考。摘要里可重点展示关键事件，但底层分析结果必须覆盖当天累计的全部事件。
8. 若不需要日报，到此结束；否则继续。

## Phase 3：日报生成

1. 日报任务必须执行 Phase 1 → Phase 2，再读取 `~/.openclaw/workspace/data/analyzed/{今日日期}_analysis.json` 和 `{baseDir}/templates/report-template.md`。
2. 报告内容必须覆盖当日累计事件库里的全部已分析事件，不得只写 Top5。
3. 用模板生成 Markdown 日报，百分比使用整数，表格使用 Markdown，风险保留 emoji 标记，结尾追加：`📌 本报告由舆情罗盘基于 OpenClaw 自动生成 | {时间}`。
4. 用 `write` 覆盖保存到 `~/.openclaw/workspace/data/reports/{今日日期}_daily_report.md`。同一天始终只有这一份日报文件；即使文件已存在，也必须重新生成覆盖。
5. 向用户输出完整日报，并注明保存路径。
