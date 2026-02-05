# backup_utils.py - VERSIÓN ULTRA SEGURA CON RESTAURACIÓN AUTOMÁTICA

import streamlit as st
import pandas as pd
from datetime import datetime
from sheets_utils import get_sheets_manager
import json
import os


def crear_respaldo_automatico(registros_df):
    """
    VERSIÓN ULTRA SEGURA: Crea respaldo automático con validaciones estrictas.
    """
    try:
        # VALIDACIÓN ESTRICTA: Solo crear respaldo si hay datos realmente válidos
        if registros_df.empty or len(registros_df) == 0:
            return False
        
        # Verificar columnas esenciales
        columnas_esenciales = ['Cod', 'Entidad']
        if not all(col in registros_df.columns for col in columnas_esenciales):
            return False
        
        # Validar registros con datos reales (no solo espacios o valores nulos)
        registros_validos = registros_df[
            (registros_df['Cod'].notna()) & 
            (registros_df['Cod'].astype(str).str.strip() != '') &
            (registros_df['Cod'].astype(str).str.strip() != 'nan') &
            (registros_df['Cod'].astype(str).str.strip() != 'None') &
            (registros_df['Entidad'].notna()) & 
            (registros_df['Entidad'].astype(str).str.strip() != '') &
            (registros_df['Entidad'].astype(str).str.strip() != 'nan') &
            (registros_df['Entidad'].astype(str).str.strip() != 'None')
        ]
        
        # REQUISITO MÍNIMO: Al menos 1 registro válido
        if len(registros_validos) == 0:
            return False
        
        # Proceder con el respaldo
        sheets_manager = get_sheets_manager()
        nombre_respaldo = "Respaldo_Registros"
        
        # Limpiar datos para respaldo
        df_respaldo = registros_validos.copy()
        df_respaldo = df_respaldo.fillna('')
        
        # Crear respaldo con timestamp en metadatos
        import pytz
        bogota_tz = pytz.timezone('America/Bogota')
        timestamp = datetime.now(bogota_tz)
        
        # Escribir respaldo
        exito = sheets_manager.escribir_hoja(df_respaldo, nombre_respaldo, limpiar_hoja=True)
        
        if exito:
            # Guardar metadatos del respaldo
            info_respaldo = {
                'fecha': timestamp,
                'registros': len(registros_validos),
                'columnas': len(df_respaldo.columns),
                'exitoso': True
            }
            
            # Guardar en session state
            st.session_state.ultimo_respaldo = info_respaldo
            
            # Guardar también en archivo local
            guardar_respaldo_local(df_respaldo, timestamp)
            
            return True
        else:
            return False
    
    except Exception as e:
        st.error(f"❌ Error al crear respaldo: {str(e)}")
        return False


def guardar_respaldo_local(df, timestamp):
    """Guarda respaldo local con timestamp"""
    try:
        timestamp_str = timestamp.strftime("%Y%m%d_%H%M%S")
        filename = f"respaldo_local_{timestamp_str}.csv"
        df.to_csv(filename, index=False, encoding='utf-8')
        
        # Mantener solo los últimos 10 respaldos locales
        import glob
        respaldos = glob.glob("respaldo_local_*.csv")
        if len(respaldos) > 10:
            respaldos.sort()
            for respaldo_viejo in respaldos[:-10]:
                try:
                    os.remove(respaldo_viejo)
                except:
                    pass
    except Exception as e:
        print(f"Error al guardar respaldo local: {e}")


