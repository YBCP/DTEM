# data_utils.py - FUNCIONES DE DATOS ESENCIALES
"""
Utilidades de datos para el sistema Ideca
- Funciones esenciales sin iconos ni texto innecesario
- Diseño limpio y funcional
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta, date
import re
import streamlit as st


# ===== FUNCIONES DE FECHAS =====

def procesar_fecha(fecha_str):
    """Procesa una fecha de manera segura"""
    if pd.isna(fecha_str) or fecha_str == '' or fecha_str is None:
        return None

    if isinstance(fecha_str, datetime):
        if pd.isna(fecha_str):
            return None
        return fecha_str

    if isinstance(fecha_str, date):
        return datetime.combine(fecha_str, datetime.min.time())

    if isinstance(fecha_str, pd.Timestamp):
        if pd.isna(fecha_str):
            return None
        return fecha_str.to_pydatetime()

    try:
        fecha_str = re.sub(r'[^\d/\-]', '', str(fecha_str).strip())
        formatos = ['%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y', '%m/%d/%Y']

        for formato in formatos:
            try:
                fecha = pd.to_datetime(fecha_str, format=formato)
                if pd.notna(fecha):
                    resultado = fecha.to_pydatetime() if hasattr(fecha, 'to_pydatetime') else fecha
                    if isinstance(resultado, date) and not isinstance(resultado, datetime):
                        return datetime.combine(resultado, datetime.min.time())
                    return resultado
            except:
                continue
        return None
    except Exception:
        return None


def formatear_fecha(fecha_str):
    """Formatea una fecha en formato DD/MM/YYYY"""
    try:
        fecha = procesar_fecha(fecha_str)
        if fecha is not None and pd.notna(fecha):
            return fecha.strftime('%d/%m/%Y')
        return ""
    except Exception:
        return ""


def es_fecha_valida(fecha):
    """Verifica si una fecha es válida"""
    if pd.isna(fecha) or fecha == '' or fecha is None:
        return False
    
    try:
        fecha_procesada = procesar_fecha(fecha)
        return fecha_procesada is not None
    except:
        return False


def es_festivo(fecha):
    """Verifica si una fecha es festivo en Colombia"""
    FESTIVOS_2025 = [
        datetime(2025, 1, 1), datetime(2025, 1, 6), datetime(2025, 3, 24),
        datetime(2025, 4, 17), datetime(2025, 4, 18), datetime(2025, 5, 1),
        datetime(2025, 5, 29), datetime(2025, 6, 19), datetime(2025, 6, 27),
        datetime(2025, 6, 30), datetime(2025, 7, 20), datetime(2025, 8, 7),
        datetime(2025, 8, 18), datetime(2025, 10, 13), datetime(2025, 11, 3),
        datetime(2025, 11, 17), datetime(2025, 12, 8), datetime(2025, 12, 25)
    ]
    
    try:
        if isinstance(fecha, datetime):
            fecha_dt = fecha
        elif isinstance(fecha, date):
            fecha_dt = datetime.combine(fecha, datetime.min.time())
        else:
            return False
        
        for festivo in FESTIVOS_2025:
            if (fecha_dt.day == festivo.day and
                fecha_dt.month == festivo.month and
                fecha_dt.year == festivo.year):
                return True
        return False
    except Exception:
        return False


# ===== FUNCIONES DE CÁLCULO =====

def calcular_porcentaje_avance(row):
    """Calcula el porcentaje de avance basado en los hitos principales"""
    try:
        avance = 0
        
        # Hito 1: Acuerdo de compromiso (25%)
        acuerdo = str(row.get('Acuerdo de compromiso', '')).strip().upper()
        if acuerdo in ['SI', 'SÍ', 'S', 'YES', 'Y', 'COMPLETO']:
            avance += 25
        
        # Hito 2: Análisis y cronograma (25%)
        analisis = row.get('Análisis y cronograma', '')
        if es_fecha_valida(analisis):
            avance += 25
        
        # Hito 3: Estándares (25%)
        estandares = row.get('Estándares', '')
        if es_fecha_valida(estandares):
            avance += 25
        
        # Hito 4: Publicación (25%)
        publicacion = row.get('Publicación', '')
        if es_fecha_valida(publicacion):
            avance += 25
        
        return min(avance, 100)
    except Exception:
        return 0


def verificar_estado_fechas(row):
    """Verifica el estado de las fechas (vencido, próximo, etc.)"""
    try:
        hoy = datetime.now().date()
        
        campos_fecha_programada = [
            'Análisis y cronograma (fecha programada)',
            'Estándares (fecha programada)', 
            'Fecha de publicación programada'
        ]
        
        for campo in campos_fecha_programada:
            if campo in row and row[campo]:
                fecha = procesar_fecha(row[campo])
                if fecha:
                    fecha_date = fecha.date() if isinstance(fecha, datetime) else fecha
                    dias_diferencia = (fecha_date - hoy).days
                    
                    if dias_diferencia < 0:
                        return 'vencido'
                    elif dias_diferencia <= 7:
                        return 'proximo'
        
        return 'normal'
    except Exception:
        return 'normal'


def verificar_completado_por_fecha(fecha_programada, fecha_completado):
    """Verifica si algo está completado por fecha"""
    try:
        if fecha_completado:
            fecha_comp = procesar_fecha(fecha_completado)
            if fecha_comp:
                return True
        
        if fecha_programada:
            fecha_prog = procesar_fecha(fecha_programada)
            if fecha_prog:
                hoy = datetime.now()
                return fecha_prog <= hoy
        
        return False
    except Exception:
        return False


# ===== FUNCIONES DE CARGA DE DATOS =====

def cargar_datos():
    """Carga datos desde Google Sheets"""
    try:
        from backup_utils import cargar_datos_con_respaldo
        return cargar_datos_con_respaldo()
    except ImportError:
        return cargar_datos_basico()


def cargar_datos_basico():
    """Carga de datos básica"""
    try:
        from sheets_utils import get_sheets_manager
        
        sheets_manager = get_sheets_manager()
        
        # Cargar registros
        registros_df = sheets_manager.leer_hoja("Registros")
        
        if registros_df.empty:
            st.warning("No hay datos en la hoja Registros")
            registros_df = crear_estructura_registros_vacia()
        
        # Cargar metas
        try:
            meta_df = sheets_manager.leer_hoja("Metas")
            if meta_df.empty:
                meta_df = crear_estructura_metas_inicial()
        except Exception:
            meta_df = crear_estructura_metas_inicial()
        
        # Limpiar datos
        registros_df = limpiar_dataframe(registros_df)
        meta_df = limpiar_dataframe(meta_df)
        
        return registros_df, meta_df
        
    except
