"""
Pipeline de Extractos Bancarios — Extractores PDF
Un parser por banco. Todos retornan List[dict] con make_transaction().
"""
import os
import re
import sys
import pdfplumber

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)
from config import (log, FILENAME_PATTERN, INPUT_DIR,
                    parse_argentine_number, normalize_date, make_transaction)

# ─────────────────────────────────────────────────────────────────────────────
# Helpers comunes
# ─────────────────────────────────────────────────────────────────────────────

# Regex que identifica un número en formato argentino (con posible signo al final)
# \d* permite casos como ',73' (menos de un peso)
_NUM_RE = re.compile(r'-?\d*(?:\.\d{3})*,\d{2}-?')


def _find_numbers(line: str):
    """Retorna lista de floats encontrados en la línea (formato argentino)."""
    return [parse_argentine_number(m) for m in _NUM_RE.findall(line)]


def _extract_text_pages(pdf_path: str) -> list[str]:
    """Extrae texto de todas las páginas de un PDF. Retorna [] si el PDF está corrupto."""
    pages = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text() or ""
                pages.append(text)
    except Exception as e:
        log.error(f"Error al abrir PDF {pdf_path}: {e}")
    return pages


# ─────────────────────────────────────────────────────────────────────────────
# COMAFI
# ─────────────────────────────────────────────────────────────────────────────
def parse_comafi(pdf_path: str, period: str) -> list[dict]:
    """
    Formato: Fecha | Conceptos | Referencias | Débitos | Créditos | Saldo
    El saldo aparece solo en la última fila del bloque del día.
    """
    fname = os.path.basename(pdf_path)
    year = int(period[:4])
    results = []
    pages = _extract_text_pages(pdf_path)

    # Patrón de fecha: DD/MM/YY al inicio de línea
    date_re = re.compile(r'^(\d{2}/\d{2}/\d{2})\s+(.+)')

    in_detail = False
    for page_text in pages:
        for line in page_text.splitlines():
            stripped = line.strip()
            su = stripped.upper()
            if not stripped:
                continue
            # Detectar inicio y fin de la sección de movimientos
            if 'DETALLE DE MOVIMIENTOS' in su:
                in_detail = True
                continue
            if in_detail and any(x in su for x in
                                 ['IMPUESTOS DEBITADOS', 'SIN MOVIMIENTOS',
                                  'SALDO FINAL', 'TOTAL MOVIMIENTOS']):
                in_detail = False
                continue
            if not in_detail:
                continue

            m = date_re.match(stripped)
            if not m:
                continue

            date_str, rest = m.group(1), m.group(2).strip()
            date = normalize_date(date_str, year)

            # Extraer descripción (todo antes del primer número)
            desc_match = re.match(r'^(.*?)(?=\d{1,3}(?:\.\d{3})*,\d{2})', rest)
            description = desc_match.group(1).strip() if desc_match else rest.strip()
            # Limpiar código de referencia al final de la descripción
            description = re.sub(r'\s+\d{7,}\s*$', '', description).strip()

            # Filtrar líneas que no son transacciones
            if any(x in description.upper() for x in ['SALDO ANTERIOR', 'SALDO FINAL',
                                                       'TOTAL MOVIMIENTOS']):
                continue

            nums = _find_numbers(rest)
            if not nums:
                continue

            debit = nums[0] if nums[0] > 0 else 0.0
            credit = 0.0

            results.append(make_transaction(
                'COMAFI', date, description, debit, credit, period, fname
            ))

    log.debug(f"  COMAFI: {len(results)} transacciones extraídas")
    return results


