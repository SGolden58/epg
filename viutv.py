import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import pytz

class ViuTVPlatform:
    def __init__(self):
        # Use a reliable XML mirror instead of the blocked API
        self.url = "https://epg.pw/xmltv/hk.xml"

    async def fetch_all_programs(self, days=2):
        all_programs = []
        # Map the mirror's IDs to your IDs
        target_map = {
            "ViuTV.hk": "099",
            "ViuTVsix.hk": "096"
        }
        
        try:
            print("Fetching ViuTV data from mirror...")
            response = requests.get(self.url, timeout=30)
            if response.status_code == 200:
                # Parse the XML content
                root = ET.fromstring(response.content)
                
                for prog in root.findall('programme'):
                    mirror_id = prog.get('channel')
                    if mirror_id in target_map:
                        ch_id = target_map[mirror_id]
                        
                        # Parse times: 20240520103000 +0000
                        start_attr = prog.get('start')
                        stop_attr = prog.get('stop')
                        
                        if start_attr and stop_attr:
                            start_str = start_attr.split(' ')[0]
                            end_str = stop_attr.split(' ')[0]
                            
                            # Convert to datetime objects
                            fmt = "%Y%m%d%H%M%S"
                            try:
                                start_dt = datetime.strptime(start_str, fmt).replace(tzinfo=pytz.UTC)
                                end_dt = datetime.strptime(end_str, fmt).replace(tzinfo=pytz.UTC)

                                all_programs.append({
                                    'channel_id': ch_id,
                                    'title': prog.findtext('title', 'No Title'),
                                    'desc': prog.findtext('desc', ''),
                                    'start': start_dt,
                                    'end': end_dt
                                })
                            except ValueError:
                                continue
                
                print(f"Successfully mirrored {len(all_programs)} programs for ViuTV.")
        except Exception as e:
            print(f"Mirror fetch failed: {e}")

        # Final Fallback if mirror also fails (Fixed timedelta syntax)
        if not all_programs:
            now = datetime.now(pytz.UTC)
            for ch_id in ["099", "096"]:
                all_programs.append({
                    'channel_id': ch_id,
                    'title': "EPG Updating",
                    'desc': "Please check back later",
                    'start': now,
                    'end': now + timedelta(hours=24)
                })
                    
        return all_programs
