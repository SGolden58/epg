import xml.etree.ElementTree as ET
import requests
import asyncio
from datetime import datetime

# Import your new scrapers
# Ensure these files are in the same folder
from hoy import HOYPlatform 
from viutv import ViuTVPlatform

# Your existing epg.pw IDs
CHANNEL_IDS = [
    370136, 370135, 369690, 369635, 369693, 1122, 2124, 2226, 
    399519, 1951, 3290, 1298, 368361, 369701, 369805, 368366, 
    368369, 368323, 3493, 369796, 368325, 486843, 3403, 
    368348, 456567, 456568, 456564, 457361, 457314, 457313, 
    457364, 456572, 370139, 457211, 457213, 457214, 456533, 
    456578, 369718, 456566, 456574, 456570, 457372, 456569
]

def create_xml_element(root, channel_id, title, start, end, desc=""):
    """Helper to add a programme to the XML root"""
    # Format time for XMLTV: YYYYMMDDHHMMSS +0800
    start_str = start.strftime("%Y%m%d%H%M%S +0800")
    end_str = end.strftime("%Y%m%d%H%M%S +0800")
    
    prog = ET.SubElement(root, "programme", {
        "start": start_str,
        "stop": end_str,
        "channel": str(channel_id)
    })
    ET.SubElement(prog, "title", {"lang": "zh"}).text = title
    ET.SubElement(prog, "desc", {"lang": "zh"}).text = desc

async def main():
    root = ET.Element("tv", {"generator-info-name": "MyCustomEPG"})

    # --- PART 1: Fetch from epg.pw (Existing logic) ---
    print("Step 1: Fetching epg.pw channels...")
    for cid in CHANNEL_IDS:
        url = f"https://epg.pw/api/epg.xml?lang=zh-hant&timezone=Asia/Kuala_Lumpur&channel_id={cid}"
        try:
            r = requests.get(url, timeout=10)
            if r.status_code == 200:
                temp_xml = ET.fromstring(r.content)
                for child in temp_xml:
                    root.append(child)
        except Exception as e:
            print(f"Error fetching epg.pw {cid}: {e}")

    # --- PART 2: Fetch HOY TV ---
    print("Step 2: Fetching HOY TV...")
    try:
        hoy = HOYPlatform() # Assumes you have a logger in your class
        hoy_channels = await hoy.fetch_channels()
        hoy_programs = await hoy.fetch_programs(hoy_channels)
        
        # Add HOY channels to XML
        for ch in hoy_channels:
            ch_node = ET.SubElement(root, "channel", {"id": ch.channel_id})
            ET.SubElement(ch_node, "display-name").text = ch.name
        
        # Add HOY programs to XML
        for p in hoy_programs:
            create_xml_element(root, p.channel_id, p.title, p.start_time, p.end_time)
    except Exception as e:
        print(f"Error adding HOY TV: {e}")

    # --- PART 3: Fetch ViuTV ---
    print("Step 3: Fetching ViuTV...")
    try:
        viu = ViuTVPlatform(None) # Pass None if logger is optional
        viu_programs = await viu.fetch_all_programs(days=2)
        
        # Add ViuTV programs to XML
        for p in viu_programs:
            create_xml_element(root, p['channel_id'], p['title'], p['start'], p['end'], p['desc'])
    except Exception as e:
        print(f"Error adding ViuTV: {e}")

    # --- PART 4: Save Final File ---
    tree = ET.ElementTree(root)
    tree.write("epg.xml", encoding="utf-8", xml_declaration=True)
    print("✅ DONE: epg.xml created with epg.pw + HOY + ViuTV!")

if __name__ == "__main__":
    asyncio.run(main())
