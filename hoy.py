import requests
import datetime
from datetime import timedelta, timezone

TZ = timezone(timedelta(hours=8))   # Kuala Lumpur timezone
BASE_URL = "https://hoy.tv/api/program-guide?date="

CHANNEL_MAP = {
    "HOY TV": "hoytv",
    "HOY INFO": "hoyinfor",
    "HOY NEWS": "hoynews"
}

def fetch_day(date_str):
    url = BASE_URL + date_str
    r = requests.get(url, timeout=20)
    r.raise_for_status()
    return r.json()

def to_xml_time(dt_str):
    # dt_str: "2024-12-01T08:00:00+08:00"
    dt = datetime.datetime.fromisoformat(dt_str)
    return dt.strftime("%Y%m%d%H%M%S %z")

def build_epg():
    today = datetime.datetime.now(TZ).date()
    days = [(today + timedelta(days=i)).isoformat() for i in range(7)]

    xml = []
    xml.append('<?xml version="1.0" encoding="UTF-8"?>')
    xml.append('<tv>')

    # channels
    for name, cid in CHANNEL_MAP.items():
        xml.append(f'  <channel id="{cid}">')
        xml.append(f'    <display-name>{name}</display-name>')
        xml.append(f'  </channel>')
        xml.append("")

    # programmes
    for d in days:
        data = fetch_day(d)
        for ch in data.get("channels", []):
            ch_name = ch.get("name")
            ch_id = CHANNEL_MAP.get(ch_name)
            if not ch_id:
                continue

            for item in ch.get("programme", []):
                start = to_xml_time(item["start"])
                end = to_xml_time(item["end"])
                title = item["title"].replace("&", "&amp;")

                xml.append(f'  <programme start="{start}" stop="{end}" channel="{ch_id}">')
                xml.append(f'    <title>{title}</title>')
                xml.append("  </programme>")

    xml.append("</tv>")

    with open("epg/hoy.xml", "w", encoding="utf-8") as f:
        f.write("\n".join(xml))

if __name__ == "__main__":
    build_epg()
