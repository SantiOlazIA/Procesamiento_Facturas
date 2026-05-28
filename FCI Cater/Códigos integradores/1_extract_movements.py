"""
FCI Santander - Extractor de Movimientos (Paso 1)

Parses Santander Valores PDF statements to extract buy/sell
transactions for each FCI fund. Outputs one JSON file per fund.

Parsing source: "CUENTA COMITENTE EN INSTRUMENTOS" section
(pages 6-7 in a typical statement), which tracks Cuotapartes.
"""
import re
import json
import os
import sys
import glob
from pypdf import PdfReader

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(SCRIPT_DIR)
from config import INPUT_PDF_DIR, log


def clean_number(s):
    """Parse Argentine number format: '1,234,567.89' or '(1,234,567.89)'."""
    s = s.strip()
    negative = False
    if s.startswith('(') and s.endswith(')'):
        negative = True
        s = s[1:-1]
    s = s.replace(',', '')
    val = float(s)
    return -val if negative else val


def make_safe_filename(fund_name):
    """Convert a fund name to a filesystem-safe string."""
    safe = fund_name.strip()
    safe = re.sub(r'[^\w\s-]', '', safe)
    safe = re.sub(r'\s+', '_', safe)
    return safe[:60]


def extract_all_funds():
    """Extract movements from all Santander PDFs, grouped by fund."""
    log.info("=" * 50)
    log.info("PASO 1: Extraccion de Movimientos (Santander)")
    log.info("=" * 50)

    if not os.path.exists(INPUT_PDF_DIR):
        log.error(f"Directorio de entrada no encontrado: {INPUT_PDF_DIR}")
        return False

    pdf_files = sorted(
        [f for f in os.listdir(INPUT_PDF_DIR) if f.lower().endswith('.pdf')]
    )

    if not pdf_files:
        log.warning("No se encontraron archivos PDF en la carpeta Input")
        return False

    log.info(f"Encontrados {len(pdf_files)} archivos PDF")

    # Dict of fund_name -> list of movements (across all PDFs)
    all_funds = {}
    # Dict of fund_name -> initial CP balance from "SALDO INICIAL"
    initial_balances = {}
    # Dict of fund_name -> final_cp from "ESTADO DE CARTERA VALORIZADA"
    portfolio_cps = {}
    errors = []

    for fname in pdf_files:
        fpath = os.path.join(INPUT_PDF_DIR, fname)
        log.info(f"  Leyendo: {fname}")

        try:
            reader = PdfReader(fpath)
            full_text = ""
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    full_text += page_text + "\n"

            comps_map, debitos_map, rescates_map = _extract_comprobantes(full_text)
            _extract_instrument_movements(
                full_text, fname, all_funds, initial_balances, comps_map, debitos_map, rescates_map
            )
            _extract_portfolio_balances(full_text, fname, portfolio_cps)

        except Exception as e:
            error_msg = f"{fname}: {type(e).__name__}: {e}"
            log.error(f"    ERROR procesando {fname}: {e}")
            errors.append(error_msg)
            continue

    # Normalize portfolio using the last Santander Valores PDF as ground truth.
    # When a fund reaches 0 balance it won't appear in that PDF's portfolio section,
    # but older PDFs may have left a stale non-zero value in portfolio_cps.
    # Fix: re-extract the final portfolio and set missing funds to 0.
    santander_pdfs = [f for f in pdf_files if 'santander' in f.lower()]
    if santander_pdfs:
        last_fpath = os.path.join(INPUT_PDF_DIR, santander_pdfs[-1])
        try:
            reader = PdfReader(last_fpath)
            last_text = "\n".join(
                (p.extract_text() or "") for p in reader.pages
            )
            final_portfolio = {}
            _extract_portfolio_balances(last_text, santander_pdfs[-1], final_portfolio)
            for fund_name in list(portfolio_cps):
                if fund_name not in final_portfolio:
                    portfolio_cps[fund_name] = 0.0  # Fully redeemed — not in last portfolio
            portfolio_cps.update(final_portfolio)
        except Exception as e:
            log.warning(f"No se pudo normalizar portfolio con ultimo PDF: {e}")

    # Clean old movement files
    old_files = glob.glob(os.path.join(SCRIPT_DIR, 'movements_*.json'))
    for old_f in old_files:
        os.remove(old_f)

    # Save one JSON per fund
    fund_count = 0
    for fund_name, movements in all_funds.items():
        if fund_count >= 10:
            log.warning("Limite de 10 FCIs alcanzado, ignorando fondos adicionales")
            break

        # Fix rounding drift: adjust the last rescate to absorb sub-0.10 residuals
        _fix_balance_drift(
            movements, initial_balances.get(fund_name, 0.0), fund_name
        )

        safe_name = make_safe_filename(fund_name)
        json_path = os.path.join(SCRIPT_DIR, f'movements_{safe_name}.json')

        output_data = {
            'fund_name': fund_name,
            'initial_balance': initial_balances.get(fund_name, 0.0),
            'movements': movements,
            'portfolio_cp': portfolio_cps.get(fund_name),
        }

        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)

        subs = sum(1 for m in movements if m['type'] == 'SUSCRIPCION')
        resc = sum(1 for m in movements if m['type'] == 'RESCATE')
        log.info(
            f"  [{fund_name}] {len(movements)} movimientos "
            f"({subs} suscripciones, {resc} rescates) -> {json_path}"
        )
        fund_count += 1

    # Summary
    log.info(f"\nResumen de extraccion:")
    log.info(f"  Fondos detectados: {fund_count}")
    log.info(f"  Archivos procesados: {len(pdf_files) - len(errors)}/{len(pdf_files)}")

    if errors:
        log.warning(f"  ERRORES ({len(errors)}):")
        for e in errors:
            log.warning(f"    - {e}")

    return len(errors) == 0


