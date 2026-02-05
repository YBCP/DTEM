"""
Script para eliminar columnas desde la posición 48 en adelante
"""
from sheets_utils import get_sheets_manager

def eliminar_columnas_desde_48():
    try:
        manager = get_sheets_manager()
        df = manager.leer_hoja('Registros')

        print(f"Columnas originales: {len(df.columns)}")

        # Obtener lista de columnas
        todas_columnas = list(df.columns)

        # Columnas a mantener (0-47)
        columnas_mantener = todas_columnas[:48]

        # Columnas a eliminar (48 en adelante)
        columnas_eliminar = todas_columnas[48:]

        print(f"\nColumnas a mantener: {len(columnas_mantener)} (indices 0-47)")
        print(f"Columnas a eliminar: {len(columnas_eliminar)} (indices 48+)")

        print("\nColumnas que se eliminaran:")
        for i, col in enumerate(columnas_eliminar):
            idx = 48 + i
            print(f"  {idx}: [{col}]")

        # Crear DataFrame solo con las columnas a mantener
        df_limpio = df[columnas_mantener]

        print(f"\nColumnas despues de limpiar: {len(df_limpio.columns)}")

        # Mostrar las últimas columnas que quedan
        print("\nUltimas 5 columnas que quedaran:")
        for i, col in enumerate(list(df_limpio.columns)[-5:]):
            idx = len(df_limpio.columns) - 5 + i
            print(f"  {idx}: [{col}]")

        # Guardar a Google Sheets
        print("\nGuardando en Google Sheets...")
        manager.escribir_hoja(df_limpio, "Registros", limpiar_hoja=True)

        print("\nColumnas eliminadas exitosamente")
        print(f"Total de columnas ahora: {len(df_limpio.columns)}")
        return True

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("="*60)
    print("ELIMINAR COLUMNAS DESDE POSICION 48")
    print("="*60)

    if eliminar_columnas_desde_48():
        print("\nExito")
    else:
        print("\nError")
