import os
import pandas as pd
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
import time
from io import StringIO

def cleanup_old_files():
   

def scrape_scstrade(context):
    print("📊 Scraping SCSTrade...")
    url = "https://www.scstrade.com/MarketStatistics/MS_MarketValuations.aspx?sectorid=-14&name=Top%2040%20Highest%20Dividend%20Yield%20Stocks"
    page = context.new_page()
    page.goto(url)
    try:
        page.wait_for_selector('table.ui-jqgrid-htable', timeout=20000)
        page.wait_for_selector('table#listind tr.jqgrow', timeout=20000)
    except Exception as e:
        print(f"  Error loading SCSTrade: {e}")
        page.close()
        return

    soup = BeautifulSoup(page.content(), 'html.parser')
    page.close()

    header_table = soup.find('table', class_='ui-jqgrid-htable')
    headers_list = []
    if header_table:
        for th in header_table.find_all('th'):
            div = th.find('div', class_='ui-jqgrid-sortable')
            if div:
                for span in div.find_all('span'):
                    span.decompose()
                headers_list.append(div.get_text(strip=True))
            else:
                headers_list.append(th.get_text(strip=True))

    data_table = soup.find('table', id='listind')
    rows = []
    if data_table:
        for tr in data_table.find_all('tr', class_='jqgrow'):
            rows.append([td.get_text(strip=True) for td in tr.find_all('td')])

    if headers_list and headers_list[0] == '':
        headers_list[0] = 'ID'
        
    if rows:
        df = pd.DataFrame(rows, columns=headers_list)
        df.to_csv("scstrade_dividends.csv", index=False)
        print(f"  ✅ Saved {len(rows)} stocks to scstrade_dividends.csv\n")
    else:
        print("  ❌ SCSTrade: No rows found.\n")

def scrape_tradingview(context):
    print("📈 Scraping TradingView...")
    url = "https://www.tradingview.com/markets/stocks-pakistan/market-movers-high-dividend/"
    page = context.new_page()
    page.goto(url)
    try:
        page.wait_for_selector('tr.listRow', timeout=20000)
        # Scroll down to trigger lazy loading
        print("  Scrolling to load background data...")
        for _ in range(3):
            page.keyboard.press("PageDown")
            time.sleep(1)
        html_content = page.content()
    except Exception as e:
        print(f"  Error loading TradingView: {e}")
        page.close()
        return
    page.close()
        
    soup = BeautifulSoup(html_content, 'html.parser')
    headers_list = []
    thead = soup.find('thead')
    if thead:
        headers_list = [th.get_text(separator=" ", strip=True) for th in thead.find_all('th')]

    rows = []
    for tr in soup.find_all('tr', class_='listRow'):
        row_data = [td.get_text(separator=" ", strip=True) for td in tr.find_all('td')]
        if row_data:
            rows.append(row_data)

    if rows:
        num_cols = len(rows[0])
        if len(headers_list) > num_cols:
            headers_list = headers_list[:num_cols]
        elif len(headers_list) < num_cols:
            headers_list += [f"Column_{i+1}" for i in range(len(headers_list), num_cols)]
            
        df = pd.DataFrame(rows, columns=headers_list)
        df.to_csv("tradingview_dividends.csv", index=False)
        print(f"  ✅ Saved {len(rows)} stocks to tradingview_dividends.csv\n")
    else:
        print("  ❌ TradingView: No rows found.\n")

def scrape_investing(context):
    print("🌐 Scraping Investing.com...")
    url = "https://www.investing.com/equities/pakistan-stock-exchange-dividends"
    page = context.new_page()
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=60000)
        print("  Waiting 5 seconds for bot protection and tables to render...")
        page.wait_for_timeout(5000)
        
        for _ in range(3):
            page.keyboard.press("PageDown")
            time.sleep(1)
            
        html_content = page.content()
    except Exception as e:
        print(f"  Error loading Investing.com: {e}")
        page.close()
        return
    page.close()
        
    try:
        tables = pd.read_html(StringIO(html_content))
        if tables:
            df = max(tables, key=len)
            df = df.dropna(axis=1, how='all')
            df.to_csv("investing_dividends.csv", index=False)
            print(f"  ✅ Saved {len(df)} rows to investing_dividends.csv\n")
        else:
            print("  ❌ Investing.com: No tables found.\n")
    except Exception as e:
        print(f"  ❌ Investing.com parsing error: {e}\n")

if __name__ == "__main__":
    cleanup_old_files()
    
    print("🚀 Firing up Playwright Browser...\n")
    # We use a single Playwright instance and context for all 3 sites to make it much faster!
    with sync_playwright() as p:
        # Headless=False because Investing.com blocked headless mode earlier
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
        )
        
        scrape_scstrade(context)
        scrape_tradingview(context)
        scrape_investing(context)
        
        browser.close()
        
    print("🎉 All scraping tasks finished successfully!")
