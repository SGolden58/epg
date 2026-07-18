import requests
import pytz
from datetime import datetime, timedelta

class ViuTVPlatform:
    def __init__(self):
        self.url = "https://api.viu.now.com/p8/2/getChannelSchedule"
        self.headers = {
            "Content-Type": "application/json",
            "Origin": "https://viutv.hk",
            "Referer": "https://viutv.hk/",
            "User-Agent": "Mozilla/5.0"
        }

    async def fetch_all_programs(self, days=2):
        all_progs = []
        kl_tz = pytz.timezone('Asia/Kuala_Lumpur')
        
        # We fetch for both 099 and 096
        for channel_id in ["099", "096"]:
            for offset in range(days):
                payload = {
                    "channelNo": channel_id,
                    "dayOffset": str(offset),
                    "deviceId": "anonymous",
                    "callerReferenceNo": "web"
                }
                try:
                    r = requests.post(self.url, json=payload, headers=self.headers, timeout=15)
                    if r.status_code == 200:
                        data = r.json()
                        schedule = data.get("status", {}).get("schedule", [])
                        
                        for item in schedule:
                            # Convert millisecond timestamp to datetime
                            start_ts = int(item["start"]) / 1000
                            duration = int(item["duration"])
                            
                            # Convert to KL Time to match your HOY logic
                            start = datetime.fromtimestamp(start_ts, tz=pytz.utc).astimezone(kl_tz)
                            end = start + timedelta(seconds=duration)
                            
                            # Create object with same attributes as HOY's 'Prog' type
                            prog = type('Prog', (), {
                                'channel_id': channel_id, 
                                'title': item.get("title", "No Title"), 
                                'desc': item.get("synopsis", ""),
                                'date': start.strftime("%Y-%m-%d"),
                                'start_time': start, 
                                'end_time': end
                            })
                            all_progs.append(prog)
                except:
                    continue
        return all_progs