def verificar_integridad_datos(registros_df):
    """
    NUEVA FUNCIÓN: Verifica la integridad de los datos cargados.
    Detecta si los datos fueron borrados o corrompidos.
    """
    try:
        # Verificar si el DataFrame está vacío
        if registros_df.empty or len(registros_df) == 0:
            return False, "DataFrame vacío"
        
        # Verificar columnas esenciales
        columnas_esenciales = ['Cod', 'Entidad']
        if not all(col in registros_df.columns for col in columnas_esenciales):
            return False, "Columnas esenciales faltantes"
        
        # Verificar que hay al menos un registro válido
        registros_validos = registros_df[
            (registros_df['Cod'].notna()) & 
            (registros_df['Cod'].astype(str).str.strip() != '') &
            (registros_df['Cod'].astype(str).str.strip() != 'nan') &
            (registros_df['Entidad'].notna()) & 
            (registros_df['Entidad'].astype(str).str.strip() != '') &
            (registros_df['Entidad'].astype(str).str.strip() != 'nan')
        ]
        
        if len(registros_validos) == 0:
            return False, "No hay registros válidos"
        
        # Verificar que no sean solo headers sin datos
        if len(registros_df) == 1 and all(registros_df.iloc[0].astype(str).str.strip() == ''):
            return False, "Solo headers sin datos"
        
        return True, f"Datos íntegros: {len(registros_validos)} registros válidos"
    
    except Exception as e:
        return False, f"Error verificando integridad: {str(e)}"


def restauracion_automatica_emergencia():
    """
    NUEVA FUNCIÓN: Restauración automática en caso de pérdida de datos.
    Se ejecuta automáticamente si se detecta que la tabla Registros está vacía.
    """
    try:
        st.warning("🚨 ALERTA: Datos de registros vacíos o corruptos detectados")
        st.info("🔄 Iniciando restauración automática desde respaldo...")
        
        sheets_manager = get_sheets_manager()
        
        # Verificar si existe respaldo
        hojas = sheets_manager.listar_hojas()
        if "Respaldo_Registros" not in hojas:
            st.error("❌ No hay respaldo disponible para restauración automática")
            return False, None
        
        # Leer respaldo
        df_respaldo = sheets_manager.leer_hoja("Respaldo_Registros")
        
        if df_respaldo.empty:
            st.error("❌ El respaldo está vacío")
            return False, None
        
        # Verificar integridad del respaldo
        es_valido, mensaje = verificar_integridad_datos(df_respaldo)
        if not es_valido:
            st.error(f"❌ El respaldo no es válido: {mensaje}")
            return False, None
        
        # Crear backup del estado actual (corrupto)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        try:
            registros_corruptos = sheets_manager.leer_hoja("Registros")
            if not registros_corruptos.empty:
                sheets_manager.escribir_hoja(registros_corruptos, f"Estado_Corrupto_{timestamp}", limpiar_hoja=True)
        except:
            pass
        
        # RESTAURAR AUTOMÁTICAMENTE
        exito = sheets_manager.escribir_hoja(df_respaldo, "Registros", limpiar_hoja=True)
        
        if exito:
            st.success("✅ RESTAURACIÓN AUTOMÁTICA EXITOSA")
            st.balloons()
            
            # Actualizar session state
            st.session_state.ultima_restauracion_automatica = {
                'fecha': datetime.now(),
                'registros_restaurados': len(df_respaldo),
                'motivo': 'Detección automática de datos vacíos/corruptos'
            }
            
            return True, df_respaldo
        else:
            st.error("❌ Error en restauración automática")
            return False, None
    
    except Exception as e:
        st.error(f"❌ Error en restauración automática de emergencia: {str(e)}")
        return False, None


def verificar_disponibilidad_respaldo():
    """Verifica disponibilidad de respaldo con información detallada"""
    try:
        sheets_manager = get_sheets_manager()
        hojas = sheets_manager.listar_hojas()
        
        if "Respaldo_Registros" in hojas:
            df_respaldo = sheets_manager.leer_hoja("Respaldo_Registros")
            
            if not df_respaldo.empty:
                # Verificar integridad del respaldo
                es_valido, mensaje = verificar_integridad_datos(df_respaldo)
                
                info_respaldo = {
                    'registros': len(df_respaldo),
                    'columnas': len(df_respaldo.columns),
                    'disponible': True,
                    'valido': es_valido,
                    'mensaje': mensaje
                }
                return True, info_respaldo
        
        return False, None
    
    except Exception as e:
        return False, None


