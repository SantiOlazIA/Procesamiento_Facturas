from pypdf import PdfReader
import os
import re

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PDF_DIR = os.path.join(os.path.dirname(SCRIPT_DIR), 'Input')
FNAME = 'FONDO COMUN DE INVERSION 24 09.pdf'

def inspect():
    path = os.path.join(PDF_DIR, FNAME)
    if not os.path.exists(path):
        print(f"File not found: {path}")
        return

    reader = PdfReader(path)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
        
    print(f"--- CONTENT OF {FNAME} ---")
    print(text)
    print("-----------------------------")

if __name__ == "__main__":
    inspect()
