"""
FCI Pipeline — Interfaz Grafica (Mejora 1)

Panel simple con tkinter para ejecutar el pipeline sin terminal.
Muestra progreso en tiempo real y permite seleccionar carpeta de PDFs.
"""
import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox
import subprocess
import sys
import os
import threading

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


class FCIApp:
    def __init__(self, root):
        self.root = root
        self.root.title("FCI Pipeline - Procesador de Fondos Comunes")
        self.root.geometry("720x580")
        self.root.resizable(True, True)
        self.root.configure(bg='#1e1e2e')
        
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('Title.TLabel', font=('Segoe UI', 16, 'bold'), 
                       foreground='#89b4fa', background='#1e1e2e')
        style.configure('Info.TLabel', font=('Segoe UI', 10), 
                       foreground='#cdd6f4', background='#1e1e2e')
        style.configure('Accent.TButton', font=('Segoe UI', 11, 'bold'),
                       padding=(20, 10))
        style.configure('Small.TButton', font=('Segoe UI', 9), padding=(10, 5))
        style.configure('Status.TLabel', font=('Segoe UI', 9),
                       foreground='#a6e3a1', background='#1e1e2e')
        
        # Title
        title = ttk.Label(root, text="Procesador FCI", style='Title.TLabel')
        title.pack(pady=(15, 5))
        
        subtitle = ttk.Label(root, text="Fondos Comunes de Inversion BBVA", style='Info.TLabel')
        subtitle.pack(pady=(0, 15))
        
        # PDF folder selector
        folder_frame = tk.Frame(root, bg='#1e1e2e')
        folder_frame.pack(fill='x', padx=20, pady=5)
        
        ttk.Label(folder_frame, text="Carpeta de PDFs:", style='Info.TLabel').pack(side='left')
        
        self.pdf_path = tk.StringVar(value=os.path.join(os.path.dirname(SCRIPT_DIR), 'Input'))
        path_entry = tk.Entry(folder_frame, textvariable=self.pdf_path, width=45,
                            bg='#313244', fg='#cdd6f4', insertbackground='#cdd6f4',
                            font=('Consolas', 9), relief='flat')
        path_entry.pack(side='left', padx=10, fill='x', expand=True)
        
        browse_btn = ttk.Button(folder_frame, text="...", command=self.browse_folder,
                              style='Small.TButton', width=3)
        browse_btn.pack(side='right')
        
        # Buttons
        btn_frame = tk.Frame(root, bg='#1e1e2e')
        btn_frame.pack(pady=15)
        
        self.run_btn = ttk.Button(btn_frame, text="Ejecutar Pipeline Completo",
                                 command=self.run_full_pipeline, style='Accent.TButton')
        self.run_btn.pack(side='left', padx=10)
        
        self.prep_btn = ttk.Button(btn_frame, text="Solo Preparar Template",
                                  command=self.run_prepare, style='Small.TButton')
        self.prep_btn.pack(side='left', padx=10)
        
        open_btn = ttk.Button(btn_frame, text="Abrir Excel",
                             command=self.open_excel, style='Small.TButton')
        open_btn.pack(side='left', padx=10)
        
        # Status
        self.status_var = tk.StringVar(value="Listo")
        status_label = ttk.Label(root, textvariable=self.status_var, style='Status.TLabel')
        status_label.pack(pady=5)
        
        # Progress bar
        self.progress = ttk.Progressbar(root, mode='determinate', length=680)
        self.progress.pack(padx=20, pady=5)
        
        # Console output
        console_label = ttk.Label(root, text="Consola:", style='Info.TLabel')
        console_label.pack(anchor='w', padx=20, pady=(10, 2))
        
        self.console = scrolledtext.ScrolledText(root, height=15, width=85,
                                                  bg='#11111b', fg='#a6e3a1',
                                                  font=('Consolas', 9),
                                                  insertbackground='#a6e3a1',
                                                  relief='flat', state='disabled')
        self.console.pack(padx=20, pady=(0, 15), fill='both', expand=True)
        
        self.running = False
    
    def browse_folder(self):
        folder = filedialog.askdirectory(initialdir=self.pdf_path.get())
        if folder:
            self.pdf_path.set(folder)
    
    def log(self, msg):
        self.console.configure(state='normal')
        self.console.insert('end', msg + '\n')
        self.console.see('end')
        self.console.configure(state='disabled')
        self.root.update_idletasks()
    
    def set_status(self, msg, color='#a6e3a1'):
        self.status_var.set(msg)
        self.root.update_idletasks()
    
    def run_script(self, script_name, step, total):
        """Run a pipeline script and capture output."""
        script_path = os.path.join(SCRIPT_DIR, script_name)
        self.set_status(f"Ejecutando {script_name}... ({step}/{total})")
        self.progress['value'] = (step / total) * 100
        self.log(f"\n>>> {script_name}")
        
        try:
            result = subprocess.run(
                [sys.executable, script_path],
                capture_output=True, text=True, cwd=SCRIPT_DIR,
                encoding='utf-8', errors='replace'
            )
            
            if result.stdout:
                for line in result.stdout.strip().split('\n'):
                    self.log(f"  {line}")
            
            if result.returncode != 0:
                self.log(f"  [ERROR] Codigo de retorno: {result.returncode}")
                if result.stderr:
                    for line in result.stderr.strip().split('\n')[:5]:
                        self.log(f"  STDERR: {line}")
                return False
            else:
                self.log(f"  [OK] Completado")
                return True
                
        except Exception as e:
            self.log(f"  [FATAL] {e}")
            return False
    
    def _run_pipeline_thread(self, scripts):
        """Execute pipeline in background thread."""
        self.running = True
        self.run_btn.configure(state='disabled')
        self.prep_btn.configure(state='disabled')
        
        self.console.configure(state='normal')
        self.console.delete('1.0', 'end')
        self.console.configure(state='disabled')
        
        self.log("=" * 55)
        self.log("   FCI PIPELINE — EJECUCION AUTOMATICA")
        self.log("=" * 55)
        
        success = True
        for i, script in enumerate(scripts, 1):
            if not self.run_script(script, i, len(scripts)):
                self.log(f"\n[!] Pipeline interrumpido en {script}")
                success = False
                break
        
        self.progress['value'] = 100
        
        if success:
            self.set_status("Pipeline completado exitosamente")
            self.log("\n" + "=" * 55)
            self.log("   PIPELINE FINALIZADO CON EXITO")
            self.log("=" * 55)
        else:
            self.set_status("Pipeline finalizado con errores")
        
        self.run_btn.configure(state='normal')
        self.prep_btn.configure(state='normal')
        self.running = False
    
    def run_full_pipeline(self):
        if self.running: return
        scripts = [
            'prepare_test.py',
            '1_extract_movements.py',
            '2_validate_input.py',
            '3_process_ledger.py',
            '4_verify_results.py'
        ]
        thread = threading.Thread(target=self._run_pipeline_thread, args=(scripts,), daemon=True)
        thread.start()
    
    def run_prepare(self):
        if self.running: return
        scripts = ['prepare_test.py']
        thread = threading.Thread(target=self._run_pipeline_thread, args=(scripts,), daemon=True)
        thread.start()
    
    def open_excel(self):
        excel_path = os.path.join(SCRIPT_DIR, 'FCI_Procesado_Anual.xlsx')
        if os.path.exists(excel_path):
            os.startfile(excel_path)
        else:
            messagebox.showinfo("Info", "El archivo Excel aun no existe.\nEjecuta el pipeline primero.")


def main():
    root = tk.Tk()
    app = FCIApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