# ─────────────────────────────────────────────────────────────────────────────
# SUPERVIELLE
# ─────────────────────────────────────────────────────────────────────────────
def parse_supervielle(pdf_path: str, period: str) -> list[dict]:
    """
    Formato: DD/MM/YY | Descripción | Voucher | Monto | Saldo
    Skip: líneas "Operación 999999999 Generada el..."
    """
    fname = os.path.basename(pdf_path)
    year = int(period[:4])
    results = []
    pages = _extract_text_pages(pdf_path)

    date_re = re.compile(r'^(\d{2}/\d{2}/\d{2})\s+(.+)')
    skip_re = re.compile(r'Operaci[oó]n\s+\d+\s+Generada', re.IGNORECASE)

    for page_text in pages:
        for line in page_text.splitlines():
            stripped = line.strip()
            if not stripped or skip_re.search(stripped):
                continue

            m = date_re.match(stripped)
            if not m:
                continue

            date_str, rest = m.group(1), m.group(2).strip()
            date = normalize_date(date_str, year)
            nums = _find_numbers(rest)

            desc_match = re.match(r'^(.*?)(?=\d{1,3}(?:\.\d{3})*,\d{2})', rest)
            description = desc_match.group(1).strip() if desc_match else rest.strip()
            # Quitar código de voucher numérico al final de la descripción
            description = re.sub(r'\s+\d{8,}\s*$', '', description).strip()

            if not nums or not description:
                continue

            # Primer número = monto de movimiento; segundo = saldo (ignorar)
            amount = nums[0]
            debit  = abs(amount) if amount > 0 else 0.0
            credit = 0.0
            # Si la línea no tiene saldo negativo marcador, puede ser crédito
            # Supervielle: saldos negativos terminan en '-'
            # La convención en los extractos: el monto es siempre débito aquí
            # (créditos son entradas de dinero, débitos son salidas)

            results.append(make_transaction(
                'SUPERVIELLE', date, description, debit, credit, period, fname
            ))

    log.debug(f"  SUPERVIELLE: {len(results)} transacciones extraídas")
    return results


# ─────────────────────────────────────────────────────────────────────────────
# BNA
# ─────────────────────────────────────────────────────────────────────────────
def parse_bna(pdf_path: str, period: str) -> list[dict]:
    """
    Formato: Fecha | Movimientos | Comprob. | Débitos | Créditos | Saldo
    Skip: líneas TRANSPORTE (carry-forward).
    """
    fname = os.path.basename(pdf_path)
    year = int(period[:4])
    results = []
    pages = _extract_text_pages(pdf_path)

    date_re = re.compile(r'^(\d{2}/\d{2}/\d{2})\s+(.+)')

    in_detail = False
    for page_text in pages:
        for line in page_text.splitlines():
            # BNA marca líneas de continuación con "____ " al inicio — quitarlo
            stripped = re.sub(r'^[_\s]+', '', line.strip())
            su = stripped.upper()
            if not stripped:
                continue

            if not in_detail and 'FECHA' in su and 'MOVIMIENTOS' in su and 'DEBITOS' in su:
                in_detail = True
                continue
            if in_detail and any(x in su for x in
                                 ['TOTAL DEBITOS', 'SALDO AL', 'INFORMACION ADICIONAL']):
                in_detail = False
                continue
            if not in_detail:
                continue
            # Skip carry-forward
            if 'TRANSPORTE' in su:
                continue

            m = date_re.match(stripped)
            if not m:
                continue

            date_str, rest = m.group(1), m.group(2).strip()
            date = normalize_date(date_str, year)
            nums = _find_numbers(rest)

            desc_match = re.match(r'^(.*?)(?=\d{1,3}(?:\.\d{3})*,\d{2})', rest)
            description = desc_match.group(1).strip() if desc_match else rest.strip()
            # Quitar número de comprobante al final
            description = re.sub(r'\s+\d{4,}\s*$', '', description).strip()

            if not nums or not description:
                continue

            debit  = nums[0] if nums[0] > 0 else 0.0
            credit = 0.0

            results.append(make_transaction(
                'BNA', date, description, debit, credit, period, fname
            ))

    log.debug(f"  BNA: {len(results)} transacciones extraídas")
    return results