def obtener_fecha_ultimo_respaldo():
    """
    NUEVA FUNCIÓN: Obtiene la fecha del último respaldo válido.
    Para mostrar en el estado del sistema.
    """
    try:
        # Primero intentar desde session state
        if 'ultimo_respaldo' in st.session_state:
            return st.session_state.ultimo_respaldo['fecha']
        
        # Si no, verificar si existe respaldo en Google Sheets
        tiene_respaldo, info = verificar_disponibilidad_respaldo()
        if tiene_respaldo and info['valido']:
            # No podemos obtener la fecha exacta de Google Sheets sin metadatos adicionales
            # Pero sabemos que existe un respaldo válido
            return "Respaldo disponible (fecha exacta no disponible)"
        
        return None
    
    except Exception as e:
        return None


def mostrar_estado_respaldos_detallado():
    """
    NUEVA FUNCIÓN: Muestra estado detallado de respaldos para el sistema.
    """
    fecha_ultimo = obtener_fecha_ultimo_respaldo()
    tiene_respaldo, info = verificar_disponibilidad_respaldo()
    
    # Información básica para mostrar en estado del sistema
    if fecha_ultimo:
        if isinstance(fecha_ultimo, datetime):
            fecha_str = fecha_ultimo.strftime("%d/%m/%Y %H:%M")
        else:
            fecha_str = str(fecha_ultimo)
        
        estado_respaldo = f"✅ Último respaldo: {fecha_str}"
    else:
        estado_respaldo = "⚠️ Sin respaldo reciente"
    
    # Información adicional
    if tiene_respaldo and info:
        if info['valido']:
            estado_adicional = f" | 💾 {info['registros']} registros respaldados"
        else:
            estado_adicional = f" | ⚠️ Respaldo corrupto: {info['mensaje']}"
    else:
        estado_adicional = " | ❌ No hay respaldo disponible"
    
    return estado_respaldo + estado_adicional


def cargar_datos_con_respaldo():
    """
    VERSIÓN ULTRA SEGURA: Carga datos con verificación automática y restauración.
    """
    try:
        sheets_manager = get_sheets_manager()
        
        # Cargar datos desde Google Sheets
        registros_df = sheets_manager.leer_hoja("Registros")
        
        # VERIFICACIÓN AUTOMÁTICA DE INTEGRIDAD
        es_valido, mensaje = verificar_integridad_datos(registros_df)
        
        if not es_valido:
            st.warning(f"⚠️ Problema detectado en datos: {mensaje}")
            
            # RESTAURACIÓN AUTOMÁTICA
            exito_restauracion, registros_restaurados = restauracion_automatica_emergencia()
            
            if exito_restauracion:
                registros_df = registros_restaurados
                st.success("🔄 Datos restaurados automáticamente desde respaldo")
            else:
                # Si falla la restauración automática, crear estructura mínima
                st.error("❌ Restauración automática falló. Creando estructura mínima.")
                registros_df = crear_estructura_registros_minima()
        else:
            st.success(f"✅ {len(registros_df)} registros cargados y verificados")
        
        # Lista de columnas requeridas
        columnas_requeridas = [
            'Cod', 'Funcionario', 'Entidad', 'Nivel Información ', 'Frecuencia actualizacion ',
            'TipoDato', 'Trimestre proyectado', 'Actas de acercamiento y manifestación de interés',
            'Suscripción acuerdo de compromiso', 'Entrega acuerdo de compromiso',
            'Acuerdo de compromiso', 'Gestion acceso a los datos y documentos requeridos ',
            'Análisis de información', 'Cronograma Concertado', 'Análisis y cronograma (fecha programada)',
            'Fecha de entrega de información', 'Plazo de análisis', 'Análisis y cronograma',
            'Seguimiento a los acuerdos', 'Registro', 'ET', 'CO', 'DD', 'REC', 'SERVICIO',
            'Estándares (fecha programada)', 'Estándares', 'Resultados de orientación técnica',
            'Verificación del servicio web geográfico', 'Verificar Aprobar Resultados',
            'Revisar y validar los datos cargados en la base de datos',
            'Aprobación resultados obtenidos en la rientación', 'Disponer datos temáticos',
            'Fecha de publicación programada', 'Publicación', 'Catálogo de recursos geográficos',
            'Oficios de cierre', 'Fecha de oficio de cierre', 'Plazo de cronograma',
            'Plazo de oficio de cierre', 'Estado', 'Observación'
        ]
        
        # Añadir columnas faltantes si hay datos válidos
        if es_valido:
            for columna in columnas_requeridas:
                if columna not in registros_df.columns:
                    registros_df[columna] = ''
            
            # Crear respaldo automático de los datos válidos
            crear_respaldo_automatico(registros_df)
            
            # Limpiar valores
            for col in registros_df.columns:
                registros_df[col] = registros_df[col].apply(lambda x: '' if pd.isna(x) or x is None else str(x).strip())
        
        # Cargar metas
        try:
            meta_df = sheets_manager.leer_hoja("Metas")
            
            if meta_df.empty:
                meta_df = crear_estructura_metas_inicial()
                sheets_manager.escribir_hoja(meta_df, "Metas", limpiar_hoja=True)
            else:
                # Limpiar valores de metas
                for col in meta_df.columns:
                    meta_df[col] = meta_df[col].apply(lambda x: '' if pd.isna(x) or x is None else str(x).strip())
        
        except Exception as e:
            meta_df = crear_estructura_metas_inicial()
        
        return registros_df, meta_df
    
    except Exception as e:
        st.error(f"❌ Error crítico cargando datos: {e}")
        
        # Último recurso: crear estructura mínima
        registros_df = crear_estructura_registros_minima()
        meta_df = crear_estructura_metas_inicial()
        
        return registros_df, meta_df


