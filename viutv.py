import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import pytz
import re

class ViuTVPlatform:
    def __init__(self):
        # Using BeeVip as a reliable third-party source for HK EPG
        self.url = "http://epg.beevip.com/hk.xml"

    async def fetch_all_programs(self, days=2):
        all_programs = []
        # Map BeeVip IDs to your IDs
        # BeeVip usually uses 'ViuTV' and 'ViuTVsix'
        target_map = {
            "ViuTV": "099",
            "ViuTVsix": "096"
        }
        
        try:
            print(f"Fetching ViuTV data from BeeVip Mirror...")
            response = requests.get(self.url, timeout=30)
            if response.status_code == 200:
                root = ET.fromstring(response.content)
                
                for prog in root.findall('programme'):
                    channel_attr = prog.get('channel', '')
                    
                    # Match channel ID
                    ch_id = None
                    if channel_attr == "ViuTV" or "99" in channel_attr:
                        ch_id = "099"
                    elif "ViuTVsix" in channel_attr or "96" in channel_attr:
                        ch_id = "096"
                        
                    if ch_id:
                        # Parse times: 20240520103000 +0800
                        start_attr = prog.get('start')
                        stop_attr = prog.get('stop')
                        
                        if start_attr and stop_attr:
                            # Extract the first 14 digits (YYYYMMDDHHMMSS)
                            s_match = re.search(r'(\d{14})', start_attr)
                            e_match = re.search(r'(\d{14})', stop_attr)
                            
                            if s_match and e_match:
                                fmt = "%Y%m%d%H%M%S"
                                # BeeVip is usually in HK time (+0800)
                                # We convert it to UTC for your epg.xml consistency
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
                
                print(f"Successfully found {len(all_programs)} programs for ViuTV.")
        except Exception as e:
            print(f"BeeVip Mirror fetch failed: {e}")

        # Final Fallback if all else fails
        if not all_programs:
            now = datetime.now(pytz.UTC)
            for cid in ["099", "096"]:
                all_programs.append({
                    'channel_id': cid,
                    'title': "ViuTV Schedule",
                    'desc': "Schedule currently being synchronized",
                    'start': now,
                    'end': now + timedelta(hours=12)
                })
                    
        return all_programs
