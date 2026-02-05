"""
Script para restaurar datos desde Respaldo_Registros
"""
import streamlit as st
from sheets_utils import get_sheets_manager

def restaurar_datos():
    """Restaura datos desde Respaldo_Registros"""
    try:
        sheets_manager = get_sheets_manager()

        print("Leyendo respaldo...")
        df_respaldo = sheets_manager.leer_hoja("Respaldo_Registros")

        if df_respaldo.empty:
            print("El respaldo esta vacio")
            return False

        print(f"Respaldo leido: {len(df_respaldo)} registros")

        # Guardar en la hoja principal
        print("Restaurando en hoja Registros...")
        sheets_manager.escribir_hoja(df_respaldo, "Registros", limpiar_hoja=True)

        print("Datos restaurados exitosamente")
        print(f"   {len(df_respaldo)} registros recuperados")
        return True

    except Exception as e:
        print(f"Error restaurando datos: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("="*60)
    print("RESTAURACION DE DATOS DESDE BACKUP")
    print("="*60)
    print("\nIniciando restauracion...")
    if restaurar_datos():
        print("\nRestauracion completada exitosamente")
    else:
        print("\nLa restauracion fallo")
