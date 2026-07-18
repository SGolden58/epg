import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import pytz
import re

class ViuTVPlatform:
    def __init__(self):
        # The source you provided
        self.url = "https://www.open-epg.com/files/hongkong4.xml"

    async def fetch_all_programs(self, days=2):
        all_programs = []
        # EXACT IDs from hongkong4.xml:
        # <channel id="ViuTV.hk">
        # <channel id="ViuTVsix.hk">
        target_map = {
            "ViuTV.hk": "099",
            "ViuTVsix.hk": "096"
        }
        
        try:
            print(f"Fetching ViuTV data from Open-EPG...")
            # Added headers to look like a browser just in case
            headers = {"User-Agent": "Mozilla/5.0"}
            response = requests.get(self.url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                root = ET.fromstring(response.content)
                
                count = 0
                for prog in root.findall('programme'):
                    channel_attr = prog.get('channel', '')
                    
                    if channel_attr in target_map:
                        ch_id = target_map[channel_attr]
                        
                        # Parse times: e.g., 20260718060000 +0800
        all_progs = []
        kl_tz = pytz.timezone('Asia/Kuala_Lumpur')
        for ch in channels:
            if not ch['epg']: continue
            try:
                r = requests.get(ch['epg'], headers=self.headers, timeout=10)
                root = ET.fromstring(r.content)
                for item in root.findall('.//EpgItem'):
                    start_str = item.findtext('EpgStartDateTime')
                    end_str = item.findtext('EpgEndDateTime')
                    
                    ep_info = item.find('EpisodeInfo')
                    title = ep_info.findtext('EpisodeShortDescription')
                    # Ensure we get the long description
                    desc = ep_info.findtext('EpisodeLongDescription')
                    
                    start = kl_tz.localize(datetime.strptime(start_str, "%Y-%m-%d %H:%M:%S"))
                    end = kl_tz.localize(datetime.strptime(end_str, "%Y-%m-%d %H:%M:%S"))

                                all_programs.append({
                                    'channel_id': ch_id,
                                    'title': prog.findtext('title', 'No Title'),
                                    'desc': prog.findtext('desc', ''),
                                    'start': start_dt.astimezone(pytz.UTC),
                                    'end': end_dt.astimezone(pytz.UTC)
                                })
                                count += 1
                
                print(f"Successfully matched {count} programs for ViuTV.")
        except Exception as e:
            print(f"Open-EPG fetch failed: {e}")

        # Only show fallback if absolutely no programs were found
        if not all_programs:
            print("No programs found in XML. Check channel IDs.")
            now = datetime.now(pytz.UTC)
            for cid in ["099", "096"]:
                all_programs.append({
                    'channel_id': cid,
                    'title': "ViuTV Schedule",
                    'desc': "Data Syncing...",
                    'start': now,
                    'end': now + timedelta(hours=6)
                })
                    
        return all_programs
