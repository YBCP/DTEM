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
from data_utils import es_fecha_valida
# Importar funciones de autenticación
from auth_utils import mostrar_login, mostrar_estado_autenticacion, verificar_autenticacion


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

def inicializar_estado_temporal(indice_seleccionado, registros_df):
    """
    Inicializa el estado temporal para el registro seleccionado.
    Los cambios se almacenan en session_state hasta que se guarden.
    """
    key_temp = f"temp_registro_{indice_seleccionado}"
    
    # Si no existe estado temporal, crear uno basado en el registro original
    if key_temp not in st.session_state:
        registro_original = registros_df.iloc[indice_seleccionado].copy()
        st.session_state[key_temp] = registro_original.to_dict()
        st.session_state[f"{key_temp}_modified"] = False
    
    return key_temp

def actualizar_campo_temporal(key_temp, campo, nuevo_valor):
    """
    CORREGIDO: Actualiza un campo específico en el estado temporal SIN causar recargas.
    """
    if key_temp in st.session_state:
        if st.session_state[key_temp][campo] != nuevo_valor:
            st.session_state[key_temp][campo] = nuevo_valor
            st.session_state[f"{key_temp}_modified"] = True
            # ✅ NO LLAMAR st.rerun() aquí - esto causaba las recargas


def obtener_valor_temporal(key_temp, campo, valor_default=""):
    """
    MEJORADO: Obtiene el valor actual de un campo desde el estado temporal con mejor manejo de errores.
    """
    try:
        if key_temp in st.session_state and campo in st.session_state[key_temp]:
            valor = st.session_state[key_temp][campo]
            # Manejar valores None o NaN
            if valor is None or (isinstance(valor, float) and pd.isna(valor)):
                return valor_default
            return str(valor).strip() if valor != "" else valor_default
        return valor_default
    except Exception:
        return valor_default


def hay_cambios_pendientes(key_temp):
    """
    MEJORADO: Verifica si hay cambios pendientes en el estado temporal con mejor detección.
    """
    try:
        if f"{key_temp}_modified" in st.session_state:
            return st.session_state[f"{key_temp}_modified"]
        return False
    except Exception:
        return False


def mostrar_mensaje_validacion_oficio_cierre():
    """
    NUEVA FUNCIÓN: Muestra mensajes específicos de validación para oficio de cierre.
    """
    st.error("""
    ❌ **No se puede introducir 'Fecha de oficio de cierre'**
    
    **Requisito:** Debe completar primero la etapa de **'Publicación'** (introducir fecha real de publicación).
    
    **Pasos a seguir:**
    1. Complete la fecha en el campo 'Publicación (fecha real)'
    2. Presione 'Guardar Registro' para aplicar los cambios
    3. Luego podrá introducir la 'Fecha de oficio de cierre'
    """)


def aplicar_validaciones_campo_especifico(key_temp, campo, nuevo_valor):
    """
    NUEVA FUNCIÓN: Aplica validaciones específicas a campos críticos antes del guardado.
    """
    validaciones_pasadas = True
    mensajes_error = []
    
    # Validación específica para Fecha de oficio de cierre
    if campo == 'Fecha de oficio de cierre' and nuevo_valor and str(nuevo_valor).strip() != '':
        # Verificar que haya fecha de publicación
        publicacion_valor = obtener_valor_temporal(key_temp, 'Publicación', '')
        if not (publicacion_valor and str(publicacion_valor).strip() != ''):
            validaciones_pasadas = False
            mensajes_error.append("Para introducir 'Fecha de oficio de cierre' debe completar primero la etapa de 'Publicación'")
    
    return validaciones_pasadas, mensajes_error
def aplicar_cambios_temporales(registros_df, indice_seleccionado, key_temp):
    """
    Aplica los cambios temporales al DataFrame principal.
    """
    if key_temp in st.session_state:
        # Actualizar el DataFrame con los valores temporales
        for campo, valor in st.session_state[key_temp].items():
            if campo in registros_df.columns:
                registros_df.at[registros_df.index[indice_seleccionado], campo] = valor
    
    return registros_df

def crear_widget_con_callback(widget_type, label, key_temp, campo, **kwargs):
    """
    CORREGIDO: Crea un widget que actualiza automáticamente el estado temporal SIN RECARGAR la página.
    """
    # Obtener valor actual
    valor_actual = obtener_valor_temporal(key_temp, campo, kwargs.get('value', ''))
    
    # Configurar key único para el widget
    widget_key = f"{key_temp}_{campo}_widget"
    
    # ✅ CORREGIDO: Callback simple que NO llama st.rerun()
    def callback_silencioso():
        """Callback que actualiza estado temporal sin recargar la página"""
        if widget_key in st.session_state:
            nuevo_valor = st.session_state[widget_key]
            actualizar_campo_temporal(key_temp, campo, nuevo_valor)
    
    # Crear widget según tipo
    if widget_type == 'selectbox':
        options = kwargs.get('options', [])
        index = options.index(valor_actual) if valor_actual in options else 0
        return st.selectbox(
            label,
            options=options,
            index=index,
            key=widget_key,
            on_change=callback_silencioso,  # ✅ Callback sin recarga
            **{k: v for k, v in kwargs.items() if k not in ['options', 'value']}
        )
    
    elif widget_type == 'text_input':
        return st.text_input(
            label,
            value=valor_actual,
            key=widget_key,
            on_change=callback_silencioso,  # ✅ Callback sin recarga
            **{k: v for k, v in kwargs.items() if k not in ['value']}
        )
    
    elif widget_type == 'text_area':
        return st.text_area(
            label,
            value=valor_actual,
            key=widget_key,
            on_change=callback_silencioso,  # ✅ Callback sin recarga
            **{k: v for k, v in kwargs.items() if k not in ['value']}
        )
    
    return None


