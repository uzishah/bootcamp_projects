# FMR Report ETL Pipeline

## Project Overview
This project is an automated ETL (Extract, Transform, Load) pipeline that processes Fund Manager Reports (FMR) from Pakistani mutual funds. It uses AWS Textract for PDF data extraction and Snowflake for data warehousing.

## Architecture

The pipeline consists of the following components:

1. **AWS S3**: Source storage for FMR PDF files
2. **AWS Textract**: OCR and table extraction from PDFs
3. **AWS Lambda**: Serverless compute for ETL logic
4. **AWS Secrets Manager**: Secure credential storage
5. **Snowflake**: Data warehouse for structured storage

## Features

- ✅ Automated PDF processing from S3
- ✅ Table extraction using AWS Textract
- ✅ Top Holdings data parsing
- ✅ Multi-company support with dynamic table creation
- ✅ Monthly data tracking
- ✅ Secure credential management
- ✅ Error handling and logging

## Project Structure

```
FMR_REPORT_ETL/
├── local code/
│   ├── extract_equity.py              # Main ETL script
│   ├── Complete-FMR-Conventional-February-2026.pdf
│   ├── FMR-February-2026 meezan.pdf
│   ├── UBL-FMR-Feb-2026.pdf
│   ├── FMR_Merged.pdf
│   └── fmr_feb-26-conventional.pdf
├── layer_packages.zip                 # Lambda layer dependencies
└── README.md                          # This file
```

## Data Flow

1. **Extract**: PDFs stored in S3 bucket organized by year/month
2. **Transform**: 
   - Textract extracts tables from PDFs
   - Script identifies "Top Holdings" tables
   - Parses holding names and percentage of assets
3. **Load**: 
   - Creates company-specific tables in Snowflake
   - Inserts data with month tracking
   - Maintains historical records

## Configuration

### S3 Structure
```
s3-fmr-us/
└── 2026/
    └── feb/
        ├── company1/
        │   └── report.pdf
        ├── company2/
        │   └── report.pdf
        └── ...
```

### Snowflake Schema
```sql
Database: FMR_DB
Schema: FMR_SCHEMA
Tables: {company_name} (dynamically created)
  - holding_name VARCHAR
  - percentage_of_assets VARCHAR
  - month VARCHAR
```

## Prerequisites

- AWS Account with configured services
- Snowflake account
- Python 3.9+
- Required Python packages:
  - boto3
  - snowflake-connector-python

## Setup Instructions

### 1. AWS Secrets Manager
Store Snowflake credentials:
```json
{
  "username": "your_username",
  "password": "your_password",
  "account": "your_account",
  "warehouse": "your_warehouse"
}
```

### 2. S3 Bucket Configuration
```bash
aws s3 mb s3://s3-fmr-us --region us-east-1
```

### 3. Lambda Layer
Package dependencies:
```bash
pip install snowflake-connector-python -t python/
zip -r layer_packages.zip python/
```

### 4. Lambda Function
- Runtime: Python 3.9
- Timeout: 900 seconds (15 minutes)
- Memory: 1024 MB
- Environment Variables: None (uses Secrets Manager)

## IAM Permissions Required

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::s3-fmr-us",
        "arn:aws:s3:::s3-fmr-us/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "textract:StartDocumentAnalysis",
        "textract:GetDocumentAnalysis"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue"
      ],
      "Resource": "arn:aws:secretsmanager:*:*:secret:FMR_SECRETS-*"
    }
  ]
}
```

## How It Works

### 1. PDF Discovery
- Lists all folders in S3 prefix (2026/feb/)
- Each folder name = company name
- Finds PDF files within each folder

### 2. Textract Processing
- Starts async document analysis job
- Waits for completion (polls every 10 seconds)
- Retrieves all blocks from all pages

### 3. Table Identification
- Searches for tables with "holding" or "asset" in headers
- Identifies name and percentage columns
- Extracts data rows (skips header)

### 4. Data Loading
- Creates table if not exists (company-specific)
- Inserts holdings with month tracking
- Commits transaction

## Sample Output

```
🚀 Job started...
📂 3 PDFs found for 2026-02

📄 Processing: meezan → 2026/feb/meezan/FMR-February-2026.pdf
⏳ Textract Job Started: abc123...
✅ meezan → 15 rows inserted for 2026-02

📄 Processing: ubl → 2026/feb/ubl/UBL-FMR-Feb-2026.pdf
⏳ Textract Job Started: def456...
✅ ubl → 12 rows inserted for 2026-02

✅ All PDFs processed successfully!
```

## Cost Estimation

- **Textract**: ~$1.50 per 1,000 pages
- **Lambda**: ~$0.20 per 1 million requests
- **S3**: ~$0.023 per GB
- **Snowflake**: Based on compute usage

**Estimated Monthly Cost**: $5-10 for ~50 PDFs

## Troubleshooting

### Common Issues

1. **Textract Job Failed**: Check PDF quality and format
2. **No Tables Found**: Verify table structure in PDF
3. **Snowflake Connection Error**: Check credentials in Secrets Manager
4. **Timeout Error**: Increase Lambda timeout for large PDFs

## Future Enhancements

- [ ] Add data validation and quality checks
- [ ] Implement SNS notifications for job status
- [ ] Add support for other table types (performance, allocation)
- [ ] Create data visualization dashboard
- [ ] Add incremental loading (avoid duplicates)

## Security Notes

⚠️ **Important**:
- Never commit credentials to version control
- Use AWS Secrets Manager for all sensitive data
- Enable S3 bucket encryption
- Implement least privilege IAM policies

---

**Last Updated**: 2026
**Version**: 1.0
