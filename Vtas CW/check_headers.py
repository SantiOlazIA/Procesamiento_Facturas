import pandas as pd

f_cater = r"data/input/IVA Cater 05 05.xls"
f_new = r"data/input/Libros IVA ventas desde 2011 2021.xlsx"

df_cater = pd.read_excel(f_cater, sheet_name='ventas nuevas', header=None, nrows=10)
df_new = pd.read_excel(f_new, header=None, nrows=10)

print("\n--- IVA Cater Column Headers (Row 6) ---")
print(df_cater.iloc[6].values[:20])

print("\n--- Libros IVA 2011-2021 Column Headers (Row 6) ---")
print(df_new.iloc[5].values[:20]) # It's row 5 for the new file (0-indexed)
