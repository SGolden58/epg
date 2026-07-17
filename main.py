import xml.etree.ElementTree as ET
import requests
import asyncio
from hoy import HOYPlatform 
from viutv import ViuTVPlatform

CHANNEL_IDS = [
    370136, 370135, 369690, 369635, 369693, 1122, 2124, 2226, 
    399519, 1951, 3290, 1298, 368361, 369701, 369805, 368366, 
    368369, 368323, 3493, 369796, 368325, 486843, 3403, 
    368348, 456567, 456568, 456564, 457361, 457314, 457313, 
    457364, 456572, 370139, 457211, 457213, 457214, 456533, 
    456578, 369718, 456566, 456574, 456570, 457372, 456569
]

# Metadata with exact names as requested
CHANNEL_METADATA = {
    "76": {"name": "HOY 76", "logo": "https://m3u.hk/logo/hoy76.png"},
    "77": {"name": "HOY 77", "logo": "https://m3u.hk/logo/hoy77.png"},
    "78": {"name": "HOY 78", "logo": "https://m3u.hk/logo/hoy78.png"},
    "099": {"name": "ViuTV 99", "logo": "https://m3u.hk/logo/viutv.png"},
    "096": {"name": "ViuTVsix 96", "logo": "https://m3u.hk/logo/viutvsix.png"}
}

def add_formatted_channel(root, ch_id):
    if ch_id not in CHANNEL_METADATA: return
    meta = CHANNEL_METADATA[ch_id]
    ch = ET.SubElement(root, "channel", {"id": str(ch_id)})
    ch.text = "\n    "
    name = ET.SubElement(ch, "display-name", {"lang": "zh"})
    name.text = meta["name"]
    name.tail = "\n    "
    icon = ET.SubElement(ch, "icon", {"src": meta["logo"]})
    icon.tail = "\n  "
    ch.tail = "\n  "

def add_formatted_prog(root, channel_id, title, start, end, desc="", date_val=""):
    prog = ET.SubElement(root, "programme", {
        "channel": str(channel_id),
        "start": start.strftime("%Y%m%d%H%M%S +0800"),
        "stop": end.strftime("%Y%m%d%H%M%S +0800")
    })
    prog.text = "\n    "
    t = ET.SubElement(prog, "title", {"lang": "zh"})
    t.text = title
    t.tail = "\n    "
    if desc:
        d = ET.SubElement(prog, "desc", {"lang": "zh"})
        d.text = desc
        d.tail = "\n    "
    if date_val:
        dt = ET.SubElement(prog, "date")
        dt.text = date_val
        dt.tail = "\n  "
    prog.tail = "\n  "

async def run_all():
    root = ET.Element("tv", {"generator-info-name": "SGolden58-EPG"})
    root.text = "\n  "

    # 1. Fetch HOY Data
    hoy = HOYPlatform()
    ch_list = await hoy.fetch_channels()
    hoy_progs = await hoy.fetch_programs(ch_list)
    
    # 2. Add HOY (Channel then its Programmes)
    for ch_id in ["76", "77", "78"]:
        add_formatted_channel(root, ch_id)
        for p in hoy_progs:
            if p.channel_id == ch_id:
                add_formatted_prog(root, p.channel_id, p.title, p.start_time, p.end_time, p.desc, p.date)

    # 3. Fetch & Add ViuTV (Channel then its Programmes)
    viu = ViuTVPlatform()
    viu_progs = await viu.fetch_all_programs(days=2)
    for ch_id in ["099", "096"]:
        add_formatted_channel(root, ch_id)
        for p in viu_progs:
            if p['channel_id'] == ch_id:
                add_formatted_prog(root, p['channel_id'], p['title'], p['start'], p['end'], p['desc'], p['start'].strftime("%Y-%m-%d"))

    # 4. Add epg.pw Data (Appends as they come from API)
    for cid in CHANNEL_IDS:
        url = f"https://epg.pw/api/epg.xml?lang=zh-hant&timezone=Asia/Kuala_Lumpur&channel_id={cid}"
        try:
            r = requests.get(url, timeout=10)
            if r.status_code == 200:
                temp_xml = ET.fromstring(r.content)
                for child in temp_xml:
                    if child.tag in ["programme", "channel"]:
                        child.tail = "\n  "
                        root.append(child)
        except: continue

    tree = ET.ElementTree(root)
    tree.write("epg.xml", encoding="utf-8", xml_declaration=True)

if __name__ == "__main__":
    asyncio.run(run_all())
