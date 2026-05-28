"""
Pipeline de Extractos Bancarios — Verificación de Totales
Extrae los totales oficiales reportados en cada extracto PDF y los compara
con los totales que extrajo el pipeline. Informa discrepancias sin abortar.
"""
import os
import re
import sys
import pdfplumber
from collections import defaultdict

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)
from config import (log, INPUT_DIR, FILENAME_PATTERN,
                    parse_argentine_number,
                    CAT_IMP_DBCR, CAT_SIRCREB, CAT_COMISIONES,
                    CAT_IVA_COM, CAT_IVA_INT, CAT_INTERESES, CAT_SELLOS)


# ─────────────────────────────────────────────────────────────────────────────
# Tipo de dato: total oficial
# ─────────────────────────────────────────────────────────────────────────────

def _find_amount(pattern: str, text: str, flags=re.IGNORECASE) -> float | None:
    """
    Busca `pattern` seguido (en la misma línea) del PRIMER monto argentino.
    Usa match lazy para no saltar por encima de otros números en la misma línea.
    El monto debe tener coma decimal (p.ej. 1.430.285,96) para no confundirse
    con fechas como '01/26' o números de cuenta.
    """
    m = re.search(
        pattern + r'[^$\n]*?\$?\s*(-?\d[\d.]*,\d{2}-?)',
        text, flags
    )
    if m:
        return abs(parse_argentine_number(m.group(1)))
    return None


def _get_full_text(pdf_path: str) -> str:
    """Extrae todo el texto de un PDF como un solo string."""
    parts = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            parts.append(page.extract_text() or '')
    return '\n'.join(parts)


# ─────────────────────────────────────────────────────────────────────────────
# Extractores de totales oficiales por banco
# Retornan dict {category: (label, official_amount)}
# ─────────────────────────────────────────────────────────────────────────────

def _totals_bna(text: str) -> dict:
    totals = {}
    # BNA: "TOTAL GRAV. LEY 25413 DEBITOS MES DE FEBRERO: $920.321,18"
    # Los "DEBITOS" y "CREDITOS" son ambos cargos al cliente (impuesto sobre cada lado)
    deb = _find_amount(r'TOTAL\s+GRAV\.\s+LEY\s+25413\s+DEBITOS', text)
    cred = _find_amount(r'TOTAL\s+GRAV\.\s+LEY\s+25413\s+CREDITOS', text)
    if deb is not None or cred is not None:
        totals[CAT_IMP_DBCR] = ('Grav. Ley 25413 (Débitos + Créditos)',
                                 (deb or 0) + (cred or 0))
    v = _find_amount(r'TOTAL\s+REG\s+REC\.\s+SIRCREB', text)
    if v is not None:
        totals[CAT_SIRCREB] = ('SIRCREB', v)
    return totals


def _totals_bsj(text: str) -> dict:
    totals = {}
    # BSJ "CREDITO IMPUESTO LEY 25413" = impuesto sobre créditos recibidos (cargo al cliente)
    deb  = _find_amount(r'TOTAL\s+DEBITO\s+IMPUESTO\s+LEY\s+25413', text)
    cred = _find_amount(r'TOTAL\s+CREDITO\s+IMPUESTO\s+LEY\s+25413', text)
    if deb is not None or cred is not None:
        totals[CAT_IMP_DBCR] = ('Imp. Ley 25413 (Débitos + Créditos)',
                                 (deb or 0) + (cred or 0))
    v = _find_amount(r'TOTAL\s+SIRCREB', text)
    if v is not None:
        totals[CAT_SIRCREB] = ('SIRCREB', v)
    return totals


def _totals_comafi(text: str) -> dict:
    totals = {}
    # COMAFI: "Ley 25413 Sobre Débitos Tasa general 74.536,00 0,600% 447,22 0,00 447,22"
    # La línea tiene: base, tasa%, impuesto, cero, impuesto. Queremos el ÚLTIMO monto no cero.
    m = re.search(r'Ley\s+25413[^\n]*', text, re.IGNORECASE)
    if m:
        amounts = re.findall(r'\d[\d.]*,\d{2}', m.group(0))
        nonzero = [a for a in amounts if parse_argentine_number(a) > 0]
        if nonzero:
            v = abs(parse_argentine_number(nonzero[-1]))
            totals[CAT_IMP_DBCR] = ('Ley 25413', v)
    return totals


