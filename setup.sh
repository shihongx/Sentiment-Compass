#!/bin/bash
set -euo pipefail

WORKSPACE="${HOME}/.openclaw/workspace"
SKILLS_DIR="${WORKSPACE}/skills"
DATA_DIR="${WORKSPACE}/data"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILL_SRC="${SCRIPT_DIR}/sentiment-compass-skill"
SKILL_DST="${SKILLS_DIR}/sentiment-compass-skill"

echo "==> 部署舆情罗盘（Sentiment Compass）"

if ! command -v openclaw >/dev/null 2>&1; then
    echo "❌ 未检测到 openclaw 命令，请先安装 OpenClaw。"
    exit 1
fi
echo "✅ OpenClaw 已安装：$(openclaw --version 2>/dev/null || echo unknown)"

if ! command -v python3 >/dev/null 2>&1; then
    echo "⚠️ 未检测到 python3，尝试安装。"
    if command -v apt-get >/dev/null 2>&1; then
        sudo apt-get update
        sudo apt-get install -y python3
    elif command -v yum >/dev/null 2>&1; then
        sudo yum install -y python3
    else
        echo "❌ 无法自动安装 Python3，请手动安装后重试。"
        exit 1
    fi
fi
echo "✅ Python3 可用：$(python3 --version)"

mkdir -p "${SKILLS_DIR}" "${DATA_DIR}/raw" "${DATA_DIR}/cleaned" "${DATA_DIR}/analyzed" "${DATA_DIR}/reports"
echo "✅ OpenClaw 工作目录已就绪：${WORKSPACE}"

if [ -d "${SKILL_DST}" ]; then
    BACKUP_PATH="${SKILL_DST}.bak.$(date +%s)"
    mv "${SKILL_DST}" "${BACKUP_PATH}"
    echo "⚠️ 检测到旧版 skill，已备份到：${BACKUP_PATH}"
fi

cp -r "${SKILL_SRC}" "${SKILLS_DIR}/"
chmod +x "${SKILL_DST}/scripts/fetch_hotlists.py"
echo "✅ Skill 已部署到：${SKILL_DST}"

TMP_JSON="$(mktemp)"
TMP_ERR="$(mktemp)"
echo "==> 测试热榜采集脚本"
if python3 "${SKILL_DST}/scripts/fetch_hotlists.py" --output "${TMP_JSON}" 2>"${TMP_ERR}"; then
    ITEM_COUNT="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1], encoding="utf-8"))["total_items"])' "${TMP_JSON}" 2>/dev/null || echo 0)"
    echo "✅ 采集脚本运行成功，共获取 ${ITEM_COUNT} 条数据"
else
    echo "⚠️ 采集脚本执行出现警告，OpenClaw 运行时仍可使用 web_search 兜底"
    cat "${TMP_ERR}" 2>/dev/null || true
fi

rm -f "${TMP_JSON}" "${TMP_ERR}"

echo
echo "🎉 部署完成"
echo "下一步建议："
echo "1. 确保已配置 LLM（推荐 qwen-plus 或 DeepSeek）"
echo "2. 确保 Tools 已启用：read、write、exec、web_search、web_fetch"
echo "3. 在 OpenClaw 中输入“采集今日舆情”测试 Skill"
echo "4. 运行 bash cron-setup.sh 配置定时任务"