def crear_selector_fecha_borrable(label, key_temp, campo, help_text=None):
    """
    CORREGIDO: Selector de fecha especializado que permite borrar completamente SIN RECARGAS AUTOMÁTICAS.
    """
    # Obtener valor actual del estado temporal
    valor_actual = obtener_valor_temporal(key_temp, campo, "")
    widget_key = f"{key_temp}_{campo}_widget"
    
    # Crear contenedor para la fecha
    with st.container():
        # Crear tres columnas: checkbox, fecha, botón borrar
        col_check, col_fecha, col_borrar = st.columns([1, 6, 1])
        
        with col_check:
            # Checkbox para activar/desactivar fecha
            tiene_fecha = bool(valor_actual and valor_actual.strip())
            
            # ✅ CORREGIDO: Callback del checkbox SIN recarga automática
            def callback_checkbox():
                """Callback del checkbox que no recarga automáticamente"""
                if f"check_{widget_key}" in st.session_state:
                    nuevo_estado = st.session_state[f"check_{widget_key}"]
                    if not nuevo_estado:
                        # Si se desactiva el checkbox, limpiar la fecha
                        actualizar_campo_temporal(key_temp, campo, "")
            
            usar_fecha = st.checkbox(
                "📅", 
                value=tiene_fecha,
                key=f"check_{widget_key}",
                help="Marcar para usar fecha",
                on_change=callback_checkbox  # ✅ Sin recarga automática
            )
        
        with col_fecha:
            if usar_fecha:
                # Solo mostrar date_input si está activado
                fecha_valor = fecha_para_selector(valor_actual) if valor_actual else None
                
                # Si no hay fecha válida, usar fecha actual como default
                if fecha_valor is None:
                    fecha_valor = datetime.now().date()
                
                # ✅ CORREGIDO: Callback del date_input SIN recarga automática
                def callback_fecha():
                    """Callback de fecha que no recarga automáticamente"""
                    if widget_key in st.session_state:
                        nueva_fecha = st.session_state[widget_key]
                        fecha_str = fecha_desde_selector_a_string(nueva_fecha)
                        actualizar_campo_temporal(key_temp, campo, fecha_str)
                
                nueva_fecha = st.date_input(
                    label,
                    value=fecha_valor,
                    key=widget_key,
                    help=help_text,
                    on_change=callback_fecha  # ✅ Sin recarga automática
                )
            else:
                # Si no está activado, mostrar campo deshabilitado
                st.text_input(
                    label,
                    value="(Sin fecha asignada)",
                    disabled=True,
                    key=f"disabled_{widget_key}"
                )
        
        with col_borrar:
            if usar_fecha:
                # ✅ CORREGIDO: Botón para limpiar fecha SIN recarga automática
                if st.button("🗑️", key=f"clear_{widget_key}", help="Limpiar fecha"):
                    # Limpiar fecha y desactivar checkbox SILENCIOSAMENTE
                    actualizar_campo_temporal(key_temp, campo, "")
                    # ✅ IMPORTANTE: Marcar que necesita actualización visual pero SIN st.rerun()
                    st.session_state[f"fecha_limpiada_{widget_key}"] = True
                    # Mostrar mensaje temporal
                    st.success("Fecha limpiada (se aplicará al guardar)")
            else:
                # Espaciador visual
                st.write("")
                
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
    """
    CORREGIDO: Muestra la pestaña de edición de registros sin recargas automáticas.
    """
    st.markdown('<div class="subtitle">Edición de Registros</div>', unsafe_allow_html=True)

    st.info(
        "Esta sección permite editar los datos usando selectores de fecha y opciones. Los cambios se aplican al presionar 'Guardar Registro'.")

    # Explicación adicional sobre las fechas y reglas de validación
    st.warning("""
    **Importante**: 
    - ⚠️ **Los cambios se mantienen temporalmente hasta que presione "Guardar Registro"**
    - ✅ **El formulario NO se recarga automáticamente** - solo al presionar "Guardar Registro"
    - Para los campos de fecha, utilice el selector de calendario que aparece.
    - El campo "Plazo de análisis" se calcula automáticamente como 5 días hábiles después de la "Fecha de entrega de información"
    - El campo "Plazo de cronograma" se calcula automáticamente como 3 días hábiles después del "Plazo de análisis"
    - El campo "Plazo de oficio de cierre" se calcula automáticamente como 7 días hábiles después de la fecha real de "Publicación"
    - Las validaciones se aplicarán automáticamente al guardar
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

    # ✅ CORREGIDO: Selector de registro SIN callback automático
    codigos_registros = registros_df['Cod'].astype(str).tolist()
    entidades_registros = registros_df['Entidad'].tolist()
    niveles_registros = registros_df['Nivel Información '].tolist()

    # Crear opciones para el selector combinando información
    opciones_registros = [f"{codigos_registros[i]} - {entidades_registros[i]} - {niveles_registros[i]}"
                          for i in range(len(codigos_registros))]

    # ✅ CORREGIDO: Selector sin callback automático - solo cambia cuando el usuario selecciona
    seleccion_registro = st.selectbox(
        "Seleccione un registro para editar:",
        options=opciones_registros,
        key="selector_registro_main"
        # ✅ NO CALLBACK - solo cambia cuando el usuario selecciona manualmente
    )

    # Obtener el índice del registro seleccionado
    indice_seleccionado = opciones_registros.index(seleccion_registro)

    # Inicializar estado temporal para este registro
    key_temp = inicializar_estado_temporal(indice_seleccionado, registros_df)
    
    # Verificar si hay cambios pendientes
    cambios_pendientes = hay_cambios_pendientes(key_temp)
    
    # Mostrar indicador de cambios pendientes
    if cambios_pendientes:
        st.warning("⚠️ **Hay cambios sin guardar.** Presione 'Guardar Registro' para aplicar los cambios o 'Cancelar Cambios' para descartarlos.")

    # Mostrar el registro seleccionado para edición
    try:
        # Obtener el registro original
        row_original = registros_df.iloc[indice_seleccionado].copy()

        # Contenedor para los datos de edición
        with st.container():
            st.markdown("---")
            # Título del registro
            st.markdown(f"### Editando Registro #{row_original['Cod']} - {row_original['Entidad']}")
            st.markdown(f"**Nivel de Información:** {row_original['Nivel Información ']}")
            st.markdown("---")

            # ===== RESTO DEL FORMULARIO IGUAL PERO SIN RECARGAS =====
            
            # ===== SECCIÓN 1: INFORMACIÓN BÁSICA =====
            st.markdown("### 1. Información Básica")
            col1, col2, col3 = st.columns(3)

            with col1:
                # Campos no editables
                st.text_input("Código", value=row_original['Cod'], disabled=True)

            with col2:
                # Tipo de Dato - USAR WIDGET CON CALLBACK CORREGIDO
                crear_widget_con_callback(
                    'selectbox',
                    "Tipo de Dato",
                    key_temp,
                    'TipoDato',
                    options=["Nuevo", "Actualizar"]
                )

            with col3:
                # Mes Proyectado - USAR WIDGET CON CALLBACK CORREGIDO
                meses = ["", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", 
                        "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
                
                crear_widget_con_callback(
                    'selectbox',
                    "Mes Proyectado",
                    key_temp,
                    'Mes Proyectado',
                    options=meses
                )
            # Frecuencia de actualización y Funcionario
            col1, col2 = st.columns(2)
            with col1:
                freq_opciones = ["", "Diaria", "Semanal", "Mensual", "Trimestral", "Semestral", "Anual"]
                crear_widget_con_callback(
                    'selectbox',
                    "Frecuencia de actualización",
                    key_temp,
                    'Frecuencia actualizacion ',
                    options=freq_opciones
                )

            # Funcionario - SISTEMA DINÁMICO MANTENIDO PERO CON ESTADO TEMPORAL
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
                    key=f"nuevo_funcionario_{key_temp}"
                )

                # Si se introduce un nuevo funcionario, agregarlo a la lista
                if nuevo_funcionario_input and nuevo_funcionario_input not in st.session_state.funcionarios:
                    st.session_state.funcionarios.append(nuevo_funcionario_input)

                # Ordenar la lista de funcionarios alfabéticamente
                funcionarios_ordenados = sorted(st.session_state.funcionarios)
                opciones_funcionarios = [""] + funcionarios_ordenados

                # Crear el selectbox para elegir funcionario
                crear_widget_con_callback(
                    'selectbox',
                    "Seleccionar funcionario",
                    key_temp,
                    'Funcionario',
                    options=opciones_funcionarios
                )

                # Si hay nuevo funcionario ingresado, usarlo
                if nuevo_funcionario_input:
                    actualizar_campo_temporal(key_temp, 'Funcionario', nuevo_funcionario_input)

            # ===== SECCIÓN 2: ACUERDOS Y COMPROMISOS =====
            st.markdown("---")
            st.markdown("### 2. Acuerdos y Compromisos")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Actas de acercamiento
                crear_widget_con_callback(
                    'selectbox',
                    "Actas de acercamiento y manifestación de interés",
                    key_temp,
                    'Actas de acercamiento y manifestación de interés',
                    options=["", "Si", "No"]
                )

                
                # Suscripción acuerdo de compromiso - SELECTOR DE FECHA BORRABLE
                crear_selector_fecha_borrable(
                    "Suscripción acuerdo de compromiso",
                    key_temp,
                    'Suscripción acuerdo de compromiso'
                )

            with col2:
                # Entrega acuerdo de compromiso - SELECTOR DE FECHA
                crear_selector_fecha_borrable(
                    "Entrega acuerdo de compromiso",
                    key_temp,
                    'Entrega acuerdo de compromiso'
                )

                # Acuerdo de compromiso - SELECTBOX
                crear_widget_con_callback(
                    'selectbox',
                    "Acuerdo de compromiso",
                    key_temp,
                    'Acuerdo de compromiso',
                    options=["", "Si", "No"]
                )

            # ===== SECCIÓN 3: GESTIÓN DE INFORMACIÓN =====
            st.markdown("---")
            st.markdown("### 3. Gestión de Información")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                # Gestión acceso a datos
                crear_widget_con_callback(
                    'selectbox',
                    "Gestión acceso a los datos y documentos requeridos",
                    key_temp,
                    'Gestion acceso a los datos y documentos requeridos ',
                    options=["", "Si", "No"]
                )

            with col2:
                # Fecha de entrega de información - SELECTOR DE FECHA BORRABLE
                crear_selector_fecha_borrable(
                    "Fecha de entrega de información",
                    key_temp,
                    'Fecha de entrega de información'
                )

            with col3:
                # Plazo de análisis - CALCULADO AUTOMÁTICAMENTE (mostrar valor temporal)
                plazo_analisis_temp = obtener_valor_temporal(key_temp, 'Plazo de análisis', '')
                st.text_input(
                    "Plazo de análisis (calculado automáticamente)",
                    value=plazo_analisis_temp,
                    disabled=True,
                    key=f"plazo_analisis_display_{key_temp}",
                    help="Se calcula automáticamente como 5 días hábiles después de la fecha de entrega de información"
                )

            # ===== SECCIÓN 4: ANÁLISIS Y CRONOGRAMA =====
            st.markdown("---")
            st.markdown("### 4. Análisis y Cronograma")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                crear_selector_fecha_borrable(
                    "Análisis y cronograma (fecha real)",
                    key_temp,
                    'Análisis y cronograma'
                )

            with col2:
                # Cronograma Concertado
                crear_widget_con_callback(
                    'selectbox',
                    "Cronograma Concertado",
                    key_temp,
                    'Cronograma Concertado',
                    options=["", "Si", "No"]
                )

            with col3:
                # Plazo de cronograma - CALCULADO AUTOMÁTICAMENTE
                plazo_cronograma_temp = obtener_valor_temporal(key_temp, 'Plazo de cronograma', '')
                st.text_input(
                    "Plazo de cronograma (calculado automáticamente)",
                    value=plazo_cronograma_temp,
                    disabled=True,
                    key=f"plazo_cronograma_display_{key_temp}",
                    help="Se calcula automáticamente como 3 días hábiles después del plazo de análisis"
                )

            with col4:
                # Seguimiento a los acuerdos
                crear_widget_con_callback(
                    'selectbox',
                    "Seguimiento a los acuerdos",
                    key_temp,
                    'Seguimiento a los acuerdos',
                    options=["", "Si", "No"]
                )

            
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
                    crear_widget_con_callback(
                        'selectbox',
                        campo,
                        key_temp,
                        campo,
                        options=["", "Completo", "No aplica"]
                    )

            # Fechas de estándares
            st.markdown("#### Fechas de Estándares")
            col1, col2 = st.columns(2)
            
            with col1:
                # Estándares fecha programada - SELECTOR DE FECHA BORRABLE
                crear_selector_fecha_borrable(
                    "Estándares (fecha programada)",
                    key_temp,
                    'Estándares (fecha programada)'
                )

            with col2:
                # Estándares fecha real - SELECTOR DE FECHA BORRABLE
                crear_selector_fecha_borrable(
                    "Estándares (fecha real)",
                    key_temp,
                    'Estándares'
                )

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
                ('Aprobación resultados obtenidos en la orientación', 'aprobacion_resultados'),
                ('Disponer datos temáticos', 'disponer_datos'),
                ('Catálogo de recursos geográficos', 'catalogo_recursos')
            ]
            
            for i, (campo, key_suffix) in enumerate(campos_publicacion):
                col = [col1, col2, col3][i % 3]
                with col:
                    crear_widget_con_callback(
                        'selectbox',
                        campo,
                        key_temp,
                        campo,
                        options=["", "Si", "No"]
                    )

            # Fechas de publicación
            st.markdown("#### Fechas de Publicación")
            col1, col2 = st.columns(2)
            
            with col1:
                # Fecha de publicación programada - SELECTOR DE FECHA BORRABLE
                crear_selector_fecha_borrable(
                    "Fecha de publicación programada",
                    key_temp,
                    'Fecha de publicación programada'
                )

            with col2:
                # Publicación fecha real - SELECTOR DE FECHA BORRABLE
                crear_selector_fecha_borrable(
                    "Publicación (fecha real)",
                    key_temp,
                    'Publicación'
                )

            # ===== SECCIÓN 7: CIERRE =====
            st.markdown("---")
            st.markdown("### 7. Cierre")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                # Plazo de oficio de cierre - CALCULADO AUTOMÁTICAMENTE
                plazo_oficio_temp = obtener_valor_temporal(key_temp, 'Plazo de oficio de cierre', '')
                st.text_input(
                    "Plazo de oficio de cierre (calculado automáticamente)",
                    value=plazo_oficio_temp,
                    disabled=True,
                    key=f"plazo_oficio_display_{key_temp}",
                    help="Se calcula automáticamente como 7 días hábiles después de la fecha de publicación"
                )

                # Oficios de cierre
                crear_widget_con_callback(
                    'selectbox',
                    "Oficios de cierre",
                    key_temp,
                    'Oficios de cierre',
                    options=["", "Si", "No"]
                )

            with col2:
                # Fecha de oficio de cierre - SELECTOR DE FECHA CON VALIDACIÓN
                publicacion_temp = obtener_valor_temporal(key_temp, 'Publicación', '')
                tiene_publicacion = publicacion_temp and pd.notna(publicacion_temp) and str(publicacion_temp).strip() != ''
                
                if not tiene_publicacion:
                    st.warning("⚠️ Para introducir fecha de oficio de cierre, primero debe completar la etapa de Publicación")
                    fecha_oficio_temp = obtener_valor_temporal(key_temp, 'Fecha de oficio de cierre', '')
                    st.text_input(
                        "Fecha de oficio de cierre (requiere publicación)",
                        value=fecha_oficio_temp,
                        disabled=True,
                        key=f"oficio_disabled_{key_temp}"
                    )
                else:
                    crear_selector_fecha_borrable(
                        "Fecha de oficio de cierre",
                        key_temp,
                        'Fecha de oficio de cierre'
                    )

            with col3:
                # Estado
                opciones_estado = ["", "En proceso", "En proceso oficio de cierre", "Completado", "Finalizado"]
                crear_widget_con_callback(
                    'selectbox',
                    "Estado",
                    key_temp,
                    'Estado',
                    options=opciones_estado
                )

            # Observación - CAMPO DE TEXTO AMPLIO
            crear_widget_con_callback(
                'text_area',
                "Observación",
                key_temp,
                'Observación',
                height=100
            )

            # ===== INFORMACIÓN DE AVANCE AL FINAL =====
            st.markdown("---")
            st.markdown("### Información de Avance")
            
            # NUEVO: Calcular porcentaje basado en valores temporales
            registro_temporal = st.session_state[key_temp] if key_temp in st.session_state else row_original.to_dict()
            porcentaje_temporal = calcular_porcentaje_avance(pd.Series(registro_temporal))
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                # Mostrar porcentaje actual vs temporal
                porcentaje_original = calcular_porcentaje_avance(row_original)
                if cambios_pendientes and porcentaje_temporal != porcentaje_original:
                    st.metric(
                        "Porcentaje de Avance", 
                        f"{porcentaje_temporal}%",
                        delta=f"{porcentaje_temporal - porcentaje_original}%"
                    )
                else:
                    st.metric("Porcentaje de Avance", f"{porcentaje_temporal}%")
            
            with col2:
                # Estado basado en porcentaje temporal
                if porcentaje_temporal == 100:
                    estado_avance = "Completado"
                    color_avance = "green"
                elif porcentaje_temporal >= 75:
                    estado_avance = "Avanzado"
                    color_avance = "blue"
                elif porcentaje_temporal >= 50:
                    estado_avance = "En progreso"
                    color_avance = "orange"
                elif porcentaje_temporal >= 25:
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
                if porcentaje_temporal == 0:
                    proxima_accion = "Iniciar acuerdo de compromiso"
                elif porcentaje_temporal == 20:
                    proxima_accion = "Completar análisis y cronograma"
                elif porcentaje_temporal == 40:
                    proxima_accion = "Completar estándares"
                elif porcentaje_temporal == 70:
                    proxima_accion = "Realizar publicación"
                elif porcentaje_temporal == 95:
                    proxima_accion = "Emitir oficio de cierre"
                else:
                    proxima_accion = "Continuar con el proceso"
                
                st.info(f"**Próxima acción:** {proxima_accion}")

            # ===== BOTONES DE ACCIÓN MODIFICADOS =====
            # ===== BOTONES DE ACCIÓN CORREGIDOS =====
            st.markdown("---")
            st.markdown("### Acciones")
            
            col1, col2, col3, col4, col5 = st.columns(5)
            
            with col1:
                # ✅ CORREGIDO: Botón para guardar cambios con validaciones
                if cambios_pendientes:
                    if st.button("💾 Guardar Registro", key=f"guardar_{key_temp}", type="primary"):
                        with st.spinner("Aplicando cambios, validaciones y guardando en Google Sheets..."):
                            try:
                                # 1. Aplicar cambios temporales al DataFrame
                                registros_df = aplicar_cambios_temporales(registros_df, indice_seleccionado, key_temp)
                                
                                # 2. ✅ NUEVO: Verificar validaciones ANTES de guardar
                                from validaciones_utils import verificar_condiciones_oficio_cierre
                                
                                # Obtener el registro actualizado
                                registro_actualizado = registros_df.iloc[indice_seleccionado]
                                
                                # Verificar si intenta introducir fecha de oficio de cierre sin publicación
                                fecha_oficio_temp = obtener_valor_temporal(key_temp, 'Fecha de oficio de cierre', '')
                                publicacion_temp = obtener_valor_temporal(key_temp, 'Publicación', '')
                                
                                if (fecha_oficio_temp and pd.notna(fecha_oficio_temp) and str(fecha_oficio_temp).strip() != ''):
                                    if not (publicacion_temp and pd.notna(publicacion_temp) and str(publicacion_temp).strip() != ''):
                                        # ❌ VALIDACIÓN FALLIDA
                                        st.session_state.mensaje_guardado = ("error", 
                                            "❌ No se puede guardar: Para introducir 'Fecha de oficio de cierre' debe completar primero la etapa de 'Publicación'")
                                        st.rerun()
                                        return registros_df

                                # 3. Aplicar validaciones de reglas de negocio
                                registros_df = validar_reglas_negocio(registros_df)

                                # 4. Actualizar los plazos automáticamente
                                registros_df = actualizar_plazo_analisis(registros_df)
                                registros_df = actualizar_plazo_cronograma(registros_df)
                                registros_df = actualizar_plazo_oficio_cierre(registros_df)

                                # 5. Guardar en Google Sheets
                                exito, mensaje = guardar_datos_editados(registros_df, crear_backup=True)

                                if exito:
                                    st.session_state.mensaje_guardado = ("success", 
                                        f"✅ {mensaje} Validaciones y plazos automáticos aplicados correctamente.")
                                    # Limpiar estado temporal después de guardar exitosamente
                                    limpiar_estado_temporal(key_temp)
                                    st.rerun()
                                else:
                                    st.session_state.mensaje_guardado = ("error", mensaje)
                                    st.rerun()
                                    
                            except Exception as e:
                                st.session_state.mensaje_guardado = ("error", f"❌ Error al guardar: {str(e)}")
                                st.rerun()
                else:
                    st.button("💾 Guardar Registro", disabled=True, help="No hay cambios pendientes para guardar")

            with col2:
                # Botón para cancelar cambios
                if cambios_pendientes:
                    if st.button("❌ Cancelar Cambios", key=f"cancelar_{key_temp}"):
                        # Limpiar estado temporal
                        limpiar_estado_temporal(key_temp)
                        st.success("Cambios cancelados")
                        st.rerun()
                else:
                    st.button("❌ Cancelar Cambios", disabled=True, help="No hay cambios pendientes para cancelar")

            # ✅ RESTO DE BOTONES SIN CAMBIOS PERO CON VALIDACIONES MEJORADAS
            
            # MOSTRAR COMPARACIÓN DE CAMBIOS si hay modificaciones
            if cambios_pendientes:
                st.markdown("---")
                st.markdown("### 📋 Resumen de Cambios Pendientes")
                
                cambios_detectados = []
                for campo, valor_temp in st.session_state[key_temp].items():
                    valor_original = row_original.get(campo, '')
                    if str(valor_temp) != str(valor_original):
                        cambios_detectados.append({
                            'Campo': campo,
                            'Valor Original': valor_original,
                            'Nuevo Valor': valor_temp
                        })
                
                if cambios_detectados:
                    df_cambios = pd.DataFrame(cambios_detectados)
                    st.dataframe(df_cambios, use_container_width=True)
                    
                    st.info(f"📊 **{len(cambios_detectados)} campo(s) modificado(s)** - Presione 'Guardar Registro' para aplicar todos los cambios")
                else:
                    st.info("✅ No se detectaron cambios en los valores")

    except Exception as e:
        st.error(f"Error al editar el registro: {e}")
        
        # Mostrar información de debug
        with st.expander("Información de Debug"):
            st.write(f"Índice seleccionado: {indice_seleccionado}")
            st.write(f"Registro seleccionado: {seleccion_registro}")
            st.write(f"Columnas disponibles: {list(registros_df.columns)}")

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
            }).map(aplicar_color, subset=['Porcentaje'])
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
        
        
        
        def crear_treemap_funcionarios(df_filtrado):
            """Crea un treemap interactivo mostrando la distribución de registros por funcionario."""
            
            # Verificar si hay datos de funcionarios
            if 'Funcionario' not in df_filtrado.columns:
                st.warning("⚠️ No se encontró la columna 'Funcionario' en los datos")
                return
            
            # Filtrar registros con funcionario asignado
            registros_con_funcionario = df_filtrado[
                (df_filtrado['Funcionario'].notna()) & 
                (df_filtrado['Funcionario'].astype(str).str.strip() != '') &
                (df_filtrado['Funcionario'].astype(str).str.strip() != 'nan') &
                (df_filtrado['Funcionario'].astype(str).str.strip() != 'None')
            ]
            
            if registros_con_funcionario.empty:
                st.info("📋 No hay registros con funcionario asignado en los datos filtrados")
                return
            
            # Contar registros por funcionario
            funcionarios_count = registros_con_funcionario['Funcionario'].value_counts().reset_index()
            funcionarios_count.columns = ['Funcionario', 'Cantidad']
            
            # Calcular estadísticas adicionales
            total_registros = len(registros_con_funcionario)
            funcionarios_count['Porcentaje'] = (funcionarios_count['Cantidad'] / total_registros * 100).round(2)
            
            # Calcular avance promedio por funcionario
            avance_por_funcionario = []
            for funcionario in funcionarios_count['Funcionario']:
                registros_funcionario = registros_con_funcionario[registros_con_funcionario['Funcionario'] == funcionario]
                if 'Porcentaje Avance' in registros_funcionario.columns:
                    avance_promedio = registros_funcionario['Porcentaje Avance'].mean()
                else:
                    avance_promedio = 0
                avance_por_funcionario.append(avance_promedio)
            
            funcionarios_count['Avance Promedio'] = avance_por_funcionario
            
            # Crear texto personalizado para el hover
            hover_text = []
            for idx, row in funcionarios_count.iterrows():
                texto = f"""
                <b>{row['Funcionario']}</b><br>
                Registros: {row['Cantidad']}<br>
                Porcentaje: {row['Porcentaje']:.1f}%<br>
                Avance Promedio: {row['Avance Promedio']:.1f}%
                """
                hover_text.append(texto)
            
            # Crear colores basados en el avance promedio
            def obtener_color_por_avance(avance):
                if avance >= 90:
                    return '#2E7D32'  # Verde oscuro - Excelente
                elif avance >= 75:
                    return '#388E3C'  # Verde - Muy bueno
                elif avance >= 60:
                    return '#689F38'  # Verde claro - Bueno
                elif avance >= 40:
                    return '#FBC02D'  # Amarillo - Regular
                elif avance >= 25:
                    return '#FF8F00'  # Naranja - Bajo
                else:
                    return '#D32F2F'  # Rojo - Crítico
            
            # Asignar colores basados en el avance
            colores_avance = [obtener_color_por_avance(avance) for avance in funcionarios_count['Avance Promedio']]
            
            # Crear el treemap
            fig_treemap = go.Figure(go.Treemap(
                labels=funcionarios_count['Funcionario'],
                values=funcionarios_count['Cantidad'],
                parents=[""] * len(funcionarios_count),
                
                # Personalización del texto
                text=[f"{func}<br>{cant} registros<br>{porc:.1f}%" 
                      for func, cant, porc in zip(funcionarios_count['Funcionario'], 
                                                funcionarios_count['Cantidad'], 
                                                funcionarios_count['Porcentaje'])],
                textinfo="text",
                textfont=dict(size=12, color='white'),
                
                # Hover personalizado
                hovertemplate='<b>%{label}</b><br>' +
                             'Registros: %{value}<br>' +
                             'Porcentaje: %{customdata[0]:.1f}%<br>' +
                             'Avance Promedio: %{customdata[1]:.1f}%<br>' +
                             '<extra></extra>',
                customdata=list(zip(funcionarios_count['Porcentaje'], funcionarios_count['Avance Promedio'])),
                
                # Colores
                marker=dict(
                    colors=colores_avance,
                    line=dict(color='white', width=2)
                ),
                
                # Configuración del treemap
                pathbar=dict(visible=False),
                textposition="middle center",
                
                # Configuración de la fuente
                texttemplate="%{label}<br>%{value} registros<br>%{customdata[0]:.1f}%",
            ))
            
            # Personalizar el layout
            fig_treemap.update_layout(
                title={
                    'text': "🗺️ Distribución de Registros por Funcionario",
                    'x': 0.5,
                    'xanchor': 'center',
                    'font': {'size': 18, 'color': '#2c3e50'}
                },
                font=dict(family="Arial", size=12),
                margin=dict(t=60, l=20, r=20, b=20),
                height=500,
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)'
            )
            
            return fig_treemap, funcionarios_count
        
        # SECCIÓN PRINCIPAL: Agregar después de la sección de descarga
        st.markdown("---")
        st.markdown("### 🗺️ Distribución de Registros por Funcionario")
        
        # Crear el treemap
        treemap_result = crear_treemap_funcionarios(df_filtrado)
        
        if treemap_result:
            fig_treemap, funcionarios_data = treemap_result
            
            # Mostrar el treemap
            st.plotly_chart(fig_treemap, use_container_width=True)
            
            # Crear métricas resumidas
            st.markdown("#### 📊 Métricas de Distribución")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                total_funcionarios = len(funcionarios_data)
                st.metric("Total Funcionarios", total_funcionarios)
            
            with col2:
                max_registros = funcionarios_data['Cantidad'].max()
                funcionario_top = funcionarios_data.loc[funcionarios_data['Cantidad'].idxmax(), 'Funcionario']
                st.metric("Máximo Registros", f"{max_registros}", help=f"Funcionario: {funcionario_top}")
            
            with col3:
                promedio_registros = funcionarios_data['Cantidad'].mean()
                st.metric("Promedio por Funcionario", f"{promedio_registros:.1f}")
            
            with col4:
                avance_general = funcionarios_data['Avance Promedio'].mean()
                st.metric("Avance Promedio General", f"{avance_general:.1f}%")
            
            # Leyenda de colores
            st.markdown("#### 🎨 Leyenda de Colores (Basada en Avance Promedio)")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("""
                <div style="display: flex; flex-direction: column; gap: 8px;">
                    <div style="display: flex; align-items: center; gap: 10px;">
                        <div style="width: 20px; height: 20px; background-color: #2E7D32; border-radius: 4px;"></div>
                        <span>90-100%: Excelente</span>
                    </div>
                    <div style="display: flex; align-items: center; gap: 10px;">
                        <div style="width: 20px; height: 20px; background-color: #388E3C; border-radius: 4px;"></div>
                        <span>75-89%: Muy Bueno</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown("""
                <div style="display: flex; flex-direction: column; gap: 8px;">
                    <div style="display: flex; align-items: center; gap: 10px;">
                        <div style="width: 20px; height: 20px; background-color: #689F38; border-radius: 4px;"></div>
                        <span>60-74%: Bueno</span>
                    </div>
                    <div style="display: flex; align-items: center; gap: 10px;">
                        <div style="width: 20px; height: 20px; background-color: #FBC02D; border-radius: 4px;"></div>
                        <span>40-59%: Regular</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                st.markdown("""
                <div style="display: flex; flex-direction: column; gap: 8px;">
                    <div style="display: flex; align-items: center; gap: 10px;">
                        <div style="width: 20px; height: 20px; background-color: #FF8F00; border-radius: 4px;"></div>
                        <span>25-39%: Bajo</span>
                    </div>
                    <div style="display: flex; align-items: center; gap: 10px;">
                        <div style="width: 20px; height: 20px; background-color: #D32F2F; border-radius: 4px;"></div>
                        <span>0-24%: Crítico</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            # Tabla detallada expandible
            with st.expander("📋 Ver Tabla Detallada"):
                # Ordenar por cantidad descendente
                tabla_ordenada = funcionarios_data.sort_values('Cantidad', ascending=False)
                
                # Formatear la tabla
                tabla_formateada = tabla_ordenada.copy()
                tabla_formateada['Porcentaje'] = tabla_formateada['Porcentaje'].apply(lambda x: f"{x:.1f}%")
                tabla_formateada['Avance Promedio'] = tabla_formateada['Avance Promedio'].apply(lambda x: f"{x:.1f}%")
                
                # Mostrar tabla con estilo
                st.dataframe(
                    tabla_formateada.style.format({
                        'Cantidad': '{:,}',
                    }).background_gradient(subset=['Cantidad'], cmap='Blues'),
                    use_container_width=True
                )
                
                # Botón para descargar tabla de funcionarios
                output_funcionarios = io.BytesIO()
                with pd.ExcelWriter(output_funcionarios, engine='openpyxl') as writer:
                    funcionarios_data.to_excel(writer, sheet_name='Distribución Funcionarios', index=False)
        
                excel_funcionarios = output_funcionarios.getvalue()
                st.download_button(
                    label="📥 Descargar distribución por funcionarios (Excel)",
                    data=excel_funcionarios,
                    file_name=f"distribucion_funcionarios_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    help="Descarga la tabla de distribución de registros por funcionario"
                )
            
            # Insights automáticos
            st.markdown("#### 💡 Insights Automáticos")
            
            # Calcular insights
            funcionario_mas_registros = funcionarios_data.loc[funcionarios_data['Cantidad'].idxmax()]
            funcionario_mejor_avance = funcionarios_data.loc[funcionarios_data['Avance Promedio'].idxmax()]
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.info(f"""
                **👑 Funcionario con más registros:**
                
                {funcionario_mas_registros['Funcionario']}
                - {funcionario_mas_registros['Cantidad']} registros ({funcionario_mas_registros['Porcentaje']:.1f}%)
                - Avance promedio: {funcionario_mas_registros['Avance Promedio']:.1f}%
                """)
            
            with col2:
                st.success(f"""
                **⭐ Funcionario con mejor avance:**
                
                {funcionario_mejor_avance['Funcionario']}
                - {funcionario_mejor_avance['Cantidad']} registros
                - Avance promedio: {funcionario_mejor_avance['Avance Promedio']:.1f}%
                """)
            
            # Recomendaciones
            if funcionarios_data['Avance Promedio'].min() < 50:
                funcionarios_bajo_avance = funcionarios_data[funcionarios_data['Avance Promedio'] < 50]
                st.warning(f"""
                **⚠️ Atención requerida:** {len(funcionarios_bajo_avance)} funcionario(s) tienen avance promedio inferior al 50%:
                
                {', '.join(funcionarios_bajo_avance['Funcionario'].tolist())}
                """)
            
            # Mostrar distribución equilibrada
            desviacion_estandar = funcionarios_data['Cantidad'].std()
            coeficiente_variacion = desviacion_estandar / funcionarios_data['Cantidad'].mean()
            
            if coeficiente_variacion < 0.3:
                st.success("✅ **Distribución equilibrada:** La carga de trabajo está bien distribuida entre funcionarios")
            elif coeficiente_variacion < 0.6:
                st.warning("⚠️ **Distribución moderada:** Considere redistribuir algunos registros para equilibrar la carga")
            else:
                st.error("🚨 **Distribución desbalanceada:** Se recomienda redistribuir registros para mejorar el equilibrio")


                         
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

        

        # Filtros para la tabla de alertas
        st.markdown("### Filtrar Alertas")

        col1, col2, col3, col4, col5, col6 = st.columns(6)

        with col1:
            entidad_filtro_alertas = st.multiselect(
                "Entidad",
                options=df_alertas['Entidad'].unique().tolist(),
                default=df_alertas['Entidad'].unique().tolist()
            )

        with col2:
            tipo_alerta_filtro = st.multiselect(
                "Tipo de Alerta",
                options=df_alertas['Tipo Alerta'].unique().tolist(),
                default=df_alertas['Tipo Alerta'].unique().tolist()
            )

        with col3:
            estado_filtro = st.multiselect(
                "Estado",
                options=df_alertas['Estado'].unique().tolist(),
                default=df_alertas['Estado'].unique().tolist()
            )

        with col4:
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

        with col5:
            tipos_dato_alertas = ['Todos'] + sorted(registros_df['TipoDato'].dropna().unique().tolist())
            tipo_dato_filtro_alertas = st.multiselect(
                "Tipo de Dato",
                options=tipos_dato_alertas,
                default=["Todos"]
            )

        with col6:
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

        # Filtro por entidad
        if entidad_filtro_alertas:
            df_alertas_filtrado = df_alertas_filtrado[df_alertas_filtrado['Entidad'].isin(entidad_filtro_alertas)]

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

        # Mostrar estadísticas de alertas FILTRADAS
        st.markdown("### Resumen de Alertas")

        col1, col2, col3 = st.columns(3)

        with col1:
            num_vencidos = len(df_alertas_filtrado[df_alertas_filtrado['Estado'] == 'Vencido'])
            st.markdown(f"""
            <div class="metric-card" style="background-color: #fee2e2;">
                <p style="font-size: 1rem; color: #b91c1c;">Vencidos</p>
                <p style="font-size: 2.5rem; font-weight: bold; color: #b91c1c;">{num_vencidos}</p>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            num_proximos = len(df_alertas_filtrado[df_alertas_filtrado['Estado'] == 'Próximo a vencer'])
            st.markdown(f"""
            <div class="metric-card" style="background-color: #fef3c7;">
                <p style="font-size: 1rem; color: #b45309;">Próximos a vencer</p>
                <p style="font-size: 2.5rem; font-weight: bold; color: #b45309;">{num_proximos}</p>
            </div>
            """, unsafe_allow_html=True)

        with col3:
            num_retrasados = len(df_alertas_filtrado[df_alertas_filtrado['Estado'] == 'Completado con retraso'])
            st.markdown(f"""
            <div class="metric-card" style="background-color: #dbeafe;">
                <p style="font-size: 1rem; color: #1e40af;">Completados con retraso</p>
                <p style="font-size: 2.5rem; font-weight: bold; color: #1e40af;">{num_retrasados}</p>
            </div>
            """, unsafe_allow_html=True)
        
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
                .style.map(lambda _: '',
                                subset=['Cod', 'Entidad', 'Nivel Información', 'Funcionario', 'Tipo Alerta',
                                        'Fecha Programada', 'Fecha Real', 'Descripción'])
                .map(highlight_estado, subset=['Estado'])
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

def mostrar_seguimiento_trimestral(registros_df, meta_df):
    """Muestra el seguimiento trimestral de publicaciones: avance real vs meta programada."""
    st.markdown('<div class="subtitle">Seguimiento Trimestral - Publicaciones: Meta vs Avance Real</div>', unsafe_allow_html=True)
    
    # Verificar disponibilidad de la columna Mes Proyectado
    if 'Mes Proyectado' not in registros_df.columns:
        st.error("❌ La columna 'Mes Proyectado' no está disponible en los datos")
        st.info("📋 Verifique que la hoja de Google Sheets tenga la columna 'Mes Proyectado'")
        return
    
    # Filtrado de registros con Mes Proyectado válido
    registros_con_mes = registros_df[
        (registros_df['Mes Proyectado'].notna()) & 
        (registros_df['Mes Proyectado'].astype(str).str.strip() != '') &
        (~registros_df['Mes Proyectado'].astype(str).str.strip().isin(['nan', 'None', 'NaN']))
    ]
    
    if registros_con_mes.empty:
        st.warning("⚠️ No hay registros con 'Mes Proyectado' válido")
        st.info("📝 Para usar el seguimiento trimestral, asigne un mes proyectado a los registros en la sección de Edición")
        return
    
    # Información explicativa
    st.info("""
    **📊 Seguimiento de Publicaciones por Trimestre**
    
    Este dashboard muestra el avance de **publicaciones reales** versus las **metas programadas** para cada trimestre:
    - **Meta:** Número de registros que deberían estar publicados al final del trimestre (acumulado)
    - **Avance:** Número de registros con fecha real de publicación completada (acumulado)
    - **Porcentaje:** (Publicaciones reales / Meta programada) × 100
    """)

    def crear_grafico_individual(datos, titulo, color_meta, color_avance):
        """Crea gráfico individual para un tipo de registro"""
        
        trimestres = ['Q1 2025', 'Q2 2025', 'Q3 2025', 'Q4 2025']
        
        # Extraer datos
        metas = [datos[q]['meta'] for q in ['Q1', 'Q2', 'Q3', 'Q4']]
        avance = [datos[q]['avance'] for q in ['Q1', 'Q2', 'Q3', 'Q4']]
        
        # Crear figura
        fig = go.Figure()
        
        # Línea de Meta
        fig.add_trace(go.Scatter(
            x=trimestres,
            y=metas,
            mode='lines+markers',
            name='🎯 Meta',
            line=dict(color=color_meta, width=4, dash='dash'),
            marker=dict(size=12, symbol='diamond'),
            hovertemplate='<b>Meta</b><br>%{x}: %{y} publicaciones<extra></extra>'
        ))
        
        # Línea de Avance
        fig.add_trace(go.Scatter(
            x=trimestres,
            y=avance,
            mode='lines+markers',
            name='✅ Avance Real',
            line=dict(color=color_avance, width=4),
            marker=dict(size=12),
            hovertemplate='<b>Avance Real</b><br>%{x}: %{y} publicaciones<extra></extra>'
        ))
        
        # Configurar layout
        fig.update_layout(
            title={
                'text': f'📈 {titulo}',
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 18, 'color': '#2c3e50', 'family': 'Arial Black'}
            },
            xaxis={
                'title': 'Trimestre',
                'gridcolor': '#ecf0f1',
                'linecolor': '#bdc3c7',
                'tickfont': {'size': 12, 'color': '#2c3e50'}
            },
            yaxis={
                'title': 'Publicaciones Acumuladas',
                'gridcolor': '#ecf0f1',
                'linecolor': '#bdc3c7',
                'tickfont': {'size': 12, 'color': '#2c3e50'}
            },
            plot_bgcolor='white',
            paper_bgcolor='white',
            font={'family': 'Arial', 'color': '#2c3e50'},
            legend={
                'x': 0.02,
                'y': 0.98,
                'bgcolor': 'rgba(255,255,255,0.9)',
                'bordercolor': '#bdc3c7',
                'borderwidth': 1,
                'font': {'size': 12}
            },
            height=400,
            hovermode='x unified',
            margin=dict(l=60, r=60, t=80, b=60)
        )
        
        # Agregar línea de referencia (75% de la meta máxima)
        max_meta = max(metas) if metas else 0
        if max_meta > 0:
            referencia_75 = max_meta * 0.75
            
            fig.add_hline(
                y=referencia_75,
                line_dash="dot",
                line_color="gray",
                annotation_text="75% Objetivo",
                annotation_position="bottom right",
                annotation_font_size=10
            )
        
        return fig

    def crear_tarjetas_resumen(datos, titulo_tipo):
        """Crea tarjetas de resumen para un tipo de registro"""
        
        # Datos del Q4 (acumulado anual)
        meta_total = datos['Q4']['meta']
        avance_total = datos['Q4']['avance']
        porcentaje_total = datos['Q4']['porcentaje']
        pendientes_total = datos['Q4']['pendientes']
        
        st.markdown(f"#### Resumen {titulo_tipo}")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 1rem; border-radius: 10px; color: white; text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                <h3 style="margin: 0; font-size: 2rem; font-weight: bold;">{meta_total}</h3>
                <p style="margin: 0; font-size: 0.9rem; opacity: 0.9;">Meta Total 2025</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); padding: 1rem; border-radius: 10px; color: white; text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                <h3 style="margin: 0; font-size: 2rem; font-weight: bold;">{avance_total}</h3>
                <p style="margin: 0; font-size: 0.9rem; opacity: 0.9;">Publicaciones Reales</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            # Color dinámico según porcentaje
            if porcentaje_total >= 75:
                color_grad = "linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)"
            elif porcentaje_total >= 50:
                color_grad = "linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)"
            elif porcentaje_total >= 25:
                color_grad = "linear-gradient(135deg, #fa709a 0%, #fee140 100%)"
            else:
                color_grad = "linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%)"
                
            st.markdown(f"""
            <div style="background: {color_grad}; padding: 1rem; border-radius: 10px; color: white; text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                <h3 style="margin: 0; font-size: 2rem; font-weight: bold;">{porcentaje_total:.1f}%</h3>
                <p style="margin: 0; font-size: 0.9rem; opacity: 0.9;">Cumplimiento</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%); padding: 1rem; border-radius: 10px; color: #2c3e50; text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                <h3 style="margin: 0; font-size: 2rem; font-weight: bold;">{pendientes_total}</h3>
                <p style="margin: 0; font-size: 0.9rem; opacity: 0.8;">Pendientes</p>
            </div>
            """, unsafe_allow_html=True)

    def crear_datos_trimestre_vacio():
        """Crea estructura vacía para trimestres sin datos"""
        return {
            'Q1': {'meta': 0, 'avance': 0, 'porcentaje': 0, 'pendientes': 0},
            'Q2': {'meta': 0, 'avance': 0, 'porcentaje': 0, 'pendientes': 0},
            'Q3': {'meta': 0, 'avance': 0, 'porcentaje': 0, 'pendientes': 0},
            'Q4': {'meta': 0, 'avance': 0, 'porcentaje': 0, 'pendientes': 0}
        }
    
    
    def calcular_publicaciones_trimestrales_simple(df, tipo_dato):
        """Versión corregida - usa metas de meta_df columnas E y J"""
    
        if 'TipoDato' not in df.columns:
            return crear_datos_trimestre_vacio()
        
        # Filtrar por tipo de dato
        try:
            if tipo_dato.upper() == 'NUEVO':
                df_filtrado = df[df['TipoDato'].astype(str).str.upper().str.contains('NUEVO', na=False)]
                columna_meta = 4  # Columna E (índice 4) para NUEVOS
            else:  # ACTUALIZAR
                df_filtrado = df[df['TipoDato'].astype(str).str.upper().str.contains('ACTUALIZAR', na=False)]
                columna_meta = 9  # Columna J (índice 9) para ACTUALIZAR
        except Exception:
            return crear_datos_trimestre_vacio()
        
        if df_filtrado.empty:
            return crear_datos_trimestre_vacio()
        
        # Definir trimestres
        trimestres = {
            'Q1': ['Enero', 'Febrero', 'Marzo'],
            'Q2': ['Abril', 'Mayo', 'Junio'], 
            'Q3': ['Julio', 'Agosto', 'Septiembre'],
            'Q4': ['Octubre', 'Noviembre', 'Diciembre']
        }
        
        # Obtener metas desde meta_df
        metas_por_trimestre = {}
        try:
            for idx, row in meta_df.iterrows():
                try:
                    fecha_str = str(row[0]).strip()
                    valor_meta = int(row[columna_meta]) if pd.notna(row[columna_meta]) and str(row[columna_meta]).strip() != '' else 0
                    
                    # Mapear fechas específicas a trimestres
                    if fecha_str == '31/03/2025':
                        metas_por_trimestre['Q1'] = valor_meta
                    elif fecha_str == '30/06/2025':
                        metas_por_trimestre['Q2'] = valor_meta
                    elif fecha_str == '30/09/2025':
                        metas_por_trimestre['Q3'] = valor_meta
                    elif fecha_str == '31/12/2025':
                        metas_por_trimestre['Q4'] = valor_meta
                except Exception:
                    continue
        except Exception:
            # Fallback: si no se pueden leer las metas, usar 0
            metas_por_trimestre = {'Q1': 0, 'Q2': 0, 'Q3': 0, 'Q4': 0}
        
        datos_trimestres = {}
        
        for trimestre, meses in trimestres.items():
            try:
                # META: Directamente desde meta_df (ya son acumuladas)
                meta_acumulada = metas_por_trimestre.get(trimestre, 0)
                
                # AVANCE: Contar publicaciones reales acumuladas hasta este trimestre
                # AVANCE: Contar publicaciones reales acumuladas hasta este trimestre
                avance_acumulado = 0
                if 'Publicación' in df_filtrado.columns and len(df_filtrado) > 0:
                    try:
                        # Calcular meses acumulados hasta este trimestre
                        meses_acumulados = []
                        for q, m in trimestres.items():
                            meses_acumulados.extend(m)
                            if q == trimestre:
                                break
                        
                        # CORREGIDO: Contar registros con fecha de publicación válida usando es_fecha_valida
                        registros_publicados = df_filtrado[
                            df_filtrado['Publicación'].apply(lambda x: es_fecha_valida(x))
                        ]
                        
                        # Si hay Mes Proyectado, filtrar por meses acumulados
                        if 'Mes Proyectado' in registros_publicados.columns:
                            # Contar los que tienen Mes Proyectado válido y están en meses acumulados
                            publicaciones_acumuladas = registros_publicados[
                                (registros_publicados['Mes Proyectado'].notna()) & 
                                (registros_publicados['Mes Proyectado'].astype(str).str.strip() != '') &
                                (~registros_publicados['Mes Proyectado'].astype(str).str.strip().isin(['nan', 'None', 'NaN'])) &
                                (registros_publicados['Mes Proyectado'].isin(meses_acumulados))
                            ]
                            
                            # CORREGIDO: Contar los que NO tienen Mes Proyectado válido pero SÍ tienen fecha de Publicación
                            publicaciones_sin_mes = registros_publicados[
                                (registros_publicados['Mes Proyectado'].isna()) | 
                                (registros_publicados['Mes Proyectado'].astype(str).str.strip() == '') |
                                (registros_publicados['Mes Proyectado'].astype(str).str.strip().isin(['nan', 'None', 'NaN']))
                            ]
                            
                            # NUEVA LÓGICA: Para que Q4 coincida con dashboard, sumar todos en Q4
                            # Determinar el trimestre actual basado en la fecha de hoy
                            from datetime import datetime
                            fecha_actual = datetime.now()
                            mes_actual = fecha_actual.month
                            
                            if mes_actual <= 3:
                                trimestre_actual = 'Q1'
                            elif mes_actual <= 6:
                                trimestre_actual = 'Q2'
                            elif mes_actual <= 9:
                                trimestre_actual = 'Q3'
                            else:
                                trimestre_actual = 'Q4'
                            
                            # Para el trimestre actual Y TODOS LOS SIGUIENTES, mostrar TODOS los publicados
                            trimestres_orden = ['Q1', 'Q2', 'Q3', 'Q4']
                            indice_actual = trimestres_orden.index(trimestre_actual)
                            indice_este_trimestre = trimestres_orden.index(trimestre)
                            
                            if indice_este_trimestre >= indice_actual:
                                avance_acumulado = len(registros_publicados)  # TODOS los publicados
                            else:
                                # Para trimestres pasados, usar la lógica original
                                # Para trimestres pasados, mantener lógica acumulativa
                                avance_acumulado = len(publicaciones_acumuladas) + len(publicaciones_sin_mes)
                                
                        else:
                            # Sin Mes Proyectado, usar proporción acumulada
                            trimestre_index = list(trimestres.keys()).index(trimestre) + 1
                            avance_acumulado = (len(registros_publicados) * trimestre_index) // 4
                            
                    except Exception:
                        avance_acumulado = 0
                # Calcular porcentaje
                porcentaje = (avance_acumulado / meta_acumulada * 100) if meta_acumulada > 0 else 0
                
                # Pendientes
                pendientes = max(0, meta_acumulada - avance_acumulado)
                
                datos_trimestres[trimestre] = {
                    'meta': meta_acumulada,
                    'avance': avance_acumulado,
                    'porcentaje': round(porcentaje, 1),
                    'pendientes': pendientes
                }
                
            except Exception as e:
                st.warning(f"Error calculando {trimestre}: {e}")
                datos_trimestres[trimestre] = {
                    'meta': 0, 'avance': 0, 'porcentaje': 0, 'pendientes': 0
                }
        
        return datos_trimestres
    # CALCULAR DATOS TRIMESTRALES
    try:
        datos_nuevos = calcular_publicaciones_trimestrales_simple(registros_con_mes, 'NUEVO')
        datos_actualizar = calcular_publicaciones_trimestrales_simple(registros_con_mes, 'ACTUALIZAR')
    except Exception as e:
        st.error(f"Error calculando datos trimestrales: {e}")
        datos_nuevos = crear_datos_trimestre_vacio()
        datos_actualizar = crear_datos_trimestre_vacio()

    # Verificar si hay datos para mostrar
    hay_datos_nuevos = any(datos_nuevos[q]['meta'] > 0 for q in ['Q1', 'Q2', 'Q3', 'Q4'])
    hay_datos_actualizar = any(datos_actualizar[q]['meta'] > 0 for q in ['Q1', 'Q2', 'Q3', 'Q4'])

    if not hay_datos_nuevos and not hay_datos_actualizar:
        st.warning("⚠️ **No hay datos suficientes para mostrar el seguimiento trimestral**")
        st.info("""
        **Para habilitar esta funcionalidad:**
        1. Asegúrese de tener registros con 'TipoDato' definido ('Nuevo' o 'Actualizar')
        2. Asigne 'Mes Proyectado' a los registros
        3. Complete fechas de 'Publicación' para ver el avance real
        """)
        return

    # LAYOUT PRINCIPAL: GRÁFICOS LADO A LADO
    st.markdown("### Evolución Acumulativa por Tipo de Registro")
    
    col_actualizar, col_nuevos = st.columns(2)
    
    # GRÁFICO IZQUIERDA: REGISTROS A ACTUALIZAR
    with col_actualizar:
        if hay_datos_actualizar:
            fig_actualizar = crear_grafico_individual(
                datos_actualizar, 
                "Registros a Actualizar",
                '#8e44ad',  # Púrpura para meta
                '#3498db'   # Azul para avance
            )
            st.plotly_chart(fig_actualizar, use_container_width=True)
        else:
            st.info("⚠️ No hay datos de registros a actualizar")
    
    # GRÁFICO DERECHA: REGISTROS NUEVOS
    with col_nuevos:
        if hay_datos_nuevos:
            fig_nuevos = crear_grafico_individual(
                datos_nuevos, 
                "Registros Nuevos",
                '#e74c3c',  # Rojo para meta
                '#27ae60'   # Verde para avance
            )
            st.plotly_chart(fig_nuevos, use_container_width=True)
        else:
            st.info("⚠️ No hay datos de registros nuevos")

    st.markdown("---")

    # TARJETAS DE RESUMEN
    if hay_datos_actualizar:
        crear_tarjetas_resumen(datos_actualizar, "Registros a Actualizar")
        st.markdown("---")
    
    if hay_datos_nuevos:
        crear_tarjetas_resumen(datos_nuevos, "Registros Nuevos")

    # INFORMACIÓN ADICIONAL
    st.markdown("### 💡 Información Adicional")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if hay_datos_actualizar:
            st.markdown("#### 🔄 Próximos Hitos - Actualizar")
            q1_pendientes = datos_actualizar['Q1']['pendientes']
            q2_pendientes = datos_actualizar['Q2']['pendientes']
            
            if q1_pendientes > 0:
                st.warning(f"📅 Q1: {q1_pendientes} publicaciones pendientes")
            elif q2_pendientes > 0:
                st.info(f"📅 Q2: {q2_pendientes} publicaciones pendientes")
            else:
                st.success("✅ Metas Q1 y Q2 completadas")
    
    with col2:
        if hay_datos_nuevos:
            st.markdown("#### 🆕 Próximos Hitos - Nuevos")
            q1_pendientes = datos_nuevos['Q1']['pendientes']
            q2_pendientes = datos_nuevos['Q2']['pendientes']
            
            if q1_pendientes > 0:
                st.warning(f"📅 Q1: {q1_pendientes} publicaciones pendientes")
            elif q2_pendientes > 0:
                st.info(f"📅 Q2: {q2_pendientes} publicaciones pendientes")
            else:
                st.success("✅ Metas Q1 y Q2 completadas")

def mostrar_reportes(registros_df, entidad_filtro, tipo_dato_filtro, acuerdo_filtro, analisis_filtro, 
                    estandares_filtro, publicacion_filtro, finalizado_filtro, mes_filtro):
    """Muestra la pestaña de reportes con tabla completa y filtros específicos - VERSIÓN COMPLETA CON MES."""
    st.markdown('<div class="subtitle">Reportes de Registros</div>', unsafe_allow_html=True)
    
    # Aplicar filtros
    df_filtrado = registros_df.copy()
    
    # Filtro por entidad
    if entidad_filtro != 'Todas':
        df_filtrado = df_filtrado[df_filtrado['Entidad'] == entidad_filtro]
                       
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
    try:
        st.dataframe(
            df_mostrar
            .style.format({'Porcentaje Avance': '{:.2f}%'})
            .apply(highlight_estado_fechas, axis=1)
            .background_gradient(cmap='RdYlGn', subset=['Porcentaje Avance']),
            use_container_width=True
        )
    except Exception as e:
        # Si falla el formato, mostrar tabla simple
        st.dataframe(df_mostrar, use_container_width=True)
    
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
    if entidad_filtro != 'Todas':
        filtros_aplicados.append(f"Entidad: {entidad_filtro}")
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

# Cambio en la función main() de app1.py

def main():
    """Función principal de la aplicación"""
    try:
        # Configurar página
        setup_page()
        load_css()

        # Inicializar session state
        if 'funcionarios' not in st.session_state:
            st.session_state.funcionarios = []
        if 'mensaje_guardado' not in st.session_state:
            st.session_state.mensaje_guardado = None

        # ===== TÍTULO =====
        st.markdown('<div class="title">📊 Tablero de Control de Seguimiento de Datos Temáticos - Ideca</div>', unsafe_allow_html=True)

        
        # ===== SIDEBAR CON AUTENTICACIÓN =====
        # Sistema de autenticación
        mostrar_login()
        mostrar_estado_autenticacion()
        
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
        # GUARDAR las columnas calculadas en Google Sheets
        try:
            with st.spinner("💾 Guardando columnas calculadas..."):
                from data_utils import guardar_datos_editados_rapido
                exito, mensaje = guardar_datos_editados_rapido(registros_df)
                if not exito:
                    st.warning(f"⚠️ Columnas calculadas en memoria solamente: {mensaje}")
        except Exception as e:
            st.warning(f"⚠️ Columnas calculadas solo en memoria: {str(e)}")
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
            
            # Inicializar valores por defecto si no existen en session_state
            if 'dash_entidad' not in st.session_state:
                st.session_state.dash_entidad = 'Todas'
            if 'dash_funcionario' not in st.session_state:
                st.session_state.dash_funcionario = 'Todos'
            if 'dash_tipo' not in st.session_state:
                st.session_state.dash_tipo = 'Todos'
            if 'dash_nivel' not in st.session_state:
                st.session_state.dash_nivel = 'Todos'
            
            col1, col2, col3, col4 = st.columns(4)
            
            # Aplicar filtros actuales para obtener datos disponibles
            df_temp = registros_df.copy()
            
            # Aplicar filtros existentes (excepto el que se está modificando)
            if st.session_state.dash_entidad != 'Todas':
                df_temp = df_temp[df_temp['Entidad'] == st.session_state.dash_entidad]
            
            if st.session_state.dash_funcionario != 'Todos' and 'Funcionario' in df_temp.columns:
                df_temp = df_temp[df_temp['Funcionario'] == st.session_state.dash_funcionario]
            
            if st.session_state.dash_tipo != 'Todos':
                df_temp = df_temp[df_temp['TipoDato'].str.upper() == st.session_state.dash_tipo.upper()]
            
            if st.session_state.dash_nivel != 'Todos':
                df_temp = df_temp[df_temp['Nivel Información '] == st.session_state.dash_nivel]
            
            with col1:
                # Obtener entidades disponibles según otros filtros
                df_for_entidades = registros_df.copy()
                if st.session_state.dash_funcionario != 'Todos' and 'Funcionario' in df_for_entidades.columns:
                    df_for_entidades = df_for_entidades[df_for_entidades['Funcionario'] == st.session_state.dash_funcionario]
                if st.session_state.dash_tipo != 'Todos':
                    df_for_entidades = df_for_entidades[df_for_entidades['TipoDato'].str.upper() == st.session_state.dash_tipo.upper()]
                if st.session_state.dash_nivel != 'Todos':
                    df_for_entidades = df_for_entidades[df_for_entidades['Nivel Información '] == st.session_state.dash_nivel]
                
                entidades_disponibles = ['Todas'] + sorted([e for e in df_for_entidades['Entidad'].unique().tolist() if e])
                
                # Si la entidad actual no está disponible, resetear
                if st.session_state.dash_entidad not in entidades_disponibles:
                    st.session_state.dash_entidad = 'Todas'
                
                entidad_seleccionada = st.selectbox(
                    'Entidad', 
                    entidades_disponibles,
                    index=entidades_disponibles.index(st.session_state.dash_entidad) if st.session_state.dash_entidad in entidades_disponibles else 0,
                    key="dash_entidad_selector"
                )
                
                if entidad_seleccionada != st.session_state.dash_entidad:
                    st.session_state.dash_entidad = entidad_seleccionada
                    st.rerun()
            
            with col2:
                # Obtener funcionarios disponibles según otros filtros
                df_for_funcionarios = registros_df.copy()
                if st.session_state.dash_entidad != 'Todas':
                    df_for_funcionarios = df_for_funcionarios[df_for_funcionarios['Entidad'] == st.session_state.dash_entidad]
                if st.session_state.dash_tipo != 'Todos':
                    df_for_funcionarios = df_for_funcionarios[df_for_funcionarios['TipoDato'].str.upper() == st.session_state.dash_tipo.upper()]
                if st.session_state.dash_nivel != 'Todos':
                    df_for_funcionarios = df_for_funcionarios[df_for_funcionarios['Nivel Información '] == st.session_state.dash_nivel]
                
                funcionarios_disponibles = ['Todos']
                if 'Funcionario' in df_for_funcionarios.columns:
                    funcionarios_unicos = [f for f in df_for_funcionarios['Funcionario'].dropna().unique().tolist() if f]
                    funcionarios_disponibles += sorted(funcionarios_unicos)
                
                # Si el funcionario actual no está disponible, resetear
                if st.session_state.dash_funcionario not in funcionarios_disponibles:
                    st.session_state.dash_funcionario = 'Todos'
                
                funcionario_seleccionado = st.selectbox(
                    'Funcionario', 
                    funcionarios_disponibles,
                    index=funcionarios_disponibles.index(st.session_state.dash_funcionario) if st.session_state.dash_funcionario in funcionarios_disponibles else 0,
                    key="dash_funcionario_selector"
                )
                
                if funcionario_seleccionado != st.session_state.dash_funcionario:
                    st.session_state.dash_funcionario = funcionario_seleccionado
                    st.rerun()
            
            with col3:
                # Obtener tipos de dato disponibles según otros filtros
                df_for_tipos = registros_df.copy()
                if st.session_state.dash_entidad != 'Todas':
                    df_for_tipos = df_for_tipos[df_for_tipos['Entidad'] == st.session_state.dash_entidad]
                if st.session_state.dash_funcionario != 'Todos' and 'Funcionario' in df_for_tipos.columns:
                    df_for_tipos = df_for_tipos[df_for_tipos['Funcionario'] == st.session_state.dash_funcionario]
                if st.session_state.dash_nivel != 'Todos':
                    df_for_tipos = df_for_tipos[df_for_tipos['Nivel Información '] == st.session_state.dash_nivel]
                
                tipos_disponibles = ['Todos'] + sorted([t for t in df_for_tipos['TipoDato'].dropna().unique().tolist() if t])
                
                # Si el tipo actual no está disponible, resetear
                if st.session_state.dash_tipo not in tipos_disponibles:
                    st.session_state.dash_tipo = 'Todos'
                
                tipo_dato_seleccionado = st.selectbox(
                    'Tipo de Dato', 
                    tipos_disponibles,
                    index=tipos_disponibles.index(st.session_state.dash_tipo) if st.session_state.dash_tipo in tipos_disponibles else 0,
                    key="dash_tipo_selector"
                )
                
                if tipo_dato_seleccionado != st.session_state.dash_tipo:
                    st.session_state.dash_tipo = tipo_dato_seleccionado
                    st.rerun()
            
            with col4:
                # Nivel de información solo activo si hay entidad seleccionada
                if st.session_state.dash_entidad != 'Todas':
                    # Obtener niveles disponibles según otros filtros
                    df_for_niveles = registros_df.copy()
                    if st.session_state.dash_entidad != 'Todas':
                        df_for_niveles = df_for_niveles[df_for_niveles['Entidad'] == st.session_state.dash_entidad]
                    if st.session_state.dash_funcionario != 'Todos' and 'Funcionario' in df_for_niveles.columns:
                        df_for_niveles = df_for_niveles[df_for_niveles['Funcionario'] == st.session_state.dash_funcionario]
                    if st.session_state.dash_tipo != 'Todos':
                        df_for_niveles = df_for_niveles[df_for_niveles['TipoDato'].str.upper() == st.session_state.dash_tipo.upper()]
                    
                    niveles_disponibles = ['Todos'] + sorted([n for n in df_for_niveles['Nivel Información '].dropna().unique().tolist() if n])
                    
                    # Si el nivel actual no está disponible, resetear
                    if st.session_state.dash_nivel not in niveles_disponibles:
                        st.session_state.dash_nivel = 'Todos'
                    
                    nivel_seleccionado = st.selectbox(
                        'Nivel de Información', 
                        niveles_disponibles,
                        index=niveles_disponibles.index(st.session_state.dash_nivel) if st.session_state.dash_nivel in niveles_disponibles else 0,
                        key="dash_nivel_selector"
                    )
                    
                    if nivel_seleccionado != st.session_state.dash_nivel:
                        st.session_state.dash_nivel = nivel_seleccionado
                        st.rerun()
                else:
                    st.session_state.dash_nivel = 'Todos'
                    nivel_seleccionado = 'Todos'
                    st.selectbox('Nivel de Información', ['Todos'], disabled=True, key="dash_nivel_disabled", 
                                help="Seleccione una entidad primero")
            
            # Usar los valores del session_state
            entidad_seleccionada = st.session_state.dash_entidad
            funcionario_seleccionado = st.session_state.dash_funcionario
            tipo_dato_seleccionado = st.session_state.dash_tipo
            nivel_seleccionado = st.session_state.dash_nivel
            
            # Aplicar todos los filtros al dataframe final
            df_filtrado = registros_df.copy()
            mascara = pd.Series([True] * len(registros_df), index=registros_df.index)

            if entidad_seleccionada != 'Todas':
                mascara &= (registros_df['Entidad'] == entidad_seleccionada)
            
            if funcionario_seleccionado != 'Todos' and 'Funcionario' in registros_df.columns:
                mascara &= (registros_df['Funcionario'] == funcionario_seleccionado)
            
            if tipo_dato_seleccionado != 'Todos':
                mascara &= (registros_df['TipoDato'].str.upper() == tipo_dato_seleccionado.upper())
            
            if nivel_seleccionado != 'Todos':
                mascara &= (registros_df['Nivel Información '] == nivel_seleccionado)
            
            # Aplicar máscara una sola vez
            df_filtrado = registros_df[mascara]
            
            st.markdown("---")
            
            # Mostrar dashboard completo
            mostrar_dashboard(df_filtrado, metas_nuevas_df, metas_actualizar_df, registros_df,
                            entidad_seleccionada, funcionario_seleccionado, nivel_seleccionado)

        # ===== TAB 2: EDICIÓN =====
              
        with tab2:
            # Verificar autenticación para edición
            from auth_utils import verificar_autenticacion
            
            if verificar_autenticacion():
                # Usuario autenticado - permitir edición
                registros_df = mostrar_edicion_registros(registros_df)
            else:
                # Usuario no autenticado - mostrar mensaje
                st.markdown('<div class="subtitle">🔐 Acceso Restringido - Edición de Registros</div>', unsafe_allow_html=True)
                
                st.warning("🔒 **Se requiere autenticación para acceder a la edición de registros**")
                
                st.info("""
                **Para acceder a esta funcionalidad:**
                1. 🔐 Use el panel "Acceso Administrativo" en la barra lateral
                2. 👤 Ingrese las credenciales de administrador
                3. ✅ Una vez autenticado, podrá editar registros
                
                **Funcionalidades disponibles sin autenticación:**
                - 📊 Dashboard y métricas
                - 📈 Seguimiento trimestral  
                - ⚠️ Alertas de vencimientos
                - 📋 Reportes y descargas
                """)
                
                # Mostrar imagen o icono decorativo
                st.markdown("""
                <div style="text-align: center; padding: 2rem;">
                    <div style="font-size: 4rem; color: #64748b;">🔐</div>
                    <p style="color: #64748b; font-style: italic;">Protección de datos habilitada</p>
                </div>
                """, unsafe_allow_html=True)

        with tab3:
            mostrar_seguimiento_trimestral(registros_df, meta_df)
        
        # ===== TAB 4: ALERTAS =====
        with tab4:
            mostrar_alertas_vencimientos(registros_df)

        # ===== TAB 5: REPORTES =====
        with tab5:
            st.markdown("### Filtros de Reportes")
            
            # Primera fila de filtros
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                # Filtro por Entidad
                entidades_reporte = ['Todas'] + sorted([e for e in registros_df['Entidad'].unique().tolist() if e])
                entidad_reporte = st.selectbox('Entidad', entidades_reporte, key="reporte_entidad")
            
            with col2:
                tipos_dato_reporte = ['Todos'] + sorted([t for t in registros_df['TipoDato'].dropna().unique().tolist() if t])
                tipo_dato_reporte = st.selectbox('Tipo de Dato', tipos_dato_reporte, key="reporte_tipo")
            
            with col3:
                acuerdo_opciones = ['Todos', 'Suscrito', 'No Suscrito']
                acuerdo_filtro = st.selectbox('Acuerdo de Compromiso', acuerdo_opciones, key="reporte_acuerdo")
            
            with col4:
                analisis_opciones = ['Todos', 'Completado', 'No Completado']
                analisis_filtro = st.selectbox('Análisis y Cronograma', analisis_opciones, key="reporte_analisis")
            
            # Segunda fila de filtros
            col5, col6, col7, col8 = st.columns(4)
            
            with col5:
                estandares_opciones = ['Todos', 'Completado', 'No Completado']
                estandares_filtro = st.selectbox('Estándares', estandares_opciones, key="reporte_estandares")
            
            with col6:
                publicacion_opciones = ['Todos', 'Completado', 'No Completado']
                publicacion_filtro = st.selectbox('Publicación', publicacion_opciones, key="reporte_publicacion")
            
            with col7:
                finalizado_opciones = ['Todos', 'Finalizado', 'No Finalizado']
                finalizado_filtro = st.selectbox('Finalizado', finalizado_opciones, key="reporte_finalizado")
            
            
            
            with col8:
                # FILTRO: Mes Proyectado
                meses_disponibles = ['Todos']
                if 'Mes Proyectado' in registros_df.columns:
                    meses_unicos = [m for m in registros_df['Mes Proyectado'].dropna().unique().tolist() if m]
                    meses_disponibles += sorted(meses_unicos)
                mes_filtro = st.selectbox('Mes Proyectado', meses_disponibles, key="reporte_mes")
            
            st.markdown("---")
            
            # Mostrar reportes
            # Mostrar reportes
            mostrar_reportes(registros_df, entidad_reporte, tipo_dato_reporte, acuerdo_filtro, analisis_filtro, 
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
            # Mostrar fecha del último respaldo en horario de Bogotá
            try:
                from backup_utils import obtener_fecha_ultimo_respaldo
                import pytz
                
                fecha_respaldo = obtener_fecha_ultimo_respaldo()
                if fecha_respaldo and isinstance(fecha_respaldo, datetime):
                    # Convertir a horario de Bogotá
                    bogota_tz = pytz.timezone('America/Bogota')
                    if fecha_respaldo.tzinfo is None:
                        # Si no tiene timezone, asumimos UTC y convertimos
                        fecha_respaldo = pytz.utc.localize(fecha_respaldo)
                    fecha_bogota = fecha_respaldo.astimezone(bogota_tz)
                    respaldo_str = fecha_bogota.strftime("%d/%m %H:%M")
                    st.metric("Último Respaldo", respaldo_str)
                elif fecha_respaldo:
                    st.metric("Respaldo", "Disponible")
                else:
                    st.metric("Respaldo", "Sin datos")
            except Exception as e:
                # Fallback: mostrar hora actual de Bogotá
                try:
                    import pytz
                    bogota_tz = pytz.timezone('America/Bogota')
                    hora_bogota = datetime.now(bogota_tz).strftime("%H:%M")
                    st.metric("Actualizado", hora_bogota)
                except:
                    ultima_actualizacion = datetime.now().strftime("%H:%M")
                    st.metric("Actualizado", ultima_actualizacion)
        
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
# ========== AGREGAR ESTAS FUNCIONES AL FINAL DE app1.py ==========

def limpiar_estado_temporal(key_temp):
    """Limpia el estado temporal de un registro."""
    try:
        if key_temp in st.session_state:
            del st.session_state[key_temp]
        if f"{key_temp}_modified" in st.session_state:
            del st.session_state[f"{key_temp}_modified"]
        
        keys_to_remove = [key for key in st.session_state.keys() if key.startswith(key_temp)]
        for key in keys_to_remove:
            if key != key_temp and f"{key_temp}_modified" not in key:
                try:
                    del st.session_state[key]
                except:
                    pass
    except Exception as e:
        pass

def crear_widget_simple(widget_type, label, key_temp, campo, **kwargs):
    """Crea widgets SIN callbacks para evitar recargas automáticas."""
    valor_actual = obtener_valor_temporal(key_temp, campo, kwargs.get('value', ''))
    widget_key = f"{key_temp}_{campo}_simple"
    
    if widget_type == 'selectbox':
        options = kwargs.get('options', [])
        index = options.index(valor_actual) if valor_actual in options else 0
        nuevo_valor = st.selectbox(
            label,
            options=options,
            index=index,
            key=widget_key,
            **{k: v for k, v in kwargs.items() if k not in ['options', 'value']}
        )
    
    elif widget_type == 'text_input':
        nuevo_valor = st.text_input(
            label,
            value=valor_actual,
            key=widget_key,
            **{k: v for k, v in kwargs.items() if k not in ['value']}
        )
    
    elif widget_type == 'text_area':
        nuevo_valor = st.text_area(
            label,
            value=valor_actual,
            key=widget_key,
            **{k: v for k, v in kwargs.items() if k not in ['value']}
        )
    else:
        return None
    
    if nuevo_valor != valor_actual:
        actualizar_campo_temporal(key_temp, campo, nuevo_valor)
    
    return nuevo_valor

def crear_selector_fecha_simple(label, key_temp, campo, help_text=None):
    """Selector de fecha SIN callbacks automáticos."""
    valor_actual = obtener_valor_temporal(key_temp, campo, "")
    
    check_key = f"{key_temp}_{campo}_check_simple"
    date_key = f"{key_temp}_{campo}_date_simple"
    clear_key = f"{key_temp}_{campo}_clear_simple"
    
    col_check, col_fecha, col_borrar = st.columns([1, 6, 1])
    
    with col_check:
        tiene_fecha = bool(valor_actual and valor_actual.strip())
        usar_fecha = st.checkbox("📅", value=tiene_fecha, key=check_key, help="Marcar para usar fecha")
        
        if not usar_fecha and valor_actual:
            actualizar_campo_temporal(key_temp, campo, "")
    
    with col_fecha:
        if usar_fecha:
            fecha_valor = fecha_para_selector(valor_actual) if valor_actual else datetime.now().date()
            
            nueva_fecha = st.date_input(
                label,
                value=fecha_valor,
                key=date_key,
                help=help_text
            )
            
            fecha_str = fecha_desde_selector_a_string(nueva_fecha)
            if fecha_str != valor_actual:
                actualizar_campo_temporal(key_temp, campo, fecha_str)
        else:
            st.text_input(
                label,
                value="(Sin fecha asignada)",
                disabled=True,
                key=f"disabled_{date_key}"
            )
    
    with col_borrar:
        if usar_fecha:
            if st.button("🗑️", key=clear_key, help="Limpiar fecha"):
                actualizar_campo_temporal(key_temp, campo, "")
                st.success("Fecha limpiada")
                st.session_state[check_key] = False

def mostrar_edicion_registros_corregida(registros_df):
    """VERSIÓN CORREGIDA sin recargas automáticas."""
    st.markdown('<div class="subtitle">Edición de Registros</div>', unsafe_allow_html=True)

    st.info("Esta sección permite editar los datos. Los cambios se aplican al presionar 'Guardar Registro'.")

    st.warning("""
    **Importante**: 
    - ⚠️ **Los cambios se mantienen temporalmente hasta que presione "Guardar Registro"**
    - ✅ **El formulario NO se recarga automáticamente**
    - Las validaciones se aplicarán automáticamente al guardar
    """)
    
    if 'mensaje_guardado' in st.session_state and st.session_state.mensaje_guardado:
        if st.session_state.mensaje_guardado[0] == "success":
            st.success(st.session_state.mensaje_guardado[1])
        else:
            st.error(st.session_state.mensaje_guardado[1])
        st.session_state.mensaje_guardado = None

    st.markdown("### Edición Individual de Registros")

    if registros_df.empty:
        st.warning("No hay registros disponibles para editar.")
        return registros_df

    codigos_registros = registros_df['Cod'].astype(str).tolist()
    entidades_registros = registros_df['Entidad'].tolist()
    niveles_registros = registros_df['Nivel Información '].tolist()

    opciones_registros = [f"{codigos_registros[i]} - {entidades_registros[i]} - {niveles_registros[i]}"
                          for i in range(len(codigos_registros))]

    seleccion_registro = st.selectbox(
        "Seleccione un registro para editar:",
        options=opciones_registros,
        key="selector_registro_corregido"
    )

    indice_seleccionado = opciones_registros.index(seleccion_registro)
    key_temp = inicializar_estado_temporal(indice_seleccionado, registros_df)
    cambios_pendientes = hay_cambios_pendientes(key_temp)
    
    if cambios_pendientes:
        st.warning("⚠️ **Hay cambios sin guardar.** Presione 'Guardar Registro' para aplicar los cambios.")

    try:
        row_original = registros_df.iloc[indice_seleccionado].copy()

        with st.container():
            st.markdown("---")
            st.markdown(f"### Editando Registro #{row_original['Cod']} - {row_original['Entidad']}")
            st.markdown(f"**Nivel de Información:** {row_original['Nivel Información ']}")
            st.markdown("---")

            # Información básica
            st.markdown("### 1. Información Básica")
            col1, col2, col3 = st.columns(3)

            with col1:
                st.text_input("Código", value=row_original['Cod'], disabled=True)

            with col2:
                crear_widget_simple(
                    'selectbox',
                    "Tipo de Dato",
                    key_temp,
                    'TipoDato',
                    options=["", "Nuevo", "Actualizar"]
                )

            with col3:
                meses = ["", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", 
                        "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
                
                crear_widget_simple(
                    'selectbox',
                    "Mes Proyectado",
                    key_temp,
                    'Mes Proyectado',
                    options=meses
                )

            # Fechas importantes
            st.markdown("### 2. Fechas Importantes")
            col1, col2 = st.columns(2)

            with col1:
                crear_selector_fecha_simple(
                    "Fecha de entrega de información",
                    key_temp,
                    'Fecha de entrega de información'
                )

            with col2:
                plazo_analisis_temp = obtener_valor_temporal(key_temp, 'Plazo de análisis', '')
                st.text_input(
                    "Plazo de análisis (calculado automáticamente)",
                    value=plazo_analisis_temp,
                    disabled=True,
                    key=f"plazo_analisis_display_{key_temp}",
                    help="Se calcula automáticamente"
                )

            # Estados del proceso
            st.markdown("### 3. Estados del Proceso")
            col1, col2, col3 = st.columns(3)

            with col1:
                crear_widget_simple(
                    'selectbox',
                    "Acuerdo de compromiso",
                    key_temp,
                    'Acuerdo de compromiso',
                    options=["", "Si", "No"]
                )

            with col2:
                crear_selector_fecha_simple(
                    "Análisis y cronograma (fecha real)",
                    key_temp,
                    'Análisis y cronograma'
                )

            with col3:
                crear_selector_fecha_simple(
                    "Estándares (fecha real)",
                    key_temp,
                    'Estándares'
                )

            # Publicación
            st.markdown("### 4. Publicación")
            col1, col2 = st.columns(2)

            with col1:
                crear_selector_fecha_simple(
                    "Publicación (fecha real)",
                    key_temp,
                    'Publicación'
                )

            with col2:
                publicacion_temp = obtener_valor_temporal(key_temp, 'Publicación', '')
                tiene_publicacion = publicacion_temp and pd.notna(publicacion_temp) and str(publicacion_temp).strip() != ''
                
                if tiene_publicacion:
                    crear_selector_fecha_simple(
                        "Fecha de oficio de cierre",
                        key_temp,
                        'Fecha de oficio de cierre'
                    )
                else:
                    st.warning("⚠️ Para introducir fecha de oficio de cierre, primero debe completar la etapa de Publicación")
                    fecha_oficio_temp = obtener_valor_temporal(key_temp, 'Fecha de oficio de cierre', '')
                    st.text_input(
                        "Fecha de oficio de cierre (requiere publicación)",
                        value=fecha_oficio_temp,
                        disabled=True,
                        key=f"oficio_disabled_{key_temp}"
                    )

            # Información adicional
            st.markdown("### 5. Información Adicional")
            col1, col2 = st.columns(2)
            
            with col1:
                opciones_estado = ["", "En proceso", "En proceso oficio de cierre", "Completado", "Finalizado"]
                crear_widget_simple(
                    'selectbox',
                    "Estado",
                    key_temp,
                    'Estado',
                    options=opciones_estado
                )

            with col2:
                funcionarios = [""] + sorted([f for f in registros_df['Funcionario'].dropna().unique().tolist() if f])
                crear_widget_simple(
                    'selectbox',
                    "Funcionario",
                    key_temp,
                    'Funcionario',
                    options=funcionarios
                )

            crear_widget_simple(
                'text_area',
                "Observación",
                key_temp,
                'Observación',
                height=100
            )
            
if __name__ == "__main__":
    main()
        

        