def _totals_galicia_mas(text: str) -> dict:
    totals = {}
    # GALICIA MAS: pdfplumber extrae las líneas de totales intercalando "PERIODO COMPRENDIDO..."
    # (con el importe) justo ANTES de la etiqueta. Buscamos el último par
    # PERIODO→"TOTAL MENSUAL RETENCION...SOBRE DEBITOS" para obtener el total mensual de febrero.
    matches = list(re.finditer(
        r'PERIODO\s+COMPRENDIDO[^\n]+\s(\d[\d.]*,\d{2})\s*\n\s*'
        r'TOTAL\s+MENSUAL\s+RETENCI[OÓ]N\s+IMPUESTO\s+LEY\s+25[^\n]*SOBRE\s+DEBITOS',
        text, re.IGNORECASE
    ))
    if matches:
        v = abs(parse_argentine_number(matches[-1].group(1)))
        if v > 0:
            totals[CAT_IMP_DBCR] = ('Retención Ley 25413 Sobre Débitos', v)
    return totals


def _totals_icbc(text: str) -> dict:
    totals = {}
    # TOT.IMP.LEY COMP es el neto (bruto - crédito computable por pago a cuenta)
    v = _find_amount(r'TOT\.IMP\.LEY\s+COMP\.', text)
    if v is not None:
        totals[CAT_IMP_DBCR + '|net'] = ('Tot. Imp. Ley 25413 (computable neto)', v)
    return totals


def _totals_supervielle(text: str) -> dict:
    totals = {}
    v = _find_amount(r'Imp\s+Ley\s+25413\s+s/Debitos', text)
    if v is not None:
        totals[CAT_IMP_DBCR] = ('Imp. Ley 25413 s/Débitos', v)
    return totals


def _totals_santander(text: str) -> dict:
    totals = {}
    # Santander: "CREDITOS" = impuesto sobre créditos (cargo al cliente, igual que BSJ)
    # Sumamos todas las apariciones de ambas líneas (pueden venir de 2 cuentas: pesos + USD)
    matches_cred = re.findall(
        r'Total\s+retencion\s+impuesto\s+ley\s+25[\. ]?413\s+por\s+CREDITOS[^$\n]*\$?\s*(-?\d[\d.]*,\d{2})',
        text, re.IGNORECASE
    )
    matches_deb = re.findall(
        r'Total\s+retencion\s+impuesto\s+ley\s+25[\. ]?413\s+por\s+DEBITOS[^$\n]*\$?\s*(-?\d[\d.]*,\d{2})',
        text, re.IGNORECASE
    )
    total_imp = (
        sum(abs(parse_argentine_number(m)) for m in matches_cred) +
        sum(abs(parse_argentine_number(m)) for m in matches_deb)
    )
    if total_imp > 0:
        totals[CAT_IMP_DBCR] = ('Ley 25413 (Débitos + Créditos, todas cuentas)', total_imp)
    v = _find_amount(r'Total\s+Retenci[oó]n\s+R[eé]gimen\s+de\s+Recaudaci[oó]n\s+SIRCREB', text)
    if v is not None:
        totals[CAT_SIRCREB] = ('SIRCREB', v)
    return totals


TOTAL_EXTRACTORS = {
    'BNA':         _totals_bna,
    'BSJ':         _totals_bsj,
    'COMAFI':      _totals_comafi,
    'GALICIA MAS': _totals_galicia_mas,
    'ICBC':        _totals_icbc,
    'SUPERVIELLE': _totals_supervielle,
    'SANTANDER':   _totals_santander,
    # BBVA y GALICIA: no tienen resumen extraíble con las herramientas actuales
}


# ─────────────────────────────────────────────────────────────────────────────
# Calcular totales extraídos por categoría
# ─────────────────────────────────────────────────────────────────────────────

def _compute_extracted_totals(transactions: list[dict]) -> dict:
    """
    Calcula totales por categoría para un banco.
    También separa débitos de créditos para IMP_DBCR.
    """
    totals = defaultdict(float)
    for txn in transactions:
        cat = txn['category']
        if not cat or cat == 'Sin clasificar':
            continue
        totals[cat] += txn['debit']
        # Separar créditos de IMP_DBCR (para comparar contra oficial)
        if CAT_IMP_DBCR in cat and txn['credit'] > 0:
            totals[CAT_IMP_DBCR + '|cred'] += txn['credit']
    return dict(totals)


