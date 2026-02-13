import sys
import os

# Add Execution folder to path to allow imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'Execution'))

try:
    from transform_excel import transform_excel
    print("Starting Invoice Processing Orchestrator...")
    transform_excel()
    print("Orchestration complete.")
except ImportError as e:
    print(f"Error importing execution modules: {e}")
except Exception as e:
    print(f"An unexpected error occurred: {e}")
