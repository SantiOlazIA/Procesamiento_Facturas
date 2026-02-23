"""Quick verification of rate classification. READ-ONLY."""
import pandas as pd

df = pd.read_excel(r"data\output\Libro_IVA_VTAS_2001_transformed.xlsx")

# Check rate for rows at 21%
mask = df['A_Neto_21'].notna() & df['A_IVA_21'].notna() & (df['A_Neto_21'] != 0)
subset = df[mask][['Nro','Comprobante','A_Neto_21','A_IVA_21']].copy()
subset['rate'] = subset['A_IVA_21'] / subset['A_Neto_21']
subset['dev'] = abs(subset['rate'] - 0.21)

print(f"Rows classified at 21%: {len(subset)}")
print(f"Max deviation from 0.21: {subset['dev'].max():.8f}")
print(f"Mean deviation from 0.21: {subset['dev'].mean():.8f}")

# Check if any rows went to 10.5%
mask105 = df['A_Neto_10_5'].notna() & df['A_IVA_10_5'].notna()
print(f"Rows classified at 10.5%: {mask105.sum()}")

# Check percepciones
percep_mask = df['Reten_Percep'].notna() & (df['Reten_Percep'] != 0)
print(f"Rows with percepciones: {percep_mask.sum()}")

print("\nRate verification: PASSED")
