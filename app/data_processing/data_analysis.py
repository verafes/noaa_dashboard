import os
import io
import sqlite3
import pandas as pd

from matplotlib import pyplot as plt

from app.logger import logger

# DB location
DB_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), "../db")
DB_NAME = "noaa_weather.db"
DB_PATH = os.path.join(DB_DIR, DB_NAME)
TABLE_NAME = "weather_data"

# Ensure the DB directory exists
os.makedirs(DB_DIR, exist_ok=True)
logger.info(f"Database directory ensured: {DB_DIR}")

label_map = {
        'TAVG': 'Average Temperature',
        'TMAX': 'Maximum Temperature',
        'TMIN': 'Minimum Temperature',
        'PRCP': 'Precipitation',
        'SNOW': 'Snowfall'
    }

def load_data_from_db(db_path, table_name):
    conn = sqlite3.connect(db_path)
    query = f"SELECT * FROM {table_name}"
    df = pd.read_sql_query(query, conn, parse_dates=['DATE'])

    buffer = io.StringIO()
    df.info(buf=buffer)
    info_str = buffer.getvalue()
    logger.info(f"Loaded DataFrame info str :\n{info_str}")
    logger.info(f"Loaded DataFrame info:\n{df.info()}")
    conn.close()
    return df

def aggregate_by_station_and_time(df, date_freq='Y'):
    df['YEAR_PERIOD'] = df['DATE'].dt.to_period(date_freq)

    agg_cols = ['TMIN', 'TAVG', 'TMAX', 'PRCP', 'SNOW']
    agg_dict = {col: 'mean' for col in agg_cols if col in df.columns}

    grouped = df.groupby(['NAME', 'YEAR_PERIOD']).agg(agg_dict).reset_index()
    return grouped

def plot_max_temperature_trends(df_grouped, stations):
    plt.figure(figsize=(12, 6))
    for station in stations:
        station_data = df_grouped[df_grouped['NAME'] == station]
        if station_data.empty:
            print(f"No data for station: {station}")
            continue
        plt.plot(station_data['YEAR_PERIOD'].dt.to_timestamp(), station_data['TMAX'], label=station)

    plt.title("Yearly Max Temperature Trends by Station")
    plt.xlabel("Year")
    plt.ylabel("Max Temperature (°F)")
    plt.legend(loc='center left', bbox_to_anchor=(1, 0.5), fontsize='small')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.show()

def aggregate_snowfall_by_station_and_time(df, date_freq='Y'):
    df['YEAR_PERIOD'] = df['DATE'].dt.to_period(date_freq)
    agg_dict = {'SNOW': 'sum'}
    grouped = df.groupby(['NAME', 'YEAR_PERIOD']).agg(agg_dict).reset_index()
    return grouped

def aggregate_weather_conditions(df, date_freq='Y'):
    df['YEAR_PERIOD'] = df['DATE'].dt.to_period(date_freq)

    agg_cols = ['TMIN', 'TAVG', 'TMAX', 'PRCP', 'SNOW', 'WT16', 'ACMH', 'WSFG',
                'RHAV', 'TSUN', 'WT08', 'WT01']

    agg_dict = {col: 'mean' for col in agg_cols if col in df.columns}

    sum_cols = ['WT16', 'WT08', 'WT01']
    for col in sum_cols:
        if col in agg_dict:
            agg_dict[col] = 'sum'

    grouped = df.groupby(['NAME', 'YEAR_PERIOD']).agg(agg_dict).reset_index()
    return grouped

def plot_temperature(df_grouped, station_name):
    data = df_grouped[df_grouped['NAME'] == station_name]
    if data.empty:
        print(f"No data for station {station_name}")
        return

    plt.figure(figsize=(10, 6))
    plt.plot(data['YEAR_PERIOD'].dt.to_timestamp(), data['TMIN'], label='TMIN', color='blue')
    plt.plot(data['YEAR_PERIOD'].dt.to_timestamp(), data['TAVG'], label='TAVG', color='orange')
    plt.plot(data['YEAR_PERIOD'].dt.to_timestamp(), data['TMAX'], label='TMAX', color='red')
    plt.title(f"Temperature Trends for {station_name}")
    plt.xlabel("Year")
    plt.ylabel("Temperature (°F)")
    plt.legend()
    plt.show()

