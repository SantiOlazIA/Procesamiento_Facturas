"""
Deeper inspection of the OLD format to understand all sheets and headers.
READ-ONLY - does NOT modify any files.
"""
import pandas as pd

FILE_PATH = r"c:\Users\Tuchi\MiEstudioIA\Vtas CW\data\input\Libro IVA VTAS 2001.xls"

xls = pd.ExcelFile(FILE_PATH)
print(f"Total sheets: {len(xls.sheet_names)}")
print(f"Sheet names: {xls.sheet_names}")

# Show only the header area (rows 0-5) and one data row from the FIRST sheet
first_sheet = xls.sheet_names[0]
df = pd.read_excel(FILE_PATH, sheet_name=first_sheet, header=None)
pd.set_option('display.max_columns', None)
pd.set_option('display.width', 250)
pd.set_option('display.max_colwidth', 40)

print(f"\n=== FIRST SHEET: '{first_sheet}' ===")
print(f"Shape: {df.shape}")
print("\n--- Header area (rows 0-5) ---")
print(df.iloc[0:6].to_string())
print("\n--- First data row (row 6) ---")
print(df.iloc[6:7].to_string())

# Check if all sheets have the same structure
print("\n\n=== COMPARING SHEET STRUCTURES ===")
for sheet_name in xls.sheet_names:
    df_temp = pd.read_excel(FILE_PATH, sheet_name=sheet_name, header=None)
    print(f"Sheet '{sheet_name}': shape={df_temp.shape}")

print("\nINSPECTION COMPLETE.")
