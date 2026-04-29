"""
PDF Extraction Module
Extracts text, tables, and fund details from FMR PDFs
"""

import pdfplumber
import re


def table_to_rows(table: list) -> list:
    """
    Convert table to individual rows (better for search)
    Each row becomes a searchable chunk
    Also handles multi-line cells (e.g., holdings lists)
    """
    if not table or len(table) < 2:
        return []
    
    rows = []
    
    for row in table:
        # Skip empty rows
        if not any(cell for cell in row if cell and str(cell).strip()):
            continue
        
        # Process each cell
        for cell in row:
            if not cell:
                continue
            
            cell_text = str(cell).strip()
            if not cell_text or len(cell_text) < 5:
                continue
            
            # If cell contains multiple lines, split them
            if '\n' in cell_text:
                lines = [line.strip() for line in cell_text.split('\n') if line.strip()]
                
                # Check if these are holdings (Company Name XX.XX%)
                holdings_list = []
                for line in lines:
                    if '%' in line and len(line) < 100:  # Likely a holding
                        holdings_list.append(line)
                
                # If we found multiple holdings, keep them together
                if len(holdings_list) >= 3:
                    rows.append("\n".join(holdings_list))
                elif holdings_list:
                    # Add individual holdings
                    rows.extend(holdings_list)
                elif len(lines) <= 3:  # Short multi-line cell, keep together
                    rows.append(cell_text)
            else:
                # Single line cell
                if len(cell_text) > 10:  # Meaningful content
                    rows.append(cell_text)
    
    return rows


def extract_fund_name(text: str) -> str:
    """Extract fund name from page text"""
    if not text:
        return ""
    
    lines = text.split('\n')
    
    # Strategy 1: Look for fund name in "Fund Review" or "Net assets of" sentences
    for line in lines:
        line_clean = line.strip()
        
        # Pattern 1: "Net assets of FUND NAME (SYMBOL) as at..." or "stood at..."
        if 'Net assets of' in line_clean or 'net assets of' in line_clean:
            # Try with symbol in parentheses
            match = re.search(r'(?:Net assets of|net assets of)\s+([^(]+)\s*\(([^)]+)\)', line_clean, re.IGNORECASE)
            if match:
                fund_name = match.group(1).strip()
                symbol = match.group(2).strip()
                return f"{fund_name} ({symbol})"
            
            # Try without symbol - extract fund name between "of" and "as at/stood at/for the"
            match = re.search(r'(?:Net assets of|net assets of)\s+([^.]+?)\s+(?:as at|stood at|for the)', line_clean, re.IGNORECASE)
            if match:
                fund_name = match.group(1).strip()
                # Clean up common suffixes
                fund_name = fund_name.replace(' for the month of', '').strip()
                if fund_name and len(fund_name) > 5:
                    return fund_name
    
    # Strategy 2: Look for common fund patterns in first 15 lines
    for line in lines[:15]:
        line_clean = line.strip()
        if any(keyword in line_clean for keyword in [
            'Mutual Fund', 'Islamic Fund', 'Equity Fund', 'Balanced Fund',
            'Income Fund', 'Money Market', 'Asset Allocation', 'Fixed Term',
            'Rozana Amdani', 'Paidaar Munafa', 'Tahaffuz', 'Sovereign',
            'AMMF', 'MIF', 'KMIF', 'MBF', 'MDEF'
        ]):
            # Clean up
            fund_name = line_clean.replace('New Account Opening', '').strip()
            fund_name = ' '.join(fund_name.split())
            if fund_name and len(fund_name) > 3:
                return fund_name
    
    return ""


