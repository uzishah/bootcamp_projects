# Pakistan Stock Market Dividend Scraper

## Project Overview
This project is a comprehensive web scraping solution that extracts dividend stock data from multiple Pakistani financial websites. It uses Playwright for browser automation to scrape real-time dividend information from various sources.

## Features

- ✅ Multi-source scraping from 3 major financial platforms
- ✅ Automated data extraction using Playwright
- ✅ CSV export for easy data analysis
- ✅ Handles dynamic content and lazy loading
- ✅ User-agent spoofing to bypass basic security filters

## Data Sources

1. **SCSTrade** - Top 40 Highest Dividend Yield Stocks
2. **TradingView** - Pakistan High Dividend Stocks
3. **Investing.com** - Pakistan Stock Exchange Dividends

## Project Structure

```
Divinded stocks/
├── master_scraper.py           # Main scraper for all 3 sources
├── extract_kasb.py             # KASB-specific scraper
├── scstrade_dividends.csv      # Output from SCSTrade
├── tradingview_dividends.csv   # Output from TradingView
├── investing_dividends.csv     # Output from Investing.com
└── README.md                   # This file
```

## Prerequisites

- Python 3.8+
- Playwright
- pandas
- BeautifulSoup4

## Installation

```bash
pip install playwright pandas beautifulsoup4
playwright install chromium
```

## Usage

### Run All Scrapers
```bash
python master_scraper.py
```

### Run KASB Scraper Only
```bash
python extract_kasb.py
```

## Output Format

Each scraper generates a CSV file with the following structure:
- Stock symbol/name
- Current price
- Dividend yield percentage
- Additional metrics (varies by source)

## Technical Details

### SCSTrade Scraper
- Targets: `table.ui-jqgrid-htable` for headers
- Waits for: `table#listind tr.jqgrow` for data rows
- Parsing: BeautifulSoup HTML parsing

### TradingView Scraper
- Targets: `tr.listRow` elements
- Implements: Scroll-based lazy loading
- Parsing: BeautifulSoup with dynamic content handling

### Investing.com Scraper
- Implements: 5-second wait for bot protection bypass
- Uses: pandas `read_html()` for table extraction
- Handles: Dynamic JavaScript-rendered content

## Error Handling

- Timeout handling for slow-loading pages
- Fallback mechanisms for missing data
- Debug HTML output for troubleshooting

## Notes

- Scrapers run in non-headless mode to avoid detection
- User-agent spoofing implemented for better success rate
- Scroll simulation for lazy-loaded content
- 20-second timeout for page loads

## Future Enhancements

- [ ] Add scheduling for automated daily scraping
- [ ] Implement data validation and cleaning
- [ ] Add database storage (MongoDB/PostgreSQL)
- [ ] Create data visualization dashboard
- [ ] Add email notifications for high-yield opportunities

## Disclaimer

This tool is for educational and research purposes only. Please respect the terms of service of the scraped websites and implement appropriate rate limiting.

---

**Last Updated**: 2026
**Version**: 1.0
