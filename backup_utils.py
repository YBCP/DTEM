# backup_utils.py - Sistema de Respaldo y Restauración

import streamlit as st
import pandas as pd
from datetime import datetime
from sheets_utils import get_sheets_manager
import json
import os


def crear_respaldo_automatico(registros_df):
    """
    Crea un respaldo automático de los datos de registros si hay datos válidos.
    
    Args:
        registros_df: DataFrame con los registros actuales
    
    Returns:
        bool: True si se creó el respaldo, False si no
    """
    try:
        # Verificar si hay datos válidos para respaldar
        if registros_df.empty or len(registros_df) == 0:
            st.info("📋 No hay datos para respaldar - tabla de registros vacía")
            return False
        
        # Verificar que tenga columnas esenciales
        columnas_esenciales = ['Cod', 'Entidad', 'Nivel Información ']
        if not all(col in registros_df.columns for col in columnas_esenciales):
            st.warning("⚠️ Datos incompletos - no se puede crear respaldo")
            return False
        
        # Verificar que tenga al menos un registro con datos válidos
        registros_validos = registros_df[
            (registros_df['Cod'].notna()) & 
            (registros_df['Cod'].astype(str).str.strip() != '') &
            (registros_df['Entidad'].notna()) & 
            (registros_df['Entidad'].astype(str).str.strip() != '')
        ]
        
        if len(registros_validos) == 0:
            st.warning("⚠️ No hay registros válidos para respaldar")
            return False
        
        # Crear respaldo en Google Sheets
        sheets_manager = get_sheets_manager()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        nombre_respaldo = f"Respaldo_Registros"
        
        # Limpiar y preparar datos para respaldo
        df_respaldo = registros_df.copy()
        df_respaldo = df_respaldo.fillna('')
        
        # Escribir respaldo en Google Sheets
        exito = sheets_manager.escribir_hoja(df_respaldo, nombre_respaldo, limpiar_hoja=True)
        
        if exito:
            # Guardar información del respaldo en session state
            st.session_state.ultimo_respaldo = {
                'fecha': datetime.now(),
                'registros': len(registros_validos),
                'columnas': len(df_respaldo.columns)
            }
            
            # Guardar también en archivo local como respaldo adicional
            guardar_respaldo_local(df_respaldo)
            
            st.success(f"✅ Respaldo creado exitosamente: {len(registros_validos)} registros respaldados")
            return True
        else:
            st.error("❌ Error al crear respaldo en Google Sheets")
            return False
    
    except Exception as e:
        st.error(f"❌ Error al crear respaldo automático: {str(e)}")
        return False


def guardar_respaldo_local(df):
    """Guarda un respaldo local adicional como seguridad"""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"respaldo_local_{timestamp}.csv"
        df.to_csv(filename, index=False, encoding='utf-8')
        
        # Mantener solo los últimos 5 respaldos locales
        import glob
        respaldos = glob.glob("respaldo_local_*.csv")
        if len(respaldos) > 5:
            respaldos.sort()
            for respaldo_viejo in respaldos[:-5]:
                try:
                    os.remove(respaldo_viejo)
                except:
                    pass
    except Exception as e:
        print(f"Error al guardar respaldo local: {e}")


def verificar_disponibilidad_respaldo():
    """
    Verifica si existe un respaldo disponible en Google Sheets.
    
    Returns:
        tuple: (existe_respaldo, info_respaldo)
    """
    try:
        sheets_manager = get_sheets_manager()
        hojas = sheets_manager.listar_hojas()
        
        if "Respaldo_Registros" in hojas:
            # Leer el respaldo para obtener información
            df_respaldo = sheets_manager.leer_hoja("Respaldo_Registros")
            
            if not df_respaldo.empty:
                info_respaldo = {
                    'registros': len(df_respaldo),
                    'columnas': len(df_respaldo.columns),
                    'disponible': True
                }
                return True, info_respaldo
        
        return False, None
    
    except Exception as e:
        st.error(f"Error al verificar respaldo: {str(e)}")
        return False, None


