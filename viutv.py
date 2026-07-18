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
        # Map the XML name to your M3U display name (tvg-name)
        target_map = {
            "ViuTV.hk": "ViuTV",
            "ViuTVsix.hk": "ViuTVsix"
        }
        
        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            response = requests.get(self.url, headers=headers, timeout=45)
            
            if response.status_code == 200:
                root = ET.fromstring(response.content)
                
                for prog in root.findall('programme'):
                    xml_name = prog.get('channel', '')
                    
                    if xml_name in target_map:
                        display_name = target_map[xml_name]
                        
                        start_attr = prog.get('start')
                        stop_attr = prog.get('stop')
                        
                        if start_attr and stop_attr:
                            s_digits = re.search(r'(\d{14})', start_attr).group(1)
                            e_digits = re.search(r'(\d{14})', stop_attr).group(1)
                            
                            # Parse as UTC and convert to KL (Fixes the 8-hour fast issue)
                            s_dt = pytz.utc.localize(datetime.strptime(s_digits, "%Y%m%d%H%M%S"))
                            e_dt = pytz.utc.localize(datetime.strptime(e_digits, "%Y%m%d%H%M%S"))
                            
                            start_kl = s_dt.astimezone(self.kl_tz)
                            end_kl = e_dt.astimezone(self.kl_tz)

                            all_programs.append({
                                'channel_id': display_name, # Using Display Name here
                                'title': prog.findtext('title', 'No Title'),
                                'desc': prog.findtext('desc', ''),
                                'start': start_kl, 
                                'end': end_kl
                            })
        except Exception as e:
            print(f"ViuTV Fetch Error: {e}")
                    
        return all_programs
