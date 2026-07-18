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
                        start_attr = prog.get('start')
                        stop_attr = prog.get('stop')
                        
                        if start_attr and stop_attr:
                            # Extract the 14 digits
                            s_match = re.search(r'(\d{14})', start_attr)
                            e_match = re.search(r'(\d{14})', stop_attr)
                            
                            if s_match and e_match:
                                fmt = "%Y%m%d%H%M%S"
                                # This file uses +0800 (HK Time)
                                hk_tz = pytz.timezone('Asia/Hong_Kong')
                                
                                start_dt = hk_tz.localize(datetime.strptime(s_match.group(1), fmt))
                                end_dt = hk_tz.localize(datetime.strptime(e_match.group(1), fmt))

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
