import pandas as pd
file_path = r'c:\Users\Tuchi\.gemini\antigravity\scratch\doe-project\data\input\Prueba Compras Gama.xlsx'
xl = pd.ExcelFile(file_path)
print(xl.sheet_names)
