# app1_corregido.py - CORRECCIÓN CRÍTICA PARA EL PROBLEMA DE REPORTES
"""
Archivo principal del sistema Ideca - CORREGIDO
SOLUCIONA: Problema de importación que causa que los reportes no se muestren
"""

import streamlit as st
import pandas as pd
from datetime import datetime

# ===== IMPORTS DE MÓDULOS FRAGMENTADOS (CORREGIDOS) =====
from dashboard import mostrar_dashboard
from editor import mostrar_edicion_registros_con_autenticacion
from alertas import mostrar_alertas_vencimientos

# ===== IMPORT CORREGIDO PARA REPORTES =====
try:
    # Intentar importar el módulo de reportes corregido primero
    from reportes_corregido import mostrar_reportes
    REPORTES_MODULE = "corregido"
except ImportError:
    try:
        # Si no existe, intentar el módulo original
        from reportes import mostrar_reportes
        REPORTES_MODULE = "original"
    except ImportError:
        # Si ninguno funciona, usar función de respaldo
        REPORTES_MODULE = "respaldo"
        
        def mostrar_reportes(registros_df, *args, **kwargs):
            """Función de respaldo para reportes cuando no se puede importar el módulo"""
            st.error("❌ ERROR CRÍTICO: Módulo de reportes no disponible")
            
            st.markdown("### 🔧 Diagnóstico del Problema")
            st.info("""
            **Problema identificado**: El módulo `reportes.py` no se puede importar correctamente.
            
            **Causas posibles**:
            1. Archivo `reportes.py` no existe en el directorio
            2. Errores de sintaxis en `reportes.py`
            3. Dependencias faltantes en `reportes.py`
            4. Problemas de compatibilidad con otros módulos
            """)
            
            st.markdown("### 💡 Soluciones")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### 🚀 Solución Rápida")
                st.code("""
# 1. Descargar reportes_corregido.py del artifact
# 2. Guardar en el mismo directorio que app1.py
# 3. Reiniciar: streamlit run app1.py
                """)
            
            with col2:
                st.markdown("#### 🔍 Verificar Estado")
                st.code("""
# Verificar archivos en directorio:
import os
print(os.listdir('.'))

# Verificar imports:
try:
    import reportes
    print("reportes.py OK")
except Exception as e:
    print(f"Error: {e}")
                """)
            
            # Mostrar datos básicos si están disponibles
            if registros_df is not None and not registros_df.empty:
                st.markdown("### 📊 Datos Disponibles (Vista Básica)")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Total Registros", len(registros_df))
                
                with col2:
                    if 'Porcentaje Avance' in registros_df.columns:
                        avance_promedio = registros_df['Porcentaje Avance'].mean()
                        st.metric("Avance Promedio", f"{avance_promedio:.1f}%")
                    else:
                        st.metric("Avance Promedio", "N/A")
                
                with col3:
                    if 'Estado' in registros_df.columns:
                        completados = len(registros_df[registros_df['Estado'] == 'Completado'])
                        st.metric("Completados", completados)
                    else:
                        st.metric("Completados", "N/A")
                
                # Mostrar tabla básica
                st.markdown("#### 📋 Vista de Datos (Primeros 10 registros)")
                st.dataframe(registros_df.head(10))
                
                # Opción de descarga
                csv_data = registros_df.to_csv(index=False)
                st.download_button(
                    label="📥 Descargar todos los datos (CSV)",
                    data=csv_data,
                    file_name=f"registros_backup_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                    mime="text/csv"
                )
            else:
                st.warning("⚠️ No hay datos disponibles para mostrar")

from trimestral import mostrar_seguimiento_trimestral

# ===== IMPORTS DE UTILIDADES EXISTENTES =====
from data_utils import (
    cargar_datos, calcular_porcentaje_avance, verificar_estado_fechas,
    procesar_metas
)
from validaciones_utils import validar_reglas_negocio
from fecha_utils import (
    actualizar_plazo_analisis, actualizar_plazo_cronograma, 
    actualizar_plazo_oficio_cierre
)
from auth_utils import mostrar_login, mostrar_estado_autenticacion
from config import setup_page, load_css
from sheets_utils import test_connection, get_sheets_manager


def mostrar_configuracion_sheets():
    """Muestra la configuración y estado de Google Sheets"""
    with st.sidebar.expander("⚙️ Configuración Google Sheets", expanded=False):
        st.markdown("### Estado de Conexión")
        
        if st.button("Probar Conexión", help="Verifica la conexión con Google Sheets"):
            with st.spinner("Probando conexión..."):
                test_connection()
        
        try:
            manager = get_sheets_manager()
            hojas = manager.listar_hojas()
            st.markdown("**Hojas disponibles:**")
            for hoja in hojas:
                st.markdown(f"- {hoja}")
        except:
            st.warning("No se pudo obtener la lista de hojas")
        
        st.markdown("---")
        st.markdown("**¿Necesitas configurar Google Sheets?**")
        st.info("Los datos se guardan de forma segura en Google Sheets con autenticación OAuth2")


