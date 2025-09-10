# data_utils.py - CORREGIDO: Error "The truth value of a Series is ambiguous"

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
            # Recortar campos excedentes
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
    VERSIÓN ULTRA SEGURA: Carga los datos con verificación adicional de Metas.
    CORREGIDO: Elimina evaluaciones ambiguas de Series
    """
    try:
        # Importar el sistema de respaldo ultra seguro
        from backup_utils import cargar_datos_con_respaldo
        
        # Usar el sistema ultra seguro
        registros_df, meta_df = cargar_datos_con_respaldo()
        
        # Verificación adicional: Que Metas no se haya corrompido
        if meta_df.empty:
            try:
                sheets_manager = get_sheets_manager()
                meta_df = sheets_manager.leer_hoja("Metas")
                if meta_df.empty:
                    # Crear estructura básica de metas como último recurso
                    meta_df = crear_estructura_metas_inicial()
                    sheets_manager.escribir_hoja(meta_df, "Metas", limpiar_hoja=True)
            except Exception as meta_error:
                meta_df = crear_estructura_metas_inicial()
        
        return registros_df, meta_df
        
    except ImportError:
        # Fallback si no está disponible el sistema de respaldo
        return cargar_datos_basico()
    
    except Exception as e:
        st.error(f"Error crítico en carga de datos: {str(e)}")
        
        # Último recurso: intentar cargar datos básicos
        try:
            return cargar_datos_basico()
        except:
            # Si todo falla, crear estructura mínima
            return crear_estructura_emergencia()

def cargar_datos_basico():
    """
    Función de respaldo básica para cargar datos cuando el sistema ultra seguro no está disponible.
    """
    try:
        sheets_manager = get_sheets_manager()
        
        # Cargar registros
        registros_df = sheets_manager.leer_hoja("Registros")
        
        if registros_df.empty:
            registros_df = crear_estructura_registros_basica()
        
        # Cargar metas
        try:
            meta_df = sheets_manager.leer_hoja("Metas")
            if meta_df.empty:
                meta_df = crear_estructura_metas_basica()
        except:
            meta_df = crear_estructura_metas_basica()
        
        return registros_df, meta_df
        
    except Exception as e:
        return crear_estructura_emergencia()

def crear_estructura_emergencia():
    """
    Crea estructura mínima de emergencia cuando todo lo demás falla.
    """
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
    CORREGIDO: Procesa una fecha de manera segura manejando NaT.
    CORRECCIÓN CRÍTICA: SIEMPRE devuelve datetime, NUNCA date
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
    """
    CORREGIDO: Verifica si un valor es una fecha válida.
    ELIMINA evaluación ambigua de Series
    """
    # CORRECCIÓN CRÍTICA: Si es una Series, no evaluar como booleano
    if isinstance(valor, pd.Series):
        return False
    
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
    CORREGIDO: Verifica si una tarea está completada basada en fechas.
    CORRECCIÓN CRÍTICA: Manejo seguro de comparaciones datetime
    """
    # CORRECCIÓN: Si fecha_completado es Series, devolver False
    if isinstance(fecha_completado, pd.Series):
        return False
    
    # CORRECCIÓN: Verificar si fecha_completado es válida
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
    CORREGIDO: Calcula el porcentaje de avance de un registro basado en los campos de completitud.
    ELIMINA evaluaciones ambiguas de Series
    """
    try:
        # CORRECCIÓN: Verificar que registro no sea None o vacío
        if registro is None:
            return 0
        
        # CORRECCIÓN: Si es una Series vacía, devolver 0
        if isinstance(registro, pd.Series) and registro.empty:
            return 0

        # NUEVA REGLA: Si tiene fecha de oficio de cierre, automáticamente 100%
        fecha_oficio = registro.get('Fecha de oficio de cierre', '')
        
        # CORRECCIÓN CRÍTICA: Manejar Series
        if isinstance(fecha_oficio, pd.Series):
            fecha_oficio = ''
        
        if fecha_oficio and pd.notna(fecha_oficio) and str(fecha_oficio).strip() != '':
            return 100

        # Si no hay fecha de cierre, calcular normalmente
        avance = 0

        # Verificar el acuerdo de compromiso (20%)
        acuerdo_valor = registro.get('Acuerdo de compromiso', '')
        if isinstance(acuerdo_valor, pd.Series):
            acuerdo_valor = ''
        
        if acuerdo_valor and str(acuerdo_valor).strip().upper() in ['SI', 'SÍ', 'S', 'YES', 'Y', 'COMPLETO']:
            avance += 20

        # Verificar análisis y cronograma - basado en la fecha (20%)
        analisis_valor = registro.get('Análisis y cronograma', '')
        if isinstance(analisis_valor, pd.Series):
            analisis_valor = ''
        
        if analisis_valor and pd.notna(analisis_valor) and str(analisis_valor).strip() != '':
            avance += 20

        # Verificar estándares - basado en la fecha (30%)
        estandares_valor = registro.get('Estándares', '')
        if isinstance(estandares_valor, pd.Series):
            estandares_valor = ''
        
        if estandares_valor and pd.notna(estandares_valor) and str(estandares_valor).strip() != '':
            avance += 30

        # Verificar publicación - basado en la fecha (25%)
        publicacion_valor = registro.get('Publicación', '')
        if isinstance(publicacion_valor, pd.Series):
            publicacion_valor = ''
        
        if publicacion_valor and pd.notna(publicacion_valor) and str(publicacion_valor).strip() != '':
            avance += 25

        return avance
        
    except Exception as e:
        # En caso de error, retornar 0
        return 0
        

def procesar_metas(meta_df):
    """
    CORREGIDO: Procesa las metas a partir del DataFrame de metas.
    ELIMINA evaluaciones ambiguas de Series
    """
    try:
        # Verificar que meta_df no esté vacío
        if meta_df.empty:
            return crear_metas_por_defecto()

        fechas = []
        metas_nuevas = {}
        metas_actualizar = {}

        # Inicializar listas para cada hito
        for hito in ['Acuerdo de compromiso', 'Análisis y cronograma', 'Estándares', 'Publicación']:
            metas_nuevas[hito] = []
            metas_actualizar[hito] = []

        # Procesar cada fila
        for i in range(len(meta_df)):
            try:
                fila = meta_df.iloc[i]

                # La primera columna contiene la fecha
                fecha = procesar_fecha(fila[0])
                if fecha is not None:
                    fechas.append(fecha)

                    # Columnas 1-4 son para registros nuevos
                    metas_nuevas['Acuerdo de compromiso'].append(
                        pd.to_numeric(fila[1] if len(fila) > 1 else 0, errors='coerce') or 0)
                    metas_nuevas['Análisis y cronograma'].append(
                        pd.to_numeric(fila[2] if len(fila) > 2 else 0, errors='coerce') or 0)
                    metas_nuevas['Estándares'].append(
                        pd.to_numeric(fila[3] if len(fila) > 3 else 0, errors='coerce') or 0)
                    metas_nuevas['Publicación'].append(
                        pd.to_numeric(fila[4] if len(fila) > 4 else 0, errors='coerce') or 0)

                    # Columnas 6-9 son para registros a actualizar
                    metas_actualizar['Acuerdo de compromiso'].append(
                        pd.to_numeric(fila[6] if len(fila) > 6 else 0, errors='coerce') or 0)
                    metas_actualizar['Análisis y cronograma'].append(
                        pd.to_numeric(fila[7] if len(fila) > 7 else 0, errors='coerce') or 0)
                    metas_actualizar['Estándares'].append(
                        pd.to_numeric(fila[8] if len(fila) > 8 else 0, errors='coerce') or 0)
                    metas_actualizar['Publicación'].append(
                        pd.to_numeric(fila[9] if len(fila) > 9 else 0, errors='coerce') or 0)
            except Exception:
                continue

        # Si no hay fechas, crear datos por defecto
        if not fechas:
            return crear_metas_por_defecto()

        # Convertir a DataFrames
        metas_nuevas_df = pd.DataFrame(metas_nuevas, index=fechas)
        metas_actualizar_df = pd.DataFrame(metas_actualizar, index=fechas)

        return metas_nuevas_df, metas_actualizar_df
        
    except Exception:
        return crear_metas_por_defecto()

def crear_metas_por_defecto():
    """Crea metas por defecto cuando hay errores"""
    fechas = [datetime.now()]
    metas_nuevas = {'Acuerdo de compromiso': [0], 'Análisis y cronograma': [0], 'Estándares': [0], 'Publicación': [0]}
    metas_actualizar = {'Acuerdo de compromiso': [0], 'Análisis y cronograma': [0], 'Estándares': [0], 'Publicación': [0]}

    metas_nuevas_df = pd.DataFrame(metas_nuevas, index=fechas)
    metas_actualizar_df = pd.DataFrame(metas_actualizar, index=fechas)

    return metas_nuevas_df, metas_actualizar_df

def verificar_estado_fechas(row):
    """
    CORREGIDO: Verifica si las fechas están vencidas o próximas a vencer.
    ELIMINA evaluaciones ambiguas de Series
    """
    try:
        fecha_actual = datetime.now()
        estado = "normal"

        campos_fecha = [
            'Análisis y cronograma (fecha programada)',
            'Estándares (fecha programada)',
            'Fecha de publicación programada'
        ]

        for campo in campos_fecha:
            # CORRECCIÓN: Verificar que el campo existe y obtener valor de forma segura
            if campo in row:
                valor_campo = row[campo]
                
                # CORRECCIÓN CRÍTICA: Verificar que no sea Series
                if isinstance(valor_campo, pd.Series):
                    continue
                
                if pd.notna(valor_campo) and str(valor_campo).strip() != '':
                    fecha = procesar_fecha(valor_campo)
                    if fecha is not None and pd.notna(fecha):
                        if fecha < fecha_actual:
                            return "vencido"
                        if fecha <= fecha_actual + timedelta(days=30):
                            estado = "proximo"

        return estado
        
    except Exception:
        # En caso de error, devolver estado normal
        return "normal"

def validar_campos_fecha(df, campos_fecha=['Análisis y cronograma', 'Estándares', 'Publicación']):
    """
    CORREGIDO: Valida que los campos específicos contengan solo fechas válidas.
    """
    df_validado = df.copy()

    for campo in campos_fecha:
        if campo in df_validado.columns:
            df_validado[campo] = df_validado[campo].apply(
                lambda x: formatear_fecha(x) if es_fecha_valida(x) else ""
            )

    return df_validado

# Funciones adicionales simplificadas...

def obtener_estado_sistema():
    """Obtiene el estado básico del sistema"""
    try:
        sheets_manager = get_sheets_manager()
        
        estado = {
            'registros_ok': False,
            'metas_ok': False,
            'total_registros': 0
        }
        
        # Verificar Registros
        try:
            registros_df = sheets_manager.leer_hoja("Registros")
            estado['registros_ok'] = not registros_df.empty
            estado['total_registros'] = len(registros_df)
        except:
            pass
        
        # Verificar Metas
        try:
            metas_df = sheets_manager.leer_hoja("Metas")
            estado['metas_ok'] = not metas_df.empty
        except:
            pass
        
        return estado
        
    except Exception:
        return {
            'registros_ok': False,
            'metas_ok': False,
            'total_registros': 0
        }
