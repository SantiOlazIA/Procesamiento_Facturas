# MiEstudioIA - Procesamiento de Facturas y FCIs

Este repositorio contiene las herramientas de automatización para el procesamiento de facturas, extractos bancarios y movimientos de Fondos Comunes de Inversión (FCI).

## Estructura del Proyecto

- `FCI LN/`: Procesamiento de movimientos para La Nobleza SRL.
- `FCI Cater/`: Procesamiento de extractos de Santander Valores para CaterWest SA.
- `Procesamiento Extractos/`:Scripts generales de extracción y clasificación.
- `Vtas CW/`: Análisis y reporte de ventas.

## Configuración Inicial

1. **Dependencias de Python**:
   Instala las librerías necesarias:
   ```bash
   pip install -r requirements.txt
   ```

2. **Variables de Entorno**:
   Copia el archivo `.env.example` a `.env` y completa las credenciales de Supabase, Google Cloud y Gmail.
   ```bash
   cp .env.example .env
   ```

3. **Credenciales de Google Drive**:
   Si utilizas la sincronización con Drive, asegúrate de tener el archivo `credenciales_drive.json` en la raíz.

## Flujos de Trabajo (Workflows)

Puedes utilizar los siguientes comandos para ejecutar los procesos principales:
- `run_fci_ln`: Procesa movimientos de FCI para La Nobleza.
- `run_fci_cater`: Procesa extractos de Santander para CaterWest.
- `run_compras_ln`: Procesa el archivo de compras.

Los archivos de entrada deben colocarse en las carpetas `Input/` correspondientes a cada módulo.
