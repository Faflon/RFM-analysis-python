# RFM Analytics Dashboard

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-1.39%2B-FF4B4B)
![SQL](https://img.shields.io/badge/Database-SQLite-lightgrey)

## Project Overview
This project is an Data Science application designed to analyze e-commerce sales data. It implements **RFM Analysis (Recency, Frequency, Monetary)** to segment customers into actionable groups (e.g., *Champions, Loyal Customers, At Risk*).

The solution includes a full **ETL Pipeline** that cleans raw data, stores it in a **SQL Database**, and visualizes insights via an interactive **Streamlit Dashboard**.

Data source: <https://www.kaggle.com/datasets/mashlyn/online-retail-ii-uci?resource=download>

## Business Problem & Solution
**Problem:** E-commerce businesses often struggle to identify their most valuable customers or recognize those at risk of churning. Raw transaction logs are difficult to interpret without aggregation.

**Solution:** A dashboard that translates transaction data into marketing intelligence:
* **Segmentation:** Automatically groups customers based on purchasing behavior (10-segment logic).
* **Whale Detection:** Identifies High-Net-Worth individuals (High Monetary Value) regardless of purchase frequency.
* **Returns Analysis:** Highlights customers with high return rates affecting net revenue.

## Tech Stack
* **Language:** Python 3.x
* **Data Processing:** Pandas, NumPy
* **Database:** SQLite, SQLAlchemy (ORM)
* **Visualization:** Plotly Express (Interactive Charts), Seaborn (Statistical Analysis)
* **Web Framework:** Streamlit (UI/UX)

## Project Structure
```text
rfm-analytics-project/
│
├── data/                     # Place 'online_retail_II.csv' here and generated SQLite database (sales.db)
│
├── src/
│   ├── data_cleaning.py      # Cleaning logic & returns handling
│   ├── database.py           # SQL read/write operations (SQLAlchemy)
│   └── rfm_functions.py      # RFM segmentation logic (10 segments)
│
├── app.py                    # Streamlit Dashboard entry point
├── db_handle_run.py          # ETL Script (Extract -> Transform -> Load)
├── requirements.txt          # Python dependencies
└── README.md                 # Project documentation
```
## How to Run

### 1. Prerequisites
Ensure you have Python installed (version 3.10 or higher recommended). Clone this repository and install dependencies:
```bash
git clone <your-repo-url>
cd rfm-analytics-project
pip install -r requirements.txt
```
### 2. Data Setup
Download the **Online Retail II** dataset (e.g., from Kaggle or UCI) and place the `.csv` file in the `data/raw/` folder.
*Note: Ensure the filename matches the one defined in `run_pipeline.py` (default: `online_retail_II.csv`).*

### 3. Run ETL Pipeline
Execute the pipeline script to clean data and populate the SQL database. This step creates the `transactions` and `returns` tables in SQLite.
```bash
python run_pipeline.py
```
### 4. Launch Dashboard
Start the Streamlit application:
```bash
streamlit run app.py
```
## RFM Segmentation

The project uses a detailed **10-segment logic** based on RFM scores (1-5 scale).

### Metrics Calculation
* **Recency (R):** Days since the last purchase.
* **Frequency (F):** Total number of unique orders.
* **Monetary (M):** Total Net Spend (*Gross Spend* - *Returns*).

For the purpose of this project, Quintile-based segmentation was utilized to distribute customers across segments (1-5 scale). This ensures a balanced distribution for visualization purposes regardless of the dataset's specific timeframe. In a real-world scenario in specific market, I would rather implement hard thresholds to reflect specific business cycles and product lifespan accurately.

### Customer Segments
Customers are assigned to one of the following segments based on R and F scores:
1.  **Champions:** Bought recently, buy often.
2.  **Loyal Customers:** Regular shoppers.
3.  **Potential Loyalists:** Recent shoppers with average frequency.
4.  **New Customers:** Bought most recently, but only once.
5.  **Promising:** Recent shoppers, low frequency.
6.  **Need Attention:** Average recency and frequency.
7.  **About To Sleep:** Below average recency and frequency.
8.  **Can't Lose Them:** Used to buy frequently but haven't returned for a long time.
9.  **At Risk:** Low recency, average frequency.
10. **Hibernating:** Last purchased long ago, low frequency.

*Additionally, a separate **"Value Tier"** (High/Mid/Low) is calculated purely based on Monetary value to identify "Whales" regardless of their behavioral segment.*

## Key Features
* **SQL Integration:** Data is queried dynamically from a local SQLite database, simulating a production environment.
* **Interactive Filtering:** Filter by Segment or Monetary Value.
* **Returns Analysis:** Dedicated section to analyze lost revenue due to returns and identify serial returners.
* **Statistical Deep Dive:** Heatmaps for correlation and Log-Scale Boxplots for spending distribution.

---
*Author: Adam Jaworski*
