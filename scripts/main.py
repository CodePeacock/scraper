import asyncio
import logging
import tracemalloc
from typing import List, Tuple

from scripts.property_market_scraper import PropertyMarketIdentifier


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

    # Allow the user to input "both" as an option
    if "both" in websites:
        websites.remove("both")
        websites.extend(["magicbricks", "makaan"])

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
