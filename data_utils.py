# data_utils.py - ERROR "truth value of Series is ambiguous" COMPLETAMENTE ELIMINADO

import pandas as pd
import numpy as np
import io
import re
import os
import streamlit as st
from datetime import datetime, timedelta, date  
from constants import REGISTROS_DATA, META_DATA
from sheets_utils import get_sheets_manager

def normalizar_csv(contenido, separador=';'):
    """Normaliza el contenido de un CSV para asegurar mismo número de columnas."""
    lineas = contenido.split('\n')
    if not lineas:
        return contenido

    # Determinar el número de columnas a partir de la primera línea
    columnas = lineas[0].count(separador) + 1

    lineas_normalizadas = []
    for linea in lineas:
        if not linea.strip():  # Ignorar líneas vacías
            continue

        campos = linea.split(separador)
        if len(campos) < columnas:
            # Añadir campos vacíos faltantes
            linea = linea + separador * (columnas - len(campos))
        elif len(campos) > columnas:
            # Truncar campos excedentes
            linea = separador.join(campos[:columnas])

        lineas_normalizadas.append(linea)

    return '\n'.join(lineas_normalizadas)

def limpiar_valor(valor):
    """Limpia un valor de entrada de posibles errores."""
    if pd.isna(valor) or valor is None:
        return ''

    # Convertir a string
    valor = str(valor)

    # Eliminar caracteres problemáticos
    valor = re.sub(r'[\000-\010]|[\013-\014]|[\016-\037]', '', valor)

    return valor.strip()

def cargar_datos():
    """
    COMPLETAMENTE CORREGIDO: Carga los datos sin usar operadores booleanos con Series
    """
    try:
        sheets_manager = get_sheets_manager()
        
        # Cargar registros
        registros_df = sheets_manager.leer_hoja("Registros")
        
        # CORRECCIÓN: Verificar sin ambigüedad
        if registros_df is None:
            st.error("No se pudo obtener datos de registros")
            registros_df = crear_estructura_registros_basica()
        elif len(registros_df) == 0:
            st.warning("Tabla de registros vacía - creando estructura básica")
            registros_df = crear_estructura_registros_basica()
        else:
            st.success(f"{len(registros_df)} registros cargados")
        
        # Cargar metas
        try:
            meta_df = sheets_manager.leer_hoja("Metas")
            if meta_df is None or len(meta_df) == 0:
                meta_df = crear_estructura_metas_basica()
        except:
            meta_df = crear_estructura_metas_basica()
        
        # Añadir columnas faltantes
        columnas_requeridas = [
            'Cod', 'Funcionario', 'Entidad', 'Nivel Información ', 'Frecuencia actualizacion ',
            'TipoDato', 'Mes Proyectado', 'Actas de acercamiento y manifestación de interés',
            'Suscripción acuerdo de compromiso', 'Entrega acuerdo de compromiso',
            'Acuerdo de compromiso', 'Gestion acceso a los datos y documentos requeridos ',
            'Análisis de información', 'Cronograma Concertado', 'Análisis y cronograma (fecha programada)',
            'Fecha de entrega de información', 'Plazo de análisis', 'Análisis y cronograma',
            'Seguimiento a los acuerdos', 
            'Registro (completo)', 'ET (completo)', 'CO (completo)', 'DD (completo)', 'REC (completo)', 'SERVICIO (completo)',
            'Estándares (fecha programada)', 'Estándares', 'Resultados de orientación técnica',
            'Verificación del servicio web geográfico', 'Verificar Aprobar Resultados',
            'Revisar y validar los datos cargados en la base de datos',
            'Aprobación resultados obtenidos en la rientación', 'Disponer datos temáticos',
            'Fecha de publicación programada', 'Publicación', 'Catálogo de recursos geográficos',
            'Oficios de cierre', 'Fecha de oficio de cierre', 'Plazo de cronograma',
            'Plazo de oficio de cierre', 'Estado', 'Observación'
        ]
        
        for columna in columnas_requeridas:
            if columna not in registros_df.columns:
                registros_df[columna] = ''
        
        # Limpiar valores sin usar operadores booleanos complejos
        for col in registros_df.columns:
            registros_df[col] = registros_df[col].apply(
                lambda x: '' if pd.isna(x) or x is None else str(x).strip()
            )
        
        return registros_df, meta_df
        
    except Exception as e:
        st.error(f"Error en carga básica: {str(e)}")
        return crear_estructura_emergencia()

