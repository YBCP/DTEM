import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.figure_factory as ff
import plotly.graph_objects as go
from datetime import datetime, timedelta, date
from validaciones_utils import validar_reglas_negocio, mostrar_estado_validaciones, verificar_condiciones_estandares, verificar_condiciones_oficio_cierre
import io
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

# Función para convertir fecha string a datetime
def string_a_fecha(fecha_str):
    """Convierte un string de fecha a objeto datetime para mostrar en el selector de fecha."""
    if not fecha_str or fecha_str == "":
        return None
    fecha = procesar_fecha(fecha_str)
    return fecha

# Función para colorear filas según estado de fechas - definida fuera de los bloques try
def highlight_estado_fechas(s):
    """Función para aplicar estilo según el valor de 'Estado Fechas'"""
    if 'Estado Fechas' in s and s['Estado Fechas'] == 'vencido':
        return ['background-color: #fee2e2'] * len(s)
    elif 'Estado Fechas' in s and s['Estado Fechas'] == 'proximo':
        return ['background-color: #fef3c7'] * len(s)
    else:
        return ['background-color: #ffffff'] * len(s)

def mostrar_configuracion_sheets():
    """Muestra la configuración y estado de Google Sheets"""
    with st.sidebar.expander("🔧 Configuración Google Sheets"):
        st.markdown("### Estado de Conexión")
        
        # Botón para probar conexión
        if st.button("🔄 Probar Conexión", help="Verifica la conexión con Google Sheets"):
            with st.spinner("Probando conexión..."):
                test_connection()
        
        # Mostrar hojas disponibles
        try:
            manager = get_sheets_manager()
            hojas = manager.listar_hojas()
            st.markdown("**Hojas disponibles:**")
            for hoja in hojas:
                st.markdown(f"- {hoja}")
        except:
            st.warning("No se pudo obtener la lista de hojas")
        
        # Link a configuración
        st.markdown("---")
        st.markdown("**¿Necesitas configurar Google Sheets?**")
        st.markdown("[📋 Ver instrucciones completas](https://github.com/tu-repo/INSTRUCCIONES_CONFIGURACION.md)")
        
        # Información de seguridad
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

