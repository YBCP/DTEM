"""
Script para crear la hoja SeguimientoPDD con estructura jerárquica correcta
Etapa → Subetapa (opcional) → Actividades
"""
import pandas as pd
import random
from datetime import datetime
from sheets_utils import get_sheets_manager

def crear_hoja_seguimiento_pdd():
    """Crea la hoja SeguimientoPDD con datos de ejemplo"""

    manager = get_sheets_manager()

    # Leer registros con Pddatos=1
    registros_df = manager.leer_hoja('Registros')
    registros_pdd = registros_df[registros_df['Pddatos'].astype(str).str.strip() == '1']

    # Leer actividades con estructura jerárquica
    actividades_df = manager.leer_hoja('ActividadesPDD')
    actividades_df['Subetapa'] = actividades_df['Subetapa'].fillna('').astype(str).str.strip()

    print(f"Registros con Pddatos=1: {len(registros_pdd)}")
    print(f"Actividades totales: {len(actividades_df)}")

    # Tomar los primeros 10 registros para ejemplo
    registros_ejemplo = registros_pdd.head(10)

    # Crear datos de ejemplo para SeguimientoPDD
    datos_seguimiento = []
    estados_posibles = ['No aplica', 'Sin iniciar', 'Iniciada', 'Completa']

    # Asignar etapas aleatorias a cada registro (principalmente 2 y 3)
    etapas_principales = [
        'Etapa 2. Aperturar (abrir) el dato.',
        'Etapa 3.Gestionar (procesamiento) dato geográfico.'
    ]

    for idx, registro in registros_ejemplo.iterrows():
        cod = registro['Cod']
        entidad = registro['Entidad']

        # Asignar etapa aleatoria
        etapa_asignada = random.choice(etapas_principales)

        # Filtrar actividades de esa etapa
        actividades_etapa = actividades_df[actividades_df['Etapa'] == etapa_asignada]

        # Para cada actividad de la etapa, crear un registro de seguimiento
        for _, act_row in actividades_etapa.iterrows():
            actividad = act_row['Actividad']
            subetapa = act_row['Subetapa'] if act_row['Subetapa'] != '' else ''

            # Generar estado aleatorio con más peso hacia "Completa" y "Iniciada"
            # Para visualización variada
            estado = random.choices(
                estados_posibles,
                weights=[10, 15, 30, 45],  # Más completas para ver progreso
                k=1
            )[0]

            datos_seguimiento.append({
                'Cod_Registro': cod,
                'Entidad': entidad,
                'Etapa': etapa_asignada,
                'Subetapa': subetapa,
                'Actividad': actividad,
                'Estado': estado,
                'Fecha_Actualizacion': datetime.now().strftime('%d/%m/%Y'),
                'Observaciones': ''
            })

    # Crear DataFrame
    df_seguimiento = pd.DataFrame(datos_seguimiento)

    print(f"\nRegistros de seguimiento creados: {len(df_seguimiento)}")
    print(f"\nPrimeros 5 registros:")
    print(df_seguimiento.head())

    # Mostrar estadísticas
    print(f"\nEstadísticas:")
    print(f"  - Registros únicos: {df_seguimiento['Cod_Registro'].nunique()}")
    print(f"  - Etapas activas: {df_seguimiento['Etapa'].nunique()}")
    print(f"  - Subetapas únicas: {df_seguimiento[df_seguimiento['Subetapa'] != '']['Subetapa'].nunique()}")

    # Verificar si la hoja ya existe
    hojas_existentes = manager.listar_hojas()

    if 'SeguimientoPDD' in hojas_existentes:
        print("\nLa hoja SeguimientoPDD ya existe. Se sobrescribirá...")

    # Escribir a Google Sheets
    print("\nEscribiendo hoja SeguimientoPDD...")
    manager.escribir_hoja(df_seguimiento, 'SeguimientoPDD', limpiar_hoja=True)

    print("Hoja SeguimientoPDD creada exitosamente!")
    print(f"\nResumen:")
    print(f"  - Registros ejemplo: {len(registros_ejemplo)}")
    print(f"  - Total entradas seguimiento: {len(df_seguimiento)}")

    # Mostrar distribución de estados
    print(f"\nDistribución de estados:")
    print(df_seguimiento['Estado'].value_counts())

    print(f"\nDistribución por etapa:")
    print(df_seguimiento.groupby('Etapa')['Cod_Registro'].nunique())

if __name__ == "__main__":
    crear_hoja_seguimiento_pdd()
