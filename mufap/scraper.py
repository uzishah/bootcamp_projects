import requests
from bs4 import BeautifulSoup
import boto3
import json
from datetime import datetime

# === CONFIGURATION ===
BUCKET_NAME = "****"        # aapka S3 bucket
REGION_NAME = "us-east-1"           # bucket region
URL = "https://www.mufap.com.pk/Industry/IndustryStatDaily?tab=3"
FOLDER_NAME = "**"          # folder ke andar file save hogi

def lambda_handler(event, context):
    try:
        print(f"[{datetime.now()}] Starting scrape...")

    
        response = requests.get(URL)
        if response.status_code != 200:
            print(f"[{datetime.now()}] Failed to fetch page. Status code: {response.status_code}")
            return {"statusCode": response.status_code, "body": "Failed to fetch page"}

       
        soup = BeautifulSoup(response.text, "html.parser")
        table = soup.find("table")
        rows = table.find_all("tr")

        data = []
        for row in rows:
            cols = row.find_all("td")
            cols = [col.text.strip() for col in cols]
            if cols:
                data.append(cols)

    
        final_data = {
            "scraped_at": str(datetime.now()),
            "data": data
        }

       
        s3 = boto3.client("s3", region_name=REGION_NAME)
        file_name = f"{FOLDER_NAME}/mufap-data-{datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}.json"

        s3.put_object(
            Bucket=BUCKET_NAME,
            Key=file_name,
            Body=json.dumps(final_data)
        )

        print(f"[{datetime.now()}] Data scraped and uploaded to S3: {file_name}")

        return {
            "statusCode": 200,
            "body": f"Data scraped and uploaded to S3: {file_name}"
        }

    except Exception as e:
        print(f"[{datetime.now()}] Error: {str(e)}")
        return {
            "statusCode": 500,
            "body": f"Error: {str(e)}"
        }