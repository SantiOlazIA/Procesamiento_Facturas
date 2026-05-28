"""
FCI Santander Pipeline - Interfaz Grafica

Dark-themed tkinter GUI with:
- Drag-and-drop / file browser to load PDFs into Input folder
- Auto-scan to detect FCIs in the loaded PDFs
- Dynamic buttons per detected FCI + "Procesar Todos"
- Real-time console output and progress bar
"""
import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext
import subprocess
import sys
import os
import shutil
import threading
import json
import glob

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(SCRIPT_DIR)

# Colors - Catppuccin Mocha theme
BG = '#1e1e2e'
BG_SURFACE = '#313244'
BG_DARK = '#11111b'
TEXT = '#cdd6f4'
TEXT_DIM = '#a6adc8'
GREEN = '#a6e3a1'
BLUE = '#89b4fa'
RED = '#f38ba8'
YELLOW = '#f9e2af'
MAUVE = '#cba6f7'


class FCISantanderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("FCI Santander - Procesador Multi-Fondo")
        self.root.geometry("800x700")
        self.root.resizable(True, True)
        self.root.configure(bg=BG)
        self.running = False
        self.detected_funds = []

        self._setup_styles()
        self._build_header()
        self._build_pdf_loader()
        self._build_fund_panel()
        self._build_console()

    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure(
            'Title.TLabel', font=('Segoe UI', 16, 'bold'),
            foreground=BLUE, background=BG
        )
        style.configure(
            'Info.TLabel', font=('Segoe UI', 10),
            foreground=TEXT, background=BG
        )
        style.configure(
            'Status.TLabel', font=('Segoe UI', 9),
            foreground=GREEN, background=BG
        )
        style.configure(
            'Accent.TButton', font=('Segoe UI', 11, 'bold'),
            padding=(15, 8)
        )
        style.configure(
            'Fund.TButton', font=('Segoe UI', 10),
            padding=(12, 6)
        )
        style.configure(
            'Small.TButton', font=('Segoe UI', 9),
            padding=(10, 5)
        )

    def _build_header(self):
        ttk.Label(
            self.root, text="Procesador FCI Santander",
            style='Title.TLabel'
        ).pack(pady=(15, 3))
        ttk.Label(
            self.root, text="Fondos Comunes de Inversion - Santander Valores",
            style='Info.TLabel'
        ).pack(pady=(0, 10))

    def _build_pdf_loader(self):
        frame = tk.LabelFrame(
            self.root, text=" Cargar PDFs ", bg=BG, fg=TEXT,
            font=('Segoe UI', 10, 'bold'), padx=10, pady=10
        )
        frame.pack(fill='x', padx=20, pady=5)

        # Drop zone
        self.drop_zone = tk.Label(
            frame,
            text=(
                "Arrastra archivos PDF aqui\n"
                "o usa el boton para seleccionarlos"
            ),
            bg=BG_SURFACE, fg=TEXT_DIM,
            font=('Segoe UI', 10),
            relief='groove', padx=20, pady=20,
            width=60, height=3
        )
        self.drop_zone.pack(fill='x', pady=(0, 8))

        btn_frame = tk.Frame(frame, bg=BG)
        btn_frame.pack(fill='x')

        ttk.Button(
            btn_frame, text="Seleccionar PDFs...",
            command=self._browse_pdfs, style='Small.TButton'
        ).pack(side='left', padx=(0, 10))

        ttk.Button(
            btn_frame, text="Escanear Fondos",
            command=self._scan_funds, style='Accent.TButton'
        ).pack(side='left', padx=(0, 10))

        ttk.Button(
            btn_frame, text="Abrir Carpeta Input",
            command=self._open_input_folder, style='Small.TButton'
        ).pack(side='right')

        # File count label
        self.file_count_var = tk.StringVar(value="")
        tk.Label(
            frame, textvariable=self.file_count_var,
            bg=BG, fg=TEXT_DIM, font=('Segoe UI', 9)
        ).pack(anchor='w', pady=(5, 0))

    def _build_fund_panel(self):
        self.fund_frame = tk.LabelFrame(
            self.root, text=" Fondos Detectados ", bg=BG, fg=TEXT,
            font=('Segoe UI', 10, 'bold'), padx=10, pady=10
        )
        self.fund_frame.pack(fill='x', padx=20, pady=5)

        self.fund_placeholder = tk.Label(
            self.fund_frame,
            text="Escanea los PDFs para detectar los fondos disponibles",
            bg=BG, fg=TEXT_DIM, font=('Segoe UI', 9, 'italic')
        )
        self.fund_placeholder.pack(pady=5)

        # Status + Progress
        status_frame = tk.Frame(self.root, bg=BG)
        status_frame.pack(fill='x', padx=20, pady=5)

        self.status_var = tk.StringVar(value="Listo")
        ttk.Label(
            status_frame, textvariable=self.status_var,
            style='Status.TLabel'
        ).pack(side='left')

        self.progress = ttk.Progressbar(
            self.root, mode='determinate', length=760
        )
        self.progress.pack(padx=20, pady=5)

    def _build_console(self):
        ttk.Label(
            self.root, text="Consola:", style='Info.TLabel'
        ).pack(anchor='w', padx=20, pady=(8, 2))

        self.console = scrolledtext.ScrolledText(
            self.root, height=12, bg=BG_DARK, fg=GREEN,
            font=('Consolas', 9), insertbackground=GREEN,
            relief='flat', state='disabled'
        )
        self.console.pack(
            padx=20, pady=(0, 15), fill='both', expand=True
        )

    # --- Actions ---

    def _browse_pdfs(self):
        files = filedialog.askopenfilenames(
            title="Seleccionar PDFs de Santander",
            filetypes=[("PDF files", "*.pdf")],
            initialdir=os.path.expanduser("~")
        )
        if files:
            self._copy_pdfs_to_input(files)

    def _copy_pdfs_to_input(self, file_paths):
        input_dir = os.path.join(os.path.dirname(SCRIPT_DIR), 'Input')
        os.makedirs(input_dir, exist_ok=True)

        copied = 0
        for src in file_paths:
            dest = os.path.join(input_dir, os.path.basename(src))
            if not os.path.exists(dest):
                shutil.copy2(src, dest)
                copied += 1
                self._log(f"  Copiado: {os.path.basename(src)}")
            else:
                self._log(
                    f"  Omitido (ya existe): {os.path.basename(src)}"
                )

        self._log(f"Se copiaron {copied} archivos nuevos a Input/")
        self._update_file_count()

    def _update_file_count(self):
        input_dir = os.path.join(os.path.dirname(SCRIPT_DIR), 'Input')
        if os.path.exists(input_dir):
            pdfs = [
                f for f in os.listdir(input_dir)
                if f.lower().endswith('.pdf')
            ]
            self.file_count_var.set(
                f"{len(pdfs)} archivo(s) PDF en la carpeta Input"
            )

    def _open_input_folder(self):
        input_dir = os.path.join(os.path.dirname(SCRIPT_DIR), 'Input')
        os.makedirs(input_dir, exist_ok=True)
        os.startfile(input_dir)

    def _scan_funds(self):
        if self.running:
            return
        self._update_file_count()
        thread = threading.Thread(
            target=self._scan_funds_thread, daemon=True
        )
        thread.start()

    def _scan_funds_thread(self):
        self.running = True
        self._set_status("Escaneando PDFs...")
        self._log("\n>>> Escaneando PDFs para detectar fondos...")

        success = self._run_script('1_extract_movements.py', 1, 1)
        if not success:
            self._log("[ERROR] Fallo en la extraccion")
            self._set_status("Error en escaneo")
            self.running = False
            return

        # Read generated JSON files to discover funds
        json_files = sorted(
            glob.glob(os.path.join(SCRIPT_DIR, 'movements_*.json'))
        )

        self.detected_funds = []
        for jf in json_files:
            with open(jf, 'r', encoding='utf-8') as f:
                data = json.load(f)
            fund_name = data.get('fund_name', 'Unknown')
            n_movements = len(data.get('movements', []))
            init_bal = data.get('initial_balance', 0.0)
            self.detected_funds.append({
                'name': fund_name,
                'json_path': jf,
                'movements': n_movements,
                'initial_balance': init_bal,
            })

        # Update the GUI on the main thread
        self.root.after(0, self._render_fund_buttons)
        self._set_status(
            f"Escaneo completo: {len(self.detected_funds)} fondos detectados"
        )
        self.running = False

    def _render_fund_buttons(self):
        # Clear existing widgets
        for widget in self.fund_frame.winfo_children():
            widget.destroy()

        if not self.detected_funds:
            tk.Label(
                self.fund_frame,
                text="No se detectaron fondos en los PDFs",
                bg=BG, fg=RED, font=('Segoe UI', 10)
            ).pack(pady=5)
            return

        # One button per fund
        for fund in self.detected_funds:
            row = tk.Frame(self.fund_frame, bg=BG)
            row.pack(fill='x', pady=3)

            label_text = (
                f"{fund['name']}  "
                f"({fund['movements']} movimientos)"
            )
            tk.Label(
                row, text=label_text, bg=BG, fg=TEXT,
                font=('Segoe UI', 10), anchor='w'
            ).pack(side='left', fill='x', expand=True)

            btn = ttk.Button(
                row, text="Procesar",
                command=lambda f=fund: self._process_single_fund(f),
                style='Fund.TButton'
            )
            btn.pack(side='right', padx=5)

        # Separator + Process All
        ttk.Separator(self.fund_frame).pack(fill='x', pady=8)

        process_all_btn = ttk.Button(
            self.fund_frame, text="Procesar Todos",
            command=self._process_all_funds, style='Accent.TButton'
        )
        process_all_btn.pack(pady=5)

    def _process_single_fund(self, fund):
        if self.running:
            return
        thread = threading.Thread(
            target=self._process_fund_thread,
            args=([fund],), daemon=True
        )
        thread.start()

    def _process_all_funds(self):
        if self.running:
            return
        thread = threading.Thread(
            target=self._process_fund_thread,
            args=(self.detected_funds,), daemon=True
        )
        thread.start()

    def _process_fund_thread(self, funds):
        self.running = True
        total = len(funds)
        self._clear_console()
        self._log("=" * 55)
        self._log("   FCI SANTANDER - PROCESAMIENTO")
        self._log("=" * 55)

        success_count = 0
        for idx, fund in enumerate(funds, 1):
            self._set_status(
                f"Procesando {fund['name']} ({idx}/{total})..."
            )
            self._log(f"\n>>> Fondo {idx}/{total}: {fund['name']}")
            self.progress['value'] = ((idx - 1) / total) * 100

            safe_name = os.path.splitext(
                os.path.basename(fund['json_path'])
            )[0].replace('movements_', '')
            output_dir = os.path.join(
                os.path.dirname(SCRIPT_DIR), 'Output'
            )
            os.makedirs(output_dir, exist_ok=True)
            output_file = os.path.join(
                output_dir, f'FCI_Procesado_{safe_name}.xlsx'
            )

            env = os.environ.copy()
            env['FCI_JSON_PATH'] = fund['json_path']
            env['FCI_OUTPUT_FILE'] = output_file
            env['FCI_CURRENT_FUND'] = fund['name']

            steps = [
                '2_validate_input.py',
                'prepare.py',
                '3_process_ledger.py',
                '4_verify_results.py',
            ]

            fund_ok = True
            for step in steps:
                if not self._run_script(step, idx, total, env=env):
                    self._log(f"  [ERROR] Fallo en {step}")
                    fund_ok = False
                    break

            if fund_ok:
                self._log(f"  [OK] {fund['name']} completado")
                success_count += 1

        self.progress['value'] = 100
        self._log(f"\n{'='*55}")
        self._log(
            f"   RESULTADO: {success_count}/{total} fondos procesados"
        )
        self._log("=" * 55)
        self._set_status(
            f"Completado: {success_count}/{total} fondos"
        )
        self.running = False

    # --- Helpers ---

    def _run_script(self, script_name, step=1, total=1, env=None):
        script_path = os.path.join(SCRIPT_DIR, script_name)
        self._log(f"\n  > {script_name}")

        try:
            result = subprocess.run(
                [sys.executable, script_path],
                capture_output=True, text=True, cwd=SCRIPT_DIR,
                encoding='utf-8', errors='replace',
                env=env
            )

            if result.stdout:
                for line in result.stdout.strip().split('\n'):
                    self._log(f"    {line}")

            if result.returncode != 0:
                self._log(
                    f"    [ERROR] Codigo de retorno: {result.returncode}"
                )
                if result.stderr:
                    for line in result.stderr.strip().split('\n')[:5]:
                        self._log(f"    STDERR: {line}")
                return False

            return True

        except Exception as e:
            self._log(f"    [FATAL] {e}")
            return False

    def _log(self, msg):
        self.console.configure(state='normal')
        self.console.insert('end', msg + '\n')
        self.console.see('end')
        self.console.configure(state='disabled')
        self.root.update_idletasks()

    def _clear_console(self):
        self.console.configure(state='normal')
        self.console.delete('1.0', 'end')
        self.console.configure(state='disabled')

    def _set_status(self, msg):
        self.status_var.set(msg)
        self.root.update_idletasks()


def main():
    root = tk.Tk()
    FCISantanderApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
