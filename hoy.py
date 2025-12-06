import requests
import datetime
import json
import re
from datetime import timedelta, timezone

# ---------- CONFIG ----------
TZ = timezone(timedelta(hours=8))  # Kuala Lumpur timezone
URL = "https://hoy.tv/program_guide"

# Only these 3 channels with assigned numbers
CHANNELS = {
    "HOY INFO": {"id": "hoyinfor", "number": 76},
    "HOY TV": {"id": "hoytv", "number": 77},
    "HOY NEWS": {"id": "hoynews", "number": 78}
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "zh-HK,zh;q=0.9,en;q=0.8",
    "Referer": "https://hoy.tv/"
}

OUTPUT_FILE = "hoy.xml"
# ----------------------------

def to_xml_time(timestr):
    # Parse ISO datetime from HOY JSON
    dt = datetime.datetime.fromisoformat(timestr)
    # Convert to Kuala Lumpur timezone (UTC+8)
    dt = dt.astimezone(TZ)
    return dt.strftime("%Y%m%d%H%M%S %z")

def extract_json(html):
    pattern = r"programGuide\s*=\s*(\{.*?\});"
    match = re.search(pattern, html, re.DOTALL)
    if not match:
        open("debug.html", "w", encoding="utf-8").write(html)
        raise Exception("JSON NOT FOUND IN PAGE — debug.html saved")
    return json.loads(match.group(1))

def build_epg():
    r = requests.get(URL, headers=HEADERS, timeout=20)
    r.raise_for_status()
    data = extract_json(r.text)

    xml = ['<?xml version="1.0" encoding="UTF-8"?>', '<tv>']

    # Channels only: HOY INFO, HOY TV, HOY NEWS
    for name, info in CHANNELS.items():
        xml.append(f'  <channel id="{info["id"]}">')
        xml.append(f'    <display-name>{name}</display-name>')
        xml.append(f'    <number>{info["number"]}</number>')  # optional for Televizo
        xml.append('  </channel>')
        xml.append('')

    # Programs
    for day in data.get("days", []):
        for channel in day.get("channels", []):
            cname = channel.get("name")
            if cname not in CHANNELS:
                continue  # skip all other channels
