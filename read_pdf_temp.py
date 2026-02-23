import os
from pypdf import PdfReader
PDF_PATH = r"c:\Users\Tuchi\MiEstudioIA\FCI Santander\Input\202506 - Santander Valores.pdf"

def dump_pages():
    reader = PdfReader(PDF_PATH)
    with open('test_pdf_out.txt', 'w', encoding='utf-8') as f:
        for page_idx in range(1, 6):
            if page_idx >= len(reader.pages):
                break
            f.write(f"\n{'='*60}\n")
            f.write(f"PAGE {page_idx + 1}\n")
            f.write(f"{'='*60}\n")
            text = reader.pages[page_idx].extract_text()
            lines = text.split('\n')
            for i, line in enumerate(lines):
                f.write(f"  [{i:03d}] {line}\n")


if __name__ == "__main__":
    dump_pages()
