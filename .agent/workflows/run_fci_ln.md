---
description: Run the full FCI LN pipeline to process PDF movements and update the ledger for La Nobleza SRL. This includes extracting movements, validating data, preparing the templates, processing the ledger with FIFO logic, and verifying the final results.
---
To execute the FCI LN pipeline:

1. **Revisión inicial**: Revisa los archivos PDF en `c:\Users\Tuchi\MiEstudioIA\FCI LN\Input` para asegurarte de que son extractos válidos (formato Banco Francés/BBVA con COMPRA/VENTA FBA RENPEB).

2. Navigate to the pipeline directory
// turbo
3. Run the pipeline orchestrator script

```bash
cd "c:\Users\Tuchi\MiEstudioIA\FCI LN\Códigos integradores"
python run_pipeline.py
```

4. **Verificación final**: Chequea el archivo Excel procesado en la carpeta Output para confirmar que los resultados y saldos FIFO sean consistentes.
