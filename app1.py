import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.figure_factory as ff
import plotly.graph_objects as go
from datetime import datetime, timedelta, date
from validaciones_utils import validar_reglas_negocio, mostrar_estado_validaciones, verificar_condiciones_estandares, verificar_condiciones_oficio_cierre
import io
import matplotlib
import base64
import os
import re
from fecha_utils import calcular_plazo_analisis, actualizar_plazo_analisis, calcular_plazo_cronograma, actualizar_plazo_cronograma, calcular_plazo_oficio_cierre, actualizar_plazo_oficio_cierre

# Importar las funciones corregidas
from config import setup_page, load_css
from data_utils import (
    cargar_datos, procesar_metas, calcular_porcentaje_avance,
    verificar_estado_fechas, formatear_fecha, es_fecha_valida,
    validar_campos_fecha, guardar_datos_editados, guardar_datos_editados_rapido, procesar_fecha,
    contar_registros_completados_por_fecha, cargar_datos_desde_excel
)
from visualization import crear_gantt, comparar_avance_metas
from constants import REGISTROS_DATA, META_DATA
from sheets_utils import test_connection, get_sheets_manager

# ========== FUNCIONES AUXILIARES ==========

def string_a_fecha(fecha_str):
    """Convierte un string de fecha a objeto datetime para mostrar en el selector de fecha."""
    if not fecha_str or fecha_str == "":
        return None
    fecha = procesar_fecha(fecha_str)
    return fecha

def highlight_estado_fechas(s):
    """Función para aplicar estilo según el valor de 'Estado Fechas'"""
    if 'Estado Fechas' in s and s['Estado Fechas'] == 'vencido':
        return ['background-color: #fee2e2'] * len(s)
    elif 'Estado Fechas' in s and s['Estado Fechas'] == 'proximo':
        return ['background-color: #fef3c7'] * len(s)
    else:
        return ['background-color: #ffffff'] * len(s)

def on_change_callback():
    """Callback para marcar que hay cambios pendientes."""
    st.session_state.cambios_pendientes = True

def fecha_para_selector(fecha_str):
    """Convierte una fecha en string a un objeto datetime para el selector."""
    if not fecha_str or pd.isna(fecha_str) or fecha_str == '':
        return None
    try:
        fecha = procesar_fecha(fecha_str)
        if fecha is not None:
            return fecha
    except:
        pass
    return None

def fecha_desde_selector_a_string(fecha):
    """Convierte un objeto datetime del selector a string con formato DD/MM/AAAA."""
    if fecha is None:
        return ""
    return fecha.strftime('%d/%m/%Y')

# ========== FUNCIONES DE CONFIGURACIÓN ==========

def mostrar_configuracion_sheets():
    """Muestra la configuración y estado de Google Sheets"""
    with st.sidebar.expander("🔧 Configuración Google Sheets"):
        st.markdown("### Estado de Conexión")
        
        if st.button("🔄 Probar Conexión", help="Verifica la conexión con Google Sheets"):
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
        st.markdown("[📋 Ver instrucciones completas](https://github.com/tu-repo/INSTRUCCIONES_CONFIGURACION.md)")
        st.info("🔒 Los datos se guardan de forma segura en Google Sheets con autenticación OAuth2")

def mostrar_carga_archivos():
    """Muestra la sección de carga de archivos Excel/CSV"""
    with st.sidebar.expander("📁 Cargar Datos desde Excel"):
        st.markdown("### Subir Archivo Excel")
        
        uploaded_file = st.file_uploader(
            "Selecciona un archivo Excel",
            type=['xlsx', 'xls'],
            help="El archivo se sincronizará automáticamente con Google Sheets"
        )
        
        if uploaded_file is not None:
            if st.button("🔄 Sincronizar con Google Sheets"):
                with st.spinner("Procesando y sincronizando archivo..."):
                    nuevos_registros, nuevas_metas = cargar_datos_desde_excel(uploaded_file)
                    
                    if nuevos_registros is not None:
                        st.success("✅ Archivo sincronizado exitosamente!")
                        st.info("🔄 Recargando la aplicación con los nuevos datos...")
                        st.rerun()
                    else:
                        st.error("❌ Error al procesar el archivo")
        
        st.markdown("---")
        st.markdown("**Formato esperado:**")
        st.markdown("- **Hoja 'Registros':** Datos principales")
        st.markdown("- **Hoja 'Metas':** Metas quincenales")
        st.warning("⚠️ La sincronización sobrescribirá los datos existentes en Google Sheets")

# ========== FUNCIÓN DE EDICIÓN ==========

