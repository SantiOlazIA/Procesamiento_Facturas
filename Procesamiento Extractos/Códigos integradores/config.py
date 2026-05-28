"""
Pipeline de Extractos Bancarios — Configuración
Caterwest SA | Procesamiento mensual
"""
import os
import sys
import logging
from datetime import datetime
import re

# --- PATHS ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SCRIPT_DIR)          # Procesamiento Extractos/
INPUT_DIR = BASE_DIR                             # PDFs en la carpeta raíz
OUTPUT_DIR = os.path.join(BASE_DIR, 'Output')
LOG_DIR = os.path.join(SCRIPT_DIR, 'logs')

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

# Patrón de nombre de archivo: 202602 - BBVA - Extracto.pdf
FILENAME_PATTERN = re.compile(r'^(\d{6})\s+-\s+(.+?)\s+-\s+Extracto\.pdf$', re.IGNORECASE)

# --- LOGGING ---
LOG_FILE = os.path.join(LOG_DIR, f'pipeline_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')


def setup_logger(name='extractos_pipeline'):
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)

    fh = logging.FileHandler(LOG_FILE, encoding='utf-8')
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter(
        '%(asctime)s | %(levelname)-7s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    ))

    ch = logging.StreamHandler(stream=open(sys.stdout.fileno(), 'w', encoding='utf-8', closefd=False))
    ch.setLevel(logging.INFO)
    ch.setFormatter(logging.Formatter('%(message)s'))

    logger.addHandler(fh)
    logger.addHandler(ch)
    return logger


log = setup_logger()

# --- CATEGORÍAS ---
CAT_COMISIONES = "Comisiones / Gastos bancarios"
CAT_IVA_COM    = "IVA de comisiones"
CAT_SELLOS     = "Imp. sellos"
CAT_INTERESES  = "Intereses (por descubierto)"
CAT_IVA_INT    = "IVA sobre intereses"
CAT_IMP_DBCR   = "Impuestos débitos y créditos (Ley 25.413)"
CAT_SIRCREB    = "SIRCREB"
CAT_IIBB       = "Impuestos IIBB (Ingresos Brutos)"
CAT_NONE       = "Sin clasificar"

CATEGORIES = [
    CAT_COMISIONES,
    CAT_IVA_COM,
    CAT_SELLOS,
    CAT_INTERESES,
    CAT_IVA_INT,
    CAT_IMP_DBCR,
    CAT_SIRCREB,
    CAT_IIBB,
]

# Categorías con IVA ambiguo (resuelto por contexto)
CAT_IVA_AMBIG = "__IVA_AMBIG__"

# --- REGLAS DE KEYWORDS POR BANCO ---
# Cada valor es una lista de substrings (case-insensitive) a buscar en la descripción.
# El orden importa: se evalúa de arriba hacia abajo; la primera coincidencia gana.
# CAT_IVA_AMBIG se resuelve después por contexto (last_category) o ratio de monto.

BANK_RULES = {
    "BBVA": [
        (CAT_COMISIONES, ["MANTENIMIENTO DE CUENTA"]),
        (CAT_IVA_COM,    ["IVA TASA GENERAL", "PERCEPCION IVA RG 2408"]),
        (CAT_INTERESES,  ["INTERES SALDO DEUDOR"]),
        (CAT_IVA_INT,    ["IVA R.I."]),
        (CAT_IMP_DBCR,   ["IMP.LEY 25413", "IMP. LEY 25413"]),
    ],
    "BNA": [
        (CAT_COMISIONES, ["COMISION PAQUETES", "COMISION DEB.", "COMIS.TRANSF"]),
        (CAT_IVA_COM,    ["I.V.A. BASE", "RETEN. I.V.A.", "RETEN.IVA"]),
        (CAT_INTERESES,  ["INTERESES"]),
        (CAT_IMP_DBCR,   ["GRAVAMEN LEY 25413", "GRAVAMEN LEY25413"]),
        (CAT_SIRCREB,    ["REG.REC.SIRCREB", "SIRCREB"]),
    ],
    "BSJ": [
        (CAT_COMISIONES, ["COM SAL DEUDOR CTA CTE"]),
        (CAT_INTERESES,  ["INTERESES POR SOBREGIROS", "INTERES POR SOBREGIRO"]),
        (CAT_IVA_COM,    ["I.V.A. PERCEPCION RG 3337", "IVA PERCEPCION RG 3337"]),
        (CAT_IMP_DBCR,   ["FV IMP DEBITO LEY 25413", "IMPUESTO DEBITO LEY 25413",
                           "IMPUESTO CREDITO LEY 25413", "IMPUESTO CREDITO LEY25413"]),
        (CAT_SIRCREB,    ["SIRCREB"]),
        (CAT_IVA_AMBIG,  ["I.V.A."]),           # resuelto por contexto
    ],
    "COMAFI": [
        (CAT_COMISIONES, ["COMISION MANTENIMIENTO SERVICIO", "COMISIÓN MANTENIMIENTO"]),
        (CAT_IVA_COM,    ["IVA - ALICUOTA GENERAL", "IVA ALICUOTA GENERAL"]),
        (CAT_IMP_DBCR,   ["IMPUESTO A LOS DEBITOS", "LEY 25413"]),
    ],
    "GALICIA": [
        (CAT_COMISIONES, ["COMISION SERVICIO DE CUENTA", "DEB-COM. GTIAS", "DEB-COM.GTIAS"]),
        (CAT_INTERESES,  ["INTERESES SOBRE SALDOS DEUDORES", "INTERESES SOBRE SALDOS"]),
        (CAT_SELLOS,     ["IMPUESTO DE SELLOS"]),
        (CAT_IMP_DBCR,   ["IMP. DEB. LEY 25413 GRAL.", "IMP.DEB.LEY 25413",
                           "IMP. CRE. LEY 25413", "IMP.CRE.LEY 25413"]),
        (CAT_SIRCREB,    ["SIRCREB", "REG.RECAU.SIRCREB"]),
        (CAT_IIBB,       ["ING. BRUTOS", "INGR. BRUTOS"]),
        (CAT_IVA_AMBIG,  ["IVA"]),              # resuelto por contexto
    ],
    "GALICIA MAS": [
        (CAT_INTERESES,  ["INTERESES SOBRE SALDOS DEUDORES", "INTERESES SOBRE SALDOS"]),
        (CAT_SELLOS,     ["IMPUESTO DE SELLOS"]),
        (CAT_IMP_DBCR,   ["IMP. DEB. LEY 25413 GRAL.", "IMP.DEB.LEY 25413"]),
        (CAT_SIRCREB,    ["SIRCREB"]),
        (CAT_IVA_AMBIG,  ["IVA"]),              # resuelto por contexto
    ],
    "ICBC": [
        (CAT_COMISIONES, ["MANTENIMIENTO DE CUENTA"]),
        (CAT_IVA_COM,    ["IMPUESTO AL VALOR AGREGADO", "PERCEPCION IVA RG"]),
        (CAT_INTERESES,  ["DEBITO LIQUIDACION INTERES", "DEB.LIQ.INTERES"]),
        (CAT_IVA_INT,    ["IVA ALICUOTA REDUCIDA"]),
        (CAT_SELLOS,     ["SELLADO", "AJ IMPUES/SELL"]),
        (CAT_IMP_DBCR,   ["IMP S/DEBITOS EN CTA CTE", "AJUSTE IMP DEBITO CTA CTE",
                           "IMP.S/DEB.CTA.CTE"]),
    ],
    "SANTANDER": [
        (CAT_COMISIONES, ["COMISION TRANSF OTROS BCOS", "COMISION TRANSFERENCIAS",
                           "COMISION POR SERVICIO DE CUENTA", "COMISION MENSUAL DE MOVS",
                           "COM.MOVIM MENSUALES",
                           "COMISION SERVICIO CUENTA DOLARES", "COMISION SERVICIO PAGO HABERES",
                           "COMISION COMPENSACION CHEQUES", "SERVICIO INTERBANKING"]),
        (CAT_IVA_COM,    ["IVA 21% REG DE TRANSFISC", "IVA 21%"]),
        (CAT_IVA_INT,    ["IVA - REG DE TRANSP FISC", "IVA REG DE TRANSP"]),
        (CAT_IMP_DBCR,   ["IMPUESTO LEY 25.413 DEBITO", "IMPUESTO LEY 25.413 CREDITO",
                           "IMPUESTO LEY 25413"]),
        (CAT_SIRCREB,    ["REGIMEN DE RECAUDACION SIRCREB", "SIRCREB"]),
    ],
    "SUPERVIELLE": [
        (CAT_INTERESES,  ["INTERESES DE SOBREGIRO", "INTERESES SOBREGIRO"]),
        (CAT_IVA_COM,    ["PERCEPCION I.V.A. RG. 3337", "PERCEPCION IVA RG 3337",
                           "PERCEPCIÓN I.V.A.RG. 3337"]),
        (CAT_IMP_DBCR,   ["IMPUESTO DÉBITOS Y CRÉDITOS/DB", "IMPUESTO DEBITOS Y CREDITOS"]),
        (CAT_IVA_AMBIG,  ["IVA"]),              # resuelto por contexto
    ],
}

# --- HELPERS ---

def parse_argentine_number(s: str) -> float:
    """
    Convierte '1.234.567,89' o '52.000,00-' a float.
    Retorna 0.0 si no se puede parsear.
    """
    if not s:
        return 0.0
    s = s.strip()
    negative = s.endswith('-') or s.startswith('-')
    s = s.strip('-').strip()
    # Quitar puntos de miles, reemplazar coma decimal por punto
    s = s.replace('.', '').replace(',', '.')
    try:
        value = float(s)
        return -value if negative else value
    except ValueError:
        return 0.0


def normalize_date(s: str, year_hint: int) -> str:
    """
    Normaliza fechas en distintos formatos a 'YYYY-MM-DD'.
    Formatos soportados: DD/MM/YY, DD/MM/YYYY, DD-MM, DD/MM
    year_hint: año completo (ej. 2026) usado cuando no está en el string.
    Retorna "" si el formato no coincide o si la fecha es inválida (ej. mes 13).
    """
    from datetime import date as _date
    s = s.strip()
    d = mo = y = None
    # DD/MM/YYYY
    m = re.match(r'^(\d{1,2})/(\d{1,2})/(\d{4})$', s)
    if m:
        d, mo, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
    else:
        # DD/MM/YY
        m = re.match(r'^(\d{1,2})/(\d{1,2})/(\d{2})$', s)
        if m:
            d, mo, y = int(m.group(1)), int(m.group(2)), 2000 + int(m.group(3))
        else:
            # DD/MM (sin año)
            m = re.match(r'^(\d{1,2})/(\d{1,2})$', s)
            if m:
                d, mo, y = int(m.group(1)), int(m.group(2)), year_hint
            else:
                # DD-MM
                m = re.match(r'^(\d{1,2})-(\d{1,2})$', s)
                if m:
                    d, mo, y = int(m.group(1)), int(m.group(2)), year_hint
    if d is None:
        return ""
    try:
        _date(y, mo, d)   # valida que la fecha es real (ej. mes 1-12, día 1-31)
    except ValueError:
        return ""
    return f"{y}-{mo:02d}-{d:02d}"


def make_transaction(bank: str, date: str, description: str,
                     debit: float, credit: float,
                     period: str, source_file: str) -> dict:
    """Construye el dict estándar de una transacción."""
    return {
        "bank": bank,
        "date": date,
        "description": description,
        "debit": abs(debit) if debit else 0.0,
        "credit": abs(credit) if credit else 0.0,
        "category": CAT_NONE,
        "period": period,
        "source_file": source_file,
    }


# --- EXCEL FORMATTING ---
FONT_NAME = 'Arial'
FONT_SIZE = 10
DATE_FORMAT = 'DD/MM/YYYY'
NUMBER_FORMAT = '#.##0,00'

HEADER_FILL_COLOR = '2E4057'   # Azul oscuro
HEADER_FONT_COLOR = 'FFFFFF'
TOTAL_FILL_COLOR  = 'D0E4F7'   # Azul claro
ALT_ROW_COLOR     = 'F5F8FC'   # Gris muy suave
NONE_ROW_COLOR    = 'FFCCCC'   # Rojo claro para Sin clasificar

BANK_COLORS = {
    'BBVA':        '004B87',
    'BNA':         '00693E',
    'BSJ':         '8B0000',
    'COMAFI':      'FF6600',
    'GALICIA':     'CC0000',
    'GALICIA MAS': 'CC0000',
    'ICBC':        'CC0000',
    'SANTANDER':   'EC0000',
    'SUPERVIELLE': '0056A2',
}
