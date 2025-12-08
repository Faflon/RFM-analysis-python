import pandas as pd
import os
from sqlalchemy import create_engine, text

def save_to_db(df: pd.DataFrame, db_path: str, table_name: str):
    """
    Saves a DataFrame into a SQLite database using SQLAlchemy engine.
    
    Args:
        df (pd.DataFrame): The data to save.
        db_path (str): The file path to the .db file.
        table_name (str): The name of the SQL table.
    """

    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    # Creating SQLAlchemy Engine
    engine = create_engine(f'sqlite:///{db_path}')
    
    # Writing data to SQL using the engine
    df.to_sql(table_name, con=engine, if_exists='replace', index=False, chunksize=1000)
    
    print(f"Data successfully saved to table '{table_name}' in {db_path}")

def load_data_from_db(db_path: str, query: str) -> pd.DataFrame:
    """
    Executes a SQL query using SQLAlchemy engine and returns a Pandas DataFrame.
    """
    
    engine = create_engine(f'sqlite:///{db_path}')
    with engine.connect() as connection:
        df = pd.read_sql(text(query), connection)
        
    return df