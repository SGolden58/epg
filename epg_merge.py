import requests
import xml.etree.ElementTree as ET

# Your selected epg.pw channel IDs
CHANNEL_IDS = [
    1122,      # 8TV
    369594,    # Astro AOD 311
    2226,      # Astro AEC HD
    5106,      # Astro QJ
    1951,      # Astro Hua Hee Dai HD
    143,       # iQIYI HD
    1298,      # Celestial Movies / 天映频道
    368361,    # TVB Plus
    368366,    # TVB Jade / 翡翠台
    368369,    # TVB Pearl / 明珠台
    410274,    # ViuTV
    410273,    # ViuTVsix
    5982,      # 美亞電影台
]

def merge_epg():
    root = ET.Element("tv")

    for cid in CHANNEL_IDS:
        url = f"https://epg.pw/api/epg.xml?channel_id={cid}"
        print(f"Downloading {cid} ...")

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
    merge_epg()
