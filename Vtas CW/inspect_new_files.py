import pandas as pd
import os

files = [
    r"data/input/CaterWest - Libro IVA VENTAS - 2007.xls",
    r"data/input/CaterWest - Libro IVA VENTAS - 2008.xls"
]

for f in files:
    print(f"\n{'='*60}")
    print(f"FILE: {f}")
    print(f"{'='*60}")
    if not os.path.exists(f):
        print("File not found.")
        continue
    
    xls = pd.ExcelFile(f)
    print(f"Sheets identified: {xls.sheet_names}")
    
    for sheet in xls.sheet_names:
        df = pd.read_excel(f, sheet_name=sheet, header=None)
        if len(df) <= 7:
            print(f"Sheet {sheet}: Empty or too short.")
            continue
            
        # Check standard header for month info
        header_month = str(df.iloc[1, 2]).strip()
        
        # Check first data row for actual date range
        data_rows = df.iloc[6:].dropna(subset=[1, 4], how='all')
        if data_rows.empty:
            print(f"Sheet {sheet}: No data rows found.")
        else:
            first_date = data_rows.iloc[0, 1]
            last_date = data_rows.iloc[-1, 1]
            count = len(data_rows)
            print(f"Sheet {sheet}: Header={header_month} | FirstDate={first_date} | LastDate={last_date} | Rows={count}")
