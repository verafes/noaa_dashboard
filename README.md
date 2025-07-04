# NOAA Dashboard - Web Scraping and Dashboard Project

A Python program that retrieves **historical daily weather data** from the [NOAA National Centers for Environmental Information](https://www.ncei.noaa.gov/access/search/data-search/daily-summaries) website and display the results in an interactive dashboard.

All operations, from web scraping with Selenium and data cleaning, to transforming, storing in a SQLite database, querying, and presenting interactive visualizations, are seamlessly managed and triggered directly through the intuitive user interface.

You can access the live version of the dashboard at: [[https://noaa-dashboard.onrender.com](https://noaa-dashboard.onrender.com)

# NOAA Historical Weather Data Dashboard

## Project Overview

This project provides a robust solution for retrieving, processing, storing, and visualizing historical daily weather data from the NOAA National Centers for Environmental Information (NCEI) website. It leverages web scraping with Selenium to collect raw data, followed by comprehensive data cleaning and transformation. The structured data is then stored in a SQLite database, accessible via a command-line interface for querying, and presented through an interactive web dashboard built with Dash for rich visualizations.

## Features

* **Web Scraping:** Automated retrieval of historical daily weather data from the NOAA NCEI website using Selenium.
* **Data Processing:** Robust data cleaning and transformation pipelines to convert raw, scraped data into a structured and usable format.
* **Database Integration:** Persistent storage of processed weather data in a local SQLite database for efficient querying and retrieval.
* **Interactive Dashboard:** A dynamic web application built with Dash, offering interactive visualizations (plots, charts, heatmaps) of weather trends and patterns.
* **Modular Design:** Separated concerns for web scraping, data processing, database management, and dashboard presentation.

## Technologies Used

* **Python 3.x:** The core programming language.
* **Flask:** The lightweight web framework Dash runs on.
* **Dash:** For building the interactive web dashboard.
* **SQLite:** A lightweight database for data storage.
* **Pandas & NumPy:** Handles data manipulation, cleaning, and analysis with DataFrames.
* **Plotly:** For generating interactive charts and plots within Dash.
* **Selenium:** For web scraping and browser automation.
* **Matplotlib & Seaborn:** Generates static and statistical plots.
* **python-dotenv:** For managing environment variables (e.g., API keys, database paths).
* **Requests:** For making HTTP requests.
* **geonamescache:** Provides offline country and city data.

## Installation

### Prerequisites

Before you begin, ensure you have the following installed:

* **Python 3.8+** (recommended)
* **pip** (Python package installer)

### Setup Steps

1.  **Clone the Repository:**
2.  **Create and Activate a Virtual Environment (Recommended):**
    ```bash
    python -m venv venv
    # On Windows:
    .\venv\Scripts\activate
    # On macOS/Linux:
    source venv/bin/activate
    ```

3.  **Install Dependencies:**
    Install all required Python packages: `pip install -r requirements.txt`

4.  **Environment Variables (Optional but Recommended):**
    Create a `.env` file in the root directory of your project to store sensitive information or configuration paths using .env.example
    Ensure you load these variables in your Python code using `python-dotenv`.

## Usage

### 1. Scrape and Ingest Data

To get started with the NOAA Historical Weather Data Dashboard, follow these steps:

1.  **Launch the Application:**
    Navigate to the root directory of the project in your terminal and run the main application script: `py run.py`

2.  **Access the Dashboard:**
    Once the application starts, it will display a URL in your terminal (e.g., `http://127.0.0.1:8050/`). Open this URL in your web browser.

3.  **Interact via the Dashboard:**
    All project functionalities—including **web scraping, data cleaning, importing data to the SQLite database, and generating interactive visualizations**—are accessible directly through the buttons and input fields on the web dashboard. 

5. Follow the prompts and click the respective buttons (e.g., "Download Data," "Submit," "Clean Data," "Import to DB," "Visualize Data") to perform operations and explore the weather data.


## License

MIT License - see LICENSE.md for details.

