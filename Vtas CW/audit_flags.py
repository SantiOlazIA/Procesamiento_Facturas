import pandas as pd
import numpy as np

def run_audit():
    df = pd.read_excel(r'data\output\All_Sales_Report.xlsx')
    comps = ['A_Neto_21','A_Neto_10_5','B_Neto_21','B_Neto_10_5','IVA_Exento','A_IVA_21','A_IVA_10_5','B_IVA_21','B_IVA_10_5','Reten_Percep']
    df['CompSum'] = df[comps].sum(axis=1)
    
    # 1. Orange Flags (Consistency)
    orange = df[abs(df['Total'] - df['CompSum']) > 0.02]
    print("\n" + "="*60)
    print("ORANGE FLAGS (Total Mismatches)")
    print("="*60)
    if not orange.empty:
        print(orange[['Nro', 'Fecha', 'Total', 'CompSum', 'Ref. Origen']])
    else:
        print("None found.")

    # 2. Yellow Flags (Rates & Percep)
    yellow_results = []
    for idx, row in df.iterrows():
        reasons = []
        # Check A21
        if row['A_Neto_21'] != 0:
            rate = abs(row['A_IVA_21'] / row['A_Neto_21'])
            if abs(rate - 0.21) > 0.01:
                reasons.append(f"A21 Rate: {rate:.4f}")
        # Check A10.5
        if row['A_Neto_10_5'] != 0:
            rate = abs(row['A_IVA_10_5'] / row['A_Neto_10_5'])
            if abs(rate - 0.105) > 0.01:
                reasons.append(f"A105 Rate: {rate:.4f}")
        # High Percep
        total_neto = row['A_Neto_21'] + row['A_Neto_10_5'] + row['B_Neto_21'] + row['B_Neto_10_5']
        if abs(total_neto) > 0.1:
            p_rate = abs(row['Reten_Percep'] / total_neto)
            if p_rate > 0.10:
                reasons.append(f"High Percep: {p_rate:.2%}")
        
        if reasons:
            yellow_results.append({
                'Nro': row['Nro'],
                'Fecha': row['Fecha'],
                'Reason': " | ".join(reasons),
                'Src': row['Ref. Origen']
            })

    print("\n" + "="*60)
    print("YELLOW FLAGS (IVA Rates / Perceptions)")
    print("="*60)
    if yellow_results:
        print(pd.DataFrame(yellow_results))
    else:
        print("None found.")

if __name__ == "__main__":
    run_audit()
