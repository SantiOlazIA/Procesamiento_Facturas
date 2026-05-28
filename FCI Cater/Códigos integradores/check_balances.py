import json
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
JSON_PATH = os.path.join(SCRIPT_DIR, 'movements.json')
# Hardcoded initial balance from prepare_test.py
INITIAL_CP = 5909501.57
INITIAL_AMT = 685714581.66 

def get_final_balances():
    if not os.path.exists(JSON_PATH):
        print("El archivo JSON no existe.")
        return

    with open(JSON_PATH, 'r', encoding='utf-8') as f:
        movs = json.load(f)
        
    # We need to filter for >= Oct 1st 2024
    # And apply the same logic as process_ledger
    
    current_cp = INITIAL_CP
    current_amt = INITIAL_AMT # This tracks the "Saldo en $" logic: Init + SubscriptionAmt + RescueProfit - RescueAmt
    
    # Actually, Saldo en $ (AE) logic in process_ledger:
    # AE = AE_prev + AB + AD
    # AB for Sub = Amount
    # AB for Rescue = -Amount consumed * Quote (approx Cost)
    # AD for Rescue = Profit (Amount - Cost)
    #
    # So effectively:
    # AE_new = AE_old + (Sub_Amount) + (-Cost + Profit)
    # Since Profit = Real_Amount - Cost
    # Then -Cost + Profit = -Cost + (Real_Amount - Cost) ... wait.
    #
    # Let's look at the formula:
    # Rescue:
    #   AB (Importe Cta Cte) = -Consume * Quote (This is the COST basis of the shares sold)
    #   AD (Renta) = Real Sale Amount - Cost Basis
    #   AE = AE_prev + AB + AD
    #      = AE_prev - Cost + (SaleAmount - Cost) ??? No, AD is H11...
    #
    # Wait, let's verify AD formula in process_ledger.
    # ws[f'AD{r_c}'] = f'=+H{current_asiento_row + 3}'
    # H{row+3} (Rentas) = G{row+1} (Caja) - H{row+2} (Cost)
    # So AD = SaleAmount - Cost
    #
    # AB is -Cost.
    # So AB + AD = -Cost + (SaleAmount - Cost) = SaleAmount - 2*Cost ... This looks wrong if AE is supposed to be "Saldo en $".
    #
    # Let's re-read process_ledger logic for AE
    # ws[f'AE{r_c}'] = f'=AE{r_c-1}+AB{r_c}+AD{r_c}'
    #
    # Verification:
    # Subscription: AB = Amount, AD = 0. -> AE += Amount. Correct.
    # Rescue: 
    #   AB = -Cost (Quote * CP)
    #   AD = SaleAmount - Cost
    #   AE += -Cost + (SaleAmount - Cost) = SaleAmount - 2*Cost.
    #
    # This implies AE is NOT tracking the simple "Cash Value" of the fund.
    # If AE represents "Saldo en $", it usually means "Valuation of remaining shares".
    # Valuation = Remaining CP * Current Price.
    #
    # BUT, if the formula is AE += AB + AD...
    # Let's perform the calculation exactly as the script does it.
    
    print(f"--- BALANCES ESTIMADOS ---")
    print(f"Saldo Inicial CP: {INITIAL_CP:,.2f}")
    print(f"Saldo Inicial $:  {INITIAL_AMT:,.2f}")
    
    # We can just read the final CP from the Excel using data_only=True (since CP doesn't depend on complex AD formulas as much, usually just Sum(Z))
    # Or just calculate CP balance from JSON.
    
    simulated_cp = INITIAL_CP
    
    # Filter 
    import datetime
    start_date = datetime.datetime(2024, 10, 1)
    
    filtered_movs = []
    for m in movs:
         try:
            d = datetime.datetime.strptime(m['date'], "%d/%m/%Y")
            if d >= start_date: filtered_movs.append(m)
         except: pass
         
    for m in filtered_movs:
        if m['type'] == 'COMPRA':
            simulated_cp += m['cp']
        else:
            simulated_cp -= m['cp']
            
    # To calculate AE (Saldo en $), we need the full FIFO simulation because AB and AD depend on the cost of the shares sold.
    # AE_new = AE_prev + AB + AD
    # For SUBSCRIPTION: AB = Amount, AD = 0. So AE += Amount.
    # For REDEMPTION: AB = -ConsumedCP * CostPrice. AD = (SalePrice - CostPrice) * ConsumedCP.
    # So AE += (-ConsumedCP * CostPrice) + (SalePrice*ConsumedCP - CostPrice*ConsumedCP)
    # AE += ConsumedCP * (SalePrice - 2*CostPrice) ??? This formula in Excel seems odd if AE is meant to be book value.
    #
    # Wait, let's look at the Excel formula for AD again from process_ledger.py
    # ws[f'AD{r_c}'] = f'=+H{current_asiento_row + 3}'
    # And H{row+3} is the PROFIT line in the accounting entry.
    # Profit = SaleAmount - CostBasis.
    #
    # And AB is the "Importe Cta Cte" which for a sale is usually the SaleAmount?
    # In process_ledger.py:
    # ws[f'AB{r_c}'] = -consume * quote_val  (This is SaleAmount, if quote_val is the current price)
    # Quote Val definition: quote_val = amt / cp (Current Price)
    #
    # So AB = -SaleAmount.
    #
    # And AE formula: AE = AE_prev + AB + AD
    # AE = AE_prev + (-SaleAmount) + (SaleAmount - CostBasis)
    # AE = AE_prev - CostBasis.
    #
    # This makes perfect sense! AE tracks the *Book Value* (Cost Basis) of the remaining investment.
    # When you subscribe, you add CostBasis (Amount).
    # When you redeem, you reduce CostBasis by the CostBasis of the shares sold.
    #
    # So to calculate Final AE, we just need to track the Cost Basis of the *remaining* shares.
    # This requires FIFO.
    
    print("Simulando FIFO para calcular Saldo en $ (Costo Historico)...")
    
    inventory = [] # List of (cp, price) tuples
    # Initial Inventory
    initial_price = INITIAL_AMT / INITIAL_CP
    inventory.append({'cp': INITIAL_CP, 'price': initial_price})
    
    import datetime
    start_date = datetime.datetime(2024, 10, 1)
    
    for m in movs:
        try:
            d = datetime.datetime.strptime(m['date'], "%d/%m/%Y")
            if d < start_date: continue
        except: continue
        
        if m['type'] == 'COMPRA':
            price = m['amount'] / m['cp']
            inventory.append({'cp': m['cp'], 'price': price})
        else: # VENTA
            needed = m['cp']
            while needed > 0.000001 and inventory:
                head = inventory[0]
                if head['cp'] > needed:
                    head['cp'] -= needed
                    needed = 0
                else:
                    needed -= head['cp']
                    inventory.pop(0)

    # Calculate remaining cost basis
    final_book_value = 0.0
    final_cp = 0.0
    for item in inventory:
        final_book_value += item['cp'] * item['price']
        final_cp += item['cp']

    print(f"Saldo Final CP (FIFO): {final_cp:,.2f}")
    print(f"Saldo Final en $ (Costo Historico): {final_book_value:,.2f}")

if __name__ == "__main__":
    get_final_balances()
