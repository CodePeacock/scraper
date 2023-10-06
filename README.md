# Property Market Identifier and Car Price Prediction App

This repository contains two Python scripts, the **Property Market Identifier** and the **Car Price Prediction App**, each designed for specific tasks. Below are instructions for using both scripts.

## Property Market Identifier

The **Property Market Identifier** script allows you to scrape property listings from various real estate websites for a specified city. It provides a simple command-line interface for selecting the city and websites to scrape. The scraped data is then saved to a CSV file.

### Prerequisites

Before using this script, ensure that you have the following dependencies installed:

- Python 3.x
- `asyncio` (Python asynchronous I/O)
- `aiohttp` (Asynchronous HTTP Client/Server Framework)
- `aiofiles` (Asynchronous file operations)
- `pandas` (Data manipulation and analysis library)
- `aiocache` (Caching library)
- `beautifulsoup4` (HTML parsing library)
- `tracemalloc` (Memory tracking library)
- `pathlib` (Filesystem path operations)
- `logging` (Logging library)

You can install these dependencies using pip:

```bash
pip install aiohttp aiofiles pandas aiocache beautifulsoup4 tracemalloc
```

### Usage

1. Clone or download this repository to your local machine.

2. Open a terminal and navigate to the directory containing the script (`property_market_identifier.py`).

3. Run the script using Python:

```bash
python property_market_identifier.py
```

4. The script will prompt you for the following information:
   - Enter the city you want to scrape data for.
   - Enter the website(s) you want to scrape. You can enter one or more of the following options:
     - `magicbricks`
     - `makaan`
     - `commonfloor`
     - `all` (to scrape from all available websites)

5. The script will start scraping property listings from the selected websites for the specified city.

6. Once the scraping is complete, the data will be saved to a CSV file in the "data" directory with a filename that includes the city name and the date of the scrape.

### Error Handling

The script includes error handling to handle various scenarios, such as invalid inputs and network errors. If an error occurs during scraping or data saving, it will be logged in the "scraper.log" file in the same directory.

### Memory Usage

The script also tracks memory usage using `tracemalloc` and logs the memory usage statistics in the "scraper.log" file.

## Car Price Prediction App

The **Car Price Prediction App** is a Streamlit web application that uses a trained Random Forest Regressor model to predict the price of a car based on certain features. Users can select car model, year, fuel type, and engine size, and the app will calculate and display the predicted car price in Indian rupees (₹).

### Prerequisites

Before running the app, make sure you have the following dependencies installed:

- Python 3.x
- `pandas` (Data manipulation and analysis library)
- `streamlit` (Web application framework)
- `scikit-learn` (Machine learning library)

You can install these dependencies using pip:

```bash
pip install pandas streamlit scikit-learn
```

### Usage

1. Clone or download this repository to your local machine.

2. Place the car dataset file (`car_dataset_.csv`) in the same directory as the script.

3. Open a terminal and navigate to the directory containing the script (`car_price_prediction_app.py`).

4. Run the Streamlit app using Python:

```bash
streamlit run car_price_prediction_app.py
```

5. The app will open in your default web browser.

6. Use the sidebar to select car features:
   - **Car Model**: Choose from the available car models.
   - **Year**: Slide to select the year of the car (between 2011 and 2023).
   - **Fuel Type**: Choose from the available fuel types.
   - **Engine Capacity**: Input the engine size (between 1 and 6).

7. Click the "Calculate Price" button to predict the car price.

8. The app will display the predicted car price in Indian rupees (₹) based on the selected features.

### Error Handling

The app includes error handling to ensure a smooth user experience. If any issues occur during the prediction process, appropriate error messages will be displayed.

## Disclaimer

- The **Property Market Identifier** script is intended for educational and personal use. Please use it responsibly and in accordance with the terms and conditions of the websites you scrape.

- The **Car Price Prediction App** is for demonstration and educational purposes only. The accuracy of the car price predictions depends on the quality and representativeness of the dataset and the machine learning model used. Actual car prices may vary, and this app should not be used for real financial decisions.

**Enjoy using both the Property Market Identifier and Car Price Prediction App!**