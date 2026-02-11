import pandas as pd
import numpy as np
import os

# ==========================================
# CONFIGURACIÓN - Cambia estas rutas aquí
# ==========================================
INPUT_FILE = r'c:\Users\Tuchi\.gemini\antigravity\scratch\doe-project\data\input\2025 12 Gama compras.xlsx'
OUTPUT_FILE = r'c:\Users\Tuchi\.gemini\antigravity\scratch\doe-project\data\output\2025_12_Gama_Compras_Transformado_Final.xlsx'
# ==========================================

def transform_excel():
    # 1. Cargar el archivo original
    try:
        df = pd.read_excel(INPUT_FILE)
        print(f"Archivo cargado correctamente: {os.path.basename(INPUT_FILE)}")
    except Exception as e:
        print(f"Error al cargar el archivo: {e}")
        return

    # 2. Preparar el DataFrame de salida (Sin deduplicación inicial)
    columns_target = [
        'Fecha', 'Tipo', 'Comprobante', 'Razón Social', 'Cuit', 'Condic.',
        'Neto Gravado 21%', 'Neto Gravado 10,5%', 'Neto Gravado 27%',
        'Conceptos no Gravados', 'I.V.A 21%', 'I.V.A 10,5%', 'I.V.A 27%',
        'Compras sin IVA', 'Percepción IB San Juan', 'Retenc. / Percepc.', 'Total'
    ]

    # Mapear columnas básicas
    df['Fecha'] = df['FECHA_EMI']
    df['Tipo'] = df['T_COMP']
    df['Comprobante'] = df['N_COMP']
    df['Razón Social'] = df['NOM_PROVE']
    df['Cuit'] = df['IDENTIFTRI']
    df['Condic.'] = df['COND_IVA']
    
    # Mapeo de OTROSIMP -> Percepción IB San Juan
    df['Percepción IB San Juan'] = df['OTROSIMP'].fillna(0)
    
    # Inicializar el resto de columnas numéricas
    cols_to_init = [
        'Neto Gravado 21%', 'Neto Gravado 10,5%', 'Neto Gravado 27%',
        'Conceptos no Gravados', 'I.V.A 21%', 'I.V.A 10,5%', 'I.V.A 27%',
        'Compras sin IVA', 'Retenc. / Percepc.'
    ]
    for col in cols_to_init:
        df[col] = 0.0

    # 3. Cálculos de Neto Gravado basados en IVA
    for index, row in df.iterrows():
        p_iva = row['PORC_IVA']
        imp_iva = row['IMP_IVA']
        imp_neto = row['IMP_NETO']
        
        if p_iva == 21:
            df.at[index, 'Neto Gravado 21%'] = imp_iva / 0.21 if imp_iva != 0 else 0
            df.at[index, 'I.V.A 21%'] = imp_iva
        elif p_iva == 10.5:
            df.at[index, 'Neto Gravado 10,5%'] = imp_iva / 0.105 if imp_iva != 0 else 0
            df.at[index, 'I.V.A 10,5%'] = imp_iva
        elif p_iva == 27:
            df.at[index, 'Neto Gravado 27%'] = imp_neto
            df.at[index, 'I.V.A 27%'] = imp_iva
        elif p_iva in [3, 1.5]:
            df.at[index, 'Retenc. / Percepc.'] = imp_iva

    # Conceptos no gravados
    df['Conceptos no Gravados'] = df['IMP_EXENTO'].fillna(0)

    # 4. Agrupar por comprobante para consolidar
    # Agrupamos por los datos que identifican unívocamente la factura
    group_cols = ['Fecha', 'Tipo', 'Comprobante', 'Razón Social', 'Cuit', 'Condic.']
    agg_map = {
        'Neto Gravado 21%': 'sum',
        'Neto Gravado 10,5%': 'sum',
        'Neto Gravado 27%': 'sum',
        'Conceptos no Gravados': 'sum',
        'I.V.A 21%': 'sum',
        'I.V.A 10,5%': 'sum',
        'I.V.A 27%': 'sum',
        'Compras sin IVA': 'sum',
        'Percepción IB San Juan': 'sum',
        'Retenc. / Percepc.': 'sum'
    }

    df_transformed = df.groupby(group_cols, as_index=False).agg(agg_map)

    # 5. CÁLCULO DEL TOTAL (Suma de columnas G a P)
    # Las columnas G a P son las del índice 6 al 15 en columns_target
    cols_to_sum = columns_target[6:16]
    df_transformed['Total'] = df_transformed[cols_to_sum].sum(axis=1)

    # Ordenar columnas final
    df_final = df_transformed[columns_target]

    # 6. ELIMINAR DUPLICADOS (AL FINAL)
    # Identificamos duplicados en la tabla final (mismo Cuit, Comprobante y Total)
    # keep=False nos permite ver todas las filas involucradas para el reporte
    all_dups = df_final[df_final.duplicated(subset=['Cuit', 'Comprobante', 'Total'], keep=False)]
    
    # keep='first' identifica solo las filas que vamos a ELIMINAR
    to_remove = df_final[df_final.duplicated(subset=['Cuit', 'Comprobante', 'Total'], keep='first')]

    if not to_remove.empty:
        print("\n--- REPORTE DE FACTURAS DUPLICADAS ELIMINADAS (PASO FINAL) ---")
        report_cols = ['Fecha', 'Comprobante', 'Razón Social', 'Cuit', 'Total']
        print(to_remove[report_cols].to_string(index=False))
        print(f"\nTotal de filas duplicadas eliminadas: {len(to_remove)}")
        
        # Guardar reporte de qué se eliminó
        report_path = OUTPUT_FILE.replace(".xlsx", "_reporte_duplicados.csv")
        to_remove.to_csv(report_path, index=False)
        print(f"Listado de eliminación guardado en: {report_path}")
    else:
        print("\nNo se encontraron facturas duplicadas al final de la consolidación.")

    # Ejecutar la eliminación real
    df_final = df_final.drop_duplicates(subset=['Cuit', 'Comprobante', 'Total'], keep='first')

    # 7. Guardar resultado
    try:
        os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
        df_final.to_excel(OUTPUT_FILE, index=False)
        print(f"\nArchivo transformado guardado en: {OUTPUT_FILE}")
    except Exception as e:
        print(f"Error al guardar el archivo: {e}")

    # Mostrar preview
    print("\n--- RESULTADO FINAL (Primeras 5 filas) ---")
    print(df_final.head().to_string())

if __name__ == "__main__":
    transform_excel()