def mostrar_informacion_sistema():
    """Muestra información del sistema fragmentado CON DIAGNÓSTICO DE REPORTES"""
    with st.sidebar:
        st.markdown("---")
        st.markdown("### ℹ️ Sistema Fragmentado")
        
        # Estado de módulos
        modulos_estado = {
            "Dashboard": "✅",
            "Editor": "✅", 
            "Alertas": "✅",
            "Trimestral": "✅",
            "Reportes": "✅" if REPORTES_MODULE != "respaldo" else "❌"
        }
        
        st.success(f"""
        **Sistema Optimizado**
        - Dashboard: {modulos_estado["Dashboard"]}
        - Editor: {modulos_estado["Editor"]} 
        - Alertas: {modulos_estado["Alertas"]}
        - Reportes: {modulos_estado["Reportes"]} ({REPORTES_MODULE})
        - Trimestral: {modulos_estado["Trimestral"]}
        
        📊 **Reducción:** 3000+ → 200 líneas
        """)
        
        # Alerta específica para reportes
        if REPORTES_MODULE == "respaldo":
            st.error("""
            🚨 **PROBLEMA DE REPORTES DETECTADO**
            
            Módulo de reportes no disponible.
            Usando función de respaldo.
            """)
            
            if st.button("🔧 Ver Solución", key="fix_reportes"):
                st.info("""
                **SOLUCIÓN RÁPIDA:**
                1. Descargar `reportes_corregido.py`
                2. Colocar en el directorio del proyecto
                3. Reiniciar Streamlit
                """)
        elif REPORTES_MODULE == "original":
            st.warning("""
            ⚠️ **USANDO MÓDULO ORIGINAL**
            
            Se recomienda actualizar a 
            `reportes_corregido.py` para 
            mejor compatibilidad.
            """)


def crear_filtros_globales(registros_df):
    """Crea filtros globales para el sistema (solo para Dashboard)"""
    st.markdown("### 🔍 Filtros del Dashboard")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        entidades_unicas = sorted(registros_df['Entidad'].unique())
        entidad_seleccionada = st.selectbox(
            "Filtrar por Entidad:",
            ['Todas'] + entidades_unicas,
            key="filtro_entidad_global"
        )
    
    with col2:
        funcionarios_unicos = sorted([
            f for f in registros_df['Funcionario'].dropna().unique() 
            if f and str(f).strip()
        ])
        funcionario_seleccionado = st.selectbox(
            "Filtrar por Funcionario:",
            ['Todos'] + funcionarios_unicos,
            key="filtro_funcionario_global"
        )
    
    with col3:
        niveles_unicos = sorted(registros_df['Nivel Información '].unique())
        nivel_seleccionado = st.selectbox(
            "Filtrar por Nivel:",
            ['Todos'] + niveles_unicos,
            key="filtro_nivel_global"
        )
    
    return entidad_seleccionada, funcionario_seleccionado, nivel_seleccionado


def aplicar_filtros_dashboard(registros_df, entidad_seleccionada, funcionario_seleccionado, nivel_seleccionado):
    """Aplica filtros para el dashboard"""
    df_filtrado = registros_df.copy()
    
    if entidad_seleccionada != 'Todas':
        df_filtrado = df_filtrado[df_filtrado['Entidad'] == entidad_seleccionada]
    
    if funcionario_seleccionado != 'Todos':
        df_filtrado = df_filtrado[df_filtrado['Funcionario'] == funcionario_seleccionado]
    
    if nivel_seleccionado != 'Todos':
        df_filtrado = df_filtrado[df_filtrado['Nivel Información '] == nivel_seleccionado]
    
    return df_filtrado


