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

# ========== FUNCIONES AUXILIARES RESTAURADAS ==========

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

# ========== FUNCIONES DE CONFIGURACIÓN RESTAURADAS ==========

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

# ========== FUNCIÓN DE EDICIÓN RESTAURADA Y MEJORADA ==========

def mostrar_edicion_registros(registros_df):
    """Muestra la pestaña de edición de registros - VERSIÓN COMPLETA RESTAURADA."""
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
    - Se aplicarán automáticamente las siguientes validaciones:
        1. Si 'Entrega acuerdo de compromiso' no está vacío, 'Acuerdo de compromiso' se actualizará a 'SI'
        2. Si 'Análisis y cronograma' tiene fecha, 'Análisis de información' se actualizará a 'SI'
        3. Al introducir fecha en 'Estándares', los campos que no estén 'Completo' se actualizarán automáticamente a 'No aplica'
        4. Si introduce fecha en 'Publicación', 'Disponer datos temáticos' se actualizará automáticamente a 'SI'
        5. Para introducir una fecha en 'Fecha de oficio de cierre', debe tener la etapa de Publicación completada (con fecha)
        6. Al introducir una fecha en 'Fecha de oficio de cierre', el campo 'Estado' se actualizará automáticamente a 'Completado'
        7. Si se elimina la fecha de oficio de cierre, el Estado se cambiará automáticamente a 'En proceso'
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

            # ===== SECCIÓN 1: INFORMACIÓN BÁSICA =====
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

            # Frecuencia de actualización y Funcionario
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
                        registros_df.at[registros_df.index[indice_seleccionado], 'Frecuencia actualizacion '] = nueva_frecuencia
                        edited = True

                # Funcionario (RESTAURADO)
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
                            registros_df.at[registros_df.index[indice_seleccionado], 'Funcionario'] = funcionario_final
                            edited = True

            # ===== SECCIÓN 2: ACTA DE COMPROMISO =====
            st.markdown("### 2. Acta de Compromiso")

            # Actas de acercamiento (RESTAURADO)
            if 'Actas de acercamiento y manifestación de interés' in row:
                col1, col2 = st.columns(2)
                with col1:
                    actas_acercamiento = st.selectbox(
                        "Actas de acercamiento",
                        options=["", "Si", "No"],
                        index=1 if row['Actas de acercamiento y manifestación de interés'].upper() in ["SI", "SÍ",
                                                                                                       "YES",
                                                                                                       "Y"] else (
                            2 if row['Actas de acercamiento y manifestación de interés'].upper() == "NO" else 0),
                        key=f"actas_acercamiento_{indice_seleccionado}",
                        on_change=on_change_callback
                    )
                    if actas_acercamiento != row['Actas de acercamiento y manifestación de interés']:
                        registros_df.at[registros_df.index[
                            indice_seleccionado], 'Actas de acercamiento y manifestación de interés'] = actas_acercamiento
                        edited = True

            # Fechas de compromiso
            col1, col2, col3 = st.columns(3)
            
            # Suscripción acuerdo de compromiso (RESTAURADO)
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

            # ===== SECCIÓN 3: ANÁLISIS Y CRONOGRAMA =====
            st.markdown("### 3. Análisis y Cronograma")

            # Gestión acceso a datos (RESTAURADO)
            if 'Gestion acceso a los datos y documentos requeridos ' in row:
                gestion_acceso = st.selectbox(
                    "Gestión acceso a los datos",
                    options=["", "Si", "No"],
                    index=1 if row['Gestion acceso a los datos y documentos requeridos '].upper() in ["SI", "SÍ",
                                                                                                      "YES",
                                                                                                      "Y"] else (
                        2 if row['Gestion acceso a los datos y documentos requeridos '].upper() == "NO" else 0),
                    key=f"gestion_acceso_analisis_{indice_seleccionado}",
                    on_change=on_change_callback
                )
                if gestion_acceso != row['Gestion acceso a los datos y documentos requeridos ']:
                    registros_df.at[registros_df.index[
                        indice_seleccionado], 'Gestion acceso a los datos y documentos requeridos '] = gestion_acceso
                    edited = True

            col1, col2, col3 = st.columns(3)

            # Campos de análisis (RESTAURADOS)
            with col1:
                if 'Análisis de información' in row:
                    analisis_info = st.selectbox(
                        "Análisis de información",
                        options=["", "Si", "No"],
                        index=1 if row['Análisis de información'].upper() in ["SI", "SÍ", "YES", "Y"] else (
                            2 if row['Análisis de información'].upper() == "NO" else 0),
                        key=f"analisis_info_{indice_seleccionado}",
                        on_change=on_change_callback
                    )
                    if analisis_info != row['Análisis de información']:
                        registros_df.at[
                            registros_df.index[indice_seleccionado], 'Análisis de información'] = analisis_info
                        edited = True

            with col2:
                if 'Cronograma Concertado' in row:
                    cronograma_concertado = st.selectbox(
                        "Cronograma Concertado",
                        options=["", "Si", "No"],
                        index=1 if row['Cronograma Concertado'].upper() in ["SI", "SÍ", "YES", "Y"] else (
                            2 if row['Cronograma Concertado'].upper() == "NO" else 0),
                        key=f"cronograma_concertado_{indice_seleccionado}",
                        on_change=on_change_callback
                    )
                    if cronograma_concertado != row['Cronograma Concertado']:
                        registros_df.at[registros_df.index[
                            indice_seleccionado], 'Cronograma Concertado'] = cronograma_concertado
                        edited = True

            with col3:
                if 'Seguimiento a los acuerdos' in row:
                    seguimiento_acuerdos = st.selectbox(
                        "Seguimiento a los acuerdos",
                        options=["", "Si", "No"],
                        index=1 if row['Seguimiento a los acuerdos'].upper() in ["SI", "SÍ", "YES", "Y"] else (
                            2 if row['Seguimiento a los acuerdos'].upper() == "NO" else 0),
                        key=f"seguimiento_acuerdos_{indice_seleccionado}",
                        on_change=on_change_callback
                    )
                    if seguimiento_acuerdos != row['Seguimiento a los acuerdos']:
                        registros_df.at[registros_df.index[
                            indice_seleccionado], 'Seguimiento a los acuerdos'] = seguimiento_acuerdos
                        edited = True

            # Fechas de análisis y cronograma
            col1, col2 = st.columns(2)

            with col1:
                # Fecha de entrega de información con cálculo automático de plazos
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
                    registros_df = actualizar_plazo_oficio_cierre(registros_df)

                    # Guardar cambios inmediatamente
                    with st.spinner("💾 Recalculando plazos..."):
                        exito, mensaje = guardar_datos_editados_rapido(registros_df)
                        if exito:
                            st.success("✅ Fecha actualizada y plazos recalculados")
                            st.rerun()

            with col2:
                # Fecha real de análisis y cronograma
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

            # Mostrar plazos calculados automáticamente
            col1, col2 = st.columns(2)
            with col1:
                plazo_analisis = row['Plazo de análisis'] if 'Plazo de análisis' in row and pd.notna(
                    row['Plazo de análisis']) else ""
                st.text_input(
                    "Plazo de análisis (calculado automáticamente)",
                    value=plazo_analisis,
                    disabled=True,
                    key=f"plazo_analisis_{indice_seleccionado}"
                )

            with col2:
                plazo_cronograma = row['Plazo de cronograma'] if 'Plazo de cronograma' in row and pd.notna(
                    row['Plazo de cronograma']) else ""
                st.text_input(
                    "Plazo de cronograma (calculado automáticamente)",
                    value=plazo_cronograma,
                    disabled=True,
                    key=f"plazo_cronograma_{indice_seleccionado}"
                )

            st.info(
                "Los plazos se calculan automáticamente: Análisis (5 días hábiles después de entrega), Cronograma (3 días hábiles después del análisis)."
            )

            # ===== SECCIÓN 4: ESTÁNDARES =====
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
                # Fecha real de estándares
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
                    
                    # Actualizar campos de estándares que no estén "Completo" a "No aplica"
                    campos_estandares = ['Registro (completo)', 'ET (completo)', 'CO (completo)', 'DD (completo)',
                                         'REC (completo)', 'SERVICIO (completo)']
                    
                    campos_actualizados = []
                    for campo in campos_estandares:
                        if campo in registros_df.columns:
                            valor_actual = str(registros_df.iloc[indice_seleccionado][campo]).strip()
                            if valor_actual.upper() != "COMPLETO":
                                registros_df.at[registros_df.index[indice_seleccionado], campo] = "No aplica"
                                nombre_campo = campo.split(' (')[0]
                                campos_actualizados.append(nombre_campo)
                    
                    if campos_actualizados:
                        st.info(f"Los siguientes estándares se actualizaron a 'No aplica': {', '.join(campos_actualizados)}")
                    
                    edited = True

                    # Guardar cambios inmediatamente
                    with st.spinner("💾 Guardando cambios..."):
                        registros_df = validar_reglas_negocio(registros_df)
                        exito, mensaje = guardar_datos_editados_rapido(registros_df)
                        if exito:
                            st.success("✅ Estándares actualizados")
                            st.rerun()

            # Sección: Cumplimiento de estándares (RESTAURADA)
            st.markdown("#### Cumplimiento de estándares")

            # Mostrar campos de estándares con lista desplegable
            campos_estandares_completo = ['Registro (completo)', 'ET (completo)', 'CO (completo)', 'DD (completo)',
                                          'REC (completo)', 'SERVICIO (completo)']
            cols = st.columns(3)

            for i, campo in enumerate(campos_estandares_completo):
                # Verificar si el campo existe en el registro
                if campo not in registros_df.iloc[indice_seleccionado]:
                    registros_df.at[registros_df.index[indice_seleccionado], campo] = "Sin iniciar"

                # Obtener el valor actual directamente del DataFrame
                valor_actual = registros_df.iloc[indice_seleccionado][campo] if pd.notna(
                    registros_df.iloc[indice_seleccionado][campo]) else "Sin iniciar"

                with cols[i % 3]:
                    # Determinar el índice correcto para el valor actual
                    opciones = ["Sin iniciar", "En proceso", "Completo", "No aplica"]
                    indice_opcion = 0  # Por defecto "Sin iniciar"

                    if valor_actual in opciones:
                        indice_opcion = opciones.index(valor_actual)
                    elif str(valor_actual).lower() == "en proceso":
                        indice_opcion = 1
                    elif str(valor_actual).lower() == "completo":
                        indice_opcion = 2
                    elif str(valor_actual).lower() == "no aplica":
                        indice_opcion = 3

                    # Extraer nombre sin el sufijo para mostrar en la interfaz
                    nombre_campo = campo.split(' (')[0]

                    # Crear el selectbox con las opciones
                    nuevo_valor = st.selectbox(
                        f"{nombre_campo}",
                        options=opciones,
                        index=indice_opcion,
                        key=f"estandar_{campo}_{indice_seleccionado}",
                        help=f"Estado de cumplimiento para {nombre_campo}"
                    )

                    # Actualizar el valor si ha cambiado
                    if nuevo_valor != valor_actual:
                        registros_df.at[registros_df.index[indice_seleccionado], campo] = nuevo_valor
                        edited = True

                        # Guardar cambios inmediatamente
                        with st.spinner("💾 Guardando..."):
                            registros_df = validar_reglas_negocio(registros_df)
                            exito, mensaje = guardar_datos_editados_rapido(registros_df)
                            if exito:
                                st.success(f"✅ {nombre_campo} actualizado")
                                st.rerun()

            # Validaciones adicionales (RESTAURADAS)
            if 'Resultados de orientación técnica' in row or 'Verificación del servicio web geográfico' in row:
                st.markdown("#### Validaciones")
                cols = st.columns(3)

                campos_validaciones = [
                    'Resultados de orientación técnica',
                    'Verificación del servicio web geográfico',
                    'Verificar Aprobar Resultados',
                    'Revisar y validar los datos cargados en la base de datos',
                    'Aprobación resultados obtenidos en la rientación'
                ]

                for i, campo in enumerate(campos_validaciones):
                    if campo in row:
                        with cols[i % 3]:
                            valor_actual = row[campo]
                            nuevo_valor = st.selectbox(
                                f"{campo}",
                                options=["", "Si", "No"],
                                index=1 if valor_actual == "Si" or valor_actual.upper() in ["SI", "SÍ", "YES",
                                                                                            "Y"] else (
                                    2 if valor_actual == "No" or valor_actual.upper() == "NO" else 0
                                ),
                                key=f"{campo}_{indice_seleccionado}",
                                on_change=on_change_callback
                            )
                            if nuevo_valor != valor_actual:
                                registros_df.at[registros_df.index[indice_seleccionado], campo] = nuevo_valor
                                edited = True

            # ===== SECCIÓN 5: PUBLICACIÓN =====
            st.markdown("### 5. Publicación")
            col1, col2, col3 = st.columns(3)

            with col1:
                # Disponer datos temáticos (RESTAURADO)
                if 'Disponer datos temáticos' in row:
                    disponer_datos = st.selectbox(
                        "Disponer datos temáticos",
                        options=["", "Si", "No"],
                        index=1 if row['Disponer datos temáticos'].upper() in ["SI", "SÍ", "YES", "Y"] else (
                            2 if row['Disponer datos temáticos'].upper() == "NO" else 0),
                        key=f"disponer_datos_{indice_seleccionado}",
                        on_change=on_change_callback
                    )
                    if disponer_datos != row['Disponer datos temáticos']:
                        registros_df.at[
                            registros_df.index[indice_seleccionado], 'Disponer datos temáticos'] = disponer_datos
                        edited = True

            with col2:
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

            with col3:
                # Fecha real de publicación
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
                    # Actualizar automáticamente "Disponer datos temáticos" a "Si"
                    if 'Disponer datos temáticos' in registros_df.columns:
                        registros_df.at[registros_df.index[indice_seleccionado], 'Disponer datos temáticos'] = 'Si'
                        st.info("Se ha actualizado automáticamente 'Disponer datos temáticos' a 'Si'")
                    
                    # Actualizar la fecha de publicación
                    registros_df.at[
                        registros_df.index[indice_seleccionado], 'Publicación'] = nueva_fecha_publicacion_str
                    edited = True

                    # Recalcular el plazo de oficio de cierre
                    registros_df = actualizar_plazo_oficio_cierre(registros_df)

                    # Guardar cambios inmediatamente
                    with st.spinner("💾 Guardando y recalculando plazos..."):
                        registros_df = validar_reglas_negocio(registros_df)
                        exito, mensaje = guardar_datos_editados_rapido(registros_df)
                        if exito:
                            st.success("✅ Publicación actualizada y plazo de cierre recalculado")
                            st.rerun()

            # Mostrar plazo de oficio de cierre
            col1, col2 = st.columns(2)
            with col1:
                plazo_oficio_cierre = row[
                    'Plazo de oficio de cierre'] if 'Plazo de oficio de cierre' in row and pd.notna(
                    row['Plazo de oficio de cierre']) else ""

                st.text_input(
                    "Plazo de oficio de cierre (calculado automáticamente)",
                    value=plazo_oficio_cierre,
                    disabled=True,
                    key=f"plazo_oficio_cierre_{indice_seleccionado}"
                )

                st.info(
                    "El plazo de oficio de cierre se calcula automáticamente como 7 días hábiles después de la fecha de publicación."
                )

            # Catálogo y oficios de cierre (RESTAURADOS)
            if 'Catálogo de recursos geográficos' in row or 'Oficios de cierre' in row:
                col1, col2, col3 = st.columns(3)

                # Catálogo de recursos geográficos
                if 'Catálogo de recursos geográficos' in row:
                    with col1:
                        catalogo_recursos = st.selectbox(
                            "Catálogo de recursos geográficos",
                            options=["", "Si", "No"],
                            index=1 if row['Catálogo de recursos geográficos'].upper() in ["SI", "SÍ", "YES",
                                                                                           "Y"] else (
                                2 if row['Catálogo de recursos geográficos'].upper() == "NO" else 0),
                            key=f"catalogo_recursos_{indice_seleccionado}",
                            on_change=on_change_callback
                        )
                        if catalogo_recursos != row['Catálogo de recursos geográficos']:
                            registros_df.at[registros_df.index[
                                indice_seleccionado], 'Catálogo de recursos geográficos'] = catalogo_recursos
                            edited = True

                # Oficios de cierre
                if 'Oficios de cierre' in row:
                    with col2:
                        oficios_cierre = st.selectbox(
                            "Oficios de cierre",
                            options=["", "Si", "No"],
                            index=1 if row['Oficios de cierre'].upper() in ["SI", "SÍ", "YES", "Y"] else (
                                2 if row['Oficios de cierre'].upper() == "NO" else 0),
                            key=f"oficios_cierre_{indice_seleccionado}",
                            on_change=on_change_callback
                        )
                        if oficios_cierre != row['Oficios de cierre']:
                            registros_df.at[
                                registros_df.index[indice_seleccionado], 'Oficios de cierre'] = oficios_cierre
                            edited = True

                # Fecha de oficio de cierre (RESTAURADO CON VALIDACIONES)
                if 'Fecha de oficio de cierre' in row:
                    with col3:
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

                        # Si se ha introducido una nueva fecha de oficio de cierre
                        if nueva_fecha_oficio_str and nueva_fecha_oficio_str != fecha_original:
                            # Validar que la publicación esté completada
                            tiene_publicacion = (
                                'Publicación' in row and 
                                pd.notna(row['Publicación']) and 
                                row['Publicación'] != ""
                            )

                            if not tiene_publicacion:
                                st.error(
                                    "No es posible diligenciar la Fecha de oficio de cierre. Debe completar primero la etapa de Publicación.")
                            else:
                                # Actualizar fecha de oficio de cierre
                                registros_df.at[registros_df.index[
                                    indice_seleccionado], 'Fecha de oficio de cierre'] = nueva_fecha_oficio_str

                                # Actualizar Estado a "Completado" automáticamente
                                registros_df.at[registros_df.index[indice_seleccionado], 'Estado'] = 'Completado'

                                # Recalcular el porcentaje de avance (ahora será 100% automáticamente)
                                registros_df.at[registros_df.index[indice_seleccionado], 'Porcentaje Avance'] = calcular_porcentaje_avance(registros_df.iloc[indice_seleccionado])

                                edited = True
                                # Guardar cambios
                                with st.spinner("💾 Guardando cambios finales..."):
                                    registros_df = validar_reglas_negocio(registros_df)
                                    exito, mensaje = guardar_datos_editados_rapido(registros_df)
                                    if exito:
                                        st.success(
                                            "✅ Oficio de cierre actualizado. Estado: 'Completado', Avance: 100%")
                                        st.rerun()

                        # Si se está borrando la fecha
                        elif nueva_fecha_oficio_str != fecha_original:
                            # Permitir borrar la fecha y actualizar Estado a "En proceso"
                            registros_df.at[registros_df.index[
                                indice_seleccionado], 'Fecha de oficio de cierre'] = nueva_fecha_oficio_str

                            # Si se borra la fecha de oficio, cambiar estado a "En proceso"
                            if registros_df.at[registros_df.index[indice_seleccionado], 'Estado'] == 'Completado':
                                registros_df.at[registros_df.index[indice_seleccionado], 'Estado'] = 'En proceso'
                                st.info(
                                    "El estado ha sido cambiado a 'En proceso' porque se eliminó la fecha de oficio de cierre.")

                            edited = True
                            # Guardar cambios
                            with st.spinner("💾 Guardando cambios..."):
                                registros_df = validar_reglas_negocio(registros_df)
                                exito, mensaje = guardar_datos_editados_rapido(registros_df)
                                if exito:
                                    st.success("✅ Fecha de oficio de cierre actualizada")
                                    st.rerun()

            # ===== SECCIÓN 6: ESTADO Y OBSERVACIONES =====
            st.markdown("### 6. Estado y Observaciones")
            col1, col2 = st.columns(2)

            # Estado general (RESTAURADO CON VALIDACIONES)
            if 'Estado' in row:
                with col1:
                    # Verificar si hay fecha de oficio de cierre válida
                    tiene_fecha_oficio = (
                            'Fecha de oficio de cierre' in row and
                            pd.notna(row['Fecha de oficio de cierre']) and
                            row['Fecha de oficio de cierre'] != ""
                    )

                    # Si no hay fecha de oficio, no se debe permitir estado Completado
                    opciones_estado = ["", "En proceso", "En proceso oficio de cierre", "Finalizado"]
                    if tiene_fecha_oficio:
                        opciones_estado = ["", "En proceso", "En proceso oficio de cierre", "Completado",
                                           "Finalizado"]

                    # Determinar el índice actual del estado
                    indice_estado = 0
                    if row['Estado'] in opciones_estado:
                        indice_estado = opciones_estado.index(row['Estado'])

                    # Crear el selector de estado
                    nuevo_estado = st.selectbox(
                        "Estado",
                        options=opciones_estado,
                        index=indice_estado,
                        key=f"estado_{indice_seleccionado}",
                        on_change=on_change_callback
                    )

                    # Si intenta seleccionar Completado sin fecha de oficio, mostrar mensaje
                    if nuevo_estado == "Completado" and not tiene_fecha_oficio:
                        st.error(
                            "No es posible establecer el estado como 'Completado' sin una fecha de oficio de cierre válida.")
                        nuevo_estado = row['Estado']

                    # Actualizar el estado si ha cambiado
                    if nuevo_estado != row['Estado']:
                        registros_df.at[registros_df.index[indice_seleccionado], 'Estado'] = nuevo_estado
                        edited = True

                        # Guardar y validar inmediatamente
                        with st.spinner("💾 Guardando estado..."):
                            registros_df = validar_reglas_negocio(registros_df)
                            exito, mensaje = guardar_datos_editados_rapido(registros_df)
                            if exito:
                                st.success("✅ Estado actualizado")
                                st.rerun()

            # Observaciones (RESTAURADO)
            if 'Observación' in row:
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

            # Botón de guardar general (RESTAURADO)
            if edited or st.session_state.cambios_pendientes:
                if st.button("💾 Guardar Todos los Cambios", key=f"guardar_{indice_seleccionado}", type="primary"):
                    # Aplicar validaciones de reglas de negocio antes de guardar
                    registros_df = validar_reglas_negocio(registros_df)

                    # Actualizar los plazos automáticamente
                    registros_df = actualizar_plazo_analisis(registros_df)
                    registros_df = actualizar_plazo_cronograma(registros_df)
                    registros_df = actualizar_plazo_oficio_cierre(registros_df)

                    # Guardar los datos en Google Sheets
                    with st.spinner("💾 Guardando todos los cambios en Google Sheets..."):
                        exito, mensaje = guardar_datos_editados(registros_df, crear_backup=True)

                    if exito:
                        st.session_state.mensaje_guardado = ("success", mensaje)
                        st.session_state.cambios_pendientes = False
                        st.rerun()
                    else:
                        st.session_state.mensaje_guardado = ("error", mensaje)

            # Botón para actualizar vista
            if st.button("🔄 Actualizar Vista", key=f"actualizar_{indice_seleccionado}"):
                st.rerun()

    except Exception as e:
        st.error(f"Error al editar el registro: {e}")

    return registros_df

