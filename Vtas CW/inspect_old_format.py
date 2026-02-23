"""
Inspect the OLD format file: Libro IVA VTAS 2001.xls
This script is READ-ONLY. It does NOT modify any files.
"""
import pandas as pd
import sys

FILE_PATH = r"c:\Users\Tuchi\MiEstudioIA\Vtas CW\data\input\Libro IVA VTAS 2001.xls"

try:
    # 1. List all sheet names
    xls = pd.ExcelFile(FILE_PATH)
    print("=" * 80)
    print(f"FILE: {FILE_PATH}")
    print(f"Number of sheets: {len(xls.sheet_names)}")
    print(f"Sheet names: {xls.sheet_names}")
    print("=" * 80)

    # 2. For each sheet, show structure
    for sheet_name in xls.sheet_names:
        print(f"\n{'=' * 80}")
        print(f"SHEET: '{sheet_name}'")
        print(f"{'=' * 80}")

        df = pd.read_excel(FILE_PATH, sheet_name=sheet_name, header=None)
        print(f"Shape (rows x cols): {df.shape}")

        # Show first 20 rows raw (no header assumption)
        print(f"\n--- First 20 rows (raw, no header) ---")
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', 200)
        pd.set_option('display.max_colwidth', 40)
        print(df.head(20).to_string())

        # Show last 5 rows
        print(f"\n--- Last 5 rows ---")
        print(df.tail(5).to_string())

        # Show dtypes
        print(f"\n--- Column dtypes ---")
        print(df.dtypes.to_string())

        # Show non-null counts
        print(f"\n--- Non-null counts per column ---")
        print(df.count().to_string())

    print("\n\nINSPECTION COMPLETE - No files were modified.")

except Exception as e:
    print(f"ERROR: {e}", file=sys.stderr)
    import traceback
    traceback.print_exc()
    sys.exit(1)
