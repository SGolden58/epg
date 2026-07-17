import pytz
import requests
from datetime import datetime, timedelta
from typing import List
# Assuming these are your base classes
# from .base import BaseEPGPlatform, Channel, Program

class ViuTVPlatform:
    """ViuTV EPG platform implementation for Channel 99 and 96"""

    def __init__(self, logger):
        self.logger = logger
        self.api_url = "https://api.viu.now.com/p8/2/getProgramList"
        self.timezone = pytz.timezone('Asia/Kuala_Lumpur')
        # Define the channels we want to fetch
        self.target_channels = [
            {"id": "099", "name": "ViuTV"},
            {"id": "096", "name": "ViuTVsix"}
        ]

    async def fetch_channels(self) -> List[dict]:
        """Returns the static channel list for ViuTV"""
        channels = []
        for ch in self.target_channels:
            channels.append({
                "channel_id": ch["id"],
                "name": ch["name"],
                "logo": f"https://vcloud-files.viu.tv/corporate/channel_logo/{ch['id']}.png"
            })
        return channels

    async def fetch_all_programs(self, days=2) -> List[dict]:
        """Fetch programs for all channels for the next X days"""
        all_programs = []
        
        for ch_info in self.target_channels:
            self.logger.info(f"📡 Fetching ViuTV: {ch_info['name']} ({ch_info['id']})")
            
            for i in range(days):
                # Calculate date in YYYYMMDD format
                target_date = (datetime.now(self.timezone) + timedelta(days=i)).strftime("%Y%m%d")
                
                programs = await self._fetch_channel_day(ch_info["id"], target_date)
                all_programs.extend(programs)
                
        return all_programs

    async def _fetch_channel_day(self, channel_no: str, date_str: str) -> List[dict]:
        """Fetch specific channel data for a specific date"""
        payload = {
            "channelNo": channel_no,
            "day": date_str,
            "callerReferenceNo": "1"
        }
        
        headers = {
            "Content-Type": "application/json",
            "Referer": "https://viu.tv/",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

        try:
            # Using standard requests (or your self.http_client)
            response = requests.post(self.api_url, json=payload, headers=headers)
            data = response.json()

            day_programs = []
            if data.get('responseCode') == "000":
                program_list = data.get('data', {}).get('programList', [])
                
                for item in program_list:
                    # ViuTV timestamps are in milliseconds
                    start_ts = int(item.get('start')) / 1000
                    end_ts = int(item.get('end')) / 1000
                    
                    start_dt = datetime.fromtimestamp(start_ts, self.timezone)
                    end_dt = datetime.fromtimestamp(end_ts, self.timezone)

                    day_programs.append({
                        "channel_id": channel_no,
                        "title": item.get('title'),
                        "desc": item.get('synopsis', ''),
                        "start": start_dt,
                        "end": end_dt
                    })
            return day_programs
        except Exception as e:
            self.logger.error(f"❌ Error fetching ViuTV {channel_no} for {date_str}: {e}")
            return []

# Example usage:
# viutv = ViuTVPlatform(your_logger)
# programs = await viutv.fetch_all_programs(days=3)