def mostrar_dashboard(df_filtrado, metas_nuevas_df, metas_actualizar_df, registros_df):
    """Muestra el dashboard principal con métricas y gráficos."""
    # Mostrar métricas generales
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
        avance_promedio = df_filtrado['Porcentaje Avance'].mean()
        st.markdown(f"""
        <div class="metric-card">
            <p style="font-size: 1rem; color: #64748b;">Avance Promedio</p>
            <p style="font-size: 2.5rem; font-weight: bold; color: #047857;">{avance_promedio:.2f}%</p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        registros_completados = len(df_filtrado[df_filtrado['Porcentaje Avance'] == 100])
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

    # Calcular comparación con metas
    comparacion_nuevos, comparacion_actualizar, fecha_meta = comparar_avance_metas(df_filtrado, metas_nuevas_df,
                                                                                   metas_actualizar_df)

    # Mostrar fecha de la meta
    st.markdown(f"**Meta más cercana a la fecha actual: {fecha_meta.strftime('%d/%m/%Y')}**")

    # Mostrar comparación en dos columnas
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Registros Nuevos")
        st.dataframe(comparacion_nuevos.style.format({
            'Porcentaje': '{:.2f}%'
        }).background_gradient(cmap='RdYlGn', subset=['Porcentaje']))

        # Gráfico de barras para registros nuevos
        fig_nuevos = px.bar(
            comparacion_nuevos.reset_index(),
            x='index',
            y=['Completados', 'Meta'],
            barmode='group',
            labels={'index': 'Hito', 'value': 'Cantidad', 'variable': 'Tipo'},
            title='Comparación de Avance vs. Meta - Registros Nuevos',
            color_discrete_map={'Completados': '#4B5563', 'Meta': '#1E40AF'}
        )
        st.plotly_chart(fig_nuevos, use_container_width=True)

    with col2:
        st.markdown("### Registros a Actualizar")
        st.dataframe(comparacion_actualizar.style.format({
            'Porcentaje': '{:.2f}%'
        }).background_gradient(cmap='RdYlGn', subset=['Porcentaje']))

        # Gráfico de barras para registros a actualizar
        fig_actualizar = px.bar(
            comparacion_actualizar.reset_index(),
            x='index',
            y=['Completados', 'Meta'],
            barmode='group',
            labels={'index': 'Hito', 'value': 'Cantidad', 'variable': 'Tipo'},
            title='Comparación de Avance vs. Meta - Registros a Actualizar',
            color_discrete_map={'Completados': '#4B5563', 'Meta': '#047857'}
        )
        st.plotly_chart(fig_actualizar, use_container_width=True)

    # Diagrama de Gantt - Cronograma de Hitos por Nivel de Información
    st.markdown('<div class="subtitle">Diagrama de Gantt - Cronograma de Hitos por Nivel de Información</div>',
                unsafe_allow_html=True)

    # Crear el diagrama de Gantt
    fig_gantt = crear_gantt(df_filtrado)
    if fig_gantt is not None:
        st.plotly_chart(fig_gantt, use_container_width=True)
    else:
        st.warning("No hay datos suficientes para crear el diagrama de Gantt.")

    # Tabla de registros con porcentaje de avance
    st.markdown('<div class="subtitle">Detalle de Registros</div>', unsafe_allow_html=True)

    # Definir el nuevo orden exacto de las columnas según lo solicitado
    columnas_mostrar = [
        # Datos básicos
        'Cod', 'Entidad', 'Nivel Información ', 'Funcionario',  # Incluir Funcionario después de datos básicos
        # Columnas adicionales en el orden específico
        'Frecuencia actualizacion ', 'TipoDato',
        'Suscripción acuerdo de compromiso', 'Entrega acuerdo de compromiso',
        'Fecha de entrega de información', 'Plazo de análisis', 'Plazo de cronograma',
        'Análisis y cronograma',
        'Registro (completo)', 'ET (completo)', 'CO (completo)', 'DD (completo)', 'REC (completo)',
        'SERVICIO (completo)',
        'Estándares (fecha programada)', 'Estándares',
        'Fecha de publicación programada', 'Publicación',
        'Plazo de oficio de cierre', 'Fecha de oficio de cierre',
        'Estado', 'Observación', 'Porcentaje Avance'
    ]

    # Mostrar tabla con colores por estado de fechas
    try:
        # Verificar que todas las columnas existan en df_filtrado
        columnas_mostrar_existentes = [col for col in columnas_mostrar if col in df_filtrado.columns]
        df_mostrar = df_filtrado[columnas_mostrar_existentes].copy()

        # Aplicar formato a las fechas
        columnas_fecha = [
            'Suscripción acuerdo de compromiso', 'Entrega acuerdo de compromiso',
            'Fecha de entrega de información', 'Plazo de análisis', 'Plazo de cronograma',
            'Análisis y cronograma', 'Estándares (fecha programada)', 'Estándares',
            'Fecha de publicación programada', 'Publicación',
            'Plazo de oficio de cierre', 'Fecha de oficio de cierre'
        ]

        for col in columnas_fecha:
            if col in df_mostrar.columns:
                df_mostrar[col] = df_mostrar[col].apply(lambda x: formatear_fecha(x) if es_fecha_valida(x) else "")

        # Mostrar el dataframe con formato
        st.dataframe(
            df_mostrar
            .style.format({'Porcentaje Avance': '{:.2f}%'})
            .apply(highlight_estado_fechas, axis=1)
            .background_gradient(cmap='RdYlGn', subset=['Porcentaje Avance']),
            use_container_width=True
        )

        # SECCIÓN DE DESCARGA
        st.markdown("### Descargar Datos")

        col1, col2 = st.columns(2)

        with col1:
            # Botón para descargar los datos filtrados
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df_mostrar.to_excel(writer, sheet_name='Registros Filtrados', index=False)

            excel_data = output.getvalue()
            st.download_button(
                label="📊 Descargar datos filtrados (Excel)",
                data=excel_data,
                file_name="registros_filtrados.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                help="Descarga los datos filtrados en formato Excel"
            )

        with col2:
            # BOTÓN PARA DESCARGAR TODOS LOS REGISTROS (datos completos)
            output_completo = io.BytesIO()
            with pd.ExcelWriter(output_completo, engine='openpyxl') as writer:
                registros_df.to_excel(writer, sheet_name='Registros Completos', index=False)

                # Añadir hojas adicionales con categorías
                if 'TipoDato' in registros_df.columns:
                    # Hoja para registros nuevos
                    registros_nuevos = registros_df[registros_df['TipoDato'].str.upper() == 'NUEVO']
                    if not registros_nuevos.empty:
                        registros_nuevos.to_excel(writer, sheet_name='Registros Nuevos', index=False)

                    # Hoja para registros a actualizar
                    registros_actualizar = registros_df[registros_df['TipoDato'].str.upper() == 'ACTUALIZAR']
                    if not registros_actualizar.empty:
                        registros_actualizar.to_excel(writer, sheet_name='Registros a Actualizar', index=False)

            excel_data_completo = output_completo.getvalue()

            # Botón para descargar todos los registros
            st.download_button(
                label="📥 Descargar TODOS los registros (Excel)",
                data=excel_data_completo,
                file_name="todos_los_registros.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                help="Descarga todos los registros en formato Excel, sin filtros aplicados",
                use_container_width=True
            )

        # Añadir información sobre el contenido
        num_registros = len(registros_df)
        num_campos = len(registros_df.columns)
        st.info(
            f"El archivo de TODOS los registros incluirá {num_registros} registros con {num_campos} campos originales.")

    except Exception as e:
        st.error(f"Error al mostrar la tabla de registros: {e}")
        st.dataframe(df_filtrado[columnas_mostrar_existentes])

# Función de callback para manejar cambios
def on_change_callback():
    """Callback para marcar que hay cambios pendientes."""
    st.session_state.cambios_pendientes = True

# Función para convertir fecha para mostrar en selectores de fecha
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

# Función para formatear fecha desde el selector para guardar en DataFrame
def fecha_desde_selector_a_string(fecha):
    """Convierte un objeto datetime del selector a string con formato DD/MM/AAAA."""
    if fecha is None:
        return ""
    return fecha.strftime('%d/%m/%Y')

def mostrar_edicion_registros(registros_df):
    """Muestra la pestaña de edición de registros."""
    st.markdown('<div class="subtitle">Edición de Registros</div>', unsafe_allow_html=True)

    st.info(
        "Esta sección permite editar los datos usando selectores de fecha y opciones. Los cambios se guardan automáticamente en Google Sheets.")

    # Explicación adicional sobre las fechas y reglas de validación
    st.warning("""
    **Importante**: 
    - Para los campos de fecha, utilice el selector de calendario que aparece.
    - El campo "Plazo de análisis" se calcula automáticamente como 5 días hábiles después de la "Fecha de entrega de información", sin contar fines de semana ni festivos.
    - El campo "Plazo de cronograma" se calcula automáticamente como 3 días hábiles después del "Plazo de análisis", sin contar fines de semana ni festivos.
    - El campo "Plazo de oficio de cierre" se calcula automáticamente como 7 días hábiles después de la fecha real de "Publicación", sin contar fines de semana ni festivos.
    - Los datos se guardan automáticamente en Google Sheets con cada modificación.
    """)
    
    # Mostrar mensaje de guardado si existe
    if st.session_state.mensaje_guardado:
        if st.session_state.mensaje_guardado[0] == "success":
            st.success(st.session_state.mensaje_guardado[1])
        else:
            st.error(st.session_state.mensaje_guardado[1])
        # Limpiar mensaje después de mostrarlo
        st.session_state.mensaje_guardado = None

    st.markdown("### Edición Individual de Registros")

    # Selector de registro - mostrar lista completa de registros para seleccionar
    codigos_registros = registros_df['Cod'].astype(str).tolist()
    entidades_registros = registros_df['Entidad'].tolist()
    niveles_registros = registros_df['Nivel Información '].tolist()

    # Crear opciones para el selector combinando información
    opciones_registros = [f"{codigos_registros[i]} - {entidades_registros[i]} - {niveles_registros[i]}"
                          for i in range(len(codigos_registros))]

    # Agregar el selector de registro
    seleccion_registro = st.selectbox(
        "Seleccione un registro para editar:",
        options=opciones_registros,
        key="selector_registro"
    )

    # Obtener el índice del registro seleccionado
    indice_seleccionado = opciones_registros.index(seleccion_registro)

    # Mostrar el registro seleccionado para edición
    try:
        # Obtener el registro seleccionado
        row = registros_df.iloc[indice_seleccionado].copy()

        # Flag para detectar cambios
        edited = False

        # Contenedor para los datos de edición
        with st.container():
            st.markdown("---")
            # Título del registro
            st.markdown(f"### Editando Registro #{row['Cod']} - {row['Entidad']}")
            st.markdown(f"**Nivel de Información:** {row['Nivel Información ']}")
            st.markdown("---")

            # SECCIÓN 1: INFORMACIÓN BÁSICA
            st.markdown("### 1. Información Básica")
            col1, col2, col3 = st.columns(3)

            with col1:
                # Campos no editables
                st.text_input("Código", value=row['Cod'], disabled=True)

            with col2:
                # Tipo de Dato
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
                # Nivel de Información
                nuevo_nivel = st.text_input(
                    "Nivel de Información",
                    value=row['Nivel Información '] if pd.notna(row['Nivel Información ']) else "",
                    key=f"nivel_info_{indice_seleccionado}",
                    on_change=on_change_callback
                )
                if nuevo_nivel != row['Nivel Información ']:
                    registros_df.at[registros_df.index[indice_seleccionado], 'Nivel Información '] = nuevo_nivel
                    edited = True

            # Frecuencia de actualización (si existe)
            if 'Frecuencia actualizacion ' in row:
                col1, col2 = st.columns(2)
                with col1:
                    nueva_frecuencia = st.selectbox(
                        "Frecuencia de actualización",
                        options=["", "Diaria", "Semanal", "Mensual", "Trimestral", "Semestral", "Anual"],
                        index=["", "Diaria", "Semanal", "Mensual", "Trimestral", "Semestral", "Anual"].index(
                            row['Frecuencia actualizacion ']) if row['Frecuencia actualizacion '] in ["", "Diaria",
                                                                                                      "Semanal",
                                                                                                      "Mensual",
                                                                                                      "Trimestral",
                                                                                                      "Semestral",
                                                                                                      "Anual"] else 0,
                        key=f"frecuencia_{indice_seleccionado}",
                        on_change=on_change_callback
                    )
                    if nueva_frecuencia != row['Frecuencia actualizacion ']:
                        registros_df.at[
                            registros_df.index[indice_seleccionado], 'Frecuencia actualizacion '] = nueva_frecuencia
                        edited = True

                # Funcionario (si existe)
                if 'Funcionario' in row:
                    with col2:
                        # Inicializar la lista de funcionarios si es la primera vez
                        if not st.session_state.funcionarios:
                            # Obtener valores únicos de funcionarios que no sean NaN
                            funcionarios_unicos = registros_df['Funcionario'].dropna().unique().tolist()
                            st.session_state.funcionarios = [f for f in funcionarios_unicos if f]

                        # Crear un campo de texto para nuevo funcionario
                        nuevo_funcionario_input = st.text_input(
                            "Nuevo funcionario (dejar vacío si selecciona existente)",
                            key=f"nuevo_funcionario_{indice_seleccionado}"
                        )

                        # Si se introduce un nuevo funcionario, agregarlo a la lista
                        if nuevo_funcionario_input and nuevo_funcionario_input not in st.session_state.funcionarios:
                            st.session_state.funcionarios.append(nuevo_funcionario_input)

                        # Ordenar la lista de funcionarios alfabéticamente
                        funcionarios_ordenados = sorted(st.session_state.funcionarios)

                        # Crear opciones con una opción vacía al principio
                        opciones_funcionarios = [""] + funcionarios_ordenados

                        # Determinar el índice del funcionario actual
                        indice_funcionario = 0
                        if pd.notna(row['Funcionario']) and row['Funcionario'] in opciones_funcionarios:
                            indice_funcionario = opciones_funcionarios.index(row['Funcionario'])

                        # Crear el selectbox para elegir funcionario
                        funcionario_seleccionado = st.selectbox(
                            "Seleccionar funcionario",
                            options=opciones_funcionarios,
                            index=indice_funcionario,
                            key=f"funcionario_select_{indice_seleccionado}",
                            on_change=on_change_callback
                        )

                        # Determinar el valor final del funcionario
                        funcionario_final = nuevo_funcionario_input if nuevo_funcionario_input else funcionario_seleccionado

                        # Actualizar el DataFrame si el funcionario cambia
                        if funcionario_final != row.get('Funcionario', ''):
                            registros_df.at[
                                registros_df.index[indice_seleccionado], 'Funcionario'] = funcionario_final
                            edited = True

            # SECCIÓN 2: ACTA DE COMPROMISO
            st.markdown("### 2. Acta de Compromiso")

            # Suscripción acuerdo de compromiso
            col1, col2, col3 = st.columns(3)
            if 'Suscripción acuerdo de compromiso' in row:
                with col1:
                    fecha_suscripcion_dt = fecha_para_selector(row['Suscripción acuerdo de compromiso'])
                    nueva_fecha_suscripcion = st.date_input(
                        "Suscripción acuerdo de compromiso",
                        value=fecha_suscripcion_dt,
                        format="DD/MM/YYYY",
                        key=f"fecha_suscripcion_{indice_seleccionado}",
                        on_change=on_change_callback
                    )
                    nueva_fecha_suscripcion_str = fecha_desde_selector_a_string(
                        nueva_fecha_suscripcion) if nueva_fecha_suscripcion else ""

                    fecha_original = "" if pd.isna(row['Suscripción acuerdo de compromiso']) else row[
                        'Suscripción acuerdo de compromiso']
                    if nueva_fecha_suscripcion_str != fecha_original:
                        registros_df.at[registros_df.index[
                            indice_seleccionado], 'Suscripción acuerdo de compromiso'] = nueva_fecha_suscripcion_str
                        edited = True

            with col2:
                # Entrega acuerdo de compromiso
                fecha_entrega_dt = fecha_para_selector(row['Entrega acuerdo de compromiso'])
                nueva_fecha_entrega = st.date_input(
                    "Entrega acuerdo de compromiso",
                    value=fecha_entrega_dt,
                    format="DD/MM/YYYY",
                    key=f"fecha_entrega_{indice_seleccionado}",
                    on_change=on_change_callback
                )

                nueva_fecha_entrega_str = fecha_desde_selector_a_string(
                    nueva_fecha_entrega) if nueva_fecha_entrega else ""

                fecha_original = "" if pd.isna(row['Entrega acuerdo de compromiso']) else row[
                    'Entrega acuerdo de compromiso']

                if nueva_fecha_entrega_str != fecha_original:
                    registros_df.at[registros_df.index[
                        indice_seleccionado], 'Entrega acuerdo de compromiso'] = nueva_fecha_entrega_str
                    edited = True

            with col3:
                # Acuerdo de compromiso
                nuevo_acuerdo = st.selectbox(
                    "Acuerdo de compromiso",
                    options=["", "Si", "No"],
                    index=1 if row['Acuerdo de compromiso'].upper() in ["SI", "SÍ", "YES", "Y"] else (
                        2 if row['Acuerdo de compromiso'].upper() == "NO" else 0),
                    key=f"acuerdo_{indice_seleccionado}",
                    on_change=on_change_callback
                )
                if nuevo_acuerdo != row['Acuerdo de compromiso']:
                    registros_df.at[
                        registros_df.index[indice_seleccionado], 'Acuerdo de compromiso'] = nuevo_acuerdo
                    edited = True

            # SECCIÓN 3: ANÁLISIS Y CRONOGRAMA  
            st.markdown("### 3. Análisis y Cronograma")

            col1, col2 = st.columns(2)
            with col1:
                # Fecha de entrega de información
                fecha_entrega_info_dt = fecha_para_selector(row['Fecha de entrega de información'])
                nueva_fecha_entrega_info = st.date_input(
                    "Fecha de entrega de información",
                    value=fecha_entrega_info_dt,
                    format="DD/MM/YYYY",
                    key=f"fecha_entrega_info_{indice_seleccionado}"
                )

                nueva_fecha_entrega_info_str = fecha_desde_selector_a_string(
                    nueva_fecha_entrega_info) if nueva_fecha_entrega_info else ""

                fecha_original = "" if pd.isna(row['Fecha de entrega de información']) else row[
                    'Fecha de entrega de información']

                if nueva_fecha_entrega_info_str != fecha_original:
                    registros_df.at[registros_df.index[
                        indice_seleccionado], 'Fecha de entrega de información'] = nueva_fecha_entrega_info_str
                    edited = True

                    # Actualizar automáticamente todos los plazos
                    registros_df = actualizar_plazo_analisis(registros_df)
                    registros_df = actualizar_plazo_cronograma(registros_df)
                    
                    # Guardar cambios inmediatamente en Google Sheets
                    with st.spinner("💾 Actualizando plazos..."):
                        exito, mensaje = guardar_datos_editados_rapido(registros_df)
                    if exito:
                        st.success("✅ Fecha y plazos actualizados")
                        st.rerun()

            with col2:
                # Análisis y cronograma (fecha real)
                fecha_analisis_dt = fecha_para_selector(row['Análisis y cronograma'])
                nueva_fecha_analisis = st.date_input(
                    "Análisis y cronograma (fecha real)",
                    value=fecha_analisis_dt,
                    format="DD/MM/YYYY",
                    key=f"fecha_analisis_{indice_seleccionado}",
                    on_change=on_change_callback
                )

                nueva_fecha_analisis_str = fecha_desde_selector_a_string(
                    nueva_fecha_analisis) if nueva_fecha_analisis else ""

                fecha_original = "" if pd.isna(row['Análisis y cronograma']) else row['Análisis y cronograma']
                if nueva_fecha_analisis_str != fecha_original:
                    registros_df.at[
                        registros_df.index[indice_seleccionado], 'Análisis y cronograma'] = nueva_fecha_analisis_str
                    edited = True

            # SECCIÓN 4: ESTÁNDARES
            st.markdown("### 4. Estándares")
            col1, col2 = st.columns(2)

            with col1:
                # Fecha programada para estándares
                if 'Estándares (fecha programada)' in row:
                    fecha_estandares_prog_dt = fecha_para_selector(row['Estándares (fecha programada)'])
                    nueva_fecha_estandares_prog = st.date_input(
                        "Estándares (fecha programada)",
                        value=fecha_estandares_prog_dt,
                        format="DD/MM/YYYY",
                        key=f"fecha_estandares_prog_{indice_seleccionado}",
                        on_change=on_change_callback
                    )
                    nueva_fecha_estandares_prog_str = fecha_desde_selector_a_string(
                        nueva_fecha_estandares_prog) if nueva_fecha_estandares_prog else ""

                    fecha_original = "" if pd.isna(row['Estándares (fecha programada)']) else row[
                        'Estándares (fecha programada)']
                    if nueva_fecha_estandares_prog_str != fecha_original:
                        registros_df.at[registros_df.index[
                            indice_seleccionado], 'Estándares (fecha programada)'] = nueva_fecha_estandares_prog_str
                        edited = True

            with col2:
                # Fecha de estándares (real)
                fecha_estandares_dt = fecha_para_selector(row['Estándares'])
                nueva_fecha_estandares = st.date_input(
                    "Fecha de estándares (real)",
                    value=fecha_estandares_dt,
                    format="DD/MM/YYYY",
                    key=f"fecha_estandares_{indice_seleccionado}",
                    on_change=on_change_callback
                )

                nueva_fecha_estandares_str = fecha_desde_selector_a_string(
                    nueva_fecha_estandares) if nueva_fecha_estandares else ""

                fecha_original = "" if pd.isna(row['Estándares']) else row['Estándares']

                if nueva_fecha_estandares_str and nueva_fecha_estandares_str != fecha_original:
                    registros_df.at[
                        registros_df.index[indice_seleccionado], 'Estándares'] = nueva_fecha_estandares_str
                    edited = True

                    # Aplicar reglas automáticas
                    registros_df = validar_reglas_negocio(registros_df)
                    
                    # Guardar en Google Sheets
                    with st.spinner("💾 Guardando cambios..."):
                        exito, mensaje = guardar_datos_editados_rapido(registros_df)
                    if exito:
                        st.success("✅ Estándares actualizados")
                        st.rerun()

            # SECCIÓN 5: PUBLICACIÓN
            st.markdown("### 5. Publicación")
            col1, col2 = st.columns(2)

            with col1:
                # Fecha programada para publicación
                if 'Fecha de publicación programada' in row:
                    fecha_publicacion_prog_dt = fecha_para_selector(row['Fecha de publicación programada'])
                    nueva_fecha_publicacion_prog = st.date_input(
                        "Fecha de publicación programada",
                        value=fecha_publicacion_prog_dt,
                        format="DD/MM/YYYY",
                        key=f"fecha_publicacion_prog_{indice_seleccionado}",
                        on_change=on_change_callback
                    )
                    nueva_fecha_publicacion_prog_str = fecha_desde_selector_a_string(
                        nueva_fecha_publicacion_prog) if nueva_fecha_publicacion_prog else ""

                    fecha_original = "" if pd.isna(row['Fecha de publicación programada']) else row[
                        'Fecha de publicación programada']
                    if nueva_fecha_publicacion_prog_str != fecha_original:
                        registros_df.at[registros_df.index[
                            indice_seleccionado], 'Fecha de publicación programada'] = nueva_fecha_publicacion_prog_str
                        edited = True

            with col2:
                # Fecha de publicación (real)
                fecha_publicacion_dt = fecha_para_selector(row['Publicación'])
                nueva_fecha_publicacion = st.date_input(
                    "Fecha de publicación (real)",
                    value=fecha_publicacion_dt,
                    format="DD/MM/YYYY",
                    key=f"fecha_publicacion_{indice_seleccionado}",
                    on_change=on_change_callback
                )

                nueva_fecha_publicacion_str = fecha_desde_selector_a_string(
                    nueva_fecha_publicacion) if nueva_fecha_publicacion else ""

                fecha_original = "" if pd.isna(row['Publicación']) else row['Publicación']

                if nueva_fecha_publicacion_str and nueva_fecha_publicacion_str != fecha_original:
                    registros_df.at[
                        registros_df.index[indice_seleccionado], 'Publicación'] = nueva_fecha_publicacion_str
                    
                    # Actualizar plazo de oficio de cierre
                    registros_df = actualizar_plazo_oficio_cierre(registros_df)
                    edited = True

                    # Guardar en Google Sheets
                    with st.spinner("💾 Guardando cambios..."):
                        exito, mensaje = guardar_datos_editados_rapido(registros_df)
                    if exito:
                        st.success("✅ Publicación actualizada")
                        st.rerun()

            # SECCIÓN 6: CIERRE
            st.markdown("### 6. Cierre")
            col1, col2 = st.columns(2)

            with col1:
                # Plazo de oficio de cierre (solo lectura)
                plazo_oficio_cierre = row[
                    'Plazo de oficio de cierre'] if 'Plazo de oficio de cierre' in row and pd.notna(
                    row['Plazo de oficio de cierre']) else ""

                st.text_input(
                    "Plazo de oficio de cierre (automático)",
                    value=plazo_oficio_cierre,
                    disabled=True,
                    key=f"plazo_oficio_cierre_{indice_seleccionado}"
                )

            with col2:
                # Fecha de oficio de cierre
                if 'Fecha de oficio de cierre' in row:
                    fecha_oficio_dt = fecha_para_selector(row['Fecha de oficio de cierre'])
                    nueva_fecha_oficio = st.date_input(
                        "Fecha de oficio de cierre",
                        value=fecha_oficio_dt,
                        format="DD/MM/YYYY",
                        key=f"fecha_oficio_{indice_seleccionado}",
                        on_change=on_change_callback
                    )
                    nueva_fecha_oficio_str = fecha_desde_selector_a_string(
                        nueva_fecha_oficio) if nueva_fecha_oficio else ""

                    fecha_original = "" if pd.isna(row['Fecha de oficio de cierre']) else row[
                        'Fecha de oficio de cierre']

                    if nueva_fecha_oficio_str != fecha_original:
                        # Validar que tenga publicación
                        tiene_publicacion = (
                            'Publicación' in row and 
                            pd.notna(row['Publicación']) and 
                            row['Publicación'] != ""
                        )

                        if nueva_fecha_oficio_str and not tiene_publicacion:
                            st.error("❌ Debe completar la Publicación antes del oficio de cierre")
                        else:
                            registros_df.at[registros_df.index[
                                indice_seleccionado], 'Fecha de oficio de cierre'] = nueva_fecha_oficio_str
                            
                            # Si se agrega fecha, Estado = Completado
                            if nueva_fecha_oficio_str:
                                registros_df.at[registros_df.index[indice_seleccionado], 'Estado'] = 'Completado'
                            
                            edited = True

                            # Guardar en Google Sheets
                            with st.spinner("💾 Guardando cambios..."):
                                exito, mensaje = guardar_datos_editados_rapido(registros_df)
                            if exito:
                                st.success("✅ Oficio de cierre actualizado")
                                st.rerun()

            # SECCIÓN 7: ESTADO Y OBSERVACIONES
            st.markdown("### 7. Estado y Observaciones")
            col1, col2 = st.columns(2)

            with col1:
                # Estado general
                if 'Estado' in row:
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
                # Observaciones
                if 'Observación' in row:
                    nueva_observacion = st.text_area(
                        "Observación",
                        value=row['Observación'] if pd.notna(row['Observación']) else "",
                        key=f"observacion_{indice_seleccionado}",
                        on_change=on_change_callback
                    )
                    if nueva_observacion != row['Observación']:
                        registros_df.at[registros_df.index[indice_seleccionado], 'Observación'] = nueva_observacion
                        edited = True

            # Mostrar botón de guardar si se han hecho cambios
            if edited or st.session_state.cambios_pendientes:
                if st.button("💾 Guardar Todos los Cambios", key=f"guardar_{indice_seleccionado}"):
                    # Aplicar validaciones de reglas de negocio antes de guardar
                    registros_df = validar_reglas_negocio(registros_df)

                    # Actualizar los plazos automáticamente
                    registros_df = actualizar_plazo_analisis(registros_df)
                    registros_df = actualizar_plazo_cronograma(registros_df)
                    registros_df = actualizar_plazo_oficio_cierre(registros_df)

                    # Guardar los datos en Google Sheets
                    with st.spinner("💾 Guardando en Google Sheets..."):
                        exito, mensaje = guardar_datos_editados(registros_df, crear_backup=True)

                    if exito:
                        st.session_state.mensaje_guardado = ("success", mensaje)
                        st.session_state.cambios_pendientes = False
                        st.rerun()
                    else:
                        st.session_state.mensaje_guardado = ("error", mensaje)

    except Exception as e:
        st.error(f"Error al editar el registro: {e}")

    return registros_df

# [Resto de las funciones continúan igual...]
# mostrar_detalle_cronogramas, mostrar_reportes, mostrar_alertas_vencimientos, etc.

def main():
    try:
        # Inicializar estado de sesión para registro de cambios
        if 'cambios_pendientes' not in st.session_state:
            st.session_state.cambios_pendientes = False

        if 'mensaje_guardado' not in st.session_state:
            st.session_state.mensaje_guardado = None

        # Inicializar lista de funcionarios en el estado de sesión
        if 'funcionarios' not in st.session_state:
            st.session_state.funcionarios = []

        # Configuración de la página
        setup_page()

        # Cargar estilos
        load_css()

        # Título
        st.markdown('<div class="title">📊 Tablero de Control de Seguimiento de Cronogramas</div>',
                    unsafe_allow_html=True)
        
        # Mostrar estado de Google Sheets
        st.markdown("### 🔗 Estado de Google Sheets")
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.info("🔄 Cargando datos desde Google Sheets...")
        
        with col2:
            if st.button("🔄 Reconectar"):
                st.rerun()

        # Sidebar con configuraciones
        mostrar_configuracion_sheets()
        mostrar_carga_archivos()

        # Información sobre el tablero
        st.sidebar.markdown('<div class="subtitle">Información</div>', unsafe_allow_html=True)
        st.sidebar.markdown("""
        <div class="info-box">
        <p><strong>Tablero de Control de Cronogramas</strong></p>
        <p>Este tablero muestra el seguimiento de cronogramas conectado a Google Sheets para persistencia permanente de datos.</p>
        <p><strong>✅ Datos sincronizados en tiempo real</strong></p>
        <p><strong>🔒 Respaldo automático</strong></p>
        <p><strong>👥 Colaboración en tiempo real</strong></p>
        </div>
        """, unsafe_allow_html=True)

        # Cargar datos
        registros_df, meta_df = cargar_datos()

        # Verificar si los DataFrames están vacíos o no tienen registros
        if registros_df.empty:
            st.warning(
                "⚠️ No hay datos de registros en Google Sheets. Puedes:")
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("- 📁 Subir un archivo Excel usando el panel lateral")
            with col2:
                st.markdown("- ➕ Agregar datos directamente en Google Sheets")
            
            # Crear estructura mínima para que la app funcione
            registros_df = pd.DataFrame(columns=[
                'Cod', 'Entidad', 'TipoDato', 'Nivel Información ',
                'Acuerdo de compromiso', 'Análisis y cronograma',
                'Estándares', 'Publicación', 'Fecha de entrega de información',
                'Plazo de análisis', 'Plazo de cronograma', 'Plazo de oficio de cierre'
            ])

        # Asegurar que las columnas requeridas existan
        columnas_requeridas = ['Cod', 'Entidad', 'TipoDato', 'Acuerdo de compromiso',
                               'Análisis y cronograma', 'Estándares', 'Publicación',
                               'Nivel Información ', 'Fecha de entrega de información',
                               'Plazo de análisis', 'Plazo de cronograma', 'Plazo de oficio de cierre']

        for columna in columnas_requeridas:
            if columna not in registros_df.columns:
                registros_df[columna] = ''

        # Aplicar validaciones de reglas de negocio
        registros_df = validar_reglas_negocio(registros_df)

        # Procesar las metas
        metas_nuevas_df, metas_actualizar_df = procesar_metas(meta_df)

        # Agregar columna de porcentaje de avance
        registros_df['Porcentaje Avance'] = registros_df.apply(calcular_porcentaje_avance, axis=1)

        # Agregar columna de estado de fechas
        registros_df['Estado Fechas'] = registros_df.apply(verificar_estado_fechas, axis=1)

        # Crear pestañas
        tab1, tab2, tab3, tab4 = st.tabs(["Dashboard", "Edición de Registros", "Alertas de Vencimientos", "Reportes"])
     
        with tab1:
            # FILTROS PARA DASHBOARD
            st.markdown("### 🔍 Filtros")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                # Filtro por entidad
                entidades = ['Todas'] + sorted(registros_df['Entidad'].unique().tolist())
                entidad_seleccionada = st.selectbox('Entidad', entidades, key="dash_entidad")
            
            with col2:
                # Filtro por funcionario
                funcionarios = ['Todos']
                if 'Funcionario' in registros_df.columns:
                    funcionarios += sorted(registros_df['Funcionario'].dropna().unique().tolist())
                funcionario_seleccionado = st.selectbox('Funcionario', funcionarios, key="dash_funcionario")
            
            with col3:
                # Filtro por tipo de dato
                tipos_dato = ['Todos'] + sorted(registros_df['TipoDato'].dropna().unique().tolist())
                tipo_dato_seleccionado = st.selectbox('Tipo de Dato', tipos_dato, key="dash_tipo")
            
            with col4:
                # Filtro por nivel de información dependiente de entidad
                if entidad_seleccionada != 'Todas':
                    # Filtrar niveles según la entidad seleccionada
                    niveles_entidad = registros_df[registros_df['Entidad'] == entidad_seleccionada]['Nivel Información '].dropna().unique().tolist()
                    niveles = ['Todos'] + sorted(niveles_entidad)
                    nivel_seleccionado = st.selectbox('Nivel de Información', niveles, key="dash_nivel")
                else:
                    # Si no hay entidad seleccionada, no mostrar el filtro de nivel
                    nivel_seleccionado = 'Todos'
            
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
            
            st.markdown("---")  # Separador visual
            
            mostrar_dashboard(df_filtrado, metas_nuevas_df, metas_actualizar_df, registros_df)     

        with tab2:
            registros_df = mostrar_edicion_registros(registros_df)

        # [Resto de las pestañas continúan igual...]

        with tab3:
            st.markdown("---")  # Separador visual
            mostrar_alertas_vencimientos(registros_df)

        with tab4:
            # Nueva pestaña de Reportes
            st.markdown("### 🔍 Filtros")
            
            # Primera fila de filtros
            col1, col2, col3 = st.columns(3)
            
            with col1:
                # 1. Filtro por tipo de dato
                tipos_dato_reporte = ['Todos'] + sorted(registros_df['TipoDato'].dropna().unique().tolist())
                tipo_dato_reporte = st.selectbox('Tipo de Dato', tipos_dato_reporte, key="reporte_tipo")
            
            with col2:
                # 2. Filtro por acuerdo de compromiso suscrito
                acuerdo_opciones = ['Todos', 'Suscrito', 'No Suscrito']
                acuerdo_filtro = st.selectbox('Acuerdo de Compromiso', acuerdo_opciones, key="reporte_acuerdo")
            
            with col3:
                # 3. Filtro por análisis y cronograma
                analisis_opciones = ['Todos', 'Completado', 'No Completado']
                analisis_filtro = st.selectbox('Análisis y Cronograma', analisis_opciones, key="reporte_analisis")
            
            # Segunda fila de filtros
            col4, col5, col6 = st.columns(3)
            
            with col4:
                # 4. Filtro por estándares completado
                estandares_opciones = ['Todos', 'Completado', 'No Completado']
                estandares_filtro = st.selectbox('Estándares', estandares_opciones, key="reporte_estandares")
            
            with col5:
                # 5. Filtro por publicación
                publicacion_opciones = ['Todos', 'Completado', 'No Completado']
                publicacion_filtro = st.selectbox('Publicación', publicacion_opciones, key="reporte_publicacion")
            
            with col6:
                # 6. Filtro por finalizado
                finalizado_opciones = ['Todos', 'Finalizado', 'No Finalizado']
                finalizado_filtro = st.selectbox('Finalizado', finalizado_opciones, key="reporte_finalizado")
            
            st.markdown("---")  # Separador visual
            
            mostrar_reportes(registros_df, tipo_dato_reporte, acuerdo_filtro, analisis_filtro, 
                           estandares_filtro, publicacion_filtro, finalizado_filtro)

        # Agregar sección de diagnóstico
        mostrar_diagnostico(registros_df, meta_df, metas_nuevas_df, metas_actualizar_df, df_filtrado)

        # Agregar sección de ayuda
        mostrar_ayuda()

    except Exception as e:
        st.error(f"❌ Error crítico: {str(e)}")
        st.markdown("### 🆘 Solución de Problemas")
        st.markdown("""
        **Posibles causas:**
        1. **Configuración de Google Sheets:** Verifica las credenciales y permisos
        2. **Conexión a Internet:** Asegúrate de tener conexión estable
        3. **Estructura de datos:** Verifica que las hojas tengan la estructura correcta
        
        **Acciones recomendadas:**
        - 🔄 Usa el botón "Reconectar" en la parte superior
        - 🔧 Revisa la configuración en el panel lateral
        - 📋 Consulta las instrucciones de configuración
        """)

def mostrar_error(error):
    """Muestra mensajes de error formateados."""
    st.error(f"❌ Error al cargar o procesar los datos: {error}")
    st.info("""
    **Posibles soluciones:**
    1. **Google Sheets**: Verifica la configuración de credenciales en el panel lateral
    2. **Conexión**: Asegúrate de tener conexión a internet estable
    3. **Permisos**: Confirma que el service account tenga acceso al spreadsheet
    4. **Estructura**: Verifica que las hojas tengan la estructura correcta

    **Acciones recomendadas:**
    - 🔄 Usa el botón "Reconectar" 
    - 🔧 Revisa la configuración en el panel lateral
    - 📁 Intenta cargar datos desde Excel usando el uploader
    """)

if __name__ == "__main__":
    main()

def mostrar_detalle_cronogramas(df_filtrado):
    """Muestra el detalle de los cronogramas con información detallada por entidad."""
    st.markdown('<div class="subtitle">Detalle de Cronogramas por Entidad</div>', unsafe_allow_html=True)

    # Verificar si hay datos filtrados
    if df_filtrado.empty:
        st.warning("No hay datos para mostrar con los filtros seleccionados.")
        return

    # Crear gráfico de barras apiladas por entidad y nivel de información
    df_conteo = df_filtrado.groupby(['Entidad', 'Nivel Información ']).size().reset_index(name='Cantidad')

    fig_barras = px.bar(
        df_conteo,
        x='Entidad',
        y='Cantidad',
        color='Nivel Información ',
        title='Cantidad de Registros por Entidad y Nivel de Información',
        labels={'Entidad': 'Entidad', 'Cantidad': 'Cantidad de Registros',
                'Nivel Información ': 'Nivel de Información'},
        color_discrete_sequence=px.colors.qualitative.Plotly
    )

    st.plotly_chart(fig_barras, use_container_width=True)

    # Crear gráfico de barras de porcentaje de avance por entidad
    df_avance = df_filtrado.groupby('Entidad')['Porcentaje Avance'].mean().reset_index()
    df_avance = df_avance.sort_values('Porcentaje Avance', ascending=False)

    fig_avance = px.bar(
        df_avance,
        x='Entidad',
        y='Porcentaje Avance',
        title='Porcentaje de Avance Promedio por Entidad',
        labels={'Entidad': 'Entidad', 'Porcentaje Avance': 'Porcentaje de Avance (%)'},
        color='Porcentaje Avance',
        color_continuous_scale='RdYlGn'
    )

    fig_avance.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig_avance, use_container_width=True)

    # Mostrar detalle de porcentaje de avance por hito
    st.markdown('### Avance por Hito')

    # Calcular porcentajes de avance para cada hito
    hitos = ['Acuerdo de compromiso', 'Análisis y cronograma', 'Estándares', 'Publicación']
    avance_hitos = {}

    for hito in hitos:
        if hito == 'Acuerdo de compromiso':
            completados = df_filtrado[df_filtrado[hito].str.upper().isin(['SI', 'SÍ', 'YES', 'Y'])].shape[0]
        else:
            completados = df_filtrado[df_filtrado[hito].notna() & (df_filtrado[hito] != '')].shape[0]

        total = df_filtrado.shape[0]
        porcentaje = (completados / total * 100) if total > 0 else 0
        avance_hitos[hito] = {'Completados': completados, 'Total': total, 'Porcentaje': porcentaje}

    # Crear dataframe para mostrar los resultados
    avance_hitos_df = pd.DataFrame(avance_hitos).T.reset_index()
    avance_hitos_df.columns = ['Hito', 'Completados', 'Total', 'Porcentaje']

    # Mostrar tabla de avance por hito
    st.dataframe(avance_hitos_df.style.format({
        'Porcentaje': '{:.2f}%'
    }).background_gradient(cmap='RdYlGn', subset=['Porcentaje']))

    # Crear gráfico de barras para el avance por hito
    fig_hitos = px.bar(
        avance_hitos_df,
        x='Hito',
        y='Porcentaje',
        title='Porcentaje de Avance por Hito',
        labels={'Hito': 'Hito', 'Porcentaje': 'Porcentaje de Avance (%)'},
        color='Porcentaje',
        color_continuous_scale='RdYlGn',
        text='Porcentaje'
    )

    fig_hitos.update_traces(texttemplate='%{text:.2f}%', textposition='outside')
    st.plotly_chart(fig_hitos, use_container_width=True)

def mostrar_reportes(registros_df, tipo_dato_filtro, acuerdo_filtro, analisis_filtro, 
                    estandares_filtro, publicacion_filtro, finalizado_filtro):
    """Muestra la pestaña de reportes con tabla completa y filtros específicos."""
    st.markdown('<div class="subtitle">Reportes de Registros</div>', unsafe_allow_html=True)
    
    # Aplicar filtros
    df_filtrado = registros_df.copy()
    
    # Filtro por tipo de dato
    if tipo_dato_filtro != 'Todos':
        df_filtrado = df_filtrado[df_filtrado['TipoDato'].str.upper() == tipo_dato_filtro.upper()]
    
    # Filtro por acuerdo de compromiso suscrito
    if acuerdo_filtro != 'Todos':
        if acuerdo_filtro == 'Suscrito':
            df_filtrado = df_filtrado[
                (df_filtrado['Suscripción acuerdo de compromiso'].notna()) & 
                (df_filtrado['Suscripción acuerdo de compromiso'] != '') |
                (df_filtrado['Entrega acuerdo de compromiso'].notna()) & 
                (df_filtrado['Entrega acuerdo de compromiso'] != '')
            ]
        else:  # No Suscrito
            df_filtrado = df_filtrado[
                ((df_filtrado['Suscripción acuerdo de compromiso'].isna()) | 
                 (df_filtrado['Suscripción acuerdo de compromiso'] == '')) &
                ((df_filtrado['Entrega acuerdo de compromiso'].isna()) | 
                 (df_filtrado['Entrega acuerdo de compromiso'] == ''))
            ]
    
    # Filtro por análisis y cronograma
    if analisis_filtro != 'Todos':
        if analisis_filtro == 'Completado':
            df_filtrado = df_filtrado[
                (df_filtrado['Análisis y cronograma'].notna()) & 
                (df_filtrado['Análisis y cronograma'] != '')
            ]
        else:  # No Completado
            df_filtrado = df_filtrado[
                (df_filtrado['Análisis y cronograma'].isna()) | 
                (df_filtrado['Análisis y cronograma'] == '')
            ]
    
    # Filtro por estándares completado
    if estandares_filtro != 'Todos':
        if estandares_filtro == 'Completado':
            df_filtrado = df_filtrado[
                (df_filtrado['Estándares'].notna()) & 
                (df_filtrado['Estándares'] != '')
            ]
        else:  # No Completado
            df_filtrado = df_filtrado[
                (df_filtrado['Estándares'].isna()) | 
                (df_filtrado['Estándares'] == '')
            ]
    
    # Filtro por publicación
    if publicacion_filtro != 'Todos':
        if publicacion_filtro == 'Completado':
            df_filtrado = df_filtrado[
                (df_filtrado['Publicación'].notna()) & 
                (df_filtrado['Publicación'] != '')
            ]
        else:  # No Completado
            df_filtrado = df_filtrado[
                (df_filtrado['Publicación'].isna()) | 
                (df_filtrado['Publicación'] == '')
            ]
    
    # Filtro por finalizado
    if finalizado_filtro != 'Todos':
        if finalizado_filtro == 'Finalizado':
            df_filtrado = df_filtrado[
                (df_filtrado['Fecha de oficio de cierre'].notna()) & 
                (df_filtrado['Fecha de oficio de cierre'] != '')
            ]
        else:  # No Finalizado
            df_filtrado = df_filtrado[
                (df_filtrado['Fecha de oficio de cierre'].isna()) | 
                (df_filtrado['Fecha de oficio de cierre'] == '')
            ]
    
    # Mostrar estadísticas del filtrado
    st.markdown("### Resumen de Registros Filtrados")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_filtrados = len(df_filtrado)
        st.markdown(f"""
        <div class="metric-card">
            <p style="font-size: 1rem; color: #64748b;">Total Filtrados</p>
            <p style="font-size: 2.5rem; font-weight: bold; color: #1E40AF;">{total_filtrados}</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        if total_filtrados > 0:
            avance_promedio = df_filtrado['Porcentaje Avance'].mean()
            st.markdown(f"""
            <div class="metric-card">
                <p style="font-size: 1rem; color: #64748b;">Avance Promedio</p>
                <p style="font-size: 2.5rem; font-weight: bold; color: #047857;">{avance_promedio:.1f}%</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="metric-card">
                <p style="font-size: 1rem; color: #64748b;">Avance Promedio</p>
                <p style="font-size: 2.5rem; font-weight: bold; color: #047857;">0%</p>
            </div>
            """, unsafe_allow_html=True)

    with col3:
        if total_filtrados > 0:
            completados = len(df_filtrado[df_filtrado['Porcentaje Avance'] == 100])
            st.markdown(f"""
            <div class="metric-card">
                <p style="font-size: 1rem; color: #64748b;">Completados</p>
                <p style="font-size: 2.5rem; font-weight: bold; color: #B45309;">{completados}</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="metric-card">
                <p style="font-size: 1rem; color: #64748b;">Completados</p>
                <p style="font-size: 2.5rem; font-weight: bold; color: #B45309;">0</p>
            </div>
            """, unsafe_allow_html=True)

    with col4:
        if total_filtrados > 0:
            porcentaje_completados = (len(df_filtrado[df_filtrado['Porcentaje Avance'] == 100]) / total_filtrados * 100)
            st.markdown(f"""
            <div class="metric-card">
                <p style="font-size: 1rem; color: #64748b;">% Completados</p>
                <p style="font-size: 2.5rem; font-weight: bold; color: #BE185D;">{porcentaje_completados:.1f}%</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="metric-card">
                <p style="font-size: 1rem; color: #64748b;">% Completados</p>
                <p style="font-size: 2.5rem; font-weight: bold; color: #BE185D;">0%</p>
            </div>
            """, unsafe_allow_html=True)

    # Mostrar tabla de registros filtrados
    st.markdown("### Tabla de Registros")
    
    if df_filtrado.empty:
        st.warning("No se encontraron registros que coincidan con los filtros seleccionados.")
        return
    
    # Definir columnas a mostrar (misma estructura que el dashboard)
    columnas_mostrar = [
        'Cod', 'Entidad', 'Nivel Información ', 'Funcionario',
        'Frecuencia actualizacion ', 'TipoDato',
        'Suscripción acuerdo de compromiso', 'Entrega acuerdo de compromiso',
        'Fecha de entrega de información', 'Plazo de análisis', 'Plazo de cronograma',
        'Análisis y cronograma',
        'Registro (completo)', 'ET (completo)', 'CO (completo)', 'DD (completo)', 'REC (completo)',
        'SERVICIO (completo)',
        'Estándares (fecha programada)', 'Estándares',
        'Fecha de publicación programada', 'Publicación',
        'Plazo de oficio de cierre', 'Fecha de oficio de cierre',
        'Estado', 'Observación', 'Porcentaje Avance'
    ]
    
    # Verificar que todas las columnas existan
    columnas_mostrar_existentes = [col for col in columnas_mostrar if col in df_filtrado.columns]
    df_mostrar = df_filtrado[columnas_mostrar_existentes].copy()
    
    # Aplicar formato a las fechas
    columnas_fecha = [
        'Suscripción acuerdo de compromiso', 'Entrega acuerdo de compromiso',
        'Fecha de entrega de información', 'Plazo de análisis', 'Plazo de cronograma',
        'Análisis y cronograma', 'Estándares (fecha programada)', 'Estándares',
        'Fecha de publicación programada', 'Publicación',
        'Plazo de oficio de cierre', 'Fecha de oficio de cierre'
    ]
    
    for col in columnas_fecha:
        if col in df_mostrar.columns:
            df_mostrar[col] = df_mostrar[col].apply(lambda x: formatear_fecha(x) if es_fecha_valida(x) else "")
    
    # Mostrar dataframe con formato
    st.dataframe(
        df_mostrar
        .style.format({'Porcentaje Avance': '{:.2f}%'})
        .apply(highlight_estado_fechas, axis=1)
        .background_gradient(cmap='RdYlGn', subset=['Porcentaje Avance']),
        use_container_width=True
    )
    
    # Botón para descargar reporte
    st.markdown("### Descargar Reporte")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Descargar como Excel
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_mostrar.to_excel(writer, sheet_name='Reporte Filtrado', index=False)

        excel_data = output.getvalue()
        st.download_button(
            label="📊 Descargar reporte como Excel",
            data=excel_data,
            file_name=f"reporte_registros_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            help="Descarga el reporte filtrado en formato Excel"
        )
    
    with col2:
        # Descargar como CSV
        csv = df_mostrar.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📄 Descargar reporte como CSV",
            data=csv,
            file_name=f"reporte_registros_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            help="Descarga el reporte filtrado en formato CSV"
        )
    
    # Información adicional sobre los filtros aplicados
    filtros_aplicados = []
    if tipo_dato_filtro != 'Todos':
        filtros_aplicados.append(f"Tipo de Dato: {tipo_dato_filtro}")
    if acuerdo_filtro != 'Todos':
        filtros_aplicados.append(f"Acuerdo de Compromiso: {acuerdo_filtro}")
    if analisis_filtro != 'Todos':
        filtros_aplicados.append(f"Análisis y Cronograma: {analisis_filtro}")
    if estandares_filtro != 'Todos':
        filtros_aplicados.append(f"Estándares: {estandares_filtro}")
    if publicacion_filtro != 'Todos':
        filtros_aplicados.append(f"Publicación: {publicacion_filtro}")
    if finalizado_filtro != 'Todos':
        filtros_aplicados.append(f"Finalizado: {finalizado_filtro}")
    
    if filtros_aplicados:
        st.info(f"**Filtros aplicados:** {', '.join(filtros_aplicados)}")
    else:
        st.info("**Mostrando todos los registros** (sin filtros aplicados)")

