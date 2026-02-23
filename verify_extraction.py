import json
import os
import glob

SCRIPT_DIR = r"c:\Users\Tuchi\MiEstudioIA\FCI Santander\Códigos integradores"

files = sorted(glob.glob(os.path.join(SCRIPT_DIR, 'movements_*.json')))

for fpath in files:
    with open(fpath, 'r', encoding='utf-8') as f:
        d = json.load(f)

    fund = d['fund_name']
    init = d.get('initial_balance', 0.0)
    portfolio = d.get('portfolio_cp')
    movements = d['movements']

    print(f"\n{'='*60}")
    print(f"Fund: {fund}")
    print(f"Initial Balance: {init:,.2f}")
    print(f"Portfolio CP (Page 8): {portfolio}")
    print(f"Total movements: {len(movements)}")

    if movements or init > 0:
        running = init
        for m in movements:
            if m['type'] == 'SUSCRIPCION':
                running += m['cp']
            else:
                running -= m['cp']

        print(f"Calculated Final CPs: {running:,.2f}")
        if portfolio is not None:
            diff = abs(running - portfolio)
            status = "MATCH" if diff < 0.99 else f"DIFFERENCE: {diff:,.2f}"
            print(f"vs Portfolio: {portfolio:,.2f} -> {status}")
