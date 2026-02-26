
--creating database
CREATE DATABASE OnlineRetailDW;
GO

USE OnlineRetailDW;
GO


----creating table-

DROP TABLE stg_online_retail;
GO

CREATE TABLE stg_online_retail (
    InvoiceNo    VARCHAR(20)     NULL,
    StockCode    VARCHAR(20)     NULL,
    Description  VARCHAR(255)    NULL,
    Quantity     VARCHAR(20)     NULL,  -- VARCHAR rakho abhi
    InvoiceDate  VARCHAR(30)     NULL,
    UnitPrice    VARCHAR(20)     NULL,  -- Yeh bhi VARCHAR
    CustomerID   VARCHAR(20)     NULL,
    Country      VARCHAR(100)    NULL
);
GO

---data loaded by script----
USE OnlineRetailDW;

SELECT COUNT(*) FROM stg_online_retail;

SELECT TOP 5 * FROM stg_online_retail;



----
-- 1. Kitne NULL hain har column mein?
SELECT 
    SUM(CASE WHEN InvoiceNo   IS NULL THEN 1 ELSE 0 END) AS InvoiceNo_Nulls,
    SUM(CASE WHEN StockCode   IS NULL THEN 1 ELSE 0 END) AS StockCode_Nulls,
    SUM(CASE WHEN Description IS NULL THEN 1 ELSE 0 END) AS Description_Nulls,
    SUM(CASE WHEN Quantity    IS NULL THEN 1 ELSE 0 END) AS Quantity_Nulls,
    SUM(CASE WHEN UnitPrice   IS NULL THEN 1 ELSE 0 END) AS UnitPrice_Nulls,
    SUM(CASE WHEN CustomerID  IS NULL THEN 1 ELSE 0 END) AS CustomerID_Nulls,
    SUM(CASE WHEN Country     IS NULL THEN 1 ELSE 0 END) AS Country_Nulls
FROM stg_online_retail;

-- 2. Kitne duplicates hain?
SELECT InvoiceNo, StockCode, COUNT(*) AS cnt
FROM stg_online_retail
GROUP BY InvoiceNo, StockCode
HAVING COUNT(*) > 1
ORDER BY cnt DESC;

-- 3. Negative quantities hain?
SELECT COUNT(*) AS Negative_Quantity
FROM stg_online_retail
WHERE TRY_CAST(Quantity AS INT) < 0;


-- Cleaned staging table
SELECT DISTINCT
    InvoiceNo,
    StockCode,
    Description,
    TRY_CAST(Quantity   AS INT)          AS Quantity,
    TRY_CAST(InvoiceDate AS DATETIME)    AS InvoiceDate,
    TRY_CAST(UnitPrice  AS DECIMAL(10,2)) AS UnitPrice,
    CustomerID,
    Country
INTO stg_online_retail_cleaned
FROM stg_online_retail
WHERE 
    TRY_CAST(Quantity AS INT) > 0    -- Negatives hataao
    AND CustomerID IS NOT NULL        -- No customer = useless row
    AND Description IS NOT NULL;      -- No description = useless row

-- Verify
SELECT COUNT(*) AS Clean_Rows FROM stg_online_retail_cleaned;


---------------------- data warehousing---------------------
-- Drop karo
DROP TABLE IF EXISTS dim_customers;
DROP TABLE IF EXISTS dim_products;
GO



-- dim_products — sirf ek description rakho per StockCode
SELECT 
    StockCode,
    MAX(Description) AS Description
INTO dim_products
FROM stg_online_retail_cleaned
WHERE StockCode IS NOT NULL
GROUP BY StockCode;
GO

SELECT COUNT(*) AS Customers FROM dim_customers;
SELECT COUNT(*) AS Products  FROM dim_products;



DROP TABLE IF EXISTS fact_sales;
DROP TABLE IF EXISTS dim_date;
GO

