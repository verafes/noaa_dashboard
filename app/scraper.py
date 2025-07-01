import os
import time
import requests
from requests.exceptions import HTTPError

from .logger import logger

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from app.utils import REVERSED_CITY_PREFS, IS_RENDER, RAW_DATA_DIR

from dotenv import load_dotenv


# Configuration
load_dotenv()
DOWNLOAD_DIR = RAW_DATA_DIR
os.makedirs(DOWNLOAD_DIR, exist_ok=True)
url = os.getenv("NOAA_URL")

def init_driver():
    """Handles creation WebDriver """
    global driver
    driver = None
    if driver is not None:
        try:
            driver.quit()
        except:
            pass
    if driver is None:
        chrome_options = Options()
        if IS_RENDER:
            chrome_options.add_argument("--headless=new")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            DOWNLOAD_DIR = os.path.abspath(RAW_DATA_DIR)
        else:
            chrome_options.add_argument("--incognito")
        chrome_options.add_experimental_option("prefs", {
            "download.default_directory": os.path.abspath(RAW_DATA_DIR),
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True
        })
        service = Service(log_path=os.devnull)
        driver = webdriver.Chrome(service=service, options=chrome_options)
        os.makedirs(DOWNLOAD_DIR, exist_ok=True)
        logger.info("Chrome WebDriver initialized.")
    return driver

def cleanup_driver():
    """Clean up the WebDriver"""
    global driver
    if driver is not None:
        driver.quit()
        driver = None
        logger.info("WebDriver closed.")

def go_to_element(element):
    """ Scrolls the page to the selected element, making it visible to the user. """
    driver.execute_script("arguments[0].scrollIntoView();", element)

def element_is_present(locator, timeout=5):
    """
    Expects to verify that the element is present in the DOM tree,
    but not necessarily visible and displayed on the page.
    """
    return WebDriverWait(driver, timeout).until(EC.presence_of_element_located(locator))

def download_csv(url):
    """Gets filename from the URL, downloads csv file and saves to ./data/"""
    filename = os.path.basename(url)

    logger.info(f"Downloading CSV: {filename}")
    file_path = os.path.join("data/raw", filename)
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise error if download fails

        with open(file_path, "wb") as f:
            f.write(response.content)

        with open(os.path.join("data", "latest_download.txt"), "w") as f:
            f.write(filename)

        logger.info(f"Saved CSV to: {file_path}")
        return file_path
    except HTTPError as e:
        if response.status_code == 503:
            logger.info("CSV not ready yet (503), retrying...")
            time.sleep(2)

        logger.error(f"❌ Failed to download: {e}")
        raise


# scrapping function
def scrape_and_download(city_name, data_type, start_date=None, end_date=None):
    """ Scrapes weather data from NOAA's Daily Summaries portal. """
    driver = None
    try:
        driver = init_driver()
        wait = WebDriverWait(driver, 20)

        logger.info(f"Scraping started for city: {city_name}, type: {data_type}, start={start_date}, end={end_date}")

        # Open NOAA Daily Summaries search page
        driver.get(url)
        # Wait for page to be completely loaded
        wait.until(lambda d: d.execute_script("return document.readyState") == "complete")
        wait.until(EC.visibility_of_element_located(
            (By.CSS_SELECTOR, "#searchForm")
        ))

        # Expand Data Types section
        data_type_section = wait.until(EC.presence_of_element_located((By.ID, "whatInput")))
        data_type_section.clear()
        data_type_section.send_keys(data_type)

        # Fill in the 'Where' field
        where_input = element_is_present((By.ID, "whereInput"))
        where_input.click()
        for letter in city_name:
            where_input.send_keys(letter)
            time.sleep(0.1)

        logger.info(f"Typing city: {city_name}")

        # Select from dropdown
        wait.until(
            EC.visibility_of_all_elements_located((By.CSS_SELECTOR, "#whereComponent .dropdown-menu .dropdown-item")))
        items = driver.find_elements(By.CSS_SELECTOR, "#whereComponent .dropdown-menu .dropdown-item")
        logger.info(f"Dropdown items found: {len(items)}")

        for item in items:
            logger.debug(f"Item: {item.text}")
            if city_name.lower() in item.text.lower():
                item.click()
                time.sleep(1)
                break

        time.sleep(1)

        # Verify the selected location badge appeared
        badge = wait.until(EC.visibility_of_element_located(
            (By.CSS_SELECTOR, "#whereComponent .badge")
        ))
        logger.info(f"Location badge confirmed: {badge.text}")

        # Go to table with csv
        msg_element = driver.find_element(By.CSS_SELECTOR, ".alert.alert-info")
        logger.debug(f"Alert message element text: {msg_element.text}")

        msg = "No search results were found based on your criteria"

        if msg_element.text == msg:
            logger.warning(msg)
            logger.debug("Returning error message instead of CSV URL")
            return msg
        else:
            element = driver.find_element(By.CSS_SELECTOR, ".row.search-result-row.ng-star-inserted h5")
            go_to_element(element)

            page_count = 0
            max_pages = 3  # limited, no need to retrieve all the data
            city_match = city_name.split(',')[0].strip().lower()
            logger.info(f"city_match: {city_match}")

            preferred_stations = [
                s.lower().split(',', 1)[0].strip()
                for s in REVERSED_CITY_PREFS.get(city_match.upper(), [])
            ]
            logger.info(f"Preferred stations: {preferred_stations}")

            matching_csv_url = None
            preferred_match = None

            while page_count < max_pages:
            # while True: loop until there are no more pages left
                wait.until(EC.presence_of_element_located(
                    (By.CSS_SELECTOR, ".row.search-result-row.ng-star-inserted h5 a")
                ))
                csv_links = []
                links = driver.find_elements(
                    By.CSS_SELECTOR, ".row.search-result-row.ng-star-inserted h5 a")

                page = driver.find_element(By.CSS_SELECTOR,".row.search-result-row.ng-star-inserted .float-right a ")
                go_to_element(page)

                # Get the download URL
                for link in links:
                    href = link.get_attribute("href")
                    text = link.text.strip()
                    csv_links.append({'name': text, 'url': href})
                    logger.info(f"Found CSV link: {text} -> {href}")
                    # download_csv(href)
                    # logger.info(f"CSV downloaded from URL: {href}")

                    # 1) match a preferred station for the city
                    if preferred_match is None and any(pref in text.lower() for pref in preferred_stations):
                        matching_csv_url = href
                        logger.info(f"Matched Preferred station: '{text}' for city: '{city_match}'")
                        break
                    # 2) city‐fallback match (only if no preferred yet)
                    if matching_csv_url is None and city_match in text.lower():
                        matching_csv_url = href
                        logger.info(f"Matched city: {city_name} in text: {text}")

                try:
                    next_button =driver.find_element(
                        By.XPATH, "//li[@aria-label='next' and not(contains(@class, 'disabled'))]/a"
                    )
                    driver.execute_script("arguments[0].click();", next_button)
                    time.sleep(1)
                    page_count += 1
                except:
                    logger.info("No more pages.")
                    break

            logger.info(f"Total CSV links found: {len(csv_links)}")

            csv_url = matching_csv_url if matching_csv_url else csv_links[0]['url']
            logger.info(f"URL to download CSV : {csv_url}")

            # Download and save csv file
            download_csv(csv_url)

            return csv_url

    except Exception as e:
        logger.error(f"Scraping error: {e}", exc_info=True)
        raise
    finally:
        cleanup_driver()