def restaurar_desde_respaldo():
    """
    Restaura los datos desde el respaldo disponible.
    
    Returns:
        tuple: (exito, df_restaurado)
    """
    try:
        sheets_manager = get_sheets_manager()
        
        # Leer datos del respaldo
        df_respaldo = sheets_manager.leer_hoja("Respaldo_Registros")
        
        if df_respaldo.empty:
            st.error("❌ El respaldo está vacío o no existe")
            return False, None
        
        # Verificar que el respaldo tenga datos válidos
        columnas_esenciales = ['Cod', 'Entidad', 'Nivel Información ']
        if not all(col in df_respaldo.columns for col in columnas_esenciales):
            st.error("❌ El respaldo no tiene la estructura correcta")
            return False, None
        
        # Crear backup del estado actual antes de restaurar (si hay datos)
        try:
            registros_actuales = sheets_manager.leer_hoja("Registros")
            if not registros_actuales.empty:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                sheets_manager.escribir_hoja(registros_actuales, f"Backup_Pre_Restauracion_{timestamp}", limpiar_hoja=True)
        except:
            pass  # No importa si falla, continuamos con la restauración
        
        # Restaurar datos a la hoja principal
        exito = sheets_manager.escribir_hoja(df_respaldo, "Registros", limpiar_hoja=True)
        
        if exito:
            st.success(f"✅ Datos restaurados exitosamente: {len(df_respaldo)} registros")
            
            # Actualizar información del último respaldo
            st.session_state.ultima_restauracion = datetime.now()
            
            return True, df_respaldo
        else:
            st.error("❌ Error al restaurar datos en Google Sheets")
            return False, None
    
    except Exception as e:
        st.error(f"❌ Error durante la restauración: {str(e)}")
        return False, None


def mostrar_estado_respaldos():
    """Muestra el estado actual de los respaldos en la interfaz"""
    
    st.markdown("### 🛡️ Estado de Respaldos")
    
    # Verificar disponibilidad de respaldo
    tiene_respaldo, info_respaldo = verificar_disponibilidad_respaldo()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Estado del último respaldo
        if 'ultimo_respaldo' in st.session_state:
            ultimo = st.session_state.ultimo_respaldo
            fecha_respaldo = ultimo['fecha'].strftime("%d/%m/%Y %H:%M")
            st.markdown(f"""
            <div style="background: #d4edda; border: 1px solid #c3e6cb; border-radius: 5px; padding: 15px;">
                <h5 style="color: #155724; margin: 0;">✅ Último Respaldo</h5>
                <p style="margin: 5px 0; color: #155724;">📅 {fecha_respaldo}</p>
                <p style="margin: 0; color: #155724;">📊 {ultimo['registros']} registros</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="background: #f8d7da; border: 1px solid #f5c6cb; border-radius: 5px; padding: 15px;">
                <h5 style="color: #721c24; margin: 0;">⚠️ Sin Respaldo Reciente</h5>
                <p style="margin: 0; color: #721c24;">No hay información de respaldos</p>
            </div>
            """, unsafe_allow_html=True)
    
    with col2:
        # Estado del respaldo disponible
        if tiene_respaldo:
            st.markdown(f"""
            <div style="background: #d1ecf1; border: 1px solid #bee5eb; border-radius: 5px; padding: 15px;">
                <h5 style="color: #0c5460; margin: 0;">💾 Respaldo Disponible</h5>
                <p style="margin: 5px 0; color: #0c5460;">📊 {info_respaldo['registros']} registros</p>
                <p style="margin: 0; color: #0c5460;">📋 {info_respaldo['columnas']} columnas</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="background: #fff3cd; border: 1px solid #ffeaa7; border-radius: 5px; padding: 15px;">
                <h5 style="color: #856404; margin: 0;">📂 Sin Respaldo</h5>
                <p style="margin: 0; color: #856404;">No hay respaldo disponible</p>
            </div>
            """, unsafe_allow_html=True)
    
    with col3:
        # Estado de la última restauración
        if 'ultima_restauracion' in st.session_state:
            fecha_restauracion = st.session_state.ultima_restauracion.strftime("%d/%m/%Y %H:%M")
            st.markdown(f"""
            <div style="background: #e2e3e5; border: 1px solid #d6d8db; border-radius: 5px; padding: 15px;">
                <h5 style="color: #383d41; margin: 0;">🔄 Última Restauración</h5>
                <p style="margin: 0; color: #383d41;">📅 {fecha_restauracion}</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="background: #e2e3e5; border: 1px solid #d6d8db; border-radius: 5px; padding: 15px;">
                <h5 style="color: #383d41; margin: 0;">🔄 Restauración</h5>
                <p style="margin: 0; color: #383d41;">No se han hecho restauraciones</p>
            </div>
            """, unsafe_allow_html=True)