-- 3. dim_date
SELECT DISTINCT
    CAST(InvoiceDate AS DATE)          AS DateID,
    YEAR(InvoiceDate)                  AS Year,
    MONTH(InvoiceDate)                 AS Month,
    DATEPART(QUARTER, InvoiceDate)     AS Quarter,
    DATENAME(MONTH, InvoiceDate)       AS MonthName,
    DAY(InvoiceDate)                   AS Day
INTO dim_date
FROM stg_online_retail_cleaned;
GO
----------------------------------------
DROP TABLE IF EXISTS fact_sales;
DROP TABLE IF EXISTS dim_customers;
GO

-- Country remove kar do
SELECT DISTINCT CustomerID
INTO dim_customers
FROM stg_online_retail_cleaned
WHERE CustomerID IS NOT NULL 
AND CustomerID != 'nan';
GO

-- fact_sales mein Country rakhenge
SELECT DISTINCT
    ROW_NUMBER() OVER (ORDER BY s.InvoiceNo) AS SaleID,
    s.InvoiceNo,
    s.CustomerID,
    s.StockCode,
    s.Country,
    CAST(s.InvoiceDate AS DATE)              AS DateID,
    CAST(s.Quantity    AS INT)               AS Quantity,
    CAST(s.UnitPrice   AS DECIMAL(10,2))     AS UnitPrice,
    CAST(s.Quantity AS INT) * 
    CAST(s.UnitPrice AS DECIMAL(10,2))       AS TotalAmount
INTO fact_sales
FROM stg_online_retail_cleaned s
WHERE s.CustomerID != 'nan';
GO

SELECT 'dim_customers' AS TableName, COUNT(*) AS Rows FROM dim_customers UNION ALL
SELECT 'fact_sales',                 COUNT(*)           FROM fact_sales;


-- Verify
SELECT 'dim_customers' AS TableName, COUNT(*) AS Rows FROM dim_customers UNION ALL
SELECT 'dim_products',               COUNT(*)           FROM dim_products  UNION ALL
SELECT 'dim_date',                   COUNT(*)           FROM dim_date       UNION ALL
SELECT 'fact_sales',                 COUNT(*)           FROM fact_sales;

=======================
ALTER TABLE dim_customers 
ALTER COLUMN CustomerID NVARCHAR(20) NOT NULL;
GO

ALTER TABLE fact_sales 
ALTER COLUMN SaleID BIGINT NOT NULL;
GO

ALTER TABLE dim_customers 
ADD CONSTRAINT PK_Customers PRIMARY KEY (CustomerID);
GO

ALTER TABLE dim_products  
ADD CONSTRAINT PK_Products PRIMARY KEY (StockCode);
GO

ALTER TABLE dim_date      
ADD CONSTRAINT PK_Date PRIMARY KEY (DateID);
GO

ALTER TABLE fact_sales    
ADD CONSTRAINT PK_Sales PRIMARY KEY (SaleID);
GO

SELECT 'Primary Keys Created!' AS Status;

======================


ALTER TABLE fact_sales
ADD CONSTRAINT FK_Sales_Customers 
FOREIGN KEY (CustomerID) REFERENCES dim_customers(CustomerID);
GO

ALTER TABLE fact_sales
ADD CONSTRAINT FK_Sales_Products 
FOREIGN KEY (StockCode) REFERENCES dim_products(StockCode);
GO

ALTER TABLE fact_sales
ADD CONSTRAINT FK_Sales_Date 
FOREIGN KEY (DateID) REFERENCES dim_date(DateID);
GO

SELECT 'Foreign Keys Created!' AS Status;



----------------
SELECT 
    f.Country,
    COUNT(DISTINCT f.InvoiceNo)    AS Total_Orders,
    SUM(f.TotalAmount)             AS Total_Revenue
FROM fact_sales f
GROUP BY f.Country
ORDER BY Total_Revenue DESC;
-----------------------




-- Frequently queried columns pe indexes
CREATE INDEX IX_Sales_CustomerID 
ON fact_sales(CustomerID);
GO

CREATE INDEX IX_Sales_StockCode  
ON fact_sales(StockCode);
GO

CREATE INDEX IX_Sales_DateID     
ON fact_sales(DateID);
GO

