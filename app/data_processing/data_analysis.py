import os
import io
import sqlite3
import pandas as pd

import matplotlib
matplotlib.use('TkAgg')

from matplotlib import pyplot as plt
import plotly.express as px
import seaborn as sns

from app.logger import logger
from app.utils import BASE_DATA_DIR,DB_DIR, DB_PATH, DB_NAME, TABLE_NAME, label_map

cols = [
    'TMIN', 'TAVG', 'TMAX', 'PRCP', 'SNOW', 'TSUN',
    'ACMH', 'WSFG', 'RHAV', 'WT01', 'WT02', 'WT08', 'WT16'
    ]

def load_data_from_db(db_path, table_name):
    """Load data from SQLite table into a DataFrame."""
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

def get_label(col):
    """Get readable label for a weather code."""
    return label_map.get(col, col)

def aggregate_by_station_and_time(df, date_freq='Y', agg_cols=None):
    """Aggregate weather data by station and period."""
    df['YEAR_PERIOD'] = df['DATE'].dt.to_period(date_freq)

    if agg_cols is None:
        agg_cols = cols

    agg_dict = {col: 'mean' for col in agg_cols if col in df.columns}

    grouped = df.groupby(['NAME', 'YEAR_PERIOD']).agg(agg_dict).reset_index()
    return grouped

def plot_max_temperature_trends(df_grouped, stations):
    """Plot yearly max temperature trends for stations."""
    plt.figure(figsize=(12, 6))
    for station in stations:
        station_data = df_grouped[df_grouped['NAME'] == station]
        if station_data.empty:
            logger.info(f"No data for station: {station}")
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
    """Sum snowfall by station and period."""
    df['YEAR_PERIOD'] = df['DATE'].dt.to_period(date_freq)
    agg_dict = {'SNOW': 'sum'}
    grouped = df.groupby(['NAME', 'YEAR_PERIOD']).agg(agg_dict).reset_index()
    return grouped

def aggregate_weather_conditions(df, date_freq='Y'):
    """Aggregate multiple weather metrics by station and period."""
    df['YEAR_PERIOD'] = df['DATE'].dt.to_period(date_freq)

    agg_dict = {col: 'mean' for col in cols if col in df.columns}

    sum_cols = ['WT16', 'WT08', 'WT01']
    for col in sum_cols:
        if col in agg_dict:
            agg_dict[col] = 'sum'

    grouped = df.groupby(['NAME', 'YEAR_PERIOD']).agg(agg_dict).reset_index()
    return grouped

def plot_temperature(df_grouped, station_name):
    """Plot temperature trends for one station."""
    data = df_grouped[df_grouped['NAME'] == station_name]
    if data.empty:
        logger.info(f"No data for station {station_name}")
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
    """Plot precipitation and snowfall for one station."""
    data = df_grouped[df_grouped['NAME'] == station_name]
    if data.empty:
        logger.info(f"No data for station {station_name}")
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
    """Plot weather event counts for one station."""
    data = df_grouped[df_grouped['NAME'] == station_name]
    if data.empty:
        logger.info(f"No data for station {station_name}")
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
    """Plot yearly snowfall trends for stations."""
    plt.figure(figsize=(14, 7))
    for station in stations:
        station_data = df_grouped[df_grouped['NAME'] == station]
        if station_data.empty:
            logger.info(f"No data for station: {station}")
            continue
        plt.plot(station_data['YEAR_PERIOD'].dt.to_timestamp(), station_data['SNOW'], label=station)

    plt.title("Yearly Snowfall Trends by Station")
    plt.xlabel("Year")
    plt.ylabel("Total Snowfall (inches)")
    plt.legend(loc='upper right', fontsize='small', ncol=2)
    plt.tight_layout()
    plt.show()

