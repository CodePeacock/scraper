import asyncio
import datetime
import tracemalloc
from functools import lru_cache

import aiohttp
import pandas as pd
from bs4 import BeautifulSoup

# tracemalloc.start()


class PropertyMarketIdentifier:
    def __init__(self, websites):
        self.websites = websites

    async def scrape_properties_magicbricks(self):
        url = "https://www.magicbricks.com/ready-to-move-flats-in-mumbai-pppfs"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
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
    async def scrape_properties_makaan(self):
        url = "https://www.makaan.com/mumbai-residential-property/buy-property-in-mumbai-city"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                html = await response.text()

        soup = BeautifulSoup(html, "lxml")
        listings = soup.find_all("div", class_="search-result-wrap")
        property_data_list = []

        for listing in listings:
            owner_elements = listing.find_all("div", class_="seller-info")
            owners = [owner.text for owner in owner_elements]
            # print(owners)

            price_elements = listing.find_all("td", class_="price")
            price_elements = [
                price.find("span", class_="val") for price in price_elements
            ]
            price_denominations = [
                price.find("span", class_="unit").text
                for price in listing.find_all("td", class_="price")
            ]
            # print(price_denominations)
            # Get text from within span tags
            prices = [price_.text for price_ in price_elements]

            property_name_elements = listing.find_all("div", class_="seller-info")
            # Get text from within span tags
            property_name_elements = [
                prop_name.find("a", class_="seller-name").text
                for prop_name in property_name_elements
            ]
            # Add price denomination to price
            prices = [
                price + "" + price_denomination
                for price, price_denomination in zip(prices, price_denominations)
            ]
            property_data_list.extend(
                [
                    {"owner": owner, "price": "₹" + price, "property_name": prop_name}
                    for owner, price, prop_name in zip(
                        owners, prices, property_name_elements
                    )
                ]
            )

        return property_data_list

    async def scrape_properties_parallel(self):
        tasks = []
        if "magicbricks" in self.websites:
            tasks.append(asyncio.create_task(self.scrape_properties_magicbricks()))
        if "makaan.com" in self.websites:
            tasks.append(asyncio.create_task(self.scrape_properties_makaan()))

        property_data = await asyncio.gather(*tasks) if tasks else []
        # Flatten the list of lists
        all_property_data = [item for sublist in property_data for item in sublist]

        filename = f"{self.websites[0]}-{datetime.datetime.now():%d-%b-%Y}.csv"
        self.save_to_csv(all_property_data, filename)
        print(f"Data saved to {filename}")

    def save_to_csv(self, data, filename):
        df = pd.DataFrame(data)
        df.to_csv(filename, index=False, encoding="utf-8")


if __name__ == "__main__":
    websites = ["magicbricks", "makaan.com"]

    # Read user choice as a command-line argument
    import sys

    if len(sys.argv) > 1:
        user_choice = sys.argv[1].strip().lower()
    else:
        user_choice = (
            input("Choose 'magicbricks', 'makaan', or 'both': ").strip().lower()
        )

    if user_choice not in ["magicbricks", "makaan", "both"]:
        print("Invalid choice. Please choose 'magicbricks', 'makaan', or 'both'.")
    else:
        # Enable tracemalloc
        tracemalloc.start()

        if user_choice in ["magicbricks", "both"]:
            websites_to_scrape = ["magicbricks"]

        if user_choice in ["makaan", "both"]:
            websites_to_scrape = ["makaan.com"]

        # Call the asynchronous function within an asyncio event loop
        loop = asyncio.get_event_loop()
        loop.run_until_complete(
            PropertyMarketIdentifier(websites_to_scrape).scrape_properties_parallel()
        )
        loop.close()

        # Optionally, print memory statistics at the end
        current, peak = tracemalloc.get_traced_memory()
        print(f"Current memory usage is {current / 10**6}MB; Peak was {peak / 10**6}MB")
