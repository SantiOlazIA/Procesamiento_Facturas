import pandas as pd
import sys

files_to_inspect = [
    r"data/input/IVA Cater 06 04.xls",
    r"data/input/IVA Cater 05 05.xls",
    r"data/input/Libros IVA ventas desde 2011 2021.xlsx"
]

for f in files_to_inspect:
    print(f"\n{'='*60}")
    print(f"FILE: {f}")
    print(f"{'='*60}")
    try:
        if f.endswith('.xls'):
            xls = pd.ExcelFile(f)
            print(f"Sheets: {xls.sheet_names}")
            # Show first sheet structure
            df = pd.read_excel(f, sheet_name=xls.sheet_names[0], header=None, nrows=15)
        else:
            df = pd.read_excel(f, header=None, nrows=15)
        
        print("\nStructure (First 15 rows):")
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', 1000)
        print(df.to_string(index=False))
        print(f"\nShape: {df.shape[1]} columns detected in preview")

    except Exception as e:
        print(f"Error reading {f}: {e}")