def plot_snowfall_pie(df_grouped, year, min_threshold=0.01):
    """Pie chart of snowfall contribution by station for a year."""
    year_str = str(year)
    data_year = df_grouped[df_grouped['YEAR_PERIOD'].astype(str) == year_str]

    if data_year.empty:
        logger.info(f"No snowfall data for year {year}")
        return

    snowfall_sum = data_year.groupby('NAME')['SNOW'].sum()
    snowfall_sum = snowfall_sum[snowfall_sum > 0]

    if snowfall_sum.empty:
        logger.info(f"No positive snowfall records found for year {year}")
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
    """Bar chart of snowfall totals by station for a year."""
    year_str = str(year)
    data_year = df_grouped[df_grouped['YEAR_PERIOD'].astype(str) == year_str]

    if data_year.empty:
        logger.info(f"No snowfall data for year {year}")
        return

    snowfall_sum = data_year.groupby('NAME')['SNOW'].sum()
    snowfall_sum = snowfall_sum[snowfall_sum >= 0.15].sort_values(ascending=False)

    if snowfall_sum.empty:
        logger.info(f"All stations had snowfall less than 0.2 inches in {year}")
        return

    plt.figure(figsize=(12, 6))
    snowfall_sum.plot(kind='bar', color='skyblue')
    plt.title(f"Total Snowfall by Station in {year}")
    plt.ylabel("Snowfall (inches)")
    plt.xlabel("Station")
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.show()

def plot_temperature_boxplot(df_grouped, temp_col='TAVG'):
    """Boxplot of temperature distribution by year."""
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

def show_max_temp_trends(df, agg_cols):
    """Aggregate and plot max temperature trends for stations."""
    df_agg = aggregate_by_station_and_time(df, date_freq='Y', agg_cols=agg_cols)
    sample_stations = df_agg['NAME'].unique()[:20]
    logger.info(f"Plotting max temperature trends for stations: {sample_stations}")
    plot_max_temperature_trends(df_agg, sample_stations)

def explore_weather_by_station(df, num):
    """Plot various weather charts for selected stations."""
    df_agg = aggregate_weather_conditions(df, date_freq='Y')
    stations = df_agg['NAME'].unique()[:num]
    for station in stations:
        logger.info(f"Plotting weather data for station: {station}")
        plot_temperature(df_agg, station)
        plot_precipitation_and_snow(df_agg, station)
        plot_weather_events(df_agg, station)
        plt.show()

def plot_station_trends(df_grouped, stations, variable, label_map, max_value=None):
    """ Plot yearly trends of a single weather variable for each station separately."""
    try:
        df_grouped = df_grouped.copy()

        for station in stations:
            station_data = df_grouped[df_grouped['NAME'] == station]
            if station_data.empty:
                logger.info(f"No data for station: {station}")
                continue
            plt.plot(station_data['YEAR_PERIOD'].dt.to_timestamp(), station_data[variable], label=station)

        df_grouped['YEAR'] = df_grouped['DATE'].dt.year
        df_filtered = df_grouped[df_grouped[variable].notna()]


        if max_value is not None:
            df_filtered = df_filtered[df_filtered[variable] <= max_value]

        if df_filtered.empty:
            print("No data to plot after filtering.")
            return

        yearly_station_avg = df_filtered.groupby(['NAME', 'YEAR'])[variable].mean().reset_index()

        title = f"Yearly Average {label_map.get(variable, variable)} by Station"

        fig = px.line(
            yearly_station_avg,
            x='YEAR',
            y=variable,
            color='NAME',
            title=title,
            labels={
                'YEAR': 'Year',
                variable: label_map.get(variable, variable),
                'NAME': 'Station'
            }
        )
        fig.show()
    except Exception as e:
        print(f"Error plotting trends: {str(e)}")

