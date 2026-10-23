#!/usr/bin/env python3
import feedparser
import json
import hashlib
import time
import os
import re

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_PATH = os.path.join(BASE_DIR, "data", "data.json")

# 可自行增删RSS源
RSS_SOURCES = [
    {"name": "The Hacker News", "url": "https://thehackernews.com/feeds/posts/default"},
    {"name": "阿里云漏洞通告", "url": "https://avd.aliyun.com/rss"},
    {"name": "FreeBuf", "url": "https://www.freebuf.com/feed"},
    {"name": "奇安信威胁情报", "url": "https://ti.qianxin.com/rss"},
]

# CVE正则
CVE_PATTERN = re.compile(r"CVE-\d{4}-\d{4,7}", re.IGNORECASE)
# 高危关键词，用来判定severity
HIGH_KEYWORDS = {"rce", "远程代码执行", "命令执行", "0day", "零日", "权限提升", "越权", "注入", "未授权访问"}
MEDIUM_KEYWORDS = {"信息泄露", "XSS", "CSRF", "路径遍历", "文件读取"}

def extract_cve(text):
    if not text:
        return ""
    res = CVE_PATTERN.findall(text)
    if res:
        return ",".join(sorted(list(set([x.upper() for x in res]))))
    return ""

def calc_severity(title, summary):
    full = (title + " " + summary).lower()
    if any(k in full for k in HIGH_KEYWORDS):
        return "高危"
    elif any(k in full for k in MEDIUM_KEYWORDS):
        return "中危"
    return "低危/提示"

def get_hash(item):
    key = f"{item['link']}{item['title']}"
    return hashlib.md5(key.encode("utf-8")).hexdigest()

def load_old_data():
    if os.path.exists(DATA_PATH):
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def fetch_rss(source):
    ret = []
    try:
        d = feedparser.parse(source["url"])
        for entry in d.entries:
            title = entry.get("title", "").strip()
            link = entry.get("link", "").strip()
            summary = entry.get("summary", "").strip()
            published = entry.get("published", "")
            if not published and "updated" in entry:
                published = entry["updated"]

            cve = extract_cve(title + " " + summary)
            severity = calc_severity(title, summary)

            item = {
                "title": title,
                "link": link,
                "summary": summary,
                "time": published,
                "source": source["name"],
                "cve": cve,
                "severity": severity
            }
            item["_hash"] = get_hash(item)
            ret.append(item)
        time.sleep(1.2)
    except Exception as e:
        print(f"[ERR] {source['name']} fetch failed: {e}")
    return ret

def main():
    old_list = load_old_data()
    old_hash_set = {x["_hash"] for x in old_list}
    new_items = []

    for src in RSS_SOURCES:
        items = fetch_rss(src)
        for it in items:
            if it["_hash"] not in old_hash_set:
                new_items.append(it)

    combined = new_items + old_list
    # 简易时间排序
    combined.sort(key=lambda x: x["time"], reverse=True)
    combined = combined[:800]

    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(combined, f, ensure_ascii=False, indent=2)
    print(f"Done. New:{len(new_items)}, Total:{len(combined)}")

if __name__ == "__main__":
    main()
