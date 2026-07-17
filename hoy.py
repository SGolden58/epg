import requests
import xml.etree.ElementTree as ET
import pytz
from datetime import datetime
from typing import List

class Channel:
    def __init__(self, channel_id, name, extra_data=None, logo=None):
        self.channel_id = channel_id
        self.name = name
        self.extra_data = extra_data or {}
        self.logo = logo

class Program:
    def __init__(self, channel_id, title, start_time, end_time, description="", raw_data=None):
        self.channel_id = channel_id
        self.title = title
        self.start_time = start_time
        self.end_time = end_time
        self.description = description
        self.raw_data = raw_data or {}

class HOYPlatform:
    """HOY TV EPG platform implementation"""

    def __init__(self):
        self.channel_list_url = "https://api2.hoy.tv/api/v3/a/channel"
        # Using standard requests for simplicity
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })

    async def fetch_channels(self) -> List[Channel]:
        """Fetch channel list from HOY TV API"""
        print("📡 Fetching channel list from HOY TV")
        
        try:
            response = self.session.get(self.channel_list_url)
            data = response.json()
        except Exception as e:
            print(f"❌ Failed to fetch HOY channels: {e}")
            return []

        channels = []
        if data.get('code') == 200:
            for raw_channel in data.get('data', []):
                name_info = raw_channel.get('name', {})
                channel_name = name_info.get('zh_hk', name_info.get('en', 'Unknown'))
                
                epg_url = raw_channel.get('epg')
                logo = raw_channel.get('image')

                if channel_name and epg_url:
                    channels.append(Channel(
                        channel_id=str(raw_channel.get('id', '')),
                        name=channel_name,
                        extra_data={'epg_url': epg_url},
                        logo=logo
                    ))

        print(f"📺 Found {len(channels)} channels from HOY TV")
        return channels

    async def fetch_programs(self, channels: List[Channel]) -> List[Program]:
        """Fetch program data for all HOY TV channels"""
        all_programs = []
        for channel in channels:
            try:
                epg_url = channel.extra_data.get('epg_url')
                if not epg_url:
                    continue
                
                print(f"🔍 Fetching EPG for: {channel.name}")
                response = self.session.get(epg_url)
                programs = self._parse_epg_xml(response.text, channel)
                all_programs.extend(programs)
            except Exception as e:
                print(f"❌ Error fetching {channel.name}: {e}")
        return all_programs

    def _parse_epg_xml(self, xml_content: str, channel: Channel) -> List[Program]:
        """Parse EPG XML content for HOY TV"""
        try:
            root = ET.fromstring(xml_content.encode('utf-8'))
        except ET.ParseError as e:
            print(f"❌ XML Parse Error for {channel.name}: {e}")
            return []

        programs = []
        kl_tz = pytz.timezone('Asia/Kuala_Lumpur')
        
        for epg_item in root.findall('.//EpgItem'):
            try:
                start_time_str = epg_item.findtext('EpgStartDateTime')
                end_time_str = epg_item.findtext('EpgEndDateTime')

                if not start_time_str or not end_time_str:
                    continue

                start_time = kl_tz.localize(datetime.strptime(start_time_str, "%Y-%m-%d %H:%M:%S"))
                end_time = kl_tz.localize(datetime.strptime(end_time_str, "%Y-%m-%d %H:%M:%S"))

                episode_info = epg_item.find('EpisodeInfo')
                title = ""
                if episode_info is not None:
                    short_desc = episode_info.findtext('EpisodeShortDescription') or ""
                    episode_index = episode_info.findtext('EpisodeIndex') or "0"
                    
                    title = short_desc
                    if episode_index.isdigit() and int(episode_index) > 0:
                        title += f" (Ep.{episode_index})"

                programs.append(Program(
                    channel_id=channel.channel_id,
                    title=title,
                    start_time=start_time,
                    end_time=end_time
                ))
            except:
                continue
        return programs
