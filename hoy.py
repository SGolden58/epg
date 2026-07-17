import requests
import xml.etree.ElementTree as ET
import pytz
from datetime import datetime

class HOYPlatform:
    def __init__(self):
        self.channel_list_url = "https://api2.hoy.tv/api/v3/a/channel"
        self.headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

    async def fetch_channels(self):
        try:
            r = requests.get(self.channel_list_url, headers=self.headers, timeout=10)
            data = r.json()
            channels = []
            for raw in data.get('data', []):
                api_id = str(raw.get('id'))
                # Force ID to 77 for your M3U
                m3u_id = "77" if api_id == "1" else api_id
                channels.append({"id": m3u_id, "epg": raw.get('epg'), "name": "HOY"})
            return channels
        except Exception as e:
            print(f"HOY API Error: {e}")
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
                    title = item.find('EpisodeInfo').findtext('EpisodeShortDescription')
                    
                    start = kl_tz.localize(datetime.strptime(start_str, "%Y-%m-%d %H:%M:%S"))
                    end = kl_tz.localize(datetime.strptime(end_str, "%Y-%m-%d %H:%M:%S"))
                    
                    # Create a simple object that main.py expects
                    prog = type('Prog', (), {'channel_id': ch['id'], 'title': title, 'start_time': start, 'end_time': end})
                    all_progs.append(prog)
            except: continue
        return all_progs