def mostrar_alertas_vencimientos(registros_df):
    """Muestra alertas de vencimientos de fechas en los registros."""
    st.markdown('<div class="subtitle">Alertas de Vencimientos</div>', unsafe_allow_html=True)

    # Fecha actual para comparaciones
    fecha_actual = datetime.now().date()

    # Función para calcular días hábiles entre fechas (excluyendo fines de semana y festivos)
    def calcular_dias_habiles(fecha_inicio, fecha_fin):
        if not fecha_inicio or not fecha_fin:
            return None

        # Convertir a objetos date si son datetime
        if isinstance(fecha_inicio, datetime):
            fecha_inicio = fecha_inicio.date()
        if isinstance(fecha_fin, datetime):
            fecha_fin = fecha_fin.date()

        # Si la fecha de inicio es posterior a la fecha fin, devolver días negativos
        if fecha_inicio > fecha_fin:
            return -calcular_dias_habiles(fecha_fin, fecha_inicio)

        # Calcular días hábiles
        dias = 0
        fecha_actual_calc = fecha_inicio
        while fecha_actual_calc <= fecha_fin:
            # Si no es fin de semana (0=lunes, 6=domingo)
            if fecha_actual_calc.weekday() < 5:
                dias += 1
            fecha_actual_calc += timedelta(days=1)

        return dias

    # Función para determinar si una fecha está próxima a vencer (dentro de 5 días hábiles)
    def es_proximo_vencimiento(fecha_limite):
        if not fecha_limite:
            return False

        # Convertir a objeto date si es datetime
        if isinstance(fecha_limite, datetime):
            fecha_limite = fecha_limite.date()

        # Si ya está vencido, no es "próximo a vencer"
        if fecha_limite < fecha_actual:
            return False

        # Calcular días hábiles hasta la fecha límite
        dias_habiles = calcular_dias_habiles(fecha_actual, fecha_limite)

        # Si está dentro de los próximos 5 días hábiles
        return dias_habiles is not None and 0 <= dias_habiles <= 5

    # Función para determinar si una fecha está vencida
    def es_vencido(fecha_limite):
        if not fecha_limite:
            return False

        # Convertir a objeto date si es datetime
        if isinstance(fecha_limite, datetime):
            fecha_limite = fecha_limite.date()

        return fecha_limite < fecha_actual

    # Función para calcular días de rezago
    def calcular_dias_rezago(fecha_limite):
        if not fecha_limite or not es_vencido(fecha_limite):
            return None

        # Convertir a objeto date si es datetime
        if isinstance(fecha_limite, datetime):
            fecha_limite = fecha_limite.date()

        return (fecha_actual - fecha_limite).days

    # Función para formatear fechas de manera segura
    def formatear_fecha_segura(fecha):
        if fecha is None or pd.isna(fecha):
            return ""
        try:
            return fecha.strftime('%d/%m/%Y')
        except:
            return ""

    # Preprocesar registros para el análisis
    registros_alertas = []

    for idx, row in registros_df.iterrows():
        try:
            # Procesar fechas (convertir de string a datetime) con manejo seguro de NaT
            fecha_entrega_acuerdo = procesar_fecha(row.get('Entrega acuerdo de compromiso', ''))
            fecha_entrega_info = procesar_fecha(row.get('Fecha de entrega de información', ''))
            fecha_plazo_cronograma = procesar_fecha(row.get('Plazo de cronograma', ''))
            fecha_analisis_cronograma = procesar_fecha(row.get('Análisis y cronograma', ''))
            fecha_estandares_prog = procesar_fecha(row.get('Estándares (fecha programada)', ''))
            fecha_estandares = procesar_fecha(row.get('Estándares', ''))
            fecha_publicacion_prog = procesar_fecha(row.get('Fecha de publicación programada', ''))
            fecha_publicacion = procesar_fecha(row.get('Publicación', ''))
            fecha_plazo_oficio_cierre = procesar_fecha(row.get('Plazo de oficio de cierre', ''))
            fecha_oficio_cierre = procesar_fecha(row.get('Fecha de oficio de cierre', ''))

            # Análisis de alertas por cada tipo de fecha
            # [Lógica similar al código original pero optimizada]
            
            # 1. Entrega de información
            if fecha_entrega_acuerdo is not None and pd.notna(fecha_entrega_acuerdo):
                if fecha_entrega_info is not None and pd.notna(fecha_entrega_info):
                    # Si hay fecha real, verificar si está con retraso
                    if fecha_entrega_info > fecha_entrega_acuerdo:
                        dias_rezago = calcular_dias_habiles(fecha_entrega_acuerdo, fecha_entrega_info)
                        registros_alertas.append({
                            'Cod': row['Cod'],
                            'Entidad': row['Entidad'],
                            'Nivel Información': row.get('Nivel Información ', ''),
                            'Funcionario': row.get('Funcionario', ''),
                            'Tipo Alerta': 'Entrega de información',
                            'Fecha Programada': fecha_entrega_acuerdo,
                            'Fecha Real': fecha_entrega_info,
                            'Días Rezago': dias_rezago,
                            'Estado': 'Completado con retraso',
                            'Descripción': f'Entrega de información con {dias_rezago} días hábiles de retraso'
                        })
                else:
                    # No hay fecha real, verificar si está vencido
                    if es_vencido(fecha_entrega_acuerdo):
                        dias_rezago = calcular_dias_rezago(fecha_entrega_acuerdo)
                        registros_alertas.append({
                            'Cod': row['Cod'],
                            'Entidad': row['Entidad'],
                            'Nivel Información': row.get('Nivel Información ', ''),
                            'Funcionario': row.get('Funcionario', ''),
                            'Tipo Alerta': 'Entrega de información',
                            'Fecha Programada': fecha_entrega_acuerdo,
                            'Fecha Real': None,
                            'Días Rezago': dias_rezago,
                            'Estado': 'Vencido',
                            'Descripción': f'Entrega de información vencida hace {dias_rezago} días'
                        })

            # [Continuar con lógica similar para otros tipos...]

        except Exception as e:
            st.warning(f"Error procesando registro {row['Cod']}: {e}")
            continue

    # Mostrar resultados de alertas
    if registros_alertas:
        df_alertas = pd.DataFrame(registros_alertas)

        # Asegurarse de que las fechas se formateen correctamente
        for col in ['Fecha Programada', 'Fecha Real']:
            if col in df_alertas.columns:
                df_alertas[col] = df_alertas[col].apply(formatear_fecha_segura)

        # Mostrar estadísticas de alertas
        st.markdown("### Resumen de Alertas")

        col1, col2, col3 = st.columns(3)

        with col1:
            num_vencidos = len(df_alertas[df_alertas['Estado'] == 'Vencido'])
            st.markdown(f"""
            <div class="metric-card" style="background-color: #fee2e2;">
                <p style="font-size: 1rem; color: #b91c1c;">Vencidos</p>
                <p style="font-size: 2.5rem; font-weight: bold; color: #b91c1c;">{num_vencidos}</p>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            num_proximos = len(df_alertas[df_alertas['Estado'] == 'Próximo a vencer'])
            st.markdown(f"""
            <div class="metric-card" style="background-color: #fef3c7;">
                <p style="font-size: 1rem; color: #b45309;">Próximos a vencer</p>
                <p style="font-size: 2.5rem; font-weight: bold; color: #b45309;">{num_proximos}</p>
            </div>
            """, unsafe_allow_html=True)

        with col3:
            num_retrasados = len(df_alertas[df_alertas['Estado'] == 'Completado con retraso'])
            st.markdown(f"""
            <div class="metric-card" style="background-color: #dbeafe;">
                <p style="font-size: 1rem; color: #1e40af;">Completados con retraso</p>
                <p style="font-size: 2.5rem; font-weight: bold; color: #1e40af;">{num_retrasados}</p>
            </div>
            """, unsafe_allow_html=True)

        # Mostrar tabla de alertas
        st.markdown("### Listado de Alertas")
        st.dataframe(df_alertas, use_container_width=True)

        # Botón para descargar alertas
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_alertas.to_excel(writer, sheet_name='Alertas', index=False)

        excel_data = output.getvalue()
        st.download_button(
            label="📥 Descargar alertas como Excel",
            data=excel_data,
            file_name="alertas_vencimientos.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            help="Descarga las alertas en formato Excel"
        )
    else:
        st.success("🎉 ¡No hay alertas de vencimientos pendientes!")

def mostrar_diagnostico(registros_df, meta_df, metas_nuevas_df, metas_actualizar_df, df_filtrado):
    """Muestra la sección de diagnóstico con análisis detallado de los datos."""
    with st.expander("🔍 Diagnóstico de Datos"):
        st.markdown("### Diagnóstico de Datos")
        st.markdown("Esta sección proporciona un diagnóstico detallado de los datos cargados desde Google Sheets.")

        # Información general
        st.markdown("#### Información General")
        col1, col2 = st.columns(2)

        with col1:
            st.metric("Total de Registros", len(registros_df))
            st.metric("Registros Filtrados", len(df_filtrado))

        with col2:
            if 'TipoDato' in registros_df.columns:
                st.metric("Registros Nuevos", len(registros_df[registros_df['TipoDato'].str.upper() == 'NUEVO']))
                st.metric("Registros a Actualizar",
                          len(registros_df[registros_df['TipoDato'].str.upper() == 'ACTUALIZAR']))

        # Estado de Google Sheets
        st.markdown("#### Estado de Google Sheets")
        try:
            manager = get_sheets_manager()
            hojas = manager.listar_hojas()
            st.success(f"✅ Conectado a Google Sheets. Hojas disponibles: {', '.join(hojas)}")
        except Exception as e:
            st.error(f"❌ Error de conexión con Google Sheets: {str(e)}")

def mostrar_ayuda():
    """Muestra la sección de ayuda con información sobre el uso del tablero."""
    with st.expander("❓ Ayuda"):
        st.markdown("### Ayuda del Tablero de Control")
        st.markdown("""
        Este tablero de control permite visualizar y gestionar el seguimiento de cronogramas con **persistencia permanente en Google Sheets**.

        #### 🔗 Características Principales
        - **✅ Datos sincronizados en tiempo real** con Google Sheets
        - **🔒 Respaldo automático** de cada cambio
        - **👥 Colaboración simultánea** de múltiples usuarios
        - **📱 Acceso desde cualquier dispositivo**

        #### 📊 Navegación
        - **Dashboard**: Métricas generales, comparación con metas y diagrama de Gantt
        - **Edición de Registros**: Edición individual con validaciones automáticas
        - **Alertas de Vencimientos**: Seguimiento de fechas críticas
        - **Reportes**: Análisis avanzados con filtros personalizados

        #### 🔧 Funcionalidades Google Sheets
        - **Carga desde Excel**: Sube archivos Excel para sincronizar automáticamente
        - **Descarga completa**: Exporta todos los datos en formato Excel
        - **Backup automático**: Cada cambio crea una copia de seguridad
        - **Edición directa**: También puedes editar directamente en Google Sheets

        #### 💾 Guardado Automático
        Los cambios se guardan automáticamente en Google Sheets al:
        - Modificar cualquier campo de fecha
        - Cambiar estados o valores
        - Aplicar validaciones de reglas de negocio

        #### 🆘 Soporte
        Para configuración inicial o problemas técnicos:
        - 📋 Consulta las [Instrucciones de Configuración](https://github.com/tu-repo/INSTRUCCIONES_CONFIGURACION.md)
        - 🔧 Usa el panel "Configuración Google Sheets" en la barra lateral
        - 🔄 Utiliza el botón "Reconectar" si hay problemas de conexión
        """)

def mostrar_error(error):
    """Muestra mensajes de error formateados."""
    st.error(f"❌ Error al cargar o procesar los datos: {error}")
    st.info("""
    **Posibles soluciones:**
    1. **Google Sheets**: Verifica la configuración de credenciales en el panel lateral
    2. **Conexión**: Asegúrate de tener conexión a internet estable
    3. **Permisos**: Confirma que el service account tenga acceso al spreadsheet
    4. **Estructura**: Verifica que las hojas tengan la estructura correcta

    **Acciones recomendadas:**
    - 🔄 Usa el botón "Reconectar" 
    - 🔧 Revisa la configuración en el panel lateral
    - 📁 Intenta cargar datos desde Excel usando el uploader
    """)

        # [Resto de las pestañas continúan igual...]

    except Exception as e:
        st.error(f"❌ Error crítico: {str(e)}")
        st.markdown("### 🆘 Solución de Problemas")
        st.markdown("""
            **Posibles causas:**
            1. **Configuración de Google Sheets:** Verifica las credenciales y permisos
            2. **Conexión a Internet:** Asegúrate de tener conexión estable
            3. **Estructura de datos:** Verifica que las hojas tengan la estructura correcta
            
            **Acciones recomendadas:**
            - 🔄 Usa el botón "Reconectar" en la parte superior
            - 🔧 Revisa la configuración en el panel lateral
            - 📋 Consulta las instrucciones de configuración
            """)

if __name__ == "__main__":
    main()
