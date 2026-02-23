"""
Final targeted inspection: get data rows from an old sheet and compare with new.
READ-ONLY - does NOT modify anything.
"""
import pandas as pd

OLD = r"c:\Users\Tuchi\MiEstudioIA\Vtas CW\data\input\Libro IVA VTAS 2001.xls"
NEW = r"c:\Users\Tuchi\MiEstudioIA\Vtas CW\data\input\Libros IVA ventas desde 2011 2021.xlsx"

pd.set_option('display.max_columns', None)
pd.set_option('display.width', 300)
pd.set_option('display.max_colwidth', 45)

# ---- OLD FORMAT: Show the MAY 01 sheet which we know has data ----
print("=" * 100)
print("OLD FORMAT - Sheet 'MAY 01' - Data rows (rows 6-19)")
print("=" * 100)
df_old = pd.read_excel(OLD, sheet_name='MAY 01', header=None)
print(df_old.iloc[6:20].to_string())

# Also show headers for reference
print("\n--- OLD: Header rows 3-5 ---")
print(df_old.iloc[3:6].to_string())

# ---- NEW FORMAT: Show headers and first data rows ----
print("\n" + "=" * 100)
print("NEW FORMAT - Sheet 'ventas nuevas' - Headers (row 5) and data rows (6-11)")
print("=" * 100)
df_new = pd.read_excel(NEW, sheet_name='ventas nuevas', header=None)
print("\n--- NEW: Header row 5 ---")
print(df_new.iloc[5:6].to_string())
print("\n--- NEW: Data rows 6-11 ---")
print(df_new.iloc[6:12].to_string())

# ---- Check: does the old format have Nota de Crédito? ----
print("\n\n--- OLD: Checking for N/C (Nota de Crédito) entries across all sheets ---")
for sheet in pd.ExcelFile(OLD).sheet_names:
    df_temp = pd.read_excel(OLD, sheet_name=sheet, header=None)
    # Column 2 appears to be "Tipo" in the old format
    ndc_mask = df_temp[3].astype(str).str.contains('NDC|N/C', na=False)
    count = ndc_mask.sum()
    if count > 0:
        print(f"  Sheet '{sheet}': {count} N/C entries found")
        # Show one example
        example = df_temp[ndc_mask].head(1)
        print(f"    Example: {example.iloc[0].tolist()}")

# ---- Check: does old format have Facturas B? ----
print("\n--- OLD: Checking for 'B' type invoices across all sheets ---")
for sheet in pd.ExcelFile(OLD).sheet_names:
    df_temp = pd.read_excel(OLD, sheet_name=sheet, header=None)
    b_mask = df_temp[2].astype(str).str.strip().eq('B')
    count = b_mask.sum()
    if count > 0:
        print(f"  Sheet '{sheet}': {count} type-B entries")
        example = df_temp[b_mask].head(1)
        print(f"    Example: {example.iloc[0].tolist()}")

# ---- Check the old format column 3 (seems to be a sub-type like "NDC", number?) ----
print("\n--- OLD: Unique values in col 2 (Tipo) and col 3 (sub-type?) ---")
for sheet in pd.ExcelFile(OLD).sheet_names:
    df_temp = pd.read_excel(OLD, sheet_name=sheet, header=None)
    data = df_temp.iloc[6:]
    col2_vals = data[2].dropna().unique()
    col3_vals = data[3].dropna().unique()
    print(f"  Sheet '{sheet}': col2={col2_vals}, col3={col3_vals}")

print("\nINSPECTION COMPLETE.")