# ─────────────────────────────────────────────────────────────────────────────
# BBVA
# ─────────────────────────────────────────────────────────────────────────────
def parse_bbva(pdf_path: str, period: str) -> list[dict]:
    """
    Formato: DD/MM ORIGEN CONCEPTO DEBITO CREDITO SALDO
    Fecha: DD/MM (sin año). Algunas líneas tienen prefijo 'D ' antes del concepto.
    """
    fname = os.path.basename(pdf_path)
    year = int(period[:4])
    results = []
    pages = _extract_text_pages(pdf_path)

    # DD/MM al inicio
    date_re = re.compile(r'^(\d{2}/\d{2})\s+(.+)')

    in_detail = False
    for page_text in pages:
        for line in page_text.splitlines():
            stripped = line.strip()
            su = stripped.upper()
            if not stripped:
                continue

            if 'SALDO ANTERIOR' in su or ('FECHA' in su and 'CONCEPTO' in su and 'DEBITO' in su):
                in_detail = True
                continue
            if in_detail and any(x in su for x in
                                 ['TOTAL MOVIMIENTOS', 'SALDO AL']):
                in_detail = False
                continue
            if not in_detail:
                continue

            m = date_re.match(stripped)
            if not m:
                continue

            date_str, rest = m.group(1), m.group(2).strip()
            date = normalize_date(date_str, year)

            # Remover prefijo de origen (una sola letra + espacio, ej. "D ")
            rest = re.sub(r'^[A-Z]\s+', '', rest).strip()

            nums = _find_numbers(rest)
            desc_match = re.match(r'^(.*?)(?=\d{1,3}(?:\.\d{3})*,\d{2}|-\d)', rest)
            description = desc_match.group(1).strip() if desc_match else rest.strip()
            # Limpiar fecha auxiliar al final (ej. "01/26")
            description = re.sub(r'\s+\d{2}/\d{2}\s*$', '', description).strip()

            if not nums or not description:
                continue

            # En BBVA los débitos son negativos en el raw
            amount = nums[0]
            debit  = abs(amount) if amount < 0 else 0.0
            credit = amount if amount > 0 else 0.0

            results.append(make_transaction(
                'BBVA', date, description, debit, credit, period, fname
            ))

    log.debug(f"  BBVA: {len(results)} transacciones extraídas")
    return results


# ─────────────────────────────────────────────────────────────────────────────
# ICBC
# ─────────────────────────────────────────────────────────────────────────────
def parse_icbc(pdf_path: str, period: str) -> list[dict]:
    """
    Formato: DD-MM CONCEPTO F.VALOR COMPROBANTE ORIGEN CANAL DEBITOS CREDITOS SALDOS
    Débitos terminan en '-' (ej. 52.000,00-). Páginas duplicadas → deduplicar.
    """
    fname = os.path.basename(pdf_path)
    year = int(period[:4])
    results = []
    seen = set()
    pages = _extract_text_pages(pdf_path)

    # DD-MM al inicio
    date_re = re.compile(r'^(\d{2}-\d{2})\s+(.+)')

    in_detail = False
    for page_text in pages:
        for line in page_text.splitlines():
            stripped = line.strip()
            su = stripped.upper()
            if not stripped:
                continue

            if 'FECHA' in su and 'CONCEPTO' in su:
                in_detail = True
                continue
            if in_detail and any(x in su for x in
                                 ['TOT.IMP.LEY', 'TOTAL MOVIMIENTOS', 'SALDO FINAL']):
                in_detail = False
                continue
            if not in_detail:
                continue

            m = date_re.match(stripped)
            if not m:
                continue

            date_str, rest = m.group(1), m.group(2).strip()
            date = normalize_date(date_str, year)

            # Números: buscar con sufijo '-' también
            nums_raw = re.findall(r'\d{1,3}(?:\.\d{3})*,\d{2}-?', rest)
            if not nums_raw:
                continue

            amount_raw = nums_raw[0]
            is_debit = amount_raw.endswith('-')
            amount = parse_argentine_number(amount_raw)

            desc_match = re.match(r'^(.*?)(?=\d{1,3}(?:\.\d{3})*,\d{2})', rest)
            description = desc_match.group(1).strip() if desc_match else rest.strip()
            # Limpiar códigos internos al final
            description = re.sub(r'\s+\d{4,}\s+.*$', '', description).strip()
            description = re.sub(r'\s+[A-Z]{3,}\s*$', '', description).strip()

            if not description:
                continue

            # Deduplicar páginas duplicadas
            key = (date, description, amount_raw)
            if key in seen:
                continue
            seen.add(key)

            debit  = abs(amount) if is_debit else 0.0
            credit = abs(amount) if not is_debit else 0.0

            results.append(make_transaction(
                'ICBC', date, description, debit, credit, period, fname
            ))

    log.debug(f"  ICBC: {len(results)} transacciones extraídas")
    return results