def plot_precipitation_and_snow(df_grouped, station_name):
    data = df_grouped[df_grouped['NAME'] == station_name]
    if data.empty:
        print(f"No data for station {station_name}")
        return

    plt.figure(figsize=(10, 6))
    plt.plot(data['YEAR_PERIOD'].dt.to_timestamp(), data['PRCP'], label='Precipitation (PRCP)', color='green')
    plt.plot(data['YEAR_PERIOD'].dt.to_timestamp(), data['SNOW'], label='Snowfall (SNOW)', color='cyan')
    plt.title(f"Precipitation and Snowfall for {station_name}")
    plt.xlabel("Year")
    plt.ylabel("Inches")
    plt.legend()
    plt.show()

def plot_weather_events(df_grouped, station_name):
    data = df_grouped[df_grouped['NAME'] == station_name]
    if data.empty:
        print(f"No data for station {station_name}")
        return

    plt.figure(figsize=(10, 6))
    plt.plot(data['YEAR_PERIOD'].dt.to_timestamp(), data['WT16'], label='WT16 (Weather Type 16)', color='purple')
    plt.plot(data['YEAR_PERIOD'].dt.to_timestamp(), data['WT08'], label='WT08 (Weather Type 08)', color='brown')
    plt.plot(data['YEAR_PERIOD'].dt.to_timestamp(), data['WT01'], label='WT01 (Weather Type 01)', color='black')
    plt.title(f"Weather Events for {station_name}")
    plt.xlabel("Year")
    plt.ylabel("Event Counts")
    plt.legend()
    plt.show()

def plot_snowfall_trends(df_grouped, stations):
    plt.figure(figsize=(14, 7))
    for station in stations:
        station_data = df_grouped[df_grouped['NAME'] == station]
        if station_data.empty:
            print(f"No data for station: {station}")
            continue
        plt.plot(station_data['YEAR_PERIOD'].dt.to_timestamp(), station_data['SNOW'], label=station)

    plt.title("Yearly Snowfall Trends by Station")
    plt.xlabel("Year")
    plt.ylabel("Total Snowfall (inches)")
    plt.legend(loc='upper right', fontsize='small', ncol=2)
    plt.tight_layout()
    plt.show()

def plot_snowfall_pie(df_grouped, year, min_threshold=0.01):
    year_str = str(year)
    data_year = df_grouped[df_grouped['YEAR_PERIOD'].astype(str) == year_str]

    if data_year.empty:
        print(f"No snowfall data for year {year}")
        return

    snowfall_sum = data_year.groupby('NAME')['SNOW'].sum()
    snowfall_sum = snowfall_sum[snowfall_sum > 0]

    if snowfall_sum.empty:
        print(f"No positive snowfall records found for year {year}")
        return

    total_snow = snowfall_sum.sum()
    large_slices = snowfall_sum[snowfall_sum / total_snow >= min_threshold]
    small_slices_sum = snowfall_sum[snowfall_sum / total_snow < min_threshold].sum()

    if small_slices_sum > 0:
        large_slices['Others'] = small_slices_sum

    fig, ax = plt.subplots(figsize=(16, 8))
    wedges, texts, autotexts = ax.pie(
        large_slices,
        labels=None,
        autopct='%1.1f%%',
        startangle=200,
        pctdistance=0.85,
        textprops={'fontsize': 9},
        wedgeprops={'edgecolor': 'white', 'linewidth': 0.5},
        radius=1.3
    )

    centre_circle = plt.Circle((0, 0), 0.85, fc='white')
    ax.add_artist(centre_circle)
    ax.set_title(f"Snowfall Contribution by Station in {year}")
    ax.axis('equal')

    ax.legend(
        wedges,
        large_slices.index,
        title="Stations",
        loc='center left',
        bbox_to_anchor=(1, 0.5),
        fontsize=9,
        title_fontsize=10
    )

    plt.subplots_adjust(left=0.05, right=0.7, top=0.9, bottom=0.1)
    plt.show()

