    async def fetch_channels(self) -> List[Channel]:
        """Fetch channel list from HOY TV API"""
        self.logger.info("📡 Fetching channel list from HOY TV")

        # Note: You might need to add headers like User-Agent
        response = self.http_client.get(self.channel_list_url)
        data = response.json()

        channels = []

        if data.get('code') == 200:
            for raw_channel in data.get('data', []):
                name_info = raw_channel.get('name', {})
                # Priority: Traditional Chinese -> English
                channel_name = name_info.get('zh_hk', name_info.get('en', 'Unknown'))
                
                epg_url = raw_channel.get('epg')
                logo = raw_channel.get('image')

                if channel_name and epg_url:
                    channels.append(Channel(
                        channel_id=str(raw_channel.get('id', '')),
                        name=channel_name,
                        # Store epg_url in extra_data so _fetch_channel_programs can find it
                        extra_data={'epg_url': epg_url, 'logo': logo},
                        logo=logo
                    ))

        self.logger.info(f"📺 Found {len(channels)} channels from HOY TV")
        return channels

    def _parse_epg_xml(self, xml_content: str, channel: Channel) -> List[Program]:
        """Parse EPG XML content for HOY TV"""
        try:
            # HOY TV XML often starts with <Channel> or <EpgList>
            root = ET.fromstring(xml_content)
        except ET.ParseError as e:
            self.logger.error(f"❌ XML Parse Error for {channel.name}: {e}")
            return []

        programs = []
        kl_tz = pytz.timezone('Asia/Kuala_Lumpur')
        
        # HOY TV XML structure usually has EpgItem directly under the root or under a Channel tag
        # We use './/EpgItem' to find them anywhere in the tree
        for epg_item in root.findall('.//EpgItem'):
            try:
                start_time_str = epg_item.findtext('EpgStartDateTime')
                end_time_str = epg_item.findtext('EpgEndDateTime')

                if not start_time_str or not end_time_str:
                    continue

                # Convert string to datetime objects
                start_time = kl_tz.localize(datetime.strptime(start_time_str, "%Y-%m-%d %H:%M:%S"))
                end_time = kl_tz.localize(datetime.strptime(end_time_str, "%Y-%m-%d %H:%M:%S"))

                # Get Title logic
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
                    end_time=end_time,
                    description="",
                    raw_data={'start': start_time_str, 'end': end_time_str}
                ))
            except Exception as e:
                continue

        return programs
