from playwright.sync_api import sync_playwright
import datetime, json
from datetime import timedelta, timezone

TZ = timezone(timedelta(hours=8))

CHANNELS = {
    "HOY INFO": ("hoyinfor", 76),
    "HOY TV": ("hoytv", 77),
    "HOY NEWS": ("hoynews", 78),
}

OUTPUT_FILE = "hoy.xml"
URL = "https://hoy.tv/program_guide"

def to_xml_time(timestr):
    dt = datetime.datetime.fromisoformat(timestr)
    dt = dt.astimezone(TZ)
    return dt.strftime("%Y%m%d%H%M%S %z")

def run_playwright_scrape():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(URL, timeout=60000)
        # Wait for schedule table or some known element to appear
        # This selector might need to be adjusted depending on site structure
        page.wait_for_timeout(5000)  # wait 5 seconds for JS load
        content = page.content()
        browser.close()
    return content

def extract_json_from_html(html):
    # Try to find embedded JSON inside <script> tags
    import re
    m = re.search(r'programGuide\s*=\s*(\{.*?\});', html, flags=re.DOTALL)
    if not m:
        return None
    obj = json.loads(m.group(1))
    return obj

def build_epg(data):
    xml = ['<?xml version="1.0" encoding="UTF-8"?>', '<tv>']

    # channels
    for name, (cid, num) in CHANNELS.items():
        xml.append(f'  <channel id="{cid}">')
        xml.append(f'    <display-name>{name}</display-name>')
        xml.append(f'    <number>{num}</number>')
        xml.append('  </channel>')
        xml.append('')

    for day in data.get("days", []):
        for ch in day.get("channels", []):
            name = ch.get("name")
            if name not in CHANNELS:
                continue
            cid, _ = CHANNELS[name]
            for p in ch.get("programme", []):
                start = to_xml_time(p["start"])
                stop = to_xml_time(p["end"])
                title = p.get("title", "").replace("&", "&amp;")
                xml.append(f'  <programme start="{start}" stop="{stop}" channel="{cid}">')
                xml.append(f'    <title>{title}</title>')
                xml.append('  </programme>')

    xml.append('</tv>')
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(xml))
    print("✅ Wrote", OUTPUT_FILE)

def main():
    html = run_playwright_scrape()
    obj = extract_json_from_html(html)
    if not obj:
        with open("debug.html", "w", encoding="utf-8") as f:
            f.write(html)
        print("❌ Failed to find JSON schedule — saved debug.html")
        return
    build_epg(obj)

if __name__ == "__main__":
    main()
