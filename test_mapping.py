import re
from pypdf import PdfReader

PDF_PATH = r"c:\Users\Tuchi\MiEstudioIA\FCI Santander\Input\202601 - Santander Valores.pdf"

def test_mapping():
    reader = PdfReader(PDF_PATH)
    full_text = ""
    for page in reader.pages:
        full_text += page.extract_text() + "\n"

    lines = full_text.split('\n')
    date_re = re.compile(r'^\d{2}/\d{2}/\d{4}$')
    
    # 1. Map Nro_Comp to Importe AND Extract Especie
    comp_to_importe = {}
    comp_to_especie = {}
    
    # 2. Collect Debitos by (Date, Especie)
    debitos = {} # (date_liq, especie) -> list of importes
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if date_re.match(line):
            if i + 7 < len(lines):
                op_line = lines[i+2].strip()
                date_liq = lines[i+1].strip()
                nro_comp = lines[i+3].strip()
                
                # Check for PESOS section RESCATE/SUSCRIPCION
                if any(op_line.startswith(p) for p in ('SUSCRIPCION', 'RESCATE')):
                    especie_str = lines[i+4].strip()
                    if not especie_str.replace(',','').replace('.','').isdigit():
                        try:
                            importe = float(lines[i+7].strip().replace(',', ''))
                            comp_to_importe[nro_comp] = abs(importe)
                            comp_to_especie[nro_comp] = especie_str
                        except ValueError:
                            pass
                            
                # Check for DEBITO POR SUSCRIPCION
                if 'DEBITO' in op_line and 'SUSCRIPCION' in op_line:
                    especie_str = lines[i+4].strip()
                    try:
                        imp_str = lines[i+5].strip()
                        if imp_str.startswith('(') and imp_str.endswith(')'):
                            imp_str = imp_str[1:-1]
                        importe = float(imp_str.replace(',', ''))
                        key = (date_liq, especie_str)
                        if key not in debitos:
                            debitos[key] = []
                        debitos[key].append(abs(importe))
                    except ValueError:
                        pass
        i += 1
        
    print(f"Found {len(comp_to_importe)} Rescates/etc with Comprobante")
    print(f"Found {sum(len(v) for v in debitos.values())} Debitos")
    
    for k, v in debitos.items():
        print(f"Debitos {k}: {v}")

def clean_number(s):
    s = s.strip()
    if s.startswith('(') and s.endswith(')'):
        s = s[1:-1]
    return float(s.replace(',', ''))

test_mapping()
