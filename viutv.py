import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import pytz
import re

class ViuTVPlatform:
    def __init__(self):
        self.url = "https://www.open-epg.com/files/hongkong4.xml"
        self.kl_tz = pytz.timezone('Asia/Kuala_Lumpur')

    async def fetch_all_programs(self, days=2):
        all_programs = []
        target_map = {
            "ViuTV.hk": "ViuTV.hk",
            "ViuTVsix.hk": "ViuTVsix.hk"
        }
        
        try:
            print(f"Fetching ViuTV data from Open-EPG...")
            headers = {"User-Agent": "Mozilla/5.0"}
            response = requests.get(self.url, headers=headers, timeout=45)
            
            if response.status_code == 200:
                root = ET.fromstring(response.content)
                
                count = 0
                for prog in root.findall('programme'):
                    channel_attr = prog.get('channel', '')
                    
                    if channel_attr in target_map:
                        ch_id = target_map[channel_attr]
                        
                        start_attr = prog.get('start') # e.g., "20260718070000 +0000"
                        stop_attr = prog.get('stop')
                        
                        if start_attr and stop_attr:
                            # 1. Extract the 14 digits (YYYYMMDDHHMMSS)
                            s_digits = re.search(r'(\d{14})', start_attr).group(1)
                            e_digits = re.search(r'(\d{14})', stop_attr).group(1)
                            
                            fmt = "%Y%m%d%H%M%S"
                            
                            # 2. Parse as UTC (the source XML is usually stored in UTC internally)
                            # If the XML says 07:00 and it's actually 15:00 KL time, 
                            # we treat 07:00 as UTC.
                            s_dt = pytz.utc.localize(datetime.strptime(s_digits, fmt))
                            e_dt = pytz.utc.localize(datetime.strptime(e_digits, fmt))
                            
                            # 3. Convert to Kuala Lumpur Time (UTC+8)
                            # This will turn 07:00 UTC into 15:00 KL
                            start_kl = s_dt.astimezone(self.kl_tz)
                            end_kl = e_dt.astimezone(self.kl_tz)

                            all_programs.append({
                                'channel_id': ch_id,
                                'title': prog.findtext('title', 'No Title'),
                                'desc': prog.findtext('desc', ''),
                                'start': start_kl, 
                                'end': end_kl
                            })
                            count += 1
                
                print(f"Successfully matched {count} programs for ViuTV.")
        except Exception as e:
            print(f"Open-EPG fetch failed: {e}")

        if not all_programs:
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
