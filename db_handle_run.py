import pandas as pd
import os
from src.data_cleaning import clean_data
from src.database import save_to_db

# Configuration Constants
RAW_DATA_PATH = 'data/online_retail_II.csv'
DB_PATH = 'data/sales.db'

def main():
    print(f"Loading raw data from {RAW_DATA_PATH}")
    if not os.path.exists(RAW_DATA_PATH):
        print(f"ERROR: File not found at {RAW_DATA_PATH}")
        return
    df_raw = pd.read_csv(RAW_DATA_PATH)  
    print(f"Raw data loaded.")

    # transformation
    # Now clean_data returns 3 dataframes, including the metadata
    print("Running cleaning logic and metadata calculation...")
    sales_df, returns_metrics_df, metadata_df = clean_data(df_raw)
    
    print("Transformation complete.")
    print(f"Saving data to SQLite database at {DB_PATH}")
    save_to_db(sales_df, DB_PATH, table_name="transactions")
    save_to_db(returns_metrics_df, DB_PATH, table_name="returns")
    save_to_db(metadata_df, DB_PATH, table_name="etl_metadata")
    
    print("ETL Pipeline Finished Successfully")

if __name__ == "__main__":
    main()