CREATE INDEX IX_Sales_Country    
ON fact_sales(Country);
GO

SELECT 'Indexes Created!' AS Status;


------------------- data quality--------
-- Quality Log Table
CREATE TABLE etl_quality_log (
    LogID        INT IDENTITY(1,1) PRIMARY KEY,
    RunDate      DATETIME DEFAULT GETDATE(),
    TableName    NVARCHAR(100),
    TotalRows    INT,
    NullCount    INT,
    DuplicateCount INT,
    Status       NVARCHAR(20)
);
GO

-- Abhi ka quality check insert karo
INSERT INTO etl_quality_log 
    (TableName, TotalRows, NullCount, DuplicateCount, Status)
VALUES
    ('fact_sales',    392732, 0, 0, 'PASSED'),
    ('dim_customers', 4339,   0, 0, 'PASSED'),
    ('dim_products',  3829,   0, 0, 'PASSED'),
    ('dim_date',      305,    0, 0, 'PASSED');
GO

-- Verify
SELECT * FROM etl_quality_log;


------------------versioning----------

-- Version tracking table
CREATE TABLE etl_version_log (
    VersionID    INT IDENTITY(1,1) PRIMARY KEY,
    RunDate      DATETIME DEFAULT GETDATE(),
    VersionNo    NVARCHAR(10),
    TotalRows    INT,
    Description  NVARCHAR(255)
);
GO

-- Pehla version insert karo
INSERT INTO etl_version_log 
    (VersionNo, TotalRows, Description)
VALUES
    ('v1.0', 392732, 'Initial load — Online Retail Dataset');
GO

SELECT * FROM etl_version_log;



-- Metadata table
CREATE TABLE etl_metadata (
    MetaID       INT IDENTITY(1,1) PRIMARY KEY,
    TableName    NVARCHAR(100),
    SourceFile   NVARCHAR(255),
    LoadDate     DATETIME DEFAULT GETDATE(),
    TotalRows    INT,
    Columns      NVARCHAR(500),
    Description  NVARCHAR(500)
);
GO

INSERT INTO etl_metadata 
    (TableName, SourceFile, TotalRows, Columns, Description)
VALUES
    ('stg_online_retail',   'online_retail.csv', 541909, 
     'InvoiceNo,StockCode,Description,Quantity,InvoiceDate,UnitPrice,CustomerID,Country', 
     'Raw staging table'),
    ('fact_sales',          'online_retail.csv', 392732, 
     'SaleID,InvoiceNo,CustomerID,StockCode,Country,DateID,Quantity,UnitPrice,TotalAmount',    
     'Main fact table'),
    ('dim_customers',       'online_retail.csv', 4339,  
     'CustomerID',                               
     'Customer dimension'),
    ('dim_products',        'online_retail.csv', 3829,  
     'StockCode,Description',                    
     'Product dimension'),
    ('dim_date',            'online_retail.csv', 305,   
     'DateID,Year,Month,Quarter,MonthName,Day',  
     'Date dimension');
GO

SELECT * FROM etl_metadata;



---------performance

-- Top 5 Products by Revenue
SELECT TOP 5
    p.Description,
    SUM(f.TotalAmount) AS Revenue
FROM fact_sales f
JOIN dim_products p ON f.StockCode = p.StockCode
GROUP BY p.Description
ORDER BY Revenue DESC;
GO

-- 2. Monthly Revenue Trend
SELECT 
    d.Year,
    d.MonthName,
    SUM(f.TotalAmount) AS Monthly_Revenue
FROM fact_sales f
JOIN dim_date d ON f.DateID = d.DateID
GROUP BY d.Year, d.MonthName, d.Month
ORDER BY d.Year, d.Month;
GO

-- 3. Top 5 Countries by Orders
SELECT TOP 5
    f.Country,
    COUNT(DISTINCT f.InvoiceNo) AS Total_Orders,
    SUM(f.TotalAmount)          AS Total_Revenue
FROM fact_sales f
GROUP BY f.Country
ORDER BY Total_Revenue DESC;
GO