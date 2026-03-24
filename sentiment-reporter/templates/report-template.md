# 📊 舆情罗盘 · 每日舆情叙事分析报告

> 📅 报告日期：{{analysis_date}}
> ⏰ 生成时间：{{generation_time}}
> 📊 分析事件数：{{events_analyzed}}
> 🎯 整体风险评估：{{average_risk}}

---

## 一、今日核心洞察

> {{overall_summary.key_insight}}

---

## 二、今日热点事件分析

{{#each events}}

### 事件 {{序号}}：{{event_name}}

**基本信息**

- 涉及来源数：{{source_count}}
- 舆情阶段：{{phase}}
- 风险等级：{{risk_level}}
- 趋势预判：{{trend_prediction}}

**叙事框架分布**

| 框架类型 | 占比 |
|---------|------|
| {{frame_name}} | {{percentage}}% |

**归因矩阵**

| 来源 | 主要框架 | 立场 | 归因对象 | 叙事策略 | 核心论点 |
|------|---------|------|---------|---------|---------|
| {{source_name}} | {{primary_frame}} | {{stance}} | {{attribution_target}} | {{narrative_strategy}} | {{core_argument}} |

**框架冲突评估**

- 冲突度：{{conflict_level}}
- 分析：{{conflict_reason}}

{{/each}}

---

## 三、叙事框架全局分布

| 框架类型 | 今日占比 | 代表性事件 |
|---------|---------|----------|
| {{frame}} | {{pct}}% | {{example_event}} |

---

## 四、风险预警清单

| 事件 | 风险等级 | 舆情阶段 | 核心归因 | 框架冲突 | 行动建议 |
|------|---------|---------|---------|---------|---------|
| {{event}} | {{risk}} | {{phase}} | {{attribution}} | {{conflict}} | {{suggestion}} |

---

## 五、今日主要发现

1. **叙事趋势**：{{narrative_trend_summary}}
2. **归因特征**：{{attribution_trend_summary}}
3. **风险研判**：{{risk_trend_summary}}

---

> 📌 本报告由 **舆情罗盘（Sentiment Compass）** 基于 OpenClaw 自动生成
> 🤖 分析引擎：OpenClaw + LLM
> ⏱️ 报告生成耗时：自动执行
