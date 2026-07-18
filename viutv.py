import requests
import pytz
from datetime import datetime, timedelta

class ViuTVPlatform:
    def __init__(self):
        # Using the Now TV Schedule API which is related to the search API you found
        self.url = "https://now-tv.now.com/nowtv-api/get-schedule"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        }

    async def fetch_all_programs(self, days=2):
        all_progs = []
        kl_tz = pytz.timezone('Asia/Kuala_Lumpur')
        
        # Now TV uses internal IDs: 099 is '099', 096 is '096'
        for channel_id in ["099", "096"]:
            for offset in range(days):
                # Calculate date in YYYYMMDD format
                target_date = (datetime.now(kl_tz) + timedelta(days=offset)).strftime("%Y%m%d")
                
                params = {
                    "channelId": channel_id,
                    "day": target_date,
                    "nowtvapi_key": "nowtv.now.com",
                    "nowtvapi_v": "1.00"
                }
                
                try:
                    # This API uses GET
                    r = requests.get(self.url, params=params, headers=self.headers, timeout=15)
                    if r.status_code == 200:
                        data = r.json()
                        # The data is inside data['com.pccw.nowtv.model.ScheduleModel']
                        schedule = data.get('com.pccw.nowtv.model.ScheduleModel', [])
                        
                        for item in schedule:
                            # Now TV provides timestamps in milliseconds
                            start_ts = int(item["startTime"]) / 1000
                            end_ts = int(item["endTime"]) / 1000
                            
                            start = datetime.fromtimestamp(start_ts, tz=pytz.utc).astimezone(kl_tz)
                            end = datetime.fromtimestamp(end_ts, tz=pytz.utc).astimezone(kl_tz)
                            
                            prog = type('Prog', (), {
                                'channel_id': channel_id, 
                                'title': item.get("programName", "No Title"), 
                                'desc': item.get("synopsis", ""),
                                'date': start.strftime("%Y-%m-%d"),
                                'start_time': start, 
                                'end_time': end
                            })
                            all_progs.append(prog)
                except Exception as e:
                    print(f"NowTV API Error for {channel_id}: {e}")
                    continue
                    
        return all_progs
