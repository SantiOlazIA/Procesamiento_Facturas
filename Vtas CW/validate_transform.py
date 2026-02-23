"""
Validate the transformed output against the original data.
READ-ONLY - does NOT modify any files.
"""
import pandas as pd
import numpy as np

ORIGINAL = r"data\input\Libro IVA VTAS 2001.xls"
TRANSFORMED = r"data\output\Libro_IVA_VTAS_2001_transformed.xlsx"

pd.set_option('display.max_columns', None)
pd.set_option('display.width', 300)
pd.set_option('display.max_colwidth', 40)

df_new = pd.read_excel(TRANSFORMED)

print("=" * 70)
print("VALIDATION REPORT")
print("=" * 70)

# 1. Row count check
print(f"\n1. Row count: {len(df_new)}")

# 2. Required columns not null
required_cols = ["Tipo", "Comprobante", "Total"]
for col in required_cols:
    nulls = df_new[col].isna().sum()
    print(f"   {col}: {nulls} nulls {'OK' if nulls == 0 else 'WARNING'}")

# 3. Fecha nulls (some expected for anulado entries)
fecha_nulls = df_new["Fecha"].isna().sum()
print(f"   Fecha: {fecha_nulls} nulls (may be OK for ANULADO entries)")

# 4. Tipo values
print(f"\n2. Tipo distribution:")
print(f"   {df_new['Tipo'].value_counts().to_dict()}")

# 5. Comprobante format check
comp_pattern = df_new["Comprobante"].str.match(r'^[A-Z]\d{12}$', na=False)
invalid_comp = df_new[~comp_pattern & df_new["Comprobante"].notna()]
print(f"\n3. Comprobante format (A + 12 digits):")
print(f"   Valid: {comp_pattern.sum()}, Invalid: {len(invalid_comp)}")
if not invalid_comp.empty:
    print(f"   Invalid examples: {invalid_comp['Comprobante'].head(5).tolist()}")

# 6. CUIT format check (no hyphens)
cuit_with_hyphens = df_new["Cuit / DNI"].astype(str).str.contains("-", na=False)
print(f"\n4. CUIT without hyphens: {(~cuit_with_hyphens).sum()} OK, {cuit_with_hyphens.sum()} still have hyphens")

# 7. Total column sanity check
total_sum = df_new["Total"].sum()
print(f"\n5. Total sum across all rows: {total_sum:,.2f}")

# 8. Spot check: compare a few rows with the original
print(f"\n6. Spot-check: Compare row 1 transformed vs original")
print(f"   Transformed: {df_new.iloc[0].to_dict()}")

# Load original sheet for comparison
df_orig = pd.read_excel(ORIGINAL, sheet_name="OCT 00", header=None)
orig_data = df_orig.iloc[6:]
orig_data = orig_data[~(orig_data[1].isna() & orig_data[9].isna())]
if not orig_data.empty:
    print(f"   Original (OCT 00 row 1): {orig_data.iloc[0].to_dict()}")

# 9. N/C rows: should NOT have negative totals (they're positive like the original)
nc_rows = df_new[df_new["Tipo"] == "N/C"]
print(f"\n7. N/C (Nota de Crédito) rows: {len(nc_rows)}")
if not nc_rows.empty:
    neg_totals = (nc_rows["Total"] < 0).sum()
    pos_totals = (nc_rows["Total"] >= 0).sum()
    print(f"   Positive totals: {pos_totals}, Negative totals: {neg_totals}")

print(f"\n{'=' * 70}")
print("VALIDATION COMPLETE")
print("=" * 70)
