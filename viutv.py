import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import pytz

class ViuTVPlatform:
    def __init__(self):
        # Try the NowTV direct linear schedule API (different from the guide API)
        self.url = "https://api.nowtv.now.com/pub/v1/node/get_linear_schedule"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Referer": "https://nowplayer.now.com/"
        }

    async def fetch_all_programs(self, days=2):
        all_programs = []
        channels = {"099": "099", "096": "096"}
        tz = pytz.timezone('Asia/Hong_Kong')
        
        for ch_id, api_id in channels.items():
            try:
                # Fetching 24 hours of data starting from now
                params = {
                    "channelId": api_id,
                    "hours": 48
                }
                print(f"Attempting API fetch for {ch_id}...")
                response = requests.get(self.url, params=params, headers=self.headers, timeout=15)
                
                if response.status_code == 200:
                    data = response.json().get('data', {})
                    # This API returns a list of programs directly in 'schedule'
                    schedule = data.get('schedule', [])
                    
                    if schedule:
                        print(f"Found {len(schedule)} programs for {ch_id} via Linear API")
                        for prog in schedule:
                            # Timestamps are in milliseconds
                            s_ts = int(prog.get('startTime')) / 1000
                            e_ts = int(prog.get('endTime')) / 1000
                            
                            all_programs.append({
                                'channel_id': ch_id,
                                'title': prog.get('title', 'No Title'),
                                'desc': prog.get('synopsis', ''),
                                'start': datetime.fromtimestamp(s_ts, tz),
                                'end': datetime.fromtimestamp(e_ts, tz)
                            })
                        continue # Success for this channel
            except Exception as e:
                print(f"Linear API failed for {ch_id}: {e}")

        # EMERGENCY FALLBACK: If API failed, try the mirror again with broader ID matching
        if not all_programs:
            try:
                print("API failed. Trying Mirror with broad matching...")
                mirror_res = requests.get("https://epg.pw/xmltv/hk.xml", timeout=20)
                if mirror_res.status_code == 200:
                    root = ET.fromstring(mirror_res.content)
                    for prog in root.findall('programme'):
                        m_id = prog.get('channel', '').lower()
                        target_id = None
                        
                        if "viutv" in m_id and "six" not in m_id: target_id = "099"
                        elif "viutvsix" in m_id or "viu" in m_id and "six" in m_id: target_id = "096"
                        
                        if target_id:
                            s_str = prog.get('start').split(' ')[0]
                            e_str = prog.get('stop').split(' ')[0]
                            fmt = "%Y%m%d%H%M%S"
                            all_programs.append({
                                'channel_id': target_id,
                                'title': prog.findtext('title', 'No Title'),
                                'desc': prog.findtext('desc', ''),
                                'start': datetime.strptime(s_str, fmt).replace(tzinfo=pytz.UTC),
                                'end': datetime.strptime(e_str, fmt).replace(tzinfo=pytz.UTC)
                            })
            except Exception as e:
                print(f"Mirror fallback failed: {e}")

        # FINAL FAILSAFE
        if not all_programs:
            now = datetime.now(pytz.UTC)
            for cid in ["099", "096"]:
                all_programs.append({
                    'channel_id': cid,
                    'title': "EPG Maintenance",
                    'desc': "Schedule temporary unavailable",
                    'start': now,
                    'end': now + timedelta(hours=6)
                })

        return all_programs
