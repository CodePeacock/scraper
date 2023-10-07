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
            property_data_list = []

            if website == "commonfloor":
                # soup = BeautifulSoup(html, "lxml")
                # CommonFloor scraping logic
                listings = soup.find_all("div", class_="snb-content-list")
                # print(listings)
                for listing in listings:
                    # print(listing)
                    owner = listing.find("h3", class_="proSnbp").text.strip()
                    # print(owner)
                    price = listing.find("tbody")
                    price = price.find_all("td")
                    # print(price)
                    icon_inr = price[0].find("i", class_="icon-inr")
                    # print(icon_inr)
                    if icon_inr:
                        print(price)
                    property_info = listing.find("div", class_="snb-projecttile-top")
                    # Get text from h2 tag inside this div
                    property_anchor = property_info.find("a")
                    # print(property_anchor.text.strip())
                    property_name = property_anchor.find("h2").text.strip()
                    # print(property_name)
                    property_data_list.append(
                        {"owner": owner, "price": price, "property_name": property_name}
                    )
                # return property_data_list

            elif website == "magicbricks":
                # Existing MagicBricks scraping logic
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

            elif website == "makaan":
                # Existing Makaan scraping logic
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

    async def scrape_properties_parallel(self):
        """
        Scrape property data from multiple websites in parallel.
        """
        if "all" in self.websites:
            websites_to_scrape = ["magicbricks", "makaan", "commonfloor"]
        else:
            websites_to_scrape = self.websites

        tasks = [self.scrape_properties(website) for website in websites_to_scrape]
        property_data = await asyncio.gather(*tasks)
        all_property_data = [item for sublist in property_data for item in sublist]

        # Create a combined CSV file name
        website_names = "-".join(websites_to_scrape)
        filename = f"{self.city}-{website_names}-{datetime.datetime.now():%d-%b-%Y}.csv"
        file_path = os.path.join(self.output_dir, filename)

        try:
            await self.save_to_csv(all_property_data, file_path)
            logging.info(f"Data saved to {file_path}")
        except Exception as e:
            traceback.print_exc()  # Print the traceback for debugging
            logging.error(f"Error saving data to CSV: {str(e)}")

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
    city = input("Enter the city you want to scrape data for: ").strip().lower()
    websites = (
        input(
            "Enter 'magicbricks', 'makaan', 'commonfloor', or 'all' to choose the website(s) to scrape: "
        )
        .strip()
        .lower()
        .split(",")
    )

    # Allow the user to input "all" as an option
    if "all" in websites:
        websites.remove("all")
        websites.extend(["magicbricks", "makaan", "commonfloor"])

    return city, websites


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