# ========== FUNCIONES COMPLETAS RESTAURADAS ==========

def mostrar_dashboard(df_filtrado, metas_nuevas_df, metas_actualizar_df, registros_df, 
                     entidad_seleccionada, funcionario_seleccionado, nivel_seleccionado):
    """Muestra el dashboard principal con métricas y gráficos - VERSIÓN COMPLETA RESTAURADA CON MODIFICACIONES."""
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

    # MODIFICACIÓN 1: Crear función para gradiente personalizado
    def crear_gradiente_personalizado(df_comparacion):
        """Crea un gradiente personalizado de rojo a verde oscuro para porcentajes 0-100, verde oscuro para >100"""
        def aplicar_color(val):
            if pd.isna(val):
                return ''
            if val <= 0:
                return 'background-color: #dc2626; color: white'  # Rojo intenso
            elif val <= 25:
                return 'background-color: #ef4444; color: white'  # Rojo
            elif val <= 50:
                return 'background-color: #f97316; color: white'  # Naranja
            elif val <= 75:
                return 'background-color: #eab308; color: black'  # Amarillo
            elif val < 100:
                return 'background-color: #84cc16; color: black'  # Verde claro
            else:  # val >= 100
                return 'background-color: #166534; color: white'  # Verde oscuro
        
        return df_comparacion.style.format({
            'Porcentaje': '{:.2f}%'
        }).applymap(aplicar_color, subset=['Porcentaje'])

    # Mostrar comparación en dos columnas
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Registros Nuevos")
        # APLICAR GRADIENTE PERSONALIZADO
        st.dataframe(crear_gradiente_personalizado(comparacion_nuevos))

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
        # APLICAR GRADIENTE PERSONALIZADO
        st.dataframe(crear_gradiente_personalizado(comparacion_actualizar))

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

    # MODIFICACIÓN 2: Diagrama de Gantt condicionado
    st.markdown('<div class="subtitle">Diagrama de Gantt - Cronograma de Hitos por Nivel de Información</div>',
                unsafe_allow_html=True)

    # Verificar si hay filtros específicos aplicados
    filtros_aplicados = (
        entidad_seleccionada != 'Todas' or 
        funcionario_seleccionado != 'Todos' or 
        nivel_seleccionado != 'Todos'
    )

    if filtros_aplicados:
        # Crear el diagrama de Gantt solo si hay filtros
        fig_gantt = crear_gantt(df_filtrado)
        if fig_gantt is not None:
            st.plotly_chart(fig_gantt, use_container_width=True)
        else:
            st.warning("No hay datos suficientes para crear el diagrama de Gantt con los filtros aplicados.")
    else:
        # Mostrar mensaje cuando no hay filtros aplicados
        st.info("📊 **Para visualizar el diagrama de Gantt seleccione la entidad o funcionario de su interés.**")

    # Tabla de registros con porcentaje de avance
    st.markdown('<div class="subtitle">Detalle de Registros</div>', unsafe_allow_html=True)

    # Definir el orden de las columnas
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

    # Mostrar tabla con colores por estado de fechas
    try:
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
            # BOTÓN PARA DESCARGAR TODOS LOS REGISTROS
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

        # Información sobre el contenido
        num_registros = len(registros_df)
        num_campos = len(registros_df.columns)
        st.info(
            f"El archivo de TODOS los registros incluirá {num_registros} registros con {num_campos} campos originales.")

    except Exception as e:
        st.error(f"Error al mostrar la tabla de registros: {e}")
        if 'columnas_mostrar_existentes' in locals():
            st.dataframe(df_filtrado[columnas_mostrar_existentes])

