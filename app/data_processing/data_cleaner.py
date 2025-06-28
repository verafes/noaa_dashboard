import os
import glob
import numpy as np
import pandas as pd

from app.utils import PROJECT_ROOT, RAW_DATA_DIR, PROCESSED_DATA_DIR, get_latest_csv_filename
from app.logger import logger

input_dir=RAW_DATA_DIR
output_dir=PROCESSED_DATA_DIR


def list_csv_files(input_dir):
    """Return a list of CSV file paths in the directory."""
    csv_files = glob.glob(os.path.join(input_dir, "*.csv"))
    if not csv_files:
        logger.info(f"No CSV files found in {input_dir}")
    else:
        logger.info(f"Found {len(csv_files)} CSV files in {input_dir}")
    return csv_files

def write_file_list(file_list, output_list_path):
    """Write list of file paths to a text file."""
    with open(output_list_path, "w") as f:
        for file_path in file_list:
            f.write(f"{os.path.basename(file_path)}\n")
    logger.info(f"Wrote list of files to {output_list_path}")

def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    base_cols = ['STATION', 'DATE', 'LATITUDE', 'LONGITUDE', 'ELEVATION', 'NAME']
    required_columns = set(base_cols)
    keep_cols = base_cols + ['TAVG', 'TMIN', 'TMAX', 'WT16', 'SNOW', 'ACMH', 'WSFG',
                         'PRCP', 'RHAV', 'TSUN', 'WT08', 'WT01', 'WT02']

    missing_columns = required_columns - set(df.columns)
    if missing_columns:
        logger.error(f"[CLEAN] Missing required columns: {', '.join(missing_columns)}")
        return pd.DataFrame()

    # Remove columns that end with '_ATTRIBUTES'
    df = df.loc[:, ~df.columns.str.endswith('_ATTRIBUTES')].copy()

    # Remove rows: replace empty strings with NaN, and drop fully empty rows
    df = df.replace(r'^\s*$', np.nan, regex=True)
    df.dropna(how='all', inplace=True)

    # Drop rows where only base_cols have values
    # (Do NOT drop it if at least one data column has a value)
    logger.info(f"Before cleaning: {df.shape}")

    data_columns = df.columns.difference(base_cols)
    logger.info(f"Data columns to check for NaNs: {list(data_columns)}")
    logger.info(f"Null counts:\n{df[data_columns].isnull().sum()}")

    df = df.dropna(subset=data_columns, how='all')
    logger.info(f"After cleaning: {df.shape}")

    # Keep only relevant columns: base + present allowed data columns
    df = df[[col for col in keep_cols if col in df.columns]].copy()

    # clean leading and trailing spaces in STR columns
    for col in df.select_dtypes(include=['object']):
        df[col] = df[col].astype(str).str.strip()
        logger.info(f"Cleaned column '{col}', sample values:\n{df[col].head()}")

    # Validate 'DATE' column
    df['DATE'] = pd.to_datetime(df['DATE'], errors='coerce')
    df.dropna(subset=['DATE'], inplace=True)
    logger.info(f"DATE column converted to datetime. Valid dates count: {df['DATE'].notna().sum()}")

    # Fill 'TAVG' with average of 'TMAX' and 'TMIN'
    if all(col in df.columns for col in ['TMAX', 'TMIN']):
        avg_temp = df[['TMAX', 'TMIN']].mean(axis=1)
        if 'TAVG' in df.columns:
            df['TAVG'] = df['TAVG'].fillna(avg_temp)
        else:
            df['TAVG'] = avg_temp

    # Remove rows with unrealistic temperature values (in Celsius)
    temp_cols = ['TAVG', 'TMIN', 'TMAX']
    for col in temp_cols:
        if col in df.columns:
            df = df[(df[col].isna()) | ((df[col] >= -500) & (df[col] <= 512))]

    # Convert all non-base columns to numeric
    numeric_cols = [col for col in df.columns if col not in base_cols]
    for col in numeric_cols:
        before_na = df[col].isna().sum()
        df[col] = pd.to_numeric(df[col], errors='coerce')
        after_na = df[col].isna().sum()
        if after_na > before_na:
            logger.warning(f"[CLEAN] Column '{col}': {after_na - before_na} non-numeric values converted to NaN.")
            # show non-numeric samples (for debugging)
            sample_invalid = df[col][df[col].isna()].dropna().head()
            logger.debug(f"[CLEAN] Example invalid values in '{col}': {sample_invalid.values}")

    logger.info(f"[CLEAN] Cleaned dataframe with {len(df)} rows")
    return df

def clean_single_csv(filename):
    """Read, clean one CSV file and return cleaned DataFrame."""
    try:
        input_file_path = os.path.join(input_dir, filename)
        logger.info(f"input_path: {input_file_path}")
        output_file_path = os.path.join(output_dir, filename)
        logger.info(f"output_path: {output_file_path}")

        df_raw = pd.read_csv(input_file_path, low_memory=False)
        df = df_raw.dropna(how='all').copy()

        for col in df.select_dtypes(include=['object']):
            df[col] = df[col].apply(lambda x: x.strip() if isinstance(x, str) else x)

        df = clean_data(df)

        logger.info(f"[CLEAN] Successfully cleaned: {filename}")
        save_clean_data_to_csv(df, output_file_path)
        return df
    except Exception as e:
        logger.info(f"Failed to clean {filename}: {e}")

def load_latest_csv(download_dir):
    """
    Loads the latest CSV file named in the latest_download.txt from the download directory.
    """
    try:
        latest_filename = get_latest_csv_filename()
    except FileNotFoundError:
        logger.info("Error: latest_download.txt not found.")
        return None

    csv_path = os.path.join(download_dir, latest_filename)
    if not os.path.exists(csv_path):
        logger.info(f"Error: CSV file not found: {csv_path}")
        return None

    return pd.read_csv(csv_path)

def save_clean_data_to_csv(df: pd.DataFrame, output_path: str):
    """Save cleaned DataFrame to CSV."""
    df.to_csv(output_path, index=False)
    logger.info(f"Saved cleaned data to: {output_path}")

def clean_all_csv_files(input_dir, output_dir):
    """
    Clean all CSV files in the directory (drop empty rows, strip spaces),
    then save cleaned CSVs to output_dir.
    """
    csv_files = glob.glob(os.path.join(input_dir, "*.csv"))
    if not csv_files:
        logger.info(f"No CSV files found in {input_dir}")
        return

    os.makedirs(output_dir, exist_ok=True)

    for file_path in csv_files:
        cleaned_df = clean_single_csv(file_path)
        if cleaned_df is not None and not cleaned_df.empty:
            filename = os.path.basename(file_path)
            output_path = os.path.join(output_dir, filename)
            save_clean_data_to_csv(cleaned_df, output_path)
            logger.info(f"Cleaned and saved: {output_path}")
        else:
            logger.info(f"Skipping file (empty or failed to clean): {file_path}")

# -------------------------
# EXAMPLE USAGE (for reference, NOT executed)
#     import sys
# examples to use
# csv_files = list_csv_files(input_dir)
# output_path = os.path.join(RAW_DATA_DIR, "csv_file_list.txt")
# write_file_list(csv_files, output_path)
#
# clean_all_csv_files(RAW_DATA_DIR, PROCESSED_DATA_DIR)
# file_path = sys.argv[1]
# file_pass = './data/raw/USW00094728.csv' # example filename
# clean_single_csv(file_path)
#
# Command line examples:
# py -m app.data_processing.data_cleaner data/raw/US1CALA0090.csv
# py -m app.data_processing.data_cleaner USC00282644.csv
# -------------------------