def crear_estructura_emergencia():
    """
    Crea estructura mínima de emergencia cuando todo lo demás falla.
    """
    st.warning("Creando estructura de emergencia")
    
    # Estructura mínima de registros
    columnas_minimas = [
        'Cod', 'Entidad', 'TipoDato', 'Nivel Información ', 'Mes Proyectado',
        'Acuerdo de compromiso', 'Análisis y cronograma', 'Estándares', 'Publicación',
        'Fecha de entrega de información', 'Plazo de análisis', 'Plazo de cronograma',
        'Plazo de oficio de cierre', 'Fecha de oficio de cierre', 'Estado', 'Observación',
        'Funcionario', 'Frecuencia actualizacion '
    ]
    
    registros_df = pd.DataFrame(columns=columnas_minimas)
    
    # Estructura mínima de metas
    meta_df = pd.DataFrame({
        0: ["15/01/2025", "31/01/2025", "15/02/2025"],
        1: [0, 0, 0], 2: [0, 0, 0], 3: [0, 0, 0], 4: [0, 0, 0], 5: [0, 0, 0],
        6: [0, 0, 0], 7: [0, 0, 0], 8: [0, 0, 0], 9: [0, 0, 0]
    })
    
    return registros_df, meta_df

def crear_estructura_registros_basica():
    """Crea estructura básica de registros"""
    columnas_basicas = [
        'Cod', 'Funcionario', 'Entidad', 'Nivel Información ', 'Frecuencia actualizacion ',
        'TipoDato', 'Mes Proyectado', 'Actas de acercamiento y manifestación de interés',
        'Suscripción acuerdo de compromiso', 'Entrega acuerdo de compromiso',
        'Acuerdo de compromiso', 'Gestion acceso a los datos y documentos requeridos ',
        'Análisis de información', 'Cronograma Concertado', 'Análisis y cronograma (fecha programada)',
        'Fecha de entrega de información', 'Plazo de análisis', 'Análisis y cronograma',
        'Seguimiento a los acuerdos', 
        'Registro (completo)', 'ET (completo)', 'CO (completo)', 'DD (completo)', 'REC (completo)', 'SERVICIO (completo)',
        'Estándares (fecha programada)', 'Estándares', 'Resultados de orientación técnica',
        'Verificación del servicio web geográfico', 'Verificar Aprobar Resultados',
        'Revisar y validar los datos cargados en la base de datos',
        'Aprobación resultados obtenidos en la rientación', 'Disponer datos temáticos',
        'Fecha de publicación programada', 'Publicación', 'Catálogo de recursos geográficos',
        'Oficios de cierre', 'Fecha de oficio de cierre', 'Plazo de cronograma',
        'Plazo de oficio de cierre', 'Estado', 'Observación'
    ]
    
    return pd.DataFrame(columns=columnas_basicas)

def crear_estructura_metas_basica():
    """Crea estructura básica de metas"""
    return pd.DataFrame({
        0: ["15/01/2025", "31/01/2025", "15/02/2025"],
        1: [0, 0, 0], 2: [0, 0, 0], 3: [0, 0, 0], 4: [0, 0, 0], 5: [0, 0, 0],
        6: [0, 0, 0], 7: [0, 0, 0], 8: [0, 0, 0], 9: [0, 0, 0]
    })

def crear_estructura_metas_inicial():
    """Crea una estructura inicial para las metas"""
    return pd.DataFrame({
        0: ["15/01/2025", "31/01/2025", "15/02/2025"],
        1: [0, 0, 0],  # Acuerdo nuevos
        2: [0, 0, 0],  # Análisis nuevos
        3: [0, 0, 0],  # Estándares nuevos
        4: [0, 0, 0],  # Publicación nuevos
        5: [0, 0, 0],  # Separador
        6: [0, 0, 0],  # Acuerdo actualizar
        7: [0, 0, 0],  # Análisis actualizar
        8: [0, 0, 0],  # Estándares actualizar
        9: [0, 0, 0],  # Publicación actualizar
    })

def procesar_fecha(fecha_str):
    """
    CORRECCIÓN CRÍTICA: Procesa una fecha de manera segura manejando NaT.
    SIEMPRE devuelve datetime, NUNCA date
    """
    if pd.isna(fecha_str) or fecha_str == '' or fecha_str is None:
        return None

    # Si es un objeto datetime o Timestamp, retornarlo directamente
    if isinstance(fecha_str, (pd.Timestamp, datetime)):
        if pd.isna(fecha_str):
            return None
        # ASEGURAR que es datetime
        if isinstance(fecha_str, pd.Timestamp):
            return fecha_str.to_pydatetime()
        return fecha_str
    
    # CORRECCIÓN CRÍTICA: Si es date, convertir SIEMPRE a datetime
    if isinstance(fecha_str, date):
        return datetime.combine(fecha_str, datetime.min.time())

    # Si es un string, procesarlo
    try:
        fecha_str = re.sub(r'[^\d/\-]', '', str(fecha_str).strip())
        formatos = ['%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y', '%m/%d/%Y']

        for formato in formatos:
            try:
                fecha = pd.to_datetime(fecha_str, format=formato)
                if pd.notna(fecha):
                    # CRÍTICO: Convertir a datetime puro si es Timestamp
                    if hasattr(fecha, 'to_pydatetime'):
                        return fecha.to_pydatetime()
                    return fecha
            except:
                continue
        return None
    except Exception:
        return None

