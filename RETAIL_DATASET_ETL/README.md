# 🛒 Retail Dataset ETL Pipeline

A complete ETL (Extract, Transform, Load) pipeline that processes online retail transaction data and builds a dimensional data warehouse using Python and SQL Server.

## 📋 Project Overview

This project demonstrates a production-grade ETL pipeline that:
- Extracts data from CSV files
- Transforms and cleanses raw data
- Loads data into a SQL Server data warehouse
- Implements star schema modeling
- Includes data quality checks and versioning

## 🏗️ Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         ETL PIPELINE ARCHITECTURE                    │
└─────────────────────────────────────────────────────────────────────┘

┌──────────────────┐
│   Source Data    │
│                  │
│ online_retail.csv│
│   (541K rows)    │
└────────┬─────────┘
         │
         │ Extract (Python + Pandas)
         ▼
┌──────────────────┐
│   main.py        │
│                  │
│ • Load CSV       │
│ • Clean Data     │
│ • Connect DB     │
└────────┬─────────┘
         │
         │ Load via pyodbc
         ▼
┌──────────────────────────────────────────────────────────────────┐
│                    SQL SERVER DATABASE                            │
│                      (OnlineRetailDW)                             │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌─────────────────────┐                                         │
│  │  STAGING LAYER      │                                         │
│  ├─────────────────────┤                                         │
│  │ stg_online_retail   │  ──Transform──►  stg_online_retail_cleaned│
│  │   (Raw Data)        │                      (Cleaned)          │
│  └─────────────────────┘                                         │
│                                                                   │
│           │                                                       │
│           │ Transform & Model (SQL)                              │
│           ▼                                                       │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │              STAR SCHEMA DATA WAREHOUSE                  │    │
│  ├─────────────────────────────────────────────────────────┤    │
│  │                                                           │    │
│  │   ┌──────────────┐      ┌──────────────┐                │    │
│  │   │dim_customers │      │ dim_products │                │    │
│  │   │              │      │              │                │    │
│  │   │ CustomerID   │      │  StockCode   │                │    │
│  │   └──────┬───────┘      └──────┬───────┘                │    │
│  │          │                     │                         │    │
│  │          │    ┌────────────────┴────────────┐           │    │
│  │          │    │                              │           │    │
│  │          └───►│      fact_sales              │◄──────┐   │    │
│  │               │                              │       │   │    │
│  │               │ • SaleID                     │       │   │    │
│  │               │ • InvoiceNo                  │       │   │    │
│  │               │ • CustomerID (FK)            │       │   │    │
│  │               │ • StockCode (FK)             │       │   │    │
│  │               │ • DateID (FK)                │       │   │    │
│  │               │ • Country                    │       │   │    │
│  │               │ • Quantity                   │       │   │    │
│  │               │ • UnitPrice                  │       │   │    │
│  │               │ • TotalAmount                │       │   │    │
│  │               │                              │       │   │    │
│  │               └──────────────────────────────┘       │   │    │
│  │                              │                       │   │    │
│  │                              ▼                       │   │    │
│  │                      ┌──────────────┐               │   │    │
│  │                      │  dim_date    │───────────────┘   │    │
│  │                      │              │                   │    │
│  │                      │   DateID     │                   │    │
│  │                      │   Year       │                   │    │
│  │                      │   Month      │                   │    │
│  │                      │   Quarter    │                   │    │
│  │                      └──────────────┘                   │    │
│  │                                                          │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │              DATA QUALITY & METADATA                     │    │
│  ├─────────────────────────────────────────────────────────┤    │
│  │ • etl_quality_log    (Quality checks)                   │    │
│  │ • etl_version_log    (Version tracking)                 │    │
│  │ • etl_metadata       (Pipeline metadata)                │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
         │
         │ Query & Analyze
         ▼
