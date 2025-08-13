import pandas as pd
import numpy as np
import io
import re
import os
import streamlit as st
from datetime import datetime, timedelta
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
    VERSIÓN SIN ACTUALIZACIONES AUTOMÁTICAS: 
    Carga los datos EXACTAMENTE como están en Google Sheets, sin aplicar cálculos.
    """
    try:
        sheets_manager = get_sheets_manager()
        
        # Cargar registros TAL COMO ESTÁN
        registros_df = sheets_manager.leer_hoja("Registros")
        
        if registros_df.empty:
            st.warning("⚠️ Tabla de registros vacía")
            registros_df = crear_estructura_registros_basica()
        else:
            # Solo limpiar valores, NO calcular nada
            for col in registros_df.columns:
                registros_df[col] = registros_df[col].apply(
                    lambda x: '' if pd.isna(x) or x is None or str(x).strip() in ['nan', 'None'] else str(x).strip()
                )
        
        # Cargar metas
        try:
            meta_df = sheets_manager.leer_hoja("Metas")
            if meta_df.empty:
                meta_df = crear_estructura_metas_inicial()
                # No guardar automáticamente
        except:
            meta_df = crear_estructura_metas_inicial()
        
        return registros_df, meta_df
        
    except Exception as e:
        st.error(f"❌ Error cargando datos: {str(e)}")
        return crear_estructura_registros_basica(), crear_estructura_metas_inicial()

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
        'Plazo de oficio de cierre', 'Estado', 'Observación', 'Porcentaje Avance', 'Estado Fechas'
    ]
    
    return pd.DataFrame(columns=columnas_basicas)

def crear_estructura_metas_inicial():
    """Crea estructura inicial para las metas"""
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
    """Procesa una fecha de manera segura manejando NaT."""
    if pd.isna(fecha_str) or fecha_str == '' or fecha_str is None:
        return None

    # Si es un objeto datetime o Timestamp, retornarlo directamente
    if isinstance(fecha_str, (pd.Timestamp, datetime)):
        if pd.isna(fecha_str):  # Comprobar si es NaT
            return None
        return fecha_str

    # Si es un string, procesarlo
    try:
        # Eliminar espacios y caracteres extraños
        fecha_str = re.sub(r'[^\d/\-]', '', str(fecha_str).strip())

        # Formatos a intentar
        formatos = ['%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y', '%m/%d/%Y']

        for formato in formatos:
            try:
                fecha = pd.to_datetime(fecha_str, format=formato)
                if pd.notna(fecha):  # Verificar que no sea NaT
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
        return ""

def calcular_porcentaje_avance(registro):
    """
    Calcula el porcentaje de avance de un registro basado en los campos de completitud.
    NUEVA REGLA: Si tiene fecha de oficio de cierre, automáticamente 100% de avance.
    """
    try:
        # NUEVA REGLA: Si tiene fecha de oficio de cierre, automáticamente 100%
        if ('Fecha de oficio de cierre' in registro and 
            registro['Fecha de oficio de cierre'] and 
            pd.notna(registro['Fecha de oficio de cierre']) and
            str(registro['Fecha de oficio de cierre']).strip() != ''):
            return 100

        # Si no hay fecha de cierre, calcular normalmente
        avance = 0

        # Verificar el acuerdo de compromiso (20%)
        if 'Acuerdo de compromiso' in registro and str(registro['Acuerdo de compromiso']).strip().upper() in ['SI',
                                                                                                              'SÍ', 'S',
                                                                                                              'YES',
                                                                                                              'Y',
                                                                                                              'COMPLETO']:
            avance += 20

        # Verificar análisis y cronograma - basado en la fecha (20%)
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

        # Verificar publicación - basado en la fecha (25%)
        if ('Publicación' in registro and 
            registro['Publicación'] and 
            pd.notna(registro['Publicación']) and
            str(registro['Publicación']).strip() != ''):
            avance += 25

        return avance
    except Exception as e:
        return 0

def procesar_metas(meta_df):
    """Procesa las metas a partir del DataFrame de metas."""
    try:
        # La estructura de las metas es compleja, vamos a procesarla
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
                continue

        # Si no hay fechas, usar datos por defecto
        if not fechas:
            fechas = [datetime.now()]
            for hito in metas_nuevas:
                metas_nuevas[hito] = [0]
                metas_actualizar[hito] = [0]

        # Convertir a DataFrames
        metas_nuevas_df = pd.DataFrame(metas_nuevas, index=fechas)
        metas_actualizar_df = pd.DataFrame(metas_actualizar, index=fechas)

        return metas_nuevas_df, metas_actualizar_df
    except Exception as e:
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
    """Verifica si las fechas están vencidas o próximas a vencer."""
    fecha_actual = datetime.now()
    estado = "normal"  # Por defecto, estado normal

    # Lista de campos de fechas a verificar
    campos_fecha = [
        'Análisis y cronograma (fecha programada)',
        'Estándares (fecha programada)',
        'Fecha de publicación programada'
    ]

    for campo in campos_fecha:
        if campo in row and pd.notna(row[campo]) and str(row[campo]).strip() != '':
            fecha = procesar_fecha(row[campo])
            if fecha is not None and pd.notna(fecha):
                # Si la fecha ya está vencida
                if fecha < fecha_actual:
                    return "vencido"  # Prioridad alta, retornamos inmediatamente

                # Si la fecha está próxima a vencer en los próximos 30 días
                if fecha <= fecha_actual + timedelta(days=30):
                    estado = "proximo"  # Marcamos como próximo, pero seguimos verificando otras fechas

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

def guardar_datos_editados(df, crear_backup=True):
    """
    VERSIÓN SIN AUTO-UPDATES: Guarda los datos editados SIN aplicar cálculos automáticos previos.
    Los cálculos se deben hacer ANTES de llamar esta función.
    """
    try:
        # Validación básica
        if 'Cod' not in df.columns or 'Entidad' not in df.columns:
            return False, "❌ Error: Solo se pueden guardar datos de registros"
        
        # Validar que los campos de fechas sean fechas válidas
        df_validado = validar_campos_fecha(df)
        
        sheets_manager = get_sheets_manager()
        
        # NOTA: Los cálculos YA deben estar aplicados en df_validado
        # Esta función solo guarda, no calcula
        
        exito = sheets_manager.escribir_hoja(df_validado, "Registros", limpiar_hoja=True)
        
        if exito:
            # Verificación básica
            try:
                df_verificacion = sheets_manager.leer_hoja("Registros")
                if not df_verificacion.empty and len(df_verificacion) >= len(df_validado) * 0.9:
                    return True, "✅ Datos guardados exitosamente en Google Sheets."
                else:
                    return True, "⚠️ Datos guardados pero con advertencias en verificación."
            except Exception as e:
                return True, "✅ Datos guardados (verificación falló)."
        else:
            return False, "❌ Error al guardar datos en Google Sheets."
            
    except Exception as e:
        error_msg = f"❌ Error al guardar datos: {str(e)}"
        return False, error_msg

def guardar_datos_editados_rapido(df, numero_fila=None):
    """
    Versión rápida para guardar cambios - SIN cálculos automáticos.
    """
    try:
        # Validación básica
        if 'Cod' not in df.columns or 'Entidad' not in df.columns:
            return False, "❌ Error: Solo se pueden guardar datos de registros"
        
        sheets_manager = get_sheets_manager()
        
        if df.empty:
            return False, "❌ Error: Datos vacíos"
        
        if numero_fila is not None:
            # Actualizar solo una fila específica
            exito = sheets_manager.actualizar_fila(df, numero_fila, "Registros")
        else:
            # Guardar todo el DataFrame
            exito = sheets_manager.escribir_hoja(df, "Registros", limpiar_hoja=True)
        
        if exito:
            return True, "✅ Datos guardados."
        else:
            return False, "❌ Error al guardar."
            
    except Exception as e:
        return False, f"❌ Error: {str(e)}"

def contar_registros_completados_por_fecha(df, columna_fecha_programada, columna_fecha_completado):
    """
    Cuenta los registros que tienen una fecha de completado o cuya fecha programada ya pasó.
    """
    count = 0
    for _, row in df.iterrows():
        if columna_fecha_programada in row and pd.notna(row[columna_fecha_programada]) and str(row[columna_fecha_programada]).strip() != '':
            fecha_programada = row[columna_fecha_programada]

            # Verificar si hay una fecha de completado VÁLIDA
            fecha_completado = None
            if columna_fecha_completado in row:
                # Usar es_fecha_valida para verificar si realmente es una fecha
                if es_fecha_valida(row[columna_fecha_completado]):
                    fecha_completado = procesar_fecha(row[columna_fecha_completado])

            if verificar_completado_por_fecha(fecha_programada, fecha_completado):
                count += 1

    return count

def verificar_completado_por_fecha(fecha_programada, fecha_completado=None):
    """
    Verifica si una tarea está completada basada en fechas.
    Si fecha_completado está presente, la tarea está completada.
    Si no, se verifica si la fecha programada ya pasó.
    """
    if fecha_completado is not None and pd.notna(fecha_completado):
        return True

    fecha_actual = datetime.now()
    fecha_prog = procesar_fecha(fecha_programada)

    if fecha_prog is not None and pd.notna(fecha_prog) and fecha_prog <= fecha_actual:
        return True

    return False

# ===== FUNCIONES DE APLICACIÓN MANUAL DE CÁLCULOS =====

def aplicar_calculos_completos(df):
    """
    NUEVA FUNCIÓN: Aplica TODOS los cálculos y validaciones de una vez.
    Esta función se llama ÚNICAMENTE cuando el usuario presiona "Guardar Cambios".
    """
    try:
        # Importar las funciones necesarias
        from validaciones_utils import validar_reglas_negocio
        from fecha_utils import actualizar_plazo_analisis, actualizar_plazo_cronograma, actualizar_plazo_oficio_cierre
        
        st.info("🔄 Aplicando validaciones y cálculos...")
        
        # 1. Aplicar reglas de negocio
        df_procesado = validar_reglas_negocio(df)
        
        # 2. Actualizar plazos automáticamente
        df_procesado = actualizar_plazo_analisis(df_procesado)
        df_procesado = actualizar_plazo_cronograma(df_procesado)  
        df_procesado = actualizar_plazo_oficio_cierre(df_procesado)
        
        # 3. Recalcular porcentajes de avance
        df_procesado['Porcentaje Avance'] = df_procesado.apply(calcular_porcentaje_avance, axis=1)
        
        # 4. Actualizar estado de fechas
        df_procesado['Estado Fechas'] = df_procesado.apply(verificar_estado_fechas, axis=1)
        
        st.success("✅ Cálculos aplicados correctamente")
        
        return df_procesado
        
    except Exception as e:
        st.error(f"❌ Error aplicando cálculos: {str(e)}")
        return df

def mostrar_preview_calculos(df, indice_registro):
    """
    NUEVA FUNCIÓN: Muestra una vista previa de cómo quedarían los cálculos sin guardar.
    """
    try:
        # Crear copia temporal
        df_temp = df.copy()
        
        # Aplicar cálculos temporalmente
        df_temp = aplicar_calculos_completos(df_temp)
        
        # Obtener el registro específico
        registro_temp = df_temp.iloc[indice_registro]
        
        # Mostrar información
        info_preview = f"""
        **Vista Previa de Cálculos para Registro #{registro_temp.get('Cod', 'N/A')}:**
        
        📅 **Plazos Calculados:**
        - Plazo de análisis: {registro_temp.get('Plazo de análisis', 'N/A')}
        - Plazo de cronograma: {registro_temp.get('Plazo de cronograma', 'N/A')} 
        - Plazo oficio cierre: {registro_temp.get('Plazo de oficio de cierre', 'N/A')}
        
        📊 **Progreso:**
        - Porcentaje avance: {registro_temp.get('Porcentaje Avance', 0)}%
        - Estado fechas: {registro_temp.get('Estado Fechas', 'N/A')}
        - Estado general: {registro_temp.get('Estado', 'N/A')}
        """
        
        return info_preview, df_temp
        
    except Exception as e:
        return f"❌ Error en vista previa: {str(e)}", df

# ===== FUNCIONES DE UTILIDAD ADICIONALES =====

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
        st.error(f"❌ Error limpiando registros: {str(e)}")
        raise e

def obtener_resumen_cambios(df_original, df_modificado):
    """
    NUEVA FUNCIÓN: Compara dos DataFrames y muestra un resumen de los cambios.
    """
    try:
        cambios = []
        
        # Verificar cambios por registro
        for idx in df_modificado.index:
            if idx in df_original.index:
                registro_original = df_original.loc[idx]
                registro_modificado = df_modificado.loc[idx]
                
                cambios_registro = []
                for col in df_modificado.columns:
                    if col in df_original.columns:
                        valor_original = str(registro_original[col]).strip()
                        valor_modificado = str(registro_modificado[col]).strip()
                        
                        if valor_original != valor_modificado:
                            cambios_registro.append(f"{col}: '{valor_original}' → '{valor_modificado}'")
                
                if cambios_registro:
                    cod = registro_modificado.get('Cod', f'Índice {idx}')
                    cambios.append(f"**Registro {cod}:**\n" + "\n".join([f"  - {c}" for c in cambios_registro]))
        
        if cambios:
            return "### 📝 Resumen de Cambios:\n\n" + "\n\n".join(cambios)
        else:
            return "### ✅ No hay cambios detectados"
            
    except Exception as e:
        return f"### ❌ Error analizando cambios: {str(e)}"