# ─────────────────────────────────────────────────────────────────────────────
# Comparar y generar reporte
# ─────────────────────────────────────────────────────────────────────────────

TOLERANCE = 1.00   # diferencia máxima admisible en pesos (ajustar si hay redondeos)
TOLERANCE_PCT = 0.01  # 1% — para importes grandes

def _fmt(v: float) -> str:
    s = f"{v:>14,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    return s


def verify_all(all_transactions: dict,
               input_dir: str = INPUT_DIR,
               period_filter: str = None) -> str:
    """
    Para cada banco verificable, extrae los totales oficiales del PDF
    y los compara con los totales del pipeline.
    Retorna un string con el reporte completo.
    """
    lines = []
    lines.append("\n" + "=" * 68)
    lines.append("  VERIFICACION DE TOTALES vs. EXTRACTOS OFICIALES")
    lines.append("=" * 68)

    # Encontrar PDFs
    pdf_map = {}
    for fname in os.listdir(input_dir):
        m = FILENAME_PATTERN.match(fname)
        if not m:
            continue
        period, bank = m.group(1), m.group(2).strip().upper()
        if period_filter and period != period_filter:
            continue
        pdf_map[bank] = (period, os.path.join(input_dir, fname))

    any_discrepancy = False

    for bank in sorted(all_transactions.keys()):
        extractor_fn = TOTAL_EXTRACTORS.get(bank)
        if not extractor_fn:
            lines.append(f"\n{bank}: [sin verificación disponible]")
            continue

        pdf_info = pdf_map.get(bank)
        if not pdf_info:
            lines.append(f"\n{bank}: [PDF no encontrado]")
            continue

        _, pdf_path = pdf_info
        try:
            text = _get_full_text(pdf_path)
            official = extractor_fn(text)
        except Exception as e:
            lines.append(f"\n{bank}: [error al leer PDF: {e}]")
            continue

        if not official:
            lines.append(f"\n{bank}: [totales oficiales no encontrados en PDF]")
            continue

        extracted = _compute_extracted_totals(all_transactions[bank])

        lines.append(f"\n{bank}:")
        lines.append(f"  {'Concepto':<45}  {'Oficial':>14}  {'Extraído':>14}  {'Diff':>12}  Estado")
        lines.append("  " + "-" * 96)

        bank_ok = True
        for key, (label, official_val) in sorted(official.items()):
            # Mapear clave oficial → valor en extracted
            if key == CAT_IMP_DBCR + '|net':
                # ICBC: el PDF reporta el neto = debitos - ajuste crédito.
                # Hacemos lo mismo: sumamos débitos y restamos créditos de CAT_IMP_DBCR.
                bruto    = extracted.get(CAT_IMP_DBCR, 0.0)
                cred_adj = extracted.get(CAT_IMP_DBCR + '|cred', 0.0)
                extracted_val = bruto - cred_adj
            else:
                extracted_val = extracted.get(key, 0.0)

            diff = official_val - extracted_val
            abs_diff = abs(diff)

            # Determinar si es discrepancia (OR: cualquier diferencia material dispara alarma)
            is_discrepancy = (
                abs_diff > TOLERANCE or
                (official_val > 0 and abs_diff / official_val > TOLERANCE_PCT)
            )

            status = "[OK]" if not is_discrepancy else "[!!]"
            if is_discrepancy:
                bank_ok = False
                any_discrepancy = True

            lines.append(
                f"  {label:<45}  {_fmt(official_val)}  {_fmt(extracted_val)}"
                f"  {_fmt(diff)}  {status}"
            )

        if bank_ok:
            lines.append("  [OK] Todo correcto para este banco.")

    lines.append("\n" + "=" * 68)
    if any_discrepancy:
        lines.append("  [!!] ATENCIÓN: hay diferencias. Revisar extracto y keywords.")
    else:
        lines.append("  [OK] Todos los totales verificados coinciden.")
    lines.append("=" * 68)

    return "\n".join(lines)
