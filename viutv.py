import requests
import pytz
from datetime import datetime, timedelta

class ViuTVPlatform:
    def __init__(self):
        # Updated to v3 API which is currently used by the web player
        self.url = "https://api.viu.now.com/p8/3/getChannelSchedule"
        self.headers = {
            "Content-Type": "application/json",
            "Origin": "https://viutv.hk",
            "Referer": "https://viutv.hk/",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

    async def fetch_all_programs(self, days=2):
        all_progs = []
        kl_tz = pytz.timezone('Asia/Kuala_Lumpur')
        
        for channel_id in ["099", "096"]:
            for offset in range(days):
                payload = {
                    "channelNo": channel_id,
                    "dayOffset": str(offset),
                    "deviceId": "anonymous",
                    "callerReferenceNo": "web"
                }
                try:
                    # MUST be a POST request
                    r = requests.post(self.url, json=payload, headers=self.headers, timeout=15)
                    if r.status_code == 200:
                        data = r.json()
                        # The data structure in v3 is slightly deeper
                        schedule = data.get("status", {}).get("schedule", [])
                        
                        for item in schedule:
                            # API provides millisecond timestamps
                            start_ts = int(item["start"]) / 1000
                            duration = int(item["duration"])
                            
                            # Convert to KL Time to match your HOY logic
                            start = datetime.fromtimestamp(start_ts, tz=pytz.utc).astimezone(kl_tz)
                            end = start + timedelta(seconds=duration)
                            
                            # Matches your HOY 'Prog' object structure exactly
                            prog = type('Prog', (), {
                                'channel_id': channel_id, 
                                'title': item.get("title", "No Title"), 
                                'desc': item.get("synopsis", ""),
                                'date': start.strftime("%Y-%m-%d"),
                                'start_time': start, 
                                'end_time': end
                            })
                            all_progs.append(prog)
                except Exception as e:
                    print(f"ViuTV Error: {e}")
                    continue
        return all_progs
