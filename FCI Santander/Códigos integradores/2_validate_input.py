"""
FCI Santander - Validacion de Datos Extraidos (Paso 2)

Reads the fund-specific JSON file and validates:
- Date format and chronological order
- No duplicate transactions
- No negative CP/amount values
- Summary statistics
"""
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

    fund_name = data.get('fund_name', 'Unknown')
    movements = data.get('movements', [])
    init_bal = data.get('initial_balance', 0.0)

    log.info(f"  Fondo: {fund_name}")
    log.info(f"  Saldo inicial: {init_bal:,.2f} CPs")
    log.info(f"  Cargados {len(movements)} movimientos")

    if not movements:
        log.warning("  Sin movimientos para validar")
        return True  # Not a fatal error

    issues = 0
    warnings = 0

    # Check 1: Chronological Order
    last_date = None
    for i, m in enumerate(movements):
        try:
            d = datetime.datetime.strptime(m['date'], "%d/%m/%Y")
            if last_date and d < last_date:
                log.error(
                    f"  Orden incorrecto en indice {i}: "
                    f"{m['date']} < {last_date.strftime('%d/%m/%Y')}"
                )
                issues += 1
            last_date = d
        except ValueError:
            log.error(
                f"  Formato de fecha invalido en indice {i}: {m['date']}"
            )
            issues += 1

    # Check 2: Duplicates (by date + type + cp + nro_comp)
    seen = set()
    for i, m in enumerate(movements):
        sig = (
            f"{m['date']}_{m['type']}_{m['cp']}"
            f"_{m.get('nro_comp', '')}"
        )
        if sig in seen:
            log.warning(
                f"  Posible duplicado en indice {i}: "
                f"{m['date']} {m['type']} cp={m['cp']}"
            )
            warnings += 1
        seen.add(sig)

    # Check 3: Negative Values
    for i, m in enumerate(movements):
        if m['cp'] < 0 or m['amount'] < 0:
            log.error(
                f"  Valor negativo en indice {i}: "
                f"cp={m['cp']}, amt={m['amount']}"
            )
            issues += 1

    # Check 4: Summary statistics
    subs = [m for m in movements if m['type'] == 'SUSCRIPCION']
    resc = [m for m in movements if m['type'] == 'RESCATE']
    log.info(
        f"  SUSCRIPCIONES: {len(subs)} "
        f"(CPs: {sum(m['cp'] for m in subs):,.2f})"
    )
    log.info(
        f"  RESCATES:      {len(resc)} "
        f"(CPs: {sum(m['cp'] for m in resc):,.2f})"
    )

    date_range = f"{movements[0]['date']} - {movements[-1]['date']}"
    log.info(f"  Rango: {date_range}")

    if issues == 0 and warnings == 0:
        log.info("  Validacion OK: datos limpios")
    elif issues == 0:
        log.info(f"  Validacion OK con {warnings} advertencia(s)")
    else:
        log.warning(
            f"  Validacion con {issues} error(es) "
            f"y {warnings} advertencia(s)"
        )

    return True


if __name__ == "__main__":
    validate()
