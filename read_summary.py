import os
from pypdf import PdfReader

PDF_PATH = r"c:\Users\Tuchi\MiEstudioIA\FCI\Input\202601 - Santander Valores.pdf"

def analyze_pages():
    print(f"Analizando: {os.path.basename(PDF_PATH)}\n")
    try:
        reader = PdfReader(PDF_PATH)
        for i in [5, 6]:  # Pages 6 and 7 (0-indexed)
            if i < len(reader.pages):
                print(f"--- PAGINA {i+1} ---")
                text = reader.pages[i].extract_text()
                lines = text.split('\n')
                for j, line in enumerate(lines[:30]):
                    print(f"  {line}")
                if len(lines) > 30:
                    print(f"  [... {len(lines) - 30} lineas omitidas ...]")
            print("-" * 60)
            
    except Exception as e:
        print(f"Error procesando PDF: {e}")

if __name__ == "__main__":
    analyze_pages()
