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

def add_formatted_prog(root, channel_id, title, start, end, desc="", date_val=""):
    """Creates a programme element with exact paragraph formatting."""
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

    # 1. Fetch Data
    hoy = HOYPlatform()
    ch_list = await hoy.fetch_channels()
    hoy_progs = await hoy.fetch_programs(ch_list)
    
    viu = ViuTVPlatform()
    viu_progs = await viu.fetch_all_programs(days=2)

    # 2. Add Channel Tags for HOY and ViuTV
    for ch in ch_list:
        c = ET.SubElement(root, "channel", {"id": ch['id']})
        c.text = "\n    "
        ET.SubElement(c, "display-name", {"lang": "zh"}).text = ch['name']
        c.tail = "\n  "

    # 3. Add Programme Tags for HOY
    for p in hoy_progs:
        add_formatted_prog(root, p.channel_id, p.title, p.start_time, p.end_time, p.desc, p.date)

    # 4. Add Programme Tags for ViuTV
    for p in viu_progs:
        add_formatted_prog(root, p['channel_id'], p['title'], p['start'], p['end'], p['desc'], p['start'].strftime("%Y-%m-%d"))

    # 5. Add epg.pw Data (Preserving its original formatting)
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
