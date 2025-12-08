import pandas as pd
import datetime as dt

def calculate_rfm_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculates raw Recency, Frequency, and Monetary values for each customer.
    """
    # Setting a reference date
    # If we used the real "today" (2025), 
    # every customer would have a "Recency" (last purchase) of 5,000 days. That makes no sense.
    snapshot_date = df['InvoiceDate'].max() + dt.timedelta(days=1)
    
    # calculating metrics
    rfm = df.groupby('Customer ID').agg({
        'InvoiceDate': lambda x: (snapshot_date - x.max()).days, # Recency: Days since last date
        'Invoice': 'nunique',                                    # Frequency: Count unique invoices
        'TotalAmount': 'sum'                                     # Monetary: Sum of money spent
    })
    
    rfm.rename(columns={
        'InvoiceDate': 'Recency',
        'Invoice': 'Frequency',
        'TotalAmount': 'Monetary'
    }, inplace=True)
    
    return rfm

def score_rfm(rfm_df: pd.DataFrame) -> pd.DataFrame:
    """
    Assigns scores from 1(bad) to 5(good) to Recency, Frequency, and Monetary.
    """

    # RECENCY: Lower is better (bought recently) - ex., Top 20% gets 5 points
    rfm_df['R_Score'] = pd.qcut(rfm_df['Recency'], q=5, labels=[5, 4, 3, 2, 1])
    
    # FREQUENCY: Higher is better.
    # .rank(method='first') was used to handle ties (many customers bought only once)
    rfm_df['F_Score'] = pd.qcut(rfm_df['Frequency'].rank(method='first'), q=5, labels=[1, 2, 3, 4, 5])
    
    # MONETARY: Higher is better.
    rfm_df['M_Score'] = pd.qcut(rfm_df['Monetary'], q=5, labels=[1, 2, 3, 4, 5])
    
    # Creating RFM string
    rfm_df['RFM_Score_Group'] = rfm_df['R_Score'].astype(str) + \
                                rfm_df['F_Score'].astype(str) + \
                                rfm_df['M_Score'].astype(str)                        
    return rfm_df

def assign_segments(rfm_df: pd.DataFrame) -> pd.DataFrame:
    """
    Creates two separate segmentations:
    1. Segment (Lifecycle based on R & F) - 10 Custom Segments
    2. Value_Segment (Financial based on M)
    """
    def get_lifecycle_segment(row):
        r, f = int(row['R_Score']), int(row['F_Score'])
        
        # 1. Champions: Bought recently (5), buy often (5)
        if r >= 5 and f >= 5:
            return 'Champions'
            
        # 2. Loyal Customers: Recent (3+) and frequent (4+)
        elif r >= 3 and f >= 4:
            return 'Loyal Customers'
            
        # 3. Potential Loyalists: Recent (4+), average freq (2-3)
        elif r >= 4 and f >= 2:
            return 'Potential Loyalists'
            
        # 4. New Customers: Very recent (5), low freq (1)
        elif r >= 5 and f == 1:
            return 'New Customers'
            
        # 5. Promising: Recent (4), low freq (1)
        elif r >= 4 and f == 1:
            return 'Promising'
            
        # 6. Need Attention: Average recency (3), average freq (3)
        elif r >= 3 and f >= 3:
            return 'Need Attention'
            
        # 7. About To Sleep: Average recency (3), low freq (1-2)
        elif r >= 3 and f <= 2:
            return 'About To Sleep'
            
        # 8. Can't Lose Them: Old recency (<=2), very high freq (4+)
        # These are former VIPs who stopped buying.
        elif r <= 2 and f >= 4:
            return "Can't Lose Them"
            
        # 9. At Risk: Old recency (<=2), average freq (2-3)
        elif r <= 2 and f >= 2:
            return 'At Risk'
            
        # 10. Hibernating: Everything else (Old recency, low freq)
        else:
            return 'Hibernating'

    def get_value_segment(row):
        m = int(row['M_Score'])
        if m == 5: return 'High Value'
        if m >= 3: return 'Mid Value'
        return 'Low Value'

    rfm_df['Segment'] = rfm_df.apply(get_lifecycle_segment, axis=1)
    rfm_df['Value_Segment'] = rfm_df.apply(get_value_segment, axis=1)
    
    return rfm_df
def run_rfm_analysis(df: pd.DataFrame) -> pd.DataFrame:
    """
    Main wrapper function to run the full analysis pipeline.
    """
    rfm = calculate_rfm_metrics(df)
    rfm = score_rfm(rfm)
    rfm = assign_segments(rfm)
    
    # Reset index to make Customer ID a normal column
    return rfm.reset_index()