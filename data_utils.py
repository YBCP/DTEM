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
        
        # ✅ VERIFICACIÓN ADICIONAL: Que Metas no se haya corrompido
        if meta_df.empty:
            st.warning("⚠️ Tabla Metas vacía - intentando recuperar...")
            try:
                sheets_manager = get_sheets_manager()
                meta_df = sheets_manager.leer_hoja("Metas")
                if meta_df.empty:
                    # Crear estructura básica de metas como último recurso
                    meta_df = crear_estructura_metas_inicial()
                    sheets_manager.escribir_hoja(meta_df, "Metas", limpiar_hoja=True)
                    st.info("🔄 Tabla Metas recreada con estructura básica")
            except Exception as meta_error:
                st.error(f"❌ Error recuperando Metas: {meta_error}")
                meta_df = crear_estructura_metas_inicial()
        
        return registros_df, meta_df
        
    except ImportError:
        # Fallback si no está disponible el sistema de respaldo
        st.warning("⚠️ Sistema de respaldo no disponible, usando método básico")
        return cargar_datos_basico()
    
    except Exception as e:
        st.error(f"❌ Error crítico en carga de datos: {str(e)}")
        
        # Último recurso: intentar cargar datos básicos
        try:
            return cargar_datos_basico()
        except:
            # Si todo falla, crear estructura mínima
            st.error("❌ Creando estructura mínima de emergencia")
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
            st.warning("⚠️ Tabla de registros vacía - creando estructura básica")
            registros_df = crear_estructura_registros_basica()
        else:
            st.success(f"✅ {len(registros_df)} registros cargados (modo básico)")
        
        # Cargar metas
        try:
            meta_df = sheets_manager.leer_hoja("Metas")
            if meta_df.empty:
                meta_df = crear_estructura_metas_basica()
        except:
            meta_df = crear_estructura_metas_basica()
        
        return registros_df, meta_df
        
    except Exception as e:
        st.error(f"❌ Error en carga básica: {str(e)}")
        return crear_estructura_emergencia()

def crear_estructura_emergencia():
    """
    Crea estructura mínima de emergencia cuando todo lo demás falla.
    """
    st.warning("🚨 Creando estructura de emergencia")
    
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
    try:
        # CORRECCIÓN: Verificar si es una Series
        if isinstance(valor, pd.Series):
            # Si es una Series, verificar cada elemento
            return valor.apply(lambda x: es_fecha_valida_individual(x)).any()
        else:
            return es_fecha_valida_individual(valor)
    except Exception:
        return False

def es_fecha_valida_individual(valor):
    """Verifica si un valor individual es una fecha válida"""
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
    # CORRECCIÓN: Verificar si fecha_completado es válida
    if fecha_completado is not None and pd.notna(fecha_completado):
        # Verificar que no sea una Series
        if isinstance(fecha_completado, pd.Series):
            return fecha_completado.notna().any()
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
        if fecha_oficio and pd.notna(fecha_oficio) and str(fecha_oficio).strip() != '':
            return 100

        # Si no hay fecha de cierre, calcular normalmente
        avance = 0

        # Verificar el acuerdo de compromiso (20%)
        acuerdo_valor = registro.get('Acuerdo de compromiso', '')
        if acuerdo_valor and str(acuerdo_valor).strip().upper() in ['SI', 'SÍ', 'S', 'YES', 'Y', 'COMPLETO']:
            avance += 20

        # Verificar análisis y cronograma - basado en la fecha (20%)
        analisis_valor = registro.get('Análisis y cronograma', '')
        if analisis_valor and pd.notna(analisis_valor) and str(analisis_valor).strip() != '':
            avance += 20

        # Verificar estándares - basado en la fecha (30%)
        estandares_valor = registro.get('Estándares', '')
        if estandares_valor and pd.notna(estandares_valor) and str(estandares_valor).strip() != '':
            avance += 30

        # Verificar publicación - basado en la fecha (25%)
        publicacion_valor = registro.get('Publicación', '')
        if publicacion_valor and pd.notna(publicacion_valor) and str(publicacion_valor).strip() != '':
            avance += 25

        return avance
        
    except Exception as e:
        # En caso de error, retornar 0
        st.warning(f"Error al calcular porcentaje de avance: {e}")
        return 0
        

