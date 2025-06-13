import os
import time
import requests

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from dotenv import load_dotenv


# Configuration
load_dotenv()
DOWNLOAD_DIR = os.path.abspath("data")
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
        chrome_options.add_argument("--incognito")
        chrome_options.add_experimental_option("prefs", {
            "download.default_directory": os.path.abspath("data"),
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True
        })
        driver = webdriver.Chrome(options=chrome_options)
        os.makedirs("data", exist_ok=True)
    return driver

def cleanup_driver():
    """Clean up the WebDriver"""
    global driver
    if driver is not None:
        driver.quit()
        driver = None

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

    file_path = os.path.join("data", filename)
    response = requests.get(url)
    response.raise_for_status()  # Raise error if download fails

    with open(file_path, "wb") as f:
        f.write(response.content)


    with open(os.path.join("data", "latest_download.txt"), "w") as f:
        f.write(filename)

    return file_path

# scrapping function
def scrape_and_download(city_name, data_type, start_date=None, end_date=None):
    """ Scrapes weather data from NOAA's Daily Summaries portal. """
    driver = None
    # with create_driver() as driver:
    try:
        driver = init_driver()
        wait = WebDriverWait(driver, 20)
        if not start_date:
            start_date = None
        if not end_date:
            end_date = None
        print(
            f"[DEBUG] Called scrape_and_download with: city={city_name}, type={data_type}, start={start_date}, end={end_date}")

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
        data_type_section.send_keys(data_type) # "Average temperature" # id=TVG

        # Fill in the 'Where' field
        where_input = element_is_present((By.ID, "whereInput"))
        where_input.click()
        for letter in city_name:
            where_input.send_keys(letter)
            time.sleep(0.1)

        print("city_name", city_name)

        # Select from dropdown
        wait.until(
            EC.visibility_of_all_elements_located((By.CSS_SELECTOR, "#whereComponent .dropdown-menu .dropdown-item")))
        items = driver.find_elements(By.CSS_SELECTOR, "#whereComponent .dropdown-menu .dropdown-item")
        print(f"Dropdown items found: {len(items)}")
        for item in items:
            print(item.text)

        for item in items:
            if city_name.lower() in item.text.lower():
                item.click()
                time.sleep(1)
                break

        time.sleep(1)

        # Verify the selected location badge appeared
        badge = wait.until(EC.visibility_of_element_located(
            (By.CSS_SELECTOR, "#whereComponent .badge")
        ))
        print(f"Badge confirmed: {badge.text}")

        # Go to table with csv
        # driver.execute_script("window.scrollBy(0, 300);")
        msg_element = driver.find_element(By.CSS_SELECTOR, ".alert.alert-info")
        msg = "No search results were found based on your criteria"

        if msg_element.text == msg:
            print(msg)
            return msg
        else:
            element = driver.find_element(By.CSS_SELECTOR, ".row.search-result-row.ng-star-inserted h5 a")
            go_to_element(element)

            wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, ".row.search-result-row.ng-star-inserted h5 a")
            ))
            links = driver.find_elements(By.CSS_SELECTOR, ".row.search-result-row.ng-star-inserted h5 a")

            # Get the download URL
            csv_url = links[0].get_attribute("href")
            print("csv_url", csv_url)

            # Download and save csv file
            download_csv(csv_url)
            driver.quit()

            return csv_url

    except Exception as e:
        print(f"Scraping error: {e}")
        raise
    finally:
        cleanup_driver()
