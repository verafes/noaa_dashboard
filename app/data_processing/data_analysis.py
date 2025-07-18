import os
import io
import base64
import sqlite3
import pandas as pd

import plotly.io as pio
from matplotlib import pyplot as plt
import plotly.express as px
import seaborn as sns

from app.logger import logger
from app.utils import DB_DIR, DB_PATH, DB_NAME, TABLE_NAME, label_map

# cache data
_cached_weather_data = None

def get_weather_data():
    global _cached_weather_data
    if _cached_weather_data is None:
        _cached_weather_data = load_data_from_db(DB_PATH, TABLE_NAME)
    return _cached_weather_data

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

def fig_to_dash_image(fig):
    """Convert a matplotlib figure to Dash HTML image."""
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches='tight')
    buf.seek(0)
    encoded = base64.b64encode(buf.read()).decode("utf-8")
    buf.close()
    return f"data:image/png;base64,{encoded}"

def plotly_fig_to_base64_img(fig):
    img_bytes = pio.to_image(fig, format='png')
    encoded = base64.b64encode(img_bytes).decode('utf-8')
    return f"data:image/png;base64,{encoded}"

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

    plt.title("Yearly Max Temperature Trends by Station", pad=15)
    plt.xlabel("Year")
    plt.ylabel("Max Temperature (°F)")
    plt.legend(loc='center left', bbox_to_anchor=(1, 0.5), fontsize='small')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    # plt.show()
    fig = plt.gcf()
    plt.close()
    return fig_to_dash_image(fig)

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
    plt.title(f"Temperature Trends for {station_name}", pad=15)
    plt.xlabel("Year")
    plt.ylabel("Temperature (°F)")
    plt.legend()
    # plt.show()
    fig = plt.gcf()
    plt.close()
    return fig_to_dash_image(fig)

def plot_precipitation_and_snow(df_grouped, station_name):
    """Plot precipitation and snowfall for one station."""
    data = df_grouped[df_grouped['NAME'] == station_name]
    if data.empty:
        logger.info(f"No data for station {station_name}")
        return

    plt.figure(figsize=(10, 6))
    plt.plot(data['YEAR_PERIOD'].dt.to_timestamp(), data['PRCP'], label='Precipitation (PRCP)', color='green')
    plt.plot(data['YEAR_PERIOD'].dt.to_timestamp(), data['SNOW'], label='Snowfall (SNOW)', color='cyan')
    plt.title(f"Precipitation and Snowfall for {station_name}", pad=15)
    plt.xlabel("Year")
    plt.ylabel("Inches")
    plt.legend()
    # plt.show()
    fig = plt.gcf()
    plt.close()
    return fig_to_dash_image(fig)

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
    plt.title(f"Weather Events for {station_name}", pad=15)
    plt.xlabel("Year")
    plt.ylabel("Event Counts")
    plt.legend()
    # plt.show()
    fig = plt.gcf()
    plt.close()
    return fig_to_dash_image(fig)

def plot_snowfall_trends(df_grouped, stations):
    """Plot yearly snowfall trends for stations."""
    plt.figure(figsize=(14, 7))
    for station in stations:
        station_data = df_grouped[df_grouped['NAME'] == station]
        if station_data.empty:
            logger.info(f"No data for station: {station}")
            continue
        plt.plot(station_data['YEAR_PERIOD'].dt.to_timestamp(), station_data['SNOW'], label=station)

    plt.title("Yearly Snowfall Trends by Station", pad=15)
    plt.xlabel("Year")
    plt.ylabel("Total Snowfall (inches)")
    plt.legend(loc='upper right', fontsize='small', ncol=2)
    plt.tight_layout()
    # plt.show()
    fig = plt.gcf()
    plt.close()
    return fig_to_dash_image(fig)

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
    # fig.show()
    fig = plt.gcf()
    plt.close()
    return fig_to_dash_image(fig)

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
    plt.title(f"Total Snowfall by Station in {year}", pad=15)
    plt.ylabel("Snowfall (inches)")
    plt.xlabel("Station")
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    # plt.show()
    fig = plt.gcf()
    plt.close()
    return fig_to_dash_image(fig)

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
    ax.set_title(f'Distribution of {readable_label} Over Years', pad=10)
    plt.suptitle('')
    ax.set_xlabel('Year')
    ax.set_ylabel(f'{readable_label} (°F)')
    plt.tight_layout()
    # plt.show()
    fig = plt.gcf()
    plt.close()
    return fig_to_dash_image(fig)

def show_max_temp_trends(df, agg_cols):
    """Aggregate and plot max temperature trends for stations."""
    df_agg = aggregate_by_station_and_time(df, date_freq='Y', agg_cols=agg_cols)
    sample_stations = df_agg['NAME'].unique()[:20]
    logger.info(f"Plotting max temperature trends for stations: {sample_stations}")
    plot_max_temperature_trends(df_agg, sample_stations)

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
        barmode='group'
    )
    fig.update_xaxes(range=[min(yearly_counts['YEAR']), max(yearly_counts['YEAR'])])
    fig.update_layout(legend_title_text='Weather Event', title_x=0.5)
    # fig.show()
    return plotly_fig_to_base64_img(fig)

def plot_yearly_distributions(df, columns, label_map):
    """Plot yearly boxplots for weather variables (spread/distribution)"""
    df['YEAR'] = df['DATE'].dt.year
    images = []
    for col in columns:
        if col in df.columns:
            fig = px.box(
                df,
                x='YEAR',
                y=col,
                title=f"{label_map.get(col, col)} Distribution by Year",
                labels={'YEAR': 'Year', col: label_map.get(col, col)}
            )
            # fig.show()
            try:
                img_bytes = fig.to_image(format="png")
                encoded = base64.b64encode(img_bytes).decode()
                img_src = f"data:image/png;base64,{encoded}"
                images.append(img_src)
            except Exception as e:
                logger.error(f"Failed to render image for {col}: {e}")
    return images

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

    df_agg_filled = df_agg.copy()
    for col in columns:
        mean_val = df_agg_filled[col].mean()
        df_agg_filled[col] = df_agg_filled[col].fillna(mean_val)
    df_corr = df_agg_filled[columns].corr()
    logger.info(df_corr)

    plt.figure(figsize=(10, 8))
    sns.heatmap(df_corr, annot=True, cmap='coolwarm', fmt=".2f")
    plt.title("Correlation Between Weather Features", pad=15)
    plt.tight_layout()
    # plt.show()
    fig = plt.gcf()
    plt.close()
    img_str = fig_to_dash_image(fig)
    logger.info(f"Generated image string length: {len(img_str)}")
    return img_str

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

    plot_aggregated_weather_event_frequencies(df_weather, ['WT01', 'WT02', 'WT08', 'WT16'], label_map)
    plot_weather_correlation_heatmap(df_weather, [
        'TMIN', 'TAVG', 'TMAX', 'PRCP', 'SNOW', 'TSUN',
        'ACMH', 'WSFG', 'RHAV', 'WT01', 'WT08', 'WT16'
    ])

    logger.info("Script completed.")

# -------------------------
# analysis_and_visualization()
# uncomment plt.show() fig.show() to run from CLI
# py -m app.data_processing.data_analysis
