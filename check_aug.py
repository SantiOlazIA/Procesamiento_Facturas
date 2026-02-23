"""Check August PDF for SuperAhorro PLUS movements."""
from pypdf import PdfReader

PDF = r"c:\Users\Tuchi\MiEstudioIA\FCI Santander\Input\202508 - Santander Valores.pdf"

reader = PdfReader(PDF)
full = ""
for p in reader.pages:
    full += (p.extract_text() or "") + "\n"

lines = full.split("\n")

# Find all fund names and SALDO INICIAL references
print("=== Fund names found ===")
for i, l in enumerate(lines):
    s = l.strip()
    if s.startswith("FCI ") or s.startswith("SUPERGES "):
        print(f"  Line {i}: {s}")
    if "SUPER AHORRO" in s.upper():
        print(f"  Line {i}: {s}")
    if "SALDO INICIAL" in s:
        # Print context around it
        ctx = lines[max(0,i-2):i+3]
        print(f"  SALDO INICIAL at line {i}:")
        for j, c in enumerate(ctx):
            print(f"    [{i-2+j}] {c.strip()}")

print("\n=== Checking all months for SUPER AHORRO PLUS ===")
import glob, os

pdfs = sorted(glob.glob(r"c:\Users\Tuchi\MiEstudioIA\FCI Santander\Input\2025*.pdf") + 
              glob.glob(r"c:\Users\Tuchi\MiEstudioIA\FCI Santander\Input\2026*.pdf"))

for pdf_path in pdfs:
    fname = os.path.basename(pdf_path)
    reader = PdfReader(pdf_path)
    text = ""
    for p in reader.pages:
        text += (p.extract_text() or "") + "\n"
    
    has_plus = "SUPER AHORRO PLUS" in text.upper()
    has_superges = "SUPERGES" in text.upper()
    
    # Count SUPER AHORRO CL H $ PJ movements  
    sa_count = text.upper().count("SUSCRIPCION")
    re_count = text.upper().count("RESCATE")
    
    print(f"  {fname}: PLUS={'YES' if has_plus else 'no'}, SUPERGES={'YES' if has_superges else 'no'}, subs={sa_count}, resc={re_count}")