def procesar_metas(meta_df):
    """
    CORREGIDO: Procesa las metas a partir del DataFrame de metas.
    ELIMINA evaluaciones ambiguas de Series
    """
    try:
        # Verificar que meta_df no esté vacío
        if meta_df.empty:
            st.warning("DataFrame de metas está vacío, usando datos por defecto")
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
            except Exception as e:
                st.warning(f"Error al procesar fila {i} de metas: {e}")
                continue

        # Si no hay fechas, crear datos por defecto
        if not fechas:
            return crear_metas_por_defecto()

        # Convertir a DataFrames
        metas_nuevas_df = pd.DataFrame(metas_nuevas, index=fechas)
        metas_actualizar_df = pd.DataFrame(metas_actualizar, index=fechas)

        return metas_nuevas_df, metas_actualizar_df
        
    except Exception as e:
        st.error(f"Error al procesar metas: {e}")
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
            if campo in row and pd.notna(row[campo]):
                valor_campo = row[campo]
                # CORRECCIÓN: Verificar que no sea Series
                if isinstance(valor_campo, pd.Series):
                    continue
                
                if str(valor_campo).strip() != '':
                    fecha = procesar_fecha(valor_campo)
                    if fecha is not None and pd.notna(fecha):
                        if fecha < fecha_actual:
                            return "vencido"
                        if fecha <= fecha_actual + timedelta(days=30):
                            estado = "proximo"

        return estado
        
    except Exception as e:
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
                lambda x: formatear_fecha(x) if es_fecha_valida_individual(x) else ""
            )

    return df_validado

def guardar_datos_editados(df, crear_backup=True):
    """
    CORREGIDO: Guarda los datos editados con verificación
    ELIMINA evaluaciones ambiguas de Series
    """
    try:
        # Validación básica
        if df is None or df.empty:
            return False, "DataFrame vacío o None"

        # Validar que solo son registros
        if 'Cod' not in df.columns or 'Entidad' not in df.columns:
            return False, "Error: Solo se pueden guardar datos de registros, no metas"
        
        # Validar que los campos de fechas sean fechas válidas
        df_validado = validar_campos_fecha(df)
        
        sheets_manager = get_sheets_manager()
        
        # Crear backup de Metas ANTES de cualquier operación
        metas_backup = None
        try:
            metas_backup = sheets_manager.leer_hoja("Metas")
            if metas_backup.empty:
                metas_backup = None
        except:
            metas_backup = None
        
        # Crear respaldo automático antes de guardar
        if crear_backup:
            try:
                from backup_utils import crear_respaldo_automatico
                respaldo_exitoso = crear_respaldo_automatico(df_validado)
                if respaldo_exitoso:
                    st.info("Respaldo automático creado antes de guardar")
                else:
                    st.warning("No se pudo crear respaldo automático, pero continuando...")
            except ImportError:
                st.warning("Sistema de respaldo no disponible")
            except Exception as e:
                st.warning(f"Error en respaldo automático: {e}, pero continuando...")
        
        # Guardar SOLO en Registros
        st.info("Guardando en hoja 'Registros' de Google Sheets...")
        
        exito = sheets_manager.escribir_hoja(df_validado, "Registros", limpiar_hoja=True)
        
        # Verificación y restauración automática de Metas
        if metas_backup is not None:
            try:
                metas_actual = sheets_manager.leer_hoja("Metas")
                if metas_actual.empty:
                    st.warning("Tabla Metas se borró - Restaurando automáticamente...")
                    restaurar_exito = sheets_manager.escribir_hoja(metas_backup, "Metas", limpiar_hoja=True)
                    if restaurar_exito:
                        st.success("Tabla Metas restaurada exitosamente")
                    else:
                        st.error("ERROR CRÍTICO: No se pudo restaurar tabla Metas")
            except Exception as verificacion_error:
                st.error(f"Error verificando/restaurando Metas: {verificacion_error}")
        
        if exito:
            # Verificar que los datos se guardaron correctamente
            try:
                df_verificacion = sheets_manager.leer_hoja("Registros")
                if not df_verificacion.empty and len(df_verificacion) >= len(df_validado) * 0.9:
                    st.success("Guardado verificado en Google Sheets - Hoja 'Registros'")
                    return True, "Datos guardados y verificados exitosamente en Google Sheets."
                else:
                    st.warning("Los datos se guardaron pero la verificación mostró inconsistencias")
                    return True, "Datos guardados pero con advertencias. Verifique el contenido."
            except Exception as e:
                st.warning(f"Error en verificación post-guardado: {e}")
                return True, "Datos guardados en Google Sheets (verificación falló)."
        else:
            return False, "Error al guardar datos en Google Sheets."
            
    except Exception as e:
        error_msg = f"Error al guardar datos: {str(e)}"
        st.error(error_msg)
        return False, error_msg

