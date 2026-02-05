"""
Script para recalcular SOLO las columnas de plazos sin afectar otros datos
"""
from sheets_utils import get_sheets_manager
from fecha_utils import actualizar_plazo_analisis, actualizar_plazo_cronograma, actualizar_plazo_oficio_cierre
import pandas as pd

def recalcular_plazos_seguro():
    """Recalcula SOLO los plazos sin tocar otras columnas"""
    try:
        sheets_manager = get_sheets_manager()

        print("Leyendo datos actuales...")
        df = sheets_manager.leer_hoja("Registros")

        if df.empty:
            print("No hay datos para procesar")
            return False

        print(f"Registros cargados: {len(df)}")

        # Guardar una copia de las columnas originales
        df_original = df.copy()

        # Aplicar cálculos de plazos
        print("\nCalculando Plazo de analisis...")
        df_calculado = actualizar_plazo_analisis(df)

        print("Calculando Plazo de cronograma...")
        df_calculado = actualizar_plazo_cronograma(df_calculado)

        print("Calculando Plazo de oficio de cierre...")
        df_calculado = actualizar_plazo_oficio_cierre(df_calculado)

        # CRÍTICO: Restaurar TODAS las columnas originales EXCEPTO las tres de plazos
        columnas_plazo = ['Plazo de análisis', 'Plazo de cronograma', 'Plazo de oficio de cierre']

        print("\nPreservando columnas originales...")
        for col in df_original.columns:
            if col not in columnas_plazo:
                # Restaurar la columna original
                df_calculado[col] = df_original[col]

        # Verificar que solo cambiaron las columnas de plazo
        print("\nVerificando cambios...")
        cambios_detectados = []
        for col in df_original.columns:
            if col not in columnas_plazo:
                if not df_original[col].equals(df_calculado[col]):
                    cambios_detectados.append(col)

        if cambios_detectados:
            print(f"ADVERTENCIA: Se detectaron cambios en columnas no esperadas: {cambios_detectados}")
            return False

        # Contar cuántos plazos se calcularon
        plazos_calculados = {
            'Plazo de análisis': 0,
            'Plazo de cronograma': 0,
            'Plazo de oficio de cierre': 0
        }

        for col in columnas_plazo:
            if col in df_calculado.columns:
                valores_no_vacios = df_calculado[col].apply(lambda x: pd.notna(x) and str(x).strip() != '')
                plazos_calculados[col] = valores_no_vacios.sum()

        print("\nPlazos calculados:")
        for col, count in plazos_calculados.items():
            print(f"  {col}: {count} registros")

        # Guardar a Google Sheets
        print("\nGuardando en Google Sheets...")
        sheets_manager.escribir_hoja(df_calculado, "Registros", limpiar_hoja=True)

        print("\nPlazos recalculados exitosamente")
        return True

    except Exception as e:
        print(f"Error recalculando plazos: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("="*60)
    print("RECALCULO SEGURO DE PLAZOS")
    print("="*60)
    print("\nEsto SOLO actualizara las columnas de plazos")
    print("Todas las demas columnas se preservaran")
    print("\nIniciando...")

    if recalcular_plazos_seguro():
        print("\nRecalculo completado exitosamente")
    else:
        print("\nEl recalculo fallo")
