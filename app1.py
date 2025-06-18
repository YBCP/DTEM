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
from auth_utils import verificar_autenticacion, mostrar_login, mostrar_estado_autenticacion, requiere_autenticacion

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

@requiere_autenticacion
def cargar_datos_desde_excel_autenticado(uploaded_file):
    """Función protegida para cargar datos desde Excel"""
    return cargar_datos_desde_excel(uploaded_file)

def mostrar_carga_archivos():
    """Muestra la sección de carga de archivos Excel/CSV con autenticación"""
    with st.sidebar.expander("🔒 Cargar Datos desde Excel (Admin)", expanded=False):
        st.markdown("### Subir Archivo Excel")
        
        if not verificar_autenticacion():
            st.warning("🔒 Función disponible solo para administradores")
            st.info("Inicia sesión en 'Acceso Administrativo' para usar esta función")
            return
        
        uploaded_file = st.file_uploader(
            "Selecciona un archivo Excel",
            type=['xlsx', 'xls'],
            help="El archivo se sincronizará automáticamente con Google Sheets"
        )
        
        if uploaded_file is not None:
            if st.button("🔄 Sincronizar con Google Sheets"):
                with st.spinner("Procesando y sincronizando archivo..."):
                    nuevos_registros, nuevas_metas = cargar_datos_desde_excel_autenticado(uploaded_file)
                    
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

def mostrar_edicion_registros(registros_df):
    """Muestra la pestaña de edición de registros - VERSIÓN COMPLETA."""
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

    # Selector de registro - mostrar lista completa de registros para seleccionar
    if registros_df.empty:
        st.warning("No hay registros disponibles para editar.")
        return registros_df

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
                    index=0 if str(row['TipoDato']).upper() == "NUEVO" else 1,
                    key=f"tipo_{indice_seleccionado}",
                    on_change=on_change_callback
                )
                if nuevo_tipo != row['TipoDato']:
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

            # ===== SECCIÓN 2: FUNCIONARIO Y FRECUENCIA =====
            st.markdown("### 2. Responsable y Frecuencia")
            col1, col2 = st.columns(2)
            
            with col1:
                # Funcionario - SISTEMA DINÁMICO
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

            with col2:
                # Frecuencia de actualización
                nueva_frecuencia = st.selectbox(
                    "Frecuencia de actualización",
                    options=["", "Diaria", "Semanal", "Mensual", "Trimestral", "Semestral", "Anual"],
                    index=["", "Diaria", "Semanal", "Mensual", "Trimestral", "Semestral", "Anual"].index(
                        row.get('Frecuencia actualizacion ', '')) if row.get('Frecuencia actualizacion ', '') in ["", "Diaria",
                                                                                                      "Semanal",
                                                                                                      "Mensual",
                                                                                                      "Trimestral",
                                                                                                      "Semestral",
                                                                                                      "Anual"] else 0,
                    key=f"frecuencia_{indice_seleccionado}",
                    on_change=on_change_callback
                )
                if nueva_frecuencia != row.get('Frecuencia actualizacion ', ''):
                    registros_df.at[registros_df.index[indice_seleccionado], 'Frecuencia actualizacion '] = nueva_frecuencia
                    edited = True

            # ===== SECCIÓN 3: FECHAS DE ENTREGA =====
            st.markdown("### 3. Fechas de Entrega")
            col1, col2, col3 = st.columns(3)
            
            with col1:
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

            with col2:
                # Plazo de análisis - CALCULADO AUTOMÁTICAMENTE
                plazo_analisis_actual = row.get('Plazo de análisis', '')
                st.text_input(
                    "Plazo de análisis (calculado automáticamente)",
                    value=plazo_analisis_actual,
                    disabled=True,
                    key=f"plazo_analisis_{indice_seleccionado}",
                    help="Se calcula automáticamente como 5 días hábiles después de la fecha de entrega de información"
                )

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

            # ===== SECCIÓN 4: FECHAS PRINCIPALES =====
            st.markdown("### 4. Fechas de Hitos Principales")
            
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

            # ===== SECCIÓN 5: PUBLICACIÓN Y CIERRE =====
            st.markdown("### 5. Publicación y Cierre")
            col1, col2, col3 = st.columns(3)
            
            with col1:
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

            with col2:
                # Plazo de oficio de cierre - CALCULADO AUTOMÁTICAMENTE
                plazo_oficio_actual = row.get('Plazo de oficio de cierre', '')
                st.text_input(
                    "Plazo de oficio de cierre (calculado automáticamente)",
                    value=plazo_oficio_actual,
                    disabled=True,
                    key=f"plazo_oficio_{indice_seleccionado}",
                    help="Se calcula automáticamente como 7 días hábiles después de la fecha de publicación"
                )

            with col3:
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

            # ===== SECCIÓN 6: ESTADO Y OBSERVACIONES =====
            st.markdown("### 6. Estado y Observaciones")
            col1, col2 = st.columns(2)
            
            with col1:
                # Estado
                opciones_estado = ["", "En proceso", "En proceso oficio de cierre", "Completado", "Finalizado"]
                nuevo_estado = st.selectbox(
                    "Estado",
                    options=opciones_estado,
                    index=opciones_estado.index(row.get('Estado', '')) if row.get('Estado', '') in opciones_estado else 0,
                    key=f"estado_{indice_seleccionado}",
                    on_change=on_change_callback
                )
                if nuevo_estado != row.get('Estado', ''):
                    registros_df.at[registros_df.index[indice_seleccionado], 'Estado'] = nuevo_estado
                    edited = True
            
            with col2:
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

            # Información de avance al final
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

