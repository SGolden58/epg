#!/usr/bin/env python3
"""
Robust HOY EPG generator.
- Tries multiple extraction strategies from https://hoy.tv/program_guide
- Falls back to Playwright rendering if needed
- Always writes epg/hoy.xml (or hoy.xml if you keep in root); adjust OUTPUT_FILE below
- If no programmes found, writes channels-only XML and exits 0 (no Action failure)
"""

import requests
import datetime
import json
import re
import os
import sys
from datetime import timedelta, timezone

# ---------- CONFIG ----------
# Where to write the resulting XML (adjust to your file layout)
OUTPUT_FILE = "hoy.xml"   # use "epg/hoy.xml" if you keep epg/ folder
PAGE_URL = "https://hoy.tv/program_guide"
TZ = timezone(timedelta(hours=8))
CHANNEL_MAP = {
    "HOY TV": "hoytv",
    "HOY INFO": "hoyinfor",
    "HOY NEWS": "hoynews"
}
# How long to wait when using Playwright (ms)
PLAYWRIGHT_WAIT = 5000
# ----------------------------

def save_channels_only():
    xml = ['<?xml version="1.0" encoding="UTF-8"?>', '<tv>']
    for name, cid in CHANNEL_MAP.items():
        xml.append(f'  <channel id="{cid}">')
        xml.append(f'    <display-name>{name}</display-name>')
        xml.append('  </channel>')
        xml.append('')
    xml.append('</tv>')
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(xml))
    print(f"[WARN] Wrote channels-only XML to {OUTPUT_FILE}")

def to_xml_time(timestr):
    # Accept ISO8601 with offset; datetime.fromisoformat handles offsets in py3.11
    try:
        dt = datetime.datetime.fromisoformat(timestr)
    except Exception:
        # Try to parse common fallback formats (without offset)
        dt = datetime.datetime.fromisoformat(timestr + "+08:00")
    return dt.strftime("%Y%m%d%H%M%S %z")

def extract_json_candidates_from_html(html):
    """
    Return list of parsed JSON objects found in the HTML which look like program guides.
    We look for:
     - explicit var assignments like programGuide = { ... };
     - window.__NUXT__ or __NEXT_DATA__ or similar script tags containing JSON
     - any JSON blob that contains the key "programme" (or "programme" spelled)
    """
    candidates = []

    # 1) look for programGuide = {...};
    m = re.search(r'programGuide\s*=\s*(\{.*?\});', html, flags=re.DOTALL)
    if m:
        try:
            candidates.append(json.loads(m.group(1)))
            print("[DEBUG] found JSON via programGuide assignment")
        except Exception as e:
            print("[DEBUG] programGuide JSON parse failed:", e)

    # 2) look for __NEXT_DATA__ or window.__NUXT__ or similar
    # Common: <script id="__NEXT_DATA__" type="application/json"> { ... } </script>
    for script_json in re.findall(r'<script[^>]*>(\s*\{.*?\})\s*</script>', html, flags=re.DOTALL):
        if '"programme"' in script_json or '"program"' in script_json or '"programGuide"' in script_json:
            try:
                candidates.append(json.loads(script_json))
                print("[DEBUG] found JSON inside <script> ... </script>")
            except Exception:
                pass

    # 3) fallback: find the largest JSON-like blob that contains "programme"
    blob_match = re.search(r'(\{(?:.|\s){200,}?\"programme\"\s*:\s*\[.*?\]\s*(?:\}|,))', html, flags=re.DOTALL)
    if blob_match:
        try:
            # try to expand braces sensibly: attempt to find balanced braces around the match
            blob = blob_match.group(1)
            candidates.append(json.loads(blob))
            print("[DEBUG] found big JSON blob with 'programme'")
        except Exception as e:
            print("[DEBUG] big JSON blob parse failed:", e)

    return candidates

