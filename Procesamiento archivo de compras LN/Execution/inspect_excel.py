import pandas as pd
import os

file_path = r'data/input/Libro1.xlsx'

try:
    if not os.path.exists(file_path):
        print(f"Error: File not found at {file_path}")
        exit(1)

    df = pd.read_excel(file_path)
    
    print("--- Column Names ---")
    print(df.columns.tolist())
    
    # Check for duplicates in N_COMP
    if 'N_COMP' in df.columns:
        duplicate_counts = df['N_COMP'].value_counts()
        duplicates = duplicate_counts[duplicate_counts > 1]
        
        print("\n--- Duplicate Invoice Numbers (N_COMP) ---")
        if not duplicates.empty:
            print(f"Found {len(duplicates)} duplicate invoice numbers:")
            print(duplicates)
        else:
            print("No duplicate invoice numbers found.")
    else:
        print("\nColumn 'N_COMP' not found in the file.")

    print("\n--- First 5 Rows ---")
    print(df.head())

except Exception as e:
    print(f"An error occurred: {e}")
