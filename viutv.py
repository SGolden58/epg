import requests
import pytz
from datetime import datetime, timedelta

class ViuTVPlatform:
    def __init__(self):
        self.api_url = "https://api.viu.now.com/p8/2/getProgramList"
        self.headers = {
            "User-Agent": "Mozilla/5.0",
            "Referer": "https://viu.tv/"
        }
        self.timezone = pytz.timezone('Asia/Kuala_Lumpur')
        self.target_channels = [
            {"api_id": "099", "m3u_id": "099"},
            {"api_id": "096", "m3u_id": "096"}
        ]

    async def fetch_all_programs(self, days=2):
        all_programs = []
        for ch in self.target_channels:
            for i in range(days):
                date_str = (datetime.now(self.timezone) + timedelta(days=i)).strftime("%Y%m%d")
                payload = {"channelNo": ch["api_id"], "day": date_str, "callerReferenceNo": "1"}
                try:
                    r = requests.post(self.api_url, json=payload, headers=self.headers, timeout=10)
                    res = r.json()
                    if res.get('responseCode') == "000":
                        for item in res['data']['programList']:
                            start = datetime.fromtimestamp(int(item['start'])/1000, self.timezone)
                            end = datetime.fromtimestamp(int(item['end'])/1000, self.timezone)
                            all_programs.append({
                                "channel_id": ch["m3u_id"],
                                "title": item['title'],
                                "desc": item.get('synopsis', ''),
                                "start": start,
                                "end": end
                            })
                except: continue
        return all_programs
