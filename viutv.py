import requests
from datetime import datetime, timedelta
import pytz

class ViuTVPlatform:
    def __init__(self):
        self.url = "https://api.nowtv.now.com/pub/v1/epg/guide"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": "https://viutv.hk/"
        }

    async def fetch_all_programs(self, days=2):
        all_programs = []
        # ViuTV 99 and ViuTVsix 96
        channels = ["099", "096"]
        
        # Calculate dates in HK/KL time
        tz = pytz.timezone('Asia/Hong_Kong')
        now = datetime.now(tz)
        
        for i in range(days):
            date_str = (now + timedelta(days=i)).strftime("%Y%m%d")
            
            for ch_id in channels:
                params = {
                    "channelId": ch_id,
                    "day": date_str
                }
                try:
                    # Using requests directly for simplicity, similar to your merge_epg.py
                    response = requests.get(self.url, params=params, headers=self.headers, timeout=15)
                    if response.status_code == 200:
                        data = response.json()
                        # The API returns a list of programs under 'data'
                        programs = data.get('data', [])
                        
                        for prog in programs:
                            # API uses milliseconds timestamp
                            start_ts = int(prog.get('start')) / 1000
                            end_ts = int(prog.get('end')) / 1000
                            
                            all_programs.append({
                                'channel_id': ch_id,
                                'title': prog.get('title', 'No Title'),
                                'desc': prog.get('synopsis', ''),
                                'start': datetime.fromtimestamp(start_ts, tz),
                                'end': datetime.fromtimestamp(end_ts, tz)
                            })
                except Exception as e:
                    print(f"Error fetching ViuTV {ch_id} for {date_str}: {e}")
                    
        return all_programs