# Annual Average by Column
def plot_annual_averages(df, columns, label_map):
    """ "Plot annual averages of selected weather features."""
    df['YEAR'] = df['DATE'].dt.year
    available = [col for col in columns if col in df.columns and df[col].notna().sum() > 0]
    missing = [col for col in columns if col not in df.columns or df[col].notna().sum() == 0]

    if missing:
        logger.info(f"Skipping missing or empty columns: {missing}")
    if not available:
        logger.info(f"❌ No valid columns to plot.")
        return

    # Group and calculate mean
    yearly_avg = df.groupby('YEAR')[available].agg('mean')
    yearly_avg = yearly_avg.dropna(how='all')
    yearly_avg = yearly_avg[(yearly_avg > 0).any(axis=1)]
    yearly_avg = yearly_avg.reset_index()

    # Reshape for Plotly (wide → long)
    melted = yearly_avg.melt(id_vars='YEAR', value_vars=available, var_name='Variable', value_name='Average')

    # Replace variable names with human-friendly labels
    melted['Variable'] = melted['Variable'].apply(lambda c: label_map.get(c, c))

    fig = px.line(
        melted,
        x='YEAR',
        y='Average',
        color='Variable',
        title='Annual Averages of Weather Features',
        labels={
            'YEAR': 'Year',
            'Average': 'Average Value',
            'Variable': 'Weather Events'
        }
    )
    fig.show()

# Weather Event Frequency (for WT codes)
def plot_weather_one_event_frequencies(df, event_cols, label_map):
    """Plot yearly counts of weather events."""
    df['YEAR'] = df['DATE'].dt.year
    for col in event_cols:
        if col in df.columns:
            flag_col = f"{col}_flag"
            df[flag_col] = df[col].apply(lambda x: 1 if x > 0 else 0)
            yearly_count = df.groupby('YEAR')[flag_col].sum().reset_index()
            fig = px.bar(
                yearly_count,
                x='YEAR',
                y=flag_col,
                title=f"{label_map.get(col, col)} Count per Year",
                labels={flag_col: label_map.get(col, col)}
            )
            logger.info(f"Plotting: {col}")
            fig.show()

def prepare_event_flags(df: pd.DataFrame, event_cols: list[str]) -> pd.DataFrame:
    """ Add *_flag columns to DataFrame where event occurred (value > 0). """
    df = df.copy()
    df['YEAR'] = df['DATE'].dt.year

    for col in event_cols:
        if col in df.columns:
            flag_col = f"{col}_flag"
            df[flag_col] = df[col].apply(lambda x: 1 if pd.notna(x) and x > 0 else 0)

    return df

def plot_aggregated_weather_event_frequencies(df, event_cols, label_map, year_from=None, year_to=None):
    """ Plot yearly counts of multiple weather events on one combined figure. """
    df = df.copy()
    df['YEAR'] = df['DATE'].dt.year

    # Ensure flags exist (should already if prepare_event_flags used)
    for col in event_cols:
        flag_col = f"{col}_flag"
        if flag_col not in df.columns:
            df[flag_col] = df[col].apply(lambda x: 1 if pd.notna(x) and x > 0 else 0)

    # Compute yearly totals to find valid years to filter out low data years
    counts_tmp = df.groupby('YEAR')[[f"{col}_flag" for col in event_cols]].sum()
    counts_tmp['total'] = counts_tmp.sum(axis=1)
    valid_years = counts_tmp[counts_tmp['total'] >= 250].index.tolist()

    logger.info(f"Filtered years (total_events >= 250): {min(valid_years)} to {max(valid_years)}")
    # Filter original df to valid years only
    df = df[df['YEAR'].isin(valid_years)]

    if year_from is not None and year_from in valid_years:
        df = df[df['YEAR'] >= year_from]
    if year_to is not None and year_to in valid_years:
        df = df[df['YEAR'] <= year_to]

    yearly_counts = df.groupby('YEAR')[[f"{col}_flag" for col in event_cols]].sum().reset_index()
    rename_map = {
        f"{col}_flag": label_map.get(col, f"Unknown ({col})")
        for col in event_cols
    }
    yearly_counts.rename(columns=rename_map, inplace=True)

    # Plot combined bar chart
    logger.info(f"Years in final chart: {yearly_counts['YEAR'].tolist()}")
    fig = px.bar(
        yearly_counts,
        x='YEAR',
        y=list(rename_map.values()),  # new human-readable column names
        title=f"Weather Event Counts per Year ({year_from or 'Start'} - {year_to or 'End'})",
        barmode='group' # side by side bars
    )
    fig.update_xaxes(range=[min(yearly_counts['YEAR']), max(yearly_counts['YEAR'])])

    fig.show()

