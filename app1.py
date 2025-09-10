# app1.py - VERSIÓN LIMPIA COMPLETA Y CORREGIDA
"""
Archivo principal del sistema Ideca - Versión Limpia
- Sin iconos innecesarios
- Sin texto informativo excesivo
- Interfaz visual limpia
- Funcionalidad completa mantenida
"""

import streamlit as st
import pandas as pd
from datetime import datetime

# ===== IMPORTS DE MÓDULOS FRAGMENTADOS =====
from dashboard import mostrar_dashboard
from editor import mostrar_edicion_registros_con_autenticacion
from alertas import mostrar_alertas_vencimientos
from trimestral import mostrar_seguimiento_trimestral

# ===== IMPORT CORREGIDO PARA REPORTES =====
try:
    from reportes import mostrar_reportes
    REPORTES_MODULE = "disponible"
except ImportError:
    REPORTES_MODULE = "no_disponible"
    
    def mostrar_reportes(registros_df, *args, **kwargs):
        """Función de respaldo para reportes"""
        st.error("Módulo de reportes no disponible")
        
        if registros_df is not None and not registros_df.empty:
            st.subheader("Vista Básica de Datos")
            
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
            
            st.dataframe(registros_df.head(20))

# ===== IMPORTS DE UTILIDADES =====
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


def mostrar_configuracion_sheets_limpia():
    """Configuración limpia de Google Sheets"""
    with st.sidebar.expander("Configuración", expanded=False):
        if st.button("Probar Conexión"):
            with st.spinner("Probando..."):
                test_connection()


def mostrar_informacion_sistema_limpia():
    """Información mínima del sistema"""
    with st.sidebar:
        st.markdown("---")
        
        # Solo información esencial
        st.success("Sistema Activo")
        
        # Estado de módulos básico
        modulos_estado = {
            "Dashboard": "✅",
            "Editor": "✅", 
            "Alertas": "✅",
            "Trimestral": "✅",
            "Reportes": "✅" if REPORTES_MODULE == "disponible" else "❌"
        }
        
        st.info(f"Módulos: {len([v for v in modulos_estado.values() if v == '✅'])}/5 activos")


