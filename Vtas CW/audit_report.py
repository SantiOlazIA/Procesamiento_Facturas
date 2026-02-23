"""
COMPREHENSIVE DATA INTEGRITY AUDIT
===================================
Cross-references ALL data in All_Sales_Report.xlsx against the original
source files. Establishes control points for:
  1. Row counts per source file and sheet
  2. Total sums per source file
  3. Every single eliminated row with exact original position
  4. Investigation of row 252 specifically
  5. Detection of phantom rows (data not found in originals)

This script is 100% READ-ONLY. It does NOT modify any file.
"""
import pandas as pd
import numpy as np
import os

pd.set_option('display.max_columns', None)
pd.set_option('display.width', 300)
pd.set_option('display.max_colwidth', 50)

REPORT_FILE = r"data\output\All_Sales_Report.xlsx"
SOURCE_FILES = {
    "2001": r"data\input\Libro IVA VTAS 2001.xls",
    "2002": r"data\input\Libro IVA VTAS 2002.xls",
    "2003": r"data\input\Libro IVA VTAS 2003.xls",
    "2004": r"data\input\Libro IVA VTAS 2004.xls",
}


def count_original_rows(filepath):
    """
    Count data rows, total sum, and empty/totales rows in an original file.
    Returns detailed per-sheet breakdown.
    """
    xls = pd.ExcelFile(filepath)
    sheets_info = []

    for sheet_name in xls.sheet_names:
        df = pd.read_excel(filepath, sheet_name=sheet_name, header=None)

        # Total rows in the sheet
        total_rows = len(df)

        # Data area: rows 6 onwards
        data_area = df.iloc[6:].copy()

        # Count TOTALES rows
        totales_mask = data_area[5].astype(str).str.upper() == "TOTALES"
        totales_count = totales_mask.sum()

        # Count empty filler rows (only row number in col 0, rest NaN)
        empty_mask = data_area[1].isna() & data_area[9].isna()
        empty_count = empty_mask.sum()

        # Actual data rows (after filtering)
        data_rows = data_area[~totales_mask & ~empty_mask]
        data_count = len(data_rows)

        # Rows with Total=0
        zero_total_mask = data_rows[14].fillna(0).astype(float) == 0
        zero_total_count = zero_total_mask.sum()

        # Non-zero data rows (what should end up in the report)
        kept_count = data_count - zero_total_count

        # Sum of Total column (col 14) for non-zero rows
        non_zero_data = data_rows[~zero_total_mask]
        total_sum = non_zero_data[14].astype(float).sum() if not non_zero_data.empty else 0

        # Collect zero-total row details
        zero_rows = []
        for idx, row in data_rows[zero_total_mask].iterrows():
            zero_rows.append({
                "sheet": sheet_name,
                "excel_row": idx + 1,  # 1-based
                "col0_nro": row[0],
                "col4_comp": row[4],
                "col5_name": row[5],
                "col14_total": row[14],
            })

        sheets_info.append({
            "sheet": sheet_name,
            "total_rows_in_sheet": total_rows,
            "header_rows": 6,
            "totales_rows": totales_count,
            "empty_filler_rows": empty_count,
            "data_rows": data_count,
            "zero_total_rows": zero_total_count,
            "kept_rows": kept_count,
            "total_sum": total_sum,
            "zero_row_details": zero_rows,
        })

    return sheets_info