def _fix_balance_drift(movements, initial_balance, fund_name):
    """Adjust rescate CPs at zero-crossing points to absorb rounding drift.

    The bank's system rounds intermediate balances, so raw CP values
    from the PDF don't always perfectly cancel at liquidation points.
    We trace the running balance using Decimal and whenever it dips
    below 0.10 after a rescate (indicating a full liquidation), we
    adjust that rescate's CP to make the balance exactly 0.
    """
    from decimal import Decimal
    balance = Decimal(str(initial_balance))
    fixes = 0

    for i, m in enumerate(movements):
        cp = Decimal(str(m['cp']))
        if m['type'] == 'SUSCRIPCION':
            balance += cp
        else:
            balance -= cp

        # Check if we hit a zero-crossing after a rescate
        residual = float(balance)
        if (m['type'] == 'RESCATE'
                and 0.001 < abs(residual) < 0.10):
            # Check that the next movement (if any) is a suscripcion
            # on a different date, confirming this is a liquidation
            is_liquidation = True
            if i + 1 < len(movements):
                nxt = movements[i + 1]
                if nxt['type'] == 'RESCATE' and nxt['date'] == m['date']:
                    is_liquidation = False

            if is_liquidation:
                m['cp'] = round(m['cp'] + residual, 2)
                balance = Decimal('0')
                fixes += 1
                log.info(
                    f"  [{fund_name}] Ajustado rescate {m['date']} "
                    f"en {residual:+.2f} (drift de redondeo)"
                )