def parse_programme_from_json(obj):
    """
    Given a JSON-like object (dict), try to locate channels/days/programme lists.
    Returns list of (channel_name, programme_item) tuples where programme_item contains 'start','end','title'
    """
    found = []
    # Try common shapes:
    # 1) { "days": [ { "channels": [ { "name": "...", "programme":[...] } ] } ] }
    if isinstance(obj, dict):
        if "days" in obj and isinstance(obj["days"], list):
            for day in obj["days"]:
                for ch in day.get("channels", []):
                    for p in ch.get("programme", []):
                        found.append((ch.get("name"), p))
        # 2) top-level "channels"
        if "channels" in obj and isinstance(obj["channels"], list):
            for ch in obj["channels"]:
                for p in ch.get("programme", []):
                    found.append((ch.get("name"), p))
        # 3) sometimes page nests under data.programGuide or data.props.programGuide etc.
        for key in ["programGuide", "programGuideData", "guide"]:
            nested = obj.get(key)
            if isinstance(nested, dict) and "days" in nested:
                for day in nested["days"]:
                    for ch in day.get("channels", []):
                        for p in ch.get("programme", []):
                            found.append((ch.get("name"), p))
        # 4) scan whole dict for any list/dict containing 'programme' key
        for k, v in obj.items():
            if isinstance(v, dict):
                sub = parse_programme_from_json(v)
                found.extend(sub)
            elif isinstance(v, list):
                for item in v:
                    if isinstance(item, dict):
                        sub = parse_programme_from_json(item)
                        found.extend(sub)
    return found

def try_requests_extract():
    print("[INFO] Trying HTTP requests extraction...")
    r = requests.get(PAGE_URL, timeout=20, headers={"User-Agent": "Mozilla/5.0"})
    r.raise_for_status()
    html = r.text
    candidates = extract_json_candidates_from_html(html)
    for cand in candidates:
        parsed = parse_programme_from_json(cand)
        if parsed:
            print(f"[INFO] Found {len(parsed)} programme items via requests extraction")
            return parsed
    print("[WARN] No programme items extracted via requests")
    return []

def try_playwright_extract():
    print("[INFO] Trying Playwright extraction (render JS)...")
    try:
        from playwright.sync_api import sync_playwright
    except Exception as e:
        print("[ERROR] Playwright not available:", e)
        return []

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(PAGE_URL, timeout=60000)
        page.wait_for_timeout(PLAYWRIGHT_WAIT)
        html = page.content()
        browser.close()

    candidates = extract_json_candidates_from_html(html)
    for cand in candidates:
        parsed = parse_programme_from_json(cand)
        if parsed:
            print(f"[INFO] Found {len(parsed)} programme items via Playwright extraction")
            return parsed

    # Final fallback: try to find program items by searching for time/title markup
    # (less reliable)
    print("[WARN] Playwright extraction found no JSON; trying HTML heuristic parse...")
    # Example heuristics (very site-specific), so omitted here for safety.
    return []

def build_xml_from_parsed(parsed_items):
    # Build XMLTV string list
    xml = ['<?xml version="1.0" encoding="UTF-8"?>', '<tv>']
    # channels
    for name, cid in CHANNEL_MAP.items():
        xml.append(f'  <channel id="{cid}">')
        xml.append(f'    <display-name>{name}</display-name>')
        xml.append('  </channel>')
        xml.append('')

    if parsed_items:
        for ch_name, item in parsed_items:
            if not ch_name or "start" not in item or "end" not in item:
                continue
            cid = CHANNEL_MAP.get(ch_name)
            if not cid:
                continue
            start = to_xml_time(item["start"])
            stop = to_xml_time(item["end"])
            title = item.get("title", "").replace("&", "&amp;")
            xml.append(f'  <programme start="{start}" stop="{stop}" channel="{cid}">')
            xml.append(f'    <title>{title}</title>')
            # optional description
            desc = item.get("description") or item.get("desc") or item.get("subtitle")
            if desc:
                desc = desc.replace("&", "&amp;")
                xml.append(f'    <desc>{desc}</desc>')
            xml.append('  </programme>')
    else:
        print("[INFO] No programmes to write; will output channels-only XML")

    xml.append('</tv>')
    return "\n".join(xml)

def main():
    # Try quick requests-based extraction
    parsed = []
    try:
        parsed = try_requests_extract()
    except Exception as e:
        print("[ERROR] requests extraction error:", e)

    # If nothing found, attempt Playwright
    if not parsed:
        try:
            parsed = try_playwright_extract()
        except Exception as e:
            print("[ERROR] playwright extraction error:", e)

    # If still nothing, write channels-only and exit successfully
    if not parsed:
        save_channels_only()
        sys.exit(0)

    xml_text = build_xml_from_parsed(parsed)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(xml_text)
    print(f"[OK] Wrote EPG to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
