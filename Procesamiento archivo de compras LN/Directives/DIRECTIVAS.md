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

## 2. Lógica de Importes Exentos y Netos Huérfanos
- **Rescate de Netos Huérfanos**: Si una fila tiene `IMP_NETO` pero su alícuota (`PORC_IVA`) no es estándar (21, 10.5, 27, 3, 1.5) o es 0/vacía, ese importe se considera **Exento/No Gravado**.
- **Destino Final**:
    - **Factura C**: `IMP_EXENTO` + `Neto Huérfano` -> **'Compras sin IVA'**.
    - **No es Factura C**: `IMP_EXENTO` + `Neto Huérfano` -> **'Conceptos no Gravados'**.

## 3. Lógica de Percepciones y Auto-Corrección (San Juan)
- **Asignación Inicial**: El valor de `OTROSIMP` se asigna temporalmente a **'Percepción IB San Juan'**.
- **Auto-Corrección (5. AUTO-CORRECCIÓN DE PERCEPCIONES)**:
    - Se calcula la **Base Imponible Total** = Suma de Netos Gravados + Conceptos no Gravados + Compras sin IVA.
    - Se comparan hipotesis de alícuotas:
        - **3%**: Si `Percepción` actual coincide con el 3% de la base (tol. 0.10), se MANTIENE.
        - **Defecto (1%)**: Si NO coincide con el 3%, se fuerza la percepción al **1%** de la base.
    - **Ajuste de Diferencia**: Si se recalculó al 1%, la diferencia (Saldo) se suma a **'Conceptos no Gravados'**.

## 4. Tratamiento de Percepciones de IVA (3% y 1.5%)
- Se deben consolidar las percepciones en la línea principal de la factura.
- Si una fila tiene `PORC_IVA` igual a **3.00** o **1.50**:
    - Su `IMP_IVA` se suma a la columna **'Retenc. / Percepc.'** de la **fila inmediata superior** (siempre que corresponda al mismo comprobante).
    - La fila de la percepción se elimina o ignora en la salida final, quedando todo consolidado en la fila principal.

## 5. Validación de Duplicados
- Se debe verificar la existencia de facturas repetidas basándose en el número de comprobante y CUIT.

## 6. Validación Visual
- **Alerta Amarilla**: Se deben pintar de color **amarillo** las filas donde:
    - El **Total** calculado no coincida con el `IMP_TOTAL` original del archivo de entrada.
    - La suma del **IVA** calculado (21% + 10.5% + 27%) no coincida con el `IMP_IVA` original (para las alícuotas correspondientes).
- Se permite una tolerancia mínima (0.02) por diferencias de redondeo.

## 7. Ordenamiento Final de Salida
Antes de guardar el archivo, se debe ordenar el listado consolidado siguiendo esta estricta jerarquía:
1.  **Por Categoría de Comprobante**:
    *   **1°**: Facturas A (Comprobante inicia con 'A').
    *   **2°**: Facturas C (Comprobante inicia con 'C').
    *   **3°**: Otros (Facturas B, M, Tickets, etc.).
    *   **Último**: Notas de Crédito (Tipo contiene 'N/C', 'NC' o 'CREDITO').
2.  **Por Razón Social**: Alfabético ascendente (A-Z).
3.  **Por Comprobante**: Numérico/Alfanumérico ascendente.

## 8. Ejecución del Script
El script `transform_excel.py` soporta argumentos de línea de comandos para especificar las rutas de entrada y salida de forma dinámica.

### Uso Básico (Rutas Default)
Ejecutar sin argumentos utilizará las rutas por defecto configuradas en el código:
`python transform_excel.py`

### Uso Avanzado (Argumentos)
Puede especificar rutas personalizadas usando `--input` y `--output`:
`python transform_excel.py --input "ruta/al/archivo.xlsx" --output "ruta/destino.xlsx"`