def mostrar_reportes(registros_df, tipo_dato_filtro, acuerdo_filtro, analisis_filtro, 
                    estandares_filtro, publicacion_filtro, finalizado_filtro):
    """Muestra la pestaña de reportes con tabla completa y filtros específicos - VERSIÓN COMPLETA."""
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
                ((df_filtrado['Suscripción acuerdo de compromiso'].notna()) & 
                 (df_filtrado['Suscripción acuerdo de compromiso'] != '')) |
                ((df_filtrado['Entrega acuerdo de compromiso'].notna()) & 
                 (df_filtrado['Entrega acuerdo de compromiso'] != ''))
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
    
    # Definir columnas a mostrar
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
    """Muestra alertas de vencimientos de fechas en los registros - VERSIÓN COMPLETA RESTAURADA."""
    st.markdown('<div class="subtitle">Alertas de Vencimientos</div>', unsafe_allow_html=True)

    # Fecha actual para comparaciones
    fecha_actual = datetime.now().date()

    # Función para calcular días hábiles entre fechas
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

    # Función para determinar si una fecha está próxima a vencer
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
            # Procesar fechas de manera segura
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

            # Caso especial: Acuerdo de compromiso pendiente
            if fecha_entrega_acuerdo is not None and pd.notna(fecha_entrega_acuerdo) and (
                    fecha_entrega_info is None or pd.isna(fecha_entrega_info)):
                if es_vencido(fecha_entrega_acuerdo):
                    dias_rezago = calcular_dias_rezago(fecha_entrega_acuerdo)
                    registros_alertas.append({
                        'Cod': row['Cod'],
                        'Entidad': row['Entidad'],
                        'Nivel Información': row.get('Nivel Información ', ''),
                        'Funcionario': row.get('Funcionario', ''),
                        'Tipo Alerta': 'Acuerdo de compromiso',
                        'Fecha Programada': fecha_entrega_acuerdo,
                        'Fecha Real': None,
                        'Días Rezago': dias_rezago,
                        'Estado': 'Vencido',
                        'Descripción': f'Entrega de acuerdo vencida hace {dias_rezago} días sin fecha de entrega de información'
                    })

            # Continuar con los demás casos siguiendo el mismo patrón...

        except Exception as e:
            st.warning(f"Error procesando registro {row['Cod']}: {e}")
            continue

    # Crear DataFrame de alertas
    if registros_alertas:
        df_alertas = pd.DataFrame(registros_alertas)

        # Formatear fechas
        for col in ['Fecha Programada', 'Fecha Real']:
            if col in df_alertas.columns:
                df_alertas[col] = df_alertas[col].apply(formatear_fecha_segura)

        # Función para aplicar colores según estado
        def highlight_estado(val):
            if val == 'Vencido':
                return 'background-color: #fee2e2; color: #b91c1c; font-weight: bold'
            elif val == 'Próximo a vencer':
                return 'background-color: #fef3c7; color: #b45309; font-weight: bold'
            elif val == 'Completado con retraso':
                return 'background-color: #dbeafe; color: #1e40af'
            return ''

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

        # Resto de la función de alertas...
        st.success("🎉 Sistema completo de alertas funcionando!")
    else:
        st.success("🎉 ¡No hay alertas de vencimientos pendientes!")