def crear_filtros_reportes():
    """Crea filtros específicos para reportes (preservados del original)"""
    st.markdown("### 🔍 Filtros de Reportes")
    
    # Crear las columnas de filtros como en el original
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        entidades_reporte = ['Todas'] + sorted(st.session_state.get('registros_df', pd.DataFrame())['Entidad'].unique() if 'registros_df' in st.session_state and not st.session_state['registros_df'].empty else [])
        entidad_reporte = st.selectbox("Entidad:", entidades_reporte, key="entidad_reporte")
        
        tipos_dato = ['Todos', 'Nuevo', 'Actualizar']
        tipo_dato_reporte = st.selectbox("Tipo de Dato:", tipos_dato, key="tipo_dato_reporte")
    
    with col2:
        acuerdo_opciones = ['Todos', 'Si', 'No']
        acuerdo_filtro = st.selectbox("Acuerdo de compromiso:", acuerdo_opciones, key="acuerdo_filtro")
        
        analisis_opciones = ['Todos', 'Con fecha', 'Sin fecha']
        analisis_filtro = st.selectbox("Análisis y cronograma:", analisis_opciones, key="analisis_filtro")
    
    with col3:
        estandares_opciones = ['Todos', 'Con fecha', 'Sin fecha']
        estandares_filtro = st.selectbox("Estándares:", estandares_opciones, key="estandares_filtro")
        
        publicacion_opciones = ['Todos', 'Con fecha', 'Sin fecha']
        publicacion_filtro = st.selectbox("Publicación:", publicacion_opciones, key="publicacion_filtro")
    
    with col4:
        finalizado_opciones = ['Todos', 'Finalizados', 'No finalizados']
        finalizado_filtro = st.selectbox("Estado:", finalizado_opciones, key="finalizado_filtro")
        
        mes_opciones = ['Todos'] + [f"{i:02d}" for i in range(1, 13)]
        mes_filtro = st.selectbox("Mes:", mes_opciones, key="mes_filtro")
    
    return (entidad_reporte, tipo_dato_reporte, acuerdo_filtro, 
            analisis_filtro, estandares_filtro, publicacion_filtro, 
            finalizado_filtro, mes_filtro)


