import asyncio
import datetime
import logging
import os
import tracemalloc
from functools import lru_cache
from pathlib import Path
from typing import List, Tuple

import aiohttp
import pandas as pd
from bs4 import BeautifulSoup


class PropertyMarketIdentifier:
    def __init__(self, websites: List[str], city: str, output_dir: str = "data"):
        """
        Initialize the PropertyMarketIdentifier.

        Args:
            websites (List[str]): List of websites to scrape ("magicbricks," "makaan," or both).
            city (str): The city for which data will be scraped.
            output_dir (str): Directory where the data will be saved. Default is "data".
        """
        self.websites = websites
        self.city = city
        self.output_dir = output_dir

        # Create the output directory if it doesn't exist
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)

    @lru_cache(maxsize=None, typed=False)
    async def scrape_properties_magicbricks(self) -> List[dict]:
        """
        Scrape property data from Magicbricks website.

        Returns:
            List[dict]: List of property data as dictionaries.
        """
        try:
            url = (
                f"https://www.magicbricks.com/ready-to-move-flats-in-{self.city}-pppfs"
            )
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    response.raise_for_status()
                    html = await response.text()

            soup = BeautifulSoup(html, "lxml")
            listings = soup.find_all("div", class_="mb-srp__left")
            property_data_list = []

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
                        {"owner": owner, "price": price, "property_name": prop_name}
                        for owner, price, prop_name in zip(
                            owners, prices, property_names
                        )
                    ]
                )

            return property_data_list
        except aiohttp.ClientError as e:
            logging.error(f"Error scraping Magicbricks: {str(e)}")
            return []

    @lru_cache(maxsize=None, typed=False)
    async def scrape_properties_makaan(self) -> List[dict]:
        """
        Scrape property data from Makaan website.

        Returns:
            List[dict]: List of property data as dictionaries.
        """
        try:
            url = f"https://www.makaan.com/{self.city}-residential-property/buy-property-in-{self.city}-city"
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    response.raise_for_status()
                    html = await response.text()

            soup = BeautifulSoup(html, "lxml")
            listings = soup.find_all("div", class_="search-result-wrap")
            property_data_list = []

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

                property_name_elements = listing.find_all("div", class_="seller-info")
                property_name_elements = [
                    prop_name.find("a", class_="seller-name").text
                    for prop_name in property_name_elements
                ]

                prices = [
                    price + "" + price_denomination
                    for price, price_denomination in zip(prices, price_denominations)
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

            return property_data_list
        except aiohttp.ClientError as e:
            logging.error(f"Error scraping Makaan: {str(e)}")
            return []

    async def scrape_properties_parallel(self):
        tasks = []
        if "magicbricks" in self.websites:
            tasks.append(self.scrape_properties_magicbricks())
        if "makaan" in self.websites:
            tasks.append(self.scrape_properties_makaan())

        property_data = await asyncio.gather(*tasks) if tasks else []
        all_property_data = [item for sublist in property_data for item in sublist]

        filename = f"{self.city}-{'-'.join(self.websites)}-{datetime.datetime.now():%d-%b-%Y}.csv"
        file_path = os.path.join(self.output_dir, filename)
        self.save_to_csv(all_property_data, file_path)
        logging.info(f"Data saved to {file_path}")

    def save_to_csv(self, data: List[dict], filename: str):
        """
        Save property data to a CSV file.

        Args:
            data (List[dict]): List of property data as dictionaries.
            filename (str): The name of the CSV file to save.
        """
        df = pd.DataFrame(data)
        df.to_csv(filename, index=False, encoding="utf-8")


def get_user_input() -> Tuple[str, List[str]]:
    """
    Get user input for city and websites to scrape.

    Returns:
        Tuple[str, List[str]]: City and websites to scrape.
    """
    city = input("Enter the city you want to scrape data for: ").strip().lower()
    websites = (
        input(
            "Enter 'magicbricks', 'makaan', or 'both' to choose the website(s) to scrape: "
        )
        .strip()
        .lower()
        .split(",")
    )
    return city, websites


if __name__ == "__main__":
    tracemalloc.start()
    logging.basicConfig(filename="scraper.log", level=logging.INFO)

    city, websites = get_user_input()

    if not city:
        logging.error("City name is required.")
        print("City name is required.")
    elif not websites:
        logging.error("At least one website must be selected.")
        print("At least one website must be selected.")
    elif any(website not in ["magicbricks", "makaan", "both"] for website in websites):
        logging.error(
            "Invalid choice for website(s). Please choose 'magicbricks', 'makaan', or 'both'."
        )
        print(
            "Invalid choice for website(s). Please choose 'magicbricks', 'makaan', or 'both'."
        )
    else:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(
            PropertyMarketIdentifier(websites, city).scrape_properties_parallel()
        )
        loop.close()

        current, peak = tracemalloc.get_traced_memory()
        logging.info(
            f"Current memory usage is {current / 10**6}MB; Peak was {peak / 10**6}MB"
        )
        print(f"Current memory usage is {current / 10**6}MB; Peak was {peak / 10**6}MB")
