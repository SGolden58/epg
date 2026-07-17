import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import pytz
import re

class ViuTVPlatform:
    def __init__(self):
        # Using the source you provided
        self.url = "https://www.open-epg.com/files/hongkong4.xml"

    async def fetch_all_programs(self, days=2):
        all_programs = []
        # Mapping Open-EPG numeric IDs to your IDs
        # In hongkong4.xml: ViuTV is "99", ViuTVsix is "96"
        target_map = {
            "99": "099",
            "96": "096"
        }
        
        try:
            print(f"Fetching ViuTV data from Open-EPG...")
            response = requests.get(self.url, timeout=30)
            if response.status_code == 200:
                root = ET.fromstring(response.content)
                
                found_count = 0
                for prog in root.findall('programme'):
                    channel_attr = prog.get('channel', '')
                    
                    if channel_attr in target_map:
                        ch_id = target_map[channel_attr]
                        found_count += 1
                        
                        # Parse times: 20260718053000 +0800
                        start_attr = prog.get('start')
                        stop_attr = prog.get('stop')
                        
                        if start_attr and stop_attr:
                            s_match = re.search(r'(\d{14})', start_attr)
                            e_match = re.search(r'(\d{14})', stop_attr)
                            
                            if s_match and e_match:
                                fmt = "%Y%m%d%H%M%S"
                                # Open-EPG is in HK time (+0800)
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
                
                print(f"Successfully found {found_count} programs from Open-EPG.")
        except Exception as e:
            print(f"Open-EPG fetch failed: {e}")

        # Final Fallback - Only if the list is still empty
        if not all_programs:
            now = datetime.now(pytz.UTC)
            for cid in ["099", "096"]:
                all_programs.append({
                    'channel_id': cid,
                    'title': "ViuTV Schedule",
                    'desc': "Check Open-EPG source",
                    'start': now,
                    'end': now + timedelta(hours=12)
                })
                    
        return all_programs
