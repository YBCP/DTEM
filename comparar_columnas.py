"""
Script para comparar columnas entre backup y actual
"""
from sheets_utils import get_sheets_manager

def comparar_columnas():
    try:
        manager = get_sheets_manager()

        df_backup = manager.leer_hoja('Respaldo_Registros')
        df_actual = manager.leer_hoja('Registros')

        print("COLUMNAS EN BACKUP vs ACTUAL")
        print("="*80)

        cols_backup = list(df_backup.columns)
        cols_actual = list(df_actual.columns)

        print(f"\nBackup: {len(cols_backup)} columnas")
        print(f"Actual: {len(cols_actual)} columnas")

        # Mostrar las últimas 15 columnas de cada uno
        print("\n" + "="*80)
        print("ULTIMAS 15 COLUMNAS EN BACKUP:")
        for i, col in enumerate(cols_backup[-15:]):
            idx = len(cols_backup) - 15 + i
            print(f"{idx}: [{col}]")

        print("\n" + "="*80)
        print("ULTIMAS 15 COLUMNAS EN ACTUAL:")
        for i, col in enumerate(cols_actual[-15:]):
            idx = len(cols_actual) - 15 + i
            print(f"{idx}: [{col}]")

        # Verificar si hay columnas en actual que no estén en backup
        print("\n" + "="*80)
        print("COLUMNAS EN ACTUAL QUE NO ESTAN EN BACKUP:")
        nuevas = [col for col in cols_actual if col not in cols_backup]
        if nuevas:
            for col in nuevas:
                print(f"  - [{col}]")
        else:
            print("  Ninguna")

        # Verificar si hay columnas en backup que no estén en actual
        print("\nCOLUMNAS EN BACKUP QUE NO ESTAN EN ACTUAL:")
        eliminadas = [col for col in cols_backup if col not in cols_actual]
        if eliminadas:
            for col in eliminadas:
                print(f"  - [{col}]")
        else:
            print("  Ninguna")

        return True

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    comparar_columnas()
