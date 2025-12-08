import pandas as pd

def clean_data(df : pd.DataFrame) -> tuple[pd.DataFrame,pd.DataFrame,pd.DataFrame]:
    """
    Cleans data and splits it into sales transactions and customer return metrics.
    Returns:
        tuple: (sales_df, returns_metrics_df)
        - sales_df: DataFrame with only successful purchases (Quantity > 0).
        - returns_metrics_df: Aggregated stats per customer regarding their returns.
        - metadata_df: Information about raw data.
    """
    
    df = df.copy()
    # Variables for eda:
    raw_rows_count = df.shape[0]
    missing_ids_count = df['Customer ID'].isna().sum()
    # Droping rows where Customer ID is NaN
    # Customer segmentation won't work if you can't tell the difference between individual customers.
    df = df.dropna(subset=['Customer ID'])
    df['Customer ID'] = df['Customer ID'].astype(int).astype(str)

    # Type to date
    df['InvoiceDate'] = pd.to_datetime(df['InvoiceDate'])

    # Adding column for total amount spent by transaction
    df['TotalAmount'] = round(df['Quantity'] * df['Price'], 2)

    returns_rows_count = (df['Quantity'] < 0).sum()
    # Splitting into Sales and Returns 
    sales_df = df[df['Quantity'] > 0].copy()
    returns_df = df[df['Quantity'] < 0].copy()

    # Calculating return metrics per Customer
    # Taking absolute values for aggregation to simplify visualization later
    returns_df['AbsReturnAmount'] = returns_df['TotalAmount'].abs()
    
    returns_metrics_df = returns_df.groupby('Customer ID').agg(
        ReturnsCount=('Invoice', 'count'),            # How many return transactions for each customer
        TotalReturnedValue=('AbsReturnAmount', 'sum') # Total money returned for each customer
    ).reset_index()

    # Creating Metadata DataFrame (for the Dashboard Tab 1)
    valid_sales_count = sales_df.shape[0]
    
    metadata_data = {
        'metric': ['raw_rows', 'missing_ids', 'return_rows', 'valid_sales_rows'],
        'value': [raw_rows_count, missing_ids_count, returns_rows_count, valid_sales_count]
    }
    metadata_df = pd.DataFrame(metadata_data)

    return sales_df, returns_metrics_df, metadata_df