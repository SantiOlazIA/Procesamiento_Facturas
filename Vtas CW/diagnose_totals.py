"""
DIAGNOSTIC: Find rows where Total != sum of component columns.
Also check for IVA values lost during classification.
READ-ONLY - does not modify any files.
"""
import pandas as pd
import numpy as np

# Check the current report
REPORT = r"data\output\All_Sales_Report.xlsx"
df = pd.read_excel(REPORT)

pd.set_option('display.max_columns', None)
pd.set_option('display.width', 300)
pd.set_option('display.max_colwidth', 40)

# Component columns that should sum to Total
component_cols = [
    "A_Neto_21", "A_Neto_10_5", "B_Neto_21", "B_Neto_10_5",
    "IVA_Exento",
    "A_IVA_21", "A_IVA_10_5", "B_IVA_21", "B_IVA_10_5",
    "Reten_Percep",
]

# Calculate sum of components
df["_comp_sum"] = df[component_cols].fillna(0).sum(axis=1)
df["_diff"] = df["Total"] - df["_comp_sum"]
df["_abs_diff"] = df["_diff"].abs()

# Find mismatches (tolerance 0.01)
mismatches = df[df["_abs_diff"] > 0.01]
print(f"Rows with Total != sum of components: {len(mismatches)}")
print(f"Total rows in report: {len(df)}")

if not mismatches.empty:
    print(f"\n--- ALL MISMATCHED ROWS ---")
    for _, row in mismatches.iterrows():
        print(f"\n  Row {int(row['Nro'])}:")
        print(f"    Fecha: {row['Fecha']}, Tipo: {row['Tipo']}, Comp: {row['Comprobante']}")
        print(f"    Razon Social: {row['Razon Social']}")
        print(f"    A_Neto_21={row['A_Neto_21']}, A_Neto_10.5={row['A_Neto_10_5']}")
        print(f"    A_IVA_21={row['A_IVA_21']}, A_IVA_10.5={row['A_IVA_10_5']}")
        print(f"    B_Neto_21={row['B_Neto_21']}, B_Neto_10.5={row['B_Neto_10_5']}")
        print(f"    B_IVA_21={row['B_IVA_21']}, B_IVA_10.5={row['B_IVA_10_5']}")
        print(f"    IVA_Exento={row['IVA_Exento']}, Percep={row['Reten_Percep']}")
        print(f"    Component sum: {row['_comp_sum']:.4f}")
        print(f"    Total:         {row['Total']:.4f}")
        print(f"    DIFFERENCE:    {row['_diff']:.4f}")

# Also check: which original file/sheet does each mismatch come from?
# We need to trace back. Let's check the originals directly.
print(f"\n\n{'=' * 70}")
print("CHECKING ORIGINALS: does col14 = sum(col8..col13) in the source files?")
print("=" * 70)

SOURCE_FILES = [
    r"data\input\Libro IVA VTAS 2001.xls",
    r"data\input\Libro IVA VTAS 2002.xls",
    r"data\input\Libro IVA VTAS 2003.xls",
    r"data\input\Libro IVA VTAS 2004.xls",
]

# In original files: col8=Neto ByZ, col9=Neto A, col10=Excluidas,
# col11=IVA General, col12=IVA No Insc, col13=Percepciones, col14=Total
for filepath in SOURCE_FILES:
    xls = pd.ExcelFile(filepath)
    for sheet in xls.sheet_names:
        df_orig = pd.read_excel(filepath, sheet_name=sheet, header=None)
        data = df_orig.iloc[6:]
        data = data[data[5].astype(str).str.upper() != "TOTALES"]
        data = data[~(data[1].isna() & data[9].isna())]

        if data.empty:
            continue

        for idx, row in data.iterrows():
            total = row[14]
            if pd.isna(total):
                continue
            total = float(total)
            if total == 0:
                continue

            # Sum components
            components = [row[8], row[9], row[10], row[11], row[12], row[13]]
            comp_sum = sum(float(c) for c in components if pd.notna(c))
            diff = abs(total - comp_sum)

            if diff > 0.01:
                import os
                print(f"\n  ORIGINAL MISMATCH: {os.path.basename(filepath)}, "
                      f"Sheet '{sheet}', Excel row {idx+1}")
                print(f"    col8(NetoByZ)={row[8]}, col9(NetoA)={row[9]}, "
                      f"col10(Excl)={row[10]}")
                print(f"    col11(IVAGen)={row[11]}, col12(IVANoI)={row[12]}, "
                      f"col13(Percep)={row[13]}")
                print(f"    Sum of cols 8-13: {comp_sum:.4f}")
                print(f"    col14(Total):     {total:.4f}")
                print(f"    DIFF: {total - comp_sum:.4f}")

print("\nDIAGNOSTIC COMPLETE.")
