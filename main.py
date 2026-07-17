# 1. Get HOY programs
hoy_programs = await hoy_platform.fetch_programs(hoy_channels)

# 2. Get ViuTV programs
viutv_platform = ViuTVPlatform(logger)
viu_programs = await viutv_platform.fetch_all_programs(days=2)

# 3. Combine and Save
all_data = hoy_programs + viu_programs
save_to_xmltv(all_data, "epg.xml")
