"""
Copyright (c) 2023 Mayur Sinalkar

This software is released under the MIT License.
https://opensource.org/licenses/MIT

"""
import asyncio
import datetime
import logging
import os
import traceback
import tracemalloc
from pathlib import Path
from typing import List, Tuple

import aiofiles
import aiohttp
import pandas as pd
from aiocache import Cache
from aiocache.serializers import JsonSerializer
from bs4 import BeautifulSoup


class PropertyMarketIdentifier:
    """
    Class to scrape property market data from various websites.

    Args:
        websites (List[str]): List of websites to scrape data from.
        city (str): The city for which data is to be scraped.
        output_dir (str, optional): Directory to save scraped data. Defaults to "data".
    """

    def __init__(self, websites: List[str], city: str, output_dir: str = "data"):
        """
        Initialize the PropertyMarketIdentifier instance.

        Args:
            websites (List[str]): List of websites to scrape data from.
            city (str): The city for which data is to be scraped.
            output_dir (str, optional): Directory to save scraped data. Defaults to "data".
        """
        self.websites = websites
        self.city = city
        self.output_dir = output_dir
        self.base_url = {
            "magicbricks": f"https://www.magicbricks.com/ready-to-move-flats-in-{city}-pppfs",
            "makaan": f"https://www.makaan.com/{city}-residential-property/buy-property-in-{city}-city",
            "commonfloor": f"https://www.commonfloor.com/{city}-property/projects",
        }
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)
        # Initialize cache
        self.cache = Cache(
            Cache.MEMORY, serializer=JsonSerializer(), namespace="web_scraping"
        )

    async def fetch_url(self, url: str) -> str:
        """
        Fetch the HTML content of a given URL asynchronously.

        Args:
            url (str): The URL to fetch.

        Returns:
            str: The HTML content of the URL.
        """
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as response:
                response.raise_for_status()
                return await response.text()

    async def scrape_properties(self, website: str) -> List[dict]:
        """
        Scrape property data from a specific website asynchronously.

        Args:
            website (str): The website to scrape data from.

        Returns:
            List[dict]: List of scraped property data as dictionaries.
        """
        # Define a cache key
        cache_key = f"{website}_{self.city}"

        # Check if data is already in cache
        cached_data = await self.cache.get(cache_key)
        if cached_data:
            return cached_data

        try:
            url = self.base_url[website]
            html = await self.fetch_url(url)

            soup = BeautifulSoup(html, "lxml")
            if website == "commonfloor":
                # CommonFloor scraping logic
                listings = soup.find_all("div", class_="snb-content-list")
                property_data_list = []

                for listing in listings:
                    owner = listing.find("h3", class_="proSnbp").text.strip()
                    price = listing.find("tbody")
                    price = price.find_all("td")
                    icon_inr = price[0].find("i", class_="icon-inr")
                    property_info = listing.find("div", class_="snb-projecttile-top")
                    property_anchor = property_info.find("a")
                    property_name = property_anchor.find("h2").text.strip()
                    property_data_list.append(
                        {"owner": owner, "price": price, "property_name": property_name}
                    )
                return property_data_list

                # Remaining scraping logic for other websites...

        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            logging.error(f"Error scraping {website.capitalize()}: {str(e)}")
            return []

    async def scrape_properties_parallel(self):
        """
        Scrape property data from multiple websites in parallel.
        """
        # ... (rest of the code)

    async def save_to_csv(self, data: List[dict], filename: str):
        """
        Save property data to a CSV file asynchronously.

        Args:
            data (List[dict]): List of property data as dictionaries.
            filename (str): The name of the CSV file to save.
        """
        try:
            df = pd.DataFrame(data)
            async with aiofiles.open(filename, mode="w", encoding="utf-8") as f:
                await f.write(df.to_csv(index=False))
            logging.info(f"Data saved to {filename}")
        except Exception as e:
            logging.error(f"Error saving data to CSV: {str(e)}")


def get_user_input() -> Tuple[str, List[str]]:
    """
    Get user input for city and websites to scrape.

    Returns:
        Tuple[str, List[str]]: Tuple containing the city and list of websites to scrape.
    """
    # ... (rest of the code)


if __name__ == "__main__":
    tracemalloc.start()
    logging.basicConfig(
        filename="scraper.log",
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )

    city, websites = get_user_input()

    if not city:
        logging.error("City name is required.")
        print("City name is required.")
    elif not websites:
        logging.error("At least one website must be selected.")
        print("At least one website must be selected.")
    elif any(
        website not in ["magicbricks", "makaan", "commonfloor", "all"]
        for website in websites
    ):
        logging.error(
            "Invalid choice for website(s). Please choose 'magicbricks', 'makaan', 'commonfloor', or 'all'."
        )
        print(
            "Invalid choice for website(s). Please choose 'magicbricks', 'makaan', 'commonfloor', or 'all'."
        )
    else:
        loop = asyncio.get_event_loop()
        try:
            loop.run_until_complete(
                PropertyMarketIdentifier(websites, city).scrape_properties_parallel()
            )
        except Exception as e:
            logging.error(f"Error running the scraper: {str(e)}")
            print(f"Error running the scraper: {str(e)}")
        finally:
            loop.close()

        current, peak = tracemalloc.get_traced_memory()
        logging.info(
            f"Current memory usage is {current / 10**6}MB; Peak was {peak / 10**6}MB"
        )
        print(f"Current memory usage is {current / 10**6}MB; Peak was {peak / 10**6}MB")