def guardar_datos_editados_rapido(df, numero_fila=None):
    """
    CORREGIDO: Versión rápida para guardar cambios individuales.
    ELIMINA evaluaciones ambiguas de Series
    """
    try:
        # Validación básica
        if df is None or df.empty:
            return False, "DataFrame vacío o None"

        # Validar que solo son registros
        if 'Cod' not in df.columns or 'Entidad' not in df.columns:
            return False, "Error: Solo se pueden guardar datos de registros"
        
        sheets_manager = get_sheets_manager()
        
        # Backup rápido de Metas
        metas_backup = None
        try:
            metas_backup = sheets_manager.leer_hoja("Metas")
            if metas_backup.empty:
                metas_backup = None
        except:
            metas_backup = None
        
        if numero_fila is not None:
            # Actualizar solo una fila específica
            exito = sheets_manager.actualizar_fila(df, numero_fila, "Registros")
        else:
            # Guardar todo el DataFrame
            exito = sheets_manager.escribir_hoja(df, "Registros", limpiar_hoja=True)
        
        # Verificación rápida de Metas
        if metas_backup is not None:
            try:
                metas_actual = sheets_manager.leer_hoja("Metas")
                if metas_actual.empty:
                    sheets_manager.escribir_hoja(metas_backup, "Metas", limpiar_hoja=True)
                    st.info("Tabla Metas restaurada automáticamente")
            except:
                pass
        
        if exito:
            return True, "Datos guardados."
        else:
            return False, "Error al guardar."
            
    except Exception as e:
        return False, f"Error: {str(e)}"

def contar_registros_completados_por_fecha(df, columna_fecha_programada, columna_fecha_completado):
    """
    CORREGIDO: Cuenta los registros que tienen una fecha de completado o cuya fecha programada ya pasó.
    ELIMINA evaluaciones ambiguas de Series
    """
    count = 0
    
    for _, row in df.iterrows():
        try:
            # Verificar que la columna existe y tiene valor
            if columna_fecha_programada in row and pd.notna(row[columna_fecha_programada]):
                valor_fecha = row[columna_fecha_programada]
                
                # CORRECCIÓN: Verificar que no sea Series
                if isinstance(valor_fecha, pd.Series):
                    continue
                    
                if str(valor_fecha).strip() != '':
                    fecha_programada = valor_fecha

                    # Verificar si hay una fecha de completado VÁLIDA
                    fecha_completado = None
                    if columna_fecha_completado in row:
                        valor_completado = row[columna_fecha_completado]
                        if not isinstance(valor_completado, pd.Series) and es_fecha_valida_individual(valor_completado):
                            fecha_completado = procesar_fecha(valor_completado)

                    if verificar_completado_por_fecha(fecha_programada, fecha_completado):
                        count += 1
        except Exception as e:
            # Ignorar errores en filas individuales y continuar
            continue

    return count