def main():
    """Función principal CORREGIDA con mejor manejo de errores"""
    try:
        # ===== CONFIGURACIÓN INICIAL =====
        setup_page()
        load_css()
        
        # ===== SISTEMA DE AUTENTICACIÓN =====
        mostrar_login()
        mostrar_estado_autenticacion() 
        mostrar_configuracion_sheets()
        mostrar_informacion_sistema()  # Ahora incluye diagnóstico de reportes
        
        # ===== TÍTULO PRINCIPAL =====
        st.markdown('<div class="title">📊 Tablero de Control - Ideca</div>', unsafe_allow_html=True)
        
        # ===== DIAGNÓSTICO INICIAL DE SISTEMA =====
        if REPORTES_MODULE == "respaldo":
            st.warning("⚠️ Sistema funcionando con módulo de reportes de respaldo")
        elif REPORTES_MODULE == "original":
            st.info("ℹ️ Sistema usando módulo de reportes original")
        else:
            st.success("✅ Sistema completamente funcional con módulo de reportes corregido")
        
        # ===== CARGA Y PROCESAMIENTO DE DATOS (CON MEJOR MANEJO DE ERRORES) =====
        with st.spinner("📊 Cargando y procesando datos..."):
            try:
                registros_df, meta_df = cargar_datos()
                
                # VERIFICACIÓN CRÍTICA DE DATOS
                if registros_df is None:
                    st.error("❌ ERROR CRÍTICO: No se pudieron cargar los registros")
                    st.stop()
                
                if registros_df.empty:
                    st.error("❌ ERROR: Los registros están vacíos")
                    st.info("🔧 Verificar conexión con Google Sheets y contenido de la hoja 'Registros'")
                    st.stop()
                
                st.success(f"✅ {len(registros_df)} registros cargados correctamente")
                
                # Aplicar validaciones automáticas
                registros_df = validar_reglas_negocio(registros_df)
                registros_df = actualizar_plazo_analisis(registros_df)
                registros_df = actualizar_plazo_cronograma(registros_df)  
                registros_df = actualizar_plazo_oficio_cierre(registros_df)
                
                # Procesar metas
                metas_nuevas_df, metas_actualizar_df = procesar_metas(meta_df)
                
                # Agregar columnas calculadas
                registros_df['Porcentaje Avance'] = registros_df.apply(calcular_porcentaje_avance, axis=1)
                registros_df['Estado Fechas'] = registros_df.apply(verificar_estado_fechas, axis=1)
                
                st.success("✅ Datos procesados y validados correctamente")
                
            except Exception as e:
                st.error(f"❌ Error crítico en carga de datos: {str(e)}")
                st.info("🔧 Verificar configuración de Google Sheets y credenciales")
                st.stop()
        
        # Guardar en session_state para los filtros
        st.session_state['registros_df'] = registros_df
        
        # ===== NAVEGACIÓN POR PESTAÑAS =====
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📊 Dashboard", 
            "✏️ Edición de Registros", 
            "📅 Seguimiento Trimestral",
            "🚨 Alertas de Vencimientos", 
            "📋 Reportes"
        ])
        
        # ===== TAB 1: DASHBOARD =====
        with tab1:
            try:
                entidad_seleccionada, funcionario_seleccionado, nivel_seleccionado = crear_filtros_globales(registros_df)
                df_filtrado = aplicar_filtros_dashboard(
                    registros_df, entidad_seleccionada, funcionario_seleccionado, nivel_seleccionado
                )
                mostrar_dashboard(
                    df_filtrado, metas_nuevas_df, metas_actualizar_df, 
                    registros_df, entidad_seleccionada, funcionario_seleccionado, nivel_seleccionado
                )
            except Exception as e:
                st.error(f"❌ Error en Dashboard: {str(e)}")
                st.info("🔧 Verificar módulo dashboard.py")
        
        # ===== TAB 2: EDITOR =====
        with tab2:
            try:
                registros_df = mostrar_edicion_registros_con_autenticacion(registros_df)
            except Exception as e:
                st.error(f"❌ Error en Editor: {str(e)}")
                st.info("🔧 Verificar módulo editor.py")
        
        # ===== TAB 3: TRIMESTRAL =====
        with tab3:
            try:
                mostrar_seguimiento_trimestral(registros_df, meta_df)
            except Exception as e:
                st.error(f"❌ Error en Seguimiento Trimestral: {str(e)}")
                st.info("🔧 Verificar módulo trimestral.py")
        
        # ===== TAB 4: ALERTAS =====
        with tab4:
            try:
                mostrar_alertas_vencimientos(registros_df)
            except Exception as e:
                st.error(f"❌ Error en Alertas: {str(e)}")
                st.info("🔧 Verificar módulo alertas.py")
        
        # ===== TAB 5: REPORTES (CORREGIDO) =====
        with tab5:
            try:
                # Filtros específicos de reportes
                filtros_reportes = crear_filtros_reportes()
                
                # Verificación adicional antes de llamar a reportes
                if registros_df is None or registros_df.empty:
                    st.error("❌ No hay datos disponibles para generar reportes")
                    st.info("🔧 Verificar carga de datos en las pestañas anteriores")
                else:
                    # Delegar al módulo reportes (con manejo de errores mejorado)
                    mostrar_reportes(registros_df, *filtros_reportes)
                    
            except Exception as e:
                st.error(f"❌ Error en Reportes: {str(e)}")
                st.markdown("### 🔧 Diagnóstico del Error en Reportes")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.info(f"""
                    **Estado del Módulo de Reportes:**
                    - Módulo cargado: {REPORTES_MODULE}
                    - Error específico: {str(e)}
                    - Datos disponibles: {not registros_df.empty if registros_df is not None else False}
                    """)
                
                with col2:
                    st.info("""
                    **Acciones Recomendadas:**
                    1. Descargar reportes_corregido.py
                    2. Colocar en directorio del proyecto  
                    3. Reiniciar aplicación
                    4. Verificar imports en app1.py
                    """)
        
        # ===== FOOTER INFORMATIVO =====
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.info(f"📊 **{len(registros_df)} registros** en el sistema")
        
        with col2:
            avance_general = registros_df['Porcentaje Avance'].mean()
            st.info(f"📈 **{avance_general:.1f}% avance** promedio general")
        
        with col3:
            st.info(f"🕐 **Actualizado:** {datetime.now().strftime('%H:%M:%S')}")
    
    except Exception as e:
        st.error("❌ Error crítico en la aplicación")
        
        # Información detallada del error
        with st.expander("🔍 Detalles del Error"):
            st.error(f"Error: {str(e)}")
            
            import traceback
            st.code(traceback.format_exc())
        
        # Diagnóstico del sistema
        st.markdown("### 🔧 Información de Diagnóstico")
        col1, col2 = st.columns(2)
        
        with col1:
            st.info(f"""
            **Sistema:**
            - Versión: Fragmentada v2.0 (Corregida)
            - Módulos: 5 independientes
            - Estado Reportes: {REPORTES_MODULE}
            """)
        
        with col2:
            modulos_cargados = {
                'dashboard': 'dashboard' in globals(),
                'editor': 'editor' in globals(),
                'alertas': 'alertas' in globals(),
                'reportes': 'mostrar_reportes' in globals(),
                'trimestral': 'trimestral' in globals()
            }
            
            st.info(f"""
            **Módulos Cargados:**
            - Dashboard: {'✅' if modulos_cargados['dashboard'] else '❌'}
            - Editor: {'✅' if modulos_cargados['editor'] else '❌'}
            - Alertas: {'✅' if modulos_cargados['alertas'] else '❌'}
            - Reportes: {'✅' if modulos_cargados['reportes'] else '❌'}
            - Trimestral: {'✅' if modulos_cargados['trimestral'] else '❌'}
            """)


if __name__ == "__main__":
    main()
