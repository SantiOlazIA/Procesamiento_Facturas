import json
import os
import sys
import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(SCRIPT_DIR)
from config import JSON_DATA_PATH, log

def validate():
    log.info("=" * 50)
    log.info("PASO 2: Validacion de Datos")
    log.info("=" * 50)
    
    if not os.path.exists(JSON_DATA_PATH):
        log.error(f"Archivo de datos no encontrado: {JSON_DATA_PATH}")
        return False
        
    with open(JSON_DATA_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    if not data:
        log.warning("Archivo de datos vacio")
        return False
        
    log.info(f"Cargados {len(data)} movimientos")
    
    issues = 0
    warnings = 0
    
    # Check 1: Chronological Order
    last_date = None
    for i, m in enumerate(data):
        try:
            d = datetime.datetime.strptime(m['date'], "%d/%m/%Y")
            if last_date and d < last_date:
                log.error(f"  Orden incorrecto en indice {i}: {m['date']} < {last_date.strftime('%d/%m/%Y')}")
                issues += 1
            last_date = d
        except ValueError:
            log.error(f"  Formato de fecha invalido en indice {i}: {m['date']}")
            issues += 1
            
    # Check 2: Duplicates
    seen = set()
    for i, m in enumerate(data):
        sig = f"{m['date']}_{m['type']}_{m['cp']}_{m['amount']}"
        if sig in seen:
            log.warning(f"  Posible duplicado en indice {i}: {m['date']} {m['type']} cp={m['cp']}")
            warnings += 1
        seen.add(sig)
        
    # Check 3: Negative Values
    for i, m in enumerate(data):
        if m['cp'] < 0 or m['amount'] < 0:
            log.error(f"  Valor negativo en indice {i}: cp={m['cp']}, amt={m['amount']}")
            issues += 1
    
    # Check 4: Summary statistics
    compras = [m for m in data if m['type'] == 'COMPRA']
    ventas = [m for m in data if m['type'] == 'VENTA']
    log.info(f"  COMPRAS: {len(compras)} (CPs: {sum(m['cp'] for m in compras):,.2f})")
    log.info(f"  VENTAS:  {len(ventas)} (CPs: {sum(m['cp'] for m in ventas):,.2f})")
    
    date_range = f"{data[0]['date']} - {data[-1]['date']}"
    log.info(f"  Rango: {date_range}")
            
    if issues == 0 and warnings == 0:
        log.info("  Validacion OK: datos limpios")
    elif issues == 0:
        log.info(f"  Validacion OK con {warnings} advertencia(s)")
    else:
        log.warning(f"  Validacion con {issues} error(es) y {warnings} advertencia(s)")
    
    return True

if __name__ == "__main__":
    validate()
