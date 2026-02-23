import pandas as pd

files = [
    r"data/input/IVA Cater 06 04.xls",
    r"data/input/IVA Cater 05 05.xls",
    r"data/input/Libro IVA VTAS 2004.xls"
]

for f in files:
    print(f"\n{'='*60}")
    print(f"FILE: {f}")
    print(f"{'='*60}")
    xls = pd.ExcelFile(f)
    print(f"Sheets: {xls.sheet_names}")
    
    # Check important sheets
    target_sheets = [s for s in xls.sheet_names if 'venta' in s.lower() or 'iva' in s.lower()]
    for sheet in target_sheets[:3]: # Limit to 3 sheets
        print(f"\n--- Sheet: '{sheet}' ---")
        try:
            df = pd.read_excel(f, sheet_name=sheet, header=None, nrows=10)
            print(df.to_string(index=False))
            print(f"Columns: {df.shape[1]}")
        except Exception as e:
            print(f"Error reading sheet {sheet}: {e}")