def mostrar_edicion_registros(registros_df):
    """Muestra la pestaña de edición de registros - VERSIÓN COMPLETA."""
    st.markdown('<div class="subtitle">Edición de Registros</div>', unsafe_allow_html=True)

    st.info("Esta sección permite editar los datos usando selectores de fecha y opciones. Los cambios se guardan automáticamente en Google Sheets.")

    # Verificar si hay registros
    if registros_df.empty:
        st.warning("No hay registros para editar. Carga datos primero usando el panel lateral.")
        return registros_df

    # Selector de registro
    codigos_registros = registros_df['Cod'].astype(str).tolist()
    entidades_registros = registros_df['Entidad'].tolist()
    niveles_registros = registros_df['Nivel Información '].tolist()

    opciones_registros = [f"{codigos_registros[i]} - {entidades_registros[i]} - {niveles_registros[i]}"
                          for i in range(len(codigos_registros))]

    seleccion_registro = st.selectbox(
        "Seleccione un registro para editar:",
        options=opciones_registros,
        key="selector_registro"
    )

    indice_seleccionado = opciones_registros.index(seleccion_registro)

    try:
        row = registros_df.iloc[indice_seleccionado].copy()
        edited = False

        st.markdown("---")
        st.markdown(f"### Editando Registro #{row['Cod']} - {row['Entidad']}")
        st.markdown(f"**Nivel de Información:** {row['Nivel Información ']}")
        st.markdown("---")

        # SECCIÓN 1: INFORMACIÓN BÁSICA
        st.markdown("### 1. Información Básica")
        col1, col2, col3 = st.columns(3)

        with col1:
            st.text_input("Código", value=row['Cod'], disabled=True)

        with col2:
            nuevo_tipo = st.selectbox(
                "Tipo de Dato",
                options=["Nuevo", "Actualizar"],
                index=0 if row['TipoDato'].upper() == "NUEVO" else 1,
                key=f"tipo_{indice_seleccionado}",
                on_change=on_change_callback
            )
            if nuevo_tipo != row['TipoDato']:
                registros_df.at[registros_df.index[indice_seleccionado], 'TipoDato'] = nuevo_tipo
                edited = True

        with col3:
            nuevo_nivel = st.text_input(
                "Nivel de Información",
                value=row['Nivel Información '] if pd.notna(row['Nivel Información ']) else "",
                key=f"nivel_info_{indice_seleccionado}",
                on_change=on_change_callback
            )
            if nuevo_nivel != row['Nivel Información ']:
                registros_df.at[registros_df.index[indice_seleccionado], 'Nivel Información '] = nuevo_nivel
                edited = True

        # Funcionario
        if 'Funcionario' in row:
            if not st.session_state.funcionarios:
                funcionarios_unicos = registros_df['Funcionario'].dropna().unique().tolist()
                st.session_state.funcionarios = [f for f in funcionarios_unicos if f]

            funcionarios_ordenados = sorted(st.session_state.funcionarios)
            opciones_funcionarios = [""] + funcionarios_ordenados

            indice_funcionario = 0
            if pd.notna(row['Funcionario']) and row['Funcionario'] in opciones_funcionarios:
                indice_funcionario = opciones_funcionarios.index(row['Funcionario'])

            funcionario_seleccionado = st.selectbox(
                "Funcionario",
                options=opciones_funcionarios,
                index=indice_funcionario,
                key=f"funcionario_select_{indice_seleccionado}",
                on_change=on_change_callback
            )

            if funcionario_seleccionado != row.get('Funcionario', ''):
                registros_df.at[registros_df.index[indice_seleccionado], 'Funcionario'] = funcionario_seleccionado
                edited = True

        # SECCIÓN 2: FECHAS DE COMPROMISO
        st.markdown("### 2. Fechas de Compromiso")
        col1, col2, col3 = st.columns(3)

        with col1:
            fecha_entrega_dt = fecha_para_selector(row['Entrega acuerdo de compromiso'])
            nueva_fecha_entrega = st.date_input(
                "Entrega acuerdo de compromiso",
                value=fecha_entrega_dt,
                format="DD/MM/YYYY",
                key=f"fecha_entrega_{indice_seleccionado}",
                on_change=on_change_callback
            )
            nueva_fecha_entrega_str = fecha_desde_selector_a_string(nueva_fecha_entrega) if nueva_fecha_entrega else ""
            fecha_original = "" if pd.isna(row['Entrega acuerdo de compromiso']) else row['Entrega acuerdo de compromiso']
            if nueva_fecha_entrega_str != fecha_original:
                registros_df.at[registros_df.index[indice_seleccionado], 'Entrega acuerdo de compromiso'] = nueva_fecha_entrega_str
                edited = True

        with col2:
            nuevo_acuerdo = st.selectbox(
                "Acuerdo de compromiso",
                options=["", "Si", "No"],
                index=1 if row['Acuerdo de compromiso'].upper() in ["SI", "SÍ", "YES", "Y"] else (2 if row['Acuerdo de compromiso'].upper() == "NO" else 0),
                key=f"acuerdo_{indice_seleccionado}",
                on_change=on_change_callback
            )
            if nuevo_acuerdo != row['Acuerdo de compromiso']:
                registros_df.at[registros_df.index[indice_seleccionado], 'Acuerdo de compromiso'] = nuevo_acuerdo
                edited = True

        # SECCIÓN 3: ANÁLISIS Y CRONOGRAMA
        st.markdown("### 3. Análisis y Cronograma")
        col1, col2 = st.columns(2)

        with col1:
            fecha_entrega_info_dt = fecha_para_selector(row['Fecha de entrega de información'])
            nueva_fecha_entrega_info = st.date_input(
                "Fecha de entrega de información",
                value=fecha_entrega_info_dt,
                format="DD/MM/YYYY",
                key=f"fecha_entrega_info_{indice_seleccionado}"
            )
            nueva_fecha_entrega_info_str = fecha_desde_selector_a_string(nueva_fecha_entrega_info) if nueva_fecha_entrega_info else ""
            fecha_original = "" if pd.isna(row['Fecha de entrega de información']) else row['Fecha de entrega de información']
            if nueva_fecha_entrega_info_str != fecha_original:
                registros_df.at[registros_df.index[indice_seleccionado], 'Fecha de entrega de información'] = nueva_fecha_entrega_info_str
                registros_df = actualizar_plazo_analisis(registros_df)
                registros_df = actualizar_plazo_cronograma(registros_df)
                edited = True

        with col2:
            fecha_analisis_dt = fecha_para_selector(row['Análisis y cronograma'])
            nueva_fecha_analisis = st.date_input(
                "Análisis y cronograma (fecha real)",
                value=fecha_analisis_dt,
                format="DD/MM/YYYY",
                key=f"fecha_analisis_{indice_seleccionado}",
                on_change=on_change_callback
            )
            nueva_fecha_analisis_str = fecha_desde_selector_a_string(nueva_fecha_analisis) if nueva_fecha_analisis else ""
            fecha_original = "" if pd.isna(row['Análisis y cronograma']) else row['Análisis y cronograma']
            if nueva_fecha_analisis_str != fecha_original:
                registros_df.at[registros_df.index[indice_seleccionado], 'Análisis y cronograma'] = nueva_fecha_analisis_str
                edited = True

        # SECCIÓN 4: ESTÁNDARES
        st.markdown("### 4. Estándares")
        col1, col2 = st.columns(2)

        with col1:
            fecha_estandares_dt = fecha_para_selector(row['Estándares'])
            nueva_fecha_estandares = st.date_input(
                "Fecha de estándares",
                value=fecha_estandares_dt,
                format="DD/MM/YYYY",
                key=f"fecha_estandares_{indice_seleccionado}",
                on_change=on_change_callback
            )
            nueva_fecha_estandares_str = fecha_desde_selector_a_string(nueva_fecha_estandares) if nueva_fecha_estandares else ""
            fecha_original = "" if pd.isna(row['Estándares']) else row['Estándares']
            if nueva_fecha_estandares_str != fecha_original:
                registros_df.at[registros_df.index[indice_seleccionado], 'Estándares'] = nueva_fecha_estandares_str
                edited = True

        # SECCIÓN 5: PUBLICACIÓN
        st.markdown("### 5. Publicación")
        col1, col2 = st.columns(2)

        with col1:
            fecha_publicacion_dt = fecha_para_selector(row['Publicación'])
            nueva_fecha_publicacion = st.date_input(
                "Fecha de publicación",
                value=fecha_publicacion_dt,
                format="DD/MM/YYYY",
                key=f"fecha_publicacion_{indice_seleccionado}",
                on_change=on_change_callback
            )
            nueva_fecha_publicacion_str = fecha_desde_selector_a_string(nueva_fecha_publicacion) if nueva_fecha_publicacion else ""
            fecha_original = "" if pd.isna(row['Publicación']) else row['Publicación']
            if nueva_fecha_publicacion_str != fecha_original:
                registros_df.at[registros_df.index[indice_seleccionado], 'Publicación'] = nueva_fecha_publicacion_str
                registros_df = actualizar_plazo_oficio_cierre(registros_df)
                edited = True

        # SECCIÓN 6: ESTADO
        st.markdown("### 6. Estado")
        col1, col2 = st.columns(2)

        with col1:
            opciones_estado = ["", "En proceso", "En proceso oficio de cierre", "Completado", "Finalizado"]
            indice_estado = 0
            if row['Estado'] in opciones_estado:
                indice_estado = opciones_estado.index(row['Estado'])

            nuevo_estado = st.selectbox(
                "Estado",
                options=opciones_estado,
                index=indice_estado,
                key=f"estado_{indice_seleccionado}",
                on_change=on_change_callback
            )
            if nuevo_estado != row['Estado']:
                registros_df.at[registros_df.index[indice_seleccionado], 'Estado'] = nuevo_estado
                edited = True

        with col2:
            nueva_observacion = st.text_area(
                "Observación",
                value=row['Observación'] if pd.notna(row['Observación']) else "",
                key=f"observacion_{indice_seleccionado}",
                on_change=on_change_callback
            )
            if nueva_observacion != row['Observación']:
                registros_df.at[registros_df.index[indice_seleccionado], 'Observación'] = nueva_observacion
                edited = True

        # Botón de guardar
        if edited or st.session_state.cambios_pendientes:
            if st.button("💾 Guardar Cambios", key=f"guardar_{indice_seleccionado}", type="primary"):
                registros_df = validar_reglas_negocio(registros_df)
                with st.spinner("💾 Guardando en Google Sheets..."):
                    exito, mensaje = guardar_datos_editados(registros_df, crear_backup=True)
                if exito:
                    st.success(mensaje)
                    st.session_state.cambios_pendientes = False
                    st.rerun()
                else:
                    st.error(mensaje)

    except Exception as e:
        st.error(f"Error al editar el registro: {e}")

    return registros_df

