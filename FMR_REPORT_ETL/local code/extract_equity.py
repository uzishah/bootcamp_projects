import boto3
import json
import time
from datetime import datetime
import snowflake.connector

# ─── CLIENTS ───────────────────────────────────────────
s3_client        = boto3.client('s3')
textract_client  = boto3.client('textract')
secrets_client   = boto3.client('secretsmanager')

# ─── CONFIG ────────────────────────────────────────────
BUCKET_NAME  = 's3-fmr-us'
PREFIX       = '2026/feb/'
SECRET_NAME  = 'FMR_SECRETS'

# ─── SNOWFLAKE CREDENTIALS ─────────────────────────────
def get_snowflake_creds():
    secret = secrets_client.get_secret_value(SecretId=SECRET_NAME)
    return json.loads(secret['SecretString'])

# ─── SNOWFLAKE CONNECTION ──────────────────────────────
def get_snowflake_conn(creds):
    return snowflake.connector.connect(
        user      = creds['username'],
        password  = creds['password'],
        account   = creds['account'],
        warehouse = creds['warehouse'],
        database  = 'FMR_DB',
        schema    = 'FMR_SCHEMA'
    )

# ─── S3 SE COMPANY FOLDERS AUR PDFS LO ────────────────
def get_pdf_files():
    pdf_files = []
    response  = s3_client.list_objects_v2(Bucket=BUCKET_NAME, Prefix=PREFIX, Delimiter='/')
    
    for prefix in response.get('CommonPrefixes', []):
        folder       = prefix['Prefix']
        company_name = folder.split('/')[-2]  # folder name = company name
        
        # Is folder ke andar PDF dhundo
        folder_response = s3_client.list_objects_v2(Bucket=BUCKET_NAME, Prefix=folder)
        for obj in folder_response.get('Contents', []):
            if obj['Key'].endswith('.pdf'):
                pdf_files.append({
                    'company' : company_name,
                    'key'     : obj['Key']
                })
    
    return pdf_files

# ─── TEXTRACT JOB START KARO ───────────────────────────
def start_textract_job(bucket, key):
    response = textract_client.start_document_analysis(
        DocumentLocation={
            'S3Object': {'Bucket': bucket, 'Name': key}
        },
        FeatureTypes=['TABLES']
    )
    return response['JobId']

# ─── TEXTRACT JOB COMPLETE HONE KA WAIT KARO ──────────
def wait_for_job(job_id):
    while True:
        response = textract_client.get_document_analysis(JobId=job_id)
        status   = response['JobStatus']
        
        if status == 'SUCCEEDED':
            return response
        elif status == 'FAILED':
            raise Exception(f"Textract job failed: {job_id}")
        
        print(f"Job {job_id} still processing... waiting 10 seconds")
        time.sleep(10)

# ─── SAARE PAGES KE BLOCKS LO ─────────────────────────
def get_all_blocks(job_id):
    blocks   = []
    response = textract_client.get_document_analysis(JobId=job_id)
    blocks.extend(response['Blocks'])
    
    # Multiple pages ke liye pagination
    while 'NextToken' in response:
        response = textract_client.get_document_analysis(
            JobId     = job_id,
            NextToken = response['NextToken']
        )
        blocks.extend(response['Blocks'])
    
    return blocks

# ─── CELL KA TEXT NIKALO ──────────────────────────────
def get_cell_text(cell, block_map):
    text = ""
    for rel in cell.get('Relationships', []):
        if rel['Type'] == 'CHILD':
            for word_id in rel['Ids']:
                word = block_map.get(word_id)
                if word and word['BlockType'] in ['WORD', 'SELECTION_ELEMENT']:
                    text += word.get('Text', '') + " "
    return text.strip()

