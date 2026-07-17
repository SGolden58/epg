import requests
from datetime import datetime, timedelta
import pytz

class ViuTVPlatform:
    def __init__(self):
        # This is the web player's schedule API, which is usually less restricted
        self.url = "https://api.viu.now.com/p8/2/get_program_details"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Referer": "https://viutv.hk/",
            "Origin": "https://viutv.hk"
        }

    async def fetch_all_programs(self, days=2):
        all_programs = []
        # Map your channel IDs to their internal API IDs
        # 99 -> ViuTV, 96 -> ViuTVsix
        channels = {"099": "99", "096": "96"}
        
        tz = pytz.timezone('Asia/Hong_Kong')
        now = datetime.now(tz)
        
        for i in range(days):
            # Format: YYYYMMDD
            date_str = (now + timedelta(days=i)).strftime("%Y%m%d")
            
            for ch_id, api_id in channels.items():
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
                        # This API returns programs in the 'data' field
                        programs = json_data.get('data', [])
                        
                        if programs and isinstance(programs, list):
                            print(f"Found {len(programs)} programs for {ch_id}")
                            for prog in programs:
                                # This API uses seconds for start_time/end_time
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
                        else:
                            print(f"API returned no data for {ch_id}")
                    else:
                        print(f"HTTP Error {response.status_code}")
                except Exception as e:
                    print(f"Request failed for {ch_id}: {e}")

        # If still empty after trying the API, then we keep the fallback
        if not all_programs:
            for ch_id in ["099", "096"]:
                all_programs.append({
                    'channel_id': ch_id,
                    'title': "EPG Updating",
                    'desc': "Schedule currently unavailable",
                    'start': now,
                    'end': now + timedelta(hours=24)
                })
                    
        return all_programs
