# -*- coding: utf-8 -*-
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
    contar_registros_completados_por_fecha
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
    try:
        if 'Estado Fechas' in s and pd.notna(s['Estado Fechas']):
            if s['Estado Fechas'] == 'vencido':
                return ['background-color: #fee2e2'] * len(s)
            elif s['Estado Fechas'] == 'proximo':
                return ['background-color: #fef3c7'] * len(s)
        return ['background-color: #ffffff'] * len(s)
    except (KeyError, TypeError, AttributeError):
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
        st.markdown("[Ver instrucciones completas](https://github.com/tu-repo/INSTRUCCIONES_CONFIGURACION.md)")
        st.info("Los datos se guardan de forma segura en Google Sheets con autenticación OAuth2")

def mostrar_edicion_registros(registros_df):
    """Muestra la pestaña de edición de registros - VERSIÓN COMPLETA RESTAURADA CON TODAS LAS SECCIONES."""
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
    if 'mensaje_guardado' in st.session_state and st.session_state.mensaje_guardado:
        if st.session_state.mensaje_guardado[0] == "success":
            st.success(st.session_state.mensaje_guardado[1])
        else:
            st.error(st.session_state.mensaje_guardado[1])
        # Limpiar mensaje después de mostrarlo
        st.session_state.mensaje_guardado = None

    st.markdown("### Edición Individual de Registros")

    # Verificar que hay registros para editar
    if registros_df.empty:
        st.warning("No hay registros disponibles para editar.")
        return registros_df

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
                tipo_actual = row.get('TipoDato', '')
                tipo_index = 0 if tipo_actual.upper() == "NUEVO" else 1 if tipo_actual.upper() == "ACTUALIZAR" else 0
                nuevo_tipo = st.selectbox(
                    "Tipo de Dato",
                    options=["Nuevo", "Actualizar"],
                    index=tipo_index,
                    key=f"tipo_{indice_seleccionado}",
                    on_change=on_change_callback
                )
                if nuevo_tipo != row.get('TipoDato', ''):
                    registros_df.at[registros_df.index[indice_seleccionado], 'TipoDato'] = nuevo_tipo
                    edited = True

            with col3:
                # Mes Proyectado - NUEVA COLUMNA
                meses = ["", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", 
                        "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
                
                mes_actual = row.get('Mes Proyectado', '') if pd.notna(row.get('Mes Proyectado', '')) else ""
                mes_index = 0
                if mes_actual and mes_actual in meses:
                    mes_index = meses.index(mes_actual)
                
                nuevo_mes = st.selectbox(
                    "Mes Proyectado",
                    options=meses,
                    index=mes_index,
                    key=f"mes_proyectado_{indice_seleccionado}",
                    on_change=on_change_callback
                )
                if nuevo_mes != row.get('Mes Proyectado', ''):
                    registros_df.at[registros_df.index[indice_seleccionado], 'Mes Proyectado'] = nuevo_mes
                    edited = True

            # Frecuencia de actualización y Funcionario
            col1, col2 = st.columns(2)
            with col1:
                freq_actual = row.get('Frecuencia actualizacion ', '')
                freq_opciones = ["", "Diaria", "Semanal", "Mensual", "Trimestral", "Semestral", "Anual"]
                freq_index = freq_opciones.index(freq_actual) if freq_actual in freq_opciones else 0
                nueva_frecuencia = st.selectbox(
                    "Frecuencia de actualización",
                    options=freq_opciones,
                    index=freq_index,
                    key=f"frecuencia_{indice_seleccionado}",
                    on_change=on_change_callback
                )
                if nueva_frecuencia != row.get('Frecuencia actualizacion ', ''):
                    registros_df.at[registros_df.index[indice_seleccionado], 'Frecuencia actualizacion '] = nueva_frecuencia
                    edited = True

            # Funcionario - SISTEMA DINÁMICO RESTAURADO
            with col2:
                # Inicializar la lista de funcionarios si es la primera vez
                if 'funcionarios' not in st.session_state:
                    st.session_state.funcionarios = []
                
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
                if pd.notna(row.get('Funcionario', '')) and row.get('Funcionario', '') in opciones_funcionarios:
                    indice_funcionario = opciones_funcionarios.index(row.get('Funcionario', ''))

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

            # ===== SECCIÓN 2: ACUERDOS Y COMPROMISOS =====
            st.markdown("---")
            st.markdown("### 2. Acuerdos y Compromisos")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Actas de acercamiento
                nueva_acta = st.selectbox(
                    "Actas de acercamiento y manifestación de interés",
                    options=["", "Si", "No"],
                    index=["", "Si", "No"].index(row.get('Actas de acercamiento y manifestación de interés', '')) 
                          if row.get('Actas de acercamiento y manifestación de interés', '') in ["", "Si", "No"] else 0,
                    key=f"acta_{indice_seleccionado}",
                    on_change=on_change_callback
                )
                if nueva_acta != row.get('Actas de acercamiento y manifestación de interés', ''):
                    registros_df.at[registros_df.index[indice_seleccionado], 'Actas de acercamiento y manifestación de interés'] = nueva_acta
                    edited = True

                # Suscripción acuerdo de compromiso - SELECTOR DE FECHA
                fecha_suscripcion_actual = fecha_para_selector(row.get('Suscripción acuerdo de compromiso', ''))
                nueva_fecha_suscripcion = st.date_input(
                    "Suscripción acuerdo de compromiso",
                    value=fecha_suscripcion_actual,
                    key=f"suscripcion_{indice_seleccionado}",
                    on_change=on_change_callback
                )
                fecha_suscripcion_str = fecha_desde_selector_a_string(nueva_fecha_suscripcion)
                if fecha_suscripcion_str != formatear_fecha(row.get('Suscripción acuerdo de compromiso', '')):
                    registros_df.at[registros_df.index[indice_seleccionado], 'Suscripción acuerdo de compromiso'] = fecha_suscripcion_str
                    edited = True

            with col2:
                # Entrega acuerdo de compromiso - SELECTOR DE FECHA
                fecha_entrega_actual = fecha_para_selector(row.get('Entrega acuerdo de compromiso', ''))
                nueva_fecha_entrega = st.date_input(
                    "Entrega acuerdo de compromiso",
                    value=fecha_entrega_actual,
                    key=f"entrega_{indice_seleccionado}",
                    on_change=on_change_callback
                )
                fecha_entrega_str = fecha_desde_selector_a_string(nueva_fecha_entrega)
                if fecha_entrega_str != formatear_fecha(row.get('Entrega acuerdo de compromiso', '')):
                    registros_df.at[registros_df.index[indice_seleccionado], 'Entrega acuerdo de compromiso'] = fecha_entrega_str
                    edited = True

                # Acuerdo de compromiso - SELECTBOX
                nuevo_acuerdo = st.selectbox(
                    "Acuerdo de compromiso",
                    options=["", "Si", "No"],
                    index=["", "Si", "No"].index(row.get('Acuerdo de compromiso', '')) 
                          if row.get('Acuerdo de compromiso', '') in ["", "Si", "No"] else 0,
                    key=f"acuerdo_{indice_seleccionado}",
                    on_change=on_change_callback
                )
                if nuevo_acuerdo != row.get('Acuerdo de compromiso', ''):
                    registros_df.at[registros_df.index[indice_seleccionado], 'Acuerdo de compromiso'] = nuevo_acuerdo
                    edited = True

            # ===== SECCIÓN 3: GESTIÓN DE INFORMACIÓN =====
            st.markdown("---")
            st.markdown("### 3. Gestión de Información")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                # Gestión acceso a datos
                nueva_gestion = st.selectbox(
                    "Gestión acceso a los datos y documentos requeridos",
                    options=["", "Si", "No"],
                    index=["", "Si", "No"].index(row.get('Gestion acceso a los datos y documentos requeridos ', '')) 
                          if row.get('Gestion acceso a los datos y documentos requeridos ', '') in ["", "Si", "No"] else 0,
                    key=f"gestion_{indice_seleccionado}",
                    on_change=on_change_callback
                )
                if nueva_gestion != row.get('Gestion acceso a los datos y documentos requeridos ', ''):
                    registros_df.at[registros_df.index[indice_seleccionado], 'Gestion acceso a los datos y documentos requeridos '] = nueva_gestion
                    edited = True

            with col2:
                # Fecha de entrega de información - SELECTOR DE FECHA
                fecha_entrega_info_actual = fecha_para_selector(row.get('Fecha de entrega de información', ''))
                nueva_fecha_entrega_info = st.date_input(
                    "Fecha de entrega de información",
                    value=fecha_entrega_info_actual,
                    key=f"entrega_info_{indice_seleccionado}",
                    on_change=on_change_callback
                )
                fecha_entrega_info_str = fecha_desde_selector_a_string(nueva_fecha_entrega_info)
                if fecha_entrega_info_str != formatear_fecha(row.get('Fecha de entrega de información', '')):
                    registros_df.at[registros_df.index[indice_seleccionado], 'Fecha de entrega de información'] = fecha_entrega_info_str
                    edited = True

            with col3:
                # Plazo de análisis - CALCULADO AUTOMÁTICAMENTE
                plazo_analisis_actual = row.get('Plazo de análisis', '')
                st.text_input(
                    "Plazo de análisis (calculado automáticamente)",
                    value=plazo_analisis_actual,
                    disabled=True,
                    key=f"plazo_analisis_{indice_seleccionado}",
                    help="Se calcula automáticamente como 5 días hábiles después de la fecha de entrega de información"
                )

            # ===== SECCIÓN 4: ANÁLISIS Y CRONOGRAMA =====
            st.markdown("---")
            st.markdown("### 4. Análisis y Cronograma")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                # Análisis de información
                nuevo_analisis_info = st.selectbox(
                    "Análisis de información",
                    options=["", "Si", "No"],
                    index=["", "Si", "No"].index(row.get('Análisis de información', '')) 
                          if row.get('Análisis de información', '') in ["", "Si", "No"] else 0,
                    key=f"analisis_info_{indice_seleccionado}",
                    on_change=on_change_callback
                )
                if nuevo_analisis_info != row.get('Análisis de información', ''):
                    registros_df.at[registros_df.index[indice_seleccionado], 'Análisis de información'] = nuevo_analisis_info
                    edited = True

            with col2:
                # Cronograma Concertado
                nuevo_cronograma = st.selectbox(
                    "Cronograma Concertado",
                    options=["", "Si", "No"],
                    index=["", "Si", "No"].index(row.get('Cronograma Concertado', '')) 
                          if row.get('Cronograma Concertado', '') in ["", "Si", "No"] else 0,
                    key=f"cronograma_{indice_seleccionado}",
                    on_change=on_change_callback
                )
                if nuevo_cronograma != row.get('Cronograma Concertado', ''):
                    registros_df.at[registros_df.index[indice_seleccionado], 'Cronograma Concertado'] = nuevo_cronograma
                    edited = True

            with col3:
                # Plazo de cronograma - CALCULADO AUTOMÁTICAMENTE
                plazo_cronograma_actual = row.get('Plazo de cronograma', '')
                st.text_input(
                    "Plazo de cronograma (calculado automáticamente)",
                    value=plazo_cronograma_actual,
                    disabled=True,
                    key=f"plazo_cronograma_{indice_seleccionado}",
                    help="Se calcula automáticamente como 3 días hábiles después del plazo de análisis"
                )

            with col4:
                # Seguimiento a los acuerdos
                nuevo_seguimiento = st.selectbox(
                    "Seguimiento a los acuerdos",
                    options=["", "Si", "No"],
                    index=["", "Si", "No"].index(row.get('Seguimiento a los acuerdos', '')) 
                          if row.get('Seguimiento a los acuerdos', '') in ["", "Si", "No"] else 0,
                    key=f"seguimiento_{indice_seleccionado}",
                    on_change=on_change_callback
                )
                if nuevo_seguimiento != row.get('Seguimiento a los acuerdos', ''):
                    registros_df.at[registros_df.index[indice_seleccionado], 'Seguimiento a los acuerdos'] = nuevo_seguimiento
                    edited = True

            # Análisis y cronograma fecha - SELECTOR DE FECHA
            col1, col2 = st.columns(2)
            with col1:
                fecha_analisis_actual = fecha_para_selector(row.get('Análisis y cronograma', ''))
                nueva_fecha_analisis = st.date_input(
                    "Análisis y cronograma (fecha real)",
                    value=fecha_analisis_actual,
                    key=f"analisis_fecha_{indice_seleccionado}",
                    on_change=on_change_callback
                )
                fecha_analisis_str = fecha_desde_selector_a_string(nueva_fecha_analisis)
                if fecha_analisis_str != formatear_fecha(row.get('Análisis y cronograma', '')):
                    registros_df.at[registros_df.index[indice_seleccionado], 'Análisis y cronograma'] = fecha_analisis_str
                    edited = True

            # ===== SECCIÓN 5: ESTÁNDARES =====
            st.markdown("---")
            st.markdown("### 5. Estándares")
            
            # Los 6 campos de estándares completos
            st.markdown("#### Completitud de Estándares")
            col1, col2, col3 = st.columns(3)
            
            campos_estandares = [
                ('Registro (completo)', 'registro'),
                ('ET (completo)', 'et'),
                ('CO (completo)', 'co'),
                ('DD (completo)', 'dd'),
                ('REC (completo)', 'rec'),
                ('SERVICIO (completo)', 'servicio')
            ]
            
            for i, (campo, key_suffix) in enumerate(campos_estandares):
                col = [col1, col2, col3][i % 3]
                with col:
                    nuevo_valor = st.selectbox(
                        campo,
                        options=["", "Completo", "No aplica"],
                        index=["", "Completo", "No aplica"].index(row.get(campo, '')) 
                              if row.get(campo, '') in ["", "Completo", "No aplica"] else 0,
                        key=f"{key_suffix}_{indice_seleccionado}",
                        on_change=on_change_callback
                    )
                    if nuevo_valor != row.get(campo, ''):
                        registros_df.at[registros_df.index[indice_seleccionado], campo] = nuevo_valor
                        edited = True

            # Fechas de estándares
            st.markdown("#### Fechas de Estándares")
            col1, col2 = st.columns(2)
            
            with col1:
                # Estándares fecha programada - SELECTOR DE FECHA
                fecha_estandares_prog_actual = fecha_para_selector(row.get('Estándares (fecha programada)', ''))
                nueva_fecha_estandares_prog = st.date_input(
                    "Estándares (fecha programada)",
                    value=fecha_estandares_prog_actual,
                    key=f"estandares_prog_{indice_seleccionado}",
                    on_change=on_change_callback
                )
                fecha_estandares_prog_str = fecha_desde_selector_a_string(nueva_fecha_estandares_prog)
                if fecha_estandares_prog_str != formatear_fecha(row.get('Estándares (fecha programada)', '')):
                    registros_df.at[registros_df.index[indice_seleccionado], 'Estándares (fecha programada)'] = fecha_estandares_prog_str
                    edited = True

            with col2:
                # Estándares fecha real - SELECTOR DE FECHA
                fecha_estandares_actual = fecha_para_selector(row.get('Estándares', ''))
                nueva_fecha_estandares = st.date_input(
                    "Estándares (fecha real)",
                    value=fecha_estandares_actual,
                    key=f"estandares_{indice_seleccionado}",
                    on_change=on_change_callback
                )
                fecha_estandares_str = fecha_desde_selector_a_string(nueva_fecha_estandares)
                if fecha_estandares_str != formatear_fecha(row.get('Estándares', '')):
                    registros_df.at[registros_df.index[indice_seleccionado], 'Estándares'] = fecha_estandares_str
                    edited = True

            # ===== SECCIÓN 6: PUBLICACIÓN =====
            st.markdown("---")
            st.markdown("### 6. Publicación")
            
            # Campos de publicación
            st.markdown("#### Proceso de Publicación")
            col1, col2, col3 = st.columns(3)
            
            campos_publicacion = [
                ('Resultados de orientación técnica', 'resultados_ot'),
                ('Verificación del servicio web geográfico', 'verificacion_web'),
                ('Verificar Aprobar Resultados', 'verificar_aprobar'),
                ('Revisar y validar los datos cargados en la base de datos', 'revisar_validar'),
                ('Aprobación resultados obtenidos en la rientación', 'aprobacion_resultados'),
                ('Disponer datos temáticos', 'disponer_datos'),
                ('Catálogo de recursos geográficos', 'catalogo_recursos')
            ]
            
            for i, (campo, key_suffix) in enumerate(campos_publicacion):
                col = [col1, col2, col3][i % 3]
                with col:
                    nuevo_valor = st.selectbox(
                        campo,
                        options=["", "Si", "No"],
                        index=["", "Si", "No"].index(row.get(campo, '')) 
                              if row.get(campo, '') in ["", "Si", "No"] else 0,
                        key=f"{key_suffix}_{indice_seleccionado}",
                        on_change=on_change_callback
                    )
                    if nuevo_valor != row.get(campo, ''):
                        registros_df.at[registros_df.index[indice_seleccionado], campo] = nuevo_valor
                        edited = True

            # Fechas de publicación
            st.markdown("#### Fechas de Publicación")
            col1, col2 = st.columns(2)
            
            with col1:
                # Fecha de publicación programada - SELECTOR DE FECHA
                fecha_pub_prog_actual = fecha_para_selector(row.get('Fecha de publicación programada', ''))
                nueva_fecha_pub_prog = st.date_input(
                    "Fecha de publicación programada",
                    value=fecha_pub_prog_actual,
                    key=f"pub_prog_{indice_seleccionado}",
                    on_change=on_change_callback
                )
                fecha_pub_prog_str = fecha_desde_selector_a_string(nueva_fecha_pub_prog)
                if fecha_pub_prog_str != formatear_fecha(row.get('Fecha de publicación programada', '')):
                    registros_df.at[registros_df.index[indice_seleccionado], 'Fecha de publicación programada'] = fecha_pub_prog_str
                    edited = True

            with col2:
                # Publicación fecha real - SELECTOR DE FECHA
                fecha_pub_actual = fecha_para_selector(row.get('Publicación', ''))
                nueva_fecha_pub = st.date_input(
                    "Publicación (fecha real)",
                    value=fecha_pub_actual,
                    key=f"publicacion_{indice_seleccionado}",
                    on_change=on_change_callback
                )
                fecha_pub_str = fecha_desde_selector_a_string(nueva_fecha_pub)
                if fecha_pub_str != formatear_fecha(row.get('Publicación', '')):
                    registros_df.at[registros_df.index[indice_seleccionado], 'Publicación'] = fecha_pub_str
                    edited = True

            # ===== SECCIÓN 7: CIERRE =====
            st.markdown("---")
            st.markdown("### 7. Cierre")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                # Plazo de oficio de cierre - CALCULADO AUTOMÁTICAMENTE
                plazo_oficio_actual = row.get('Plazo de oficio de cierre', '')
                st.text_input(
                    "Plazo de oficio de cierre (calculado automáticamente)",
                    value=plazo_oficio_actual,
                    disabled=True,
                    key=f"plazo_oficio_{indice_seleccionado}",
                    help="Se calcula automáticamente como 7 días hábiles después de la fecha de publicación"
                )

                # Oficios de cierre
                nuevo_oficio = st.selectbox(
                    "Oficios de cierre",
                    options=["", "Si", "No"],
                    index=["", "Si", "No"].index(row.get('Oficios de cierre', '')) 
                          if row.get('Oficios de cierre', '') in ["", "Si", "No"] else 0,
                    key=f"oficios_{indice_seleccionado}",
                    on_change=on_change_callback
                )
                if nuevo_oficio != row.get('Oficios de cierre', ''):
                    registros_df.at[registros_df.index[indice_seleccionado], 'Oficios de cierre'] = nuevo_oficio
                    edited = True

            with col2:
                # Fecha de oficio de cierre - SELECTOR DE FECHA CON VALIDACIÓN
                fecha_oficio_actual = fecha_para_selector(row.get('Fecha de oficio de cierre', ''))
                
                # Verificar si puede introducir fecha de cierre
                tiene_publicacion = (row.get('Publicación', '') and 
                                   pd.notna(row.get('Publicación', '')) and 
                                   str(row.get('Publicación', '')).strip() != '')
                
                if not tiene_publicacion:
                    st.warning("⚠️ Para introducir fecha de oficio de cierre, primero debe completar la etapa de Publicación")
                    st.text_input(
                        "Fecha de oficio de cierre (requiere publicación)",
                        value=formatear_fecha(fecha_oficio_actual) if fecha_oficio_actual else "",
                        disabled=True,
                        key=f"oficio_disabled_{indice_seleccionado}"
                    )
                else:
                    nueva_fecha_oficio = st.date_input(
                        "Fecha de oficio de cierre",
                        value=fecha_oficio_actual,
                        key=f"oficio_{indice_seleccionado}",
                        on_change=on_change_callback
                    )
                    fecha_oficio_str = fecha_desde_selector_a_string(nueva_fecha_oficio)
                    if fecha_oficio_str != formatear_fecha(row.get('Fecha de oficio de cierre', '')):
                        registros_df.at[registros_df.index[indice_seleccionado], 'Fecha de oficio de cierre'] = fecha_oficio_str
                        edited = True

            with col3:
                # Estado
                opciones_estado = ["", "En proceso", "En proceso oficio de cierre", "Completado", "Finalizado"]
                estado_actual = row.get('Estado', '')
                estado_index = opciones_estado.index(estado_actual) if estado_actual in opciones_estado else 0
                nuevo_estado = st.selectbox(
                    "Estado",
                    options=opciones_estado,
                    index=estado_index,
                    key=f"estado_{indice_seleccionado}",
                    on_change=on_change_callback
                )
                if nuevo_estado != row.get('Estado', ''):
                    registros_df.at[registros_df.index[indice_seleccionado], 'Estado'] = nuevo_estado
                    edited = True

            # Observación - CAMPO DE TEXTO AMPLIO
            nueva_observacion = st.text_area(
                "Observación",
                value=row.get('Observación', '') if pd.notna(row.get('Observación', '')) else "",
                height=100,
                key=f"observacion_{indice_seleccionado}",
                on_change=on_change_callback
            )
            if nueva_observacion != row.get('Observación', ''):
                registros_df.at[registros_df.index[indice_seleccionado], 'Observación'] = nueva_observacion
                edited = True

            # ===== INFORMACIÓN DE AVANCE AL FINAL =====
            st.markdown("---")
            st.markdown("### Información de Avance")
            
            # Calcular porcentaje de avance actual
            porcentaje_actual = calcular_porcentaje_avance(registros_df.iloc[indice_seleccionado])
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Porcentaje de Avance", f"{porcentaje_actual}%")
            
            with col2:
                # Estado basado en porcentaje
                if porcentaje_actual == 100:
                    estado_avance = "Completado"
                    color_avance = "green"
                elif porcentaje_actual >= 75:
                    estado_avance = "Avanzado"
                    color_avance = "blue"
                elif porcentaje_actual >= 50:
                    estado_avance = "En progreso"
                    color_avance = "orange"
                elif porcentaje_actual >= 25:
                    estado_avance = "Inicial"
                    color_avance = "yellow"
                else:
                    estado_avance = "Sin iniciar"
                    color_avance = "red"
                
                st.markdown(f"""
                <div style="padding: 10px; border-radius: 5px; background-color: {color_avance}; color: white; text-align: center;">
                    <strong>{estado_avance}</strong>
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                # Próxima acción sugerida
                if porcentaje_actual == 0:
                    proxima_accion = "Iniciar acuerdo de compromiso"
                elif porcentaje_actual == 20:
                    proxima_accion = "Completar análisis y cronograma"
                elif porcentaje_actual == 40:
                    proxima_accion = "Completar estándares"
                elif porcentaje_actual == 70:
                    proxima_accion = "Realizar publicación"
                elif porcentaje_actual == 95:
                    proxima_accion = "Emitir oficio de cierre"
                else:
                    proxima_accion = "Continuar con el proceso"
                
                st.info(f"**Próxima acción:** {proxima_accion}")

            # ===== BOTONES DE ACCIÓN =====
            st.markdown("---")
            st.markdown("### Acciones")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                # Botón para guardar cambios individuales
                if edited or st.session_state.get('cambios_pendientes', False):
                    if st.button("💾 Guardar Cambios", key=f"guardar_individual_{indice_seleccionado}", type="primary"):
                        # Aplicar validaciones de reglas de negocio antes de guardar
                        registros_df = validar_reglas_negocio(registros_df)

                        # Actualizar los plazos automáticamente
                        registros_df = actualizar_plazo_analisis(registros_df)
                        registros_df = actualizar_plazo_cronograma(registros_df)
                        registros_df = actualizar_plazo_oficio_cierre(registros_df)

                        # Guardar los datos en Google Sheets
                        with st.spinner("Guardando cambios en Google Sheets..."):
                            exito, mensaje = guardar_datos_editados(registros_df, crear_backup=True)

                        if exito:
                            st.session_state.mensaje_guardado = ("success", mensaje)
                            st.session_state.cambios_pendientes = False
                            st.rerun()
                        else:
                            st.session_state.mensaje_guardado = ("error", mensaje)

            with col2:
                # Botón para recalcular plazos
                if st.button("🔄 Recalcular Plazos", key=f"recalcular_{indice_seleccionado}"):
                    with st.spinner("Recalculando plazos automáticamente..."):
                        # Actualizar los plazos automáticamente
                        registros_df = actualizar_plazo_analisis(registros_df)
                        registros_df = actualizar_plazo_cronograma(registros_df)
                        registros_df = actualizar_plazo_oficio_cierre(registros_df)
                        
                        # Guardar cambios
                        exito, mensaje = guardar_datos_editados_rapido(registros_df)
                        if exito:
                            st.success("Plazos recalculados y guardados")
                            st.rerun()
                        else:
                            st.error("Error al guardar plazos recalculados")

            with col3:
                # Botón para aplicar validaciones
                if st.button("✅ Aplicar Validaciones", key=f"validar_{indice_seleccionado}"):
                    with st.spinner("Aplicando reglas de validación..."):
                        # Aplicar reglas de negocio
                        registros_df = validar_reglas_negocio(registros_df)
                        
                        # Guardar cambios
                        exito, mensaje = guardar_datos_editados_rapido(registros_df)
                        if exito:
                            st.success("Validaciones aplicadas y guardadas")
                            st.rerun()
                        else:
                            st.error("Error al guardar validaciones")

            with col4:
                # Botón para actualizar vista
                if st.button("🔄 Actualizar Vista", key=f"actualizar_{indice_seleccionado}"):
                    st.rerun()

    except Exception as e:
        st.error(f"Error al editar el registro: {e}")
        
        # Mostrar información de debug
        with st.expander("Información de Debug"):
            st.write(f"Índice seleccionado: {indice_seleccionado}")
            st.write(f"Registro seleccionado: {seleccion_registro}")
            st.write(f"Columnas disponibles: {list(registros_df.columns)}")
            
            # Mostrar traceback completo
            import traceback
            st.code(traceback.format_exc())

    return registros_df
# ========== FUNCIÓN DASHBOARD MODIFICADA ==========

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
        avance_promedio = df_filtrado['Porcentaje Avance'].mean() if not df_filtrado.empty else 0
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
            try:
                if pd.isna(val) or val is None:
                    return ''
                val = float(val)  # Asegurar que es numérico
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
            except (ValueError, TypeError):
                return ''
        
        try:
            if df_comparacion.empty or 'Porcentaje' not in df_comparacion.columns:
                return df_comparacion
            
            return df_comparacion.style.format({
                'Porcentaje': '{:.2f}%'
            }).applymap(aplicar_color, subset=['Porcentaje'])
        except Exception:
            # Fallback si falla el estilo
            return df_comparacion

    # Función para crear visualización estilo Opción 3
    def crear_visualizacion_barras_cumplimiento(df_comparacion, titulo, tipo_registro):
        """Crea visualización de barras con indicador de cumplimiento (Opción 3)"""
        if titulo:
            st.markdown(f"#### {titulo}")
        
        # Crear HTML personalizado para las barras de cumplimiento
        html_content = ""
        
        for hito in df_comparacion.index:
            completados = df_comparacion.loc[hito, 'Completados']
            meta = df_comparacion.loc[hito, 'Meta']
            porcentaje = df_comparacion.loc[hito, 'Porcentaje']
            
            # Determinar color según porcentaje
            if porcentaje < 50:
                color = '#dc2626'  # Rojo
                color_text = '#fee2e2'  # Rojo claro para el texto
            elif porcentaje < 80:
                color = '#f59e0b'  # Amarillo/Naranja
                color_text = '#fef3c7'  # Amarillo claro para el texto
            else:
                color = '#16a34a'  # Verde
                color_text = '#dcfce7'  # Verde claro para el texto
            
            # Calcular ancho de la barra (máximo 100%)
            ancho_barra = min(porcentaje, 100)
            
            html_content += f"""
            <div style="margin-bottom: 15px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 5px;">
                    <span style="font-weight: 600; font-size: 14px;">{hito}</span>
                    <span style="font-size: 12px; color: #64748b;">{completados}/{meta}</span>
                </div>
                <div style="position: relative; background-color: #e5e7eb; height: 32px; border-radius: 6px; overflow: hidden;">
                    <div style="
                        width: {ancho_barra}%; 
                        height: 100%; 
                        background-color: {color}; 
                        transition: width 0.5s ease-in-out;
                        border-radius: 6px;
                    "></div>
                    <div style="
                        position: absolute; 
                        top: 0; 
                        left: 0; 
                        right: 0; 
                        bottom: 0; 
                        display: flex; 
                        align-items: center; 
                        justify-content: center; 
                        font-weight: bold; 
                        font-size: 12px;
                        color: white;
                        text-shadow: 1px 1px 2px rgba(0,0,0,0.5);
                    ">
                        {porcentaje:.1f}%
                    </div>
                </div>
                <div style="text-align: center; margin-top: 3px; font-size: 11px; color: {color}; font-weight: 600;">
                    {'🎯 Meta Alcanzada' if porcentaje >= 100 else '📈 En Progreso' if porcentaje >= 80 else '⚠️ Requiere Atención' if porcentaje >= 50 else '🚨 Crítico'}
                </div>
            </div>
            """
        
        # Mostrar el HTML
        st.markdown(html_content, unsafe_allow_html=True)
        
        # Agregar leyenda de colores
        st.markdown("""
        <div style="display: flex; justify-content: center; gap: 20px; margin-top: 10px; font-size: 11px;">
            <div style="display: flex; align-items: center; gap: 5px;">
                <div style="width: 12px; height: 12px; background-color: #dc2626; border-radius: 2px;"></div>
                <span>< 50%</span>
            </div>
            <div style="display: flex; align-items: center; gap: 5px;">
                <div style="width: 12px; height: 12px; background-color: #f59e0b; border-radius: 2px;"></div>
                <span>50-79%</span>
            </div>
            <div style="display: flex; align-items: center; gap: 5px;">
                <div style="width: 12px; height: 12px; background-color: #16a34a; border-radius: 2px;"></div>
                <span>≥ 80%</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Mostrar comparación en dos columnas
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Registros Nuevos")
        # CONSERVAR: La tabla con gradiente personalizado
        st.dataframe(crear_gradiente_personalizado(comparacion_nuevos))
        
        # CAMBIO: Reemplazar el gráfico de Plotly con la nueva visualización
        crear_visualizacion_barras_cumplimiento(comparacion_nuevos, "", "nuevos")

    with col2:
        st.markdown("### Registros a Actualizar")
        # CONSERVAR: La tabla con gradiente personalizado
        st.dataframe(crear_gradiente_personalizado(comparacion_actualizar))
        
        # CAMBIO: Reemplazar el gráfico de Plotly con la nueva visualización
        crear_visualizacion_barras_cumplimiento(comparacion_actualizar, "", "actualizar")

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
        st.info("Para visualizar el diagrama de Gantt seleccione la entidad o funcionario de su interés.")

    # Tabla de registros con porcentaje de avance
    st.markdown('<div class="subtitle">Detalle de Registros</div>', unsafe_allow_html=True)

    # USAR TODAS LAS COLUMNAS DISPONIBLES DEL DATAFRAME
    try:
        df_mostrar = df_filtrado.copy()

        # Aplicar formato a las fechas
        columnas_fecha = [
            'Fecha de entrega de información', 'Plazo de análisis', 'Plazo de cronograma',
            'Análisis y cronograma', 'Estándares',
            'Publicación', 'Plazo de oficio de cierre', 'Fecha de oficio de cierre'
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
                label="Descargar datos filtrados (Excel)",
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
                label="Descargar TODOS los registros (Excel)",
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
# ========== FUNCIÓN ALERTAS COMPLETA RESTAURADA ==========

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
            fecha_plazo_analisis = procesar_fecha(row.get('Plazo de análisis', ''))
            fecha_plazo_cronograma = procesar_fecha(row.get('Plazo de cronograma', ''))
            fecha_analisis_cronograma = procesar_fecha(row.get('Análisis y cronograma', ''))
            fecha_estandares_prog = procesar_fecha(row.get('Estándares (fecha programada)', ''))
            fecha_estandares = procesar_fecha(row.get('Estándares', ''))
            fecha_publicacion_prog = procesar_fecha(row.get('Fecha de publicación programada', ''))
            fecha_publicacion = procesar_fecha(row.get('Publicación', ''))
            fecha_plazo_oficio_cierre = procesar_fecha(row.get('Plazo de oficio de cierre', ''))
            fecha_oficio_cierre = procesar_fecha(row.get('Fecha de oficio de cierre', ''))

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

            # 2. Análisis y cronograma
            if fecha_plazo_cronograma is not None and pd.notna(fecha_plazo_cronograma):
                if fecha_analisis_cronograma is not None and pd.notna(fecha_analisis_cronograma):
                    # Hay fecha real, verificar si está con retraso
                    if fecha_analisis_cronograma > fecha_plazo_cronograma:
                        dias_rezago = calcular_dias_habiles(fecha_plazo_cronograma, fecha_analisis_cronograma)
                        registros_alertas.append({
                            'Cod': row['Cod'],
                            'Entidad': row['Entidad'],
                            'Nivel Información': row.get('Nivel Información ', ''),
                            'Funcionario': row.get('Funcionario', ''),
                            'Tipo Alerta': 'Análisis y cronograma',
                            'Fecha Programada': fecha_plazo_cronograma,
                            'Fecha Real': fecha_analisis_cronograma,
                            'Días Rezago': dias_rezago,
                            'Estado': 'Completado con retraso',
                            'Descripción': f'Análisis realizado con {dias_rezago} días hábiles de retraso'
                        })
                else:
                    # No hay fecha real, verificar si está vencido o próximo
                    if es_vencido(fecha_plazo_cronograma):
                        dias_rezago = calcular_dias_rezago(fecha_plazo_cronograma)
                        registros_alertas.append({
                            'Cod': row['Cod'],
                            'Entidad': row['Entidad'],
                            'Nivel Información': row.get('Nivel Información ', ''),
                            'Funcionario': row.get('Funcionario', ''),
                            'Tipo Alerta': 'Análisis y cronograma',
                            'Fecha Programada': fecha_plazo_cronograma,
                            'Fecha Real': None,
                            'Días Rezago': dias_rezago,
                            'Estado': 'Vencido',
                            'Descripción': f'Plazo de cronograma vencido hace {dias_rezago} días sin fecha real'
                        })
                    elif es_proximo_vencimiento(fecha_plazo_cronograma):
                        dias_restantes = calcular_dias_habiles(fecha_actual, fecha_plazo_cronograma)
                        registros_alertas.append({
                            'Cod': row['Cod'],
                            'Entidad': row['Entidad'],
                            'Nivel Información': row.get('Nivel Información ', ''),
                            'Funcionario': row.get('Funcionario', ''),
                            'Tipo Alerta': 'Análisis y cronograma',
                            'Fecha Programada': fecha_plazo_cronograma,
                            'Fecha Real': None,
                            'Días Rezago': -dias_restantes,  # Negativo indica días por vencer
                            'Estado': 'Próximo a vencer',
                            'Descripción': f'Plazo de cronograma vence en {dias_restantes} días hábiles'
                        })

            # 3. Estándares
            if fecha_estandares_prog is not None and pd.notna(fecha_estandares_prog):
                if fecha_estandares is not None and pd.notna(fecha_estandares):
                    # Hay fecha real, verificar si está con retraso
                    if fecha_estandares > fecha_estandares_prog:
                        dias_rezago = calcular_dias_habiles(fecha_estandares_prog, fecha_estandares)
                        registros_alertas.append({
                            'Cod': row['Cod'],
                            'Entidad': row['Entidad'],
                            'Nivel Información': row.get('Nivel Información ', ''),
                            'Funcionario': row.get('Funcionario', ''),
                            'Tipo Alerta': 'Estándares',
                            'Fecha Programada': fecha_estandares_prog,
                            'Fecha Real': fecha_estandares,
                            'Días Rezago': dias_rezago,
                            'Estado': 'Completado con retraso',
                            'Descripción': f'Estándares completados con {dias_rezago} días hábiles de retraso'
                        })
                else:
                    # No hay fecha real, verificar si está vencido o próximo
                    if es_vencido(fecha_estandares_prog):
                        dias_rezago = calcular_dias_rezago(fecha_estandares_prog)
                        registros_alertas.append({
                            'Cod': row['Cod'],
                            'Entidad': row['Entidad'],
                            'Nivel Información': row.get('Nivel Información ', ''),
                            'Funcionario': row.get('Funcionario', ''),
                            'Tipo Alerta': 'Estándares',
                            'Fecha Programada': fecha_estandares_prog,
                            'Fecha Real': None,
                            'Días Rezago': dias_rezago,
                            'Estado': 'Vencido',
                            'Descripción': f'Fecha programada de estándares vencida hace {dias_rezago} días'
                        })
                    elif es_proximo_vencimiento(fecha_estandares_prog):
                        dias_restantes = calcular_dias_habiles(fecha_actual, fecha_estandares_prog)
                        registros_alertas.append({
                            'Cod': row['Cod'],
                            'Entidad': row['Entidad'],
                            'Nivel Información': row.get('Nivel Información ', ''),
                            'Funcionario': row.get('Funcionario', ''),
                            'Tipo Alerta': 'Estándares',
                            'Fecha Programada': fecha_estandares_prog,
                            'Fecha Real': None,
                            'Días Rezago': -dias_restantes,
                            'Estado': 'Próximo a vencer',
                            'Descripción': f'Fecha programada de estándares vence en {dias_restantes} días hábiles'
                        })

            # 4. Publicación
            if fecha_publicacion_prog is not None and pd.notna(fecha_publicacion_prog):
                if fecha_publicacion is not None and pd.notna(fecha_publicacion):
                    # Hay fecha real, verificar si está con retraso
                    if fecha_publicacion > fecha_publicacion_prog:
                        dias_rezago = calcular_dias_habiles(fecha_publicacion_prog, fecha_publicacion)
                        registros_alertas.append({
                            'Cod': row['Cod'],
                            'Entidad': row['Entidad'],
                            'Nivel Información': row.get('Nivel Información ', ''),
                            'Funcionario': row.get('Funcionario', ''),
                            'Tipo Alerta': 'Publicación',
                            'Fecha Programada': fecha_publicacion_prog,
                            'Fecha Real': fecha_publicacion,
                            'Días Rezago': dias_rezago,
                            'Estado': 'Completado con retraso',
                            'Descripción': f'Publicación realizada con {dias_rezago} días hábiles de retraso'
                        })
                else:
                    # No hay fecha real, verificar si está vencido o próximo
                    if es_vencido(fecha_publicacion_prog):
                        dias_rezago = calcular_dias_rezago(fecha_publicacion_prog)
                        registros_alertas.append({
                            'Cod': row['Cod'],
                            'Entidad': row['Entidad'],
                            'Nivel Información': row.get('Nivel Información ', ''),
                            'Funcionario': row.get('Funcionario', ''),
                            'Tipo Alerta': 'Publicación',
                            'Fecha Programada': fecha_publicacion_prog,
                            'Fecha Real': None,
                            'Días Rezago': dias_rezago,
                            'Estado': 'Vencido',
                            'Descripción': f'Fecha programada de publicación vencida hace {dias_rezago} días'
                        })
                    elif es_proximo_vencimiento(fecha_publicacion_prog):
                        dias_restantes = calcular_dias_habiles(fecha_actual, fecha_publicacion_prog)
                        registros_alertas.append({
                            'Cod': row['Cod'],
                            'Entidad': row['Entidad'],
                            'Nivel Información': row.get('Nivel Información ', ''),
                            'Funcionario': row.get('Funcionario', ''),
                            'Tipo Alerta': 'Publicación',
                            'Fecha Programada': fecha_publicacion_prog,
                            'Fecha Real': None,
                            'Días Rezago': -dias_restantes,
                            'Estado': 'Próximo a vencer',
                            'Descripción': f'Fecha programada de publicación vence en {dias_restantes} días hábiles'
                        })

            # 5. Oficio de cierre
            if fecha_plazo_oficio_cierre is not None and pd.notna(fecha_plazo_oficio_cierre):
                if fecha_oficio_cierre is not None and pd.notna(fecha_oficio_cierre):
                    # Hay fecha real, verificar si está con retraso
                    if fecha_oficio_cierre > fecha_plazo_oficio_cierre:
                        dias_rezago = calcular_dias_habiles(fecha_plazo_oficio_cierre, fecha_oficio_cierre)
                        registros_alertas.append({
                            'Cod': row['Cod'],
                            'Entidad': row['Entidad'],
                            'Nivel Información': row.get('Nivel Información ', ''),
                            'Funcionario': row.get('Funcionario', ''),
                            'Tipo Alerta': 'Oficio de cierre',
                            'Fecha Programada': fecha_plazo_oficio_cierre,
                            'Fecha Real': fecha_oficio_cierre,
                            'Días Rezago': dias_rezago,
                            'Estado': 'Completado con retraso',
                            'Descripción': f'Oficio de cierre emitido con {dias_rezago} días hábiles de retraso'
                        })
                else:
                    # No hay fecha real, verificar si está vencido o próximo
                    if es_vencido(fecha_plazo_oficio_cierre):
                        dias_rezago = calcular_dias_rezago(fecha_plazo_oficio_cierre)
                        registros_alertas.append({
                            'Cod': row['Cod'],
                            'Entidad': row['Entidad'],
                            'Nivel Información': row.get('Nivel Información ', ''),
                            'Funcionario': row.get('Funcionario', ''),
                            'Tipo Alerta': 'Oficio de cierre',
                            'Fecha Programada': fecha_plazo_oficio_cierre,
                            'Fecha Real': None,
                            'Días Rezago': dias_rezago,
                            'Estado': 'Vencido',
                            'Descripción': f'Plazo de oficio de cierre vencido hace {dias_rezago} días'
                        })
                    elif es_proximo_vencimiento(fecha_plazo_oficio_cierre):
                        dias_restantes = calcular_dias_habiles(fecha_actual, fecha_plazo_oficio_cierre)
                        registros_alertas.append({
                            'Cod': row['Cod'],
                            'Entidad': row['Entidad'],
                            'Nivel Información': row.get('Nivel Información ', ''),
                            'Funcionario': row.get('Funcionario', ''),
                            'Tipo Alerta': 'Oficio de cierre',
                            'Fecha Programada': fecha_plazo_oficio_cierre,
                            'Fecha Real': None,
                            'Días Rezago': -dias_restantes,
                            'Estado': 'Próximo a vencer',
                            'Descripción': f'Plazo de oficio de cierre vence en {dias_restantes} días hábiles'
                        })

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

        # Filtros para la tabla de alertas
        st.markdown("### Filtrar Alertas")

        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            tipo_alerta_filtro = st.multiselect(
                "Tipo de Alerta",
                options=df_alertas['Tipo Alerta'].unique().tolist(),
                default=df_alertas['Tipo Alerta'].unique().tolist()
            )

        with col2:
            estado_filtro = st.multiselect(
                "Estado",
                options=df_alertas['Estado'].unique().tolist(),
                default=df_alertas['Estado'].unique().tolist()
            )

        with col3:
            if 'Funcionario' in df_alertas.columns and not df_alertas['Funcionario'].isna().all():
                funcionarios = [f for f in df_alertas['Funcionario'].dropna().unique().tolist() if f]
                if funcionarios:
                    funcionario_filtro = st.multiselect(
                        "Funcionario",
                        options=["Todos"] + sorted(funcionarios),
                        default=["Todos"]
                    )
                else:
                    funcionario_filtro = ["Todos"]
            else:
                funcionario_filtro = ["Todos"]

        with col4:
            tipos_dato_alertas = ['Todos'] + sorted(registros_df['TipoDato'].dropna().unique().tolist())
            tipo_dato_filtro_alertas = st.multiselect(
                "Tipo de Dato",
                options=tipos_dato_alertas,
                default=["Todos"]
            )

        with col5:
            meses_disponibles_alertas = ['Todos']
            if 'Mes Proyectado' in registros_df.columns:
                meses_unicos_alertas = [m for m in registros_df['Mes Proyectado'].dropna().unique().tolist() if m]
                meses_disponibles_alertas += sorted(meses_unicos_alertas)
            mes_filtro_alertas = st.multiselect(
                "Mes Proyectado",
                options=meses_disponibles_alertas,
                default=["Todos"]
            )
            
        # Aplicar filtros
        df_alertas_filtrado = df_alertas.copy()

        if tipo_alerta_filtro:
            df_alertas_filtrado = df_alertas_filtrado[df_alertas_filtrado['Tipo Alerta'].isin(tipo_alerta_filtro)]

        if estado_filtro:
            df_alertas_filtrado = df_alertas_filtrado[df_alertas_filtrado['Estado'].isin(estado_filtro)]

        if 'Funcionario' in df_alertas.columns and funcionario_filtro and "Todos" not in funcionario_filtro:
            df_alertas_filtrado = df_alertas_filtrado[df_alertas_filtrado['Funcionario'].isin(funcionario_filtro)]

        if tipo_dato_filtro_alertas and "Todos" not in tipo_dato_filtro_alertas:
            # Obtener códigos de registros que coinciden con el tipo de dato
            codigos_tipo_dato = registros_df[registros_df['TipoDato'].isin(tipo_dato_filtro_alertas)]['Cod'].tolist()
            df_alertas_filtrado = df_alertas_filtrado[df_alertas_filtrado['Cod'].isin(codigos_tipo_dato)]

        # Agregar después de los otros filtros
        if mes_filtro_alertas and "Todos" not in mes_filtro_alertas:
            # Obtener códigos de registros que coinciden con el mes proyectado
            codigos_mes_proyectado = registros_df[registros_df['Mes Proyectado'].isin(mes_filtro_alertas)]['Cod'].tolist()
            df_alertas_filtrado = df_alertas_filtrado[df_alertas_filtrado['Cod'].isin(codigos_mes_proyectado)]
        
        # Mostrar tabla de alertas con formato
        st.markdown("### Listado de Alertas")

        # Definir columnas a mostrar
        columnas_alertas = [
            'Cod', 'Entidad', 'Nivel Información', 'Funcionario', 'Tipo Alerta',
            'Estado', 'Fecha Programada', 'Fecha Real', 'Días Rezago', 'Descripción'
        ]

        # Verificar que todas las columnas existan
        columnas_alertas_existentes = [col for col in columnas_alertas if col in df_alertas_filtrado.columns]

        try:
            # Ordenar por estado (vencidos primero) y días de rezago
            df_alertas_filtrado['Estado_orden'] = df_alertas_filtrado['Estado'].map({
                'Vencido': 1,
                'Próximo a vencer': 2,
                'Completado con retraso': 3
            })

            df_alertas_filtrado = df_alertas_filtrado.sort_values(
                by=['Estado_orden', 'Días Rezago'],
                ascending=[True, False]
            )

            # Mostrar tabla con formato
            st.dataframe(
                df_alertas_filtrado[columnas_alertas_existentes]
                .style.applymap(lambda _: '',
                                subset=['Cod', 'Entidad', 'Nivel Información', 'Funcionario', 'Tipo Alerta',
                                        'Fecha Programada', 'Fecha Real', 'Descripción'])
                .applymap(highlight_estado, subset=['Estado'])
                .format({'Días Rezago': '{:+d}'})  # Mostrar signo + o - en días rezago
            )

            # Botón para descargar alertas
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df_alertas_filtrado[columnas_alertas_existentes].to_excel(writer, sheet_name='Alertas', index=False)

            excel_data = output.getvalue()
            st.download_button(
                label="Descargar alertas como Excel",
                data=excel_data,
                file_name="alertas_vencimientos.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                help="Descarga las alertas filtradas en formato Excel"
            )
        except Exception as e:
            st.error(f"Error al mostrar la tabla de alertas: {e}")
            # Mostrar tabla sin formato como último recurso
            st.dataframe(df_alertas_filtrado[columnas_alertas_existentes])
    else:
        st.success("¡No hay alertas de vencimientos pendientes!")

# ========== FUNCIÓN REPORTES CON MES PROYECTADO ==========

def mostrar_reportes(registros_df, tipo_dato_filtro, acuerdo_filtro, analisis_filtro, 
                    estandares_filtro, publicacion_filtro, finalizado_filtro, mes_filtro):
    """Muestra la pestaña de reportes con tabla completa y filtros específicos - VERSIÓN COMPLETA CON MES."""
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
                (df_filtrado['Acuerdo de compromiso'].str.upper().isin(['SI', 'SÍ', 'S', 'YES', 'Y', 'COMPLETO']))
            ]
        else:  # No Suscrito
            df_filtrado = df_filtrado[
                ~(df_filtrado['Acuerdo de compromiso'].str.upper().isin(['SI', 'SÍ', 'S', 'YES', 'Y', 'COMPLETO']))
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
    
    # FILTRO: Mes Proyectado
    if mes_filtro != 'Todos':
        df_filtrado = df_filtrado[df_filtrado['Mes Proyectado'] == mes_filtro]
    
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
        'Cod', 'Entidad', 'Nivel Información ', 'Funcionario', 'Mes Proyectado',
        'Frecuencia actualizacion ', 'TipoDato',
        'Fecha de entrega de información', 'Plazo de análisis', 'Plazo de cronograma',
        'Análisis y cronograma', 'Estándares', 'Publicación',
        'Plazo de oficio de cierre', 'Fecha de oficio de cierre',
        'Estado', 'Observación', 'Porcentaje Avance'
    ]
    
    # Verificar que todas las columnas existan
    columnas_mostrar_existentes = [col for col in columnas_mostrar if col in df_filtrado.columns]
    df_mostrar = df_filtrado[columnas_mostrar_existentes].copy()
    
    # Aplicar formato a las fechas
    columnas_fecha = [
        'Fecha de entrega de información', 'Plazo de análisis', 'Plazo de cronograma',
        'Análisis y cronograma', 'Estándares', 'Publicación',
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
            label="Descargar reporte como Excel",
            data=excel_data,
            file_name=f"reporte_registros_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            help="Descarga el reporte filtrado en formato Excel"
        )
    
    with col2:
        # Descargar como CSV
        csv = df_mostrar.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Descargar reporte como CSV",
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
    if mes_filtro != 'Todos':
        filtros_aplicados.append(f"Mes Proyectado: {mes_filtro}")
    
    if filtros_aplicados:
        st.info(f"**Filtros aplicados:** {', '.join(filtros_aplicados)}")
    else:
        st.info("**Mostrando todos los registros** (sin filtros aplicados)")


# ========== FUNCIÓN SEGUIMIENTO TRIMESTRAL - COMPLETA Y CORRECTA ==========
# COPIAR ESTA FUNCIÓN COMPLETA EN TU app1.py ANTES DE def main():

# ========== FUNCIÓN SEGUIMIENTO TRIMESTRAL - SOLO PUBLICACIONES ==========
def mostrar_seguimiento_trimestral(registros_df):
    """Muestra el seguimiento trimestral de publicaciones: avance real vs meta programada."""
    st.markdown('<div class="subtitle">Seguimiento Trimestral - Publicaciones: Meta vs Avance Real</div>', unsafe_allow_html=True)
    
    # ✅ VERIFICACIÓN MEJORADA DE LA COLUMNA MES PROYECTADO
    if 'Mes Proyectado' not in registros_df.columns:
        st.error("❌ La columna 'Mes Proyectado' no está disponible en los datos")
        st.info("📋 Verifique que la hoja de Google Sheets tenga la columna 'Mes Proyectado'")
        
        # Mostrar las columnas disponibles para debugging
        with st.expander("🔍 Columnas disponibles en los datos"):
            st.write("Columnas encontradas:")
            for i, col in enumerate(registros_df.columns):
                st.write(f"{i+1}. {col}")
        
        # Función de debug
        with st.expander("🔍 Debug Completo de Datos"):
            debug_datos_seguimiento_trimestral(registros_df)
        
        return
    
    # ✅ ANÁLISIS DETALLADO DE DATOS CON DEBUG
    with st.expander("🔍 Análisis Detallado de Datos", expanded=False):
        st.markdown("### 📊 Estadísticas de Datos")
        
        total_registros = len(registros_df)
        st.write(f"📊 Total de registros: {total_registros}")
        
        # Analizar Mes Proyectado paso a paso
        mes_no_nulo = len(registros_df[registros_df['Mes Proyectado'].notna()])
        st.write(f"📅 Con Mes Proyectado no nulo: {mes_no_nulo}")
        
        mes_no_vacio = len(registros_df[
            (registros_df['Mes Proyectado'].notna()) & 
            (registros_df['Mes Proyectado'].astype(str).str.strip() != '')
        ])
        st.write(f"📅 Con Mes Proyectado no vacío: {mes_no_vacio}")
        
        # Mostrar valores únicos
        if mes_no_nulo > 0:
            valores_mes = registros_df['Mes Proyectado'].dropna().unique()
            st.write(f"📅 Meses únicos encontrados: {list(valores_mes)}")
            
            # Distribución por mes
            distribucion_mes = registros_df['Mes Proyectado'].value_counts()
            st.write("📊 Distribución por mes:")
            st.dataframe(distribucion_mes)
        
        # Analizar TipoDato
        if 'TipoDato' in registros_df.columns:
            tipo_no_nulo = len(registros_df[registros_df['TipoDato'].notna()])
            st.write(f"🏷️ Con TipoDato no nulo: {tipo_no_nulo}")
            
            if tipo_no_nulo > 0:
                valores_tipo = registros_df['TipoDato'].dropna().unique()
                st.write(f"🏷️ Tipos únicos encontrados: {list(valores_tipo)}")
                
                distribucion_tipo = registros_df['TipoDato'].value_counts()
                st.write("📊 Distribución por tipo:")
                st.dataframe(distribucion_tipo)
    
    # ✅ FILTRADO MÁS PERMISIVO Y CON DEBUGGING
    st.markdown("### 🔍 Proceso de Filtrado de Datos")
    
    # Paso 1: Filtrar registros con Mes Proyectado válido
    registros_paso1 = registros_df[registros_df['Mes Proyectado'].notna()]
    st.info(f"Paso 1 - Mes Proyectado no nulo: {len(registros_paso1)} registros")
    
    if len(registros_paso1) == 0:
        st.error("❌ No hay registros con Mes Proyectado no nulo")
        return
    
    # Paso 2: Filtrar registros con Mes Proyectado no vacío
    registros_paso2 = registros_paso1[
        registros_paso1['Mes Proyectado'].astype(str).str.strip() != ''
    ]
    st.info(f"Paso 2 - Mes Proyectado no vacío: {len(registros_paso2)} registros")
    
    if len(registros_paso2) == 0:
        st.error("❌ No hay registros con Mes Proyectado no vacío")
        st.write("Valores encontrados:", registros_paso1['Mes Proyectado'].unique().tolist())
        return
    
    # Paso 3: Filtrar valores problemáticos
    registros_con_mes = registros_paso2[
        (~registros_paso2['Mes Proyectado'].astype(str).str.strip().isin(['nan', 'None', 'NaN']))
    ]
    st.info(f"Paso 3 - Mes Proyectado válido: {len(registros_con_mes)} registros")
    
    if registros_con_mes.empty:
        st.warning("⚠️ No hay registros con 'Mes Proyectado' válido después del filtrado")
        st.write("Valores encontrados después del paso 2:", registros_paso2['Mes Proyectado'].unique().tolist())
        
        # Mostrar muestra de datos para debugging
        st.markdown("### 🔍 Muestra de Datos para Debug")
        if not registros_df.empty:
            muestra_cols = ['Cod', 'Entidad', 'Mes Proyectado', 'TipoDato']
            muestra_cols = [col for col in muestra_cols if col in registros_df.columns]
            muestra = registros_df[muestra_cols].head(10)
            st.dataframe(muestra)
        
        return
    
    # Si llegamos aquí, hay datos válidos para el seguimiento trimestral
    st.success(f"✅ {len(registros_con_mes)} registros tienen 'Mes Proyectado' asignado")
    
    # CSS personalizado para los medidores (mismo código que antes)
    st.markdown("""
    <style>
    .trimestre-section {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        border-radius: 15px;
        padding: 25px;
        margin-bottom: 30px;
        border: 2px solid #dee2e6;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    
    .trimestre-title {
        background: linear-gradient(90deg, #BE185D, #9D174D);
        color: white;
        padding: 15px;
        border-radius: 10px;
        text-align: center;
        font-size: 1.5rem;
        font-weight: bold;
        margin-bottom: 25px;
        box-shadow: 0 4px 15px rgba(190, 24, 93, 0.3);
    }
    
    .gauge-info-card {
        background: white;
        border-radius: 10px;
        padding: 20px;
        margin-top: 15px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        border-left: 4px solid #BE185D;
    }
    
    .meta-vs-avance {
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-size: 1rem;
        margin-bottom: 10px;
    }
    
    .detalle-info {
        font-size: 0.9rem;
        color: #6b7280;
        margin-top: 8px;
    }
    
    .meta-text { color: #7f8c8d; font-weight: 500; }
    .avance-excelente { color: #27ae60; font-weight: bold; }
    .avance-bueno { color: #2ecc71; font-weight: bold; }
    .avance-regular { color: #f39c12; font-weight: bold; }
    .avance-bajo { color: #e74c3c; font-weight: bold; }
    .avance-critico { color: #c0392b; font-weight: bold; }
    
    .summary-card {
        background: linear-gradient(135deg, #BE185D 0%, #9D174D 100%);
        color: white;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
        margin: 10px 0;
    }
    
    .summary-value {
        font-size: 2rem;
        font-weight: bold;
        margin-bottom: 5px;
    }
    
    .summary-label {
        font-size: 0.9rem;
        opacity: 0.9;
    }
    
    .legend-container {
        background: #f8f9fa;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 30px;
        border: 1px solid #dee2e6;
    }
    
    .legend-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
        gap: 15px;
        margin-top: 15px;
    }
    
    .legend-item {
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 0.9rem;
        font-weight: 500;
    }
    
    .legend-color {
        width: 18px;
        height: 18px;
        border-radius: 50%;
        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
    }
    
    .trimestre-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
        gap: 30px;
        margin-bottom: 30px;
    }
    
    .gauge-container {
        background: white;
        border-radius: 15px;
        padding: 20px;
        box-shadow: 0 8px 25px rgba(0,0,0,0.1);
        border: 1px solid #e8f4f8;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Información explicativa
    st.info("""
    **📊 Seguimiento de Publicaciones por Trimestre**
    
    Este dashboard muestra el avance de **publicaciones reales** versus las **metas programadas** para cada trimestre:
    - **Meta:** Número de registros que deberían estar publicados al final del trimestre
    - **Avance:** Número de registros con fecha real de publicación completada
    - **Porcentaje:** (Publicaciones reales / Meta programada) × 100
    """)
    
    # Leyenda de colores
    st.markdown("""
    <div class="legend-container">
        <h4 style="margin: 0 0 15px 0; color: #2c3e50; text-align: center;">📊 Escala de Cumplimiento</h4>
        <div class="legend-grid">
            <div class="legend-item">
                <div class="legend-color" style="background: #27ae60;"></div>
                <span>Excelente (90-100%)</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background: #2ecc71;"></div>
                <span>Bueno (75-89%)</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background: #f39c12;"></div>
                <span>Regular (50-74%)</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background: #e74c3c;"></div>
                <span>Bajo (25-49%)</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background: #c0392b;"></div>
                <span>Crítico (0-24%)</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Función para determinar clase CSS según porcentaje
    def get_avance_class(porcentaje):
        if porcentaje >= 90: return "avance-excelente"
        elif porcentaje >= 75: return "avance-bueno"
        elif porcentaje >= 50: return "avance-regular"
        elif porcentaje >= 25: return "avance-bajo"
        else: return "avance-critico"
    
    # Función para crear medidor circular
    def crear_medidor_publicaciones(valor, titulo, meta_num, avance_num, trimestre_info):
        # Determinar color según porcentaje
        if valor >= 90: color = '#27ae60'
        elif valor >= 75: color = '#2ecc71'
        elif valor >= 50: color = '#f39c12'
        elif valor >= 25: color = '#e74c3c'
        else: color = '#c0392b'
        
        fig = go.Figure(go.Indicator(
            mode = "gauge+number+delta",
            value = valor,
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': titulo, 'font': {'size': 18, 'color': '#2c3e50', 'family': 'Arial'}},
            delta = {'reference': 75, 'increasing': {'color': '#27ae60'}, 'decreasing': {'color': '#e74c3c'}},
            gauge = {
                'axis': {'range': [None, 100], 'tickwidth': 2, 'tickcolor': '#34495e'},
                'bar': {'color': color, 'thickness': 0.75},
                'bgcolor': '#ecf0f1',
                'borderwidth': 3,
                'bordercolor': '#bdc3c7',
                'steps': [
                    {'range': [0, 25], 'color': '#fadbd8'},
                    {'range': [25, 50], 'color': '#f8d7da'},
                    {'range': [50, 75], 'color': '#fff3cd'},
                    {'range': [75, 90], 'color': '#d1ecf1'},
                    {'range': [90, 100], 'color': '#d4edda'}
                ],
                'threshold': {
                    'line': {'color': '#BE185D', 'width': 5},
                    'thickness': 0.8,
                    'value': 75
                }
            },
            number = {'font': {'size': 32, 'color': color, 'family': 'Arial'}, 'suffix': '%'}
        ))
        
        fig.update_layout(
            height=300,
            margin=dict(l=20, r=20, t=60, b=20),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font={'color': '#2c3e50', 'family': 'Arial'}
        )
        
        return fig
    
    # ✅ FUNCIÓN DE CÁLCULO CORREGIDA Y CON DEBUG
    def calcular_publicaciones_trimestrales(df, tipo_dato):
        """Función corregida con mejor manejo de errores y debugging detallado"""
        
        # Debug inicial
        st.write(f"🔍 **Calculando para tipo: {tipo_dato}**")
        st.write(f"📊 Registros de entrada: {len(df)}")
        
        # ✅ Verificar que existe la columna TipoDato
        if 'TipoDato' not in df.columns:
            st.error(f"❌ Columna 'TipoDato' no encontrada para tipo {tipo_dato}")
            return crear_datos_trimestre_vacio()
        
        # ✅ Filtrar por tipo de dato de manera más robusta
        try:
            if tipo_dato.upper() == 'NUEVO':
                # Filtro más permisivo para NUEVO
                mask_tipo = (
                    (df['TipoDato'].notna()) & 
                    (df['TipoDato'].astype(str).str.upper().str.strip().isin(['NUEVO', 'NUEVA']))
                )
            else:
                # Filtro más permisivo para ACTUALIZAR
                mask_tipo = (
                    (df['TipoDato'].notna()) & 
                    (df['TipoDato'].astype(str).str.upper().str.strip().isin(['ACTUALIZAR', 'ACTUALIZACION']))
                )
            
            df_filtrado = df[mask_tipo]
            st.write(f"📊 Registros después de filtrar por tipo '{tipo_dato}': {len(df_filtrado)}")
            
        except Exception as e:
            st.error(f"❌ Error filtrando por tipo {tipo_dato}: {str(e)}")
            return crear_datos_trimestre_vacio()
        
        if df_filtrado.empty:
            st.warning(f"⚠️ No hay registros de tipo '{tipo_dato}' con mes proyectado")
            return crear_datos_trimestre_vacio()
        
        # Mostrar distribución por mes para este tipo
        if len(df_filtrado) > 0:
            distribucion_meses = df_filtrado['Mes Proyectado'].value_counts()
            st.write(f"📅 Distribución por mes para {tipo_dato}:")
            for mes, cantidad in distribucion_meses.items():
                st.write(f"   • {mes}: {cantidad} registros")
        
        # Definir trimestres (basado en Mes Proyectado)
        trimestres = {
            'Q1': ['Enero', 'Febrero', 'Marzo'],
            'Q2': ['Abril', 'Mayo', 'Junio'], 
            'Q3': ['Julio', 'Agosto', 'Septiembre'],
            'Q4': ['Octubre', 'Noviembre', 'Diciembre']
        }
        
        datos_trimestres = {}
        
        for trimestre, meses in trimestres.items():
            try:
                # Filtrar registros del trimestre
                df_trimestre = df_filtrado[df_filtrado['Mes Proyectado'].isin(meses)]
                
                st.write(f"📊 **{trimestre}** ({', '.join(meses)}): {len(df_trimestre)} registros")
                
                # META: Total de registros que deberían estar publicados al final del trimestre
                meta_publicaciones = len(df_trimestre)
                
                # AVANCE: Registros con fecha real de publicación
                avance_publicaciones = 0
                if 'Publicación' in df_trimestre.columns and len(df_trimestre) > 0:
                    try:
                        mask_publicacion = (
                            (df_trimestre['Publicación'].notna()) & 
                            (df_trimestre['Publicación'].astype(str).str.strip() != '') &
                            (~df_trimestre['Publicación'].astype(str).str.strip().isin(['nan', 'None', 'NaN']))
                        )
                        avance_publicaciones = len(df_trimestre[mask_publicacion])
                    except Exception as pub_error:
                        st.warning(f"⚠️ Error calculando publicaciones para {trimestre}: {str(pub_error)}")
                        avance_publicaciones = 0
                
                # Calcular porcentaje
                porcentaje = (avance_publicaciones / meta_publicaciones * 100) if meta_publicaciones > 0 else 0
                
                # Información adicional para debugging
                registros_programados = 0
                if 'Fecha de publicación programada' in df_trimestre.columns and len(df_trimestre) > 0:
                    try:
                        mask_programada = (
                            (df_trimestre['Fecha de publicación programada'].notna()) & 
                            (df_trimestre['Fecha de publicación programada'].astype(str).str.strip() != '') &
                            (~df_trimestre['Fecha de publicación programada'].astype(str).str.strip().isin(['nan', 'None', 'NaN']))
                        )
                        registros_programados = len(df_trimestre[mask_programada])
                    except Exception as prog_error:
                        st.warning(f"⚠️ Error calculando programadas para {trimestre}: {str(prog_error)}")
                        registros_programados = 0
                
                datos_trimestres[trimestre] = {
                    'meta': meta_publicaciones,
                    'avance': avance_publicaciones,
                    'porcentaje': porcentaje,
                    'programados': registros_programados,
                    'pendientes': meta_publicaciones - avance_publicaciones
                }
                
                st.write(f"   • Meta: {meta_publicaciones}, Avance: {avance_publicaciones}, Porcentaje: {porcentaje:.1f}%")
                
            except Exception as trimestre_error:
                st.error(f"❌ Error procesando {trimestre}: {str(trimestre_error)}")
                datos_trimestres[trimestre] = {
                    'meta': 0, 'avance': 0, 'porcentaje': 0, 'programados': 0, 'pendientes': 0
                }
        
        return datos_trimestres
    
    def crear_datos_trimestre_vacio():
        """Crea estructura vacía para trimestres sin datos"""
        return {
            'Q1': {'meta': 0, 'avance': 0, 'porcentaje': 0, 'programados': 0, 'pendientes': 0},
            'Q2': {'meta': 0, 'avance': 0, 'porcentaje': 0, 'programados': 0, 'pendientes': 0},
            'Q3': {'meta': 0, 'avance': 0, 'porcentaje': 0, 'programados': 0, 'pendientes': 0},
            'Q4': {'meta': 0, 'avance': 0, 'porcentaje': 0, 'programados': 0, 'pendientes': 0}
        }
    
    # Pestañas para Nuevos y Actualizados
    tab_nuevos, tab_actualizados, tab_debug = st.tabs(["📈 Registros Nuevos", "🔄 Registros a Actualizar", "🔍 Debug Detallado"])
    
    # TAB REGISTROS NUEVOS
    with tab_nuevos:
        st.markdown("### 🆕 Seguimiento de Publicaciones - Registros Nuevos")
        
        with st.expander("🔍 Proceso de Cálculo - Registros Nuevos", expanded=False):
            datos_nuevos = calcular_publicaciones_trimestrales(registros_con_mes, 'NUEVO')
        
        # Crear grid de medidores
        st.markdown('<div class="trimestre-grid">', unsafe_allow_html=True)
        
        # Crear medidores para cada trimestre que tenga datos
        trimestres_con_datos = [q for q in ['Q1', 'Q2', 'Q3', 'Q4'] if datos_nuevos[q]['meta'] > 0]
        
        if not trimestres_con_datos:
            st.warning("⚠️ No hay registros nuevos con 'Mes Proyectado' asignado para mostrar en gráficos.")
            st.info("📝 Verifique que hay registros con TipoDato='Nuevo' y Mes Proyectado asignado")
        else:
            # Dividir en columnas
            cols = st.columns(min(len(trimestres_con_datos), 4))
            
            for idx, trimestre in enumerate(trimestres_con_datos):
                datos = datos_nuevos[trimestre]
                
                with cols[idx % 4]:
                    # Título del trimestre
                    trimestre_nombre = {
                        'Q1': '🌱 Q1 2025\nEnero - Marzo',
                        'Q2': '☀️ Q2 2025\nAbril - Junio',
                        'Q3': '🍂 Q3 2025\nJulio - Septiembre',
                        'Q4': '❄️ Q4 2025\nOctubre - Diciembre'
                    }[trimestre]
                    
                    # Crear medidor
                    fig_publicacion = crear_medidor_publicaciones(
                        datos['porcentaje'],
                        trimestre_nombre,
                        datos['meta'],
                        datos['avance'],
                        trimestre
                    )
                    st.plotly_chart(fig_publicacion, use_container_width=True, key=f"nuevos_pub_{trimestre}")
                    
                    # Información detallada
                    avance_class = get_avance_class(datos['porcentaje'])
                    st.markdown(f"""
                    <div class="gauge-info-card">
                        <div class="meta-vs-avance">
                            <span class="meta-text">Meta: {datos['meta']} publicaciones</span>
                            <span class="{avance_class}">Real: {datos['avance']} ({datos['porcentaje']:.1f}%)</span>
                        </div>
                        <div class="detalle-info">
                            📅 Programadas: {datos['programados']} | ⏳ Pendientes: {datos['pendientes']}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Resumen para registros nuevos
        if trimestres_con_datos:
            st.markdown("### 📊 Resumen Anual - Registros Nuevos")
            
            total_meta_nuevos = sum([datos_nuevos[q]['meta'] for q in ['Q1', 'Q2', 'Q3', 'Q4']])
            total_avance_nuevos = sum([datos_nuevos[q]['avance'] for q in ['Q1', 'Q2', 'Q3', 'Q4']])
            promedio_nuevos = (total_avance_nuevos / total_meta_nuevos * 100) if total_meta_nuevos > 0 else 0
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.markdown(f"""
                <div class="summary-card">
                    <div class="summary-value">{promedio_nuevos:.1f}%</div>
                    <div class="summary-label">Promedio Anual</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"""
                <div class="summary-card">
                    <div class="summary-value">{total_avance_nuevos}/{total_meta_nuevos}</div>
                    <div class="summary-label">Publicaciones Reales/Meta</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                trimestres_activos = len(trimestres_con_datos)
                st.markdown(f"""
                <div class="summary-card">
                    <div class="summary-value">{trimestres_activos}</div>
                    <div class="summary-label">Trimestres Activos</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col4:
                mejor_trimestre = max(trimestres_con_datos, key=lambda q: datos_nuevos[q]['porcentaje']) if trimestres_con_datos else "N/A"
                st.markdown(f"""
                <div class="summary-card">
                    <div class="summary-value">{mejor_trimestre}</div>
                    <div class="summary-label">Mejor Trimestre</div>
                </div>
                """, unsafe_allow_html=True)
    
    # TAB REGISTROS A ACTUALIZAR
    with tab_actualizados:
        st.markdown("### 🔄 Seguimiento de Publicaciones - Registros a Actualizar")
        
        with st.expander("🔍 Proceso de Cálculo - Registros a Actualizar", expanded=False):
            datos_actualizar = calcular_publicaciones_trimestrales(registros_con_mes, 'ACTUALIZAR')
        
        # Crear grid de medidores
        st.markdown('<div class="trimestre-grid">', unsafe_allow_html=True)
        
        # Crear medidores para cada trimestre que tenga datos
        trimestres_con_datos = [q for q in ['Q1', 'Q2', 'Q3', 'Q4'] if datos_actualizar[q]['meta'] > 0]
        
        if not trimestres_con_datos:
            st.warning("⚠️ No hay registros a actualizar con 'Mes Proyectado' asignado para mostrar en gráficos.")
            st.info("📝 Verifique que hay registros con TipoDato='Actualizar' y Mes Proyectado asignado")
        else:
            # Dividir en columnas
            cols = st.columns(min(len(trimestres_con_datos), 4))
            
            for idx, trimestre in enumerate(trimestres_con_datos):
                datos = datos_actualizar[trimestre]
                
                with cols[idx % 4]:
                    # Título del trimestre
                    trimestre_nombre = {
                        'Q1': '🌱 Q1 2025\nEnero - Marzo',
                        'Q2': '☀️ Q2 2025\nAbril - Junio',
                        'Q3': '🍂 Q3 2025\nJulio - Septiembre',
                        'Q4': '❄️ Q4 2025\nOctubre - Diciembre'
                    }[trimestre]
                    
                    # Crear medidor
                    fig_publicacion = crear_medidor_publicaciones(
                        datos['porcentaje'],
                        trimestre_nombre,
                        datos['meta'],
                        datos['avance'],
                        trimestre
                    )
                    st.plotly_chart(fig_publicacion, use_container_width=True, key=f"actualizar_pub_{trimestre}")
                    
                    # Información detallada
                    avance_class = get_avance_class(datos['porcentaje'])
                    st.markdown(f"""
                    <div class="gauge-info-card">
                        <div class="meta-vs-avance">
                            <span class="meta-text">Meta: {datos['meta']} publicaciones</span>
                            <span class="{avance_class}">Real: {datos['avance']} ({datos['porcentaje']:.1f}%)</span>
                        </div>
                        <div class="detalle-info">
                            📅 Programadas: {datos['programados']} | ⏳ Pendientes: {datos['pendientes']}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Resumen para registros a actualizar
        if trimestres_con_datos:
            st.markdown("### 📊 Resumen Anual - Registros a Actualizar")
            
            total_meta_actualizar = sum([datos_actualizar[q]['meta'] for q in ['Q1', 'Q2', 'Q3', 'Q4']])
            total_avance_actualizar = sum([datos_actualizar[q]['avance'] for q in ['Q1', 'Q2', 'Q3', 'Q4']])
            promedio_actualizar = (total_avance_actualizar / total_meta_actualizar * 100) if total_meta_actualizar > 0 else 0
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.markdown(f"""
                <div class="summary-card">
                    <div class="summary-value">{promedio_actualizar:.1f}%</div>
                    <div class="summary-label">Promedio Anual</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"""
                <div class="summary-card">
                    <div class="summary-value">{total_avance_actualizar}/{total_meta_actualizar}</div>
                    <div class="summary-label">Publicaciones Reales/Meta</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                trimestres_activos = len(trimestres_con_datos)
                st.markdown(f"""
                <div class="summary-card">
                    <div class="summary-value">{trimestres_activos}</div>
                    <div class="summary-label">Trimestres Activos</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col4:
                mejor_trimestre = max(trimestres_con_datos, key=lambda q: datos_actualizar[q]['porcentaje']) if trimestres_con_datos else "N/A"
                st.markdown(f"""
                <div class="summary-card">
                    <div class="summary-value">{mejor_trimestre}</div>
                    <div class="summary-label">Mejor Trimestre</div>
                </div>
                """, unsafe_allow_html=True)
    
    # TAB DEBUG DETALLADO
    with tab_debug:
        st.markdown("### 🔍 Debug Detallado del Sistema")
        debug_datos_seguimiento_trimestral(registros_df)

# Función de debug independiente (agregar al final del archivo)
def debug_datos_seguimiento_trimestral(registros_df):
    """Función específica para debuggear problemas del seguimiento trimestral"""
    
    st.markdown("## 🔍 DEBUG: Análisis Detallado de Datos")
    
    # 1. Verificar estructura general
    st.markdown("### 1. Estructura General")
    st.write(f"- Shape del DataFrame: {registros_df.shape}")
    st.write(f"- Columnas totales: {len(registros_df.columns)}")
    st.write(f"- Registros totales: {len(registros_df)}")
    
    # 2. Verificar columna Mes Proyectado
    st.markdown("### 2. Análisis de 'Mes Proyectado'")
    
    if 'Mes Proyectado' in registros_df.columns:
        st.success("✅ Columna 'Mes Proyectado' existe")
        
        # Estadísticas de la columna
        mes_serie = registros_df['Mes Proyectado']
        st.write(f"- Valores no nulos: {mes_serie.notna().sum()}")
        st.write(f"- Valores nulos: {mes_serie.isna().sum()}")
        
        # Valores únicos
        valores_unicos = mes_serie.dropna().unique()
        st.write(f"- Valores únicos: {len(valores_unicos)}")
        st.write(f"- Lista de valores: {valores_unicos.tolist()}")
        
        # Conteo por valor
        conteo_valores = mes_serie.value_counts()
        st.write("- Distribución:")
        st.dataframe(conteo_valores)
        
        # Muestra de registros con mes proyectado
        registros_con_mes = registros_df[registros_df['Mes Proyectado'].notna()]
        st.write(f"- Registros con mes proyectado: {len(registros_con_mes)}")
        
        if len(registros_con_mes) > 0:
            st.markdown("#### Muestra de registros con Mes Proyectado:")
            muestra_cols = ['Cod', 'Entidad', 'Mes Proyectado', 'TipoDato']
            muestra_cols = [col for col in muestra_cols if col in registros_df.columns]
            st.dataframe(registros_con_mes[muestra_cols].head(10))
    else:
        st.error("❌ Columna 'Mes Proyectado' NO existe")
        st.write("Columnas disponibles:")
        for i, col in enumerate(registros_df.columns):
            st.write(f"{i+1}. {col}")
    
    # 3. Verificar columna TipoDato
    st.markdown("### 3. Análisis de 'TipoDato'")
    
    if 'TipoDato' in registros_df.columns:
        st.success("✅ Columna 'TipoDato' existe")
        
        tipo_serie = registros_df['TipoDato']
        st.write(f"- Valores no nulos: {tipo_serie.notna().sum()}")
        st.write(f"- Valores nulos: {tipo_serie.isna().sum()}")
        
        # Valores únicos
        valores_tipo = tipo_serie.dropna().unique()
        st.write(f"- Valores únicos: {valores_tipo.tolist()}")
        
        # Conteo por tipo
        conteo_tipo = tipo_serie.value_counts()
        st.write("- Distribución:")
        st.dataframe(conteo_tipo)
    else:
        st.error("❌ Columna 'TipoDato' NO existe")
    
    # 4. Análisis cruzado
    st.markdown("### 4. Análisis Cruzado")
    
    if 'Mes Proyectado' in registros_df.columns and 'TipoDato' in registros_df.columns:
        # Tabla cruzada
        tabla_cruzada = pd.crosstab(
            registros_df['Mes Proyectado'].fillna('Sin Mes'), 
            registros_df['TipoDato'].fillna('Sin Tipo'),
            margins=True
        )
        st.write("Tabla cruzada Mes Proyectado vs TipoDato:")
        st.dataframe(tabla_cruzada)
        
        # Registros con ambos campos válidos
        registros_completos = registros_df[
            (registros_df['Mes Proyectado'].notna()) & 
            (registros_df['TipoDato'].notna()) &
            (registros_df['Mes Proyectado'].astype(str).str.strip() != '') &
            (registros_df['TipoDato'].astype(str).str.strip() != '')
        ]
        
        st.write(f"📊 Registros con Mes Proyectado Y TipoDato válidos: {len(registros_completos)}")
        
        if len(registros_completos) > 0:
            # Separar por tipo
            nuevos = registros_completos[registros_completos['TipoDato'].str.upper() == 'NUEVO']
            actualizar = registros_completos[registros_completos['TipoDato'].str.upper() == 'ACTUALIZAR']
            
            st.write(f"- Registros NUEVOS con mes: {len(nuevos)}")
            st.write(f"- Registros ACTUALIZAR con mes: {len(actualizar)}")
            
            # Distribución por trimestre
            meses_q1 = ['Enero', 'Febrero', 'Marzo']
            meses_q2 = ['Abril', 'Mayo', 'Junio']
            meses_q3 = ['Julio', 'Agosto', 'Septiembre']
            meses_q4 = ['Octubre', 'Noviembre', 'Diciembre']
            
            for tipo, df_tipo in [('NUEVOS', nuevos), ('ACTUALIZAR', actualizar)]:
                st.write(f"\n**Distribución {tipo} por trimestre:**")
                q1 = len(df_tipo[df_tipo['Mes Proyectado'].isin(meses_q1)])
                q2 = len(df_tipo[df_tipo['Mes Proyectado'].isin(meses_q2)])
                q3 = len(df_tipo[df_tipo['Mes Proyectado'].isin(meses_q3)])
                q4 = len(df_tipo[df_tipo['Mes Proyectado'].isin(meses_q4)])
                
                st.write(f"- Q1: {q1}, Q2: {q2}, Q3: {q3}, Q4: {q4}")
    
    # 5. Verificar columnas de publicación
    st.markdown("### 5. Análisis de Columnas de Publicación")
    
    columnas_publicacion = ['Publicación', 'Fecha de publicación programada']
    for col in columnas_publicacion:
        if col in registros_df.columns:
            st.success(f"✅ Columna '{col}' existe")
            
            serie = registros_df[col]
            valores_validos = serie[
                (serie.notna()) & 
                (serie.astype(str).str.strip() != '') &
                (~serie.astype(str).str.strip().isin(['nan', 'None', 'NaN']))
            ]
            
            st.write(f"- Valores válidos en '{col}': {len(valores_validos)}")
            
            if len(valores_validos) > 0:
                st.write(f"- Muestra de valores válidos: {valores_validos.head().tolist()}")
        else:
            st.error(f"❌ Columna '{col}' NO existe")
    
    # 6. Muestra completa de datos
    st.markdown("### 6. Muestra Completa de Datos")
    
    if not registros_df.empty:
        # Mostrar primeros registros con columnas relevantes
        columnas_relevantes = ['Cod', 'Entidad', 'Mes Proyectado', 'TipoDato', 'Publicación', 'Fecha de publicación programada']
        columnas_disponibles = [col for col in columnas_relevantes if col in registros_df.columns]
        
        st.write("Primeros 10 registros con columnas relevantes:")
        st.dataframe(registros_df[columnas_disponibles].head(10))
        
        # Mostrar últimos registros
        st.write("Últimos 5 registros con columnas relevantes:")
        st.dataframe(registros_df[columnas_disponibles].tail(5))
    
    return len(registros_df) > 0
    
    # Pestañas para Nuevos y Actualizados
    tab_nuevos, tab_actualizados = st.tabs(["📈 Registros Nuevos", "🔄 Registros a Actualizar"])
    
    # TAB REGISTROS NUEVOS
    with tab_nuevos:
        st.markdown("### 🆕 Seguimiento de Publicaciones - Registros Nuevos")
        
        datos_nuevos = calcular_publicaciones_trimestrales(registros_df, 'NUEVO')
        
        # Crear grid de medidores
        st.markdown('<div class="trimestre-grid">', unsafe_allow_html=True)
        
        # Crear medidores para cada trimestre que tenga datos
        trimestres_con_datos = [q for q in ['Q1', 'Q2', 'Q3', 'Q4'] if datos_nuevos[q]['meta'] > 0]
        
        if not trimestres_con_datos:
            st.warning("No hay registros nuevos con 'Mes Proyectado' asignado.")
        else:
            # Dividir en columnas
            cols = st.columns(min(len(trimestres_con_datos), 4))
            
            for idx, trimestre in enumerate(trimestres_con_datos):
                datos = datos_nuevos[trimestre]
                
                with cols[idx % 4]:
                    # Título del trimestre
                    trimestre_nombre = {
                        'Q1': '🌱 Q1 2025\nEnero - Marzo',
                        'Q2': '☀️ Q2 2025\nAbril - Junio',
                        'Q3': '🍂 Q3 2025\nJulio - Septiembre',
                        'Q4': '❄️ Q4 2025\nOctubre - Diciembre'
                    }[trimestre]
                    
                    # Crear medidor
                    fig_publicacion = crear_medidor_publicaciones(
                        datos['porcentaje'],
                        trimestre_nombre,
                        datos['meta'],
                        datos['avance'],
                        trimestre
                    )
                    st.plotly_chart(fig_publicacion, use_container_width=True, key=f"nuevos_pub_{trimestre}")
                    
                    # Información detallada
                    avance_class = get_avance_class(datos['porcentaje'])
                    st.markdown(f"""
                    <div class="gauge-info-card">
                        <div class="meta-vs-avance">
                            <span class="meta-text">Meta: {datos['meta']} publicaciones</span>
                            <span class="{avance_class}">Real: {datos['avance']} ({datos['porcentaje']:.1f}%)</span>
                        </div>
                        <div class="detalle-info">
                            📅 Programadas: {datos['programados']} | ⏳ Pendientes: {datos['pendientes']}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Resumen para registros nuevos
        st.markdown("### 📊 Resumen Anual - Registros Nuevos")
        
        total_meta_nuevos = sum([datos_nuevos[q]['meta'] for q in ['Q1', 'Q2', 'Q3', 'Q4']])
        total_avance_nuevos = sum([datos_nuevos[q]['avance'] for q in ['Q1', 'Q2', 'Q3', 'Q4']])
        promedio_nuevos = (total_avance_nuevos / total_meta_nuevos * 100) if total_meta_nuevos > 0 else 0
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
            <div class="summary-card">
                <div class="summary-value">{promedio_nuevos:.1f}%</div>
                <div class="summary-label">Promedio Anual</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="summary-card">
                <div class="summary-value">{total_avance_nuevos}/{total_meta_nuevos}</div>
                <div class="summary-label">Publicaciones Reales/Meta</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            trimestres_activos = len(trimestres_con_datos)
            st.markdown(f"""
            <div class="summary-card">
                <div class="summary-value">{trimestres_activos}</div>
                <div class="summary-label">Trimestres Activos</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            mejor_trimestre = max(trimestres_con_datos, key=lambda q: datos_nuevos[q]['porcentaje']) if trimestres_con_datos else "N/A"
            st.markdown(f"""
            <div class="summary-card">
                <div class="summary-value">{mejor_trimestre}</div>
                <div class="summary-label">Mejor Trimestre</div>
            </div>
            """, unsafe_allow_html=True)
    
    # TAB REGISTROS A ACTUALIZAR
    with tab_actualizados:
        st.markdown("### 🔄 Seguimiento de Publicaciones - Registros a Actualizar")
        
        datos_actualizar = calcular_publicaciones_trimestrales(registros_df, 'ACTUALIZAR')
        
        # Crear grid de medidores
        st.markdown('<div class="trimestre-grid">', unsafe_allow_html=True)
        
        # Crear medidores para cada trimestre que tenga datos
        trimestres_con_datos = [q for q in ['Q1', 'Q2', 'Q3', 'Q4'] if datos_actualizar[q]['meta'] > 0]
        
        if not trimestres_con_datos:
            st.warning("No hay registros a actualizar con 'Mes Proyectado' asignado.")
        else:
            # Dividir en columnas
            cols = st.columns(min(len(trimestres_con_datos), 4))
            
            for idx, trimestre in enumerate(trimestres_con_datos):
                datos = datos_actualizar[trimestre]
                
                with cols[idx % 4]:
                    # Título del trimestre
                    trimestre_nombre = {
                        'Q1': '🌱 Q1 2025\nEnero - Marzo',
                        'Q2': '☀️ Q2 2025\nAbril - Junio',
                        'Q3': '🍂 Q3 2025\nJulio - Septiembre',
                        'Q4': '❄️ Q4 2025\nOctubre - Diciembre'
                    }[trimestre]
                    
                    # Crear medidor
                    fig_publicacion = crear_medidor_publicaciones(
                        datos['porcentaje'],
                        trimestre_nombre,
                        datos['meta'],
                        datos['avance'],
                        trimestre
                    )
                    st.plotly_chart(fig_publicacion, use_container_width=True, key=f"actualizar_pub_{trimestre}")
                    
                    # Información detallada
                    avance_class = get_avance_class(datos['porcentaje'])
                    st.markdown(f"""
                    <div class="gauge-info-card">
                        <div class="meta-vs-avance">
                            <span class="meta-text">Meta: {datos['meta']} publicaciones</span>
                            <span class="{avance_class}">Real: {datos['avance']} ({datos['porcentaje']:.1f}%)</span>
                        </div>
                        <div class="detalle-info">
                            📅 Programadas: {datos['programados']} | ⏳ Pendientes: {datos['pendientes']}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Resumen para registros a actualizar
        st.markdown("### 📊 Resumen Anual - Registros a Actualizar")
        
        total_meta_actualizar = sum([datos_actualizar[q]['meta'] for q in ['Q1', 'Q2', 'Q3', 'Q4']])
        total_avance_actualizar = sum([datos_actualizar[q]['avance'] for q in ['Q1', 'Q2', 'Q3', 'Q4']])
        promedio_actualizar = (total_avance_actualizar / total_meta_actualizar * 100) if total_meta_actualizar > 0 else 0
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
            <div class="summary-card">
                <div class="summary-value">{promedio_actualizar:.1f}%</div>
                <div class="summary-label">Promedio Anual</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="summary-card">
                <div class="summary-value">{total_avance_actualizar}/{total_meta_actualizar}</div>
                <div class="summary-label">Publicaciones Reales/Meta</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            trimestres_activos = len(trimestres_con_datos)
            st.markdown(f"""
            <div class="summary-card">
                <div class="summary-value">{trimestres_activos}</div>
                <div class="summary-label">Trimestres Activos</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            mejor_trimestre = max(trimestres_con_datos, key=lambda q: datos_actualizar[q]['porcentaje']) if trimestres_con_datos else "N/A"
            st.markdown(f"""
            <div class="summary-card">
                <div class="summary-value">{mejor_trimestre}</div>
                <div class="summary-label">Mejor Trimestre</div>
            </div>
            """, unsafe_allow_html=True)
    
    
# ========== FUNCIÓN PRINCIPAL ==========

# Cambio en la función main() de app1.py

def main():
    """Función principal de la aplicación"""
    try:
        # Configurar página
        setup_page()
        load_css()

        # Inicializar session state
        if 'cambios_pendientes' not in st.session_state:
            st.session_state.cambios_pendientes = False
        if 'funcionarios' not in st.session_state:
            st.session_state.funcionarios = []
        if 'mensaje_guardado' not in st.session_state:
            st.session_state.mensaje_guardado = None

        # ===== TÍTULO =====
        st.markdown('<div class="title">📊 Tablero de Control de Seguimiento de Datos Temáticos - Ideca</div>', unsafe_allow_html=True)

        
        # ===== SIDEBAR CON AUTENTICACIÓN =====
        # Sistema de autenticación
        # mostrar_login()
        # mostrar_estado_autenticacion()
        
        # Configuración de Google Sheets
        mostrar_configuracion_sheets()
        
        # Información sobre el tablero
        # Información sobre el tablero
        st.sidebar.markdown('<div class="subtitle">Información</div>', unsafe_allow_html=True)
        st.sidebar.markdown("""
            <div class="info-box">
            <p><strong>Tablero de Control de Cronogramas</strong></p>
            <p><strong>VERSIÓN ULTRA SEGURA - GOOGLE SHEETS</strong></p>
            <p>🛡️ Con respaldo automático y restauración</p>
            </div>
            """, unsafe_allow_html=True)

        # CAMBIO: Mover la carga de datos dentro del expander "Estado del Sistema"
        

        with st.expander("🔍 Estado del Sistema", expanded=False):
            st.markdown("### 📊 Estado de Datos y Respaldos")
            
            # Importar funciones de respaldo
            try:
                from backup_utils import (
                    mostrar_estado_respaldos_detallado, 
                    verificar_disponibilidad_respaldo, 
                    obtener_fecha_ultimo_respaldo,
                    restauracion_automatica_emergencia,
                    restaurar_desde_respaldo
                )
                sistema_respaldo_disponible = True
            except ImportError:
                sistema_respaldo_disponible = False
                st.warning("⚠️ Sistema de respaldo no disponible")
            
            # Primera fila: Estado de conexión y reconexión
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.info("📊 Datos sincronizados con Google Sheets en tiempo real")
            
            with col2:
                if st.button("🔄 Reconectar"):
                    # Limpiar cache y reconectar
                    if 'sheets_manager' in st.session_state:
                        del st.session_state.sheets_manager
                    st.rerun()
            
            # Segunda fila: Estado de respaldos (solo si está disponible)
            if sistema_respaldo_disponible:
                st.markdown("---")
                
                # Obtener información de respaldos
                fecha_ultimo_respaldo = obtener_fecha_ultimo_respaldo()
                tiene_respaldo, info_respaldo = verificar_disponibilidad_respaldo()
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.markdown("**🛡️ Estado de Respaldos:**")
                    if fecha_ultimo_respaldo:
                        if isinstance(fecha_ultimo_respaldo, datetime):
                            fecha_formateada = fecha_ultimo_respaldo.strftime("%d/%m/%Y %H:%M")
                            st.success(f"✅ Último respaldo: {fecha_formateada}")
                        else:
                            st.info(f"💾 {fecha_ultimo_respaldo}")
                    else:
                        st.warning("⚠️ Sin respaldo disponible")
                
                with col2:
                    st.markdown("**💾 Respaldo Disponible:**")
                    if tiene_respaldo and info_respaldo:
                        if info_respaldo['valido']:
                            st.success(f"✅ {info_respaldo['registros']} registros")
                        else:
                            st.error(f"❌ Respaldo corrupto")
                    else:
                        st.warning("⚠️ No disponible")
                
                with col3:
                    st.markdown("**🔄 Restauración Automática:**")
                    if 'ultima_restauracion_automatica' in st.session_state:
                        fecha_rest = st.session_state.ultima_restauracion_automatica['fecha']
                        st.info(f"🔄 {fecha_rest.strftime('%H:%M')}")
                    else:
                        st.success("✅ No requerida")
                
                # Panel de restauración manual (si hay respaldo válido)
                if tiene_respaldo and info_respaldo and info_respaldo['valido']:
                    st.markdown("---")
                    st.markdown("**🔧 Restauración Manual:**")
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        if st.button("🔄 Restaurar desde Respaldo", help="Restaura manualmente desde el último respaldo válido"):
                            with st.spinner("Restaurando datos..."):
                                exito, df = restaurar_desde_respaldo()
                                if exito:
                                    st.success("✅ Restauración exitosa")
                                    st.balloons()
                                    st.rerun()
                                else:
                                    st.error("❌ Error en restauración")
                    
                    with col2:
                        st.metric("Registros en Respaldo", info_respaldo['registros'])
                    
                    with col3:
                        st.metric("Columnas en Respaldo", info_respaldo['columnas'])
            
            # Carga de datos con sistema de seguridad
            st.markdown("---")
            st.markdown("**📈 Carga de Datos:**")
            
            with st.spinner("🔍 Verificando integridad y cargando datos..."):
                registros_df, meta_df = cargar_datos()
            
            # Mostrar resultado de la carga
            if registros_df.empty:
                st.warning("⚠️ No hay datos de registros cargados")
                
                # Opciones de recuperación si no hay datos
                if sistema_respaldo_disponible and tiene_respaldo and info_respaldo and info_respaldo['valido']:
                    st.info(f"💾 Respaldo disponible con {info_respaldo['registros']} registros")
                    if st.button("🔄 Restaurar Automáticamente", type="primary"):
                        exito, df = restauracion_automatica_emergencia()
                        if exito:
                            st.rerun()
                else:
                    st.error("❌ No hay respaldo disponible para restauración")
                    
                # Crear estructura mínima como último recurso
                if registros_df.empty:
                    columnas_minimas = [
                        'Cod', 'Entidad', 'TipoDato', 'Nivel Información ', 'Mes Proyectado',
                        'Acuerdo de compromiso', 'Análisis y cronograma', 'Estándares', 'Publicación',
                        'Fecha de entrega de información', 'Plazo de análisis', 'Plazo de cronograma',
                        'Plazo de oficio de cierre', 'Funcionario', 'Frecuencia actualizacion ', 
                        'Estado', 'Observación', 'Fecha de oficio de cierre'
                    ]
                    registros_df = pd.DataFrame(columns=columnas_minimas)
            else:
                # Verificar si hubo restauración automática
                if 'ultima_restauracion_automatica' in st.session_state:
                    ultima_rest = st.session_state.ultima_restauracion_automatica
                    st.success(f"✅ {len(registros_df)} registros cargados (incluye restauración automática: {ultima_rest['registros_restaurados']} registros)")
                else:
                    st.success(f"✅ {len(registros_df)} registros cargados exitosamente")

        # ===== ASEGURAR COLUMNAS REQUERIDAS =====
        columnas_requeridas = [
            'Cod', 'Entidad', 'TipoDato', 'Acuerdo de compromiso',
            'Análisis y cronograma', 'Estándares', 'Publicación',
            'Nivel Información ', 'Mes Proyectado', 'Fecha de entrega de información',
            'Plazo de análisis', 'Plazo de cronograma', 'Plazo de oficio de cierre',
            'Funcionario', 'Frecuencia actualizacion ', 'Estado', 'Observación',
            'Fecha de oficio de cierre'
        ]

        for columna in columnas_requeridas:
            if columna not in registros_df.columns:
                registros_df[columna] = ''

        # ===== APLICAR VALIDACIONES Y CÁLCULOS (sin spinner visible) =====
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

        # ===== MOSTRAR VALIDACIONES =====
        with st.expander("Validación de Reglas de Negocio"):
            st.markdown("### Estado de Validaciones")
            st.info("""
            **Reglas aplicadas automáticamente:**
            1. Si 'Entrega acuerdo de compromiso' no está vacío → 'Acuerdo de compromiso' = SI
            2. Si 'Análisis y cronograma' tiene fecha → 'Análisis de información' = SI
            3. Al introducir fecha en 'Estándares' → campos no completos = "No aplica"
            4. Si introduce fecha en 'Publicación' → 'Disponer datos temáticos' = SI
            5. Para 'Fecha de oficio de cierre' → requiere etapa de Publicación completada
            6. Al introducir 'Fecha de oficio de cierre' → Estado = "Completado" y avance = 100%
            7. Plazos calculados automáticamente considerando días hábiles y festivos
            
            **Nuevas funcionalidades implementadas:**
            8. 🔐 Sistema de autenticación para funciones administrativas
            9. 📅 Campo "Mes Proyectado" para organización temporal
            10. 🔍 Filtro por mes en reportes para análisis específicos
            11. 🌈 Gradiente de metas mejorado: rojo (0%) → verde oscuro (100%+)
            12. 📊 Diagrama de Gantt condicional: solo con filtros específicos
            """)
            mostrar_estado_validaciones(registros_df, st)

        # ===== CREAR PESTAÑAS =====
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "Dashboard", 
            "Edición de Registros", 
            "Seguimiento Trimestral", 
            "Alertas de Vencimientos", 
            "Reportes"
        ])
     
        # ===== TAB 1: DASHBOARD =====
        with tab1:
            st.markdown("### Filtros")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                # Filtro por entidad
                entidades = ['Todas'] + sorted([e for e in registros_df['Entidad'].unique().tolist() if e])
                entidad_seleccionada = st.selectbox('Entidad', entidades, key="dash_entidad")
            
            with col2:
                # Filtro por funcionario
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
                # Filtro por nivel de información dependiente de entidad
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
            
            # Mostrar dashboard completo
            mostrar_dashboard(df_filtrado, metas_nuevas_df, metas_actualizar_df, registros_df,
                            entidad_seleccionada, funcionario_seleccionado, nivel_seleccionado)

        # ===== TAB 2: EDICIÓN =====
              
        with tab2:
            # Llamar a la función de edición
            registros_df = mostrar_edicion_registros(registros_df)

        with tab3:
            mostrar_seguimiento_trimestral(registros_df)
        
        # ===== TAB 4: ALERTAS =====
        with tab4:
            mostrar_alertas_vencimientos(registros_df)

        # ===== TAB 5: REPORTES =====
        with tab5:
            st.markdown("### Filtros de Reportes")
            
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
            
            # Tercera fila de filtros
            col7, col8, col9 = st.columns(3)
            
            with col7:
                # FILTRO: Mes Proyectado
                meses_disponibles = ['Todos']
                if 'Mes Proyectado' in registros_df.columns:
                    meses_unicos = [m for m in registros_df['Mes Proyectado'].dropna().unique().tolist() if m]
                    meses_disponibles += sorted(meses_unicos)
                mes_filtro = st.selectbox('Mes Proyectado', meses_disponibles, key="reporte_mes")
            
            st.markdown("---")
            
            # Mostrar reportes
            mostrar_reportes(registros_df, tipo_dato_reporte, acuerdo_filtro, analisis_filtro, 
                           estandares_filtro, publicacion_filtro, finalizado_filtro, mes_filtro)

        # ===== FOOTER =====
        st.markdown("---")
        st.markdown("### 📊 Resumen del Sistema")
        
        col1, col2, col3, col4, col5 = st.columns(5)  # Una columna adicional
        
        with col1:
            st.metric("Total Registros", len(registros_df))
        
        with col2:
            total_con_funcionario = len(registros_df[registros_df['Funcionario'].notna() & (registros_df['Funcionario'] != '')])
            st.metric("Con Funcionario", total_con_funcionario)
        
        with col3:
            en_proceso = len(registros_df[registros_df['Estado'].isin(['En proceso', 'En proceso oficio de cierre'])])
            st.metric("En Proceso", en_proceso)
        
        with col4:
            # Mostrar estado del respaldo
            if fecha_ultimo_respaldo:
                if isinstance(fecha_ultimo_respaldo, datetime):
                    tiempo_respaldo = fecha_ultimo_respaldo.strftime("%H:%M")
                    st.metric("Último Respaldo", tiempo_respaldo)
                else:
                    st.metric("Respaldo", "Disponible")
            else:
                st.metric("Respaldo", "Sin datos")
        
        with col5:
            ultima_actualizacion = datetime.now().strftime("%H:%M")
            st.metric("Actualizado", ultima_actualizacion)

        # Información de versión con características de seguridad
        st.info("""
        **🛡️ Tablero de Control Ultra Seguro - Datos Temáticos - Ideca**
        
        **Características de Seguridad Implementadas:**
        - ✅ Verificación automática de integridad de datos
        - ✅ Respaldo automático antes de cualquier modificación  
        - ✅ Restauración automática en caso de pérdida de datos
        - ✅ Respaldos locales adicionales como seguridad extra
        - ✅ Detección automática de datos corruptos o vacíos
        - ✅ Sistema de alertas en tiempo real sobre el estado de respaldos
        - ✅ Panel de restauración manual para casos especiales
        
        **Protección Anti-Pérdida de Datos:** Si la tabla Registros se borra accidentalmente, 
        el sistema detectará automáticamente el problema y restaurará los datos desde el último respaldo válido.
        """)

    except Exception as e:
        st.error(f"Error crítico: {str(e)}")
        
        # Información detallada del error para debugging
        import traceback
        with st.expander("Detalles del Error (para debugging)"):
            st.code(traceback.format_exc())
        
        st.markdown("### 🛡️ Sistema de Recuperación de Emergencia")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            **🚨 Problemas Detectados:**
            - Error crítico en el sistema
            - Posible corrupción de datos
            - Problemas de conexión a Google Sheets
            - Fallo en el sistema de respaldos
            """)
        
        with col2:
            st.markdown("""
            **🔧 Acciones de Recuperación:**
            - Usar "Recuperación de Emergencia" abajo
            - Verificar respaldos disponibles
            - Revisar configuración de Google Sheets
            - Consultar registros de actividad del sistema
            """)
        
        # Sistema de recuperación de emergencia mejorado
        st.markdown("---")
        st.markdown("### 🚨 Recuperación de Emergencia")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🔄 Recuperación Automática", type="primary"):
                try:
                    # Intentar restauración automática de emergencia
                    from backup_utils import restauracion_automatica_emergencia
                    exito, df = restauracion_automatica_emergencia()
                    if exito:
                        st.success("✅ Recuperación exitosa")
                        st.rerun()
                    else:
                        st.error("❌ Recuperación automática falló")
                except Exception as recovery_error:
                    st.error(f"❌ Error en recuperación: {recovery_error}")
        
        with col2:
            if st.button("🔍 Verificar Respaldos"):
                try:
                    from backup_utils import verificar_disponibilidad_respaldo
                    tiene_respaldo, info = verificar_disponibilidad_respaldo()
                    
                    if tiene_respaldo:
                        st.success(f"✅ Respaldo encontrado: {info['registros']} registros")
                        if info['valido']:
                            st.info("💾 Respaldo válido y listo para usar")
                        else:
                            st.warning(f"⚠️ Respaldo disponible pero: {info['mensaje']}")
                    else:
                        st.error("❌ No se encontraron respaldos")
                        
                except Exception as backup_error:
                    st.error(f"❌ Error verificando respaldos: {backup_error}")
        
        with col3:
            if st.button("🔄 Reiniciar Sistema"):
                # Limpiar todo el estado y reiniciar
                for key in list(st.session_state.keys()):
                    if not key.startswith('_'):  # Mantener variables internas de Streamlit
                        del st.session_state[key]
                st.rerun()

        # Información adicional de contacto o soporte
        st.markdown("---")
        st.warning("""
        **📞 Si el problema persiste:**
        1. Verificar la conexión a internet
        2. Revisar permisos de Google Sheets
        3. Contactar al administrador del sistema
        4. Documentar el error para soporte técnico
        """)
# Sistema de recuperación de emergencia
        st.markdown("---")
        st.markdown("### 🚨 Sistema de Recuperación")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🔄 Recuperación Automática", type="primary"):
                try:
                    from backup_utils import restauracion_automatica_emergencia
                    exito, df = restauracion_automatica_emergencia()
                    if exito:
                        st.success("✅ Recuperación exitosa")
                        st.rerun()
                    else:
                        st.error("❌ Falló la recuperación automática")
                except Exception as e:
                    st.error(f"❌ Error: {e}")
        
        with col2:
            if st.button("🔍 Verificar Respaldos"):
                try:
                    from backup_utils import verificar_disponibilidad_respaldo
                    tiene_respaldo, info = verificar_disponibilidad_respaldo()
                    if tiene_respaldo:
                        st.success(f"✅ Respaldo: {info['registros']} registros")
                    else:
                        st.error("❌ Sin respaldos")
                except Exception as e:
                    st.error(f"❌ Error: {e}")
        
        with col3:
            if st.button("🔄 Reiniciar Sistema"):
                for key in list(st.session_state.keys()):
                    if not key.startswith('_'):
                        del st.session_state[key]
                st.rerun()

if __name__ == "__main__":
    main()
        

        