# Resto de funciones auxiliares...
def verificar_integridad_metas():
    """Verifica específicamente la integridad de la tabla Metas"""
    try:
        sheets_manager = get_sheets_manager()
        metas_df = sheets_manager.leer_hoja("Metas")
        
        if metas_df.empty:
            return False, "Tabla Metas está vacía"
        
        if len(metas_df.columns) < 5:
            return False, "Tabla Metas tiene muy pocas columnas"
        
        if len(metas_df) < 3:
            return False, "Tabla Metas tiene muy pocas filas"
        
        return True, f"Tabla Metas OK: {len(metas_df)} filas, {len(metas_df.columns)} columnas"
        
    except Exception as e:
        return False, f"Error verificando Metas: {str(e)}"

def proteger_metas_durante_operacion(funcion_operacion, *args, **kwargs):
    """Wrapper para proteger Metas durante cualquier operación crítica"""
    try:
        sheets_manager = get_sheets_manager()
        
        # Crear backup de Metas antes de la operación
        metas_backup = None
        try:
            metas_backup = sheets_manager.leer_hoja("Metas")
            if metas_backup.empty:
                metas_backup = None
        except:
            metas_backup = None
        
        # Ejecutar la operación
        resultado = funcion_operacion(*args, **kwargs)
        
        # Verificar Metas después de la operación
        if metas_backup is not None:
            try:
                metas_actual = sheets_manager.leer_hoja("Metas")
                if metas_actual.empty:
                    sheets_manager.escribir_hoja(metas_backup, "Metas", limpiar_hoja=True)
                    st.warning("Tabla Metas restaurada automáticamente después de operación")
            except Exception as restore_error:
                st.error(f"Error restaurando Metas: {restore_error}")
        
        return resultado
        
    except Exception as e:
        st.error(f"Error en operación protegida: {str(e)}")
        return None

def limpiar_y_validar_registros(df):
    """Limpia y valida registros antes de cualquier operación"""
    try:
        # Verificar que es un DataFrame de registros
        if 'Cod' not in df.columns or 'Entidad' not in df.columns:
            raise ValueError("DataFrame no contiene columnas de registros válidas")
        
        # Limpiar valores
        df_limpio = df.copy()
        for col in df_limpio.columns:
            df_limpio[col] = df_limpio[col].apply(
                lambda x: '' if pd.isna(x) or x is None or str(x).strip() in ['nan', 'None'] else str(x).strip()
            )
        
        # Validar que hay al menos un registro válido
        registros_validos = df_limpio[
            (df_limpio['Cod'].notna()) & 
            (df_limpio['Cod'].astype(str).str.strip() != '') &
            (df_limpio['Entidad'].notna()) & 
            (df_limpio['Entidad'].astype(str).str.strip() != '')
        ]
        
        if registros_validos.empty:
            raise ValueError("No hay registros válidos después de la limpieza")
        
        return df_limpio
        
    except Exception as e:
        st.error(f"Error limpiando registros: {str(e)}")
        raise e

def sincronizar_con_google_sheets(df, hoja="Registros", crear_backup=True):
    """Sincronización segura con Google Sheets con protección de Metas"""
    try:
        # Validar que solo son registros
        if hoja == "Registros" and ('Cod' not in df.columns or 'Entidad' not in df.columns):
            return False, "Error: Solo se pueden sincronizar datos de registros"
        
        # Limpiar y validar datos
        df_validado = limpiar_y_validar_registros(df)
        
        # Usar protección de Metas
        def operacion_sincronizacion():
            sheets_manager = get_sheets_manager()
            return sheets_manager.escribir_hoja(df_validado, hoja, limpiar_hoja=True)
        
        # Ejecutar con protección
        exito = proteger_metas_durante_operacion(operacion_sincronizacion)
        
        if exito:
            # Crear respaldo si se solicita
            if crear_backup and hoja == "Registros":
                try:
                    from backup_utils import crear_respaldo_automatico
                    crear_respaldo_automatico(df_validado)
                except:
                    pass
            
            return True, f"Sincronización exitosa con {hoja}"
        else:
            return False, f"Error en sincronización con {hoja}"
            
    except Exception as e:
        return False, f"Error en sincronización: {str(e)}"