# ─────────────────────────────────────────────────────────────────────────────
# BSJ
# ─────────────────────────────────────────────────────────────────────────────
def parse_bsj(pdf_path: str, period: str) -> list[dict]:
    """
    Formato: DD/MM/YY CONCEPTO NRO.XXXXXXXXXX DEBITO SALDO
    El voucher NRO.XXXXXXXXXX está embebido en la descripción.
    Skip: SUBTOTAL, T R A N S P O R T E.
    """
    fname = os.path.basename(pdf_path)
    year = int(period[:4])
    results = []
    pages = _extract_text_pages(pdf_path)

    date_re = re.compile(r'^(\d{2}/\d{2}/\d{2})\s+(.+)')
    voucher_re = re.compile(r'\s+NRO\.\d+', re.IGNORECASE)
    skip_words = ['SUBTOTAL', 'T R A N S P O R T E', 'TRANSPORTE', 'SALDO ANTERIOR',
                  'SALDO AL', 'FECHA ', 'AV.', 'RN 40', 'RUTA']

    in_detail = False
    for page_text in pages:
        for line in page_text.splitlines():
            stripped = line.strip()
            su = stripped.upper()
            if not stripped:
                continue

            # Detectar inicio/fin ANTES de aplicar skip_words
            if 'FECHA' in su and 'CONCEPTO' in su and 'DEBITO' in su:
                in_detail = True
                continue
            if in_detail and ('TOTAL DE MOVIMIENTOS' in su or 'TOTAL MOVIMIENTOS' in su):
                in_detail = False
                continue
            if not in_detail:
                continue

            if any(sw in su for sw in skip_words):
                continue

            m = date_re.match(stripped)
            if not m:
                continue

            date_str, rest = m.group(1), m.group(2).strip()
            date = normalize_date(date_str, year)

            # Extraer y remover el voucher NRO. al final de la descripción
            rest_clean = voucher_re.sub('', rest).strip()

            nums = _find_numbers(rest_clean)
            desc_match = re.match(r'^(.*?)(?=\d{1,3}(?:\.\d{3})*,\d{2})', rest_clean)
            description = desc_match.group(1).strip() if desc_match else rest_clean.strip()

            if not nums or not description:
                continue

            debit  = abs(nums[0]) if nums[0] != 0 else 0.0
            credit = 0.0

            results.append(make_transaction(
                'BSJ', date, description, debit, credit, period, fname
            ))

    log.debug(f"  BSJ: {len(results)} transacciones extraídas")
    return results


