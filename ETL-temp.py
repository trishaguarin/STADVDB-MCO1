import pandas as pd
import numpy as np
from sqlalchemy import create_engine
import mysql.connector
import os
import re
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ========== CONFIGURATION SECTION - EDIT YOUR PREFERENCES HERE ==========

# STAGE 1: SQL to CSV Conversion
sql_input_folder = './sql_files'           # Folder containing your SQL files
csv_output_folder = './converted_csv'      # Where converted CSVs will be saved

# STAGE 2: ETL Processing
process_converted_csv = True               # True = run ETL after conversion, False = only convert to CSV
csv_input_folder = './converted_csv'       # Folder with CSVs to process (usually same as csv_output_folder)

# Database Configuration
db_config = {
    'user': 'your_mysql_user',             # Your MySQL username
    'password': 'your_mysql_password',      # Your MySQL password
    'host': 'localhost',                    # 'localhost' or remote server IP
    'database': 'your_database',            # Your database name
    'port': 3306                            # MySQL port (default 3306)
}

# Processing Options
load_to_database = True                    # True = load to MySQL, False = save as files
final_output_folder = './final_output'     # Where to save final files (if not loading to database)

# CSV Reading Options (for Stage 2)
csv_delimiter = ','                        # Delimiter in CSV files: ',' or ';' or '\t' or '|'
csv_encoding = 'utf-8'                     # File encoding: 'utf-8', 'latin1', 'iso-8859-1', 'cp1252'

# ========== DATA FORMAT PREFERENCES - CUSTOMIZE YOUR DATA FORMATS HERE ==========

# Missing Value Handling
drop_na = True                             # True = remove rows with ANY missing values, False = keep and fill them
fill_na_numeric = None                     # What to fill numeric NAs with: None (keep as NaN), 0, -1, or any number
fill_na_string = ''                        # What to fill text NAs with: '' (empty), 'Unknown', 'N/A', etc.

# Date/Time Format Preferences
date_columns = ['date', 'created_at', 'updated_at', 'timestamp']  # List column names that contain dates
datetime_output_format = '%Y-%m-%d %H:%M:%S'   # Format for datetime columns
                                               # Examples:
                                               # '%Y-%m-%d %H:%M:%S' → 2024-03-15 14:30:00
                                               # '%m/%d/%Y %I:%M %p' → 03/15/2024 02:30 PM
                                               # '%d-%b-%Y %H:%M' → 15-Mar-2024 14:30

date_only_format = '%Y-%m-%d'                  # Format for date-only columns (no time)
                                               # Examples:
                                               # '%Y-%m-%d' → 2024-03-15
                                               # '%m/%d/%Y' → 03/15/2024
                                               # '%d/%m/%Y' → 15/03/2024

# Number Format Preferences
decimal_places = 2                         # Number of decimal places for float numbers (2 = 12.34)
round_numeric_columns = True               # True = round decimals, False = keep original precision

# Text Format Preferences
string_columns_to_upper = []               # Columns to convert to UPPERCASE: ['name', 'city', 'country']
string_columns_to_lower = []               # Columns to convert to lowercase: ['email', 'username']
string_columns_to_title = []               # Columns to convert to Title Case: ['full_name', 'address']
strip_whitespace = True                    # True = remove extra spaces from beginning/end of text

# Data Cleaning Options
remove_duplicates = True                   # True = remove duplicate rows
columns_to_drop = []                       # Columns to remove completely: ['temp_col', 'unused_field']

# Calculated Columns
calculate_total_price = True               # True = create 'total_price' from 'quantity' × 'unit_price' (if they exist)
additional_calculations = {
    # Add your own calculated columns here:
    # 'profit': lambda df: df['revenue'] - df['cost'],
    # 'full_name': lambda df: df['first_name'] + ' ' + df['last_name'],
    # 'age_group': lambda df: df['age'].apply(lambda x: 'Adult' if x >= 18 else 'Minor')
}

# ========== END DATA FORMAT PREFERENCES ==========

# Database Loading Options
if_exists = 'replace'                      # What to do if table exists: 'replace', 'append', 'fail'

