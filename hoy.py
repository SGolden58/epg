import requests
import datetime
import json
import re
from datetime import timedelta, timezone

TZ = timezone(timedelta(hours=8))

URL = "https://hoy.tv/program_guide"

CHANNEL_MAP = {
    "HOY TV": "hoytv",
    "HOY INFO": "hoyinfor",
    "HOY NEWS": "hoynews"
}

def extract_json(html):
    """
    Extract embedded programGuide JSON from the page.
    """
    pattern = r"programGuide\s*=\s*(\{.*?\});"
    match = re.search(pattern, html, re.DOTALL)
    if not match:
        raise Exception("JSON NOT FOUND IN PAGE")
    return json.loads(match.group(1))

def to_xml_time(timestr):
    # timestr format: 2025-12-07T08:00:00+08:00
    dt = datetime.datetime.fromisoformat(timestr)
    return dt.strftime("%Y%m%d%H%M%S %z")

def build_epg():
    r = requests.get(URL, timeout=20)
    r.raise_for_status()

    data = extract_json(r.text)

    xml = []
    xml.append('<?xml version="1.0" encoding="UTF-8"?>')
    xml.append('<tv>')

    # channels
    for name, cid in CHANNEL_MAP.items():
        xml.append(f'  <channel id="{cid}">')
        xml.append(f'    <display-name>{name}</display-name>')
        xml.append('  </channel>')
        xml.append('')

    # schedule
    for day in data.get("days", []):
        for channel in day.get("channels", []):
            cname = channel.get("name")
            cid = CHANNEL_MAP.get(cname)
            if not cid:
                continue

            for item in channel.get("programme", []):
                start = to_xml_time(item["start"])
                stop = to_xml_time(item["end"])
                title = item["title"].replace("&", "&amp;")

                xml.append(f'  <programme start="{start}" stop="{stop}" channel="{cid}">')
                xml.append(f'    <title>{title}</title>')
                xml.append('  </programme>')

    xml.append("</tv>")

    with open("hoy.xml", "w", encoding="utf-8") as f:
        f.write("\n".join(xml))

if __name__ == "__main__":
    build_epg()
