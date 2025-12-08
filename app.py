import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from src.database import load_data_from_db
from src.rfm_functions import run_rfm_analysis

st.set_page_config(
    page_title="RFM Analytics Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# helper function for formatting large numbers (e.g. 1.2M instead of 1,200,000)
def format_currency(value):
    if value >= 1_000_000:
        return f"${value / 1_000_000:.2f}M"
    elif value >= 1_000:
        return f"${value / 1_000:.1f}K"
    else:
        return f"${value:,.0f}"

# ensuring consistent colors across all charts for each segment
SEGMENT_COLORS = {
    "Champions": "#006400",           # Dark Green
    "Loyal Customers": "#228B22",     # Forest Green
    "Potential Loyalists": "#32CD32", # Lime Green
    "New Customers": "#7FFFD4",       # Aquamarine
    "Promising": "#FFD700",           # Gold
    "Need Attention": "#FFA500",      # Orange
    "About To Sleep": "#FF8C00",      # Dark Orange
    "At Risk": "#CD5C5C",             # Indian Red
    "Can't Lose Them": "#B22222",     # Firebrick
    "Hibernating": "#808080",         # Grey
    "Lost": "#2F4F4F"                 # Dark Slate Grey
}

### Data loading:
#cache to boost performence
@st.cache_data
def get_main_data():
    """
    Loads cleaned transactions and returns data from SQL.
    Runs the RFM analysis pipeline and merges results.
    """
    db_path = 'data/sales.db'
    
    #loading transactions
    query = "SELECT * FROM transactions"
    df_trans = load_data_from_db(db_path, query)
    df_trans['InvoiceDate'] = pd.to_datetime(df_trans['InvoiceDate'])
    
    #RFM Analysis
    rfm_data = run_rfm_analysis(df_trans)
    
    #loading returns
    query_ret = "SELECT * FROM returns"
    df_ret = load_data_from_db(db_path, query_ret)
    
    #mearging sales with returns
    #left join because not every customer has returned items
    rfm_final = rfm_data.merge(df_ret, on='Customer ID', how='left')
    
    #filling NaNs for customers with no returns
    rfm_final['ReturnsCount'] = rfm_final['ReturnsCount'].fillna(0)
    rfm_final['TotalReturnedValue'] = rfm_final['TotalReturnedValue'].fillna(0)
    
    #calculating Net Monetary Value (Gross Sales - Returns)
    rfm_final['Net_Monetary'] = rfm_final['Monetary'] - rfm_final['TotalReturnedValue']
    
    return rfm_final, df_trans

@st.cache_data
def get_etl_metadata():
    """
    Loads ETL metrics (row counts, missing values) from the database.
    Used for the Data Quality tab.
    """
    db_path = 'data/sales.db'
    query = "SELECT * FROM etl_metadata"
    df_meta = load_data_from_db(db_path, query)
    #converting to dictionary for easy lookup: {'metric_name': value}
    return dict(zip(df_meta['metric'], df_meta['value']))


#executing data loading
try:
    df_rfm, df_clean_transactions = get_main_data()
    etl_meta = get_etl_metadata()
except Exception as e:
    st.error(f"Error loading data. Please ensure 'db_handle_run.py' has been executed. Details: {e}")
    st.stop()

### SIDEBAR
st.sidebar.title("Filter Options")
st.sidebar.info("Note: Filters apply to Tabs 2, 3, and 4. Tab 1 & Tab 2 (Distribution) show full data.")

#define the logical order for segments (Best -> Worst)
ordered_segments = [
    "Champions", "Loyal Customers", "Potential Loyalists", 
    "New Customers", "Promising", "Need Attention", 
    "About To Sleep", "Can't Lose Them", "At Risk", "Hibernating"
]

#filter A: Segment Selection
available_segments = df_rfm['Segment'].unique()
#sorting available segments based on logical order for tree plot
sorted_available = [seg for seg in ordered_segments if seg in available_segments]

st.sidebar.subheader("Select Customer Segments")
selected_segments = st.sidebar.pills(
    "Choose segments",
    options=sorted_available,
    selection_mode="multi",
    default=sorted_available,
    label_visibility="collapsed"
)

#safety check for empty selection
if not selected_segments:
    st.sidebar.warning("Please select at least one segment.")
    selected_segments = []

#filter B: Monetary Value Tier
st.sidebar.subheader("Monetary Value Filter")
tier_options = ['Low Value', 'Mid Value', 'High Value']
selected_tier_range = st.sidebar.select_slider(
    "Select Value Range",
    options=tier_options,
    value=('Low Value', 'High Value')
)

#handlding the slider range selection
start_idx = tier_options.index(selected_tier_range[0])
end_idx = tier_options.index(selected_tier_range[1])
selected_values = tier_options[start_idx : end_idx + 1]

# CREATE FILTERED DATASET (Used for Business Views)
filtered_df = df_rfm[
    (df_rfm['Segment'].isin(selected_segments)) &
    (df_rfm['Value_Segment'].isin(selected_values))
]

### MAIN DASHBOARD
st.title("📊 Customer Segmentation Dashboard")

# Create 4 Tabs
tab1, tab2, tab3, tab4 = st.tabs([
    "🗃️ Data Quality & ETL", 
    "📊 RFM Segmentation", 
    "↩️ Returns Analysis", 
    "🔬 Statistical Plots"
])

### TAB 1: DATA QUALITY & ETL #ETL as Extract, Transform, Load

with tab1:
    st.header("Data Quality")
    
    # 1. raw vs processed metrics
    #using data fetched from 'etl_metadata' table, avoiding heavy recalc
    if etl_meta:
        c1, c2, c3 = st.columns(3)
        raw_rows = etl_meta.get('raw_rows', 0)
        valid_rows = etl_meta.get('valid_sales_rows', 0)
        
        c1.metric("Raw Rows (Input CSV)", f"{raw_rows:,}")
        c2.metric("Valid Sales (Output SQL)", f"{valid_rows:,}")
        c3.metric("Retention Rate", f"{(valid_rows/raw_rows)*100:.1f}%")
        
        st.divider()
        
        # 2. waretfall chart (Data Transformation Logic)
        st.subheader("ETL Transformation Logic")
        st.caption("Visualizing data reduction during the cleaning process.")
        
        missing = etl_meta.get('missing_ids', 0)
        returns = etl_meta.get('return_rows', 0)
        
        fig_waterfall = go.Figure(go.Waterfall(
            name = "Data Flow",
            orientation = "v",
            measure = ["absolute", "relative", "relative", "total"],
            x = ["Raw CSV", "Missing IDs", "Returns (Separated)", "Clean Sales"],
            textposition = "outside",
            text = [f"{raw_rows/1000:.0f}k", f"-{missing/1000:.0f}k", f"-{returns/1000:.0f}k", f"{valid_rows/1000:.0f}k"],
            y = [raw_rows, -missing, -returns, valid_rows],
            connector = {"line":{"color":"rgb(63, 63, 63)"}},
        ))
        fig_waterfall.update_layout(title="Data Volume Waterfall", height=350)
        st.plotly_chart(fig_waterfall, use_container_width=True)
    
    # 3. eda
    st.divider()
    st.subheader("EDA on clean transactions)")
    st.caption("Analyze the distribution of key variables in the processed dataset.")
    
    eda_col = st.selectbox("Select Variable to Inspect", ['TotalAmount', 'Quantity', 'Price', 'InvoiceDate'])
    
    col_plot, col_stats = st.columns([3, 1])
    with col_plot:
        #optimization for performance if dataset is huge
        plot_data = df_clean_transactions
        if len(plot_data) > 20000:
            plot_data = plot_data.sample(20000)
            st.caption("Displaying random sample of 20k rows for performance.")
            
        #histogram with Log Y Scale
        fig_hist = px.histogram(
            plot_data, 
            x=eda_col, 
            title=f"Distribution of {eda_col}", 
            template="plotly_white",
            color_discrete_sequence=['#3b82f6'],
            log_y=True
        )
        st.plotly_chart(fig_hist, use_container_width=True)
        
        #descriptions
        st.markdown("> The log-scale distribution reveals 'long-tail' pattern common in retail. The vast majority of transactions are small, but the minority of high-value outliers significantly drives the total revenue.")
    
    with col_stats:
        st.markdown("**Descriptive Statistics**")
        desc = df_clean_transactions[eda_col].describe()
        st.dataframe(desc, use_container_width=True)

### TAB 2: RFM SEGMENTATION
with tab2:
    #RFM DISTRIBUTION
    st.header("RFM Population Distribution")
    st.caption("Exploratory analysis of the derived RFM metrics before segmentation.")
    
    rfm_var = st.selectbox("Select RFM Metric", ['Recency', 'Frequency', 'Monetary', 'Net_Monetary'])
    
    col_rfm_plot, col_rfm_stats = st.columns([3, 1])
    
    with col_rfm_plot:
        fig_rfm_dist = px.histogram(
            df_rfm, 
            x=rfm_var, 
            title=f"Distribution of {rfm_var}",
            template="plotly_white",
            color_discrete_sequence=['#8A2BE2'], #distinct color
            log_y=True
        )
        st.plotly_chart(fig_rfm_dist, use_container_width=True)
        
        st.markdown("> Most customers make only one purchase, creating a heavily skewed distribution. This confirms the Pareto Principle (80/20 rule), suggesting that a small percentage of repeat buyers generates the bulk of the store's engagement. Some of the people had contrubuted negative net monetary value, what can be an error at the data or some specific store policy.")
        
    with col_rfm_stats:
        st.markdown(f"**Stats: {rfm_var}**")
        st.dataframe(df_rfm[rfm_var].describe(), use_container_width=True)
        
    st.divider()

    # BUSINESS OVERVIEW
    st.header("Business Segmentation Overview")
    
    # KPI Metrics
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Selected Customers", f"{filtered_df.shape[0]:,}")
    c2.metric("Avg Recency", f"{filtered_df['Recency'].mean():.0f} days")
    c3.metric("Avg Frequency", f"{filtered_df['Frequency'].mean():.1f} orders")
    c4.metric("Net Revenue", format_currency(filtered_df['Net_Monetary'].sum()))
    
    st.divider()
    
    # A. Scatter Plot
    st.subheader("Customer Matrix (Recency vs Frequency)")
    st.caption("Bubble size represents **Positive Net Spend**.")
    
    scatter_df = filtered_df[filtered_df['Net_Monetary'] > 0]
    
    if not scatter_df.empty:
        fig_scatter = px.scatter(
            scatter_df,
            x="Recency",
            y="Frequency",
            color="Segment",
            size="Net_Monetary",
            hover_name="Customer ID",
            log_y=True,
            size_max=40,
            color_discrete_map=SEGMENT_COLORS, 
            template="plotly_dark",
            height=500,
            category_orders={"Segment": ordered_segments}
        )
        fig_scatter.update_traces(marker=dict(sizemin=4))
        st.plotly_chart(fig_scatter, use_container_width=True)
        
        # INSIGHT (Markdown styled as quote)
        st.markdown("""
        > * **Top-Left (Champions & Loyal):** Frequent and recent buyers. **Strategy:** Upsell & Loyalty Rewards.
        > * **Bottom-Left (New & Promising):** Recent buyers with low frequency. **Strategy:** Onboarding & Relationship building.
        > * **Top-Right (At Risk & Can't Lose):** Used to buy frequently but stopped (High Recency). **Strategy:** Urgent Win-Back campaigns.
        > * **Bottom-Right (Hibernating):** Low frequency and haven't bought in a long time. **Strategy:** Minimal spending / Ignore.
        """)
    else:
        st.warning("No data available for Scatter Plot (Try selecting different filters).")
        
    # B. Comparison Charts
    col_tree, col_rev = st.columns(2)
    
    with col_tree:
        st.subheader("Population Share")
        if not filtered_df.empty:
            treemap_data = filtered_df['Segment'].value_counts().reset_index()
            treemap_data.columns = ['Segment', 'Count']
            
            #calculating percentage
            total_count = treemap_data['Count'].sum()
            treemap_data['Percentage'] = treemap_data['Count'] / total_count
            
            #sorting for consistency
            treemap_data['Segment'] = pd.Categorical(treemap_data['Segment'], categories=ordered_segments, ordered=True)
            treemap_data = treemap_data.sort_values('Segment')

            fig_tree = px.treemap(
                treemap_data,
                path=['Segment'],
                values='Count',
                color='Segment',
                color_discrete_map=SEGMENT_COLORS,
                template="plotly_dark"
            )
            fig_tree.update_traces(
                textinfo="label+value+percent entry",
                texttemplate="%{label}<br>%{customdata[0]:.1%}",
                customdata=treemap_data[['Percentage']]
            )
            fig_tree.update_layout(margin=dict(t=0, l=0, r=0, b=0))
            st.plotly_chart(fig_tree, use_container_width=True)
            
            st.markdown("> While 'Hibernating' and 'New Customers' often make up the largest volume of the population, they typically contribute disproportionately less to the bottom line.")

    with col_rev:
        st.subheader("Revenue Share")
        if not filtered_df.empty:
            rev_data = filtered_df.groupby('Segment')['Net_Monetary'].sum().reset_index()
            
            fig_rev = px.bar(
                rev_data,
                x='Segment',
                y='Net_Monetary',
                color='Segment',
                color_discrete_map=SEGMENT_COLORS,
                template="plotly_dark",
                category_orders={"Segment": ordered_segments}
            )
            fig_rev.update_layout(showlegend=False, xaxis_title=None)
            st.plotly_chart(fig_rev, use_container_width=True)



### TAB 3: RETURNS ANALYSIS
with tab3:
    st.header("Returns & Refunds Impact")
    st.caption("Analysis of customers who returned items.")
    
    returns_df = filtered_df[filtered_df['TotalReturnedValue'] > 0].copy()
    
    if not returns_df.empty:
        r1, r2 = st.columns([1, 2])
        
        with r1:
            total_ret = returns_df['TotalReturnedValue'].sum()
            st.metric("Total Refunded", format_currency(total_ret), delta="Lost Revenue", delta_color="inverse")
            st.metric("Returners Count", f"{returns_df.shape[0]:,}")
            st.metric("Avg Refund per Returner", f"${returns_df['TotalReturnedValue'].mean():.0f}")
            
        with r2:
            fig_ret = px.scatter(
                returns_df,
                x="TotalReturnedValue",
                y="ReturnsCount",
                color="Segment",
                size="TotalReturnedValue",
                hover_name="Customer ID",
                title="Top Returners: Value vs Count",
                template="plotly_dark",
                color_discrete_map=SEGMENT_COLORS,
                log_x=True,
                log_y=True 
            )
            fig_ret.update_traces(marker=dict(sizemin=4))
            st.plotly_chart(fig_ret, use_container_width=True)
            
            st.markdown("> This chart helps distinguish between 'serial returners' (high count, low value) and one-time high-value refunds. Customers in the top-right corner negatively impact profit margins the most and may require a stricter return policy or dedicated customer service intervention (keep in mind plot is log scaled).")
            
        st.subheader("Top 10 Serial Returners")
        st.dataframe(
            returns_df[['Customer ID', 'Segment', 'ReturnsCount', 'TotalReturnedValue']]
            .sort_values('TotalReturnedValue', ascending=False)
            .head(10),
            use_container_width=True
        )
    else:
        st.info("No returns found for the selected segments.")



### TAB 4: STATISTICAL PLOTS

with tab4:
    st.header("Statistical Plots")
    st.caption("Couple more of the insights using Seaborn & Matplotlib.")
    
    positive_df = filtered_df[filtered_df['Net_Monetary'] > 0]
    
    # ROW 1
    s1, s2 = st.columns(2)
    
    with s1:
        st.subheader("Correlation Heatmap")
        st.caption("Lower triangle only.")
        corr_cols = ['Recency', 'Frequency', 'Net_Monetary', 'ReturnsCount']
        corr_matrix = filtered_df[corr_cols].corr()
        mask = np.triu(np.ones_like(corr_matrix, dtype=bool))
        
        fig_sns1, ax1 = plt.subplots(figsize=(6, 5))
        sns.heatmap(
            corr_matrix, 
            mask=mask, 
            annot=True, 
            cmap='mako', 
            fmt=".2f", 
            linewidths=0.5, 
            ax=ax1
        )
        st.pyplot(fig_sns1)
        
    with s2:
        st.subheader("Mean vs Median Spend")
        st.caption("Gap indicates outliers (Whales).")
        
        agg_data = positive_df.groupby('Segment')['Net_Monetary'].agg(['mean', 'median']).reset_index()
        melted_data = agg_data.melt(id_vars='Segment', var_name='Metric', value_name='Value')
        
        fig_sns2, ax2 = plt.subplots(figsize=(8, 5))
        sns.barplot(
            data=melted_data, 
            x='Segment', 
            y='Value', 
            hue='Metric',
            palette={'mean': '#4c72b0', 'median': '#55a868'},
            order=ordered_segments, 
            ax=ax2
        )
        ax2.set_yscale("log")
        plt.xticks(rotation=45, ha='right')
        sns.despine()
        st.pyplot(fig_sns2)
        
        st.markdown("> A large gap between Mean and Median indicates a distribution skewed by high-spending 'Whales'. If the Mean is significantly higher than the Median in a segment (e.g., Champions), it suggests that even within top tiers, there are hyper-valuable outliers driving the average up.")
        

    st.divider()

    st.subheader("Detailed Distribution of Net Spend")
    st.caption("Boxplot showing the spread of spending behavior.")
    
    fig_sns3, ax3 = plt.subplots(figsize=(12, 5))
    sns.boxplot(
        data=positive_df,
        x='Segment',
        y='Net_Monetary',
        palette=SEGMENT_COLORS,
        order=ordered_segments,
        ax=ax3
    )
    ax3.set_yscale("log")
    plt.xticks(rotation=45, ha='right')
    plt.ylabel("Net Monetary ($)")
    sns.despine()
    st.pyplot(fig_sns3)
    
    st.markdown("> The boxplot exposes the variability of spend within each segment. Taller boxes indicate inconsistent spending behavior, while shorter boxes suggest a homogenous group. Segments with many outliers above the upper whisker represent opportunities for up-selling.")