import xml.etree.ElementTree as ET
import requests
import asyncio
from hoy import HOYPlatform 
from viutv import ViuTVPlatform
import pytz

# Your selected epg.pw channel IDs
CHANNEL_IDS = [
    370136, 370135, 369690, 369635, 369693, 1122, 2124, 2226, 
    399519, 1951, 3290, 1298, 368361, 369701, 369805, 368366, 
    368369, 368323, 3493, 369796, 368325, 486843, 3403, 
    368348, 456567, 456568, 456564, 457361, 457314, 457313, 
    457364, 456572, 370139, 457211, 457213, 457214, 456533, 
    456578, 369718, 456566, 456574, 456570, 457372, 456569
]

# Metadata for custom channels
CUSTOM_CHANNELS = {
    "76": {"name": "HOY 76", "logo": "https://cdn.jsdelivr.net/gh/SGolden58/svg@main/Logo/HOYTV.svg.png"},
    "77": {"name": "HOY 77", "logo": "https://cdn.jsdelivr.net/gh/SGolden58/svg@main/Logo/HOYTV.svg.png"},
    "78": {"name": "HOY 78", "logo": "https://cdn.jsdelivr.net/gh/SGolden58/svg@main/Logo/HOYTV.svg.png"},
    "099": {"name": "ViuTV", "logo": "https://m3u.hk/logo/viutv.png"},
    "096": {"name": "ViuTVsix", "logo": "https://m3u.hk/logo/viutvsix.png"}
}

def add_custom_channel_tag(root, ch_id):
    """Adds ONLY the channel tag."""
    meta = CUSTOM_CHANNELS.get(ch_id)
    if not meta: return
    ch = ET.SubElement(root, "channel", {"id": str(ch_id)})
    ch.text = "\n    "
    dn = ET.SubElement(ch, "display-name", {"lang": "Malaysia"})
    dn.text = meta["name"]
    dn.tail = "\n    "
    ic = ET.SubElement(ch, "icon", {"src": meta["logo"]})
    ic.tail = "\n  "
    ch.tail = "\n  "

def add_custom_programme_tags(root, ch_id, progs):
    """Adds ONLY the programme tags."""
    for p in progs:
        p_id = p.channel_id if hasattr(p, 'channel_id') else p['channel_id']
        if str(p_id) != str(ch_id): continue

        title = p.title if hasattr(p, 'title') else p['title']
        desc = p.desc if hasattr(p, 'desc') else p['desc']
        start = p.start_time if hasattr(p, 'start_time') else p['start']
        end = p.end_time if hasattr(p, 'end_time') else p['end']
        
        utc_start = start.astimezone(pytz.utc).strftime("%Y%m%d%H%M%S +0000")
        utc_end = end.astimezone(pytz.utc).strftime("%Y%m%d%H%M%S +0000")
        date_val = start.strftime("%Y-%m-%d")

        prog = ET.SubElement(root, "programme", {
            "channel": str(ch_id),
            "start": utc_start,
            "stop": utc_end
        })
        prog.text = "\n    "
        t = ET.SubElement(prog, "title", {"lang": "zh"})
        t.text = title
        t.tail = "\n    "
        if desc:
            d = ET.SubElement(prog, "desc", {"lang": "zh"})
            d.text = desc
            d.tail = "\n    "
        dt = ET.SubElement(prog, "date")
        dt.text = date_val
        dt.tail = "\n  "
        prog.tail = "\n  "

async def run_all():
    root = ET.Element("tv")
    root.text = "\n  "

    # Fetch External Data
    hoy = HOYPlatform()
    hoy_ch_list = await hoy.fetch_channels()
    hoy_progs = await hoy.fetch_programs(hoy_ch_list)
    
    viu = ViuTVPlatform()
    viu_progs = await viu.fetch_all_programs(days=2)

    # --- STEP 1: ADD ALL CHANNELS FIRST ---
    for cid in ["76", "77", "78", "099", "096"]:
        add_custom_channel_tag(root, cid)

    epg_pw_programmes = []
    for cid in CHANNEL_IDS:
        url = f"https://epg.pw/api/epg.xml?lang=zh-hant&timezone=Asia/Kuala_Lumpur&channel_id={cid}"
        try:
            r = requests.get(url, timeout=20)
            if r.status_code == 200:
                temp_xml = ET.fromstring(r.content)
                for child in temp_xml:
                    if child.tag == "channel":
                        child.tail = "\n  "
                        root.append(child)
                    elif child.tag == "programme":
                        epg_pw_programmes.append(child)
        except: continue

    # --- STEP 2: ADD ALL PROGRAMMES SECOND ---
    for cid in ["76", "77", "78"]:
        add_custom_programme_tags(root, cid, hoy_progs)
    
    for cid in ["099", "096"]:
        add_custom_programme_tags(root, cid, viu_progs)

    for p_node in epg_pw_programmes:
        p_node.tail = "\n  "
        root.append(p_node)

    tree = ET.ElementTree(root)
    tree.write("epg.xml", encoding="utf-8", xml_declaration=True)

if __name__ == "__main__":
    asyncio.run(run_all())
