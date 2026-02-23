import os
import sys
import logging
from datetime import datetime

# --- PATHS ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SCRIPT_DIR)  # Parent of integradores -> FCI
INPUT_PDF_DIR = os.environ.get('FCI_INPUT_DIR', os.path.join(BASE_DIR, 'Input'))

# Output
OUTPUT_EXCEL_PATH = os.environ.get('FCI_OUTPUT_FILE', os.path.join(SCRIPT_DIR, 'FCI_Procesado_Anual.xlsx'))
JSON_DATA_PATH = os.path.join(SCRIPT_DIR, 'movements.json')
TEMPLATE_EXCEL_PATH = os.path.join(SCRIPT_DIR, 'Template_FCI.xlsx')
LOG_DIR = os.path.join(SCRIPT_DIR, 'logs')

# --- LOGGING ---
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, f'pipeline_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')

def setup_logger(name='fci_pipeline'):
    """Create a logger that writes to both console and file with timestamps."""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger  # Already configured
    
    logger.setLevel(logging.DEBUG)
    
    # File handler (detailed)
    fh = logging.FileHandler(LOG_FILE, encoding='utf-8')
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter(
        '%(asctime)s | %(levelname)-7s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    ))
    
    # Console handler (concise)
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(logging.Formatter('%(message)s'))
    
    logger.addHandler(fh)
    logger.addHandler(ch)
    return logger

log = setup_logger()

# --- VALIDATION ---
def check_paths():
    if not os.path.exists(INPUT_PDF_DIR):
        log.error(f"Input directory not found: {INPUT_PDF_DIR}")
        return False
    return True

# --- PDF PROCESSING ---
REGEX_PATTERN = r'(\d{2}/\d{2})\s+\d{2}/\d{2}\s+(VENTA|COMPRA)\s+.*?FBA RENPEB\s+([\d\.]+,\d{2})\s+[\d\.]+,\d+\s+[\d\.]+,\d{2}\s+([\d\.]+,\d{2})'

INITIAL_YEAR = 2024 
START_MONTH = 10  # October

# --- EXCEL FORMATTING ---
FONT_NAME = 'Arial'
FONT_SIZE = 10
DATE_FORMAT = 'DD/MM/YYYY'
BORDER_STYLE = 'medium'

# Pleasant Colors (Red, Green, Blue, Yellow + variants)
VIBRANT_COLORS = [
    'FF4444', '44BB44', '4488FF', 'FFDD44',  # Red, Green, Blue, Yellow
    'FF8844', 'AA66FF', '44BBBB', 'FF6688',  # Orange, Violet, Teal, Coral
    '88DD44', '44AAFF', 'FF88CC', 'FFAA44',  # Lime, Sky, Pink, Gold
    'BB88FF', '66DDAA', 'FF8888', '44DDDD',  # Lavender, Mint, Salmon, Cyan
]
