
import asyncio
from datetime import datetime
import aiohttp
from bs4 import BeautifulSoup
import logging


async def get_completion() -> tuple[str | None, float | None]:
    url = "https://are-we-there-yet.hackclub.com"
    selector = ".progress-text"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            response.raise_for_status()
            html = await response.text()
            
    soup = BeautifulSoup(html, "html.parser")
    percentage_element = soup.select_one(selector)

    timestamp_element = soup.select_one(".last-updated")
    # e.g. Last updated: 2025-11-24 19:10:26 +0000
    
    
    if percentage_element and timestamp_element:
        time_parsed = timestamp_element.get_text(strip=True)[14:]
        unix_timestamp = datetime.strptime(time_parsed, "%Y-%m-%d %H:%M:%S %z").timestamp()
        return percentage_element.get_text(strip=True)[:-1], unix_timestamp
    if percentage_element or timestamp_element:
        logging.warning("Incomplete data retrieved, something is probably wrong (me when break parsing)")
    logging.error("Could not retrieve completion percentage or timestamp")
    return None, None


async def main():
    last_logged: float | None = None
    while True:
        with open("history.txt", "a+") as f:
            percentage, timestamp = await get_completion()
            if percentage and timestamp and (last_logged is None or timestamp > last_logged):
                if last_logged is None or timestamp > last_logged:
                    last_logged = timestamp
                f.write(f"{timestamp}: {percentage}\n")
            if not percentage or not timestamp:
                logging.error("oh noes")
        await asyncio.sleep(30) # update interval on their side is just over 60s, but to be safe


if __name__ == "__main__":
    asyncio.run(main())
