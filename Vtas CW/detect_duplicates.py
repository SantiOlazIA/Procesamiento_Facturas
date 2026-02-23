import pandas as pd
import os

# -------------------------------------------------------------------
# Configuration
# -------------------------------------------------------------------
SOURCE_FILE = r'data\output\All_Sales_Report.xlsx'

if not os.path.exists(SOURCE_FILE):
    print(f"Error: {SOURCE_FILE} not found.")
    exit(1)

# -------------------------------------------------------------------
# Process
# -------------------------------------------------------------------
print("Loading data for duplicate audit...")
df = pd.read_excel(SOURCE_FILE)

# Define duplicate criteria: Same CUIT, Same Comprobante, Same Total
df['Total_Round'] = df['Total'].apply(lambda x: round(float(x), 2) if pd.notnull(x) else 0.0)
duplicate_cols = ['Cuit / DNI', 'Comprobante', 'Total_Round']

# Find duplicates
# keep=False marks all duplicates, not just the extras
duplicates = df[df.duplicated(subset=duplicate_cols, keep=False)].copy()

if duplicates.empty:
    print("\n[SUCCESS] No duplicates found based on the criteria (CUIT, Tipo, Comprobante).")
else:
    print(f"\n[ALERT] Found {len(duplicates)} rows that appear in duplicate sets.")
    
    # Sort for better readability
    duplicates = duplicates.sort_values(by=duplicate_cols + ['Fecha'])
    
    # Display the first few examples
    print("\nSample of identified duplicates:")
    display_cols = ['Nro', 'Fecha', 'Tipo', 'Comprobante', 'Cuit / DNI', 'Razon Social', 'Total', 'Ref. Origen']
    print(duplicates[display_cols].head(50).to_string(index=False))
    
    # Generate a summary CSV for the user to review in detail if many
    duplicates_csv = r'data\output\duplicates_audit.csv'
    duplicates[display_cols].to_csv(duplicates_csv, index=False)
    print(f"\nA full audit of all {len(duplicates)} flagged rows has been saved to: {duplicates_csv}")
    
    # Summary by set
    duplicate_sets = duplicates.groupby(duplicate_cols).size().reset_index(name='Count')
    print(f"\nSUMMARY: There are {len(duplicate_sets)} distinct sets of duplicates.")
    print(duplicate_sets.head(10).to_string(index=False))