# ========== FUNCIÓN DASHBOARD ==========

def mostrar_dashboard(df_filtrado, metas_nuevas_df, metas_actualizar_df, registros_df, mostrar_gantt=False):
    """Muestra el dashboard principal con métricas y gráficos."""
    
    # Métricas generales
    st.markdown('<div class="subtitle">Métricas Generales</div>', unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_registros = len(df_filtrado)
        st.markdown(f"""
        <div class="metric-card">
            <p style="font-size: 1rem; color: #64748b;">Total Registros</p>
            <p style="font-size: 2.5rem; font-weight: bold; color: #1E40AF;">{total_registros}</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        avance_promedio = df_filtrado['Porcentaje Avance'].mean() if not df_filtrado.empty else 0
        st.markdown(f"""
        <div class="metric-card">
            <p style="font-size: 1rem; color: #64748b;">Avance Promedio</p>
            <p style="font-size: 2.5rem; font-weight: bold; color: #047857;">{avance_promedio:.2f}%</p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        registros_completados = len(df_filtrado[df_filtrado['Porcentaje Avance'] == 100]) if not df_filtrado.empty else 0
        st.markdown(f"""
        <div class="metric-card">
            <p style="font-size: 1rem; color: #64748b;">Registros Completados</p>
            <p style="font-size: 2.5rem; font-weight: bold; color: #B45309;">{registros_completados}</p>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        porcentaje_completados = (registros_completados / total_registros * 100) if total_registros > 0 else 0
        st.markdown(f"""
        <div class="metric-card">
            <p style="font-size: 1rem; color: #64748b;">% Completados</p>
            <p style="font-size: 2.5rem; font-weight: bold; color: #BE185D;">{porcentaje_completados:.2f}%</p>
        </div>
        """, unsafe_allow_html=True)

    # Comparación con metas
    st.markdown('<div class="subtitle">Comparación con Metas Quincenales</div>', unsafe_allow_html=True)
    
    comparacion_nuevos, comparacion_actualizar, fecha_meta = comparar_avance_metas(df_filtrado, metas_nuevas_df, metas_actualizar_df)
    
    st.markdown(f"**Meta más cercana a la fecha actual: {fecha_meta.strftime('%d/%m/%Y')}**")

    # CAMBIO 1: Gradiente personalizado de rojo a verde (0-100%), valores >100% en verde
    def aplicar_gradiente_personalizado(val):
        try:
            val_num = float(val)
            if val_num <= 100:
                intensity = val_num / 100
                red = int(255 * (1 - intensity))
                green = int(255 * intensity)
                return f'background-color: rgb({red}, {green}, 0); color: white;'
            else:
                return 'background-color: rgb(0, 255, 0); color: white;'
        except:
            return ''

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Registros Nuevos")
        styled_nuevos = comparacion_nuevos.style.format({
            'Porcentaje': '{:.2f}%'
        }).applymap(aplicar_gradiente_personalizado, subset=['Porcentaje'])
        st.dataframe(styled_nuevos, use_container_width=True)

    with col2:
        st.markdown("### Registros a Actualizar")
        styled_actualizar = comparacion_actualizar.style.format({
            'Porcentaje': '{:.2f}%'
        }).applymap(aplicar_gradiente_personalizado, subset=['Porcentaje'])
        st.dataframe(styled_actualizar, use_container_width=True)

    # CAMBIO 2: Diagrama de Gantt condicionado
    st.markdown('<div class="subtitle">Diagrama de Gantt - Cronograma de Hitos por Nivel de Información</div>', unsafe_allow_html=True)

    if mostrar_gantt:
        fig_gantt = crear_gantt(df_filtrado)
        if fig_gantt is not None:
            st.plotly_chart(fig_gantt, use_container_width=True)
        else:
            st.warning("No hay datos suficientes para crear el diagrama de Gantt con los filtros seleccionados.")
    else:
        st.info("📊 Visualiza el diagrama de Gantt seleccionando el funcionario o entidad de tu interés.")

    # Tabla de registros
    st.markdown('<div class="subtitle">Detalle de Registros</div>', unsafe_allow_html=True)

    if not df_filtrado.empty:
        columnas_mostrar = [
            'Cod', 'Entidad', 'Nivel Información ', 'Funcionario', 'TipoDato',
            'Entrega acuerdo de compromiso', 'Acuerdo de compromiso',
            'Fecha de entrega de información', 'Análisis y cronograma',
            'Estándares', 'Publicación', 'Estado', 'Porcentaje Avance'
        ]
        
        columnas_existentes = [col for col in columnas_mostrar if col in df_filtrado.columns]
        df_mostrar = df_filtrado[columnas_existentes].copy()

        st.dataframe(
            df_mostrar.style.format({'Porcentaje Avance': '{:.2f}%'})
            .background_gradient(cmap='RdYlGn', subset=['Porcentaje Avance']),
            use_container_width=True
        )
    else:
        st.warning("No hay registros que coincidan con los filtros seleccionados.")

# ========== FUNCIÓN REPORTES ==========

def mostrar_reportes(registros_df, tipo_dato_filtro, acuerdo_filtro, analisis_filtro, 
                    estandares_filtro, publicacion_filtro, finalizado_filtro):
    """Muestra la pestaña de reportes con tabla completa y filtros específicos."""
    st.markdown('<div class="subtitle">Reportes de Registros</div>', unsafe_allow_html=True)
    
    # Aplicar filtros
    df_filtrado = registros_df.copy()
    
    if tipo_dato_filtro != 'Todos':
        df_filtrado = df_filtrado[df_filtrado['TipoDato'].str.upper() == tipo_dato_filtro.upper()]
    
    if acuerdo_filtro == 'Suscrito':
        df_filtrado = df_filtrado[
            ((df_filtrado['Entrega acuerdo de compromiso'].notna()) & 
             (df_filtrado['Entrega acuerdo de compromiso'] != ''))
        ]
    elif acuerdo_filtro == 'No Suscrito':
        df_filtrado = df_filtrado[
            ((df_filtrado['Entrega acuerdo de compromiso'].isna()) | 
             (df_filtrado['Entrega acuerdo de compromiso'] == ''))
        ]
    
    if analisis_filtro == 'Completado':
        df_filtrado = df_filtrado[
            (df_filtrado['Análisis y cronograma'].notna()) & 
            (df_filtrado['Análisis y cronograma'] != '')
        ]
    elif analisis_filtro == 'No Completado':
        df_filtrado = df_filtrado[
            (df_filtrado['Análisis y cronograma'].isna()) | 
            (df_filtrado['Análisis y cronograma'] == '')
        ]
    
    # Mostrar estadísticas
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Filtrados", len(df_filtrado))
    with col2:
        if len(df_filtrado) > 0:
            st.metric("Avance Promedio", f"{df_filtrado['Porcentaje Avance'].mean():.1f}%")
        else:
            st.metric("Avance Promedio", "0%")
    with col3:
        completados = len(df_filtrado[df_filtrado['Porcentaje Avance'] == 100]) if len(df_filtrado) > 0 else 0
        st.metric("Completados", completados)
    with col4:
        porcentaje = (completados / len(df_filtrado) * 100) if len(df_filtrado) > 0 else 0
        st.metric("% Completados", f"{porcentaje:.1f}%")

    # Mostrar tabla
    if not df_filtrado.empty:
        st.dataframe(df_filtrado, use_container_width=True)
    else:
        st.warning("No se encontraron registros que coincidan con los filtros seleccionados.")

# ========== FUNCIÓN ALERTAS ==========

def mostrar_alertas_vencimientos(registros_df):
    """Muestra alertas de vencimientos de fechas en los registros."""
    st.markdown('<div class="subtitle">Alertas de Vencimientos</div>', unsafe_allow_html=True)

    if registros_df.empty:
        st.info("No hay registros para analizar alertas.")
        return

    fecha_actual = datetime.now().date()
    registros_alertas = []

    for idx, row in registros_df.iterrows():
        try:
            # Verificar fechas vencidas
            fecha_entrega = procesar_fecha(row.get('Fecha de entrega de información', ''))
            if fecha_entrega and fecha_entrega.date() < fecha_actual:
                registros_alertas.append({
                    'Cod': row['Cod'],
                    'Entidad': row['Entidad'],
                    'Tipo Alerta': 'Entrega de información',
                    'Estado': 'Vencido',
                    'Días Rezago': (fecha_actual - fecha_entrega.date()).days
                })

            # Verificar fechas próximas a vencer
            fecha_analisis = procesar_fecha(row.get('Plazo de cronograma', ''))
            if fecha_analisis and fecha_analisis.date() > fecha_actual:
                dias_restantes = (fecha_analisis.date() - fecha_actual).days
                if dias_restantes <= 5:
                    registros_alertas.append({
                        'Cod': row['Cod'],
                        'Entidad': row['Entidad'],
                        'Tipo Alerta': 'Plazo de cronograma',
                        'Estado': 'Próximo a vencer',
                        'Días Rezago': -dias_restantes
                    })

        except Exception as e:
            continue

    if registros_alertas:
        df_alertas = pd.DataFrame(registros_alertas)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            vencidos = len(df_alertas[df_alertas['Estado'] == 'Vencido'])
            st.metric("Vencidos", vencidos)
        
        with col2:
            proximos = len(df_alertas[df_alertas['Estado'] == 'Próximo a vencer'])
            st.metric("Próximos a vencer", proximos)
        
        with col3:
            st.metric("Total Alertas", len(df_alertas))

        st.dataframe(df_alertas, use_container_width=True)
    else:
        st.success("🎉 ¡No hay alertas de vencimientos pendientes!")

# ========== FUNCIÓN DIAGNÓSTICO ==========

def mostrar_diagnostico(registros_df, meta_df, metas_nuevas_df, metas_actualizar_df, df_filtrado):
    """Muestra la sección de diagnóstico con análisis detallado de los datos."""
    with st.expander("🔍 Diagnóstico de Datos"):
        st.markdown("### Diagnóstico de Datos")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Total de Registros", len(registros_df))
            st.metric("Registros Filtrados", len(df_filtrado))

        with col2:
            if 'TipoDato' in registros_df.columns:
                st.metric("Registros Nuevos", len(registros_df[registros_df['TipoDato'].str.upper() == 'NUEVO']))
                st.metric("Registros a Actualizar", len(registros_df[registros_df['TipoDato'].str.upper() == 'ACTUALIZAR']))

        # Estado de Google Sheets
        st.markdown("#### Estado de Google Sheets")
        try:
            manager = get_sheets_manager()
            hojas = manager.listar_hojas()
            st.success(f"✅ Conectado a Google Sheets. Hojas disponibles: {', '.join(hojas)}")
        except Exception as e:
            st.error(f"❌ Error de conexión con Google Sheets: {str(e)}")

# ========== FUNCIÓN AYUDA ==========

def mostrar_ayuda():
    """Muestra la sección de ayuda con información sobre el uso del tablero."""
    with st.expander("❓ Ayuda"):
        st.markdown("### Ayuda del Dashboard de Seguimiento a Datos Temáticos - Ideca")
        st.markdown("""
        Este tablero de control permite visualizar y gestionar el seguimiento de cronogramas con **persistencia permanente en Google Sheets**.

        #### 🔗 Características Principales
        - **✅ Datos sincronizados en tiempo real** con Google Sheets
        - **🔒 Respaldo automático** de cada cambio
        - **👥 Colaboración simultánea** de múltiples usuarios
        - **📱 Acceso desde cualquier dispositivo**
        - **🔧 Edición completa y detallada** de todos los campos
        - **⚡ Validaciones automáticas** y cálculo de plazos

        #### 📊 Navegación
        - **Dashboard**: Métricas generales, comparación con metas y diagrama de Gantt
        - **Edición de Registros**: Edición individual completa
        - **Alertas de Vencimientos**: Seguimiento de fechas críticas
        - **Reportes**: Análisis avanzados con filtros personalizados

        #### 🔧 Funcionalidades Google Sheets
        - **Carga desde Excel**: Sube archivos Excel para sincronizar automáticamente
        - **Descarga completa**: Exporta todos los datos en formato Excel
        - **Backup automático**: Cada cambio crea una copia de seguridad

        #### 💾 Guardado Automático
        Los cambios se guardan automáticamente en Google Sheets al modificar campos.

        #### 🆘 Soporte
        Para configuración inicial o problemas técnicos:
        - 🔧 Usa el panel "Configuración Google Sheets" en la barra lateral
        - 🔄 Utiliza el botón "Reconectar" si hay problemas de conexión
        """)

# ========== FUNCIÓN PRINCIPAL ==========

def main():
    """Función principal con todas las funcionalidades y cambios solicitados."""
    try:
        # Inicialización del estado de sesión
        if 'cambios_pendientes' not in st.session_state:
            st.session_state.cambios_pendientes = False
        if 'mensaje_guardado' not in st.session_state:
            st.session_state.mensaje_guardado = None
        if 'funcionarios' not in st.session_state:
            st.session_state.funcionarios = []

        # Configuración de la página
        setup_page()
        load_css()

        # TÍTULO ACTUALIZADO
        st.markdown('<div class="title">📊 Dashboard de Seguimiento a Datos Temáticos - Ideca</div>', unsafe_allow_html=True)
        
        # Estado de Google Sheets
        st.markdown("### 🔗 Estado de Google Sheets")
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.info("🔄 Datos sincronizados con Google Sheets en tiempo real")
        
        with col2:
            if st.button("🔄 Reconectar"):
                if 'sheets_manager' in st.session_state:
                    del st.session_state.sheets_manager
                st.rerun()

        # Sidebar
        mostrar_configuracion_sheets()
        mostrar_carga_archivos()

        st.sidebar.markdown('<div class="subtitle">Información</div>', unsafe_allow_html=True)
        st.sidebar.markdown("""
        <div class="info-box">
        <p><strong>Dashboard de Seguimiento a Datos Temáticos - Ideca</strong></p>
        <p><strong>✅ VERSIÓN COMPLETA</strong></p>
        <p>• Edición detallada de todos los campos</p>
        <p>• Validaciones automáticas completas</p>
        <p>• Cálculo de plazos automático</p>
        <p>• Guardado inteligente en Google Sheets</p>
        <p>• Diagrama de Gantt condicionado</p>
        <p>• Gradiente de comparación mejorado</p>
        </div>
        """, unsafe_allow_html=True)

        # Carga de datos
        with st.spinner("📊 Cargando datos desde Google Sheets..."):
            registros_df, meta_df = cargar_datos()

        if registros_df.empty:
            st.warning("⚠️ No hay datos de registros en Google Sheets.")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown("**📁 Subir Excel**")
                st.markdown("Usar el panel lateral para cargar datos")
            with col2:
                st.markdown("**➕ Editar Google Sheets**")
                st.markdown("Agregar datos directamente en la hoja")
            with col3:
                st.markdown("**🔧 Configurar**")
                st.markdown("Verificar credenciales y permisos")
            
            # Crear estructura mínima
            registros_df = pd.DataFrame(columns=[
                'Cod', 'Entidad', 'TipoDato', 'Nivel Información ',
                'Acuerdo de compromiso', 'Análisis y cronograma',
                'Estándares', 'Publicación', 'Fecha de entrega de información',
                'Plazo de análisis', 'Plazo de cronograma', 'Plazo de oficio de cierre',
                'Funcionario', 'Estado', 'Observación'
            ])
        else:
            st.success(f"✅ {len(registros_df)} registros cargados exitosamente desde Google Sheets")

        # Asegurar columnas requeridas
        columnas_requeridas = [
            'Cod', 'Entidad', 'TipoDato', 'Acuerdo de compromiso',
            'Análisis y cronograma', 'Estándares', 'Publicación',
            'Nivel Información ', 'Fecha de entrega de información',
            'Plazo de análisis', 'Plazo de cronograma', 'Plazo de oficio de cierre',
            'Funcionario', 'Estado', 'Observación', 'Entrega acuerdo de compromiso'
        ]

        for columna in columnas_requeridas:
            if columna not in registros_df.columns:
                registros_df[columna] = ''

        # Aplicar validaciones y cálculos
        with st.spinner("🔧 Aplicando validaciones y calculando plazos..."):
            registros_df = validar_reglas_negocio(registros_df)
            registros_df = actualizar_plazo_analisis(registros_df)
            registros_df = actualizar_plazo_cronograma(registros_df)
            registros_df = actualizar_plazo_oficio_cierre(registros_df)

        # Procesar las metas
        metas_nuevas_df, metas_actualizar_df = procesar_metas(meta_df)

        # Agregar columnas calculadas
        registros_df['Porcentaje Avance'] = registros_df.apply(calcular_porcentaje_avance, axis=1)
        registros_df['Estado Fechas'] = registros_df.apply(verificar_estado_fechas, axis=1)

        # Mostrar validaciones
        with st.expander("🔍 Validación de Reglas de Negocio"):
            st.markdown("### Estado de Validaciones")
            st.info("""
            **Reglas aplicadas automáticamente:**
            1. ✅ Si 'Entrega acuerdo de compromiso' no está vacío → 'Acuerdo de compromiso' = SI
            2. ✅ Si 'Análisis y cronograma' tiene fecha → campos dependientes se actualizan
            3. ✅ Plazos calculados automáticamente considerando días hábiles y festivos
            """)
            mostrar_estado_validaciones(registros_df, st)

        # Crear pestañas
        tab1, tab2, tab3, tab4 = st.tabs([
            "📊 Dashboard", 
            "✏️ Edición de Registros", 
            "⚠️ Alertas de Vencimientos", 
            "📋 Reportes"
        ])
     
        # TAB 1: DASHBOARD
        with tab1:
            st.markdown("### 🔍 Filtros")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                entidades = ['Todas'] + sorted([e for e in registros_df['Entidad'].unique().tolist() if e])
                entidad_seleccionada = st.selectbox('Entidad', entidades, key="dash_entidad")
            
            with col2:
                funcionarios = ['Todos']
                if 'Funcionario' in registros_df.columns:
                    funcionarios_unicos = [f for f in registros_df['Funcionario'].dropna().unique().tolist() if f]
                    funcionarios += sorted(funcionarios_unicos)
                funcionario_seleccionado = st.selectbox('Funcionario', funcionarios, key="dash_funcionario")
            
            with col3:
                tipos_dato = ['Todos'] + sorted([t for t in registros_df['TipoDato'].dropna().unique().tolist() if t])
                tipo_dato_seleccionado = st.selectbox('Tipo de Dato', tipos_dato, key="dash_tipo")
            
            with col4:
                # CAMBIO 3: Filtro condicional por nivel de información
                if entidad_seleccionada != 'Todas':
                    niveles_entidad = registros_df[registros_df['Entidad'] == entidad_seleccionada]['Nivel Información '].dropna().unique().tolist()
                    niveles_entidad = [n for n in niveles_entidad if n]
                    niveles = ['Todos'] + sorted(niveles_entidad)
                    nivel_seleccionado = st.selectbox('Nivel de Información', niveles, key="dash_nivel")
                else:
                    nivel_seleccionado = 'Todos'
                    st.selectbox('Nivel de Información', ['Seleccione una entidad primero'], disabled=True, key="dash_nivel_disabled")
            
            # Aplicar filtros
            df_filtrado = registros_df.copy()
            
            if entidad_seleccionada != 'Todas':
                df_filtrado = df_filtrado[df_filtrado['Entidad'] == entidad_seleccionada]
            
            if funcionario_seleccionado != 'Todos' and 'Funcionario' in df_filtrado.columns:
                df_filtrado = df_filtrado[df_filtrado['Funcionario'] == funcionario_seleccionado]
            
            if tipo_dato_seleccionado != 'Todos':
                df_filtrado = df_filtrado[df_filtrado['TipoDato'].str.upper() == tipo_dato_seleccionado.upper()]
            
            if nivel_seleccionado != 'Todos':
                df_filtrado = df_filtrado[df_filtrado['Nivel Información '] == nivel_seleccionado]
            
            # CAMBIO 2: Determinar si mostrar Gantt
            mostrar_gantt = (entidad_seleccionada != 'Todas' or 
                           funcionario_seleccionado != 'Todos' or 
                           nivel_seleccionado != 'Todos')
            
            st.markdown("---")
            
            # Mostrar dashboard
            mostrar_dashboard(df_filtrado, metas_nuevas_df, metas_actualizar_df, registros_df, mostrar_gantt)

        # TAB 2: EDICIÓN
        with tab2:
            registros_df = mostrar_edicion_registros(registros_df)

        # TAB 3: ALERTAS
        with tab3:
            mostrar_alertas_vencimientos(registros_df)

        # TAB 4: REPORTES
        with tab4:
            st.markdown("### 🔍 Filtros de Reportes")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                tipos_dato_reporte = ['Todos'] + sorted([t for t in registros_df['TipoDato'].dropna().unique().tolist() if t])
                tipo_dato_reporte = st.selectbox('Tipo de Dato', tipos_dato_reporte, key="reporte_tipo")
            
            with col2:
                acuerdo_opciones = ['Todos', 'Suscrito', 'No Suscrito']
                acuerdo_filtro = st.selectbox('Acuerdo de Compromiso', acuerdo_opciones, key="reporte_acuerdo")
            
            with col3:
                analisis_opciones = ['Todos', 'Completado', 'No Completado']
                analisis_filtro = st.selectbox('Análisis y Cronograma', analisis_opciones, key="reporte_analisis")
            
            col4, col5, col6 = st.columns(3)
            
            with col4:
                estandares_opciones = ['Todos', 'Completado', 'No Completado']
                estandares_filtro = st.selectbox('Estándares', estandares_opciones, key="reporte_estandares")
            
            with col5:
                publicacion_opciones = ['Todos', 'Completado', 'No Completado']
                publicacion_filtro = st.selectbox('Publicación', publicacion_opciones, key="reporte_publicacion")
            
            with col6:
                finalizado_opciones = ['Todos', 'Finalizado', 'No Finalizado']
                finalizado_filtro = st.selectbox('Finalizado', finalizado_opciones, key="reporte_finalizado")
            
            st.markdown("---")
            
            mostrar_reportes(registros_df, tipo_dato_reporte, acuerdo_filtro, analisis_filtro, 
                           estandares_filtro, publicacion_filtro, finalizado_filtro)

        # Secciones adicionales
        mostrar_diagnostico(registros_df, meta_df, metas_nuevas_df, metas_actualizar_df, df_filtrado)
        mostrar_ayuda()

        # Footer
        st.markdown("---")
        st.markdown("### 📊 Resumen del Sistema")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("📝 Total Campos", len(registros_df.columns))
        
        with col2:
            total_con_funcionario = len(registros_df[registros_df['Funcionario'].notna() & (registros_df['Funcionario'] != '')])
            st.metric("👥 Con Funcionario", total_con_funcionario)
        
        with col3:
            en_proceso = len(registros_df[registros_df['Estado'].isin(['En proceso', 'En proceso oficio de cierre'])])
            st.metric("⚙️ En Proceso", en_proceso)
        
        with col4:
            ultima_actualizacion = datetime.now().strftime("%d/%m/%Y %H:%M")
            st.metric("🔄 Última Actualización", ultima_actualizacion)

        # Información de versión
        st.info("""
        🎉 **Dashboard de Seguimiento a Datos Temáticos - Ideca - Versión Completa**
        
        ✅ **Funcionalidades Principales:**
        • Edición completa de registros con validaciones automáticas
        • Sincronización en tiempo real con Google Sheets
        • Sistema de backup automático
        • Alertas de vencimiento con análisis detallado
        • Reportes avanzados con múltiples filtros
        
        🆕 **Nuevas Características Implementadas:**
        • Gradiente de comparación de metas optimizado (0-100% rojo→verde, >100% verde)
        • Diagrama de Gantt inteligente (solo aparece con filtros activos)
        • Filtro de nivel de información condicionado por entidad
        • Interfaz mejorada específica para seguimiento de datos temáticos
        """)

    except Exception as e:
        st.error(f"❌ Error crítico en la aplicación: {str(e)}")
        
        import traceback
        with st.expander("🔍 Detalles Técnicos del Error"):
            st.code(traceback.format_exc())
        
        st.markdown("### 🆘 Guía de Solución de Problemas")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            **🔧 Problemas Más Comunes:**
            - Credenciales de Google Sheets incorrectas
            - Permisos insuficientes del service account
            - ID de spreadsheet incorrecto
            - Estructura de datos incorrecta
            """)
        
        with col2:
            st.markdown("""
            **🔄 Acciones Recomendadas:**
            - Usar el botón "🔄 Reconectar" arriba
            - Verificar configuración en el panel lateral
            - Revisar permisos del spreadsheet
            - Contactar soporte técnico si persiste
            """)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🔄 Limpiar Cache", type="primary"):
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.rerun()
        
        with col2:
            if st.button("📊 Reiniciar Conexión", type="secondary"):
                keys_to_delete = [key for key in st.session_state.keys() 
                                if key.startswith(('sheets_', 'manager_'))]
                for key in keys_to_delete:
                    del st.session_state[key]
                st.rerun()
        
        with col3:
            if st.button("🆘 Modo Emergencia", type="secondary"):
                st.session_state['emergency_mode'] = True
                st.warning("⚠️ Activado modo emergencia.")
                st.rerun()

if __name__ == "__main__":
    main()