def plot_yearly_distributions(df, columns, label_map):
    """Plot yearly boxplots for weather variables (spread/distribution)"""
    df['YEAR'] = df['DATE'].dt.year
    for col in columns:
        if col in df.columns:
            fig = px.box(
                df,
                x='YEAR',
                y=col,
                title=f"{label_map.get(col, col)} Distribution by Year",
                labels={'YEAR': 'Year', col: label_map.get(col, col)}
            )
            fig.show()

def plot_weather_correlation_heatmap(df, columns):
    """Show correlation heatmap for selected weather features."""
    df_agg = aggregate_weather_conditions(df, date_freq='Y')

    missing_cols = [col for col in columns if col not in df_agg.columns]
    if missing_cols:
        logger.info(f"Missing columns in aggregated data: {missing_cols}")
        columns = [col for col in columns if col in df_agg.columns]

    if not columns:
        logger.info("No valid columns to plot.")
        return

    logger.info("Missing values per column in aggregated data:")
    for col in columns:
        nan_count = df_agg[col].isna().sum()
        logger.info(f"  {col}: {nan_count} missing")

    df_agg_clean = df_agg.dropna(subset=columns)
    logger.info(f"Rows after dropping missing values in {columns}: {len(df_agg_clean)}")

    df_corr = df_agg[columns].corr()

    plt.figure(figsize=(10, 8))
    sns.heatmap(df_corr, annot=True, cmap='coolwarm', fmt=".2f")
    plt.title("Correlation Between Weather Features")
    plt.tight_layout()
    plt.show()

def menu(df_weather, year, num):
    """Interactive menu to explore weather data plots."""
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
            agg_cols = ['TMIN', 'TAVG', 'TMAX', 'PRCP', 'SNOW', 'TSUN']
            show_max_temp_trends(df_weather, agg_cols)
        elif choice == '2':
            plot_snowfall_pie(df_weather, year)
        elif choice == '3':
            plot_snowfall_bar(df_weather, year)
        elif choice == '4':
            explore_weather_by_station(df_weather, num)
        elif choice == '5':
            df_agg = aggregate_weather_conditions(df_weather, date_freq='Y')
            plot_temperature_boxplot(df_agg)
        elif choice == '0':
            print("Exiting. Bye!")
            break
        else:
            print("Invalid option. Try again.")

def analysis_and_visualization():
    """Performs weather data analysis and generates visualizations for weather trends in CLI"""
    logger.info("Starting weather data analysis...")

    df_weather = load_data_from_db(DB_PATH, TABLE_NAME)
    logger.info(f"Loaded weather data: {len(df_weather)} records")

    logger.info("Checking for missing values:")
    logger.info(f"\n{df_weather.isna().sum()}")

    df_agg = aggregate_weather_conditions(df_weather)
    logger.info(f"Aggregated data shape: {df_agg.shape}")
    sample_stations = df_agg['NAME'].unique()[:20]
    logger.info(f"Plotting max temperature trends for stations: {sample_stations}")
    plot_max_temperature_trends(df_agg, sample_stations)

    plot_snowfall_trends(df_agg, sample_stations)

    # Pie chart for snowfall in 2020
    plot_snowfall_pie(df_agg, 2020)

    # Bar chart for snowfall in 2020
    plot_snowfall_bar(df_agg, 2020)

    # Boxplot for average temp distribution over years
    plot_temperature_boxplot(df_agg, temp_col='TAVG')

    plot_annual_averages(df_weather, ['TSUN', 'WSFG', 'RHAV'], label_map)
    plot_aggregated_weather_event_frequencies(df_weather, ['WT01', 'WT02', 'WT08', 'WT16'], label_map)
    plot_weather_correlation_heatmap(df_weather, [
        'TMIN', 'TAVG', 'TMAX', 'PRCP', 'SNOW', 'TSUN',
        'ACMH', 'WSFG', 'RHAV', 'WT01', 'WT08', 'WT16'
    ])

    logger.info("Script completed.")

# -------------------------
# analysis_and_visualization()
# py -m app.data_processing.data_analysis
