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

def indent_element(elem, level=1):
    """Manually adds newlines and spaces to make HOY data look like the example."""
    i = "\n" + level * "  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for subelem in elem:
            indent_element(subelem, level + 1)
        if not subelem.tail or not subelem.tail.strip():
            subelem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i

def create_xml_element(root, channel_id, title, start, end, desc="", date_val=""):
    start_str = start.strftime("%Y%m%d%H%M%S +0800")
    end_str = end.strftime("%Y%m%d%H%M%S +0800")
    prog = ET.SubElement(root, "programme", {
        "channel": str(channel_id),
        "start": start_str,
        "stop": end_str
    })
    
    t = ET.SubElement(prog, "title", {"lang": "zh"})
    t.text = title
    
    if desc:
        d = ET.SubElement(prog, "desc", {"lang": "zh"})
        d.text = desc
        
    if date_val:
        dt = ET.SubElement(prog, "date")
        dt.text = date_val
    
    # Apply the multi-line indentation to this specific programme
    indent_element(prog)

async def run_all():
    root = ET.Element("tv", {"generator-info-name": "SGolden58-EPG"})
    root.text = "\n"

    # 1. HOY TV
    try:
        hoy = HOYPlatform()
        ch_list = await hoy.fetch_channels()
        progs = await hoy.fetch_programs(ch_list)
        for p in progs:
            create_xml_element(root, p.channel_id, p.title, p.start_time, p.end_time, p.desc, p.date)
    except: pass

    # 2. ViuTV
    try:
        viu = ViuTVPlatform()
        viu_progs = await viu.fetch_all_programs(days=2)
        for p in viu_progs:
            d_str = p['start'].strftime("%Y-%m-%d")
            create_xml_element(root, p['channel_id'], p['title'], p['start'], p['end'], p['desc'], d_str)
    except: pass

    # 3. epg.pw (Append as-is to preserve its own formatting)
    for cid in CHANNEL_IDS:
        url = f"https://epg.pw/api/epg.xml?lang=zh-hant&timezone=Asia/Kuala_Lumpur&channel_id={cid}"
        try:
            r = requests.get(url, timeout=10)
            if r.status_code == 200:
                temp_xml = ET.fromstring(r.content)
                for child in temp_xml:
                    if child.tag in ["programme", "channel"]:
                        root.append(child)
        except: continue

    tree = ET.ElementTree(root)
    tree.write("epg.xml", encoding="utf-8", xml_declaration=True)

if __name__ == "__main__":
    asyncio.run(run_all())