def mostrar_panel_restauracion():
    """Muestra el panel de restauración de datos"""
    
    st.markdown("### 🔧 Panel de Restauración")
    
    # Verificar si hay respaldo disponible
    tiene_respaldo, info_respaldo = verificar_disponibilidad_respaldo()
    
    if tiene_respaldo:
        st.info(f"💾 Respaldo disponible: {info_respaldo['registros']} registros con {info_respaldo['columnas']} columnas")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔄 Restaurar Datos desde Respaldo", type="primary"):
                with st.spinner("Restaurando datos desde respaldo..."):
                    exito, df_restaurado = restaurar_desde_respaldo()
                    
                    if exito:
                        st.success("✅ Datos restaurados exitosamente")
                        st.balloons()
                        st.rerun()
                    else:
                        st.error("❌ Error durante la restauración")
        
        with col2:
            st.warning("⚠️ Esta acción sobrescribirá los datos actuales en la tabla Registros")
    
    else:
        st.warning("⚠️ No hay respaldo disponible para restaurar")
        st.info("El respaldo se crea automáticamente cuando hay datos válidos en la tabla Registros")


def cargar_datos_con_respaldo():
    """
    Versión mejorada de cargar_datos() que incluye sistema de respaldo automático.
    
    Returns:
        tuple: (registros_df, meta_df)
    """
    try:
        sheets_manager = get_sheets_manager()
        
        # Primero intentar cargar registros existentes
        st.info("🔄 Cargando datos desde Google Sheets...")
        registros_df = sheets_manager.leer_hoja("Registros")
        
        # Lista de columnas requeridas (INCLUYE MES PROYECTADO)
        columnas_requeridas = [
            'Cod', 'Funcionario', 'Entidad', 'Nivel Información ', 'Frecuencia actualizacion ',
            'TipoDato', 'Mes Proyectado', 'Actas de acercamiento y manifestación de interés',
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
        
        if registros_df.empty:
            st.warning("⚠️ La tabla 'Registros' está vacía")
            
            # Verificar si hay respaldo disponible
            tiene_respaldo, info_respaldo = verificar_disponibilidad_respaldo()
            
            if tiene_respaldo:
                st.info(f"💾 Se encontró un respaldo con {info_respaldo['registros']} registros")
                
                # Mostrar opción de restauración automática
                if st.button("🔄 Restaurar automáticamente desde respaldo"):
                    exito, registros_df = restaurar_desde_respaldo()
                    if exito:
                        st.rerun()
                else:
                    # Crear DataFrame vacío con estructura correcta
                    registros_df = pd.DataFrame(columns=columnas_requeridas)
            else:
                st.info("📋 Creando estructura inicial de la tabla...")
                # Crear DataFrame vacío con estructura correcta
                registros_df = pd.DataFrame(columns=columnas_requeridas)
                sheets_manager.escribir_hoja(registros_df, "Registros", limpiar_hoja=True)
        
        else:
            st.success(f"✅ {len(registros_df)} registros cargados desde Google Sheets")
            
            # Verificar y añadir columnas faltantes
            for columna in columnas_requeridas:
                if columna not in registros_df.columns:
                    st.warning(f"⚠️ Añadiendo columna faltante: '{columna}'")
                    registros_df[columna] = ''
            
            # CREAR RESPALDO AUTOMÁTICO si hay datos válidos
            crear_respaldo_automatico(registros_df)
            
            # Limpiar valores
            for col in registros_df.columns:
                registros_df[col] = registros_df[col].apply(lambda x: '' if pd.isna(x) or x is None else str(x).strip())
        
        # Cargar metas
        try:
            meta_df = sheets_manager.leer_hoja("Metas")
            
            if meta_df.empty:
                st.warning("⚠️ La hoja 'Metas' está vacía. Creando estructura inicial...")
                meta_df = crear_estructura_metas_inicial()
                sheets_manager.escribir_hoja(meta_df, "Metas", limpiar_hoja=True)
            else:
                st.success("✅ Metas cargadas desde Google Sheets")
                
                # Limpiar valores de metas
                for col in meta_df.columns:
                    meta_df[col] = meta_df[col].apply(lambda x: '' if pd.isna(x) or x is None else str(x).strip())
        
        except Exception as e:
            st.error(f"❌ Error al cargar metas: {str(e)}")
            meta_df = crear_estructura_metas_inicial()
        
        return registros_df, meta_df
    
    except Exception as e:
        st.error(f"❌ Error general al cargar datos: {e}")
        
        # Como último recurso, crear DataFrames mínimos
        registros_df = pd.DataFrame(columns=columnas_requeridas)
        meta_df = crear_estructura_metas_inicial()
        
        return registros_df, meta_df


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
