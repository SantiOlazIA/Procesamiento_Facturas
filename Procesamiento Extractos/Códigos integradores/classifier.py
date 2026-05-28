"""
Pipeline de Extractos Bancarios — Clasificador
Aplica BANK_RULES por banco con desambiguación de IVA por contexto.
"""
import os
import sys
from collections import defaultdict

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)
from config import (log, BANK_RULES, CATEGORIES,
                    CAT_IVA_AMBIG, CAT_IVA_COM, CAT_IVA_INT,
                    CAT_COMISIONES, CAT_INTERESES, CAT_NONE, CAT_IIBB)

# Sólo estas categorías "anclan" el contexto para desambiguación de IVA.
# IMP_DBCR y SELLOS NO actualizan el contexto — el IVA debe seguir al COMISION/INTERES.
_CONTEXT_CATS = {CAT_COMISIONES, CAT_IVA_COM, CAT_INTERESES, CAT_IVA_INT}


def _match_rules(description: str, bank: str) -> str:
    """
    Aplica las reglas del banco. Retorna la categoría encontrada o CAT_IVA_AMBIG / CAT_NONE.
    """
    desc_upper = description.upper()
    rules = BANK_RULES.get(bank, [])
    for cat, keywords in rules:
        for kw in keywords:
            if kw.upper() in desc_upper:
                return cat
    return CAT_NONE


def _resolve_iva_ambig(last_cat: str, debit: float, prev_debit: float, bank: str = '?') -> str:
    """
    Desambigua IVA cuando CAT_IVA_AMBIG.
    Método 1: contexto (last_cat).
    Método 2: ratio del monto (10.5% → intereses, 21% → comisiones).
    """
    if last_cat in (CAT_INTERESES, CAT_IVA_INT):
        return CAT_IVA_INT
    if last_cat in (CAT_COMISIONES, CAT_IVA_COM):
        return CAT_IVA_COM

    # Fallback: ratio
    if prev_debit and prev_debit > 0 and debit > 0:
        ratio = debit / prev_debit
        if 0.09 <= ratio <= 0.12:
            return CAT_IVA_INT
        if 0.18 <= ratio <= 0.23:
            return CAT_IVA_COM

    log.warning(f"IVA_AMBIG sin resolver [{bank}]: debit={debit:.2f}, last_cat={last_cat!r} -> Sin clasificar")
    return CAT_NONE


def classify_bank(transactions: list[dict], bank: str) -> list[dict]:
    """
    Clasifica una lista de transacciones de un banco.
    Ordena por fecha antes de clasificar y resetea contexto en cambio de período,
    evitando contaminación cross-month en el estado stateful de IVA.
    """
    # Ordenar cronológicamente para que el contexto IVA fluya en orden correcto
    transactions.sort(key=lambda t: t['date'])

    last_cat    = CAT_NONE
    prev_debit  = 0.0
    last_period = None

    for txn in transactions:
        # Resetear contexto en cruce de período (evita contaminación cross-month)
        current_period = txn.get('period')
        if current_period and current_period != last_period:
            if last_period is not None:
                last_cat   = CAT_NONE
                prev_debit = 0.0
            last_period = current_period

        cat = _match_rules(txn['description'], bank)

        if cat == CAT_IVA_AMBIG:
            resolved = _resolve_iva_ambig(last_cat, txn['debit'], prev_debit, bank)
            txn['category'] = resolved
            # El IVA no cambia last_cat (para no romper contexto del próximo IVA)
        else:
            txn['category'] = cat
            # Solo actualizamos el contexto con categorías "ancla" (COMISIONES/INTERESES)
            if cat in _CONTEXT_CATS:
                last_cat   = cat
                prev_debit = txn['debit']

    return transactions


def classify_all(all_transactions: dict) -> dict:
    """Aplica classify_bank a cada banco."""
    for bank, txns in all_transactions.items():
        classify_bank(txns, bank)
    return all_transactions


# -----------------------------------------------------------------------------
# Reporte de revisión
# -----------------------------------------------------------------------------

