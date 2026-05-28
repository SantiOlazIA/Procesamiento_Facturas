"""
FCI Santander Pipeline - Orquestador (Modo Consola)

Runs extraction, then loops through each detected fund
to run validation -> prepare -> ledger -> verify.
"""
import subprocess
import sys
import os
import time
import glob
import json
import re

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def run_step(script_name, env=None):
    """Execute a pipeline step as a subprocess."""
    print(f"  > {script_name}")

    start_time = time.time()
    script_path = os.path.join(SCRIPT_DIR, script_name)

    try:
        result = subprocess.run(
            [sys.executable, script_path],
            cwd=SCRIPT_DIR, text=True,
            encoding='utf-8', errors='replace',
            check=False, env=env
        )

        elapsed = time.time() - start_time
        if result.returncode != 0:
            print(
                f"    [ERROR] {script_name} fallo "
                f"(codigo {result.returncode}, {elapsed:.1f}s)"
            )
            return False

        print(f"    [OK] {elapsed:.1f}s")
        return True

    except KeyboardInterrupt:
        print("\n\n!!! Interrumpido por el usuario")
        return False
    except Exception as e:
        print(f"    [FATAL] {e}")
        return False


def make_safe_filename(fund_name):
    """Convert a fund name into a filesystem-safe filename."""
    safe = fund_name.strip()
    safe = re.sub(r'[^\w\s-]', '', safe)
    safe = re.sub(r'\s+', '_', safe)
    return safe[:60]


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Pipeline FCI Santander - Multi-Fondo"
    )
    parser.add_argument(
        '--input', type=str,
        help='Directorio de entrada (contiene los PDFs)'
    )
    args = parser.parse_args()

    if args.input:
        if not os.path.exists(args.input):
            print(f"!!! Error: Directorio no existe: {args.input}")
            sys.exit(1)
        os.environ['FCI_INPUT_DIR'] = os.path.abspath(args.input)

    print("=" * 55)
    print("   FCI SANTANDER PIPELINE - MODO CONSOLA")
    print("=" * 55)

    total_start = time.time()

    # Step 1: Extract movements from all PDFs
    print("\n[PASO 1] Extraccion de movimientos")
    if not run_step('1_extract_movements.py'):
        print("!!! Extraccion fallida. Pipeline detenido.")
        sys.exit(1)

    # Discover which funds were extracted
    json_files = sorted(
        glob.glob(os.path.join(SCRIPT_DIR, 'movements_*.json'))
    )

    if not json_files:
        print("!!! No se generaron archivos de movimientos.")
        sys.exit(1)

    funds = []
    for jf in json_files:
        with open(jf, 'r', encoding='utf-8') as f:
            data = json.load(f)
        funds.append({
            'name': data.get('fund_name', 'Unknown'),
            'json_path': jf,
            'movements': len(data.get('movements', [])),
        })

    print(f"\nFondos detectados: {len(funds)}")
    for i, fund in enumerate(funds, 1):
        print(f"  {i}. {fund['name']} ({fund['movements']} mov.)")

    # Steps 2-5: Process each fund
    per_fund_steps = [
        '2_validate_input.py',
        'prepare.py',
        '3_process_ledger.py',
        '4_verify_results.py',
    ]

    success_count = 0
    for idx, fund in enumerate(funds, 1):
        print(f"\n{'='*55}")
        print(f"  FONDO {idx}/{len(funds)}: {fund['name']}")
        print(f"{'='*55}")

        safe_name = make_safe_filename(fund['name'])
        output_dir = os.path.join(os.path.dirname(SCRIPT_DIR), 'Output')
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(
            output_dir, f'FCI_Procesado_{safe_name}.xlsx'
        )

        env = os.environ.copy()
        env['FCI_JSON_PATH'] = fund['json_path']
        env['FCI_OUTPUT_FILE'] = output_file
        env['FCI_CURRENT_FUND'] = fund['name']

        fund_ok = True
        for step in per_fund_steps:
            if not run_step(step, env=env):
                fund_ok = False
                break

        if fund_ok:
            print(f"  [OK] {fund['name']} -> {output_file}")
            success_count += 1
        else:
            print(f"  [ERROR] {fund['name']} fallo")

    total_elapsed = time.time() - total_start
    print(f"\n{'='*55}")
    print(
        f"   RESULTADO: {success_count}/{len(funds)} fondos procesados "
        f"en {total_elapsed:.1f}s"
    )
    print("=" * 55)

    sys.exit(0 if success_count == len(funds) else 1)


if __name__ == "__main__":
    main()
