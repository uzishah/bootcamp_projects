from playwright.sync_api import sync_playwright
import pandas as pd
import time
from io import StringIO

def scrape_kasb():
    url = "https://kasb.com/dividend-stocks/"
    print(f"Loading URL: {url}")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        # Add basic user-agent just in case the site has basic security filters
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            print("Waiting for widgets and data to render...")
            
            # Wait 5 seconds instead of strictly looking for an HTML <table> element 
            # because the website might use divs or iframes for its layout.
            page.wait_for_timeout(5000)
            
            # Basic scrolling in case elements are lazy-loaded
            for _ in range(3):
                page.keyboard.press("PageDown")
                time.sleep(1)
                
            html_content = page.content()
        except Exception as e:
            print(f"Error loading the page: {e}")
            browser.close()
            return
            
        browser.close()
        
    print("Parsing HTML extract...")
    try:
        # We wrap html_content in StringIO to prevent Pandas from throwing a DeprecationWarning
        tables = pd.read_html(StringIO(html_content))
        
        if not tables:
            print("No standard HTML tables found on the page.")
            with open("kasb_debug.html", "w", encoding="utf-8") as file:
                file.write(html_content)
            print("Saved exactly what the browser saw to 'kasb_debug.html' so we can inspect it.")
            return
            
        # The true data table is almost always the one with the most rows
        df = max(tables, key=len)
        
        # Clean up columns by dropping fully empty columns if any exist
        df = df.dropna(axis=1, how='all')
        
        output_csv = "kasb_dividend_stocks.csv"
        df.to_csv(output_csv, index=False)
        
        print(f"Successfully scraped {len(df)} rows from KASB!")
        print(f"Data saved to {output_csv}")
        print("\nPreview of extracted data:")
        print(df.head())
        
    except Exception as e:
        print(f"Error parsing the tables: {e}")

if __name__ == "__main__":
    scrape_kasb()
