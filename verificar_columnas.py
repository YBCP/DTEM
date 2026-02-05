"""
Script para verificar columnas duplicadas
"""
from sheets_utils import get_sheets_manager
import pandas as pd

def verificar_columnas():
    try:
        manager = get_sheets_manager()
        df = manager.leer_hoja('Registros')

        print(f"Total de columnas: {len(df.columns)}")
        print("\n" + "="*60)

        # Listar todas las columnas con su índice
        print("\nTODAS LAS COLUMNAS:")
        for i, col in enumerate(df.columns):
            print(f"{i}: [{col}]")

        # Buscar duplicados exactos
        print("\n" + "="*60)
        print("\nCOLUMNAS DUPLICADAS (exactas):")
        columnas_vistas = {}
        for i, col in enumerate(df.columns):
            if col in columnas_vistas:
                print(f"DUPLICADO: [{col}] aparece en posiciones {columnas_vistas[col]} y {i}")
            else:
                columnas_vistas[col] = i

        # Buscar columnas con nombres similares (con/sin espacios)
        print("\n" + "="*60)
        print("\nCOLUMNAS SIMILARES (con variaciones de espacios):")
        columnas_normalizadas = {}
        for i, col in enumerate(df.columns):
            col_normalizada = col.strip()
            if col_normalizada in columnas_normalizadas:
                idx_original = columnas_normalizadas[col_normalizada]
                col_original = df.columns[idx_original]
                print(f"SIMILAR: [{col_original}] (pos {idx_original}) vs [{col}] (pos {i})")
            else:
                columnas_normalizadas[col_normalizada] = i

        return True

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    verificar_columnas()