def main():
    # ================================================================
    # CONTROL POINT 1: Load the report and show basic stats
    # ================================================================
    print("=" * 80)
    print("CONTROL POINT 1: REPORT FILE OVERVIEW")
    print("=" * 80)

    report_df = pd.read_excel(REPORT_FILE)
    print(f"  File: {REPORT_FILE}")
    print(f"  Total rows: {len(report_df)}")
    print(f"  Columns: {list(report_df.columns)}")
    print(f"  Report Total sum: {report_df['Total'].sum():.4f}")

    # ================================================================
    # CONTROL POINT 2: Per-source-file breakdown
    # ================================================================
    print(f"\n{'=' * 80}")
    print("CONTROL POINT 2: SOURCE FILE ROW COUNTS & TOTALS")
    print("=" * 80)

    grand_total_kept = 0
    grand_total_sum = 0.0
    all_zero_rows = []
    expected_rows_per_file = {}

    for label, filepath in SOURCE_FILES.items():
        print(f"\n  --- {label}: {os.path.basename(filepath)} ---")
        sheets = count_original_rows(filepath)

        file_kept = 0
        file_sum = 0.0
        file_data = 0
        file_zero = 0

        for s in sheets:
            file_kept += s["kept_rows"]
            file_sum += s["total_sum"]
            file_data += s["data_rows"]
            file_zero += s["zero_total_rows"]
            all_zero_rows.extend(s["zero_row_details"])

            if s["data_rows"] > 0:
                print(f"    Sheet '{s['sheet']}': "
                      f"data={s['data_rows']}, "
                      f"zero_total={s['zero_total_rows']}, "
                      f"kept={s['kept_rows']}, "
                      f"sum={s['total_sum']:.2f}")

        print(f"    FILE TOTAL: data={file_data}, removed={file_zero}, "
              f"kept={file_kept}, sum={file_sum:.4f}")

        expected_rows_per_file[label] = file_kept
        grand_total_kept += file_kept
        grand_total_sum += file_sum

    print(f"\n  GRAND TOTAL expected rows: {grand_total_kept}")
    print(f"  GRAND TOTAL expected sum: {grand_total_sum:.4f}")
    print(f"  REPORT actual rows: {len(report_df)}")
    print(f"  REPORT actual sum: {report_df['Total'].sum():.4f}")

    row_diff = len(report_df) - grand_total_kept
    sum_diff = report_df['Total'].sum() - grand_total_sum
    print(f"\n  ** ROW DIFFERENCE: {row_diff} **")
    print(f"  ** SUM DIFFERENCE: {sum_diff:.4f} **")

    if row_diff != 0:
        print(f"  >>> WARNING: Row count mismatch! Report has {abs(row_diff)} "
              f"{'extra' if row_diff > 0 else 'missing'} row(s).")
    if abs(sum_diff) > 0.01:
        print(f"  >>> WARNING: Sum mismatch! Difference of {sum_diff:.4f}")

    # ================================================================
    # CONTROL POINT 3: EVERY SINGLE ELIMINATED ROW
    # ================================================================
    print(f"\n{'=' * 80}")
    print("CONTROL POINT 3: COMPLETE LIST OF ELIMINATED ROWS (Total=0)")
    print(f"  Total eliminated: {len(all_zero_rows)}")
    print("=" * 80)

    for file_label, filepath in SOURCE_FILES.items():
        file_zeros = [z for z in all_zero_rows
                      if any(z["sheet"] in pd.ExcelFile(filepath).sheet_names
                             for _ in [1])]
        # Re-do per file to be accurate
    
    # Print all zero rows grouped by source file
    for file_label, filepath in SOURCE_FILES.items():
        xls = pd.ExcelFile(filepath)
        file_zeros = [z for z in all_zero_rows if z["sheet"] in xls.sheet_names]
        if file_zeros:
            print(f"\n  From {os.path.basename(filepath)}:")
            for i, z in enumerate(file_zeros, 1):
                print(f"    {i}. Sheet '{z['sheet']}', Excel row {z['excel_row']}, "
                      f"Orig.Nro={z['col0_nro']}, Comp={z['col4_comp']}, "
                      f"Name={z['col5_name']}, Total={z['col14_total']}")

    # ================================================================
    # CONTROL POINT 4: INVESTIGATE ROW 252
    # ================================================================
    print(f"\n{'=' * 80}")
    print("CONTROL POINT 4: INVESTIGATION OF ROW 252")
    print("=" * 80)

    if len(report_df) >= 252:
        row252 = report_df.iloc[251]  # 0-based
        print(f"  Row 252 in All_Sales_Report:")
        print(f"    Nro:           {row252['Nro']}")
        print(f"    Fecha:         {row252['Fecha']}")
        print(f"    Tipo:          {row252['Tipo']}")
        print(f"    Comprobante:   {row252['Comprobante']}")
        print(f"    Razon Social:  {row252['Razon Social']}")
        print(f"    Cuit / DNI:    {row252['Cuit / DNI']}")
        print(f"    A_Neto_21:     {row252['A_Neto_21']}")
        print(f"    A_IVA_21:      {row252['A_IVA_21']}")
        print(f"    Total:         {row252['Total']}")

        # Search for this data in ALL original files
        comp252 = str(row252['Comprobante']).strip()
        name252 = str(row252['Razon Social']).strip()
        total252 = row252['Total']
        date252 = row252['Fecha']

        print(f"\n  Searching for Comprobante '{comp252}' in all source files...")
        print(f"  Also searching for Name '{name252}' and Total={total252}...")

        for label, filepath in SOURCE_FILES.items():
            xls = pd.ExcelFile(filepath)
            for sheet in xls.sheet_names:
                df = pd.read_excel(filepath, sheet_name=sheet, header=None)
                data = df.iloc[6:]

                # Search by comprobante (col 4)
                for idx, row in data.iterrows():
                    comp_raw = str(row[4]).strip() if pd.notna(row[4]) else ""
                    name_raw = str(row[5]).strip() if pd.notna(row[5]) else ""
                    total_raw = row[14] if pd.notna(row[14]) else None

                    # Match by comprobante number (the numeric part)
                    comp_match = False
                    if comp252 and comp_raw:
                        # Strip letter prefix from comp252 for comparison
                        comp252_num = comp252.lstrip("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
                        comp_raw_num = comp_raw.replace("-", "").lstrip("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
                        if comp252_num and comp_raw_num and comp252_num == comp_raw_num:
                            comp_match = True

                    # Match by name
                    name_match = (name252.upper() in name_raw.upper()
                                  or name_raw.upper() in name252.upper()) if name252 and name_raw else False

                    # Match by total
                    total_match = False
                    if total_raw is not None and not pd.isna(total252):
                        try:
                            total_match = abs(float(total_raw) - float(total252)) < 0.01
                        except:
                            pass

                    if comp_match or (name_match and total_match):
                        print(f"    FOUND in {label} -> Sheet '{sheet}', Excel row {idx + 1}:")
                        print(f"      Col0={row[0]}, Col1={row[1]}, Col2={row[2]}, "
                              f"Col3={row[3]}, Col4={row[4]}")
                        print(f"      Col5={row[5]}, Col14={row[14]}")

        # Also show surrounding rows for context
        print(f"\n  Context: Rows 249-255 in the report:")
        subset = report_df.iloc[248:255][["Nro", "Fecha", "Tipo", "Comprobante",
                                          "Razon Social", "Total"]]
        print(subset.to_string(index=False))
    else:
        print(f"  Report only has {len(report_df)} rows, no row 252.")

    # ================================================================
    # CONTROL POINT 5: CHECK FOR PHANTOM ROWS
    # ================================================================
    print(f"\n{'=' * 80}")
    print("CONTROL POINT 5: PHANTOM ROW DETECTION")
    print("  Checking if report row count matches the sum of originals")
    print("=" * 80)

    # The 2001 data was loaded from the pre-transformed file, so let's
    # verify that file separately
    print(f"\n  Expected breakdown:")
    for label, count in expected_rows_per_file.items():
        print(f"    {label}: {count} rows")
    print(f"    SUM: {grand_total_kept}")
    print(f"    Report: {len(report_df)}")

    if row_diff > 0:
        print(f"\n  >>> {row_diff} EXTRA ROW(S) detected in the report!")
        print(f"  These could be:")
        print(f"    - Rows from the 2001 pre-transformed file that were counted differently")
        print(f"    - Artifact rows from header/footer leaking through filters")
    elif row_diff < 0:
        print(f"\n  >>> {abs(row_diff)} MISSING ROW(S) detected!")
    else:
        print(f"\n  Row counts match perfectly.")

    # ================================================================
    # CONTROL POINT 6: TOTAL SUM VERIFICATION PER YEAR BOUNDARY
    # ================================================================
    print(f"\n{'=' * 80}")
    print("CONTROL POINT 6: TOTAL SUM VERIFICATION BY DATE RANGE")
    print("=" * 80)

    # For each source file, sum TOTALES rows as independent check
    for label, filepath in SOURCE_FILES.items():
        xls = pd.ExcelFile(filepath)
        totales_sum = 0
        for sheet in xls.sheet_names:
            df = pd.read_excel(filepath, sheet_name=sheet, header=None)
            data = df.iloc[6:]
            totales_rows = data[data[5].astype(str).str.upper() == "TOTALES"]
            for _, trow in totales_rows.iterrows():
                try:
                    totales_sum += float(trow[14])
                except:
                    pass
        print(f"  {label} TOTALES sum (from original): {totales_sum:.4f}")

    print(f"\n{'=' * 80}")
    print("AUDIT COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()