def crear_estructura_registros_minima():
    """Crea estructura mínima de registros cuando todo falla"""
    columnas_minimas = [
        'Cod', 'Funcionario', 'Entidad', 'Nivel Información ', 'Frecuencia actualizacion ',
        'TipoDato', 'Trimestre proyectado', 'Acuerdo de compromiso', 'Análisis y cronograma',
        'Estándares', 'Publicación', 'Fecha de entrega de información',
        'Plazo de análisis', 'Plazo de cronograma', 'Plazo de oficio de cierre',
        'Fecha de oficio de cierre', 'Estado', 'Observación'
    ]
    
    return pd.DataFrame(columns=columnas_minimas)


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


def restaurar_desde_respaldo():
    """Función manual para restaurar desde respaldo"""
    try:
        sheets_manager = get_sheets_manager()
        
        df_respaldo = sheets_manager.leer_hoja("Respaldo_Registros")
        
        if df_respaldo.empty:
            st.error("❌ El respaldo está vacío")
            return False, None
        
        # Verificar integridad
        es_valido, mensaje = verificar_integridad_datos(df_respaldo)
        if not es_valido:
            st.error(f"❌ El respaldo no es válido: {mensaje}")
            return False, None
        
        # Crear backup del estado actual
        try:
            registros_actuales = sheets_manager.leer_hoja("Registros")
            if not registros_actuales.empty:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                sheets_manager.escribir_hoja(registros_actuales, f"Backup_Manual_{timestamp}", limpiar_hoja=True)
        except:
            pass
        
        # Restaurar
        exito = sheets_manager.escribir_hoja(df_respaldo, "Registros", limpiar_hoja=True)
        
        if exito:
            st.session_state.ultima_restauracion_manual = datetime.now()
            return True, df_respaldo
        else:
            return False, None
    
    except Exception as e:
        st.error(f"❌ Error en restauración manual: {str(e)}")
        return False, None


def mostrar_panel_restauracion():
    """Panel de restauración manual"""
    st.markdown("### 🔧 Panel de Restauración Manual")
    
    tiene_respaldo, info = verificar_disponibilidad_respaldo()
    
    if tiene_respaldo and info['valido']:
        st.info(f"💾 Respaldo válido disponible: {info['registros']} registros")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔄 Restaurar Manualmente", type="primary"):
                with st.spinner("Restaurando datos..."):
                    exito, df = restaurar_desde_respaldo()
                    if exito:
                        st.success("✅ Restauración manual exitosa")
                        st.balloons()
                        st.rerun()
        
        with col2:
            st.warning("⚠️ Esto sobrescribirá los datos actuales")
    
    elif tiene_respaldo:
        st.error(f"❌ El respaldo existe pero no es válido: {info['mensaje']}")
    else:
        st.warning("⚠️ No hay respaldo disponible")