# ========== FUNCIÓN DASHBOARD ==========

def mostrar_dashboard(df_filtrado, metas_nuevas_df, metas_actualizar_df, registros_df, 
                     entidad_seleccionada, funcionario_seleccionado, nivel_seleccionado):
    """Muestra el dashboard principal con métricas y gráficos - VERSIÓN FUNCIONAL."""
    
    # Mostrar métricas generales
    st.markdown('<div class="subtitle">Métricas Generales</div>', unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        total_registros = len(df_filtrado)
        st.metric("Total Registros", total_registros)

    with col2:
        avance_promedio = df_filtrado['Porcentaje Avance'].mean() if not df_filtrado.empty else 0
        st.metric("Avance Promedio", f"{avance_promedio:.1f}%")

    with col3:
        registros_completados = len(df_filtrado[df_filtrado['Porcentaje Avance'] == 100])
        st.metric("Registros Completados", registros_completados)

    with col4:
        porcentaje_completados = (registros_completados / total_registros * 100) if total_registros > 0 else 0
        st.metric("% Completados", f"{porcentaje_completados:.1f}%")

    # Comparación con metas
    st.markdown('<div class="subtitle">Comparación con Metas</div>', unsafe_allow_html=True)

    try:
        # Calcular comparación con metas
        comparacion_nuevos, comparacion_actualizar, fecha_meta = comparar_avance_metas(df_filtrado, metas_nuevas_df,
                                                                                       metas_actualizar_df)

        # Mostrar fecha de la meta
        st.markdown(f"**Meta más cercana a la fecha actual: {fecha_meta.strftime('%d/%m/%Y')}**")

        # Mostrar comparación en dos columnas
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### Registros Nuevos")
            st.dataframe(comparacion_nuevos, use_container_width=True)

        with col2:
            st.markdown("### Registros a Actualizar")
            st.dataframe(comparacion_actualizar, use_container_width=True)

        # Gráfico de barras de comparación
        try:
            # Crear gráfico combinado
            fig = go.Figure()
            
            hitos = list(comparacion_nuevos.index)
            
            # Barras para registros nuevos
            fig.add_trace(go.Bar(
                name='Completados (Nuevos)',
                x=hitos,
                y=comparacion_nuevos['Completados'],
                marker_color='lightblue'
            ))
            
            fig.add_trace(go.Bar(
                name='Meta (Nuevos)',
                x=hitos,
                y=comparacion_nuevos['Meta'],
                marker_color='blue',
                opacity=0.7
            ))
            
            # Barras para registros a actualizar
            fig.add_trace(go.Bar(
                name='Completados (Actualizar)',
                x=hitos,
                y=comparacion_actualizar['Completados'],
                marker_color='lightgreen'
            ))
            
            fig.add_trace(go.Bar(
                name='Meta (Actualizar)',
                x=hitos,
                y=comparacion_actualizar['Meta'],
                marker_color='green',
                opacity=0.7
            ))

            fig.update_layout(
                title='Comparación: Completados vs Metas por Hito',
                xaxis_title='Hitos',
                yaxis_title='Cantidad',
                barmode='group',
                height=400
            )

            st.plotly_chart(fig, use_container_width=True)
            
        except Exception as e:
            st.warning(f"Error al crear gráfico de comparación: {e}")

    except Exception as e:
        st.warning(f"Error al mostrar comparación con metas: {e}")

    # Diagrama de Gantt condicionado
    st.markdown('<div class="subtitle">Diagrama de Gantt</div>', unsafe_allow_html=True)

    # Verificar si hay filtros específicos aplicados
    filtros_aplicados = (
        entidad_seleccionada != 'Todas' or 
        funcionario_seleccionado != 'Todos' or 
        nivel_seleccionado != 'Todos'
    )

    if filtros_aplicados:
        # Crear el diagrama de Gantt solo si hay filtros
        try:
            fig_gantt = crear_gantt(df_filtrado)
            if fig_gantt is not None:
                st.plotly_chart(fig_gantt, use_container_width=True)
            else:
                st.warning("No hay datos suficientes para crear el diagrama de Gantt con los filtros aplicados.")
        except Exception as e:
            st.error(f"Error al crear diagrama de Gantt: {e}")
    else:
        # Mostrar mensaje cuando no hay filtros aplicados
        st.info("Para visualizar el diagrama de Gantt seleccione la entidad o funcionario de su interés.")

    # Distribución por estado
    st.markdown('<div class="subtitle">Distribución por Estado</div>', unsafe_allow_html=True)
    
    try:
        if not df_filtrado.empty and 'Estado' in df_filtrado.columns:
            # Contar registros por estado
            estados_count = df_filtrado['Estado'].value_counts()
            
            if not estados_count.empty:
                # Crear gráfico de pastel
                fig_pie = px.pie(
                    values=estados_count.values,
                    names=estados_count.index,
                    title='Distribución de Registros por Estado'
                )
                st.plotly_chart(fig_pie, use_container_width=True)
            else:
                st.info("No hay datos de estado para mostrar.")
        else:
            st.info("No hay datos disponibles para mostrar la distribución por estado.")
    except Exception as e:
        st.warning(f"Error al crear gráfico de distribución: {e}")

    # Tabla de registros con porcentaje de avance
    st.markdown('<div class="subtitle">Detalle de Registros</div>', unsafe_allow_html=True)

    # Definir el orden de las columnas
    columnas_mostrar = [
        'Cod', 'Entidad', 'Nivel Información ', 'Funcionario', 'Mes Proyectado',
        'TipoDato', 'Análisis y cronograma', 'Estándares', 'Publicación',
        'Fecha de oficio de cierre', 'Estado', 'Porcentaje Avance'
    ]

    # Mostrar tabla
    try:
        # Verificar que todas las columnas existan
        columnas_mostrar_existentes = [col for col in columnas_mostrar if col in df_filtrado.columns]
        df_mostrar = df_filtrado[columnas_mostrar_existentes].copy()

        # Aplicar formato a las fechas
        columnas_fecha = ['Análisis y cronograma', 'Estándares', 'Publicación', 'Fecha de oficio de cierre']

        for col in columnas_fecha:
            if col in df_mostrar.columns:
                df_mostrar[col] = df_mostrar[col].apply(lambda x: formatear_fecha(x) if es_fecha_valida(x) else "")

        # Mostrar el dataframe
        st.dataframe(df_mostrar, use_container_width=True)

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

    except Exception as e:
        st.error(f"Error al mostrar la tabla de registros: {e}")
        if 'columnas_mostrar_existentes' in locals():
            st.dataframe(df_filtrado[columnas_mostrar_existentes])

# ========== FUNCIÓN ALERTAS ==========

def mostrar_alertas_vencimientos(registros_df):
    """Muestra alertas de vencimientos de fechas en los registros - VERSIÓN FUNCIONAL."""
    st.markdown('<div class="subtitle">Alertas de Vencimientos</div>', unsafe_allow_html=True)

    # Fecha actual para comparaciones
    fecha_actual = datetime.now().date()

    # Función para calcular días de diferencia
    def calcular_dias_diferencia(fecha_str):
        if not fecha_str or pd.isna(fecha_str) or fecha_str == '':
            return None
        
        fecha = procesar_fecha(fecha_str)
        if fecha is None:
            return None
        
        # Convertir a date si es datetime
        if isinstance(fecha, datetime):
            fecha = fecha.date()
        
        return (fecha - fecha_actual).days

    # Procesar alertas
    alertas = []
    
    for idx, row in registros_df.iterrows():
        try:
            cod = row.get('Cod', '')
            entidad = row.get('Entidad', '')
            nivel = row.get('Nivel Información ', '')
            funcionario = row.get('Funcionario', '')
            
            # Verificar fechas programadas vs reales
            campos_verificar = [
                ('Análisis y cronograma', 'Análisis y cronograma'),
                ('Estándares', 'Estándares'),
                ('Publicación', 'Publicación')
            ]
            
            for campo, campo_real in campos_verificar:
                fecha_real = row.get(campo_real, '')
                
                # Si no hay fecha real, verificar si debería haberla
                if not fecha_real or pd.isna(fecha_real) or fecha_real == '':
                    # Crear alerta por falta de fecha
                    alertas.append({
                        'Cod': cod,
                        'Entidad': entidad,
                        'Nivel Información': nivel,
                        'Funcionario': funcionario,
                        'Tipo Alerta': campo,
                        'Estado': 'Pendiente',
                        'Prioridad': 'Media',
                        'Descripción': f'{campo} sin fecha completada'
                    })
                else:
                    # Verificar si hay retraso comparando con plazos
                    if campo == 'Análisis y cronograma':
                        plazo = row.get('Plazo de cronograma', '')
                        if plazo and pd.notna(plazo) and plazo != '':
                            dias_diff = calcular_dias_diferencia(plazo)
                            if dias_diff is not None and dias_diff < -5:  # Más de 5 días de retraso
                                alertas.append({
                                    'Cod': cod,
                                    'Entidad': entidad,
                                    'Nivel Información': nivel,
                                    'Funcionario': funcionario,
                                    'Tipo Alerta': f'{campo} - Retraso',
                                    'Estado': 'Atrasado',
                                    'Prioridad': 'Alta',
                                    'Descripción': f'{campo} completado con retraso respecto al plazo'
                                })
            
            # Verificar oficio de cierre
            fecha_oficio = row.get('Fecha de oficio de cierre', '')
            fecha_publicacion = row.get('Publicación', '')
            
            if fecha_publicacion and pd.notna(fecha_publicacion) and fecha_publicacion != '':
                if not fecha_oficio or pd.isna(fecha_oficio) or fecha_oficio == '':
                    # Verificar si ya pasó suficiente tiempo desde la publicación
                    dias_pub = calcular_dias_diferencia(fecha_publicacion)
                    if dias_pub is not None and dias_pub < -7:  # Más de 7 días desde publicación
                        alertas.append({
                            'Cod': cod,
                            'Entidad': entidad,
                            'Nivel Información': nivel,
                            'Funcionario': funcionario,
                            'Tipo Alerta': 'Oficio de cierre',
                            'Estado': 'Atrasado',
                            'Prioridad': 'Alta',
                            'Descripción': 'Oficio de cierre pendiente después de publicación'
                        })
                    else:
                        alertas.append({
                            'Cod': cod,
                            'Entidad': entidad,
                            'Nivel Información': nivel,
                            'Funcionario': funcionario,
                            'Tipo Alerta': 'Oficio de cierre',
                            'Estado': 'Pendiente',
                            'Prioridad': 'Media',
                            'Descripción': 'Oficio de cierre pendiente'
                        })
        
        except Exception as e:
            continue
    
    # Mostrar alertas
    if alertas:
        df_alertas = pd.DataFrame(alertas)
        
        # Mostrar estadísticas
        st.markdown("### Resumen de Alertas")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_alertas = len(df_alertas)
            st.metric("Total Alertas", total_alertas)
        
        with col2:
            alta_prioridad = len(df_alertas[df_alertas['Prioridad'] == 'Alta'])
            st.metric("Alta Prioridad", alta_prioridad)
        
        with col3:
            pendientes = len(df_alertas[df_alertas['Estado'] == 'Pendiente'])
            st.metric("Pendientes", pendientes)
        
        with col4:
            entidades_afectadas = df_alertas['Entidad'].nunique()
            st.metric("Entidades Afectadas", entidades_afectadas)
        
        # Gráfico de alertas por tipo
        try:
            st.markdown("### Distribución de Alertas")
            
            # Por tipo de alerta
            col1, col2 = st.columns(2)
            
            with col1:
                tipo_count = df_alertas['Tipo Alerta'].value_counts()
                fig_tipo = px.bar(
                    x=tipo_count.index,
                    y=tipo_count.values,
                    title='Alertas por Tipo',
                    labels={'x': 'Tipo de Alerta', 'y': 'Cantidad'}
                )
                st.plotly_chart(fig_tipo, use_container_width=True)
            
            with col2:
                prioridad_count = df_alertas['Prioridad'].value_counts()
                fig_prioridad = px.pie(
                    values=prioridad_count.values,
                    names=prioridad_count.index,
                    title='Alertas por Prioridad'
                )
                st.plotly_chart(fig_prioridad, use_container_width=True)
                
        except Exception as e:
            st.warning(f"Error al crear gráficos: {e}")
        
        # Filtros para alertas
        st.markdown("### Filtrar Alertas")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            tipos_alerta = ['Todos'] + list(df_alertas['Tipo Alerta'].unique())
            tipo_filtro = st.selectbox("Tipo de Alerta", tipos_alerta)
        
        with col2:
            prioridades = ['Todas'] + list(df_alertas['Prioridad'].unique())
            prioridad_filtro = st.selectbox("Prioridad", prioridades)
        
        with col3:
            estados = ['Todos'] + list(df_alertas['Estado'].unique())
            estado_filtro = st.selectbox("Estado", estados)
        
        # Aplicar filtros
        df_alertas_filtrado = df_alertas.copy()
        
        if tipo_filtro != 'Todos':
            df_alertas_filtrado = df_alertas_filtrado[df_alertas_filtrado['Tipo Alerta'] == tipo_filtro]
        
        if prioridad_filtro != 'Todas':
            df_alertas_filtrado = df_alertas_filtrado[df_alertas_filtrado['Prioridad'] == prioridad_filtro]
        
        if estado_filtro != 'Todos':
            df_alertas_filtrado = df_alertas_filtrado[df_alertas_filtrado['Estado'] == estado_filtro]
        
        # Mostrar tabla de alertas
        st.markdown("### Listado de Alertas")
        
        # Aplicar colores según prioridad
        def highlight_prioridad(row):
            if row['Prioridad'] == 'Alta':
                return ['background-color: #fee2e2'] * len(row)
            elif row['Prioridad'] == 'Media':
                return ['background-color: #fef3c7'] * len(row)
            else:
                return ['background-color: #f0f9ff'] * len(row)
        
        try:
            styled_df = df_alertas_filtrado.style.apply(highlight_prioridad, axis=1)
            st.dataframe(styled_df, use_container_width=True)
        except:
            st.dataframe(df_alertas_filtrado, use_container_width=True)
        
        # Botón para descargar alertas
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_alertas_filtrado.to_excel(writer, sheet_name='Alertas', index=False)

        excel_data = output.getvalue()
        st.download_button(
            label="Descargar alertas como Excel",
            data=excel_data,
            file_name="alertas_vencimientos.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            help="Descarga las alertas en formato Excel"
        )
    else:
        st.success("¡No hay alertas pendientes!")
        
        # Mostrar mensaje motivacional
        st.balloons()
        st.markdown("""
        ### 🎉 ¡Excelente trabajo!
        
        No se han detectado alertas pendientes en este momento. Esto significa que:
        
        ✅ Los procesos están al día  
        ✅ No hay retrasos significativos  
        ✅ El seguimiento está funcionando correctamente  
        
        **Continúa con el excelente trabajo de seguimiento.**
        """)

# ========== FUNCIÓN REPORTES ==========

def mostrar_reportes(registros_df, tipo_dato_filtro, acuerdo_filtro, analisis_filtro, 
                    estandares_filtro, publicacion_filtro, finalizado_filtro, mes_filtro):
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
        st.metric("Total Filtrados", total_filtrados)

    with col2:
        if total_filtrados > 0:
            avance_promedio = df_filtrado['Porcentaje Avance'].mean()
            st.metric("Avance Promedio", f"{avance_promedio:.1f}%")
        else:
            st.metric("Avance Promedio", "0%")

    with col3:
        if total_filtrados > 0:
            completados = len(df_filtrado[df_filtrado['Porcentaje Avance'] == 100])
            st.metric("Completados", completados)
        else:
            st.metric("Completados", "0")

    with col4:
        if total_filtrados > 0:
            porcentaje_completados = (len(df_filtrado[df_filtrado['Porcentaje Avance'] == 100]) / total_filtrados * 100)
            st.metric("% Completados", f"{porcentaje_completados:.1f}%")
        else:
            st.metric("% Completados", "0%")

    # Gráfico de distribución de avance
    if total_filtrados > 0:
        st.markdown("### Distribución del Avance")
        
        try:
            # Crear categorías de avance
            def categorizar_avance(porcentaje):
                if porcentaje == 0:
                    return "Sin iniciar (0%)"
                elif porcentaje < 25:
                    return "Inicial (1-24%)"
                elif porcentaje < 50:
                    return "En progreso bajo (25-49%)"
                elif porcentaje < 75:
                    return "En progreso alto (50-74%)"
                elif porcentaje < 100:
                    return "Casi completo (75-99%)"
                else:
                    return "Completado (100%)"
            
            df_filtrado['Categoria Avance'] = df_filtrado['Porcentaje Avance'].apply(categorizar_avance)
            
            # Contar por categoría
            categoria_count = df_filtrado['Categoria Avance'].value_counts()
            
            # Crear gráfico de barras horizontal
            fig_avance = px.bar(
                x=categoria_count.values,
                y=categoria_count.index,
                orientation='h',
                title='Distribución de Registros por Nivel de Avance',
                labels={'x': 'Cantidad de Registros', 'y': 'Nivel de Avance'},
                color=categoria_count.values,
                color_continuous_scale='RdYlGn'
            )
            
            st.plotly_chart(fig_avance, use_container_width=True)
            
        except Exception as e:
            st.warning(f"Error al crear gráfico de avance: {e}")

    # Mostrar tabla de registros filtrados
    st.markdown("### Tabla de Registros")
    
    if df_filtrado.empty:
        st.warning("No se encontraron registros que coincidan con los filtros seleccionados.")
        return
    
    # Definir columnas a mostrar
    columnas_mostrar = [
        'Cod', 'Entidad', 'Nivel Información ', 'Funcionario', 'Mes Proyectado',
        'TipoDato', 'Análisis y cronograma', 'Estándares', 'Publicación',
        'Fecha de oficio de cierre', 'Estado', 'Porcentaje Avance'
    ]
    
    # Verificar que todas las columnas existan
    columnas_mostrar_existentes = [col for col in columnas_mostrar if col in df_filtrado.columns]
    df_mostrar = df_filtrado[columnas_mostrar_existentes].copy()
    
    # Aplicar formato a las fechas
    columnas_fecha = ['Análisis y cronograma', 'Estándares', 'Publicación', 'Fecha de oficio de cierre']
    
    for col in columnas_fecha:
        if col in df_mostrar.columns:
            df_mostrar[col] = df_mostrar[col].apply(lambda x: formatear_fecha(x) if es_fecha_valida(x) else "")
    
    # Mostrar dataframe con formato condicional
    try:
        # Aplicar formato condicional al porcentaje de avance
        def highlight_avance(val):
            if pd.isna(val):
                return ''
            if val == 100:
                return 'background-color: #dcfce7; color: #166534'  # Verde
            elif val >= 75:
                return 'background-color: #dbeafe; color: #1e40af'  # Azul
            elif val >= 50:
                return 'background-color: #fef3c7; color: #b45309'  # Amarillo
            elif val >= 25:
                return 'background-color: #fed7aa; color: #c2410c'  # Naranja
            else:
                return 'background-color: #fee2e2; color: #b91c1c'  # Rojo
        
        styled_df = df_mostrar.style.applymap(highlight_avance, subset=['Porcentaje Avance'])
        st.dataframe(styled_df, use_container_width=True)
        
    except:
        # Si falla el formato, mostrar sin estilo
        st.dataframe(df_mostrar, use_container_width=True)
    
    # Botón para descargar reporte
    st.markdown("### Descargar Reporte")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Descargar como Excel
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_mostrar.to_excel(writer, sheet_name='Reporte Filtrado', index=False)

        excel_data = output.getvalue()
        st.download_button(
            label="📊 Descargar como Excel",
            data=excel_data,
            file_name=f"reporte_registros_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            help="Descarga el reporte filtrado en formato Excel"
        )
    
    with col2:
        # Descargar como CSV
        csv = df_mostrar.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📄 Descargar como CSV",
            data=csv,
            file_name=f"reporte_registros_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            help="Descarga el reporte filtrado en formato CSV"
        )
    
    with col3:
        # Crear reporte resumido
        if st.button("📋 Generar Reporte Resumido"):
            # Crear reporte ejecutivo
            resumen = {
                'Fecha del Reporte': datetime.now().strftime('%d/%m/%Y %H:%M'),
                'Total de Registros': len(df_mostrar),
                'Registros Completados': len(df_mostrar[df_mostrar['Porcentaje Avance'] == 100]),
                'Registros en Proceso': len(df_mostrar[(df_mostrar['Porcentaje Avance'] > 0) & (df_mostrar['Porcentaje Avance'] < 100)]),
                'Registros Sin Iniciar': len(df_mostrar[df_mostrar['Porcentaje Avance'] == 0]),
                'Avance Promedio': f"{df_mostrar['Porcentaje Avance'].mean():.1f}%"
            }
            
            # Mostrar resumen
            st.markdown("#### 📋 Reporte Ejecutivo")
            for key, value in resumen.items():
                st.write(f"**{key}:** {value}")
    
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