def build_review_report(all_transactions: dict) -> str:
    """
    Genera el reporte de revisión de clasificación para mostrar en consola
    antes de generar el Excel.
    """
    lines = []
    lines.append("=" * 68)
    lines.append("  REVISION DE CLASIFICACION")
    lines.append("=" * 68)

    unclassified = []

    for bank in sorted(all_transactions.keys()):
        txns = all_transactions[bank]
        if not txns:
            continue

        # Agrupar por (descripción normalizada, categoría) — mismo desc con distintas cats = filas separadas
        groups = defaultdict(lambda: {'count': 0, 'total': 0.0, 'category': ''})
        for txn in txns:
            desc_key = txn['description'].upper()[:45]
            cat_key  = txn['category']
            key = (desc_key, cat_key)
            groups[key]['count']    += 1
            groups[key]['total']    += txn['debit']
            groups[key]['category']  = cat_key

        lines.append(f"\n{bank}:")
        for desc, info in sorted(groups.items(), key=lambda x: (x[1]['category'], x[0])):
            cat   = info['category']
            count = info['count']
            total = info['total']
            total_fmt = f"${total:>14,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
            if cat == CAT_NONE:
                unclassified.append((bank, desc[0], total, count))
                lines.append(f"  !! {desc[0]:<45}  Sin clasificar")
            else:
                lines.append(
                    f"  OK {desc[0]:<45}  -> {cat:<38}  {count:>3} reg  {total_fmt}"
                )

    if unclassified:
        lines.append("\n" + "-" * 68)
        lines.append("!! SIN CLASIFICAR — editar BANK_RULES en config.py para agregar keywords:")
        for bank, desc, total, count in unclassified:
            total_fmt = f"${total:>12,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
            lines.append(f"   [{bank}]  \"{desc}\"  ({count} reg, {total_fmt})")
    else:
        lines.append("\n  [OK] Todo clasificado correctamente.")

    lines.append("=" * 68)
    return "\n".join(lines)


def build_totals_summary(all_transactions: dict) -> str:
    """
    Genera el resumen de totales por banco y categoría para mostrar
    después de generar el Excel.
    """
    # Calcular totales
    bank_totals = defaultdict(lambda: defaultdict(float))
    for bank, txns in all_transactions.items():
        for txn in txns:
            if txn['category'] != CAT_NONE:
                bank_totals[bank][txn['category']] += txn['debit']

    # Formato
    col_w = 16
    cat_abbrevs = {
        'Comisiones / Gastos bancarios':              'Comisiones',
        'IVA de comisiones':                          'IVA Com.',
        'Imp. sellos':                                'Sellos',
        'Intereses (por descubierto)':                'Intereses',
        'IVA sobre intereses':                        'IVA Int.',
        'Impuestos débitos y créditos (Ley 25.413)':  'Imp.DB/CR',
        'SIRCREB':                                    'SIRCREB',
        'Impuestos IIBB (Ingresos Brutos)':           'IIBB',
    }

    def fmt(v):
        if v == 0:
            return '—'.center(col_w)
        s = f"{v:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        return s.rjust(col_w)

    headers = [ab.center(col_w) for ab in cat_abbrevs.values()]
    lines = []
    lines.append("\n" + "=" * 68)
    lines.append("  RESUMEN DE TOTALES")
    lines.append("=" * 68)
    lines.append(f"{'Banco':<14}" + "".join(headers))
    lines.append("-" * (14 + col_w * len(CATEGORIES)))

    grand = defaultdict(float)
    for bank in sorted(bank_totals.keys()):
        row = f"{bank:<14}"
        for cat in CATEGORIES:
            v = bank_totals[bank].get(cat, 0.0)
            grand[cat] += v
            row += fmt(v)
        lines.append(row)

    lines.append("-" * (14 + col_w * len(CATEGORIES)))
    total_row = f"{'TOTAL':<14}"
    for cat in CATEGORIES:
        total_row += fmt(grand[cat])
    lines.append(total_row)
    lines.append("=" * 68)
    return "\n".join(lines)