┌──────────────────┐
│   BI Tools /     │
│   Analytics      │
└──────────────────┘
```

## 🛠️ Technologies Used

- **Python 3.x**
  - `pandas` - Data manipulation and CSV processing
  - `pyodbc` - SQL Server database connectivity

- **SQL Server**
  - Database: OnlineRetailDW
  - ODBC Driver 17 for SQL Server

- **Data Modeling**
  - Star Schema Design
  - Dimensional Modeling

## 📊 Database Schema

### Fact Table
- **fact_sales** (392,732 rows)
  - Primary Key: SaleID
  - Foreign Keys: CustomerID, StockCode, DateID
  - Measures: Quantity, UnitPrice, TotalAmount

### Dimension Tables
- **dim_customers** (4,339 customers)
- **dim_products** (3,829 products)
- **dim_date** (305 unique dates)

### Metadata Tables
- **etl_quality_log** - Data quality validation results
- **etl_version_log** - ETL version tracking
- **etl_metadata** - Pipeline metadata and lineage

## 🚀 Setup Instructions

### Prerequisites
```bash
pip install pandas pyodbc
```

### Database Configuration
1. Update credentials in `main.py`:
```python
server   = "your_server"
username = "your_username"
password = "your_password"
database = "OnlineRetailDW"
```

2. Ensure SQL Server is running and accessible
3. Install ODBC Driver 17 for SQL Server

### Running the Pipeline

1. **Extract & Load (Python)**
```bash
python main.py
```

2. **Transform & Model (SQL)**
```sql
-- Run SQLQuery1.sql in SQL Server Management Studio
-- This creates the data warehouse schema
```

## 📈 Data Flow

1. **Extract**: Load CSV file (541,909 rows) using pandas
2. **Clean**: Remove nulls, handle data types, clean CustomerID format
3. **Stage**: Load into `stg_online_retail` table
4. **Transform**: Create `stg_online_retail_cleaned` with:
   - Removed negative quantities
   - Filtered null CustomerIDs and Descriptions
   - Cast data types appropriately
5. **Model**: Build star schema with fact and dimension tables
6. **Validate**: Run data quality checks
7. **Index**: Create indexes for query optimization

## ✨ Features

### Data Quality
- NULL value detection and handling
- Duplicate record identification
- Negative quantity filtering
- Data type validation

### Performance Optimization
- Indexed columns: CustomerID, StockCode, DateID, Country
- Batch insert operations
- Primary and foreign key constraints

### Metadata Management
- Quality log tracking
- Version control
- Pipeline metadata documentation

### Analytics Queries
- Top products by revenue
- Monthly revenue trends
- Country-wise sales analysis
- Customer purchase patterns

## 📁 Project Structure

```
RETAIL_DATASET_ETL/
├── data/
│   └── online_retail.csv          # Source data
├── main.py                        # Python ETL script
├── SQLQuery1.sql                  # SQL transformations
├── Screenshot 2026-02-26 130815.png  # Reference screenshot
└── README.md                      # This file
```

## 📊 Sample Analytics

### Top 5 Countries by Revenue
```sql
SELECT TOP 5
    f.Country,
    COUNT(DISTINCT f.InvoiceNo) AS Total_Orders,
    SUM(f.TotalAmount) AS Total_Revenue
FROM fact_sales f
GROUP BY f.Country
ORDER BY Total_Revenue DESC;
```

### Monthly Revenue Trend
```sql
SELECT
    d.Year,
    d.MonthName,
    SUM(f.TotalAmount) AS Monthly_Revenue
FROM fact_sales f
JOIN dim_date d ON f.DateID = d.DateID
GROUP BY d.Year, d.MonthName, d.Month
ORDER BY d.Year, d.Month;
```

## 🎯 Key Metrics

- **Total Transactions**: 392,732
- **Unique Customers**: 4,339
- **Unique Products**: 3,829
- **Date Range**: 305 unique dates
- **Data Quality**: 100% (all quality checks passed)

## 📝 Notes

- The pipeline uses `autocommit=True` for immediate transaction commits
- CustomerID format is cleaned (removes `.0` suffix)
- All NULL values are properly handled
- Star schema enables efficient analytical queries

## 🤝 Contributing

Feel free to fork this project and submit pull requests for improvements.

## 📄 License

This project is open source and available for educational purposes.

---

**Built with ❤️ for Data Engineering Bootcamp**
