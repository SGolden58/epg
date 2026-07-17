import requests
from datetime import datetime, timedelta
import pytz

class ViuTVPlatform:
    def __init__(self):
        self.url = "https://api.nowtv.now.com/pub/v1/epg/guide"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": "https://viutv.hk/",
            "Accept": "application/json"
        }

    async def fetch_all_programs(self, days=2):
        all_programs = []
        channels = ["099", "096"]
        
        tz = pytz.timezone('Asia/Hong_Kong')
        now = datetime.now(tz)
        
        for i in range(days):
            date_str = (now + timedelta(days=i)).strftime("%Y%m%d")
            
            for ch_id in channels:
                params = {"channelId": ch_id, "day": date_str}
                try:
                    print(f"Fetching ViuTV {ch_id} for {date_str}...")
                    response = requests.get(self.url, params=params, headers=self.headers, timeout=15)
                    
                    if response.status_code == 200:
                        json_data = response.json()
                        
                        # The API returns a list in 'data'. We need to find the right channel entry.
                        entries = json_data.get('data', [])
                        if not isinstance(entries, list):
                            # Sometimes it's a single dict instead of a list
                            entries = [entries]

                        for entry in entries:
                            # Check if this entry has the programs
                            progs_list = entry.get('programs', [])
                            
                            if not progs_list:
                                continue

                            print(f"Found {len(progs_list)} programs for {ch_id}")
                            for prog in progs_list:
                                # Extract timestamps safely
                                s_ts = prog.get('start')
                                e_ts = prog.get('end')
                                
                                if s_ts and e_ts:
                                    start_dt = datetime.fromtimestamp(int(s_ts) / 1000, tz)
                                    end_dt = datetime.fromtimestamp(int(e_ts) / 1000, tz)
                                    
                                    all_programs.append({
                                        'channel_id': ch_id,
                                        'title': prog.get('title', 'No Title'),
                                        'desc': prog.get('synopsis', ''),
                                        'start': start_dt,
                                        'end': end_dt
                                    })
                    else:
                        print(f"ViuTV API Error: {response.status_code}")
                except Exception as e:
                    print(f"Error processing ViuTV {ch_id}: {e}")
                    
        return all_programs
