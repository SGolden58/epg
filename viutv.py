import requests
import pytz
from datetime import datetime, timedelta

class ViuTVPlatform:
    def __init__(self):
        # v3 is the current active version for the web player
        self.url = "https://api.viu.now.com/p8/3/getChannelSchedule"
        self.headers = {
            "Content-Type": "application/json",
            "Origin": "https://viutv.hk",
            "Referer": "https://viutv.hk/",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        }

    async def fetch_all_programs(self, days=2):
        all_progs = []
        kl_tz = pytz.timezone('Asia/Kuala_Lumpur')
        
        # 099 = ViuTV, 096 = ViuTVsix
        for channel_id in ["099", "096"]:
            for offset in range(days):
                payload = {
                    "channelNo": channel_id,
                    "dayOffset": str(offset),
                    "deviceId": "anonymous",
                    "callerReferenceNo": "web"
                }
                
                try:
                    # This MUST be a POST request to work
                    response = requests.post(self.url, json=payload, headers=self.headers, timeout=15)
                    
                    if response.status_code == 200:
                        data = response.json()
                        # The API returns a status object containing the schedule
                        status_obj = data.get("status", {})
                        schedule = status_obj.get("schedule", [])
                        
                        for item in schedule:
                            # API provides start time in milliseconds
                            start_ts = int(item["start"]) / 1000
                            duration = int(item["duration"])
                            
                            # Convert UTC timestamp to KL Time
                            start = datetime.fromtimestamp(start_ts, tz=pytz.utc).astimezone(kl_tz)
                            end = start + timedelta(seconds=duration)
                            
                            # Create object matching your hoy.py structure
                            prog = type('Prog', (), {
                                'channel_id': channel_id, 
                                'title': item.get("title", "No Title"), 
                                'desc': item.get("synopsis", ""),
                                'date': start.strftime("%Y-%m-%d"),
                                'start_time': start, 
                                'end_time': end
                            })
                            all_progs.append(prog)
                    else:
                        print(f"ViuTV API Error: {response.status_code} for channel {channel_id}")
                except Exception as e:
                    print(f"ViuTV Request Failed: {e}")
                    continue
                    
        return all_progs
