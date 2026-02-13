
import pandas as pd
import os

try:
    df = pd.read_excel(r'c:\Users\Tuchi\MiEstudioIA\Input\202601 - IVA Compras.xlsx')
    with open('cols.txt', 'w') as f:
        f.write("Columns:\n")
        f.write(str(df.columns.tolist()) + "\n\n")
        f.write("First 5 rows:\n")
        f.write(df.head().to_string())
    print("Inspection complete. Check cols.txt")
except Exception as e:
    print(f"Error: {e}")