def es_fecha_valida(valor):
    """Verifica si un valor es una fecha válida."""
    try:
        fecha = procesar_fecha(valor)
        return fecha is not None and pd.notna(fecha)
    except Exception:
        return False

def formatear_fecha(fecha_str):
    """Formatea una fecha en formato DD/MM/YYYY manejando NaT."""
    try:
        fecha = procesar_fecha(fecha_str)
        if fecha is not None and pd.notna(fecha):
            return fecha.strftime('%d/%m/%Y')
        return ""
    except Exception:
        # Si hay cualquier error, devuelve cadena vacía
        return ""

def verificar_completado_por_fecha(fecha_programada, fecha_completado=None):
    """
    CORRECCIÓN CRÍTICA: Verifica si una tarea está completada basada en fechas.
    Manejo seguro de comparaciones datetime
    """
    if fecha_completado is not None and pd.notna(fecha_completado):
        return True

    fecha_actual = datetime.now()  # SIEMPRE datetime
    fecha_prog = procesar_fecha(fecha_programada)  # SIEMPRE devuelve datetime o None

    if fecha_prog is not None and pd.notna(fecha_prog):
        # Ya no necesitamos conversión porque procesar_fecha() siempre devuelve datetime
        if fecha_prog <= fecha_actual:
            return True

    return False

def calcular_porcentaje_avance(registro):
    """
    MODIFICADO: Calcula el porcentaje de avance de un registro basado en los campos de completitud.
    NUEVA REGLA: Si tiene fecha de oficio de cierre, automáticamente 100% de avance.

    Ponderación (cuando no hay fecha de cierre):
    - Acuerdo de compromiso: 20%
    - Análisis y cronograma (fecha real): 20%
    - Estándares (fecha real): 30%
    - Publicación (fecha real): 25%
    - Fecha de oficio de cierre: 5%
    """
    try:
        # NUEVA REGLA: Si tiene fecha de oficio de cierre, automáticamente 100%
        if ('Fecha de oficio de cierre' in registro and 
            registro['Fecha de oficio de cierre'] and 
            pd.notna(registro['Fecha de oficio de cierre']) and
            str(registro['Fecha de oficio de cierre']).strip() != ''):
            return 100

        # Si no hay fecha de cierre, calcular normalmente
        # Inicializar el avance
        avance = 0

        # Verificar el acuerdo de compromiso (20%)
        if 'Acuerdo de compromiso' in registro and str(registro['Acuerdo de compromiso']).strip().upper() in ['SI',
                                                                                                              'SÍ', 'S',
                                                                                                              'YES',
                                                                                                              'Y',
                                                                                                              'COMPLETO']:
            avance += 20

        # Verificar análisis y cronograma - VERIFICADO: basado en la fecha (20%)
        if ('Análisis y cronograma' in registro and 
            registro['Análisis y cronograma'] and 
            pd.notna(registro['Análisis y cronograma']) and
            str(registro['Análisis y cronograma']).strip() != ''):
            avance += 20

        # Verificar estándares - basado en la fecha (30%)
        if ('Estándares' in registro and 
            registro['Estándares'] and 
            pd.notna(registro['Estándares']) and
            str(registro['Estándares']).strip() != ''):
            avance += 30

        # Verificar publicación - VERIFICADO: basado en la fecha (25%)
        if ('Publicación' in registro and 
            registro['Publicación'] and 
            pd.notna(registro['Publicación']) and
            str(registro['Publicación']).strip() != ''):
            avance += 25

        # Nota: No sumamos los 5% del oficio de cierre aquí porque si llegáramos a este punto
        # significa que no hay fecha de cierre, por lo que el máximo sería 95%

        return avance
    except Exception as e:
        # En caso de error, retornar 0
        return 0

