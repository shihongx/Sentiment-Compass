#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
热榜采集脚本 — 舆情罗盘 (Sentiment Compass)

通过 HTTP 请求获取百度热搜和微博热搜的公开 JSON 接口数据，
输出统一格式 JSON。仅使用 Python 标准库，无需第三方依赖。

用法:
    python3 fetch_hotlists.py --output /path/to/output.json
    python3 fetch_hotlists.py  # 输出到 stdout
"""

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone, timedelta


UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/125.0.0.0 Safari/537.36"
)

CST = timezone(timedelta(hours=8))

# ---------------------------------------------------------------------------
# 百度热搜
# ---------------------------------------------------------------------------

def fetch_baidu():
    """抓取百度热搜 top20，返回统一 items 列表。"""
    url = "https://top.baidu.com/api/board?platform=wise&tab=realtime"
    req = urllib.request.Request(url, headers={"User-Agent": UA})

    with urllib.request.urlopen(req, timeout=15) as resp:
        if resp.status != 200:
            raise RuntimeError(f"HTTP {resp.status}")
        raw = json.loads(resp.read().decode("utf-8"))

    entries = raw["data"]["cards"][0]["content"]
    items = []
    for entry in entries[:20]:
        items.append({
            "title": entry.get("word", ""),
            "source": "百度热搜",
            "snippet": entry.get("desc", ""),
            "url": entry.get("url", ""),
            "heat_score": _safe_int(entry.get("hotScore")),
            "category": "auto",
            "collected_via": "hotlist_script",
        })
    return items


# ---------------------------------------------------------------------------
# 微博热搜
# ---------------------------------------------------------------------------

def fetch_weibo():
    """抓取微博热搜 top20，返回统一 items 列表。"""
    url = "https://weibo.com/ajax/side/hotSearch"
    headers = {
        "User-Agent": UA,
        "Cookie": "SUB=_2AkMWJrkXf8NxqwFRmP8SymnhaY1wwg3EieKnXB_JJRMxHRl-yT9kqlUJtRB6PaZeZ6vE1YfhF5VH_bwlGfvuS6PH_gCU",
    }
    req = urllib.request.Request(url, headers=headers)

    with urllib.request.urlopen(req, timeout=15) as resp:
        if resp.status != 200:
            raise RuntimeError(f"HTTP {resp.status}")
        raw = json.loads(resp.read().decode("utf-8"))

    entries = raw["data"]["realtime"]
    items = []
    for entry in entries[:20]:
        word = entry.get("word", "")
        encoded_word = urllib.parse.quote(f"#{word}#")
        items.append({
            "title": word,
            "source": "微博热搜",
            "snippet": "",
            "url": f"https://s.weibo.com/weibo?q={encoded_word}",
            "heat_score": _safe_int(entry.get("num")),
            "category": "auto",
            "collected_via": "hotlist_script",
        })
    return items


# ---------------------------------------------------------------------------
# 工具函数
# ---------------------------------------------------------------------------

def _safe_int(val):
    """将值安全转换为 int，失败返回 None。"""
    if val is None:
        return None
    try:
        return int(val)
    except (ValueError, TypeError):
        return None


def build_output(all_items, source_status):
    """构建最终输出 JSON 结构。"""
    now = datetime.now(CST)
    return {
        "fetch_time": now.isoformat(),
        "sources": source_status,
        "items": all_items,
    }


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="热榜数据采集")
    parser.add_argument("--output", type=str, default=None,
                        help="输出文件路径，不指定则输出到 stdout")
    args = parser.parse_args()

    all_items = []
    source_status = {}
    any_success = False

    # --- 百度热搜 ---
    try:
        baidu_items = fetch_baidu()
        all_items.extend(baidu_items)
        source_status["baidu"] = {"status": "ok", "count": len(baidu_items)}
        any_success = True
    except (urllib.error.URLError, urllib.error.HTTPError,
            KeyError, IndexError, TypeError, json.JSONDecodeError,
            RuntimeError, OSError) as exc:
        print(f"[WARN] 百度热搜采集失败: {exc}", file=sys.stderr)
        source_status["baidu"] = {"status": "failed", "error": str(exc)}

    # --- 微博热搜 ---
    try:
        weibo_items = fetch_weibo()
        all_items.extend(weibo_items)
        source_status["weibo"] = {"status": "ok", "count": len(weibo_items)}
        any_success = True
    except (urllib.error.URLError, urllib.error.HTTPError,
            KeyError, IndexError, TypeError, json.JSONDecodeError,
            RuntimeError, OSError) as exc:
        print(f"[WARN] 微博热搜采集失败: {exc}", file=sys.stderr)
        source_status["weibo"] = {"status": "failed", "error": str(exc)}

    if not any_success:
        print("[ERROR] 所有数据源采集失败", file=sys.stderr)
        sys.exit(1)

    output = build_output(all_items, source_status)
    json_str = json.dumps(output, ensure_ascii=False, indent=2)

    if args.output:
        os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(json_str)
        print(f"[INFO] 数据已写入 {args.output}", file=sys.stderr)
    else:
        print(json_str)


if __name__ == "__main__":
    main()
