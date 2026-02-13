import pandas as pd
import os
import argparse
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from openpyxl import load_workbook
from openpyxl.styles import PatternFill

# ==========================================
# CONFIGURACIÓN DE DEFAULTS
# ==========================================
DEFAULT_INPUT = r'C:\Users\Tuchi\MiEstudioIA\Input\202601 - IVA Compras.xlsx'
DEFAULT_OUTPUT = r'C:\Users\Tuchi\MiEstudioIA\Output\Gama_Compras_Procesado_Final.xlsx'

def to_decimal(val):
    """Convierte un valor a Decimal con 2 decimales de precisión."""
    if pd.isna(val):
        return Decimal('0.00')
    try:
        # Convertir a string primero evita problemas de precisión de float
        return Decimal(str(val)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    except (InvalidOperation, ValueError):
        return Decimal('0.00')

def parse_arguments():
    """Configura y parsea los argumentos de línea de comandos."""
    parser = argparse.ArgumentParser(description='Procesamiento de archivos de compras (LN) - Calidad Profesional')
    parser.add_argument('--input', type=str, default=DEFAULT_INPUT, 
                        help=f'Ruta del archivo Excel de entrada (Default: {DEFAULT_INPUT})')
    parser.add_argument('--output', type=str, default=DEFAULT_OUTPUT, 
                        help=f'Ruta del archivo Excel de salida (Default: {DEFAULT_OUTPUT})')
    return parser.parse_args()

def transform_excel(input_file, output_file):
    if not os.path.exists(input_file):
        print(f"Error: No se encuentra el archivo en {input_file}")
        return

    print(f"Procesando archivo: {input_file}")
    print(f"Destino: {output_file}")

    # 1. CARGA DE DATOS
    df_orig = pd.read_excel(input_file)
    
    # Conversión INMEDIATA a Decimal para columnas monetarias clave
    monetary_cols = ['IMP_NETO', 'IMP_IVA', 'IMP_TOTAL', 'IMP_EXENTO', 'OTROSIMP']
    for col in monetary_cols:
        if col in df_orig.columns:
            df_orig[col] = df_orig[col].apply(to_decimal)
    
    # Columnas objetivo del formato Gama
    columns_target = [
        'Fecha', 'Tipo', 'Comprobante', 'Razón Social', 'Cuit', 'Condic.',
        'Neto Gravado 21%', 'Neto Gravado 10,5%', 'Neto Gravado 27%',
        'Conceptos no Gravados', 'I.V.A 21%', 'I.V.A 10,5%', 'I.V.A 27%',
        'Compras sin IVA', 'Percepción IB San Juan', 'Retenc. / Percepc.', 'Total'
    ]

    # 2. PROCESAMIENTO FILA POR FILA
    temp_rows = []
    
    # Ordenamos por comprobante para asegurar que las filas del 3% o 1.5% estén juntas
    df_orig = df_orig.sort_values(by=['IDENTIFTRI', 'N_COMP', 'FECHA_EMI']).reset_index(drop=True)

    for i, row in df_orig.iterrows():
        n_comp = str(row['N_COMP']).strip()
        # Convertir porcentaje a float para comparaciones simples, o Decimal si se prefiere exactitud estricta
        # Usaremos comparación laxa para el tipo de alícuota (21, 10.5) pero Decimal para los cálculos
        p_iva = float(row['PORC_IVA']) if not pd.isna(row['PORC_IVA']) else 0.0
        
        imp_iva = row['IMP_IVA']   # Ya es Decimal
        imp_neto = row['IMP_NETO'] # Ya es Decimal
        imp_total = row['IMP_TOTAL'] # Ya es Decimal
        imp_exento = row['IMP_EXENTO'] # Ya es Decimal
        otros_imp = row['OTROSIMP'] # Ya es Decimal
        
        # --- REGLA: PERCEPCIONES 3% o 1.5% ---
        # Si coincide con el comprobante anterior, sumamos la percepción arriba y saltamos
        if i > 0 and p_iva in [3.0, 1.5] and n_comp == str(df_orig.loc[i-1, 'N_COMP']).strip():
            temp_rows[-1]['Retenc. / Percepc.'] += imp_iva
            # Guardamos el total original para validación posterior
            temp_rows[-1]['original_total_ref'] += imp_total
            continue

        # --- MAPEO BASE ---
        new_row = {col: Decimal('0.00') for col in columns_target}
        new_row['Fecha'] = row['FECHA_EMI']
        new_row['Tipo'] = row['T_COMP']
        new_row['Comprobante'] = n_comp
        new_row['Razón Social'] = row['NOM_PROVE']
        new_row['Cuit'] = row['IDENTIFTRI']
        new_row['Condic.'] = row['COND_IVA']
        
        # Guardar valores originales de Tango para el chequeo final
        new_row['original_total_ref'] = imp_total
        new_row['original_iva_ref'] = imp_iva if p_iva in [21.0, 10.5, 27.0] else Decimal('0.00')

        # --- REGLA: ALÍCUOTAS IVA ---
        # Nota: Usamos Decimal para los cálculos
        if p_iva == 21.0:
            new_row['Neto Gravado 21%'] = imp_neto
            new_row['I.V.A 21%'] = imp_iva
        elif p_iva == 10.5:
            new_row['Neto Gravado 10,5%'] = imp_neto
            new_row['I.V.A 10,5%'] = imp_iva
        elif p_iva == 27.0:
            new_row['Neto Gravado 27%'] = imp_neto
            new_row['I.V.A 27%'] = imp_iva
        elif p_iva in [3.0, 1.5]: 
            new_row['Retenc. / Percepc.'] = imp_iva

        # --- REGLA: FACTURA C Y CONCEPTOS NO GRAVADOS ---
        is_factura_c = n_comp.upper().startswith('C')
        if is_factura_c:
            new_row['Compras sin IVA'] = imp_exento
        else:
            # Otros Impuestos + Exento van a Conceptos No Gravados
            new_row['Conceptos no Gravados'] = imp_exento + otros_imp
            
        temp_rows.append(new_row)

    df_intermediate = pd.DataFrame(temp_rows)

    # 3. CONSOLIDACIÓN (Agrupar por CUIT y Comprobante)
    group_cols = ['Fecha', 'Tipo', 'Comprobante', 'Razón Social', 'Cuit', 'Condic.']
    
    # Definir columnas numéricas a sumar (todas menos las de grupo y strings)
    numeric_cols = [col for col in columns_target if col not in group_cols] + ['original_total_ref', 'original_iva_ref']
    
    # Agrupar: Para Decimal, sum no funciona directo en cython, usamos apply o lambda
    # Una forma robusta es convertir a float para groupby y volver, pero NO queremos perder precisión.
    # Panda's sum() might behave weirdly with Objects (Decimal).
    # Safer approach: Custom aggregation
    # df_consolidated = df_intermediate.groupby(group_cols, as_index=False)[numeric_cols].apply(lambda x: x.sum()) 
    # ^ Esto puede ser lento. Mejor: iterar sobre las columnas decimales.
    
    df_consolidated = df_intermediate.groupby(group_cols, as_index=False)[numeric_cols].sum()

    # 4. CÁLCULO DE TOTAL Y VALIDACIÓN
    cols_a_sumar = columns_target[6:16] # Columnas de importes
    
    # Suma horizontal con Decimals
    df_consolidated['Total'] = df_consolidated[cols_a_sumar].sum(axis=1)

    # Validacion con Tolerancia de Decimal
    TOLERANCE = Decimal('0.02')
    
    def check_diff(row):
        total_diff = abs(row['Total'] - row['original_total_ref']) > TOLERANCE
        iva_calc = row['I.V.A 21%'] + row['I.V.A 10,5%'] + row['I.V.A 27%']
        iva_diff = abs(iva_calc - row['original_iva_ref']) > TOLERANCE
        return total_diff or iva_diff

    df_consolidated['ERROR_VALIDACION'] = df_consolidated.apply(check_diff, axis=1)

    # 5. GUARDADO Y FORMATO
    df_final = df_consolidated[columns_target + ['ERROR_VALIDACION']].copy()
    
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    # IMPORTANTE: openpyxl no soporta Decimal nativamente en versiones viejas, 
    # pero pandas to_excel convierte a float al escribir si el motor es openpyxl?
    # No, escribirá objetos Decimal que Excel puede no entender o ver como texto.
    # Para asegurar compatibilidad FINAL con Excel (celdas numéricas), convertimos a float antes de guardar.
    # La precisión ya fue garantizada en los cálculos.
    
    # Convertir Decimals a float para el output final (Excel necesita floats/number format)
    for col in df_final.columns:
        if col not in group_cols and col != 'ERROR_VALIDACION':
            df_final[col] = df_final[col].apply(lambda x: float(x) if isinstance(x, Decimal) else x)

    df_final.to_excel(output_file, index=False)

    # Aplicar color amarillo
    wb = load_workbook(output_file)
    ws = wb.active
    yellow_fill = PatternFill(start_color="FFFF00", end_color="FFFF00", fill_type="solid")

    error_col_index = len(columns_target) + 1
    
    for row_idx in range(2, ws.max_row + 1):
        if ws.cell(row=row_idx, column=error_col_index).value == True:
            for col_idx in range(1, len(columns_target) + 1):
                ws.cell(row=row_idx, column=col_idx).fill = yellow_fill

    ws.delete_cols(error_col_index)
    
    wb.save(output_file)
    print(f"--- PROCESO FINALIZADO ---")
    print(f"Archivo generado: {output_file}")
    print(f"Se procesaron {len(df_final)} facturas consolidadas.")

if __name__ == "__main__":
    args = parse_arguments()
    transform_excel(args.input, args.output)
