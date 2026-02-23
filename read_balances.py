import os
import re
from pypdf import PdfReader

PDF_PATH = r"c:\Users\Tuchi\MiEstudioIA\FCI\Input\202601 - Santander Valores.pdf"

def analyze_cuotapartes():
    try:
        reader = PdfReader(PDF_PATH)
        
        print("--- EXTRAYENDO OPERACIONES DE CPs (PAGS 6-7) ---")
        logs_text = reader.pages[5].extract_text() + "\n" + reader.pages[6].extract_text()
        
        lines = logs_text.split('\n')
        
        # We'll look for lines that have 'SUSCRIPCION' or 'RESCATE' and extract the CANTIDAD
        total_cp_fci1 = 0.0 # FCI SUPER AHORRO CL H $ PJ
        
        print("Operaciones encontradas (extracto):")
        for i, line in enumerate(lines):
            line = line.strip()
            # The structure on page 6/7 seems to be:
            # 23/01/2026
            # 23/01/2026
            # SUSCRIPCION INMEDIATO
            # 916,115
            # 102,644,135.49
            # 102,644,135.49
            if "SUSCRIPCION INMEDIATO" in line or "RESCATE INMEDIATO" in line:
                # The next line contains the COMP number, then Amount? Wait, checking the read_summary.py output:
                # 26/01/2026
                # 26/01/2026
                # RESCATE INMEDIATO
                # 916,735  <-- Nro COMP
                # (15,007,192.57) <-- CANTIDAD (But it's formatted as currency?)
                # 87,636,942.92 <-- SALDO
                pass
        
        # Actually, let's just print a chunk of lines following a "SUSCRIPCION" to see the exact format of the numbers on pages 6-7.
        print("\nVerificando formato de numeros en paginas 6-7:")
        for i, line in enumerate(lines):
            if "SUSCRIPCION" in line or "RESCATE" in line:
                print(f"--- Operacion: {line.strip()} ---")
                for j in range(i+1, i+5):
                    if j < len(lines):
                        print(f"  > {lines[j].strip()}")
                break # Just checking the first one to understand the structure

    except Exception as e:
        print(f"Error procesando PDF: {e}")

if __name__ == "__main__":
    analyze_cuotapartes()
