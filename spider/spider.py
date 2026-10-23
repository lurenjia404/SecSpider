import feedparser
import json
import time
import os
import re
import requests
from bs4 import BeautifulSoup

# 输出路径
DATA_PATH = os.path.join(os.path.dirname(__file__), "../data/data.json")
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

LEVEL_MAP = {
    "严重": "critical",
    "critical": "critical",
    "高危": "high",
    "high": "high",
    "中危": "medium",
    "medium": "medium",
    "低危": "low",
    "low": "low"
}

def cvss2level(score: float) -> str:
    """CVSS分数转前端等级"""
    if score >= 9.0:
        return "critical"
    elif score >=7.0:
        return "high"
    elif score >=4.0:
        return "medium"
    else:
        return "low"

def get_rss_list():
    rss_list = [
        {
            "name": "CNVD",
            "url": "https://www.cnvd.org.cn/rss.xml"
        },
        {
            "name": "The Hacker News",
            "url": "https://thehackernews.com/feeds/posts/default"
        }
    ]
    return rss_list

def fetch_rss(source_name, rss_url):
    items_out = []
    try:
        feed = feedparser.parse(rss_url)
        for entry in feed.entries:
            title = entry.get("title", "").strip()
            link = entry.get("link", "").strip()
            desc = entry.get("summary", "").strip()
            published = entry.get("published_parsed")
            if published:
                t = time.strftime("%Y-%m-%d %H:%M:%S", published)
            else:
                t = time.strftime("%Y-%m-%d %H:%M:%S")
            cve_match = re.search(r"CVE-\d{4}-\d+", title + " " + desc)
            cve = cve_match.group(0) if cve_match else "-"
            level = "info"
            item = {
                "time": t,
                "level": level,
                "title": title,
                "cve": cve,
                "source": source_name,
                "desc": desc,
                "url": link
            }
            items_out.append(item)
    except Exception as e:
        print(f"[ERR] RSS {source_name} 抓取失败: {e}")
    return items_out

def fetch_avd_high_risk():
    """阿里云AVD高危列表爬虫，进入详情页拿CVSS，自动生成level"""
    items_out = []
    list_url = "https://avd.aliyun.com/high-risk/list"
    try:
        resp = requests.get(list_url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        table = soup.select_one("table")
        rows = table.select("tr")[1:]
        for tr in rows:
            tds = tr.select("td")
            if len(tds) <4:
                continue
            avd_id = tds[0].get_text(strip=True)
            title = tds[1].get_text(strip=True)
            pub_time = tds[3].get_text(strip=True)
            detail_a = tds[1].select_one("a")
            if not detail_a:
                continue
            detail_url = "https://avd.aliyun.com" + detail_a["href"]
            # 访问详情页拿CVSS
            try:
                d_resp = requests.get(detail_url, headers=HEADERS, timeout=10)
                d_soup = BeautifulSoup(d_resp.text, "html.parser")
                cvss_text = d_soup.find(string=re.compile("CVSS"))
                cvss_score = 0.0
                if cvss_text:
                    m = re.search(r"[:：]\s*([0-9.]+)", cvss_text)
                    if m:
                        cvss_score = float(m.group(1))
                level = cvss2level(cvss_score)
                desc = d_soup.get_text(strip=True)[:600]
                cve_match = re.search(r"CVE-\d{4}-\d+", title + " " + desc)
                cve = cve_match.group(0) if cve_match else "-"
                item = {
                    "time": pub_time,
                    "level": level,
                    "title": f"[{avd_id}] {title}",
                    "cve": cve,
                    "source": "阿里云AVD",
                    "desc": desc,
                    "url": detail_url
                }
                items_out.append(item)
                time.sleep(0.4)
            except Exception as e:
                print(f"[WARN] AVD详情 {detail_url} 解析异常: {e}")
                continue
    except Exception as e:
        print(f"[ERR] AVD列表页抓取失败: {e}")
    return items_out


def main():
    all_items = []
    # 抓取RSS源
    for src in get_rss_list():
        print(f"[*] 抓取RSS: {src['name']}")
        part = fetch_rss(src["name"], src["url"])
        all_items.extend(part)
    # 抓取AVD页面爬虫（带等级）
    print("[*] 抓取阿里云AVD高危列表（带CVSS等级）")
    avd_items = fetch_avd_high_risk()
    all_items.extend(avd_items)

    # url去重
    seen = set()
    unique = []
    for it in all_items:
        if it["url"] not in seen:
            seen.add(it["url"])
            unique.append(it)
    # 时间倒序
    unique.sort(key=lambda x: x["time"], reverse=True)

    out_data = {
        "update_ts": int(time.time()),
        "items": unique
    }
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(out_data, f, ensure_ascii=False, indent=2)
    print(f"Done. New:{len(unique)}, Total:{len(unique)}")


if __name__ == "__main__":
    main()
