import requests
import pytz
from datetime import datetime, timedelta

class ViuTVPlatform:
    def __init__(self):
        # This is the ACTUAL API used by viu.tv/epg/99
        self.url = "https://cht-api.viu.tv/api/v1.1/broadcast/program-line-up"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Origin": "https://viu.tv",
            "Referer": "https://viu.tv/"
        }
        # 99 = ViuTV, 96 = ViuTVsix
        self.channel_map = {
            "99": "099",
            "96": "096"
        }

    async def fetch_all_programs(self, days=2):
        all_progs = []
        kl_tz = pytz.timezone('Asia/Kuala_Lumpur')
        
        # ViuTV API takes a date range
        start_date = datetime.now(kl_tz)
        
        for ch_id_raw, m3u_id in self.channel_map.items():
            # The API uses a GET request with channel_id and duration
            params = {
                "channel_id": ch_id_raw,
                "duration": days * 24 # hours
            }
            
            try:
                response = requests.get(self.url, params=params, headers=self.headers, timeout=20)
                if response.status_code != 200:
                    print(f"ViuTV API Error: {response.status_code}")
                    continue
                    
                data = response.json()
                # The data is in ['entries']
                entries = data.get('entries', [])
                
                for entry in entries:
                    # Timestamps are in ISO format: "2024-07-19T05:30:00+08:00"
                    start_str = entry.get('start')
                    end_str = entry.get('end')
                    
                    # Parse ISO format
                    start_dt = datetime.fromisoformat(start_str).astimezone(kl_tz)
                    end_dt = datetime.fromisoformat(end_str).astimezone(kl_tz)
                    
                    prog = type('Prog', (), {
                        'channel_id': m3u_id,
                        'title': entry.get('title', 'No Title'),
                        'desc': entry.get('short_description', '') or entry.get('description', ''),
                        'date': start_dt.strftime("%Y-%m-%d"),
                        'start_time': start_dt,
                        'end_time': end_dt
                    })
                    all_progs.append(prog)
                        
            except Exception as e:
                print(f"Error fetching ViuTV {ch_id_raw}: {e}")
                    
        return all_progs