def _extract_comprobantes(full_text):
    """Scan the full text (PESOS section) to map Nro Comp to Importe and collect Debitos/Rescates."""
    lines = full_text.split('\n')
    date_re = re.compile(r'^\d{2}/\d{2}/\d{4}$')
    op_prefixes = ('SUSCRIPCION', 'RESCATE')
    # Standard rescate op names that appear in the instruments section directly
    _STANDARD_RESCATES = {'RESCATE INMEDIATO', 'RESCATE T+', 'RESCATE INMEDIATO DOLARES'}
    comps = {}
    debitos = {}   # key: (date_liq, especie), value: list of importes  — T+ suscripciones
    rescates = {}  # key: (date_liq, especie), value: list of importes  — non-standard rescates

    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if date_re.match(line):
            if i + 7 < len(lines):
                date_liq = lines[i+1].strip()
                op_line = lines[i+2].strip()

                # Check for RESCATE or SUSCRIPCION operations
                if any(op_line.startswith(prefix) for prefix in op_prefixes):
                    if date_re.match(date_liq):
                        nro_comp = lines[i+3].strip()
                        especie_str = lines[i+4].strip()
                        try:
                            clean_number(especie_str)
                            is_number = True
                        except ValueError:
                            is_number = False

                        if not is_number:
                            importe_str = lines[i+7].strip()
                            try:
                                importe = abs(clean_number(importe_str))
                                comps[nro_comp] = importe
                                # Non-standard rescates (e.g. RESCATE 24 HS) don't appear in
                                # the instruments section by nro_comp — store by date+especie
                                # so DEBITO DE TITULOS POR RESCATE DE FONDOS can look them up.
                                if op_line.startswith('RESCATE') and op_line not in _STANDARD_RESCATES:
                                    key = (date_liq, especie_str)
                                    if key not in rescates:
                                        rescates[key] = []
                                    rescates[key].append(importe)
                            except ValueError:
                                pass

                # Check for DEBITO POR SUSCRIPCION (For T+ subscriptions)
                if 'DEBITO' in op_line and 'SUSCRIPCION' in op_line:
                    especie_str = lines[i+4].strip()
                    try:
                        imp_str = lines[i+5].strip()
                        importe = abs(clean_number(imp_str))
                        key = (date_liq, especie_str)
                        if key not in debitos:
                            debitos[key] = []
                        debitos[key].append(importe)
                    except ValueError:
                        pass
        i += 1
    return comps, debitos, rescates


