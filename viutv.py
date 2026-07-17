import requests
from datetime import datetime, timedelta
import pytz

class ViuTVPlatform:
    def __init__(self):
        # Mobile API endpoint - usually more stable
        self.url = "https://api.nowtv.now.com/pub/v1/epg/guide"
        self.headers = {
            "User-Agent": "ViuTV/4.5.1 (iPhone; iOS 15.0; Scale/3.00)",
            "Referer": "https://viutv.hk/"
        }

    async def fetch_all_programs(self, days=2):
        all_programs = []
        channels = ["099", "096"]
        
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
                    response = requests.get(self.url, params=params, headers=self.headers, timeout=15)
                    if response.status_code == 200:
                        data = response.json().get('data', [])
                        # If data is a list, find the one with the matching channelId
                        if isinstance(data, list):
                            for entry in data:
                                if str(entry.get('channelId')) == ch_id:
                                    programs = entry.get('programs', [])
                                    for prog in programs:
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
                    print(f"Error: {e}")

        # DEBUG: If list is still empty, add a fake program to see if main.py is working
        if not all_programs:
            for ch_id in channels:
                all_programs.append({
                    'channel_id': ch_id,
                    'title': "EPG Updating",
                    'desc': "Schedule currently unavailable",
                    'start': now,
                    'end': now + timedelta(hours=24)
                })
                    
        return all_programs
