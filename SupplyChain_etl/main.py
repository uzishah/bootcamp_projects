import os
import pandas as pd
import snowflake.connector
from snowflake.connector.pandas_tools import write_pandas


# STEP 1: KAGGLE CREDENTIALS & DOWNLOAD

os.environ['KAGGLE_USERNAME'] = '****'   #apna Kaggle username daalo
os.environ['KAGGLE_KEY'] = '***'         # apni Kaggle API key daalo

import kaggle

print(" Downloading dataset from Kaggle...")
kaggle.api.dataset_download_files(
    'evilspirit05/datasupplychain',
    path='./supply_chain_data',
    unzip=True
)
print(" Dataset downloaded successfully!\n")


# STEP 2: LOAD CSV INTO PANDAS DATAFRAME

print(" Loading CSV files...")

# List all downloaded files
files = os.listdir('./supply_chain_data')
print(f"Files found: {files}\n")

# Load the main dataset (adjust filename if different)
df = pd.read_csv('./supply_chain_data/DataCoSupplyChainDataset.csv', encoding='latin-1')

print(f"✅ Data loaded! Shape: {df.shape}")
print(f"Columns: {list(df.columns)}\n")


# STEP 3: CLEAN COLUMN NAMES
# (Snowflake doesn't like spaces in column names)

print(" Cleaning column names...")
df.columns = (
    df.columns
    .str.strip()
    .str.upper()
    .str.replace(' ', '_')
    .str.replace(r'[^A-Z0-9_]', '', regex=True)
)
print(f"✅ Columns cleaned!\n")


# STEP 4: CONNECT TO SNOWFLAKE

print(" Connecting to Snowflake...")

conn = snowflake.connector.connect(
    account   = '**',   # Your account identifier
    user      = '**',           # Your username
    password  = '******',  # apna password daalo yahan
    warehouse = 'COMPUTE',
    database  = 'SCM_ETL',
    schema    = 'SCM_SCHEMA'
)

cursor = conn.cursor()
print(" Connected to Snowflake successfully!\n")

# STEP 5: CREATE TABLE IN SNOWFLAKE
# Activate warehouse explicitly
cursor.execute("USE WAREHOUSE COMPUTE_WH")
cursor.execute("USE DATABASE SCM_ETL")
cursor.execute("USE SCHEMA SCM_SCHEMA")


print(" Creating table in Snowflake...")

# Drop table if already exists (useful for re-runs)
cursor.execute("DROP TABLE IF EXISTS RAW_SUPPLY_CHAIN")

# Build CREATE TABLE statement dynamically from DataFrame columns
def get_snowflake_type(dtype):
    if 'int' in str(dtype):
        return 'NUMBER'
    elif 'float' in str(dtype):
        return 'FLOAT'
    else:
        return 'VARCHAR(500)'

col_definitions = ",\n  ".join(
    f'"{col}" {get_snowflake_type(df[col].dtype)}'
    for col in df.columns
)

create_table_sql = f"""
CREATE OR REPLACE TABLE RAW_SUPPLY_CHAIN (
  {col_definitions}
)
"""

cursor.execute(create_table_sql)
print("✅ Table created!\n")


# STEP 6: LOAD DATA INTO SNOWFLAKE
# ─────────────────────────────────────────

print(f"📤 Loading {len(df)} rows into Snowflake...")

# Handle NaN values
df = df.where(pd.notnull(df), None)

# Write DataFrame to Snowflake
success, num_chunks, num_rows, output = write_pandas(
    conn=conn,
    df=df,
    table_name='RAW_SUPPLY_CHAIN',
    database='SCM_ETL',
    schema='SCM_SCHEMA'
)

if success:
    print(f"✅ Data loaded successfully!")
    print(f"   Total rows loaded : {num_rows}")
    print(f"   Total chunks used : {num_chunks}\n")
else:
    print("❌ Something went wrong during loading!")


# STEP 7: VERIFY DATA IN SNOWFLAKE


print(" Verifying data in Snowflake...")
cursor.execute("SELECT COUNT(*) FROM RAW_SUPPLY_CHAIN")
count = cursor.fetchone()[0]
print(f" Total rows in Snowflake table: {count}\n")

# Preview first 5 rows
cursor.execute("SELECT * FROM RAW_SUPPLY_CHAIN LIMIT 5")
rows = cursor.fetchall()
print("📋 First 5 rows preview:")
for row in rows:
    print(row)

# ─────────────────────────────────────────
# CLOSE CONNECTION
# ─────────────────────────────────────────

cursor.close()
conn.close()
print("\n🎉 ETL Pipeline Complete! Data is now in Snowflake.")
print("   Go to Snowflake UI → SCM_ETL → SCM_SCHEMA → RAW_SUPPLY_CHAIN")