# ─── TOP HOLDINGS TABLE FILTER KARO ──────────────────
def extract_top_holdings(blocks):
    block_map = {b['Id']: b for b in blocks}
    
    for block in blocks:
        if block['BlockType'] != 'TABLE':
            continue
        
        # Table ki cells nikalo
        cells = {}
        for rel in block.get('Relationships', []):
            if rel['Type'] == 'CHILD':
                for cell_id in rel['Ids']:
                    cell = block_map.get(cell_id)
                    if cell and cell['BlockType'] == 'CELL':
                        row = cell['RowIndex']
                        col = cell['ColumnIndex']
                        cells[(row, col)] = get_cell_text(cell, block_map)
        
        if not cells:
            continue
        
        # Header row check karo — Top Holdings table hai?
        header_texts = [v.lower() for k, v in cells.items() if k[0] == 1]
        header_str   = ' '.join(header_texts)
        
        if 'holding' not in header_str and 'asset' not in header_str:
            continue
        
        # Sahi columns dhundo
        name_col    = None
        percent_col = None
        
        max_col = max(k[1] for k in cells.keys())
        for col in range(1, max_col + 1):
            header = cells.get((1, col), '').lower()
            if any(w in header for w in ['name', 'holding', 'company', 'scrip']):
                name_col    = col
            if any(w in header for w in ['%', 'asset', 'percent']):
                percent_col = col
        
        if not name_col or not percent_col:
            continue
        
        # Data rows nikalo (header skip karo)
        max_row  = max(k[0] for k in cells.keys())
        holdings = []
        
        for row in range(2, max_row + 1):
            name    = cells.get((row, name_col), '').strip()
            percent = cells.get((row, percent_col), '').strip()
            
            if name and percent:
                holdings.append({
                    'holding_name'        : name,
                    'percentage_of_assets': percent
                })
        
        if holdings:
            return holdings
    
    return []

# ─── MONTH S3 PATH SE NIKALO ──────────────────────────
def get_month_from_prefix(prefix):
    # '2026/feb/' → '2026-02'
    parts      = prefix.strip('/').split('/')
    year       = parts[0]
    month_str  = parts[1]
    month_map  = {
        'jan':'01','feb':'02','mar':'03','apr':'04',
        'may':'05','jun':'06','jul':'07','aug':'08',
        'sep':'09','oct':'10','nov':'11','dec':'12'
    }
    month_num  = month_map.get(month_str.lower(), '01')
    return f"{year}-{month_num}"

# ─── SNOWFLAKE MEIN TABLE BANAO AUR DATA INSERT KARO ──
def load_to_snowflake(conn, company_name, holdings, month):
    cursor     = conn.cursor()
    table_name = company_name.lower()
    
    # Table nahi hai toh banao
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS FMR_DB.FMR_SCHEMA.{table_name} (
            holding_name         VARCHAR,
            percentage_of_assets VARCHAR,
            month                VARCHAR
        )
    """)
    
    # Data insert karo
    for row in holdings:
        cursor.execute(f"""
            INSERT INTO FMR_DB.FMR_SCHEMA.{table_name}
            (holding_name, percentage_of_assets, month)
            VALUES (%s, %s, %s)
        """, (row['holding_name'], row['percentage_of_assets'], month))
    
    conn.commit()
    cursor.close()
    print(f"✅ {company_name} → {len(holdings)} rows inserted for {month}")

# ─── MAIN ─────────────────────────────────────────────
def main():
    print("🚀 Job started...")
    
    creds  = get_snowflake_creds()
    conn   = get_snowflake_conn(creds)
    month  = get_month_from_prefix(PREFIX)
    pdfs   = get_pdf_files()
    
    print(f"📂 {len(pdfs)} PDFs found for {month}")
    
    for pdf in pdfs:
        print(f"\n📄 Processing: {pdf['company']} → {pdf['key']}")
        
        job_id   = start_textract_job(BUCKET_NAME, pdf['key'])
        print(f"⏳ Textract Job Started: {job_id}")
        
        wait_for_job(job_id)
        blocks   = get_all_blocks(job_id)
        holdings = extract_top_holdings(blocks)
        
        if holdings:
            load_to_snowflake(conn, pdf['company'], holdings, month)
        else:
            print(f"⚠️ No Top Holdings table found in {pdf['company']}")
    
    conn.close()
    print("\n✅ All PDFs processed successfully!")

main()