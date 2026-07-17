import requests
import xml.etree.ElementTree as ET
import pytz
from datetime import datetime

class HOYPlatform:
    def __init__(self):
        self.channel_list_url = "https://api2.hoy.tv/api/v3/a/channel"
        self.headers = {"User-Agent": "Mozilla/5.0"}

    async def fetch_channels(self):
        try:
            r = requests.get(self.channel_list_url, headers=self.headers, timeout=10)
            data = r.json()
            channels = []
            for raw in data.get('data', []):
                api_id = str(raw.get('id'))
                # Mapping as requested
                if api_id == "1": 
                    m3u_id, name = "76", "HOY International"
                elif api_id == "2": 
                    m3u_id, name = "77", "HOY TV"
                elif api_id == "3": 
                    m3u_id, name = "78", "HOY Infotainment"
                else: 
                    m3u_id, name = api_id, "HOY"
                
                channels.append({"id": m3u_id, "name": name, "epg": raw.get('epg')})
            return channels
        except:
            return []

    async def fetch_programs(self, channels):
        all_progs = []
        kl_tz = pytz.timezone('Asia/Kuala_Lumpur')
        for ch in channels:
            if not ch['epg']: continue
            try:
                r = requests.get(ch['epg'], headers=self.headers, timeout=10)
                root = ET.fromstring(r.content)
                for item in root.findall('.//EpgItem'):
                    start_str = item.findtext('EpgStartDateTime')
                    end_str = item.findtext('EpgEndDateTime')
                    
                    ep_info = item.find('EpisodeInfo')
                    title = ep_info.findtext('EpisodeShortDescription')
                    # Ensure we get the long description
                    desc = ep_info.findtext('EpisodeLongDescription')
                    
                    start = kl_tz.localize(datetime.strptime(start_str, "%Y-%m-%d %H:%M:%S"))
                    end = kl_tz.localize(datetime.strptime(end_str, "%Y-%m-%d %H:%M:%S"))
                    
                    prog = type('Prog', (), {
                        'channel_id': ch['id'], 
                        'title': title, 
                        'desc': desc if desc else "",
                        'date': start.strftime("%Y-%m-%d"),
                        'start_time': start, 
                        'end_time': end
                    })
                    all_progs.append(prog)
            except: continue
        return all_progs
