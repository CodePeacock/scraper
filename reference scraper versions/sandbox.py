from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache

import pandas as pd
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm


class PropertyMarketIdentifier:
    def __init__(self, websites):
        """
        Initialize the PropertyMarketIdentifier class with a list of websites to scrape.
        """
        self.websites = websites

    @lru_cache(maxsize=None, typed=False)
    def scrape_properties(self, website):
        """
        Scrape property data from the specified website and return it as a list of dictionaries.
        """
        url = f"https://www.{website}/ready-to-move-flats-in-mumbai-pppfs"
        response = requests.get(url)
        soup = BeautifulSoup(response.content, "html.parser")
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

            price_list = listing.find_all("div", class_="mb-srp__card__price--amount")
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
                    for owner, price, prop_name in zip(owners, prices, property_names)
                ]
            )

        return property_data_list

    @lru_cache(maxsize=None, typed=False)
    def scrape_properties_parallel(self):
        """
        Scrape property data from all specified websites in parallel and save it to a CSV file.
        """
        all_property_data = []  # Create a list to store all property data

        with ThreadPoolExecutor(max_workers=16) as executor:
            results = list(
                tqdm(
                    executor.map(self.scrape_properties, self.websites),
                    total=len(self.websites),
                )
            )

        for website_data in results:
            all_property_data.extend(website_data)

        # Convert the data to a DataFrame for efficient processing
        df = pd.DataFrame(all_property_data)

        # Save all the scraped data to a CSV file
        df.to_csv("property_data1.csv", index=False, encoding="utf-8")


if __name__ == "__main__":
    websites = [
        "magicbricks.com",
    ]
    PropertyMarketIdentifier(websites).scrape_properties_parallel()
