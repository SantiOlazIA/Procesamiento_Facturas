from fpdf import FPDF
import os

# Define output path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_DIR = os.path.join(os.path.dirname(SCRIPT_DIR), 'Input')

def create_pdf(filename, movements):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Courier", size=10)
    
    # Header simulation
    pdf.cell(200, 10, txt="SALDOS CONSOLIDADOS", ln=1, align='L')
    pdf.cell(200, 10, txt="               CONCEPTO                                 Saldos al:    30/11/2025", ln=1, align='L')
    pdf.cell(200, 10, txt="             Bonos/Fdos/Acc.val en  $            1.000.000,00       30/11/2025", ln=1, align='L')
    pdf.cell(200, 10, txt="_" * 80, ln=1, align='L')
    
    # Movement Section
    pdf.cell(200, 10, txt="MOVIMIENTO DE INVERSIONES", ln=1, align='L')
    pdf.cell(200, 10, txt="   BONOS/FONDOS/ACCIONES CTA. TITULOS          471/00005908523", ln=1, align='L')
    pdf.cell(200, 10, txt="      Iva-Responsable Inscripto", ln=1, align='L')
    pdf.cell(200, 10, txt=" OPERACIONES REALIZADAS", ln=1, align='L')
    pdf.cell(200, 10, txt="   FECHA VENC. DESCRIPCION                              CANTIDAD      PRECIO   GASTOS        IMPORTE", ln=1, align='L')
    
    # Add movements
    # Format: 02/09 02/09 VENTA            DB  FBA RENPEB        292.481,39 112827,69300    0,00      33000.000,01
    for m in movements:
        line = f"   {m['date']} {m['date']} {m['type'].ljust(16)} {m['db_cr']}  FBA RENPEB       {m['cp']:>11} {m['price']}    0,00     {m['amount']:>13}"
        pdf.cell(200, 5, txt=line, ln=1, align='L')

    filepath = os.path.join(INPUT_DIR, filename)
    pdf.output(filepath)
    print(f"Created: {filepath}")

# Data for Nov 2025
# Current CP: ~1.8M. Price ~155? Let's assume price 200.
# Subscription: 10,000 CP @ 200 -> 2,000,000
# Redemption: 5,000 CP @ 200 -> 1,000,000
movs_nov_25 = [
    {'date': '05/11', 'type': 'COMPRA', 'db_cr': 'CR', 'cp': '10.000,00', 'price': '200,000000', 'amount': '2000.000,00'},
    {'date': '20/11', 'type': 'VENTA', 'db_cr': 'DB', 'cp': '5.000,00', 'price': '205,000000', 'amount': '1025.000,00'}
]

# Data for Dec 2025 (Another file to test sorting)
# Subscription: 20,000 CP @ 210 -> 4,200,000
movs_dec_25 = [
    {'date': '10/12', 'type': 'COMPRA', 'db_cr': 'CR', 'cp': '20.000,00', 'price': '210,000000', 'amount': '4200.000,00'}
]

if __name__ == "__main__":
    create_pdf("FONDO COMUN DE INVERSION 25 11.pdf", movs_nov_25)
    create_pdf("FONDO COMUN DE INVERSION 25 12.pdf", movs_dec_25)
