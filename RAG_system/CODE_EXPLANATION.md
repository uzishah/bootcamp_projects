# 📚 Complete Code Explanation - Line by Line

## 🎯 Project Overview
Yeh ek RAG (Retrieval Augmented Generation) based chatbot hai jo FMR (Fund Manager Reports) PDFs ko read karke questions ka jawab deta hai.

---

## 1️⃣ **src/pdf_extractor.py** - PDF se Data Nikalna

### Import Statements
```python
import pdfplumber  # PDF files ko read karne ke liye
import re          # Regular expressions (pattern matching) ke liye
```

---

### Function 1: `table_to_rows(table: list) -> list`
**Purpose:** Table ko individual rows mein convert karta hai

```python
def table_to_rows(table: list) -> list:
    # Line 16-17: Agar table empty hai ya sirf 1 row hai, toh return empty list
    if not table or len(table) < 2:
        return []
    
    rows = []  # Yahan extracted rows store honge
    
    # Line 21: Har row ko process karo
    for row in table:
        # Line 23-24: Empty rows ko skip karo
        if not any(cell for cell in row if cell and str(cell).strip()):
            continue
        
        # Line 27: Har cell ko process karo
        for cell in row:
            if not cell:  # Empty cell skip
                continue
            
            cell_text = str(cell).strip()  # Cell ko string mein convert aur trim
            
            # Line 33: Agar cell mein 5 se kam characters hain, skip
            if not cell_text or len(cell_text) < 5:
                continue
            
            # Line 36: Agar cell mein multiple lines hain (\n se separated)
            if '\n' in cell_text:
                lines = [line.strip() for line in cell_text.split('\n') if line.strip()]
                
                # Line 40-43: Check karo kya yeh holdings hain
                # Holdings = "Company Name 12.34%" format
                holdings_list = []
                for line in lines:
                    if '%' in line and len(line) < 100:
                        holdings_list.append(line)
                
                # Line 46-47: Agar 3+ holdings hain, unko ek saath rakho
                if len(holdings_list) >= 3:
                    rows.append("\n".join(holdings_list))
                # Line 48-50: Agar kam holdings hain, individual add karo
                elif holdings_list:
                    rows.extend(holdings_list)
                # Line 51-52: Short multi-line cells ko as-is rakho
                elif len(lines) <= 3:
                    rows.append(cell_text)
            else:
                # Line 54-56: Single line cells (10+ chars) add karo
                if len(cell_text) > 10:
                    rows.append(cell_text)
    
    return rows  # Extracted rows return karo
```

**Example:**
```
Input Table:
| Fund Name | NAV |
| AMMF      | 100 |

Output:
["AMMF", "100"]
```

---

### Function 2: `extract_fund_name(text: str) -> str`
**Purpose:** Page text se fund ka naam nikalta hai

```python
def extract_fund_name(text: str) -> str:
    # Line 64-65: Agar text empty hai, return empty string
    if not text:
        return ""
    
    lines = text.split('\n')  # Text ko lines mein split karo
    
    # STRATEGY 1: "Net assets of FUND NAME" pattern dhundho
    # Line 70: Har line check karo
    for line in lines:
        line_clean = line.strip()
        
        # Line 73: Agar line mein "Net assets of" hai
        if 'Net assets of' in line_clean or 'net assets of' in line_clean:
            
            # Line 75-80: Pattern 1 - "Net assets of AMMF (Symbol)"
            # Regex: (?:...) = non-capturing group
            # \s+ = one or more spaces
            # [^(]+ = anything except opening bracket
            # \(([^)]+)\) = text inside brackets
            match = re.search(
                r'(?:Net assets of|net assets of)\s+([^(]+)\s*\(([^)]+)\)', 
                line_clean, 
                re.IGNORECASE  # Case insensitive
            )
            if match:
                fund_name = match.group(1).strip()  # First captured group
                symbol = match.group(2).strip()     # Second captured group
                return f"{fund_name} ({symbol})"
            
            # Line 83-90: Pattern 2 - "Net assets of AMMF as at..."
            # [^.]+ = anything except period
            # +? = non-greedy (minimum match)
            match = re.search(
                r'(?:Net assets of|net assets of)\s+([^.]+?)\s+(?:as at|stood at|for the)', 
                line_clean, 
                re.IGNORECASE
            )
            if match:
                fund_name = match.group(1).strip()
                fund_name = fund_name.replace(' for the month of', '').strip()
                if fund_name and len(fund_name) > 5:
                    return fund_name
    
    # STRATEGY 2: First 15 lines mein common keywords dhundho
    # Line 93: Sirf first 15 lines check karo (performance)
    for line in lines[:15]:
        line_clean = line.strip()
        
        # Line 95-100: Agar line mein fund-related keywords hain
        if any(keyword in line_clean for keyword in [
            'Mutual Fund', 'Islamic Fund', 'Equity Fund', 'Balanced Fund',
            'Income Fund', 'Money Market', 'Asset Allocation', 'Fixed Term',
            'Rozana Amdani', 'Paidaar Munafa', 'Tahaffuz', 'Sovereign',
            'AMMF', 'MIF', 'KMIF', 'MBF', 'MDEF'
        ]):
            # Line 102-105: Clean up the fund name
            fund_name = line_clean.replace('New Account Opening', '').strip()
            fund_name = ' '.join(fund_name.split())  # Remove extra spaces
            if fund_name and len(fund_name) > 3:
                return fund_name
    
    return ""  # Agar kuch nahi mila, empty return
```

