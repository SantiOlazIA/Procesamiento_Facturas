from pypdf import PdfReader
import re
import json
import datetime
import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(SCRIPT_DIR)
from config import INPUT_PDF_DIR, REGEX_PATTERN, JSON_DATA_PATH, START_MONTH, INITIAL_YEAR, log

def clean_decimal(s):
    s = s.replace('.', '').replace(',', '.')
    return float(s)

def extract_all():
    log.info("=" * 50)
    log.info("PASO 1: Extraccion de Movimientos de PDFs")
    log.info("=" * 50)
    
    all_movements = []
    errors = []  # Mejora 3: collect errors instead of failing
    
    if not os.path.exists(INPUT_PDF_DIR):
        log.error(f"Directorio de entrada no encontrado: {INPUT_PDF_DIR}")
        return False

    files = [f for f in os.listdir(INPUT_PDF_DIR) if f.lower().endswith('.pdf')]
    
    if not files:
        log.warning("No se encontraron archivos PDF en la carpeta Input")
        return False
    
    # Sort files logic
    def get_sort_key(fname):
        nums = re.findall(r'\d+', fname)
        if len(nums) == 2:
            y = int(nums[0])
            m = int(nums[1])
            if y < 100: y += 2000
            return y * 100 + m
        if len(nums) == 3:
            d = int(nums[0])
            m = int(nums[1])
            y = int(nums[2])
            if y < 100: y += 2000
            return y * 100 + m
        return 0
        
    files.sort(key=get_sort_key)
    log.info(f"Encontrados {len(files)} archivos PDF")
    log.debug(f"Orden de procesamiento: {files}")

    regex = re.compile(REGEX_PATTERN)
    current_year = INITIAL_YEAR 
    last_processed_month = START_MONTH - 1 

    for fname in files:
        fpath = os.path.join(INPUT_PDF_DIR, fname)
        
        file_y = 0
        try:
            nums = re.findall(r'\d+', fname)
            if len(nums) == 2: file_y = int(nums[0]) + 2000
            elif len(nums) == 3: file_y = int(nums[2]) + 2000
        except: pass

        log.info(f"  Leyendo: {fname}")
        
        try:
            reader = PdfReader(fpath)
            text = ""
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
                else:
                    log.warning(f"    Pagina sin texto en {fname}")
                
            lines = text.split('\n')
            file_movements = []
            
            for l in lines:
                match = regex.search(l)
                if match:
                    day_str = match.group(1).split('/')[0]
                    month_str = match.group(1).split('/')[1]
                    m_type = match.group(2)
                    cp = clean_decimal(match.group(3))
                    amt = clean_decimal(match.group(4))
                    
                    m_month = int(month_str)
                    
                    if file_y > 2000:
                        if m_month == 12 and (file_y % 100) == (current_year + 1) % 100:
                            year_to_use = current_year
                        else:
                            year_to_use = file_y
                            if file_y > current_year: current_year = file_y
                    else:
                        if m_month < last_processed_month and (last_processed_month - m_month) > 6:
                            current_year += 1
                        year_to_use = current_year
                    
                    final_date = f"{day_str}/{month_str}/{year_to_use}"
                    
                    item = {
                        'date': final_date, 
                        'type': m_type, 
                        'cp': cp, 
                        'amount': amt,
                        'source': fname,
                        'sort_val': datetime.datetime.strptime(final_date, "%d/%m/%Y").timestamp()
                    }
                    file_movements.append(item)
                    last_processed_month = m_month
            
            if not file_movements:
                log.warning(f"    Sin movimientos encontrados en {fname}")
                errors.append(f"{fname}: 0 movimientos extraidos (posible formato inesperado)")
            else:
                log.info(f"    -> {len(file_movements)} movimientos extraidos")
                log.debug(f"    Tipos: {sum(1 for m in file_movements if m['type']=='COMPRA')} COMPRA, "
                         f"{sum(1 for m in file_movements if m['type']=='VENTA')} VENTA")
            
            file_movements.sort(key=lambda x: x['sort_val'])
            for m in file_movements:
                del m['sort_val']
                all_movements.append(m)

        except Exception as e:
            error_msg = f"{fname}: {type(e).__name__}: {e}"
            log.error(f"    ERROR procesando {fname}: {e}")
            errors.append(error_msg)
            # Mejora 3: Continue processing other PDFs instead of stopping
            continue
            
    all_movements.sort(key=lambda x: datetime.datetime.strptime(x['date'], "%d/%m/%Y"))

    with open(JSON_DATA_PATH, 'w', encoding='utf-8') as f:
        json.dump(all_movements, f, indent=2)
    
    # Summary
    log.info(f"\nResumen de extraccion:")
    log.info(f"  Total movimientos: {len(all_movements)}")
    log.info(f"  Archivos procesados: {len(files) - len(errors)}/{len(files)}")
    
    if errors:
        log.warning(f"  ERRORES ({len(errors)}):")
        for e in errors:
            log.warning(f"    - {e}")
    
    log.info(f"  Guardado en: {JSON_DATA_PATH}")
    return len(errors) == 0

if __name__ == "__main__":
    extract_all()
