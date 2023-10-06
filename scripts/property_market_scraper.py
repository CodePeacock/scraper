import asyncio
import logging
from pathlib import Path
from typing import List

import aiofiles
import aiohttp
import pandas as pd
from aiocache import Cache
from aiocache.serializers import JsonSerializer
from bs4 import BeautifulSoup


class PropertyMarketIdentifier:
    def __init__(self, websites: List[str], city: str, output_dir: str = "data"):
        self.websites = websites
        self.city = city
        self.output_dir = output_dir
        self.base_url = {
            "magicbricks": f"https://www.magicbricks.com/ready-to-move-flats-in-{city}-pppfs",
            "makaan": f"https://www.makaan.com/{city}-residential-property/buy-property-in-{city}-city",
        }

        Path(self.output_dir).mkdir(parents=True, exist_ok=True)

        # Initialize cache
        self.cache = Cache(
            Cache.MEMORY, serializer=JsonSerializer(), namespace="web_scraping"
        )

    async def fetch_url(self, url: str) -> str:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as response:
                response.raise_for_status()
                return await response.text()

    async def scrape_properties(self, website: str) -> List[dict]:
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
            property_data_list = []

            if website == "magicbricks":  # Check if website is valid
                listings = soup.find_all("div", class_="mb-srp__left")
                for listing in listings:
                    owner_names = listing.find_all("div", class_="mb-srp__card__ads")
                    owners = [
                        owner.find("div", class_="mb-srp__card__ads--name").text.lstrip(
                            "Owner: "
                        )
                        for owner in owner_names
                    ]

                    price_list = listing.find_all(
                        "div", class_="mb-srp__card__price--amount"
                    )
                    prices = [price.text for price in price_list]

                    property_names = [
                        property_name.text
                        for property_name in listing.find_all(
                            "h2", class_="mb-srp__card--title"
                        )
                    ]

                    property_data_list.extend(
                        [
                            {
                                "owner": owner,
                                "price": price,
                                "property_name": prop_name,
                            }
                            for owner, price, prop_name in zip(
                                owners, prices, property_names
                            )
                        ]
                    )
            elif website == "makaan":  # Check if website is valid
                listings = soup.find_all("div", class_="search-result-wrap")
                for listing in listings:
                    owner_elements = listing.find_all("div", class_="seller-info")
                    owners = [owner.text for owner in owner_elements]

                    price_elements = listing.find_all("td", class_="price")
                    price_elements = [
                        price.find("span", class_="val") for price in price_elements
                    ]
                    price_denominations = [
                        price.find("span", class_="unit").text
                        for price in listing.find_all("td", class_="price")
                    ]

                    prices = [price_.text for price_ in price_elements]

                    property_name_elements = listing.find_all(
                        "div", class_="seller-info"
                    )
                    property_name_elements = [
                        prop_name.find("a", class_="seller-name").text
                        for prop_name in property_name_elements
                    ]

                    prices = [
                        price + " " + price_denomination
                        for price, price_denomination in zip(
                            prices, price_denominations
                        )
                    ]

                    property_data_list.extend(
                        [
                            {
                                "owner": owner.replace("BUILDER0", ""),
                                "price": "₹" + price,
                                "property_name": prop_name,
                            }
                            for owner, price, prop_name in zip(
                                owners, prices, property_name_elements
                            )
                        ]
                    )

            await self.cache.set(
                cache_key, property_data_list, ttl=3600
            )  # Cache for 1 hour
            return property_data_list
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            logging.error(f"Error scraping {website.capitalize()}: {str(e)}")
            return []

    async def save_to_csv(self, data: List[dict], filename: str):
        try:
            df = pd.DataFrame(data)
            async with aiofiles.open(filename, mode="w", encoding="utf-8") as f:
                await f.write(df.to_csv(index=False))
            logging.info(f"Data saved to {filename}")
        except Exception as e:
            logging.error(f"Error saving data to CSV: {str(e)}")
