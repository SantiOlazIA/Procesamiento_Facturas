# Procesamiento de Archivos de Compras (LN)

Este documento resume las reglas de negocio y directivas para el procesamiento de archivos de facturas de compras.

## 1. Identificación de Datos
- Las filas de los archivos de entrada (e.g., `Libro1.xlsx`), a excepción de la primera (encabezado), constituyen información de **facturas de compras**.

## 2. Validación de Duplicados
- Se debe verificar la existencia de números de factura repetidos en la columna **`N_COMP`**.

## 3. Tratamiento de Percepciones de IVA
Se deben aplicar las siguientes transformaciones:
1. **Nueva Columna**: Crear una columna a la derecha llamada **"Percepciones de IVA"**.
2. **Transferencia de Valores**: Si en la columna **`PORC_IVA`** el valor es **"3.00"**:
    - Buscar el valor correspondiente en la columna **`IMP_IVA`**.
    - Mover dicho valor a la celda de la columna **"Percepciones de IVA"** en la **fila inmediata superior**.
3. **Eliminación de Fila**: Una vez transferido el valor, se debe **eliminar la fila** que contenía el valor "3.00" en `PORC_IVA`.