def plot_snowfall_bar(df_grouped, year):
    year_str = str(year)
    data_year = df_grouped[df_grouped['YEAR_PERIOD'].astype(str) == year_str]

    if data_year.empty:
        print(f"No snowfall data for year {year}")
        return

    snowfall_sum = data_year.groupby('NAME')['SNOW'].sum().sort_values(ascending=False)

    plt.figure(figsize=(12, 6))
    snowfall_sum.plot(kind='bar', color='skyblue')
    plt.title(f"Total Snowfall by Station in {year}")
    plt.ylabel("Snowfall (inches)")
    plt.xlabel("Station")
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.show()

def plot_temperature_boxplot(df_grouped, temp_col='TAVG'):
    fig, ax = plt.subplots(figsize=(20, 6))
    readable_label = label_map.get(temp_col, temp_col)
    df_grouped.boxplot(
        column=temp_col,
        by='YEAR_PERIOD',
        grid=False,
        rot=90,
        patch_artist=True,
        ax=ax
    )
    ax.set_title(f'Distribution of {readable_label} Over Years')
    plt.suptitle('')
    ax.set_xlabel('Year')
    ax.set_ylabel(f'{readable_label} (°F)')
    plt.tight_layout()
    plt.show()

def show_max_temp_trends(df):
    df_agg = aggregate_by_station_and_time(df, date_freq='Y')
    sample_stations = df_agg['NAME'].unique()[:20]
    logger.info(f"Plotting max temperature trends for stations: {sample_stations}")
    plot_max_temperature_trends(df_agg, sample_stations)

def explore_weather_by_station(df, num):
    df_agg = aggregate_weather_conditions(df, date_freq='Y')
    stations = df_agg['NAME'].unique()[:num]
    for station in stations:
        print(f"Plotting weather data for station: {station}")
        plot_temperature(df_agg, station)
        plot_precipitation_and_snow(df_agg, station)
        plot_weather_events(df_agg, station)

def show_temp_boxplot(df):
    df_agg = aggregate_weather_conditions(df, date_freq='Y')
    plot_temperature_boxplot(df_agg, temp_col='TAVG')

def menu(df_weather):
    while True:
        print("\n====== NOAA Weather Data Menu ======")
        print("1 - Show loaded weather data info")
        print("2 - Plot max temperature trends")
        print("3 - Show snowfall pie & bar chart for year")
        print("4 - Explore temperature, PRCP, and WT per station")
        print("5 - Boxplot: Avg temperature distribution over years")
        print("0 - Exit")
        choice = input("Choose an option: ").strip()

        if choice == '1':
            show_max_temp_trends(df_weather)
        elif choice == '2':
            plot_snowfall_pie(df_weather)
        elif choice == '3':
            plot_snowfall_bar(df_weather)
        elif choice == '4':
            explore_weather_by_station(df_weather)
        elif choice == '5':
            plot_temperature_boxplot(df_weather)
        elif choice == '0':
            print("Exiting. Bye!")
            break
        else:
            print("Invalid option. Try again.")

if __name__ == "__main__":
    logger.info("Starting weather data analysis...")

    df_weather = load_data_from_db(DB_PATH, TABLE_NAME)
    logger.info(f"Loaded weather data: {len(df_weather)} records")

    logger.info("Checking for missing values:")
    logger.info(f"\n{df_weather.isna().sum()}")

    df_agg = aggregate_by_station_and_time(df_weather, date_freq='Y')
    logger.info(f"Aggregated data shape: {df_agg.shape}")
    sample_stations = df_agg['NAME'].unique()[:20]
    logger.info(f"Plotting max temperature trends for stations: {sample_stations}")
    plot_max_temperature_trends(df_agg, sample_stations)

    plot_snowfall_trends(df_agg, sample_stations)

    df_agg = aggregate_weather_conditions(df_weather, date_freq='Y')

    # Pie chart for snowfall in 2020
    plot_snowfall_pie(df_agg, 2020)

    # Bar chart for snowfall in 2020
    plot_snowfall_bar(df_agg, 2020)

    # Boxplot for average temp distribution over years
    plot_temperature_boxplot(df_agg, temp_col='TAVG')

    logger.info("Script completed.")