# ─────────────────────────────────────────────────────────────────────────────
# GALICIA / GALICIA MAS (parser compartido)
# ─────────────────────────────────────────────────────────────────────────────
def parse_galicia(pdf_path: str, period: str, bank_name: str = 'GALICIA') -> list[dict]:
    """
    Formato: DD/MM/YY DESCRIPCIÓN (multilinea) MONTO SALDO
    Los montos están en la misma línea que la fecha.
    Líneas de continuación (sin fecha ni monto) se descartan.
    El saldo puede terminar en '-' (saldo deudor).
    """
    fname = os.path.basename(pdf_path)
    year = int(period[:4])
    results = []
    pages = _extract_text_pages(pdf_path)

    date_re = re.compile(r'^(\d{2}/\d{2}/\d{2})\s+(.+)')
    skip_words = ['SALDO ANTERIOR', 'SALDO AL ', 'FECHA ', 'DETALLE',
                  'TOTAL MOVIMIENTOS', 'DESCRIPCI']

    in_detail = False
    for page_text in pages:
        for line in page_text.splitlines():
            stripped = line.strip()
            su = stripped.upper()
            if not stripped:
                continue

            # Detectar inicio/fin ANTES de skip_words
            if 'FECHA' in su and 'DESCRIPCI' in su:
                in_detail = True
                continue
            if in_detail and any(x in su for x in
                                 ['TOTAL MOVIMIENTOS', 'SALDO FINAL', 'ACLARACIONES']):
                in_detail = False
                continue
            if not in_detail:
                continue

            if any(sw in su for sw in skip_words):
                continue

            m = date_re.match(stripped)
            if not m:
                continue   # Línea de continuación — ignorar

            date_str, rest = m.group(1), m.group(2).strip()
            date = normalize_date(date_str, year)

            nums = _find_numbers(rest)
            desc_match = re.match(r'^(.*?)(?=-?\d{1,3}(?:\.\d{3})*,\d{2})', rest)
            description = desc_match.group(1).strip() if desc_match else rest.strip()

            if not nums or not description:
                continue

            # En Galicia los montos en la línea son negativos para débitos
            amount = nums[0]
            debit  = abs(amount) if amount < 0 else 0.0
            credit = abs(amount) if amount > 0 else 0.0

            results.append(make_transaction(
                bank_name, date, description, debit, credit, period, fname
            ))

    log.debug(f"  {bank_name}: {len(results)} transacciones extraídas")
    return results


def parse_galicia_mas(pdf_path: str, period: str) -> list[dict]:
    return parse_galicia(pdf_path, period, bank_name='GALICIA MAS')


