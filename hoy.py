#!/usr/bin/env python3
import requests, json, re, datetime
from datetime import timedelta, timezone

TZ = timezone(timedelta(hours=8))
URL = "https://hoy.tv/program_guide"

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
}

OUTPUT = "hoy.xml"

def to_xml_time(timestr):
    dt = datetime.datetime.fromisoformat(timestr)
    dt = dt.astimezone(TZ)
    return dt.strftime("%Y%m%d%H%M%S %z")

def fetch():
    r = requests.get(URL, headers=HEADERS, timeout=20)
    r.raise_for_status()
    return r.text

def extract_schedule(html):
    # Try to find embedded JSON
    m = re.search(r'window\.__NUXT__\s*=\s*(\{.*?\});', html, flags=re.DOTALL)
    if m:
        data = json.loads(m.group(1))
    else:
        # fallback: generic JSON blob
        m2 = re.search(r'programGuide\s*=\s*(\{.*?\});', html, flags=re.DOTALL)
        if m2:
            data = json.loads(m2.group(1))
        else:
            return None

    # Traverse data to find programmes
    programmes = []
    def walk(obj):
        if isinstance(obj, dict):
            if "programme" in obj and isinstance(obj["programme"], list):
                channel = obj.get("name")
                for p in obj["programme"]:
                    programmes.append((channel, p))
            else:
                for v in obj.values():
                    walk(v)
        elif isinstance(obj, list):
            for i in obj:
                walk(i)

    walk(data)
    return programmes if programmes else None

def build_xml(progs):
    xml = ['<?xml version="1.0" encoding="UTF-8"?>', '<tv>']
    for name, info in CHANNELS.items():
        xml.append(f'  <channel id="{info["id"]}">')
        xml.append(f'    <display-name>{name}</display-name>')
        xml.append(f'    <number>{info["number"]}</number>')
        xml.append('  </channel>')
    for ch_name, p in progs:
        if ch_name not in CHANNELS: continue
        cid = CHANNELS[ch_name]["id"]
        start = to_xml_time(p["start"])
        stop = to_xml_time(p["end"])
        title = p.get("title","").replace("&", "&amp;")
        xml.append(f'  <programme start="{start}" stop="{stop}" channel="{cid}">')
        xml.append(f'    <title>{title}</title>')
        xml.append('  </programme>')
    xml.append('</tv>')
    with open(OUTPUT, "w", encoding="utf-8") as f:
        f.write("\n".join(xml))

def main():
    html = fetch()
    progs = extract_schedule(html)
    if not progs:
        with open("debug.html", "w", encoding="utf-8") as f:
            f.write(html)
        print("❗ No programmes found — saved debug.html for inspection.")
        return
    build_xml(progs)
    print("✅ Generated", OUTPUT)

if __name__ == "__main__":
    main()
