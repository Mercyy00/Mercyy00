#!/usr/bin/env python3
"""
Scrape real daily contribution counts from GitHub's public, unauthenticated
contributions endpoint (the same fragment the profile page itself uses) and
write data/contributions.json with raw days plus derived stats
(current streak, longest streak, best day, monthly totals).

No token, no auth, no GraphQL -- public HTML served by GitHub.
Run daily by .github/workflows/update-profile-art.yml.
"""
import datetime
import json
import os
import re
import sys

USERNAME = os.environ.get("GH_PROFILE_USER", "Mercyy00")
URL = f"https://github.com/users/{USERNAME}/contributions"
OUT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "contributions.json")


def fetch_days():
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) profile-bot/1.0"}
    html_text = ""
    try:
        import requests
        resp = requests.get(URL, headers=headers, timeout=30)
        resp.raise_for_status()
        html_text = resp.text
    except ImportError:
        import urllib.request
        req = urllib.request.Request(URL, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as r:
            html_text = r.read().decode("utf-8")

    days = []
    # Try bs4 if available, otherwise fallback to HTMLParser
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html_text, "html.parser")
        cells = soup.select("td.ContributionCalendar-day")
        for td in cells:
            date = td.get("data-date")
            if not date:
                continue
            level = int(td.get("data-level") or 0)
            td_id = td.get("id")
            tooltip_el = soup.find("tool-tip", attrs={"for": td_id}) if td_id else None
            text = tooltip_el.get_text(strip=True) if tooltip_el else ""
            if re.search(r"no contributions", text, re.I):
                count = 0
            else:
                m = re.search(r"(\d+)\s+contribution", text, re.I)
                count = int(m.group(1)) if m else (level if level > 0 else 0)
            days.append({"date": date, "count": count, "level": level})
    except ImportError:
        from html.parser import HTMLParser

        class FallbackParser(HTMLParser):
            def __init__(self):
                super().__init__()
                self.days_list = []
                self.tooltips = {}
                self.cur_for = None
                self.cur_text = []

            def handle_starttag(self, tag, attrs):
                d = dict(attrs)
                if tag == "td" and "ContributionCalendar-day" in d.get("class", ""):
                    date = d.get("data-date")
                    if date:
                        self.days_list.append({
                            "date": date,
                            "level": int(d.get("data-level", 0)),
                            "id": d.get("id", ""),
                            "count": 0
                        })
                elif tag == "tool-tip":
                    self.cur_for = d.get("for")
                    self.cur_text = []

            def handle_data(self, data):
                if self.cur_for:
                    self.cur_text.append(data)

            def handle_endtag(self, tag):
                if tag == "tool-tip" and self.cur_for:
                    self.tooltips[self.cur_for] = "".join(self.cur_text).strip()
                    self.cur_for = None
                    self.cur_text = []

        parser = FallbackParser()
        parser.feed(html_text)
        for item in parser.days_list:
            text = parser.tooltips.get(item["id"], "")
            if re.search(r"no contribution", text, re.I):
                count = 0
            else:
                m = re.search(r"(\d+)\s+contribution", text, re.I)
                count = int(m.group(1)) if m else (item["level"] if item["level"] > 0 else 0)
            days.append({"date": item["date"], "count": count, "level": item["level"]})

    if not days:
        print("Error: No contribution calendar days found.", file=sys.stderr)
        sys.exit(1)

    days.sort(key=lambda d: d["date"])
    return days


def compute_current_streak(days):
    idx = len(days) - 1
    if days[idx]["count"] == 0:
        idx -= 1  # today might not have commits yet
    streak = 0
    end_idx = idx
    while idx >= 0 and days[idx]["count"] > 0:
        streak += 1
        idx -= 1
    start_idx = idx + 1
    if streak == 0:
        return 0, None, None
    return streak, days[start_idx]["date"], days[end_idx]["date"]


def compute_longest_streak(days):
    longest = run = 0
    longest_start = longest_end = None
    run_start_idx = None
    for i, d in enumerate(days):
        if d["count"] > 0:
            if run == 0:
                run_start_idx = i
            run += 1
            if run > longest:
                longest = run
                longest_start = days[run_start_idx]["date"]
                longest_end = days[i]["date"]
        else:
            run = 0
    return longest, longest_start, longest_end


def build_data(days):
    total = sum(d["count"] for d in days)
    active_days = sum(1 for d in days if d["count"] > 0)
    best = max(days, key=lambda d: d["count"]) if days else {"date": "", "count": 0}
    cur_len, cur_start, cur_end = compute_current_streak(days)
    long_len, long_start, long_end = compute_longest_streak(days)

    monthly = {}
    for d in days:
        key = d["date"][:7]
        monthly[key] = monthly.get(key, 0) + d["count"]
    monthly_list = [{"month": k, "total": v} for k, v in sorted(monthly.items())]

    return {
        "username": USERNAME,
        "generated_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "range": {"start": days[0]["date"], "end": days[-1]["date"]},
        "total_contributions": total,
        "active_days": active_days,
        "avg_per_active_day": round(total / active_days, 1) if active_days else 0,
        "current_streak": {"length": cur_len, "start": cur_start, "end": cur_end},
        "longest_streak": {"length": long_len, "start": long_start, "end": long_end},
        "best_day": {"date": best["date"], "count": best["count"]},
        "monthly": monthly_list,
        "days": days,
    }


if __name__ == "__main__":
    days = fetch_days()
    data = build_data(days)
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print(f"Wrote {OUT_PATH}: {data['total_contributions']} contributions, "
          f"active days: {data['active_days']}, "
          f"current streak: {data['current_streak']['length']}, "
          f"longest streak: {data['longest_streak']['length']}")
