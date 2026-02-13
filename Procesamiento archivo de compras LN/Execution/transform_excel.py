import pandas as pd
import os
from openpyxl import load_workbook
from openpyxl.styles import PatternFill

# ==========================================
# CONFIGURACIÓN DE RUTAS
# ==========================================
INPUT_FILE = r'C:\Users\Tuchi\MiEstudioIA\Input\202601 - IVA Compras.xlsx'
OUTPUT_FILE = r'C:\Users\Tuchi\MiEstudioIA\Output\Gama_Compras_Procesado_Final.xlsx'

def transform_excel():
    if not os.path.exists(INPUT_FILE):
        print(f"Error: No se encuentra el archivo en {INPUT_FILE}")
        return

    # 1. CARGA DE DATOS
    df_orig = pd.read_excel(INPUT_FILE)
    
    # Columnas objetivo del formato Gama
    columns_target = [
        'Fecha', 'Tipo', 'Comprobante', 'Razón Social', 'Cuit', 'Condic.',
        'Neto Gravado 21%', 'Neto Gravado 10,5%', 'Neto Gravado 27%',
        'Conceptos no Gravados', 'I.V.A 21%', 'I.V.A 10,5%', 'I.V.A 27%',
        'Compras sin IVA', 'Percepción IB San Juan', 'Retenc. / Percepc.', 'Total'
    ]

    # 2. PROCESAMIENTO FILA POR FILA (Lógica de Percepciones y Factura C)
    temp_rows = []
    
    # Ordenamos por comprobante para asegurar que las filas del 3% o 1.5% estén juntas
    df_orig = df_orig.sort_values(by=['IDENTIFTRI', 'N_COMP', 'FECHA_EMI']).reset_index(drop=True)

    for i, row in df_orig.iterrows():
        n_comp = str(row['N_COMP']).strip()
        p_iva = row['PORC_IVA']
        imp_iva = row['IMP_IVA']
        
        # --- REGLA: PERCEPCIONES 3% o 1.5% ---
        # Si coincide con el comprobante anterior, sumamos la percepción arriba y saltamos
        if i > 0 and p_iva in [3, 1.5] and n_comp == str(df_orig.loc[i-1, 'N_COMP']).strip():
            temp_rows[-1]['Retenc. / Percepc.'] += imp_iva
            # Guardamos el total original para validación posterior
            temp_rows[-1]['original_total_ref'] += row['IMP_TOTAL'] 
            continue

        # --- MAPEO BASE ---
        new_row = {col: 0.0 for col in columns_target}
        new_row['Fecha'] = row['FECHA_EMI']
        new_row['Tipo'] = row['T_COMP']
        new_row['Comprobante'] = n_comp
        new_row['Razón Social'] = row['NOM_PROVE']
        new_row['Cuit'] = row['IDENTIFTRI']
        new_row['Condic.'] = row['COND_IVA']
        
        # Guardar valores originales de Tango para el chequeo final
        new_row['original_total_ref'] = row['IMP_TOTAL']
        new_row['original_iva_ref'] = row['IMP_IVA'] if p_iva in [21, 10.5, 27] else 0.0

        # --- REGLA: ALÍCUOTAS IVA ---
        if p_iva == 21:
            new_row['Neto Gravado 21%'] = row['IMP_NETO']
            new_row['I.V.A 21%'] = row['IMP_IVA']
        elif p_iva == 10.5:
            new_row['Neto Gravado 10,5%'] = row['IMP_NETO']
            new_row['I.V.A 10,5%'] = row['IMP_IVA']
        elif p_iva == 27:
            new_row['Neto Gravado 27%'] = row['IMP_NETO']
            new_row['I.V.A 27%'] = row['IMP_IVA']
        elif p_iva in [3, 1.5]: # Si es la primera fila del comprobante y es percepción
            new_row['Retenc. / Percepc.'] = row['IMP_IVA']

        # --- REGLA: FACTURA C Y CONCEPTOS NO GRAVADOS ---
        is_factura_c = n_comp.upper().startswith('C')
        if is_factura_c:
            new_row['Compras sin IVA'] = row['IMP_EXENTO']
        else:
            # Otros Impuestos + Exento van a Conceptos No Gravados
            new_row['Conceptos no Gravados'] = row['IMP_EXENTO'] + row['OTROSIMP']
            
        temp_rows.append(new_row)

    df_intermediate = pd.DataFrame(temp_rows)

    # 3. CONSOLIDACIÓN (Agrupar por CUIT y Comprobante)
    # Esto une las filas que tengan diferentes alícuotas (21 y 10.5) en una misma factura
    group_cols = ['Fecha', 'Tipo', 'Comprobante', 'Razón Social', 'Cuit', 'Condic.']
    
    # Sumamos todas las columnas numéricas pero mantenemos las referencias originales para validar
    agg_map = {col: 'sum' for col in columns_target if col not in group_cols}
    agg_map['original_total_ref'] = 'sum'
    agg_map['original_iva_ref'] = 'sum'
    
    df_consolidated = df_intermediate.groupby(group_cols, as_index=False).agg(agg_map)

    # 4. CÁLCULO DE TOTAL Y VALIDACIÓN
    cols_a_sumar = columns_target[6:16] # Columnas de importes (Netos, IVAs, Retenciones, etc.)
    df_consolidated['Total'] = df_consolidated[cols_a_sumar].sum(axis=1)

    # Creamos una columna temporal para saber si hay que pintar de amarillo
    # Tolerancia de 0.01 para evitar errores por decimales (floats)
    def check_diff(row):
        total_diff = abs(row['Total'] - row['original_total_ref']) > 0.02
        iva_calc = row['I.V.A 21%'] + row['I.V.A 10,5%'] + row['I.V.A 27%']
        iva_diff = abs(iva_calc - row['original_iva_ref']) > 0.02
        return total_diff or iva_diff

    df_consolidated['ERROR_VALIDACION'] = df_consolidated.apply(check_diff, axis=1)

    # 5. GUARDADO Y FORMATO (Openpyxl)
    df_final = df_consolidated[columns_target + ['ERROR_VALIDACION']]
    
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    df_final.to_excel(OUTPUT_FILE, index=False)

    # Aplicar color amarillo a las filas con error
    wb = load_workbook(OUTPUT_FILE)
    ws = wb.active
    yellow_fill = PatternFill(start_color="FFFF00", end_color="FFFF00", fill_type="solid")

    # Recorrer las filas para pintar (empezamos en fila 2 por el encabezado)
    # La columna ERROR_VALIDACION es la última (columna 18)
    error_col_index = len(columns_target) + 1
    
    for row_idx in range(2, ws.max_row + 1):
        if ws.cell(row=row_idx, column=error_col_index).value == True:
            for col_idx in range(1, len(columns_target) + 1):
                ws.cell(row=row_idx, column=col_idx).fill = yellow_fill

    # Eliminar la columna de error antes de guardar
    ws.delete_cols(error_col_index)
    
    wb.save(OUTPUT_FILE)
    print(f"--- PROCESO FINALIZADO ---")
    print(f"Archivo generado: {OUTPUT_FILE}")
    print(f"Se procesaron {len(df_final)} facturas consolidadas.")

if __name__ == "__main__":
    transform_excel()