# ─────────────────────────────────────────────────────────────────────────────
# SANTANDER (33 páginas)
# ─────────────────────────────────────────────────────────────────────────────
def parse_santander(pdf_path: str, period: str) -> list[dict]:
    """
    Formato: Fecha | Comprobante | Movimiento | Débito | Crédito | Saldo
    - La fecha puede estar en su propia línea o inline.
    - Los montos tienen prefijo '$'.
    - Descripción puede continuar en la línea siguiente (sin fecha ni '$').
    """
    fname = os.path.basename(pdf_path)
    year = int(period[:4])
    results = []
    pages = _extract_text_pages(pdf_path)

    date_re  = re.compile(r'^(\d{2}/\d{2}/\d{2})')
    money_re = re.compile(r'\$\s*([\d.,]+)')   # $ 1.234,56

    # Prefijos de líneas de resumen/totales que NO son transacciones individuales
    skip_prefixes = [
        'TOTAL RETENCION', 'TOTAL RETENCI', 'POR RETENCION', 'POR RETENCI',
        'POR DEVOLUCION', 'POR DEVOLUCI', 'TOTAL DEVOLUCION', 'TOTAL DEVOLUCI',
        'RESP:', 'SALDO INICIAL', 'SALDO TOTAL', 'LOS DEP', 'POR PERSONA',
    ]

    def parse_money(s: str) -> float:
        s = s.replace('.', '').replace(',', '.').strip()
        try:
            return float(s)
        except ValueError:
            return 0.0

    in_detail = False
    current_date = ""

    for page_text in pages:
        for line in page_text.splitlines():
            stripped = line.strip()
            su = stripped.upper()
            if not stripped:
                continue

            # Detectar sección de movimientos
            if 'MOVIMIENTO' in su and ('DÉBITO' in su or 'DEBITO' in su):
                in_detail = True
                continue
            if in_detail and any(x in su for x in
                                 ['TOTAL MOVIMIENTOS', 'SALDO AL ', 'RESUMEN DE']):
                in_detail = False
                continue
            if not in_detail:
                continue

            # Actualizar fecha si la línea es solo una fecha
            dm = date_re.match(stripped)
            if dm:
                current_date = normalize_date(dm.group(1), year)

            # Buscar montos con '$'
            moneys = money_re.findall(stripped)
            if not moneys:
                continue

            # Extraer descripción (todo lo que está antes del primer '$')
            if '$' not in stripped:
                continue
            before_money = stripped[:stripped.index('$')].strip()
            # Remover fecha y comprobante del inicio
            before_money = date_re.sub('', before_money).strip()
            before_money = re.sub(r'^\d{5,}\s*', '', before_money).strip()
            description = before_money

            if not description or not current_date:
                continue

            # Filtrar líneas de resumen/subtotal que causarían doble conteo
            desc_u = description.upper()
            if any(desc_u.startswith(p.upper()) for p in skip_prefixes):
                continue

            amount = parse_money(moneys[0])
            # En Santander el primer monto es débito; si solo hay uno y la descripción
            # dice "credito", es crédito. Simplificamos: siempre como débito.
            debit  = amount
            credit = 0.0

            results.append(make_transaction(
                'SANTANDER', current_date, description, debit, credit, period, fname
            ))

    log.debug(f"  SANTANDER: {len(results)} transacciones extraídas")
    return results


# ─────────────────────────────────────────────────────────────────────────────
# DISPATCHER
# ─────────────────────────────────────────────────────────────────────────────

PARSERS = {
    'BBVA':        parse_bbva,
    'BNA':         parse_bna,
    'BSJ':         parse_bsj,
    'COMAFI':      parse_comafi,
    'GALICIA':     parse_galicia,
    'GALICIA MAS': parse_galicia_mas,
    'ICBC':        parse_icbc,
    'SANTANDER':   parse_santander,
    'SUPERVIELLE': parse_supervielle,
}


def extract_all(input_dir: str = INPUT_DIR,
                period_filter: str = None) -> dict[str, list[dict]]:
    """
    Escanea input_dir buscando archivos 'YYYYMM - BANCO - Extracto.pdf'.
    Retorna {bank_name: [transactions]}.
    Si period_filter es 'YYYYMM', solo procesa ese período.
    """
    results = {}
    files = [f for f in os.listdir(input_dir) if f.lower().endswith('.pdf')]
    matched = []

    for fname in sorted(files):
        m = FILENAME_PATTERN.match(fname)
        if not m:
            log.debug(f"  Ignorado (no coincide patrón): {fname}")
            continue
        period, bank = m.group(1), m.group(2).strip().upper()
        if period_filter and period != period_filter:
            continue
        matched.append((period, bank, fname))

    if not matched:
        log.warning(f"No se encontraron PDFs en: {input_dir}")
        return {}

    log.info(f"PDFs encontrados: {len(matched)}")
    for period, bank, fname in matched:
        pdf_path = os.path.join(input_dir, fname)
        parser = PARSERS.get(bank)
        if not parser:
            log.warning(f"  Sin parser para banco '{bank}' ({fname})")
            continue
        log.info(f"  Extrayendo {bank} ({period})...")
        try:
            txns = parser(pdf_path, period)
            key = bank
            if key not in results:
                results[key] = []
            results[key].extend(txns)
        except Exception as e:
            log.error(f"  Error en {fname}: {e}", exc_info=True)

    total = sum(len(v) for v in results.values())
    log.info(f"Total extraído: {total} transacciones en {len(results)} bancos")
    return results