# ========== FUNCIÓN PRINCIPAL ==========

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
        st.markdown('<div class="title">🔐 Tablero de Control de Seguimiento de Datos Temáticos - Ideca</div>',
                    unsafe_allow_html=True)
        
        # ===== SIDEBAR CON AUTENTICACIÓN =====
        # Sistema de autenticación
        mostrar_login()
        mostrar_estado_autenticacion()
        
        # Configuración de Google Sheets
        mostrar_configuracion_sheets()
        
        # Carga de archivos Excel (PROTEGIDA)
        mostrar_carga_archivos()

        # Información sobre el tablero
        st.sidebar.markdown('<div class="subtitle">Información</div>', unsafe_allow_html=True)
        st.sidebar.markdown("""
        <div class="info-box">
        <p><strong>Tablero de Control de Cronogramas</strong></p>
        <p><strong>VERSIÓN COMPLETA Y FUNCIONAL</strong></p>
        <ul>
        <li>🔐 Sistema de autenticación</li>
        <li>📊 Dashboard interactivo</li>
        <li>✏️ Edición completa de registros</li>
        <li>🚨 Sistema de alertas inteligente</li>
        <li>📋 Reportes avanzados</li>
        <li>🔄 Sincronización automática</li>
        </ul>
        </div>
        """, unsafe_allow_html=True)

        # Mover la carga de datos dentro del expander "Estado del Sistema"
        with st.expander("Estado del Sistema", expanded=False):
            # Estado de conexión y autenticación
            col1, col2, col3 = st.columns([2, 2, 1])
            
            with col1:
                st.info("📊 Datos sincronizados con Google Sheets en tiempo real")
            
            with col2:
                if verificar_autenticacion():
                    st.success("🔐 Sesión administrativa activa")
                else:
                    st.warning("⚠️ Sesión no administrativa")
            
            with col3:
                if st.button("🔄 Reconectar"):
                    # Limpiar cache y reconectar
                    if 'sheets_manager' in st.session_state:
                        del st.session_state.sheets_manager
                    st.rerun()
            
            # Carga de datos
            st.markdown("---")
            st.markdown("**Carga de Datos:**")
            
            with st.spinner("Cargando datos desde Google Sheets..."):
                registros_df, meta_df = cargar_datos()

            # Verificar si los DataFrames están vacíos
            if registros_df.empty:
                st.warning("No hay datos de registros en Google Sheets.")
                
                # Crear estructura mínima para que la app funcione
                registros_df = pd.DataFrame(columns=[
                    'Cod', 'Entidad', 'TipoDato', 'Nivel Información ', 'Mes Proyectado',
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
            'Nivel Información ', 'Mes Proyectado', 'Fecha de entrega de información',
            'Plazo de análisis', 'Plazo de cronograma', 'Plazo de oficio de cierre',
            'Funcionario', 'Frecuencia actualizacion ', 'Estado', 'Observación',
            'Fecha de oficio de cierre'
        ]

        for columna in columnas_requeridas:
            if columna not in registros_df.columns:
                registros_df[columna] = ''

        # ===== APLICAR VALIDACIONES Y CÁLCULOS =====
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
        with st.expander("Validación de Reglas de Negocio", expanded=False):
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
            
            **Funcionalidades implementadas:**
            8. 🔐 Sistema de autenticación para funciones administrativas
            9. 📅 Campo "Mes Proyectado" para organización temporal
            10. 🔍 Filtro por mes en reportes para análisis específicos
            11. 📊 Dashboard completo con gráficos interactivos
            12. 🚨 Sistema de alertas inteligente con prioridades
            13. 📋 Reportes ejecutivos con visualizaciones
            14. 🎨 Interfaz mejorada con formato condicional
            """)
            mostrar_estado_validaciones(registros_df, st)

        # ===== CREAR PESTAÑAS =====
        tab1, tab2, tab3, tab4 = st.tabs([
            "📊 Dashboard", 
            "✏️ Edición de Registros", 
            "🚨 Alertas de Vencimientos", 
            "📋 Reportes"
        ])
     
        # ===== TAB 1: DASHBOARD =====
        with tab1:
            st.markdown("### 🔍 Filtros")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                # Filtro por entidad
                entidades = ['Todas'] + sorted([e for e in registros_df['Entidad'].unique().tolist() if e])
                entidad_seleccionada = st.selectbox('🏢 Entidad', entidades, key="dash_entidad")
            
            with col2:
                # Filtro por funcionario
                funcionarios = ['Todos']
                if 'Funcionario' in registros_df.columns:
                    funcionarios_unicos = [f for f in registros_df['Funcionario'].dropna().unique().tolist() if f]
                    funcionarios += sorted(funcionarios_unicos)
                funcionario_seleccionado = st.selectbox('👤 Funcionario', funcionarios, key="dash_funcionario")
            
            with col3:
                # Filtro por tipo de dato
                tipos_dato = ['Todos'] + sorted([t for t in registros_df['TipoDato'].dropna().unique().tolist() if t])
                tipo_dato_seleccionado = st.selectbox('📊 Tipo de Dato', tipos_dato, key="dash_tipo")
            
            with col4:
                # Filtro por nivel de información dependiente de entidad
                if entidad_seleccionada != 'Todas':
                    niveles_entidad = registros_df[registros_df['Entidad'] == entidad_seleccionada]['Nivel Información '].dropna().unique().tolist()
                    niveles_entidad = [n for n in niveles_entidad if n]
                    niveles = ['Todos'] + sorted(niveles_entidad)
                    nivel_seleccionado = st.selectbox('📑 Nivel de Información', niveles, key="dash_nivel")
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
            
            # Mostrar dashboard
            mostrar_dashboard(df_filtrado, metas_nuevas_df, metas_actualizar_df, registros_df,
                            entidad_seleccionada, funcionario_seleccionado, nivel_seleccionado)

        # ===== TAB 2: EDICIÓN =====
        with tab2:
            # Llamar a la función de edición
            registros_df = mostrar_edicion_registros(registros_df)

        # ===== TAB 3: ALERTAS =====
        with tab3:
            mostrar_alertas_vencimientos(registros_df)

        # ===== TAB 4: REPORTES =====
        with tab4:
            st.markdown("### 🔍 Filtros de Reportes")
            
            # Primera fila de filtros
            col1, col2, col3 = st.columns(3)
            
            with col1:
                tipos_dato_reporte = ['Todos'] + sorted([t for t in registros_df['TipoDato'].dropna().unique().tolist() if t])
                tipo_dato_reporte = st.selectbox('📊 Tipo de Dato', tipos_dato_reporte, key="reporte_tipo")
            
            with col2:
                acuerdo_opciones = ['Todos', 'Suscrito', 'No Suscrito']
                acuerdo_filtro = st.selectbox('📝 Acuerdo de Compromiso', acuerdo_opciones, key="reporte_acuerdo")
            
            with col3:
                analisis_opciones = ['Todos', 'Completado', 'No Completado']
                analisis_filtro = st.selectbox('📈 Análisis y Cronograma', analisis_opciones, key="reporte_analisis")
            
            # Segunda fila de filtros
            col4, col5, col6 = st.columns(3)
            
            with col4:
                estandares_opciones = ['Todos', 'Completado', 'No Completado']
                estandares_filtro = st.selectbox('⚙️ Estándares', estandares_opciones, key="reporte_estandares")
            
            with col5:
                publicacion_opciones = ['Todos', 'Completado', 'No Completado']
                publicacion_filtro = st.selectbox('📢 Publicación', publicacion_opciones, key="reporte_publicacion")
            
            with col6:
                finalizado_opciones = ['Todos', 'Finalizado', 'No Finalizado']
                finalizado_filtro = st.selectbox('✅ Finalizado', finalizado_opciones, key="reporte_finalizado")
            
            # Tercera fila de filtros
            col7, col8, col9 = st.columns(3)
            
            with col7:
                # FILTRO: Mes Proyectado
                meses_disponibles = ['Todos']
                if 'Mes Proyectado' in registros_df.columns:
                    meses_unicos = [m for m in registros_df['Mes Proyectado'].dropna().unique().tolist() if m]
                    meses_disponibles += sorted(meses_unicos)
                mes_filtro = st.selectbox('📅 Mes Proyectado', meses_disponibles, key="reporte_mes")
            
            st.markdown("---")
            
            # Mostrar reportes
            mostrar_reportes(registros_df, tipo_dato_reporte, acuerdo_filtro, analisis_filtro, 
                           estandares_filtro, publicacion_filtro, finalizado_filtro, mes_filtro)

        # ===== FOOTER =====
        st.markdown("---")
        st.markdown("### 📊 Resumen del Sistema")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("📋 Total Registros", len(registros_df))
        
        with col2:
            total_con_funcionario = len(registros_df[registros_df['Funcionario'].notna() & (registros_df['Funcionario'] != '')])
            st.metric("👤 Con Funcionario", total_con_funcionario)
        
        with col3:
            en_proceso = len(registros_df[registros_df['Estado'].isin(['En proceso', 'En proceso oficio de cierre'])])
            st.metric("⏳ En Proceso", en_proceso)
        
        with col4:
            ultima_actualizacion = datetime.now().strftime("%d/%m/%Y %H:%M")
            st.metric("🕐 Última Actualización", ultima_actualizacion)

        # Información de versión
        st.success("""
        **🎉 Tablero de Control - Versión Completa y Funcional**
        
        ✅ **Todas las funcionalidades implementadas y funcionando:**
        - 🔐 Sistema de autenticación completo (admin/qwerty)
        - 📊 Dashboard interactivo con métricas y gráficos
        - ✏️ Edición completa de registros con interface intuitiva
        - 🚨 Sistema de alertas inteligente con prioridades
        - 📋 Reportes avanzados con filtros y visualizaciones
        - 📅 Campo "Mes Proyectado" totalmente integrado
        - 🔄 Sincronización automática con Google Sheets
        - 🎯 Validaciones de reglas de negocio automáticas
        - 📈 Gráficos interactivos con Plotly
        - 🎨 Interfaz moderna con formato condicional
        """)
        
        # Mostrar estado de autenticación en footer
        if verificar_autenticacion():
            st.success("🔐 Sesión administrativa activa - Todas las funciones disponibles")
        else:
            st.warning("⚠️ Sesión no administrativa - Carga de datos restringida")

    except Exception as e:
        st.error(f"❌ Error crítico: {str(e)}")
        
        # Información detallada del error para debugging
        import traceback
        with st.expander("🔧 Detalles del Error (para debugging)"):
            st.code(traceback.format_exc())
        
        st.markdown("### 🆘 Solución de Problemas")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            **❗ Problemas Comunes:**
            - Configuración de Google Sheets incorrecta
            - Credenciales faltantes o incorrectas
            - Estructura de datos incorrecta en Google Sheets
            - Problemas de conexión a internet
            - Problemas de autenticación
            """)
        
        with col2:
            st.markdown("""
            **🔧 Acciones Recomendadas:**
            - Usar el botón "Reconectar" arriba
            - Verificar configuración en el panel lateral
            - Revisar permisos del service account
            - Consultar las instrucciones de configuración
            - Verificar credenciales de autenticación admin
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

        
