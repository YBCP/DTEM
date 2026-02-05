"""
Script para eliminar columnas duplicadas manteniendo las originales
"""
from sheets_utils import get_sheets_manager
import pandas as pd

def limpiar_columnas_duplicadas():
    try:
        manager = get_sheets_manager()
        df = manager.leer_hoja('Registros')

        print(f"Columnas originales: {len(df.columns)}")

        # Lista de columnas a eliminar (las que están duplicadas al final)
        # Basado en la verificación, estas son las columnas duplicadas:
        columnas_a_eliminar = [
            'Nivel Información ',  # pos 48 - duplicado de pos 3
            'Frecuencia actualizacion ',  # pos 49 - duplicado de pos 4
            'Gestion acceso a los datos y documentos requeridos ',  # pos 50 - duplicado de pos 10
            'Registro',  # pos 51 - debe quedarse "Registro (completo)" pos 19
            'ET',  # pos 52 - debe quedarse "ET (completo)" pos 20
            'CO',  # pos 53 - debe quedarse "CO (completo)" pos 21
            'DD',  # pos 54 - debe quedarse "DD (completo)" pos 22
            'REC',  # pos 55 - debe quedarse "REC (completo)" pos 23
            'SERVICIO',  # pos 56 - debe quedarse "SERVICIO (completo)" pos 24
            'Aprobación resultados obtenidos en la rientación'  # pos 57 - error tipográfico
        ]

        print("\nColumnas que se eliminarán:")
        for col in columnas_a_eliminar:
            if col in df.columns:
                pos = list(df.columns).index(col)
                print(f"  - [{col}] (posición {pos})")

        # Crear DataFrame sin las columnas duplicadas
        df_limpio = df.drop(columns=[col for col in columnas_a_eliminar if col in df.columns])

        print(f"\nColumnas después de limpiar: {len(df_limpio.columns)}")
        print(f"Columnas eliminadas: {len(df.columns) - len(df_limpio.columns)}")

        # Verificar que las columnas correctas siguen presentes
        print("\nVerificando columnas importantes:")
        columnas_importantes = [
            'Nivel Información',  # Sin espacio (la correcta según pos 3)
            'Frecuencia actualizacion',  # Sin espacio (la correcta según pos 4)
            'Gestion acceso a los datos y documentos requeridos',  # Sin espacio (pos 10)
            'Registro (completo)',
            'ET (completo)',
            'CO (completo)',
            'DD (completo)',
            'REC (completo)',
            'SERVICIO (completo)',
            'Plazo de análisis',
            'Plazo de cronograma',
            'Plazo de oficio de cierre'
        ]

        for col in columnas_importantes:
            if col in df_limpio.columns:
                print(f"  OK: [{col}]")
            else:
                print(f"  FALTA: [{col}]")

        # Guardar a Google Sheets
        print("\nGuardando en Google Sheets...")
        manager.escribir_hoja(df_limpio, "Registros", limpiar_hoja=True)

        print("\nLimpieza completada exitosamente")
        return True

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("="*60)
    print("LIMPIEZA DE COLUMNAS DUPLICADAS")
    print("="*60)

    if limpiar_columnas_duplicadas():
        print("\nExito")
    else:
        print("\nError en la limpieza")
