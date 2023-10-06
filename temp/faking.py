import concurrent.futures  # Import for multithreading
import csv

import faker
from tqdm import tqdm


# Create a function to generate fake data for a single listing
def generate_listing(fake):
    posted_on = fake.past_date()
    owner_name = fake.name()
    location = fake.city()
    bhk = fake.random.randint(1, 4)
    balcony = fake.random.randint(0, 2)
    sq_ft = fake.random.randint(500, 2000)
    price = fake.random.randint(1000000, 10000000)
    return [posted_on, owner_name, location, bhk, balcony, sq_ft, price]


# Create a Faker instance
fake = faker.Faker(locale="en_IN")

# Create a list to store the data
# data = []

# Set the total number of listings to generate
total_listings = 30000

# Use tqdm to monitor progress
with concurrent.futures.ThreadPoolExecutor() as executor:
    results = list(
        tqdm(
            executor.map(generate_listing, [fake] * total_listings),
            total=total_listings,
            desc="Generating Data",
        )
    )

# Write the data to a CSV file
with open("real_estate_dataset.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(
        ["Posted on", "Owner Name", "Location", "BHK", "Balcony", "Sq. ft", "Price"]
    )
    writer.writerows(results)
