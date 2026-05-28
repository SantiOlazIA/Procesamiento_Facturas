# DIRECTIVAS — FCI Pipeline

## Estructura del Proyecto

```
FCI/
├── Input/                          # PDFs de resúmenes bancarios
│   ├── FONDO COMUN DE INVERSION *.pdf
│   └── Formato FCI v2.xlsx         # Template de referencia
├── Códigos integradores/
│   ├── config.py                   # Configuración + logging
│   ├── prepare_test.py             # Prepara template (auto-detect)
│   ├── 1_extract_movements.py      # PDF → JSON
│   ├── 2_validate_input.py         # Validación de datos
│   ├── 3_process_ledger.py         # Motor FIFO + asientos + formato
│   ├── 4_verify_results.py         # Verificación cruzada
│   ├── run_pipeline.py             # Orquestador por terminal
│   ├── gui.py                      # Interfaz gráfica
│   ├── tests.py                    # 43 tests unitarios
│   ├── movements.json              # Datos extraídos (intermedio)
│   ├── Template_FCI.xlsx           # Template limpio (regenerable)
│   ├── FCI_Procesado_Anual.xlsx    # RESULTADO FINAL
│   └── logs/                       # Logs con timestamps
└── Directives/
    └── DIRECTIVAS.md               # Este archivo
```

## Reglas de Formato Excel

### Bordes (patrón REF de Formato FCI v2.xlsx)
- **Suscripción** (4 filas): header B-H top, F box, footer bottom
- **Rescate** (5 filas): header B-H top, F box, footer bottom
- Limpiar TODOS los bordes B-H al preparar template (evita residuos V2)

### Formato numérico
- Montos (AB, AE, AD, G, H): `#,##0.00`
- CPs (Z, AC, AF, AG): `#,##0.00`
- Cotización (AA): `#,##0.0000000000`
- Fechas (W): `DD/MM/YYYY`

### Headers cuadro (fila 4, W-AG)
- Fondo azul `#4472C4`, texto blanco, negrita, centrado
- Labels: Fecha, Concepto, Código, Cuotas parte, Cotización, Importe Cta Cte, Saldo en CP, Renta rescate, Saldo en $, Prueba, Prueba

### Colores FIFO
Paleta de 16 colores: rojo, verde, azul, amarillo + variantes (naranja, violeta, teal, coral, lima, cielo, rosa, oro, lavanda, menta, salmón, cian)

### Columnas Prueba (AF/AG)
- `AF = IF(+AB>1,+AB,-AB)/AA`
- `AG = +AF-IF(Y=1,+Z,-Z)`
- Resultado esperado: AG = 0 en todas las filas

## Filtro de fechas
- Usa `>=` (no `>`) para incluir movimientos del mismo día
- La suscripción inicial se auto-detecta del primer COMPRA en movements.json

## Ejecución
- **Terminal**: `python run_pipeline.py`
- **GUI**: `python gui.py`
- **Tests**: `python tests.py`

## Dependencias
- `openpyxl` — Excel
- `pypdf` — PDFs
- `tkinter` — GUI (incluido en Python)
