import subprocess
import sys
import os
import time

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

def run_step(script_name):
    print(f"\n{'='*60}")
    print(f">>> EJECUTANDO: {script_name}")
    print(f"{'='*60}")
    
    start_time = time.time()
    script_path = os.path.join(SCRIPT_DIR, script_name)
    
    try:
        # Run subprocess and wait for output
        result = subprocess.run(
            [sys.executable, script_path],
            cwd=SCRIPT_DIR,
            text=True,
            check=False 
        )
        
        elapsed = time.time() - start_time
        print(f"\n>>> Finalizado en {elapsed:.2f} segundos. Codigo de retorno: {result.returncode}")
        
        return result.returncode == 0
        
    except KeyboardInterrupt:
        print("\n\n!!! Interrumpido por el usuario")
        return False
    except Exception as e:
        print(f"\n!!! Error ejecutando {script_name}: {e}")
        return False

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Pipeline FCI - Automatización de Fondos Comunes de Inversión")
    parser.add_argument('--input', type=str, help='Directorio de entrada (contiene los PDFs)')
    parser.add_argument('--output', type=str, help='Archivo de salida (Excel final)')
    args = parser.parse_args()

    # Set environment variables for subprocesses (config.py will read these)
    if args.input:
        if not os.path.exists(args.input):
            print(f"!!! Error: El directorio de entrada especificado no existe: {args.input}")
            sys.exit(1)
        os.environ['FCI_INPUT_DIR'] = os.path.abspath(args.input)
        print(f">>> Usando directorio de entrada personalizado: {os.environ['FCI_INPUT_DIR']}")
    
    if args.output:
        os.environ['FCI_OUTPUT_FILE'] = os.path.abspath(args.output)
        print(f">>> Usando archivo de salida personalizado: {os.environ['FCI_OUTPUT_FILE']}")

    steps = [
        '1_extract_movements.py',
        '2_validate_input.py',
        'prepare_test.py',
        '3_process_ledger.py',
        '4_verify_results.py'
    ]
    
    print("INICIANDO PIPELINE FCI (Modo Consola)")
    print(f"Directorio base script: {SCRIPT_DIR}")
    
    total_start = time.time()
    
    for i, script in enumerate(steps, 1):
        print(f"\n[PASO {i}/{len(steps)}]")
        success = run_step(script)
        if not success:
            print(f"\n!!! EL PIPELINE SE DETUVO POR ERROR EN EL PASO {i}")
            sys.exit(1)
            
    total_elapsed = time.time() - total_start
    print(f"\n{'='*60}")
    print(f"PIPELINE COMPLETADO EXITOSAMENTE en {total_elapsed:.2f} segundos")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