def _extract_instrument_movements(
    full_text, source_file, all_funds, initial_balances, comps_map, debitos_map,
    rescates_map=None,
):
    """Parse the 'CUENTA COMITENTE EN INSTRUMENTOS' section for CP movements."""
    lines = full_text.split('\n')
    date_re = re.compile(r'^\d{2}/\d{2}/\d{4}$')
    op_types = {
        'SUSCRIPCION INMEDIATO': 'SUSCRIPCION',
        'SUSCRIPCION T+': 'SUSCRIPCION',
        'SUSCRIPCION INMEDIATO DOLARES': 'SUSCRIPCION',  # SFAI USD fund
        'RESCATE INMEDIATO': 'RESCATE',
        'RESCATE T+': 'RESCATE',
        'RESCATE INMEDIATO DOLARES': 'RESCATE',          # SFAI USD fund
        'DEBITO DE TITULOS POR RESCATE DE FONDOS': 'RESCATE',  # MVIJ 24-hs rescate
    }

    current_fund = None
    current_especie = None
    i = 0

    while i < len(lines):
        line = lines[i].strip()

        # Detect fund name: lines starting with "FCI " or "SUPERGES "
        # Guard: only enter a fund section when SALDO INICIAL follows within 2 lines.
        # This prevents false detection on summary/portfolio pages where fund names also
        # appear but are followed by balance amounts, not SALDO INICIAL.
        if line.startswith('FCI ') or line.startswith('SUPERGES '):
            window = [lines[j].strip() for j in range(i + 1, min(i + 3, len(lines)))]
            if 'SALDO INICIAL' in window:
                current_fund = line
                # The especie code (e.g. SA$) is typically on the line prior
                if i > 0:
                    current_especie = lines[i - 1].strip()
                if current_fund not in all_funds:
                    all_funds[current_fund] = []
            i += 1
            continue

        # Capture initial balance
        if current_fund and line == 'SALDO INICIAL':
            if i + 1 < len(lines):
                try:
                    init_val = clean_number(lines[i + 1].strip())
                    if current_fund not in initial_balances:
                        initial_balances[current_fund] = init_val
                except ValueError:
                    pass
            i += 2
            continue

        # Detect operation block: starts with a date line
        if current_fund and date_re.match(line):
            date_conc = line
            # Peek ahead for: date_liq, op_type, nro_comp, cantidad, saldo
            if i + 4 < len(lines):
                date_liq = lines[i + 1].strip()
                op_line = lines[i + 2].strip()
                nro_comp = lines[i + 3].strip()
                cantidad_str = lines[i + 4].strip()

                if op_line in op_types and date_re.match(date_liq):
                    try:
                        # Dollar-section operations (e.g. SFAI) insert the especie code
                        # between nro_comp and cantidad, so try i+4 first, fall back to i+5.
                        try:
                            cantidad = clean_number(cantidad_str)
                        except ValueError:
                            cantidad = clean_number(lines[i + 5].strip())

                        importe = comps_map.get(nro_comp)

                        # Fallback for SUSCRIPCION T+ (no direct nro_comp in pesos section)
                        if importe is None and op_types.get(op_line) == 'SUSCRIPCION':
                            key = (date_liq, current_especie)
                            if key in debitos_map and debitos_map[key]:
                                importe = debitos_map[key].pop(0)  # Consume chronologically

                        # Fallback for DEBITO DE TITULOS POR RESCATE DE FONDOS
                        # (nro_comp in instruments != nro_comp in pesos; match by date+especie)
                        if importe is None and op_types.get(op_line) == 'RESCATE' and rescates_map:
                            key = (date_liq, current_especie)
                            if key in rescates_map and rescates_map[key]:
                                importe = rescates_map[key].pop(0)

                        if importe is None:
                            log.warning(
                                f"  [{source_file}] No se encontro IMPORTE para comp {nro_comp} (CPs={cantidad})"
                            )
                            importe = abs(cantidad)

                        movement = {
                            'date': date_conc,
                            'type': op_types[op_line],
                            'cp': round(abs(cantidad), 2),
                            'amount': round(importe, 2),
                            'source': source_file,
                            'nro_comp': nro_comp,
                        }
                        all_funds[current_fund].append(movement)
                        i += 5  # Skip past the saldo line
                        continue
                    except (ValueError, IndexError):
                        pass

        # Reset fund on footer / new section
        if 'SALDO FINAL al' in line:
            current_fund = None

        i += 1


def _extract_portfolio_balances(full_text, source_file, portfolio_cps):
    """Extract final CP balances from 'ESTADO DE CARTERA VALORIZADA' section."""
    lines = full_text.split('\n')
    in_portfolio = False
    i = 0

    while i < len(lines):
        line = lines[i].strip()

        if 'ESTADO DE CARTERA VALORIZADA' in line:
            in_portfolio = True
            i += 1
            continue

        if in_portfolio and (line.startswith('FCI ') or line.startswith('SUPERGES ')):
            fund_name = line
            # Next lines: LD, CANTIDAD, PRECIO, IMPORTE
            if i + 3 < len(lines):
                ld_line = lines[i + 1].strip()
                cantidad_str = lines[i + 2].strip()
                if ld_line == 'LD':
                    try:
                        cp_val = clean_number(cantidad_str)
                        portfolio_cps[fund_name] = cp_val
                        log.debug(
                            f"  Portfolio [{fund_name}]: "
                            f"{cp_val:,.2f} CPs"
                        )
                    except ValueError:
                        pass
            i += 4
            continue

        # Stop at end of portfolio
        if in_portfolio and 'TOTAL' in line:
            in_portfolio = False

        i += 1


if __name__ == "__main__":
    success = extract_all_funds()
    sys.exit(0 if success else 1)
