#!/bin/bash
set -euo pipefail

echo "==> 配置舆情罗盘定时任务"

openclaw cron add \
  --name "舆情罗盘-上午采集" \
  --cron "0 10 * * *" \
  --tz "Asia/Shanghai" \
  --session isolated \
  --message "采集今日舆情" \
  --announce

openclaw cron add \
  --name "舆情罗盘-傍晚采集" \
  --cron "0 18 * * *" \
  --tz "Asia/Shanghai" \
  --session isolated \
  --message "采集今日舆情" \
  --announce

openclaw cron add \
  --name "舆情罗盘-生成日报" \
  --cron "0 23 * * *" \
  --tz "Asia/Shanghai" \
  --session isolated \
  --message "生成今日舆情日报" \
  --announce

echo
echo "✅ 定时任务已配置完成"
echo "已配置任务："
echo "  10:00 上午采集"
echo "  18:00 傍晚采集"
echo "  23:00 生成日报（任务内自带采集 + 分析 + 报告）"
echo
echo "常用管理命令："
echo "  openclaw cron list"
echo "  openclaw cron run <job-id>"
echo "  openclaw cron runs --id <job-id>"
echo "  openclaw cron edit <job-id> --enabled false"
echo "  openclaw cron remove <job-id>"
