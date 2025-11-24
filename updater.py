
import asyncio
from datetime import datetime
import aiohttp
import logging


async def get_completion() -> tuple[str | None, float | None]:
    url = "https://are-we-there-yet.hackclub.com/api/status"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            response.raise_for_status()
            data = await response.json()
            
    try:
        percentage = data["migration_data"]["percent_completed"]
        last_updated_str = data["last_updated"]
        
        # ISO format: 2025-11-24T20:11:39.518+00:00
        dt = datetime.fromisoformat(last_updated_str)
        unix_timestamp = dt.timestamp()
        
        return str(percentage), unix_timestamp
    except (KeyError, ValueError) as e:
        logging.error(f"Error parsing API response: {e}")
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
