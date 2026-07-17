import requests
import xml.etree.ElementTree as ET
from collections import defaultdict

# Your selected epg.pw channel IDs
CHANNEL_IDS = [
    370136,    # TV1
    370135,    # TV2
    369690,    # TV3
    369635,    # NTV7
    369693,    # TV9
    1122,      # 8TV
    2124,      # Astro AOD 311
    2226,      # Astro AEC HD
    399519,    # Astro QJ
    1951,      # Astro Hua Hee Dai HD
    3290,      # iQIYI HD
    1298,      # 天映频道
    368361,    # TVB Plus
    369701,    # TVB Jade
    369805,    # TVB Jade(SG)
    368366,    # 翡翠台
    368369,    # 明珠台
    368323,    # 娛樂新聞台
    3493,      # TVB Xing He HD
    369796,    # TVB Xing He HD(SG)
    368325,    # 千禧經典台
    410274,    # ViuTV
    410273,    # ViuTVsix
    486843,    # Cartoon Netwrk
    368348,    # 美亞電影台
    456568,    # 東森洋片台
    456564,    # 東森電影台
    457361,    # 龍華電影HD
    457314,    # 龍華偶像HD
    457313,    # 龍華戲劇HD
    457364,    # 龍華洋片HD
    456572,    # 緯來育樂台
    370139,    # 民視
    457211,    # 台視HD
    457213,    # 中視HD
    457214,    # 華視HD
    456533,    # 東森超視
    456578,    # momo綜合台
    369718,    # TVBS Asia
]

def merge_epg():
    root = ET.Element("tv")

    for cid in CHANNEL_IDS:
        url = (
            "https://epg.pw/api/epg.xml"
            f"?lang=zh-hant&timezone=Asia/Kuala_Lumpur&channel_id={cid}"
        )
        print("Downloading:", url)

        try:
            r = requests.get(url, timeout=20)
            r.raise_for_status()
        except Exception as e:
            print(f"Failed to download {cid}: {e}")
            continue

        try:
            tree = ET.fromstring(r.content)
        except Exception as e:
            print(f"XML parse error for {cid}: {e}")
            continue

        # append channel + programmes into final XML
        for elem in tree:
            root.append(elem)

    # Save final merged EPG
    ET.ElementTree(root).write("epg.xml", encoding="utf-8", xml_declaration=True)
    print("DONE: epg.xml created.")

if __name__ == "__main__":
    merge_epg()import xml.etree.ElementTree as ET
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

def add_custom_section(root, ch_id, progs):
    """Adds channel and its programmes in the exact epg.pw style."""
    meta = CUSTOM_CHANNELS.get(ch_id)
    if not meta: return

    # 1. Add Channel Tag
    ch = ET.SubElement(root, "channel", {"id": str(ch_id)})
    ch.text = "\n    "
    dn = ET.SubElement(ch, "display-name", {"lang": "Malaysia"})
    dn.text = meta["name"]
    dn.tail = "\n    "
    ic = ET.SubElement(ch, "icon", {"src": meta["logo"]})
    ic.tail = "\n  "
    ch.tail = "\n  "

    # 2. Add Programme Tags
    for p in progs:
        # Handle different data structures for HOY and ViuTV
        p_id = p.channel_id if hasattr(p, 'channel_id') else p['channel_id']
        if str(p_id) != str(ch_id): continue

        title = p.title if hasattr(p, 'title') else p['title']
        desc = p.desc if hasattr(p, 'desc') else p['desc']
        start = p.start_time if hasattr(p, 'start_time') else p['start']
        end = p.end_time if hasattr(p, 'end_time') else p['end']
        
        # Convert to UTC +0000 to match epg.pw
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

    # 1. Add HOY Channels (76, 77, 78)
    for cid in ["76", "77", "78"]:
        add_custom_section(root, cid, hoy_progs)

    # 2. Add ViuTV Channels (099, 096)
    for cid in ["099", "096"]:
        add_custom_section(root, cid, viu_progs)

    # 3. Add epg.pw Channels
    for cid in CHANNEL_IDS:
        url = f"https://epg.pw/api/epg.xml?lang=zh-hant&timezone=Asia/Kuala_Lumpur&channel_id={cid}"
        try:
            r = requests.get(url, timeout=20)
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
