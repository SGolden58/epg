import requests
from datetime import datetime, timedelta
import pytz

class ViuTVPlatform:
    def __init__(self):
        # Using the direct ViuTV web helper API
        self.url = "https://api.viu.now.com/p8/2/get_program_details"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": "https://viutv.hk/",
            "Origin": "https://viutv.hk"
        }

    async def fetch_all_programs(self, days=2):
        all_programs = []
        # 99 is ViuTV, 96 is ViuTVsix
        channels = {"099": "99", "096": "96"}
        
        tz = pytz.timezone('Asia/Hong_Kong')
        now = datetime.now(tz)
        
        for i in range(days):
            date_str = (now + timedelta(days=i)).strftime("%Y%m%d")
            
            for ch_id, api_id in channels.items():
                # This endpoint uses a different structure
                params = {
                    "ch_id": api_id,
                    "day": date_str,
                    "caller": "web"
                }
                try:
                    print(f"Fetching ViuTV {ch_id} for {date_str}...")
                    response = requests.get(self.url, params=params, headers=self.headers, timeout=15)
                    
                    if response.status_code == 200:
                        json_data = response.json()
                        # The web API returns programs in a list under 'data'
                        programs = json_data.get('data', [])
                        
                        if not programs:
                            print(f"No programs found for {ch_id} on {date_str}")
                            continue

                        print(f"Successfully found {len(programs)} programs for {ch_id}")
                        for prog in programs:
                            # Web API uses 'start_time' and 'end_time' in seconds
                            s_ts = int(prog.get('start_time', 0))
                            e_ts = int(prog.get('end_time', 0))
                            
                            if s_ts > 0:
                                all_programs.append({
                                    'channel_id': ch_id,
                                    'title': prog.get('title', 'No Title'),
                                    'desc': prog.get('synopsis', ''),
                                    'start': datetime.fromtimestamp(s_ts, tz),
                                    'end': datetime.fromtimestamp(e_ts, tz)
                                })
                except Exception as e:
                    print(f"Error fetching ViuTV {ch_id}: {e}")
                    
        return all_programs
