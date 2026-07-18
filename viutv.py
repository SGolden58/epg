import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import pytz
import re

class ViuTVPlatform:
    def __init__(self):
        # Open-EPG source
        self.url = "https://www.open-epg.com/files/hongkong4.xml"
        self.kl_tz = pytz.timezone('Asia/Kuala_Lumpur')

    async def fetch_all_programs(self, days=2):
        all_programs = []
        # Mapping Open-EPG IDs to your preferred IDs
        target_map = {
            "ViuTV.hk": "099",
            "ViuTVsix.hk": "096"
        }
        
        try:
            print(f"Fetching ViuTV data from Open-EPG...")
            headers = {"User-Agent": "Mozilla/5.0"}
            # Using a timeout as XML files can be large
            response = requests.get(self.url, headers=headers, timeout=45)
            
            if response.status_code == 200:
                root = ET.fromstring(response.content)
                
                count = 0
                for prog in root.findall('programme'):
                    channel_attr = prog.get('channel', '')
                    
                    if channel_attr in target_map:
                        ch_id = target_map[channel_attr]
                        
                        # XMLTV format: 20260718060000 +0800
                        start_attr = prog.get('start')
                        stop_attr = prog.get('stop')
                        
                        if start_attr and stop_attr:
                            # Extract 14 digits for YYYYMMDDHHMMSS
                            s_match = re.search(r'(\d{14})', start_attr)
                            e_match = re.search(r'(\d{14})', stop_attr)
                            
                            if s_match and e_match:
                                fmt = "%Y%m%d%H%M%S"
                                
                                # 1. Parse the raw time
                                s_dt = datetime.strptime(s_match.group(1), fmt)
                                e_dt = datetime.strptime(e_match.group(1), fmt)
                                
                                # 2. Localize to KL Time (UTC+8)
                                # We assume the source is already HK/KL time (+8)
                                start_kl = self.kl_tz.localize(s_dt)
                                end_kl = self.kl_tz.localize(e_dt)

                                all_programs.append({
                                    'channel_id': ch_id,
                                    'title': prog.findtext('title', 'No Title'),
                                    'desc': prog.findtext('desc', ''),
                                    # Televizo works best when start/end are datetime objects 
                                    # or strings formatted with the +0800 offset
                                    'start': start_kl, 
                                    'end': end_kl
                                })
                                count += 1
                
                print(f"Successfully matched {count} programs for ViuTV.")
        except Exception as e:
            print(f"Open-EPG fetch failed: {e}")

        # Fallback logic
        if not all_programs:
            print("No programs found in XML. Generating placeholder.")
            now = datetime.now(self.kl_tz)
            for cid in ["099", "096"]:
                all_programs.append({
                    'channel_id': cid,
                    'title': "ViuTV Schedule",
                    'desc': "Data Syncing...",
                    'start': now,
                    'end': now + timedelta(hours=6)
                })
                    
        return all_programs