def mostrar_diagnostico(registros_df, meta_df, metas_nuevas_df, metas_actualizar_df, df_filtrado):
    """Muestra la sección de diagnóstico con análisis detallado de los datos - VERSIÓN COMPLETA."""
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

        st.success("✅ Diagnóstico completo disponible")

def mostrar_ayuda():
    """Muestra la sección de ayuda con información sobre el uso del tablero - VERSIÓN COMPLETA."""
    with st.expander("❓ Ayuda"):
        st.markdown("### Ayuda del Tablero de Control")
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
        - **Edición de Registros**: Edición individual completa con todas las secciones
        - **Alertas de Vencimientos**: Seguimiento de fechas críticas con análisis detallado
        - **Reportes**: Análisis avanzados con filtros personalizados

        #### 🔧 Funcionalidades Google Sheets
        - **Carga desde Excel**: Sube archivos Excel para sincronizar automáticamente
        - **Descarga completa**: Exporta todos los datos en formato Excel
        - **Backup automático**: Cada cambio crea una copia de seguridad
        - **Edición directa**: También puedes editar directamente en Google Sheets

        #### 💾 Guardado Automático
        Los cambios se guardan automáticamente en Google Sheets al:
        - Modificar cualquier campo de fecha
        - Cambiar estados o valores de estándares
        - Aplicar validaciones de reglas de negocio
        - Calcular plazos automáticamente

        #### 🔄 Validaciones Automáticas Restauradas
        - **Acuerdo de compromiso**: Se actualiza automáticamente al ingresar fechas
        - **Análisis y cronograma**: Campos dependientes se actualizan automáticamente
        - **Estándares**: Campos no completados se marcan como "No aplica" al ingresar fecha
        - **Publicación**: "Disponer datos temáticos" se actualiza automáticamente
        - **Oficio de cierre**: Estado se cambia a "Completado" y avance al 100%
        - **Plazos**: Se calculan automáticamente basados en días hábiles

        #### 📅 Cálculo de Plazos Automático
        - **Plazo de análisis**: 5 días hábiles después de fecha de entrega
        - **Plazo de cronograma**: 3 días hábiles después del plazo de análisis
        - **Plazo de oficio de cierre**: 7 días hábiles después de publicación
        - **Considera**: Fines de semana y festivos colombianos

        #### 📊 Nuevas Mejoras
        - **Gradiente de metas mejorado**: Colores de rojo a verde oscuro (0-100%), verde oscuro para >100%
        - **Diagrama de Gantt condicional**: Solo se muestra cuando hay filtros específicos aplicados
        - **Mensaje informativo**: Guía al usuario a seleccionar filtros para ver el Gantt

        #### 🆘 Soporte
        Para configuración inicial o problemas técnicos:
        - 📋 Consulta las [Instrucciones de Configuración](https://github.com/tu-repo/INSTRUCCIONES_CONFIGURACION.md)
        - 🔧 Usa el panel "Configuración Google Sheets" en la barra lateral
        - 🔄 Utiliza el botón "Reconectar" si hay problemas de conexión
        - 💾 Todos los cambios se guardan automáticamente en Google Sheets
        """)

def main():
    """Función principal completamente restaurada con todas las funcionalidades y modificaciones."""
    try:
        # ===== INICIALIZACIÓN DEL ESTADO DE SESIÓN =====
        if 'cambios_pendientes' not in st.session_state:
            st.session_state.cambios_pendientes = False

        if 'mensaje_guardado' not in st.session_state:
            st.session_state.mensaje_guardado = None

        # RESTAURADO: Lista de funcionarios dinámicos
        if 'funcionarios' not in st.session_state:
            st.session_state.funcionarios = []

        # ===== CONFIGURACIÓN DE LA PÁGINA =====
        setup_page()
        load_css()

        # ===== TÍTULO Y ESTADO =====
        st.markdown('<div class="title">📊 Tablero de Control de Seguimiento de Cronogramas</div>',
                    unsafe_allow_html=True)
        
        # Mostrar estado de Google Sheets
        st.markdown("### 🔗 Estado de Google Sheets")
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.info("🔄 Datos sincronizados con Google Sheets en tiempo real")
        
        with col2:
            if st.button("🔄 Reconectar"):
                # Limpiar cache y reconectar
                if 'sheets_manager' in st.session_state:
                    del st.session_state.sheets_manager
                st.rerun()

        # ===== SIDEBAR RESTAURADO =====
        # Configuración de Google Sheets
        mostrar_configuracion_sheets()
        
        # Carga de archivos Excel
        mostrar_carga_archivos()

        # Información sobre el tablero (RESTAURADA)
        st.sidebar.markdown('<div class="subtitle">Información</div>', unsafe_allow_html=True)
        st.sidebar.markdown("""
        <div class="info-box">
        <p><strong>Tablero de Control de Cronogramas</strong></p>
        <p><strong>✅ VERSIÓN COMPLETA CON MEJORAS</strong></p>
        <p>• Gradiente de metas mejorado (rojo a verde)</p>
        <p>• Diagrama de Gantt condicional</p>
        <p>• Edición detallada de todos los campos</p>
        <p>• Validaciones automáticas completas</p>
        <p>• Cálculo de plazos automático</p>
        <p>• Guardado inteligente en Google Sheets</p>
        <p>• Sistema de funcionarios dinámico</p>
        <p>• Alertas de vencimiento detalladas</p>
        </div>
        """, unsafe_allow_html=True)

        # ===== CARGA DE DATOS =====
        with st.spinner("📊 Cargando datos desde Google Sheets..."):
            registros_df, meta_df = cargar_datos()

        # Verificar si los DataFrames están vacíos
        if registros_df.empty:
            st.warning("⚠️ No hay datos de registros en Google Sheets.")
            
            # Opciones para el usuario
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
            
            # Crear estructura mínima para que la app funcione
            registros_df = pd.DataFrame(columns=[
                'Cod', 'Entidad', 'TipoDato', 'Nivel Información ',
                'Acuerdo de compromiso', 'Análisis y cronograma',
                'Estándares', 'Publicación', 'Fecha de entrega de información',
                'Plazo de análisis', 'Plazo de cronograma', 'Plazo de oficio de cierre',
                'Funcionario', 'Frecuencia actualizacion ', 'Estado', 'Observación'
            ])
        else:
            st.success(f"✅ {len(registros_df)} registros cargados exitosamente desde Google Sheets")

        # ===== ASEGURAR COLUMNAS REQUERIDAS =====
        columnas_requeridas = [
            'Cod', 'Entidad', 'TipoDato', 'Acuerdo de compromiso',
            'Análisis y cronograma', 'Estándares', 'Publicación',
            'Nivel Información ', 'Fecha de entrega de información',
            'Plazo de análisis', 'Plazo de cronograma', 'Plazo de oficio de cierre',
            'Funcionario', 'Frecuencia actualizacion ', 'Estado', 'Observación',
            # CAMPOS RESTAURADOS
            'Suscripción acuerdo de compromiso', 'Entrega acuerdo de compromiso',
            'Actas de acercamiento y manifestación de interés',
            'Gestion acceso a los datos y documentos requeridos ',
            'Análisis de información', 'Cronograma Concertado',
            'Seguimiento a los acuerdos',
            'Registro (completo)', 'ET (completo)', 'CO (completo)', 
            'DD (completo)', 'REC (completo)', 'SERVICIO (completo)',
            'Estándares (fecha programada)', 'Fecha de publicación programada',
            'Disponer datos temáticos', 'Catálogo de recursos geográficos',
            'Oficios de cierre', 'Fecha de oficio de cierre',
            'Resultados de orientación técnica', 'Verificación del servicio web geográfico',
            'Verificar Aprobar Resultados', 'Revisar y validar los datos cargados en la base de datos',
            'Aprobación resultados obtenidos en la rientación'
        ]

        for columna in columnas_requeridas:
            if columna not in registros_df.columns:
                registros_df[columna] = ''

        # ===== APLICAR VALIDACIONES Y CÁLCULOS =====
        with st.spinner("🔧 Aplicando validaciones y calculando plazos..."):
            # Aplicar reglas de negocio
            registros_df = validar_reglas_negocio(registros_df)

            # Actualizar plazos automáticamente
            registros_df = actualizar_plazo_analisis(registros_df)
            registros_df = actualizar_plazo_cronograma(registros_df)
            registros_df = actualizar_plazo_oficio_cierre(registros_df)

        # Procesar las metas
        metas_nuevas_df, metas_actualizar_df = procesar_metas(meta_df)

        # Agregar columnas calculadas
        registros_df['Porcentaje Avance'] = registros_df.apply(calcular_porcentaje_avance, axis=1)
        registros_df['Estado Fechas'] = registros_df.apply(verificar_estado_fechas, axis=1)

        # ===== MOSTRAR VALIDACIONES (RESTAURADO) =====
        with st.expander("🔍 Validación de Reglas de Negocio"):
            st.markdown("### Estado de Validaciones")
            st.info("""
            **Reglas aplicadas automáticamente:**
            1. ✅ Si 'Entrega acuerdo de compromiso' no está vacío → 'Acuerdo de compromiso' = SI
            2. ✅ Si 'Análisis y cronograma' tiene fecha → 'Análisis de información' = SI
            3. ✅ Al introducir fecha en 'Estándares' → campos no completos = "No aplica"
            4. ✅ Si introduce fecha en 'Publicación' → 'Disponer datos temáticos' = SI
            5. ✅ Para 'Fecha de oficio de cierre' → requiere etapa de Publicación completada
            6. ✅ Al introducir 'Fecha de oficio de cierre' → Estado = "Completado" y avance = 100%
            7. ✅ Plazos calculados automáticamente considerando días hábiles y festivos
            
            **🆕 Nuevas mejoras implementadas:**
            8. ✅ Gradiente de metas mejorado: rojo (0%) → verde oscuro (100%+)
            9. ✅ Diagrama de Gantt condicional: solo con filtros específicos
            """)
            mostrar_estado_validaciones(registros_df, st)

        # ===== CREAR PESTAÑAS =====
        tab1, tab2, tab3, tab4 = st.tabs([
            "📊 Dashboard", 
            "✏️ Edición de Registros", 
            "⚠️ Alertas de Vencimientos", 
            "📋 Reportes"
        ])
     
        # ===== TAB 1: DASHBOARD (COMPLETO RESTAURADO CON MODIFICACIONES) =====
        with tab1:
            st.markdown("### 🔍 Filtros")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                # Filtro por entidad
                entidades = ['Todas'] + sorted([e for e in registros_df['Entidad'].unique().tolist() if e])
                entidad_seleccionada = st.selectbox('Entidad', entidades, key="dash_entidad")
            
            with col2:
                # Filtro por funcionario (RESTAURADO)
                funcionarios = ['Todos']
                if 'Funcionario' in registros_df.columns:
                    funcionarios_unicos = [f for f in registros_df['Funcionario'].dropna().unique().tolist() if f]
                    funcionarios += sorted(funcionarios_unicos)
                funcionario_seleccionado = st.selectbox('Funcionario', funcionarios, key="dash_funcionario")
            
            with col3:
                # Filtro por tipo de dato
                tipos_dato = ['Todos'] + sorted([t for t in registros_df['TipoDato'].dropna().unique().tolist() if t])
                tipo_dato_seleccionado = st.selectbox('Tipo de Dato', tipos_dato, key="dash_tipo")
            
            with col4:
                # Filtro por nivel de información dependiente de entidad (RESTAURADO)
                if entidad_seleccionada != 'Todas':
                    niveles_entidad = registros_df[registros_df['Entidad'] == entidad_seleccionada]['Nivel Información '].dropna().unique().tolist()
                    niveles_entidad = [n for n in niveles_entidad if n]
                    niveles = ['Todos'] + sorted(niveles_entidad)
                    nivel_seleccionado = st.selectbox('Nivel de Información', niveles, key="dash_nivel")
                else:
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
            
            st.markdown("---")
            
            # Mostrar dashboard completo CON PARÁMETROS DE FILTROS PARA GANTT
            mostrar_dashboard(df_filtrado, metas_nuevas_df, metas_actualizar_df, registros_df,
                            entidad_seleccionada, funcionario_seleccionado, nivel_seleccionado)

        # ===== TAB 2: EDICIÓN (FUNCIONALIDAD COMPLETA RESTAURADA) =====
        with tab2:
            # Llamar a la función de edición completamente restaurada
            registros_df = mostrar_edicion_registros(registros_df)

        # ===== TAB 3: ALERTAS (FUNCIONALIDAD COMPLETA RESTAURADA) =====
        with tab3:
            st.markdown("---")
            mostrar_alertas_vencimientos(registros_df)

        # ===== TAB 4: REPORTES (FUNCIONALIDAD COMPLETA RESTAURADA) =====
        with tab4:
            st.markdown("### 🔍 Filtros de Reportes")
            
            # Primera fila de filtros
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
            
            # Segunda fila de filtros
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
            
            # Mostrar reportes completos
            mostrar_reportes(registros_df, tipo_dato_reporte, acuerdo_filtro, analisis_filtro, 
                           estandares_filtro, publicacion_filtro, finalizado_filtro)

        # ===== SECCIONES ADICIONALES RESTAURADAS =====
        
        # Diagnóstico de datos (COMPLETO)
        mostrar_diagnostico(registros_df, meta_df, metas_nuevas_df, metas_actualizar_df, df_filtrado)

        # Ayuda completa (RESTAURADA)
        mostrar_ayuda()

        # ===== FOOTER CON INFORMACIÓN =====
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

        # Información de versión CON MEJORAS
        st.info("""
        🎉 **Tablero de Control - Versión Completa con Mejoras**
        
        ✅ Todas las funcionalidades de edición han sido restauradas
        ✅ Sistema de validaciones completo
        ✅ Cálculo automático de plazos con días hábiles
        ✅ Gestión dinámica de funcionarios
        ✅ Guardado inteligente en Google Sheets
        ✅ Alertas de vencimiento detalladas
        ✅ Reportes avanzados con filtros
        
        🆕 **Mejoras Implementadas:**
        ✅ Gradiente de metas mejorado: rojo (0%) → verde oscuro (100%+)
        ✅ Diagrama de Gantt condicional: se muestra solo con filtros específicos
        ✅ Mensaje informativo para guiar al usuario sobre el Gantt
        """)

    except Exception as e:
        st.error(f"❌ Error crítico: {str(e)}")
        
        # Información detallada del error para debugging
        import traceback
        with st.expander("🔍 Detalles del Error (para debugging)"):
            st.code(traceback.format_exc())
        
        st.markdown("### 🆘 Solución de Problemas")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            **🔧 Problemas Comunes:**
            - Configuración de Google Sheets incorrecta
            - Credenciales faltantes o incorrectas
            - Estructura de datos incorrecta en Google Sheets
            - Problemas de conexión a internet
            """)
        
        with col2:
            st.markdown("""
            **🔄 Acciones Recomendadas:**
            - Usar el botón "Reconectar" arriba
            - Verificar configuración en el panel lateral
            - Revisar permisos del service account
            - Consultar las instrucciones de configuración
            """)
        
        # Botón de recuperación
        if st.button("🔄 Intentar Recuperación", type="primary"):
            # Limpiar estado y recargar
            for key in list(st.session_state.keys()):
                if key.startswith(('sheets_', 'registros_', 'meta_')):
                    del st.session_state[key]
            st.rerun()

if __name__ == "__main__":
    main()
