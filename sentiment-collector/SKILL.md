---
name: sentiment-collector
description: 采集舆情数据、监测热点话题、查看今日热搜。当用户说"采集舆情""查看热点""监测XX话题""今日有什么热点"时使用。不适用于分析数据或生成报告。
version: 1.0.0
author: sentiment-compass-team
---

# 舆情数据采集 Skill

通过热榜脚本和 web_search 工具采集中文互联网舆情数据，输出统一格式的结构化 JSON。

## 适用场景

- 用户要求采集舆情数据
- 用户询问今日热点 / 今日有什么热搜
- 用户要求监测某个话题或关键词
- 定时任务消息包含"执行舆情采集"字样

**不适用于**：分析已有数据（使用 narrative-analyzer）、生成报告（使用 sentiment-reporter）。

## 执行步骤

### Step 1 — 准备工作目录

使用 `exec` 运行：

```bash
TODAY=$(date +%Y-%m-%d)
mkdir -p ~/.openclaw/workspace/data/raw/$TODAY ~/.openclaw/workspace/data/cleaned
```

记录 `$TODAY` 变量，后续步骤中使用。

### Step 2 — 运行热榜采集脚本

使用 `exec` 执行：

```bash
python3 {baseDir}/scripts/fetch_hotlists.py --output ~/.openclaw/workspace/data/raw/$TODAY/hotlists.json
```

- 脚本自动访问百度热搜和微博热搜的公开接口，返回统一 JSON。
- **如果脚本失败**（退出码非零或输出包含 `ERROR`）：跳过此步，在最终摘要中注明"热榜采集失败，使用 web_search 兜底"。

### Step 3 — 使用 web_search 搜索深度内容

1. 如果 Step 2 成功，从热榜 JSON 中取热度最高的 **前 5 个话题**。
2. 如果 Step 2 失败，使用用户指定的关键词；若用户未指定，搜索"今日重大新闻事件"。
3. 对每个话题调用 `web_search`，查询格式：`"{话题名称}" 最新报道 评论`。
4. 每次返回约 5 条结果（标题 + URL + 摘要片段），这些摘要足以用于后续叙事分析。

**重要**：不需要使用 `web_fetch` 获取完整网页正文。摘要已足够判断叙事框架和立场。仅当用户明确要求"深入分析某篇文章"时才使用 `web_fetch`。

### Step 4 — 数据清洗与结构化

将所有来源数据合并为以下 JSON 格式：

- 去重：标题含相同核心关键词且来源相同时，保留热度更高的条目。
- 按热度降序排列。
- 为每条分配递增 id。

```json
{
  "collection_time": "ISO-8601 时间戳",
  "collection_date": "YYYY-MM-DD",
  "topic_count": 15,
  "sources_covered": ["百度热搜", "微博热搜", "web_search"],
  "items": [
    {
      "id": 1,
      "title": "标题",
      "source": "百度热搜",
      "snippet": "摘要描述 50-150 字",
      "url": "https://...",
      "heat_score": 9876543,
      "category": "社会",
      "collected_via": "hotlist_script"
    },
    {
      "id": 2,
      "title": "标题",
      "source": "新华网",
      "snippet": "web_search 返回的摘要片段",
      "url": "https://...",
      "heat_score": null,
      "category": "auto",
      "collected_via": "web_search"
    }
  ]
}
```

### Step 5 — 保存清洗后数据

使用 `write` 工具将 JSON 写入：

```
~/.openclaw/workspace/data/cleaned/{TODAY}_collected.json
```

如果同一天已有文件，读取已有文件，将新 items 追加并去重后重新保存。

### Step 6 — 输出采集摘要

向用户回复以下格式的摘要：

```
✅ 舆情采集完成
📅 日期：{TODAY}
📊 共采集 {N} 条数据
🌐 覆盖来源：百度热搜、微博热搜、web_search
🔥 热度 TOP3：
  1. {标题} — {来源} — 热度 {值}
  2. {标题} — {来源} — 热度 {值}
  3. {标题} — {来源} — 热度 {值}

💡 提示：输入"分析今日舆情"可进行叙事框架深度分析
```

## 错误处理

- 热榜脚本失败 → 用 web_search 兜底，不中断流程。
- web_search 返回空结果 → 换用更宽泛的关键词重试一次。
- 所有途径均失败 → 告知用户"采集失败，请检查网络连接和 web_search 配置"。
