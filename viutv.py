import requests
import xml.etree.ElementTree as ET
from datetime import datetime
import pytz

class ViuTVPlatform:
    def __init__(self):
        # Use a reliable XML mirror instead of the blocked API
        self.url = "https://epg.pw/xmltv/hk.xml"

    async def fetch_all_programs(self, days=2):
        all_programs = []
        # Map the mirror's IDs to your IDs
        # epg.pw uses 'ViuTV.hk' and 'ViuTVsix.hk'
        target_map = {
            "ViuTV.hk": "099",
            "ViuTVsix.hk": "096"
        }
        
        try:
            print("Fetching ViuTV data from mirror...")
            response = requests.get(self.url, timeout=30)
            if response.status_code == 200:
                root = ET.fromstring(response.content)
                
                for prog in root.findall('programme'):
                    mirror_id = prog.get('channel')
                    if mirror_id in target_map:
                        ch_id = target_map[mirror_id]
                        
                        # Parse times: 20240520103000 +0000
                        start_str = prog.get('start').split(' ')[0]
                        end_str = prog.get('stop').split(' ')[0]
                        
                        # Convert to datetime objects
                        fmt = "%Y%m%d%H%M%S"
                        start_dt = datetime.strptime(start_str, fmt).replace(tzinfo=pytz.UTC)
                        end_dt = datetime.strptime(end_str, fmt).replace(tzinfo=pytz.UTC)

                        all_programs.append({
                            'channel_id': ch_id,
                            'title': prog.findtext('title', 'No Title'),
                            'desc': prog.findtext('desc', ''),
                            'start': start_dt,
                            'end': end_dt
                        })
                
                print(f"Successfully mirrored {len(all_programs)} programs for ViuTV.")
        except Exception as e:
            print(f"Mirror fetch failed: {e}")

        # Final Fallback if mirror also fails
        if not all_programs:
            now = datetime.now(pytz.timezone('Asia/Hong_Kong'))
            for ch_id in ["099", "096"]:
                all_programs.append({
                    'channel_id': ch_id,
                    'title': "EPG Updating",
                    'desc': "Please check back later",
                    'start': now,
                    'end': now + datetime.timedelta(hours=24)
                })
                    
        return all_programs
