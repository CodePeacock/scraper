import asyncio
import datetime
import logging
import os
import tracemalloc
from pathlib import Path
from typing import List, Tuple

import aiohttp
import pandas as pd
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

    async def scrape_properties(self, website: str) -> List[dict]:
        try:
            url = self.base_url[website]
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as response:
                    response.raise_for_status()
                    html = await response.text()

            soup = BeautifulSoup(html, "lxml")
            property_data_list = []

            if website == "magicbricks":
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
                            {"owner": owner, "price": price, "property_name": prop_name}
                            for owner, price, prop_name in zip(
                                owners, prices, property_names
                            )
                        ]
                    )
            elif website == "makaan":
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

            return property_data_list
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            logging.error(f"Error scraping {website.capitalize()}: {str(e)}")
            return []

    async def scrape_properties_parallel(self):
        tasks = [self.scrape_properties(website) for website in self.websites]
        property_data = await asyncio.gather(*tasks)
        all_property_data = [item for sublist in property_data for item in sublist]

        filename = f"{self.city}-{'-'.join(self.websites)}-{datetime.datetime.now():%d-%b-%Y}.csv"
        file_path = os.path.join(self.output_dir, filename)
        self.save_to_csv(all_property_data, file_path)
        logging.info(f"Data saved to {file_path}")

    def save_to_csv(self, data: List[dict], filename: str):
        try:
            df = pd.DataFrame(data)
            df.to_csv(filename, index=False, encoding="utf-8")
            logging.info(f"Data saved to {filename}")
        except Exception as e:
            logging.error(f"Error saving data to CSV: {str(e)}")


def get_user_input() -> Tuple[str, List[str]]:
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
