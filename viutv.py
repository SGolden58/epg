import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import pytz
import re

class ViuTVPlatform:
    def __init__(self):
        self.url = "https://www.open-epg.com/files/hongkong4.xml"
        # Set KL timezone
        self.kl_tz = pytz.timezone('Asia/Kuala_Lumpur')

    async def fetch_all_programs(self, days=2):
        all_programs = []
        # These IDs must match your M3U file's tvg-id
        target_map = {
            "ViuTV.hk": "099",
            "ViuTVsix.hk": "096"
        }
        
        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            response = requests.get(self.url, headers=headers, timeout=45)
            
            if response.status_code == 200:
                root = ET.fromstring(response.content)
                
                for prog in root.findall('programme'):
                    channel_attr = prog.get('channel', '')
                    
                    if channel_attr in target_map:
                        ch_id = target_map[channel_attr]
                        
                        start_attr = prog.get('start')
                        stop_attr = prog.get('stop')
                        
                        if start_attr and stop_attr:
                            # Extract 14 digits
                            s_digits = re.search(r'(\d{14})', start_attr).group(1)
                            e_digits = re.search(r'(\d{14})', stop_attr).group(1)
                            
                            fmt = "%Y%m%d%H%M%S"
                            
                            # 1. Parse from XML as UTC
                            s_dt = pytz.utc.localize(datetime.strptime(s_digits, fmt))
                            e_dt = pytz.utc.localize(datetime.strptime(e_digits, fmt))
                            
                            # 2. Convert to KL Time
                            start_kl = s_dt.astimezone(self.kl_tz)
                            end_kl = e_dt.astimezone(self.kl_tz)

                            # 3. Format specifically for Televizo XML output
                            # This creates the string "20260718150000 +0800"
                            televizo_start = start_kl.strftime("%Y%m%d%H%M%S +0800")
                            televizo_end = end_kl.strftime("%Y%m%d%H%M%S +0800")

                            all_programs.append({
                                'channel_id': ch_id,
                                'title': prog.findtext('title', 'No Title'),
                                'desc': prog.findtext('desc', ''),
                                'start': televizo_start, # String with offset
                                'end': televizo_end,     # String with offset
                                'raw_start': start_kl    # Keep object for sorting if needed
                            })
                
                print(f"Matched {len(all_programs)} programs.")
        except Exception as e:
            print(f"Error: {e}")
                    
        return all_programs