def extract_fund_details(text: str) -> list:
    """
    Extract key fund details as separate searchable chunks
    Returns list of "Key: Value" pairs
    """
    if not text:
        return []
    
    details = []
    lines = text.split('\n')
    
    # Key fields to extract
    key_fields = [
        'Fund Type', 'Fund Category', 'Risk Profile', 'Launch Date',
        'Benchmark', 'Listing', 'Trustee', 'Auditor', 'AMC Rating',
        'Unit Type', 'Front End Load', 'Back End Load', 'Management Fee',
        'Fund Manager', 'NAV', 'Net Assets', 'Expense Ratio'
    ]
    
    for line in lines:
        line_clean = line.strip()
        # Check if line contains a key field
        for key in key_fields:
            if line_clean.startswith(key):
                # Extract key-value pair
                if ':' in line_clean or key in line_clean:
                    details.append(line_clean)
                    break
    
    return details


def extract_pdf(pdf_path: str) -> list:
    """
    Extract all content from PDF
    Returns list of items with text, page, type, and fund_name
    """
    items = []
    
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            pg = page.page_number
            
            # Get full text
            full_text = page.extract_text(x_tolerance=2, y_tolerance=2)
            fund_name = extract_fund_name(full_text)
            
            # Extract fund details as separate chunks
            fund_details = extract_fund_details(full_text)
            for detail in fund_details:
                items.append({
                    "text": f"{fund_name} - {detail}" if fund_name else detail,
                    "page": pg,
                    "type": "fund_detail",
                    "fund_name": fund_name
                })
            
            # Extract tables
            tables = page.extract_tables() or []
            
            for table in tables:
                if not table:
                    continue
                
                # Look for holdings in table (cells with multiple "Limited XX.XX%" entries)
                holdings_cells = []
                for row in table:
                    for cell in row:
                        if cell and isinstance(cell, str):
                            # Check if cell has multiple holdings (3+ lines with % and Limited/Company/Bank)
                            lines = cell.split('\n')
                            holding_lines = [l for l in lines if '%' in l and any(w in l for w in ['Limited', 'Company', 'Bank'])]
                            if len(holding_lines) >= 3:
                                holdings_cells.append('\n'.join(holding_lines))
                            elif len(holding_lines) == 1:
                                # Single holding
                                holdings_cells.append(holding_lines[0])
                
                # If we found holdings, combine them
                if len(holdings_cells) >= 5:
                    all_holdings = '\n'.join(holdings_cells)
                    items.append({
                        "text": f"Top 10 Holdings of {fund_name}:\n{all_holdings}" if fund_name else f"Top Holdings:\n{all_holdings}",
                        "page": pg,
                        "type": "holdings_list",
                        "fund_name": fund_name
                    })
                
                # Store individual table rows (for better retrieval)
                rows = table_to_rows(table)
                for row_text in rows:
                    # Skip if already captured in holdings
                    if '%' in row_text and any(word in row_text for word in ['Limited', 'Company', 'Bank']) and len(row_text) < 100:
                        continue  # Skip individual holdings, we already have them combined
                    
                    items.append({
                        "text": row_text,
                        "page": pg,
                        "type": "table_row",
                        "fund_name": fund_name
                    })
                
                # Store full table for context
                header = " | ".join([str(c).strip() for c in table[0] if c]) if table else ""
                table_text = []
                for row in table[1:]:
                    row_text = " | ".join([str(c).strip() for c in row if c])
                    if row_text:
                        table_text.append(row_text)
                
                if table_text:
                    full_table = f"Table: {header}\n" + "\n".join(table_text)
                    items.append({
                        "text": full_table,
                        "page": pg,
                        "type": "table",
                        "fund_name": fund_name
                    })
            
            # Extract text (chunked - smaller for Jina AI)
            if full_text and full_text.strip():
                # Smaller chunks to avoid Jina AI token limit
                chunk_size = 600
                overlap = 100
                
                if len(full_text) <= chunk_size:
                    items.append({
                        "text": full_text.strip(),
                        "page": pg,
                        "type": "text",
                        "fund_name": fund_name
                    })
                else:
                    start = 0
                    while start < len(full_text):
                        end = start + chunk_size
                        chunk = full_text[start:end]
                        items.append({
                            "text": chunk,
                            "page": pg,
                            "type": "text",
                            "fund_name": fund_name
                        })
                        start = end - overlap
    
    return items
