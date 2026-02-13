import pandas as pd
import json

file_path = r'c:\Users\Tuchi\.gemini\antigravity\scratch\doe-project\data\input\Prueba Compras Gama.xlsx'

try:
    df = pd.read_excel(file_path)
    # Convert to JSON for easy display or just print head
    print("--- HEAD ---")
    print(df.head().to_string())
    print("--- COLUMNS ---")
    print(df.columns.tolist())
    print("--- SHAPE ---")
    print(df.shape)
except Exception as e:
    print(f"Error: {e}")
