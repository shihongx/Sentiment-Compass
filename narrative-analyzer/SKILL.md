---
name: narrative-analyzer
description: 分析舆情数据的叙事框架、归因逻辑和传播态势。当用户说"分析舆情""解读叙事框架""对比报道角度""归因分析"时使用。不适用于采集数据或生成报告。
version: 1.0.0
author: sentiment-compass-team
---

# 舆情叙事框架分析 Skill

对采集到的舆情数据执行三层分析：叙事框架识别 → 归因逻辑解构 → 态势研判。

## 适用场景

- 用户说"分析今日舆情""分析 XXX 事件的叙事框架""对比各媒体报道角度"
- 舆情采集完成后用户要求分析
- 定时任务消息包含"进行叙事分析"

**不适用于**：采集数据（使用 sentiment-collector）、生成报告（使用 sentiment-reporter）。

## 前置检查（必须先执行）

在开始分析之前，检查数据是否就绪：

1. 用 `exec` 获取今日日期：`TODAY=$(date +%Y-%m-%d)`
2. 用 `read` 检查文件 `~/.openclaw/workspace/data/cleaned/${TODAY}_collected.json` 是否存在。
3. 如果文件 **存在** → 跳到下方"执行步骤"。
4. 如果文件 **不存在** → 今天还没有采集数据，需要自动补链：
   a. 用 `exec` 运行：`mkdir -p ~/.openclaw/workspace/data/raw/$TODAY ~/.openclaw/workspace/data/cleaned`
   b. 用 `exec` 运行：`python3 ~/.openclaw/workspace/skills/sentiment-collector/scripts/fetch_hotlists.py --output ~/.openclaw/workspace/data/raw/$TODAY/hotlists.json`
   c. 用 `read` 读取上一步输出的 `hotlists.json`，取热度最高的前 5 个话题。
   d. 对每个话题调用 `web_search`，查询：`"{话题}" 最新报道 评论`。
   e. 将热榜数据 + web_search 结果合并、去重、按热度降序排列，构造为 collected JSON 格式（参照 sentiment-collector 的输出 schema）。
   f. 用 `write` 保存到 `~/.openclaw/workspace/data/cleaned/${TODAY}_collected.json`。
   g. 继续执行下方分析步骤。

## 叙事框架参考（5 种框架）

| 框架 | 英文 | 核心特征 | 典型表述 |
|------|------|---------|---------|
| 冲突框架 | Conflict | 强调对立、争议、矛盾双方 | "炮轰""激烈争论""对峙" |
| 人情味框架 | Human Interest | 聚焦个人故事、情感共鸣 | "他/她的故事""令人心碎" |
| 责任归因框架 | Attribution | 指出谁该为此事负责 | "谁之过""监管缺失" |
| 经济后果框架 | Economic | 聚焦经济/财务影响 | "损失达X亿""股价暴跌" |
| 道德框架 | Morality | 诉诸伦理道德判断 | "良心何在""触碰底线" |

如需更详细的框架识别指导，用 `read` 工具读取 `{baseDir}/references/framework-guide.md`。

## 执行步骤

### Step 1 — 读取数据

用 `read` 读取 `~/.openclaw/workspace/data/cleaned/${TODAY}_collected.json`。如果今日文件不存在且昨日文件存在，使用昨日文件。都不存在则告知用户"未找到已采集的舆情数据，请先运行舆情采集"并停止。

### Step 2 — 事件聚类

- 将 items 按话题相似性分组（标题包含相同关键实体/事件名的归为一组）。
- 每组即一个"事件"，组内条目作为该事件的"多源报道"。
- 无法清晰聚类时，每条单独作为一个事件。
- 最多分析 **前 5 个事件**（按组内条目数 + 热度总和排序取 top5）。

### Step 3 — 三层分析

对每个事件执行：

**第一层：叙事框架识别**

对事件内每条来源的标题 + 摘要判断：
- 主要叙事框架（从 5 种中选 1-2 种）
- 叙事立场：批评 / 支持 / 中立 / 观望
- 核心论点：一句话概括
- 情感强度：1-5 分

**第二层：归因逻辑解构**

横向对比同一事件不同来源：
- 归因主体：政府 / 企业 / 个人 / 制度 / 技术 / 社会 / 自然 / 不明确
- 叙事策略：放大 / 淡化 / 转移注意力 / 情感共鸣 / 客观陈述
- 输出归因矩阵表格
- 框架冲突度：低 / 中 / 高（附判断理由）

**第三层：态势研判**

- 舆情阶段：萌芽期 / 升温期 / 爆发期 / 衰减期
- 风险等级：🟢绿色 / 🟡黄色 / 🟠橙色 / 🔴红色
- 趋势预判：一句话描述未来 24 小时走势

### Step 4 — 保存分析结果

用 `exec` 确保目录存在：`mkdir -p ~/.openclaw/workspace/data/analyzed`

用 `write` 将分析结果保存到 `~/.openclaw/workspace/data/analyzed/${TODAY}_analysis.json`，格式：

```json
{
  "analysis_time": "ISO-8601",
  "analysis_date": "YYYY-MM-DD",
  "events_analyzed": 5,
  "events": [
    {
      "event_name": "事件名称",
      "source_count": 4,
      "sources": [
        {
          "title": "...",
          "source_name": "...",
          "primary_frame": "冲突框架",
          "secondary_frame": "责任归因框架",
          "stance": "批评",
          "core_argument": "一句话",
          "sentiment_intensity": 4,
          "attribution_target": "企业",
          "narrative_strategy": "放大"
        }
      ],
      "attribution_matrix": {
        "primary_attributions": {"企业": 2, "制度": 1},
        "dominant_attribution": "企业",
        "frame_distribution": {"冲突框架": 50, "责任归因框架": 30},
        "conflict_level": "高",
        "conflict_reason": "说明文字"
      },
      "situation_assessment": {
        "phase": "升温期",
        "risk_level": "🟠橙色",
        "trend_prediction": "预计未来24小时走势描述"
      }
    }
  ],
  "overall_summary": {
    "dominant_frame_today": "冲突框架",
    "average_risk": "🟡黄色",
    "key_insight": "50-100字的总结洞察"
  }
}
```

### Step 5 — 输出分析摘要

向用户回复：

```
🔍 舆情叙事分析完成

📅 分析日期：{TODAY}
📊 共分析 {N} 个事件

📌 核心发现：
{overall_summary.key_insight}

🔥 高风险事件：
  ⚠️ {event_name} — {risk_level} — {phase}
     归因焦点：{dominant_attribution}
     框架冲突度：{conflict_level}

💡 提示：输入"生成舆情日报"可生成完整可视化报告
```

## 错误处理

- 数据文件为空或格式异常 → 告知用户"数据文件损坏，请重新采集"。
- 某个事件来源太少（仅 1 条）→ 跳过归因矩阵，仅做单源框架识别。
- 分析过程中 LLM 不确定框架类型 → 标记为"待定"并在摘要中注明。