def procesar_metas(meta_df):
    """Procesa las metas a partir del DataFrame de metas."""
    try:
        # La estructura de las metas es compleja, vamos a procesarla
        # Asumiendo que las filas 3 en adelante contienen las fechas y metas
        fechas = []
        metas_nuevas = {}
        metas_actualizar = {}

        # Inicializar listas para cada hito
        for hito in ['Acuerdo de compromiso', 'Análisis y cronograma', 'Estándares', 'Publicación']:
            metas_nuevas[hito] = []
            metas_actualizar[hito] = []

        # Procesar cada fila (desde la fila 3 que contiene las fechas y valores)
        for i in range(len(meta_df)):
            try:
                fila = meta_df.iloc[i]

                # La primera columna contiene la fecha
                fecha = procesar_fecha(fila[0])
                if fecha is not None:
                    fechas.append(fecha)

                    # Columnas 1-4 son para registros nuevos (asegurar que existan)
                    metas_nuevas['Acuerdo de compromiso'].append(
                        pd.to_numeric(fila[1] if len(fila) > 1 else 0, errors='coerce') or 0)
                    metas_nuevas['Análisis y cronograma'].append(
                        pd.to_numeric(fila[2] if len(fila) > 2 else 0, errors='coerce') or 0)
                    metas_nuevas['Estándares'].append(
                        pd.to_numeric(fila[3] if len(fila) > 3 else 0, errors='coerce') or 0)
                    metas_nuevas['Publicación'].append(
                        pd.to_numeric(fila[4] if len(fila) > 4 else 0, errors='coerce') or 0)

                    # Columnas 6-9 son para registros a actualizar (asegurar que existan)
                    metas_actualizar['Acuerdo de compromiso'].append(
                        pd.to_numeric(fila[6] if len(fila) > 6 else 0, errors='coerce') or 0)
                    metas_actualizar['Análisis y cronograma'].append(
                        pd.to_numeric(fila[7] if len(fila) > 7 else 0, errors='coerce') or 0)
                    metas_actualizar['Estándares'].append(
                        pd.to_numeric(fila[8] if len(fila) > 8 else 0, errors='coerce') or 0)
                    metas_actualizar['Publicación'].append(
                        pd.to_numeric(fila[9] if len(fila) > 9 else 0, errors='coerce') or 0)
            except Exception as e:
                st.warning(f"Error al procesar fila {i} de metas: {e}")
                continue

        # Si no hay fechas, mostrar un error
        if not fechas:
            st.warning("No se pudieron procesar las fechas de las metas, usando datos por defecto")
            # Crear un DataFrame de ejemplo como respaldo
            fechas = [datetime.now()]
            for hito in metas_nuevas:
                metas_nuevas[hito] = [0]
                metas_actualizar[hito] = [0]

        # Convertir a DataFrames
        metas_nuevas_df = pd.DataFrame(metas_nuevas, index=fechas)
        metas_actualizar_df = pd.DataFrame(metas_actualizar, index=fechas)

        return metas_nuevas_df, metas_actualizar_df
    except Exception as e:
        st.error(f"Error al procesar metas: {e}")
        # Crear DataFrames vacíos como respaldo
        fechas = [datetime.now()]
        metas_nuevas = {'Acuerdo de compromiso': [0], 'Análisis y cronograma': [0], 'Estándares': [0],
                        'Publicación': [0]}
        metas_actualizar = {'Acuerdo de compromiso': [0], 'Análisis y cronograma': [0], 'Estándares': [0],
                            'Publicación': [0]}

        metas_nuevas_df = pd.DataFrame(metas_nuevas, index=fechas)
        metas_actualizar_df = pd.DataFrame(metas_actualizar, index=fechas)

        return metas_nuevas_df, metas_actualizar_df

def verificar_estado_fechas(row):
    """
    CORRECCIÓN CRÍTICA: Verifica si las fechas están vencidas o próximas a vencer.
    Comparaciones datetime seguras
    """
    fecha_actual = datetime.now()  # SIEMPRE datetime
    estado = "normal"

    campos_fecha = [
        'Análisis y cronograma (fecha programada)',
        'Estándares (fecha programada)',
        'Fecha de publicación programada'
    ]

    for campo in campos_fecha:
        if campo in row and pd.notna(row[campo]) and str(row[campo]).strip() != '':
            fecha = procesar_fecha(row[campo])  # SIEMPRE devuelve datetime o None
            if fecha is not None and pd.notna(fecha):
                # Ya no necesitamos conversión manual
                if fecha < fecha_actual:
                    return "vencido"
                if fecha <= fecha_actual + timedelta(days=30):
                    estado = "proximo"

    return estado

def validar_campos_fecha(df, campos_fecha=['Análisis y cronograma', 'Estándares', 'Publicación']):
    """
    Valida que los campos específicos contengan solo fechas válidas.
    Si no son fechas válidas, los convierte a fechas o los deja vacíos.
    """
    df_validado = df.copy()

    for campo in campos_fecha:
        if campo in df_validado.columns:
            df_validado[campo] = df_validado[campo].apply(
                lambda x: formatear_fecha(x) if es_fecha_valida(x) else ""
            )

    return df_validado
