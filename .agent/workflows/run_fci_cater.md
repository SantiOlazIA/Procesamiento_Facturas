---
description: Run the FCI Cater multi-fund pipeline to process Santander Valores PDF statements for CaterWest SA
---

To execute the FCI Cater pipeline:

1. **Revisión inicial**: Revisa los archivos PDF en `c:\Users\Tuchi\MiEstudioIA\FCI Cater\Input` para asegurarte de que corresponden a extractos de Santander Valores y están listos antes de procesarlos.

// turbo-all

2. Navigate to the pipeline directory and run the orchestrator

```bash
cd "c:\Users\Tuchi\MiEstudioIA\FCI Cater\Códigos integradores"
python run_pipeline.py
```

3. **Verificación final**: Opcionalmente, revisa el Excel generado en la carpeta Output para constatar que los asientos y los cálculos FIFO se realizaron con éxito.

4. Alternatively, launch the GUI for interactive use

```bash
cd "c:\Users\Tuchi\MiEstudioIA\FCI Cater\Códigos integradores"
python gui.py
```
