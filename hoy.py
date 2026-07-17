import requests
import xml.etree.ElementTree as ET
import pytz
from datetime import datetime
from typing import List

class Channel:
    def __init__(self, channel_id, name, extra_data=None):
        self.channel_id = channel_id
        self.name = name
        self.extra_data = extra_data or {}

class Program:
    def __init__(self, channel_id, title, start_time, end_time):
        self.channel_id = channel_id
        self.title = title
        self.start_time = start_time
        self.end_time = end_time

class HOYPlatform:
    def __init__(self):
        self.channel_list_url = "https://api2.hoy.tv/api/v3/a/channel"
        self.session = requests.Session()

    async def fetch_channels(self) -> List[Channel]:
        try:
            response = self.session.get(self.channel_list_url)
            data = response.json()
            channels = []
            if data.get('code') == 200:
                for raw in data.get('data', []):
                    # We force the ID to match your M3U "HOY 77"
                    # Usually HOY 77 is ID "77" in their API
                    api_id = str(raw.get('id'))
                    m3u_id = "HOY 77" if api_id == "77" else f"HOY {api_id}"
                    
                    channels.append(Channel(
                        channel_id=m3u_id, 
                        name=raw.get('name', {}).get('zh_hk', 'HOY TV'),
                        extra_data={'epg_url': raw.get('epg')}
                    ))
            return channels
        except:
            return []

    async def fetch_programs(self, channels: List[Channel]) -> List[Program]:
        all_progs = []
        for ch in channels:
            if not ch.extra_data.get('epg_url'): continue
            res = self.session.get(ch.extra_data['epg_url'])
            root = ET.fromstring(res.text.encode('utf-8'))
            kl_tz = pytz.timezone('Asia/Kuala_Lumpur')
            for item in root.findall('.//EpgItem'):
                start = kl_tz.localize(datetime.strptime(item.findtext('EpgStartDateTime'), "%Y-%m-%d %H:%M:%S"))
                end = kl_tz.localize(datetime.strptime(item.findtext('EpgEndDateTime'), "%Y-%m-%d %H:%M:%S"))
                title = item.find('EpisodeInfo').findtext('EpisodeShortDescription')
                all_progs.append(Program(ch.channel_id, title, start, end))
        return all_progs
