import asyncio
from typing import List

import aiohttp
from bs4 import BeautifulSoup

base_url = "https://www.commonfloor.com/mumbai-property/projects"


async def fetch_url(url: str) -> str:
    async with aiohttp.ClientSession() as session:
        async with session.get(url, timeout=10) as response:
            response.raise_for_status()
            return await response.text()


async def scrape_properties(website: str) -> List[dict]:
    html = await fetch_url(base_url)
    website = "commonfloor"
    if website == "commonfloor":
        soup = BeautifulSoup(html, "lxml")
        # CommonFloor scraping logic
        listings = soup.find_all("div", class_="snb-content-list")
        print(listings)
        property_data_list = []
        for listing in listings:
            print(listing)
            owner = listing.find("div", class_="owner-info").text.strip()
            price = listing.find("span", class_="price").text.strip()
            property_name = listing.find("h2", class_="ng-binding").text.strip()

            property_data_list.append(
                {"owner": owner, "price": price, "property_name": property_name}
            )
        return property_data_list


async def main():
    property_data = await scrape_properties(website="commonfloor")
    print(property_data)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
