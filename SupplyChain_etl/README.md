# Supply Chain Management ETL Pipeline

A complete ETL (Extract, Transform, Load) pipeline that extracts supply chain data from Kaggle, transforms it, and loads it into Snowflake data warehouse for advanced analytics.

## 📋 Project Overview

This project implements an end-to-end data pipeline for supply chain management analytics. It downloads the DataCo Supply Chain dataset from Kaggle, performs data cleaning and transformation, and loads it into Snowflake for comprehensive analysis using SQL queries, stored procedures, views, streams, and automated tasks.

## ✨ Features

### ETL Pipeline (`main.py`)
- **Extract**: Automated download of supply chain dataset from Kaggle API
- **Transform**: Data cleaning and column name standardization
- **Load**: Efficient bulk loading into Snowflake using pandas integration
- Dynamic table creation based on DataFrame schema
- Data validation and verification

### Analytics & Insights (`supplychainETL.sql`)
- **Shipment Analysis**: Total quantity shipped per product category
- **Warehouse Efficiency**: Average shipping time and efficiency scores by shipping mode
- **Sales Performance**: Total shipment value per department/supplier
- **Product Rankings**: Top 5 products by shipment quantity
- **Revenue Distribution**: Shipment value distribution across categories
- **Year-over-Year Comparison**: Sales growth analysis by department

### Advanced Snowflake Features
- **Stored Procedure**: `UPDATE_SHIPMENT` - Update shipment status and delays
- **View**: `SHIPMENT_PERFORMANCE_VIEW` - Consolidated shipment performance metrics
- **Stream**: `SHIPMENT_STREAM` - Real-time change data capture
- **Task**: `SHIPMENT_HISTORY_TASK` - Automated history tracking (runs every minute)
- **History Table**: Tracks all shipment modifications with timestamps

## 🛠️ Technologies Used

- **Python 3.x**
- **Pandas** - Data manipulation and analysis
- **Snowflake Connector** - Database connectivity
- **Kaggle API** - Dataset download
- **Snowflake** - Cloud data warehouse
- **SQL** - Data analysis and transformations

## 📦 Prerequisites

1. **Python Libraries**:
   ```bash
   pip install pandas snowflake-connector-python kaggle
   ```

2. **Kaggle API Credentials**:
   - Create account on [Kaggle](https://www.kaggle.com/)
   - Generate API token from Account Settings
   - Note your username and API key

3. **Snowflake Account**:
   - Active Snowflake account
   - Warehouse, database, and schema access
   - User credentials

## ⚙️ Setup Instructions

### 1. Configure Kaggle Credentials
Edit `main.py` and add your credentials:
```python
os.environ['KAGGLE_USERNAME'] = 'your_username'
os.environ['KAGGLE_KEY'] = 'your_api_key'
```

### 2. Configure Snowflake Connection
Update Snowflake credentials in `main.py`:
```python
conn = snowflake.connector.connect(
    account   = 'your_account_identifier',
    user      = 'your_username',
    password  = 'your_password',
    warehouse = 'COMPUTE_WH',
    database  = 'SCM_ETL',
    schema    = 'SCM_SCHEMA'
)
```

### 3. Create Database and Schema
Run the initial setup commands from `supplychainETL.sql`:
```sql
CREATE DATABASE SCM_ETL;
CREATE SCHEMA SCM_ETL.SCM_SCHEMA;
USE SCHEMA SCM_ETL.SCM_SCHEMA;
```

## 🚀 Usage

### Run ETL Pipeline
```bash
python main.py
```

This will:
1. Download dataset from Kaggle
2. Load and clean the data
3. Create table in Snowflake
4. Load data into Snowflake
5. Verify the data load

### Run Analytics Queries
Execute queries from `supplychainETL.sql` in Snowflake to:
- Analyze shipment performance
- Track warehouse efficiency
- Monitor sales trends
- Generate business insights

### Enable Automated History Tracking
```sql
ALTER TASK SHIPMENT_HISTORY_TASK RESUME;
```

## 📁 Project Structure

```
SupplyChain_etl/
│
├── main.py                      # ETL pipeline script
├── supplychainETL.sql          # Analytics queries and Snowflake objects
├── supply_chain_data/          # Downloaded dataset directory
│   └── DataCoSupplyChainDataset.csv
└── README.md                   # Project documentation
```

## 📊 Data Schema

The pipeline creates a `RAW_SUPPLY_CHAIN` table with the following key columns:
- Order information (ORDER_ID, ORDER_STATUS, ORDER_DATE)
- Product details (PRODUCT_NAME, CATEGORY_NAME, DEPARTMENT_NAME)
- Shipping data (SHIPPING_MODE, DAYS_FOR_SHIPPING_REAL, DAYS_FOR_SHIPMENT_SCHEDULED)
- Financial metrics (SALES, ORDER_PROFIT_PER_ORDER, ORDER_ITEM_QUANTITY)

## 🔍 Key Insights Available

- Which product categories generate the most shipments?
- Which shipping modes are most efficient?
- What are the top-performing departments by revenue?
- How do sales trends change year-over-year?
- What is the distribution of order values across categories?

## 📝 Notes

- The ETL pipeline handles NaN values automatically
- Column names are standardized (uppercase, underscores, no special characters)
- The history tracking task runs every minute when enabled
- All timestamps are recorded in UTC

## 🤝 Contributing

Feel free to fork this project and submit pull requests for improvements.

## 📄 License

This project is for educational and analytical purposes.

---

**Dataset Source**: [DataCo Supply Chain Dataset on Kaggle](https://www.kaggle.com/datasets/evilspirit05/datasupplychain)