# Output Options (when load_to_database = False)
output_format = 'csv'                      # Output file format: 'csv', 'excel', 'json', 'parquet'

# ========== END CONFIGURATION SECTION ==========


# ========== STAGE 1: SQL TO CSV CONVERSION ==========

def parse_sql_to_csv(sql_filepath, output_folder):
    """Convert SQL INSERT statements to CSV file"""
    logger.info(f"Converting SQL file: {sql_filepath}")
    
    try:
        with open(sql_filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract table name
        table_match = re.search(r'CREATE TABLE (?:IF NOT EXISTS )?`?(\w+)`?', content, re.IGNORECASE)
        table_name = table_match.group(1) if table_match else os.path.splitext(os.path.basename(sql_filepath))[0]
        
        # Extract column names from CREATE TABLE
        create_match = re.search(r'CREATE TABLE.*?\((.*?)\);', content, re.IGNORECASE | re.DOTALL)
        columns = []
        if create_match:
            col_definitions = create_match.group(1)
            # Extract column names
            col_pattern = r'`?(\w+)`?\s+(?:INT|VARCHAR|TEXT|DATE|DATETIME|DECIMAL|FLOAT|DOUBLE|BOOLEAN|TIMESTAMP|CHAR|BIGINT|SMALLINT|TINYINT)'
            columns = re.findall(col_pattern, col_definitions, re.IGNORECASE)
        
        # Extract INSERT statements
        insert_pattern = r"INSERT INTO.*?VALUES\s*\((.*?)\)(?:,|\;)"
        inserts = re.findall(insert_pattern, content, re.IGNORECASE | re.DOTALL)
        
        if not inserts:
            logger.warning(f"No INSERT statements found in {sql_filepath}")
            return None
        
        # Parse values
        data = []
        for insert in inserts:
            # Split by comma, but respect quoted strings
            values = re.findall(r"'(?:[^']|'')*'|[^,]+", insert)
            values = [v.strip().strip("'").replace("''", "'") for v in values]
            # Replace NULL with empty string
            values = ['' if v.upper() == 'NULL' else v for v in values]
            data.append(values)
        
        # Create DataFrame
        if columns and len(columns) == len(data[0]):
            df = pd.DataFrame(data, columns=columns)
        else:
            df = pd.DataFrame(data)
            logger.warning(f"Could not extract column names properly, using default column names")
        
        # Save to CSV
        os.makedirs(output_folder, exist_ok=True)
        csv_filename = f"{table_name}.csv"
        csv_path = os.path.join(output_folder, csv_filename)
        df.to_csv(csv_path, index=False)
        
        logger.info(f"✓ Converted {sql_filepath} → {csv_path} ({len(df)} rows, {len(df.columns)} columns)")
        
        return {
            'sql_file': sql_filepath,
            'csv_file': csv_path,
            'table_name': table_name,
            'rows': len(df),
            'columns': len(df.columns)
        }
        
    except Exception as e:
        logger.error(f"Error converting {sql_filepath}: {str(e)}")
        return None


def convert_all_sql_to_csv():
    """Convert all SQL files in folder to CSV"""
    if not os.path.exists(sql_input_folder):
        logger.error(f"SQL input folder not found: {sql_input_folder}")
        return []
    
    sql_files = [f for f in os.listdir(sql_input_folder) if f.endswith('.sql')]
    
    if not sql_files:
        logger.warning(f"No SQL files found in {sql_input_folder}")
        return []
    
    logger.info(f"\n{'='*60}")
    logger.info(f"STAGE 1: CONVERTING {len(sql_files)} SQL FILES TO CSV")
    logger.info(f"{'='*60}\n")
    
    results = []
    for sql_file in sql_files:
        sql_path = os.path.join(sql_input_folder, sql_file)
        result = parse_sql_to_csv(sql_path, csv_output_folder)
        if result:
            results.append(result)
    
    # Print summary
    logger.info(f"\n{'='*60}")
    logger.info("SQL TO CSV CONVERSION SUMMARY")
    logger.info(f"{'='*60}")
    logger.info(f"Total SQL files processed: {len(results)}/{len(sql_files)}")
    
    for result in results:
        logger.info(f"\n  ✓ {os.path.basename(result['sql_file'])}")
        logger.info(f"    → {os.path.basename(result['csv_file'])}")
        logger.info(f"    Table: {result['table_name']} | Rows: {result['rows']} | Columns: {result['columns']}")
    
    return results


# ========== STAGE 2: ETL PROCESSING ==========

def extract(file_path):
    """Extract data from CSV file"""
    logger.info(f"Extracting data from: {file_path}")
    
    try:
        df = pd.read_csv(file_path, sep=csv_delimiter, encoding=csv_encoding)
        logger.info(f"Successfully extracted {len(df)} rows and {len(df.columns)} columns")
        return df
    
    except Exception as e:
        logger.error(f"Error extracting data from {file_path}: {str(e)}")
        return None


def transform(df, filename=''):
    """Clean and transform the data"""
    if df is None or df.empty:
        logger.warning(f"Empty dataframe for {filename}, skipping transformation")
        return df
    
    logger.info(f"Transforming data for {filename}...")
    original_rows = len(df)
    
    # Strip whitespace from all string columns first
    if strip_whitespace:
        for col in df.select_dtypes(include=['object']).columns:
            df[col] = df[col].astype(str).str.strip()
            df[col] = df[col].replace('nan', np.nan)
    
    # Drop specified columns
    if columns_to_drop:
        df = df.drop(columns=columns_to_drop, errors='ignore')
        logger.info(f"Dropped columns: {columns_to_drop}")
    
    # Handle missing values
    if drop_na:
        df = df.dropna()
        logger.info(f"Dropped {original_rows - len(df)} rows with NA values")
    else:
        # Fill numeric NAs
        if fill_na_numeric is not None:
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            df[numeric_cols] = df[numeric_cols].fillna(fill_na_numeric)
        
        # Fill string NAs
        string_cols = df.select_dtypes(include=['object']).columns
        df[string_cols] = df[string_cols].fillna(fill_na_string)
    
    # Convert date columns to specified format
    for col in date_columns:
        if col in df.columns:
            try:
                df[col] = pd.to_datetime(df[col], errors='coerce')
                # Check if it has time component
                has_time = (df[col].dt.hour != 0).any() or (df[col].dt.minute != 0).any()
                if has_time:
                    df[col] = df[col].dt.strftime(datetime_output_format)
                else:
                    df[col] = df[col].dt.strftime(date_only_format)
                logger.info(f"Converted column '{col}' to datetime format")
            except Exception as e:
                logger.warning(f"Could not convert column '{col}' to datetime: {str(e)}")
    
    # String case conversions
    for col in string_columns_to_upper:
        if col in df.columns:
            df[col] = df[col].astype(str).str.upper()
            logger.info(f"Converted column '{col}' to UPPERCASE")
    
    for col in string_columns_to_lower:
        if col in df.columns:
            df[col] = df[col].astype(str).str.lower()
            logger.info(f"Converted column '{col}' to lowercase")
    
    for col in string_columns_to_title:
        if col in df.columns:
            df[col] = df[col].astype(str).str.title()
            logger.info(f"Converted column '{col}' to Title Case")
    
    # Round numeric columns
    if round_numeric_columns:
        for col in df.select_dtypes(include=[np.number]).columns:
            if df[col].dtype == 'float64':
                df[col] = df[col].round(decimal_places)
    
    # Calculate total_price if applicable
    if calculate_total_price:
        if 'quantity' in df.columns and 'unit_price' in df.columns:
            df['total_price'] = pd.to_numeric(df['quantity'], errors='coerce') * pd.to_numeric(df['unit_price'], errors='coerce')
            if round_numeric_columns:
                df['total_price'] = df['total_price'].round(decimal_places)
            logger.info("Calculated 'total_price' column")
    
    # Apply additional custom calculations
    for col_name, calculation_func in additional_calculations.items():
        try:
            df[col_name] = calculation_func(df)
            logger.info(f"Applied custom calculation for column '{col_name}'")
        except Exception as e:
            logger.error(f"Error applying calculation for '{col_name}': {str(e)}")
    
    # Remove duplicates
    if remove_duplicates:
        before = len(df)
        df = df.drop_duplicates()
        removed = before - len(df)
        if removed > 0:
            logger.info(f"Removed {removed} duplicate rows")
    
    logger.info(f"Transformation complete: {len(df)} rows remaining")
    return df


def load_to_database(df, table_name):
    """Load data into MySQL database"""
    logger.info(f"Loading data into MySQL table '{table_name}'...")
    
    try:
        # Create connection string using SQLAlchemy
        engine = create_engine(
            f"mysql+mysqlconnector://{db_config['user']}:{db_config['password']}@"
            f"{db_config['host']}:{db_config['port']}/{db_config['database']}"
        )
        
        # Load data to the MySQL table
        df.to_sql(name=table_name, con=engine, if_exists=if_exists, index=False)
        logger.info(f"✓ Successfully loaded {len(df)} rows into table '{table_name}'")
        
        return True
    
    except Exception as e:
        logger.error(f"✗ Error loading data to database: {str(e)}")
        return False


def save_to_file(df, original_filename):
    """Save processed data to file"""
    os.makedirs(final_output_folder, exist_ok=True)
    
    base_name = os.path.splitext(original_filename)[0]
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    try:
        if output_format == 'csv':
            output_path = os.path.join(final_output_folder, f"{base_name}_final_{timestamp}.csv")
            df.to_csv(output_path, index=False)
        
        elif output_format == 'excel':
            output_path = os.path.join(final_output_folder, f"{base_name}_final_{timestamp}.xlsx")
            df.to_excel(output_path, index=False, engine='openpyxl')
        
        elif output_format == 'json':
            output_path = os.path.join(final_output_folder, f"{base_name}_final_{timestamp}.json")
            df.to_json(output_path, orient='records', indent=2)
        
        elif output_format == 'parquet':
            output_path = os.path.join(final_output_folder, f"{base_name}_final_{timestamp}.parquet")
            df.to_parquet(output_path, index=False)
        
        logger.info(f"✓ Saved processed data to: {output_path}")
        return output_path
    
    except Exception as e:
        logger.error(f"✗ Error saving file: {str(e)}")
        return None


def load(df, table_name, filename=''):
    """Load data to destination (database or file)"""
    if load_to_database:
        return load_to_database(df, table_name)
    else:
        return save_to_file(df, filename)
        f"{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
            
        
        # Load data to the MySQL table
        df.to_sql(name=table_name, con=engine, if_exists=IF_EXISTS, index=False)
        logger.info(f"✓ Successfully loaded {len(df)} rows into table '{table_name}'")
        
    return True

def save_to_file(df, original_filename):
    """Save processed data to file"""
    os.makedirs(FINAL_OUTPUT_FOLDER, exist_ok=True)
    
    base_name = os.path.splitext(original_filename)[0]
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    try:
        if OUTPUT_FORMAT == 'csv':
            output_path = os.path.join(FINAL_OUTPUT_FOLDER, f"{base_name}_final_{timestamp}.csv")
            df.to_csv(output_path, index=False)
        
        elif OUTPUT_FORMAT == 'excel':
            output_path = os.path.join(FINAL_OUTPUT_FOLDER, f"{base_name}_final_{timestamp}.xlsx")
            df.to_excel(output_path, index=False, engine='openpyxl')
        
        elif OUTPUT_FORMAT == 'json':
            output_path = os.path.join(FINAL_OUTPUT_FOLDER, f"{base_name}_final_{timestamp}.json")
            df.to_json(output_path, orient='records', indent=2)
        
        elif OUTPUT_FORMAT == 'parquet':
            output_path = os.path.join(FINAL_OUTPUT_FOLDER, f"{base_name}_final_{timestamp}.parquet")
            df.to_parquet(output_path, index=False)
        
        logger.info(f"✓ Saved processed data to: {output_path}")
        return output_path
    
    except Exception as e:
        logger.error(f"✗ Error saving file: {str(e)}")
        return None


def load(df, table_name, filename=''):
    """Load data to destination (database or file)"""
    if LOAD_TO_DATABASE:
        return load_to_database(df, table_name)
    else:
        return save_to_file(df, filename)


def etl_single_file(csv_file_path):
    """Run ETL process for a single CSV file"""
    filename = os.path.basename(csv_file_path)
    table_name = os.path.splitext(filename)[0]
    
    logger.info(f"\n{'='*60}")
    logger.info(f"Processing: {filename}")
    logger.info(f"{'='*60}")
    
    # Extract
    df = extract(csv_file_path)
    if df is None:
        return None
    
    # Transform
    df = transform(df, filename=filename)
    if df is None or df.empty:
        logger.warning(f"No data to load for {filename}")
        return None
    
    # Load
    result = load(df, table_name, filename=filename)
    
    return {
        'file': filename,
        'table': table_name,
        'rows': len(df),
        'columns': len(df.columns),
        'success': result is not False
    }


def process_all_csv_files():
    """Run ETL process for all CSV files"""
    if not os.path.exists(CSV_INPUT_FOLDER):
        logger.error(f"CSV input folder not found: {CSV_INPUT_FOLDER}")
        return []
    
    csv_files = [f for f in os.listdir(CSV_INPUT_FOLDER) if f.endswith('.csv')]
    
    if not csv_files:
        logger.warning(f"No CSV files found in {CSV_INPUT_FOLDER}")
        return []
    
    logger.info(f"\n{'='*60}")
    logger.info(f"STAGE 2: PROCESSING {len(csv_files)} CSV FILES")
    logger.info(f"{'='*60}\n")
    
    results = []
    for csv_file in csv_files:
        csv_path = os.path.join(CSV_INPUT_FOLDER, csv_file)
        result = etl_single_file(csv_path)
        if result:
            results.append(result)
    
    # Print summary
    logger.info(f"\n{'='*60}")
    logger.info("ETL PROCESSING SUMMARY")
    logger.info(f"{'='*60}")
    
    for result in results:
        status = "✓ SUCCESS" if result['success'] else "✗ FAILED"
        logger.info(f"\n{status}")
        logger.info(f"  File: {result['file']}")
        logger.info(f"  Table: {result['table']}")
        logger.info(f"  Rows: {result['rows']}")
        logger.info(f"  Columns: {result['columns']}")
    
    logger.info(f"\nTotal processed: {len(results)}/{len(csv_files)} files")
    
    return results


# ========== MAIN EXECUTION ==========

def main():
    """Main execution flow"""
    logger.info("\n" + "="*60)
    logger.info("ETL PIPELINE STARTING")
    logger.info("="*60)
    logger.info(f"Destination: {'DATABASE' if LOAD_TO_DATABASE else 'FILE'}")
    
    # STAGE 1: Convert SQL to CSV
    conversion_results = convert_all_sql_to_csv()
    
    if not conversion_results:
        logger.warning("No SQL files were converted. Exiting.")
        return
    
    # STAGE 2: Process converted CSVs (if enabled)
    if PROCESS_CONVERTED_CSV:
        logger.info(f"\nCSV files are ready in: {CSV_OUTPUT_FOLDER}")
        logger.info("You can review/edit them before proceeding.\n")
        
        user_input = input("Do you want to proceed with ETL processing? (yes/no): ").strip().lower()
        
        if user_input in ['yes', 'y']:
            etl_results = process_all_csv_files()
        else:
            logger.info("\nETL processing skipped. CSV files are available for manual review.")
            logger.info(f"To process later, set PROCESS_CONVERTED_CSV = True and run again.")
    else:
        logger.info(f"\nConversion complete! CSV files saved to: {CSV_OUTPUT_FOLDER}")
        logger.info("Set PROCESS_CONVERTED_CSV = True to run ETL processing.")
    
    logger.info("\n" + "="*60)
    logger.info("PIPELINE COMPLETED")
    logger.info("="*60)


if __name__ == "__main__":
    main()