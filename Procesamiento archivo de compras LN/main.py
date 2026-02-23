import sys
import os

# Add Execution folder to path to allow imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'Execution'))

try:
    from transform_excel import transform_excel
    import argparse
    
    parser = argparse.ArgumentParser(description="Orchestrator for Compras LN")
    parser.add_argument("--input", default=r'C:\Users\Tuchi\MiEstudioIA\Input\202601 - IVA Compras.xlsx', help="Path to input Excel file")
    parser.add_argument("--output", default=r'C:\Users\Tuchi\MiEstudioIA\Output\Gama_Compras_Procesado_Final.xlsx', help="Path to output Excel file")
    
    args = parser.parse_args()
    
    print(f"Starting Invoice Processing Orchestrator...")
    print(f"Input: {args.input}")
    print(f"Output: {args.output}")
    
    transform_excel(args.input, args.output)
    print("Orchestration complete.")
except ImportError as e:
    print(f"Error importing execution modules: {e}")
except Exception as e:
    print(f"An unexpected error occurred: {e}")
