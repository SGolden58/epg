import requests
import pytz
from datetime import datetime, timedelta


class ViuTVPlatform:
    def __init__(self):
        self.schedule_url = "https://api.viu.now.com/p8/2/getChannelSchedule"
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Origin": "https://viutv.hk",
            "Referer": "https://viutv.hk/",
            "User-Agent": "Mozilla/5.0"
        }
        # ViuTV uses specific channel numbers in their backend API
        self.target_channels = [
            {"api_id": "099", "m3u_id": "099", "name": "ViuTV"},
            {"api_id": "096", "m3u_id": "096", "name": "ViuTVsix"}
        ]

    async def fetch_channels(self):
        # Returns the core channel mapping structured exactly like your HOY code
        channels = []
        for ch in self.target_channels:
            channels.append({
                "id": ch["m3u_id"],
                "api_id": ch["api_id"],
                "name": ch["name"]
            })
        return channels

    async def fetch_programs(self, channels):
        all_progs = []
        # Both HK and KL share the exact same UTC+8 timezone offset
        kl_tz = pytz.timezone('Asia/Kuala_Lumpur')
        
        for ch in channels:
            # ViuTV's API returns schedule data per single day. 
            # We loop from day 0 (today) to day 2 (next 2 days) to pull a full guide window.
            for day_offset in ["0", "1", "2"]:
                payload = {
                    "channelNo": ch["api_id"],
                    "dayOffset": day_offset,
                    "deviceId": "anonymous",
                    "callerReferenceNo": "web"
                }
                
                try:
                    r = requests.post(self.schedule_url, json=payload, headers=self.headers, timeout=10)
                    data = r.json()
                    
                    # Extract the listings array out of the response payload
                    listings = data.get("data", {}).get("scheduleList", [])
                    
                    for item in listings:
                        title = item.get("progTitle", "")
                        desc = item.get("progDesc", "")
                        
                        # ViuTV tracks time natively in millisecond UNIX timestamps
                        start_ms = int(item.get("startMilliSec", 0))
                        duration_ms = int(item.get("duration", 0))
                        end_ms = start_ms + duration_ms
                        
                        # Convert timestamps straight to localized datetime objects
                        start = datetime.fromtimestamp(start_ms / 1000.0, tz=kl_tz)
                        end = datetime.fromtimestamp(end_ms / 1000.0, tz=kl_tz)
                        
                        prog = type('Prog', (), {
                            'channel_id': ch['id'], 
                            'title': title, 
                            'desc': desc if desc else "",
                            'date': start.strftime("%Y-%m-%d"),
                            'start_time': start, 
                            'end_time': end
                        })
                        all_progs.append(prog)
                except:
                    continue
                    
        return all_progs
