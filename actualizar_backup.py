"""
Script para actualizar el backup con la estructura correcta
"""
from sheets_utils import get_sheets_manager

def actualizar_backup():
    try:
        manager = get_sheets_manager()

        # Leer datos actuales (ya limpios)
        df_registros = manager.leer_hoja('Registros')

        print(f"Registros actuales: {len(df_registros)} filas, {len(df_registros.columns)} columnas")

        # Actualizar backup
        print("\nActualizando Respaldo_Registros...")
        manager.escribir_hoja(df_registros, "Respaldo_Registros", limpiar_hoja=True)

        print("\nBackup actualizado exitosamente")
        return True

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("="*60)
    print("ACTUALIZAR BACKUP")
    print("="*60)

    if actualizar_backup():
        print("\nExito")
    else:
        print("\nError")
