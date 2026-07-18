import requests
import pytz
from datetime import datetime, timedelta

class ViuTVPlatform:
    def __init__(self):
        # Official ViuTV API endpoint
        self.url = "https://api.viu.now.com/p8/2/getProgramList"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": "https://viu.tv/"
        }
        # Channel ID mapping: 99 -> 099, 96 -> 096
        self.channels = {
            "99": "099",
            "96": "096"
        }

    async def fetch_all_programs(self, days=2):
        all_progs = []
        kl_tz = pytz.timezone('Asia/Kuala_Lumpur')
        
        # Get dates for today and tomorrow
        today = datetime.now(kl_tz)
        dates = [(today + timedelta(days=i)).strftime("%Y%m%d") for i in range(days)]

        for ch_id_raw, m3u_id in self.channels.items():
            for date_str in dates:
                payload = {
                    "channelId": ch_id_raw,
                    "day": date_str,
                    "callerReferenceNo": "1"
                }
                
                try:
                    # Using POST as required by their API
                    response = requests.post(self.url, json=payload, headers=self.headers, timeout=20)
                    if response.status_code != 200:
                        continue
                        
                    data = response.json()
                    # The programs are inside ['programList']
                    programs = data.get('programList', [])
                    
                    for item in programs:
                        # ViuTV provides timestamps in milliseconds
                        start_ts = int(item.get('start')) / 1000
                        end_ts = int(item.get('end')) / 1000
                        
                        start_dt = datetime.fromtimestamp(start_ts, tz=pytz.utc).astimezone(kl_tz)
                        end_dt = datetime.fromtimestamp(end_ts, tz=pytz.utc).astimezone(kl_tz)
                        
                        prog = type('Prog', (), {
                            'channel_id': m3u_id,
                            'title': item.get('title', 'No Title'),
                            'desc': item.get('synopsis', ''),
                            'date': start_dt.strftime("%Y-%m-%d"),
                            'start_time': start_dt,
                            'end_time': end_dt
                        })
                        all_progs.append(prog)
                        
                except Exception as e:
                    print(f"Error fetching ViuTV {ch_id_raw} for {date_str}: {e}")
                    
        return all_progs