**Example:**
```
Input: "Net assets of Al Meezan Mutual Fund (AMMF) as at April 30..."
Output: "Al Meezan Mutual Fund (AMMF)"
```

---

### Function 3: `extract_fund_details(text: str) -> list`
**Purpose:** Fund ki important details nikalta hai (Benchmark, Launch Date, etc.)

```python
def extract_fund_details(text: str) -> list:
    # Line 113-114: Empty text check
    if not text:
        return []
    
    details = []  # Extracted details yahan store honge
    lines = text.split('\n')
    
    # Line 120-125: Important fields ki list
    key_fields = [
        'Fund Type',        # e.g., "Open End"
        'Fund Category',    # e.g., "Equity"
        'Risk Profile',     # e.g., "High"
        'Launch Date',      # e.g., "13-Jul-1995"
        'Benchmark',        # e.g., "KMI-30"
        'Listing',          # e.g., "PSX"
        'Trustee',          # e.g., "CDC"
        'Auditor',          # e.g., "A.F. Ferguson"
        'AMC Rating',       # e.g., "AM1"
        'Unit Type',        # e.g., "Growth"
        'Front End Load',   # e.g., "2.00%"
        'Back End Load',    # e.g., "Nil"
        'Management Fee',   # e.g., "Upto 3%"
        'Fund Manager',     # e.g., "Ahmed Hassan"
        'NAV',              # e.g., "100.50"
        'Net Assets',       # e.g., "Rs. 11 billion"
        'Expense Ratio'     # e.g., "2.5%"
    ]
    
    # Line 127: Har line check karo
    for line in lines:
        line_clean = line.strip()
        
        # Line 129: Har key field check karo
        for key in key_fields:
            # Line 130: Agar line key field se start hoti hai
            if line_clean.startswith(key):
                # Line 132: Agar line mein ':' hai ya key hai
                if ':' in line_clean or key in line_clean:
                    details.append(line_clean)  # Add to details
                    break  # Next line pe jao
    
    return details  # Extracted details return karo
```

**Example:**
```
Input: "Benchmark KMI-30\nLaunch Date 13-Jul-1995\nFront End Load 2.00%"
Output: ["Benchmark KMI-30", "Launch Date 13-Jul-1995", "Front End Load 2.00%"]
```

---

### Function 4: `extract_pdf(pdf_path: str) -> list`
**Purpose:** Main function - PDF se sab kuch extract karta hai

