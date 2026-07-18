import requests
import pytz
from datetime import datetime, timedelta


class ViuTVPlatform:
    def __init__(self):
        # The source you provided
        self.url = "https://www.open-epg.com/files/hongkong4.xml"

    async def fetch_all_programs(self, days=2):
        all_programs = []
        # EXACT IDs from hongkong4.xml:
        # <channel id="ViuTV.hk">
        # <channel id="ViuTVsix.hk">
        target_map = {
            "ViuTV.hk": "099",
            "ViuTVsix.hk": "096"
        }

    async def fetch_channels(self):
        return [{"id": ch["m3u_id"], "api_id": ch["api_id"], "name": ch["name"]} for ch in self.target_channels]

    async def fetch_programs(self, channels):
        all_progs = []
        kl_tz = pytz.timezone('Asia/Kuala_Lumpur')
        
        async with httpx.AsyncClient(headers=self.headers, timeout=10) as client:
            tasks = []
            for ch in channels:
                for day_offset in ["0", "1", "2"]:
                    payload = {
                        "channelNo": ch["api_id"],
                        "dayOffset": day_offset,
                        "deviceId": "anonymous",
                        "callerReferenceNo": "web"
                    }
                    tasks.append(self._fetch_day(client, payload, ch, kl_tz))
            
            results = await asyncio.gather(*tasks)
            for res in results:
                all_progs.extend(res)
                
        return all_progs

    async def _fetch_day(self, client, payload, ch, tz):
        day_progs = []
        try:
            r = await client.post(self.schedule_url, json=payload)
            data = r.json()
            listings = data.get("data", {}).get("scheduleList", [])
            
            for item in listings:
                start_ms = int(item.get("startMilliSec", 0))
                duration_ms = int(item.get("duration", 0))
                
                start = datetime.fromtimestamp(start_ms / 1000.0, tz=tz)
                end = datetime.fromtimestamp((start_ms + duration_ms) / 1000.0, tz=tz)
                
                # Using a dictionary or a NamedTuple is often cleaner than type('Prog', ...)
                prog = {
                    'channel_id': ch['id'],
                    'title': item.get("progTitle", "No Title"),
                    'desc': item.get("progDesc", ""),
                    'date': start.strftime("%Y-%m-%d"),
                    'start_time': start,
                    'end_time': end
                }
                day_progs.append(prog)
        except Exception as e:
            print(f"Error fetching {ch['name']}: {e}")
        return day_progs

# Usage example:
# platform = ViuTVPlatform()
# channels = await platform.fetch_channels()
# programs = await platform.fetch_programs(channels)
