#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import json
import re
import ssl
import sys
from datetime import datetime, timedelta, timezone
from urllib import error, parse, request


USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/131.0.0.0 Safari/537.36"
)
TIMEOUT = 15
SSL_CONTEXT = ssl._create_unverified_context()
CST = timezone(timedelta(hours=8))


def now_iso():
    return datetime.now(CST).isoformat(timespec="seconds")


def make_request(url, headers=None):
    req_headers = {"User-Agent": USER_AGENT}
    if headers:
        req_headers.update(headers)
    return request.Request(url, headers=req_headers)


def fetch_json(url, headers=None):
    req = make_request(url, headers=headers)
    with request.urlopen(req, timeout=TIMEOUT, context=SSL_CONTEXT) as resp:
        status = getattr(resp, "status", 200)
        if status != 200:
            raise RuntimeError("HTTP {}".format(status))
        charset = resp.headers.get_content_charset() or "utf-8"
        raw = resp.read().decode(charset, errors="replace")
    return json.loads(raw)


def safe_int(value, default=0):
    if value is None:
        return default
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, (int, float)):
        return int(value)
    text = str(value).strip().replace(",", "")
    if not text:
        return default
    try:
        return int(float(text))
    except ValueError:
        return default


def parse_zhihu_heat(detail_text):
    text = str(detail_text or "").strip()
    if not text:
        return 0
    match = re.search(r"(\d+(?:\.\d+)?)", text)
    if not match:
        return 0
    number = float(match.group(1))
    if "亿" in text:
        number *= 100000000
    elif "万" in text:
        number *= 10000
    return int(number)


def normalize_url(value):
    text = str(value or "").strip()
    return text or ""


def fetch_baidu():
    data = fetch_json(
        "https://top.baidu.com/api/board?platform=wise&tab=realtime",
        headers={"Referer": "https://top.baidu.com"},
    )
    cards = data["data"]["cards"]
    raw_content = cards[0]["content"]
    try:
        content = raw_content[0]["content"]
    except (TypeError, KeyError, IndexError):
        content = raw_content

    items = []
    for rank, item in enumerate(content[:15], start=1):
        items.append(
            {
                "title": str(item["word"]).strip(),
                "platform": "百度热搜",
                "rank": rank,
                "heat_score": safe_int(item.get("hotScore")),
                "url": normalize_url(item.get("url")),
            }
        )
    return items


def fetch_weibo():
    data = fetch_json(
        "https://weibo.com/ajax/side/hotSearch",
        headers={"Referer": "https://weibo.com"},
    )
    realtime = data["data"]["realtime"]
    items = []
    rank = 1
    for item in realtime:
        if safe_int(item.get("is_ad")) == 1:
            continue
        word = str(item["word"]).strip()
        items.append(
            {
                "title": word,
                "platform": "微博热搜",
                "rank": rank,
                "heat_score": safe_int(item.get("num")),
                "url": "https://s.weibo.com/weibo?q=%23{}%23".format(
                    parse.quote(word)
                ),
            }
        )
        rank += 1
        if len(items) >= 15:
            break
    return items


def fetch_zhihu():
    data = fetch_json(
        "https://api.zhihu.com/topstory/hot-lists/total?limit=15&desktop=true",
        headers={
            "Referer": "https://www.zhihu.com",
            "Origin": "https://www.zhihu.com",
        },
    )
    hot_items = data["data"]
    items = []
    for rank, item in enumerate(hot_items[:15], start=1):
        target = item["target"]
        target_url = normalize_url(target.get("url"))
        if not target_url and target.get("id"):
            target_url = "https://www.zhihu.com/question/{}".format(target["id"])
        items.append(
            {
                "title": str(target["title"]).strip(),
                "platform": "知乎热榜",
                "rank": rank,
                "heat_score": parse_zhihu_heat(item.get("detail_text")),
                "url": target_url,
            }
        )
    return items


def fetch_toutiao():
    data = fetch_json("https://www.toutiao.com/hot-event/hot-board/?origin=toutiao_pc")
    hot_items = data["data"]
    items = []
    for rank, item in enumerate(hot_items[:15], start=1):
        items.append(
            {
                "title": str(item["Title"]).strip(),
                "platform": "头条热榜",
                "rank": rank,
                "heat_score": safe_int(item.get("HotValue")),
                "url": normalize_url(item.get("Url")),
            }
        )
    return items


def warn_source(status_map, key, label, exc):
    message = "{}".format(exc).strip() or type(exc).__name__
    status_map[key] = {"status": "failed", "error": message}
    print("[WARN] {} 采集失败: {}".format(label, message), file=sys.stderr)


def write_output(path, payload):
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    if path:
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
            fh.write("\n")
    else:
        sys.stdout.write(text)
        sys.stdout.write("\n")


def main():
    parser = argparse.ArgumentParser(description="Fetch hotlists from Chinese web platforms.")
    parser.add_argument("--output", help="Output JSON file path.")
    args = parser.parse_args()

    items = []
    status = {}
    fetchers = [
        ("baidu", "百度热搜", fetch_baidu),
        ("weibo", "微博热搜", fetch_weibo),
        ("zhihu", "知乎热榜", fetch_zhihu),
        ("toutiao", "头条热榜", fetch_toutiao),
    ]

    for key, label, func in fetchers:
        try:
            fetched = func()
            status[key] = {"status": "ok", "count": len(fetched)}
            items.extend(fetched)
        except (
            error.URLError,
            error.HTTPError,
            TimeoutError,
            ValueError,
            KeyError,
            IndexError,
            TypeError,
            RuntimeError,
        ) as exc:
            warn_source(status, key, label, exc)
        except Exception as exc:
            warn_source(status, key, label, exc)

    if not any(info.get("status") == "ok" for info in status.values()):
        print("[ERROR] 所有数据源采集失败", file=sys.stderr)
        sys.exit(1)

    payload = {
        "fetch_time": now_iso(),
        "sources_status": status,
        "total_items": len(items),
        "items": items,
    }
    write_output(args.output, payload)


if __name__ == "__main__":
    main()
