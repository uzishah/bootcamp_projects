import pandas as pd
import pyodbc

# ── CREDENTIALS ────────────────────────────────────────
server   = "*****"
username = "**"
password = "***"
database = "*****"

# ── CONNECTION ──────────────────────────────────────────
conn = pyodbc.connect(
    f"DRIVER={{ODBC Driver 17 for SQL Server}};"
    f"SERVER={server};DATABASE={database};UID={username};PWD={password}",
    autocommit=True
)
cursor = conn.cursor()
print("✅ Connected!")

# ── CSV LOAD ────────────────────────────────────────────
df = pd.read_csv(
    r'D:\uzair shah\CDE\BOOTCAMP PROJECTS\RETAIL_DATASET_ETL\data\online_retail.csv',
    encoding='latin-1',
    dtype=str
)
print(f"✅ CSV Loaded: {len(df)} rows")

# ── CLEAN ───────────────────────────────────────────────
# CustomerID 17850.0 → 17850
df['CustomerID'] = df['CustomerID'].str.replace('.0', '', regex=False)

# Sab NaN → None
df = df.where(pd.notnull(df), None)
df = df.replace('nan', None)
df = df.replace('', None)

print("✅ Data cleaned!")

# ── TABLE ───────────────────────────────────────────────
cursor.execute("DROP TABLE IF EXISTS stg_online_retail")
cursor.execute("""
    CREATE TABLE stg_online_retail (
        InvoiceNo    NVARCHAR(20)  NULL,
        StockCode    NVARCHAR(20)  NULL,
        Description  NVARCHAR(255) NULL,
        Quantity     NVARCHAR(20)  NULL,
        InvoiceDate  NVARCHAR(30)  NULL,
        UnitPrice    NVARCHAR(20)  NULL,
        CustomerID   NVARCHAR(20)  NULL,
        Country      NVARCHAR(100) NULL
    )
""")
print("✅ Table created!")

# ── BATCH INSERT ────────────────────────────────────────
insert_query = "INSERT INTO stg_online_retail VALUES (?,?,?,?,?,?,?,?)"

rows = [tuple(row) for row in df.itertuples(index=False, name=None)]

cursor.fast_executemany = False
rows = [tuple(str(x) if x is not None else None for x in row) 
        for row in df.itertuples(index=False, name=None)]
cursor.executemany(insert_query, rows)
print(f"✅ {len(rows)} rows inserted!")

# ── VERIFY ──────────────────────────────────────────────
cursor.execute("SELECT COUNT(*) FROM stg_online_retail")
print(f"✅ Total in DB: {cursor.fetchone()[0]}")

conn.close()
print("✅ Done!")