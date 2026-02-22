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
    486843,    # Cartoon Netwrk (UK)
    3403,      # Cartoon Netwrk (Astro)
    368348,    # 美亞電影台
    456567,    # HBO
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
    456566,    # 龍祥時代電影台
    456574,    # CINEMAX
    456570,    # 好萊塢電影台
    457372,    # Catchplay HD電影台
    456569,    # AXN台灣台
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
    merge_epg()
