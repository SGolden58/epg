import requests
import pytz
from datetime import datetime, timedelta

class ViuTVPlatform:
    def __init__(self):
        # List of APIs to try in order
        self.api_versions = [
            "https://api.viu.now.com/p8/3/getChannelSchedule",
            "https://api.viu.now.com/p8/2/getChannelSchedule"
        ]
        
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
                    "deviceId": "1234567890abcdef", # Use a dummy hex ID
                    "callerReferenceNo": "web"
                }
                
                schedule = []
                # Try each API version until we get data
                for url in self.api_versions:
                    try:
                        r = requests.post(url, json=payload, headers=self.headers, timeout=10)
                        if r.status_code == 200:
                            data = r.json()
                            schedule = data.get("status", {}).get("schedule", [])
                            if schedule: # If we got data, stop trying other versions
                                break
                    except:
                        continue
                
                # Process the schedule if found
                for item in schedule:
                    try:
                        start_ts = int(item["start"]) / 1000
                        duration = int(item["duration"])
                        
                        start = datetime.fromtimestamp(start_ts, tz=pytz.utc).astimezone(kl_tz)
                        end = start + timedelta(seconds=duration)
                        
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
