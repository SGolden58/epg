import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import datetime

KL_OFFSET = "+0800"

CHANNELS = {
    "HOY TV": "hoytv",
    "HOY INFO": "hoyinfor",
    "HOY NEWS": "hoynews"
}

URL = "https://hoy.tv/program_guide"

async def fetch_schedule():
    print("Loading HOY website…")

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(URL, timeout=90000)

        await page.wait_for_timeout(5000)  # allow JS to load

        html = await page.content()
        await browser.close()
        return html


def parse_schedule(html):
    soup = BeautifulSoup(html, "html.parser")

    xml = []

    for channel_name, channel_id in CHANNELS.items():
        xml.append(f'''
  <channel id="{channel_id}">
    <display-name>{channel_name}</display-name>
  </channel>
''')

    tables = soup.select(".program-guide-table")

    today = datetime.datetime.now()

    for i, table in enumerate(tables):
        day = today + datetime.timedelta(days=i)
        date_str = day.strftime("%Y%m%d")

        rows = table.select("tr")

        for row in rows:
            time_cell = row.select_one(".time")
            title_cell = row.select_one(".title")

            if not time_cell or not title_cell:
                continue

            start_time = time_cell.text.strip()
            title = title_cell.text.strip()

            try:
                hour, minute = start_time.split(":")
            except:
                continue

            start_dt = day.replace(hour=int(hour), minute=int(minute), second=0)
            stop_dt = start_dt + datetime.timedelta(minutes=30)

            start_str = start_dt.strftime("%Y%m%d%H%M%S") + " " + KL_OFFSET
            stop_str = stop_dt.strftime("%Y%m%d%H%M%S") + " " + KL_OFFSET

            channel_list = list(CHANNELS.values())
            channel_id = channel_list[i % len(channel_list)]

            xml.append(f'''
  <programme start="{start_str}" stop="{stop_str}" channel="{channel_id}">
    <title>{title}</title>
  </programme>
''')

    return xml


async def main():
    html = await fetch_schedule()
    xml_data = parse_schedule(html)

    final = ['<?xml version="1.0" encoding="UTF-8"?>', '<tv>']
    final.extend(xml_data)
    final.append('</tv>')

    with open("hoy.xml", "w", encoding="utf-8") as f:
        f.write("\n".join(final))

    print("EPG generated → hoy.xml")


if __name__ == "__main__":
    asyncio.run(main())