def obtener_estado_sistema():
    """Obtiene el estado completo del sistema de datos"""
    try:
        sheets_manager = get_sheets_manager()
        
        estado = {
            'registros': {'existe': False, 'filas': 0, 'columnas': 0, 'valido': False},
            'metas': {'existe': False, 'filas': 0, 'columnas': 0, 'valido': False},
            'respaldo': {'existe': False, 'filas': 0, 'valido': False},
            'hojas_disponibles': [],
            'errores': []
        }
        
        # Verificar hojas disponibles
        try:
            estado['hojas_disponibles'] = sheets_manager.listar_hojas()
        except Exception as e:
            estado['errores'].append(f"Error listando hojas: {str(e)}")
        
        # Verificar Registros
        try:
            registros_df = sheets_manager.leer_hoja("Registros")
            estado['registros']['existe'] = True
            estado['registros']['filas'] = len(registros_df)
            estado['registros']['columnas'] = len(registros_df.columns)
            
            # Validar registros
            if 'Cod' in registros_df.columns and 'Entidad' in registros_df.columns:
                registros_validos = registros_df[
                    (registros_df['Cod'].notna()) & 
                    (registros_df['Cod'].astype(str).str.strip() != '') &
                    (registros_df['Entidad'].notna()) & 
                    (registros_df['Entidad'].astype(str).str.strip() != '')
                ]
                estado['registros']['valido'] = len(registros_validos) > 0
        except Exception as e:
            estado['errores'].append(f"Error verificando Registros: {str(e)}")
        
        # Verificar Metas
        try:
            metas_df = sheets_manager.leer_hoja("Metas")
            estado['metas']['existe'] = True
            estado['metas']['filas'] = len(metas_df)
            estado['metas']['columnas'] = len(metas_df.columns)
            estado['metas']['valido'] = len(metas_df) > 0 and len(metas_df.columns) >= 5
        except Exception as e:
            estado['errores'].append(f"Error verificando Metas: {str(e)}")
        
        # Verificar Respaldo
        try:
            respaldo_df = sheets_manager.leer_hoja("Respaldo_Registros")
            estado['respaldo']['existe'] = True
            estado['respaldo']['filas'] = len(respaldo_df)
            estado['respaldo']['valido'] = len(respaldo_df) > 0
        except Exception as e:
            estado['errores'].append(f"Error verificando Respaldo: {str(e)}")
        
        return estado
        
    except Exception as e:
        return {
            'error_critico': str(e),
            'registros': {'existe': False, 'valido': False},
            'metas': {'existe': False, 'valido': False},
            'respaldo': {'existe': False, 'valido': False}
        }

def reparar_sistema_automatico():
    """Repara automáticamente problemas comunes del sistema"""
    try:
        sheets_manager = get_sheets_manager()
        reparaciones = []
        
        # Verificar y reparar Metas
        try:
            metas_df = sheets_manager.leer_hoja("Metas")
            if metas_df.empty:
                metas_nueva = crear_estructura_metas_inicial()
                sheets_manager.escribir_hoja(metas_nueva, "Metas", limpiar_hoja=True)
                reparaciones.append("Tabla Metas recreada")
        except:
            metas_nueva = crear_estructura_metas_inicial()
            sheets_manager.escribir_hoja(metas_nueva, "Metas", limpiar_hoja=True)
            reparaciones.append("Tabla Metas creada desde cero")
        
        # Verificar y reparar Registros
        try:
            registros_df = sheets_manager.leer_hoja("Registros")
            if registros_df.empty:
                try:
                    respaldo_df = sheets_manager.leer_hoja("Respaldo_Registros")
                    if not respaldo_df.empty:
                        sheets_manager.escribir_hoja(respaldo_df, "Registros", limpiar_hoja=True)
                        reparaciones.append("Registros restaurados desde respaldo")
                    else:
                        registros_nuevo = crear_estructura_registros_basica()
                        sheets_manager.escribir_hoja(registros_nuevo, "Registros", limpiar_hoja=True)
                        reparaciones.append("Estructura básica de Registros creada")
                except:
                    registros_nuevo = crear_estructura_registros_basica()
                    sheets_manager.escribir_hoja(registros_nuevo, "Registros", limpiar_hoja=True)
                    reparaciones.append("Estructura básica de Registros creada")
        except:
            registros_nuevo = crear_estructura_registros_basica()
            sheets_manager.escribir_hoja(registros_nuevo, "Registros", limpiar_hoja=True)
            reparaciones.append("Tabla Registros creada desde cero")
        
        return True, reparaciones
        
    except Exception as e:
        return False, [f"Error en reparación automática: {str(e)}"]