```python
def extract_pdf(pdf_path: str) -> list:
    items = []  # Yahan sare extracted items store honge
    
    # Line 147: PDF file open karo
    with pdfplumber.open(pdf_path) as pdf:
        
        # Line 148: Har page ko process karo
        for page in pdf.pages:
            pg = page.page_number  # Page number (1, 2, 3...)
            
            # Line 151-152: Page ka text extract karo
            # x_tolerance, y_tolerance = spacing for better text extraction
            full_text = page.extract_text(x_tolerance=2, y_tolerance=2)
            fund_name = extract_fund_name(full_text)  # Fund name nikalo
            
            # STEP 1: Extract fund details
            # Line 155-162: Fund details ko separate chunks mein store karo
            fund_details = extract_fund_details(full_text)
            for detail in fund_details:
                items.append({
                    "text": f"{fund_name} - {detail}" if fund_name else detail,
                    "page": pg,
                    "type": "fund_detail",  # Type = fund_detail
                    "fund_name": fund_name
                })
            
            # STEP 2: Extract tables
            # Line 165: Page se sare tables extract karo
            tables = page.extract_tables() or []
            
            # Line 167: Har table ko process karo
            for table in tables:
                if not table:  # Empty table skip
                    continue
                
                # STEP 2A: Look for holdings in table
                # Line 171-183: Holdings cells dhundho
                holdings_cells = []
                for row in table:
                    for cell in row:
                        if cell and isinstance(cell, str):
                            lines = cell.split('\n')
                            
                            # Holdings = lines with % and company names
                            holding_lines = [
                                l for l in lines 
                                if '%' in l and any(w in l for w in ['Limited', 'Company', 'Bank'])
                            ]
                            
                            # Agar 3+ holdings ek cell mein hain
                            if len(holding_lines) >= 3:
                                holdings_cells.append('\n'.join(holding_lines))
                            # Agar 1 holding hai
                            elif len(holding_lines) == 1:
                                holdings_cells.append(holding_lines[0])
                
                # Line 185-192: Agar 5+ holdings mile, combine karke store karo
                if len(holdings_cells) >= 5:
                    all_holdings = '\n'.join(holdings_cells)
                    items.append({
                        "text": f"Top 10 Holdings of {fund_name}:\n{all_holdings}" if fund_name else f"Top Holdings:\n{all_holdings}",
                        "page": pg,
                        "type": "holdings_list",  # Special type for holdings
                        "fund_name": fund_name
                    })
                
                # STEP 2B: Store individual table rows
                # Line 194-203: Table rows ko individual chunks mein store karo
                rows = table_to_rows(table)
                for row_text in rows:
                    # Holdings ko skip karo (already stored above)
                    if '%' in row_text and any(word in row_text for word in ['Limited', 'Company', 'Bank']) and len(row_text) < 100:
                        continue
                    
                    items.append({
                        "text": row_text,
                        "page": pg,
                        "type": "table_row",  # Type = table_row
                        "fund_name": fund_name
                    })
                
                # STEP 2C: Store full table for context
                # Line 205-216: Complete table bhi store karo
                header = " | ".join([str(c).strip() for c in table[0] if c]) if table else ""
                table_text = []
                for row in table[1:]:  # Skip header row
                    row_text = " | ".join([str(c).strip() for c in row if c])
                    if row_text:
                        table_text.append(row_text)
                
                if table_text:
                    full_table = f"Table: {header}\n" + "\n".join(table_text)
                    items.append({
                        "text": full_table,
                        "page": pg,
                        "type": "table",  # Type = table
                        "fund_name": fund_name
                    })
            
            # STEP 3: Extract text chunks
            # Line 218-237: Page text ko chunks mein divide karo
            if full_text and full_text.strip():
                chunk_size = 600   # Har chunk 600 characters
                overlap = 100      # Chunks ke beech 100 chars overlap
                
                # Agar text chhota hai, as-is store karo
                if len(full_text) <= chunk_size:
                    items.append({
                        "text": full_text.strip(),
                        "page": pg,
                        "type": "text",
                        "fund_name": fund_name
                    })
                else:
                    # Bada text hai, chunks mein divide karo
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
                        start = end - overlap  # Overlap ke saath next chunk
    
    return items  # Sare extracted items return karo
```

**Output Structure:**
```python
[
    {
        "text": "Al Meezan Mutual Fund (AMMF) - Benchmark KMI-30",
        "page": 8,
        "type": "fund_detail",
        "fund_name": "Al Meezan Mutual Fund (AMMF)"
    },
    {
        "text": "Top 10 Holdings of AMMF:\nLucky Cement 12.93%\nMari Energies 10.58%...",
        "page": 8,
        "type": "holdings_list",
        "fund_name": "Al Meezan Mutual Fund (AMMF)"
    },
    # ... more items
]
```

---

## Summary of pdf_extractor.py

**4 Main Functions:**

1. **`table_to_rows()`** - Table rows ko extract karta hai
2. **`extract_fund_name()`** - Fund ka naam dhundhta hai
3. **`extract_fund_details()`** - Important details nikalta hai
4. **`extract_pdf()`** - Main function - sab kuch extract karta hai

**Output Types:**
- `fund_detail` - Benchmark, Launch Date, etc.
- `holdings_list` - Top 10 holdings combined
- `table_row` - Individual table rows
- `table` - Complete tables
- `text` - Regular text chunks

**Key Concepts:**
- **Regex** - Pattern matching ke liye
- **Chunking** - Bade text ko chhote pieces mein todna
- **Overlap** - Chunks ke beech common text (context maintain karne ke liye)

---

Kya main baaki files (chunker.py, embedder.py, query_engine.py) bhi explain karoon?
