# Procesamiento de Archivos de Compras (LN)

Este documento resume las reglas de negocio y directivas para el procesamiento de archivos de facturas de compras.

## 1. Identificación de Datos y Mapeo
- Las filas de los archivos de entrada constituyen información de facturas de compras.
- **Mapeo de Columnas (Tango -> Salida)**:
    - `IDENTIFTRI` -> **Cuit**
    - `NOM_PROVE` -> **Razón Social**
    - `FECHA_EMI` -> **Fecha**
    - `T_COMP` -> **Tipo**
    - `N_COMP` -> **Comprobante**
    - `COND_IVA` -> **Condic.**

## 2. Lógica de Factura C y Conceptos
- **Factura C**: Si el comprobante (`N_COMP`) comienza con la letra **'C'**, el valor de `IMP_EXENTO` se asigna a la columna **'Compras sin IVA'**.
- **Otras Facturas**: Para el resto, la suma de `IMP_EXENTO` + `OTROSIMP` se asigna a la columna **'Conceptos no Gravados'**.

## 3. Tratamiento de Percepciones de IVA (3% y 1.5%)
- Se deben consolidar las percepciones en la línea principal de la factura.
- Si una fila tiene `PORC_IVA` igual a **3.00** o **1.50**:
    - Su `IMP_IVA` se suma a la columna **'Retenc. / Percepc.'** de la **fila inmediata superior** (siempre que corresponda al mismo comprobante).
    - La fila de la percepción se elimina o ignora en la salida final, quedando todo consolidado en la fila principal.

## 4. Validación de Duplicados
- Se debe verificar la existencia de facturas repetidas basándose en el número de comprobante y CUIT.

## 5. Validación Visual
- **Alerta Amarilla**: Se deben pintar de color **amarillo** las filas donde:
    - El **Total** calculado no coincida con el `IMP_TOTAL` original del archivo de entrada.
    - La suma del **IVA** calculado (21% + 10.5% + 27%) no coincida con el `IMP_IVA` original (para las alícuotas correspondientes).
- Se permite una tolerancia mínima (0.02) por diferencias de redondeo.

## 6. Ejecución del Script
El script `transform_excel.py` soporta argumentos de línea de comandos para especificar las rutas de entrada y salida de forma dinámica.

### Uso Básico (Rutas Default)
Ejecutar sin argumentos utilizará las rutas por defecto configuradas en el código:
`python transform_excel.py`

### Uso Avanzado (Argumentos)
Puede especificar rutas personalizadas usando `--input` y `--output`:
`python transform_excel.py --input "ruta/al/archivo.xlsx" --output "ruta/destino.xlsx"`