def diagnosticar_errores_datetime(df):
    """Función de diagnóstico para identificar problemas de datetime en el DataFrame"""
    print("\nDIAGNÓSTICO DE ERRORES DATETIME")
    print("="*50)
    
    campos_fecha = [
        'Fecha de entrega de información',
        'Plazo de análisis', 
        'Plazo de cronograma',
        'Análisis y cronograma',
        'Estándares (fecha programada)',
        'Estándares',
        'Fecha de publicación programada', 
        'Publicación',
        'Plazo de oficio de cierre',
        'Fecha de oficio de cierre'
    ]
    
    problemas_encontrados = []
    
    for campo in campos_fecha:
        if campo in df.columns:
            print(f"\nAnalizando campo: {campo}")
            
            valores_problematicos = []
            tipos_encontrados = []
            
            for idx, valor in df[campo].items():
                if pd.notna(valor) and str(valor).strip() != '':
                    try:
                        fecha_procesada = procesar_fecha(valor)
                        if fecha_procesada is None:
                            valores_problematicos.append((idx, valor, type(valor).__name__))
                        else:
                            tipos_encontrados.append(type(fecha_procesada).__name__)
                    except Exception as e:
                        valores_problematicos.append((idx, valor, f"Error: {e}"))
            
            if valores_problematicos:
                print(f"   {len(valores_problematicos)} valores problemáticos encontrados")
                for idx, valor, tipo_error in valores_problematicos[:3]:
                    print(f"      Fila {idx}: {valor} ({tipo_error})")
                problemas_encontrados.append(campo)
            else:
                tipos_unicos = list(set(tipos_encontrados))
                print(f"   Campo correcto. Tipos después de procesar: {tipos_unicos}")
    
    if problemas_encontrados:
        print(f"\nCAMPOS CON PROBLEMAS: {problemas_encontrados}")
    else:
        print("\nTODOS LOS CAMPOS DE FECHA ESTÁN CORRECTOS")
    
    return problemas_encontrados

def reparar_fechas_automaticamente(df):
    """Repara automáticamente los problemas de fechas más comunes"""
    print("\nREPARANDO FECHAS AUTOMÁTICAMENTE...")
    
    df_reparado = df.copy()
    reparaciones = 0
    
    campos_fecha = [
        'Fecha de entrega de información',
        'Análisis y cronograma',
        'Estándares (fecha programada)',
        'Estándares',
        'Fecha de publicación programada', 
        'Publicación',
        'Fecha de oficio de cierre'
    ]
    
    for campo in campos_fecha:
        if campo in df_reparado.columns:
            for idx, valor in df_reparado[campo].items():
                if pd.notna(valor) and str(valor).strip() != '':
                    try:
                        fecha_procesada = procesar_fecha(valor)
                        if fecha_procesada is None:
                            df_reparado.at[idx, campo] = ''
                            reparaciones += 1
                        else:
                            df_reparado.at[idx, campo] = formatear_fecha(fecha_procesada)
                    except Exception:
                        df_reparado.at[idx, campo] = ''
                        reparaciones += 1
    
    print(f"Reparaciones aplicadas: {reparaciones}")
    return df_reparado