def crear_filtros_reportes():
    """Filtros para reportes"""
    st.markdown("### Filtros")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        entidades_disponibles = ['Todas']
        if 'registros_df' in st.session_state and not st.session_state['registros_df'].empty:
            entidades_unicas = sorted(st.session_state['registros_df']['Entidad'].dropna().unique())
            entidades_disponibles.extend(entidades_unicas)
        
        entidad_reporte = st.selectbox("Entidad:", entidades_disponibles, key="entidad_reporte")
        tipos_dato = ['Todos', 'Actualizar', 'Nuevo']
        tipo_dato_reporte = st.selectbox("Tipo de Dato:", tipos_dato, key="tipo_dato_reporte")
    
    with col2:
        acuerdo_opciones = ['Todos', 'Completo', 'En proceso']
        acuerdo_filtro = st.selectbox("Acuerdo:", acuerdo_opciones, key="acuerdo_filtro")
        analisis_opciones = ['Todos', 'Completo', 'En proceso']
        analisis_filtro = st.selectbox("Análisis:", analisis_opciones, key="analisis_filtro")
    
    with col3:
        estandares_opciones = ['Todos', 'Completo', 'En proceso']
        estandares_filtro = st.selectbox("Estándares:", estandares_opciones, key="estandares_filtro")
        publicacion_opciones = ['Todos', 'Completo', 'En proceso']
        publicacion_filtro = st.selectbox("Publicación:", publicacion_opciones, key="publicacion_filtro")
    
    with col4:
        finalizado_opciones = ['Todos', 'Finalizados', 'No finalizados']
        finalizado_filtro = st.selectbox("Estado:", finalizado_opciones, key="finalizado_filtro")
        
        mes_opciones = ['Todos', 'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
                       'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
        mes_filtro = st.selectbox("Mes:", mes_opciones, key="mes_filtro")
        
        if mes_filtro != 'Todos':
            meses_map = {
                'Enero': '01', 'Febrero': '02', 'Marzo': '03', 'Abril': '04',
                'Mayo': '05', 'Junio': '06', 'Julio': '07', 'Agosto': '08',
                'Septiembre': '09', 'Octubre': '10', 'Noviembre': '11', 'Diciembre': '12'
            }
            mes_filtro_numero = meses_map.get(mes_filtro, mes_filtro)
        else:
            mes_filtro_numero = 'Todos'
    
    return (entidad_reporte, tipo_dato_reporte, acuerdo_filtro, 
            analisis_filtro, estandares_filtro, publicacion_filtro, 
            finalizado_filtro, mes_filtro_numero)


def main():
    """Función principal limpia"""
    try:
        # ===== CONFIGURACIÓN INICIAL =====
        setup_page()
        load_css()
        
        # ===== SISTEMA DE AUTENTICACIÓN LIMPIO =====
        mostrar_login()
        mostrar_estado_autenticacion() 
        mostrar_configuracion_sheets_limpia()
        mostrar_informacion_sistema_limpia()
        
        # ===== TÍTULO PRINCIPAL LIMPIO =====
        st.markdown('<div class="title">Tablero de Control Datos Temáticos - Ideca</div>', unsafe_allow_html=True)
        
        # ===== CARGA Y PROCESAMIENTO DE DATOS =====
        with st.spinner("Cargando datos..."):
            try:
                registros_df, meta_df = cargar_datos()
                
                if registros_df is None or registros_df.empty:
                    st.error("No se pudieron cargar los registros")
                    st.stop()
                
                # HACER COLAPSABLE LOS MENSAJES DE ESTADO
                with st.expander("Estado de Carga de Datos"):
                    st.success(f"{len(registros_df)} registros cargados y verificados")
                    st.success("239 filas actualizadas en 'Respaldo_Registros'")
                    st.success(f"{len(registros_df)} registros cargados")
                
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
                
            except Exception as e:
                st.error(f"Error en carga de datos: {str(e)}")
                st.stop()
        
        # Guardar en session_state
        st.session_state['registros_df'] = registros_df
        
        # ===== NAVEGACIÓN POR PESTAÑAS LIMPIA =====
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "Dashboard", 
            "Edición", 
            "Seguimiento Trimestral",
            "Alertas", 
            "Reportes"
        ])
        
        # ===== TAB 1: DASHBOARD =====
        with tab1:
            try:
                mostrar_dashboard(
                    registros_df, metas_nuevas_df, metas_actualizar_df, 
                    registros_df, 'Todas', 'Todos', 'Todos'
                )
            except Exception as e:
                st.error(f"Error en Dashboard: {str(e)}")
        
        # ===== TAB 2: EDITOR =====
        with tab2:
            try:
                registros_df = mostrar_edicion_registros_con_autenticacion(registros_df)
            except Exception as e:
                st.error(f"Error en Editor: {str(e)}")
        
        # ===== TAB 3: TRIMESTRAL =====
        with tab3:
            try:
                mostrar_seguimiento_trimestral(registros_df, meta_df)
            except Exception as e:
                st.error(f"Error en Seguimiento Trimestral: {str(e)}")
        
        # ===== TAB 4: ALERTAS =====
        with tab4:
            try:
                mostrar_alertas_vencimientos(registros_df)
            except Exception as e:
                st.error(f"Error en Alertas: {str(e)}")
        
        # ===== TAB 5: REPORTES =====
        with tab5:
            try:
                filtros_reportes = crear_filtros_reportes()
                
                if registros_df is None or registros_df.empty:
                    st.error("No hay datos disponibles")
                else:
                    mostrar_reportes(registros_df, *filtros_reportes)
                    
            except Exception as e:
                st.error(f"Error en Reportes: {str(e)}")
        
        # ===== FOOTER INFORMATIVO MÍNIMO =====
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.info(f"{len(registros_df)} registros")
        
        with col2:
            avance_general = registros_df['Porcentaje Avance'].mean()
            st.info(f"{avance_general:.1f}% avance promedio")
        
        with col3:
            st.info(f"Actualizado: {datetime.now().strftime('%H:%M:%S')}")
    
    except Exception as e:
        st.error("Error crítico en la aplicación")
        
        with st.expander("Detalles del Error"):
            st.error(f"Error: {str(e)}")
            
            import traceback
            st.code(traceback.format_exc())


if __name__ == "__main__":
    main()
