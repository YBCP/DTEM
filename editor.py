# editor.py - ARREGLADO: Los campos aparecen INMEDIATAMENTE
"""
ÚNICO CAMBIO: Los campos de texto aparecen inmediatamente al seleccionar "Nuevo funcionario" o "Nueva entidad"
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date
import time

# LISTAS DE OPCIONES
MESES = ["", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
         "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]

FRECUENCIAS = ["", "Diaria", "Semanal", "Quincenal", "Mensual", "Bimestral", 
               "Trimestral", "Semestral", "Anual", "Eventual"]

# IMPORTS SEGUROS
try:
    from sheets_utils import GoogleSheetsManager
except ImportError:
    GoogleSheetsManager = None

def get_safe_value(row, column_name, default=''):
    """Obtiene un valor de forma segura del DataFrame"""
    try:
        if column_name in row.index:
            value = row[column_name]
            if pd.isna(value) or value is None:
                return default
            return str(value).strip()
        return default
    except:
        return default

def obtener_funcionarios_unicos(df):
    """Obtiene lista única de funcionarios limpios"""
    if df is None or 'Funcionario' not in df.columns:
        return []
    
    funcionarios = []
    for func in df['Funcionario'].dropna().unique():
        func_str = str(func).strip()
        if func_str and func_str.lower() not in ['nan', 'none', '']:
            funcionarios.append(func_str)
    
    return sorted(list(set(funcionarios)))

def obtener_entidades_unicas(df):
    """Obtiene lista única de entidades limpias"""
    if df is None or 'Entidad' not in df.columns:
        return []
    
    entidades = []
    for ent in df['Entidad'].dropna().unique():
        ent_str = str(ent).strip()
        if ent_str and ent_str.lower() not in ['nan', 'none', '']:
            entidades.append(ent_str)
    
    return sorted(list(set(entidades)))

def fecha_a_string(fecha):
    """Convierte fecha a string"""
    if fecha is None:
        return ""
    try:
        if isinstance(fecha, date):
            return fecha.strftime("%d/%m/%Y")
        elif isinstance(fecha, str) and fecha.strip():
            return fecha.strip()
        else:
            return ""
    except:
        return ""

def string_a_fecha(fecha_str):
    """Convierte string a fecha"""
    if not fecha_str or not fecha_str.strip() or fecha_str.strip() == "":
        return None
    
    try:
        formatos = ["%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"]
        for formato in formatos:
            try:
                return datetime.strptime(fecha_str.strip(), formato).date()
            except:
                continue
        return None
    except:
        return None

def guardar_en_sheets(df):
    """Guarda datos en Google Sheets"""
    if GoogleSheetsManager is None:
        return False, "GoogleSheetsManager no disponible"
    
    try:
        manager = GoogleSheetsManager()
        if df.empty:
            return False, "No se puede guardar un DataFrame vacío"
        
        df_clean = df.copy()
        df_clean = df_clean.fillna('')
        df_clean = df_clean.astype(str)
        df_clean = df_clean.replace('nan', '').replace('None', '')
        
        exito = manager.escribir_hoja(df_clean, "Registros", limpiar_hoja=True)
        
        if exito:
            st.session_state['registros_df'] = df_clean
            return True, "Datos guardados en Google Sheets"
        else:
            return False, "Error al escribir en Google Sheets"
            
    except Exception as e:
        return False, f"Error: {str(e)}"

def calcular_avance(row):
    """Calcula porcentaje de avance"""
    try:
        avance = 0
        if get_safe_value(row, 'Acuerdo de compromiso', '').lower() in ['si', 'sí']:
            avance += 25
        if get_safe_value(row, 'Análisis y cronograma', '').strip():
            avance += 25
        if get_safe_value(row, 'Estándares', '').strip():
            avance += 25
        if get_safe_value(row, 'Publicación', '').strip():
            avance += 25
        return min(avance, 100)
    except:
        return 0

def generar_codigo(df):
    """Genera nuevo código"""
    try:
        if df.empty:
            return "001"
        
        max_codigo = 0
        for _, row in df.iterrows():
            try:
                codigo_str = str(get_safe_value(row, 'Cod', '0'))
                numero = int(''.join(filter(str.isdigit, codigo_str)))
                if numero > max_codigo:
                    max_codigo = numero
            except:
                continue
        
        return f"{max_codigo + 1:03d}"
    except:
        return "001"

def mostrar_selector_funcionario(funcionario_actual, funcionarios_existentes, key_base):
    """
    SOLUCIÓN SIN BOTONES: Compatible con st.form
    """
    st.markdown("**Funcionario:**")
    
    # Selectbox normal con opción "Nuevo funcionario"
    opciones = [""] + funcionarios_existentes + ["➕ Nuevo funcionario"]
    
    valor_inicial = 0
    if funcionario_actual and funcionario_actual in funcionarios_existentes:
        valor_inicial = funcionarios_existentes.index(funcionario_actual) + 1
    
    seleccion = st.selectbox(
        "Funcionario:",
        opciones,
        index=valor_inicial,
        key=f"func_select_{key_base}"
    )
    
    # Si selecciona "Nuevo funcionario", mostrar campo inmediatamente
    if seleccion == "➕ Nuevo funcionario":
        nuevo_funcionario = st.text_input(
            "Escriba el nombre del nuevo funcionario:",
            value="",
            placeholder="Nombre completo del funcionario",
            key=f"func_nuevo_{key_base}"
        )
        return nuevo_funcionario.strip() if nuevo_funcionario else ""
    elif seleccion == "":
        return ""
    else:
        return seleccion

def mostrar_selector_entidad(entidad_actual, entidades_existentes, key_base):
    """
    SOLUCIÓN SIN BOTONES: Compatible con st.form
    """
    st.markdown("**Entidad:**")
    
    # Selectbox normal con opción "Nueva entidad"
    opciones = [""] + entidades_existentes + ["➕ Nueva entidad"]
    
    valor_inicial = 0
    if entidad_actual and entidad_actual in entidades_existentes:
        valor_inicial = entidades_existentes.index(entidad_actual) + 1
    
    seleccion = st.selectbox(
        "Entidad:",
        opciones,
        index=valor_inicial,
        key=f"ent_select_{key_base}"
    )
    
    # Si selecciona "Nueva entidad", mostrar campo inmediatamente  
    if seleccion == "➕ Nueva entidad":
        nueva_entidad = st.text_input(
            "Escriba el nombre de la nueva entidad:",
            value="",
            placeholder="Nombre completo de la entidad",
            key=f"ent_nueva_{key_base}"
        )
        return nueva_entidad.strip() if nueva_entidad else ""
    elif seleccion == "":
        return ""
    else:
        return seleccion

def mostrar_formulario_completo(row, indice, es_nuevo=False, df=None):
    """FORMULARIO COMPLETO - Solo se modifican los selectores de funcionario y entidad"""
    
    # Obtener listas existentes
    funcionarios_existentes = obtener_funcionarios_unicos(df)
    entidades_existentes = obtener_entidades_unicas(df)
    
    # Key base único
    key_base = f"{indice}_{'nuevo' if es_nuevo else 'edit'}_{datetime.now().microsecond}"
    
    # ======================
    # INFORMACIÓN BÁSICA
    # ======================
    st.subheader("Información Básica")
    col1, col2 = st.columns(2)
    
    with col1:
        # CÓDIGO
        codigo = st.text_input(
            "Código:",
            value=get_safe_value(row, 'Cod'),
            disabled=es_nuevo,
            key=f"codigo_{key_base}"
        )
        
        # FUNCIONARIO - CORREGIDO
        funcionario_actual = get_safe_value(row, 'Funcionario')
        funcionario = mostrar_selector_funcionario(funcionario_actual, funcionarios_existentes, key_base)
    
    with col2:
        # ENTIDAD - CORREGIDO  
        entidad_actual = get_safe_value(row, 'Entidad')
        entidad = mostrar_selector_entidad(entidad_actual, entidades_existentes, key_base)
        
        # NIVEL DE INFORMACIÓN
        nivel_info = st.text_input(
            "Nivel de Información:",
            value=get_safe_value(row, 'Nivel Información '),
            key=f"nivel_{key_base}"
        )
    
    # TIPO DE DATO
    col1, col2, col3 = st.columns(3)
    with col1:
        tipo_actual = get_safe_value(row, 'TipoDato')
        tipo_opciones = ["", "Actualizar", "Nuevo"]
        tipo_index = tipo_opciones.index(tipo_actual) if tipo_actual in tipo_opciones else 0
        
        tipo_dato = st.selectbox(
            "Tipo de Dato:",
            options=tipo_opciones,
            index=tipo_index,
            key=f"tipo_{key_base}"
        )
    
    with col2:
        # MES PROYECTADO
        mes_actual = get_safe_value(row, 'Mes Proyectado')
        mes_index = MESES.index(mes_actual) if mes_actual in MESES else 0
        
        mes_proyectado = st.selectbox(
            "Mes Proyectado:",
            options=MESES,
            index=mes_index,
            key=f"mes_{key_base}"
        )
    
    with col3:
        # FRECUENCIA
        frecuencia_actual = get_safe_value(row, 'Frecuencia actualizacion ')
        frecuencia_index = FRECUENCIAS.index(frecuencia_actual) if frecuencia_actual in FRECUENCIAS else 0
        
        frecuencia = st.selectbox(
            "Frecuencia:",
            options=FRECUENCIAS,
            index=frecuencia_index,
            key=f"freq_{key_base}"
        )
    
    # ======================
    # ACUERDOS Y COMPROMISOS
    # ======================
    st.subheader("Acuerdos y Compromisos")
    col1, col2 = st.columns(2)
    
    with col1:
        # ACTAS DE INTERÉS
        actas_value = get_safe_value(row, 'Actas de acercamiento y manifestación de interés')
        actas_index = 0
        if actas_value in ["Si", "No"]:
            actas_index = ["", "Si", "No"].index(actas_value)
        
        actas_interes = st.selectbox(
            "Actas de interés:",
            options=["", "Si", "No"],
            index=actas_index,
            key=f"actas_{key_base}"
        )
        
        # ACUERDO DE COMPROMISO
        acuerdo_value = get_safe_value(row, 'Acuerdo de compromiso')
        acuerdo_index = 0
        if acuerdo_value in ["Si", "No"]:
            acuerdo_index = ["", "Si", "No"].index(acuerdo_value)
        
        acuerdo_compromiso = st.selectbox(
            "Acuerdo de compromiso:",
            options=["", "Si", "No"],
            index=acuerdo_index,
            key=f"acuerdo_{key_base}"
        )
    
    with col2:
        # FECHAS DE ACUERDOS
        suscripcion_fecha = string_a_fecha(get_safe_value(row, 'Suscripción acuerdo de compromiso'))
        suscripcion = st.date_input(
            "Suscripción acuerdo:",
            value=suscripcion_fecha,
            key=f"suscripcion_{key_base}"
        )
        
        if st.checkbox("Limpiar fecha suscripción", key=f"limpiar_susc_{key_base}"):
            suscripcion = None
        
        entrega_fecha = string_a_fecha(get_safe_value(row, 'Entrega acuerdo de compromiso'))
        entrega_acuerdo = st.date_input(
            "Entrega acuerdo:",
            value=entrega_fecha,
            key=f"entrega_{key_base}"
        )
        
        if st.checkbox("Limpiar fecha entrega", key=f"limpiar_entrega_{key_base}"):
            entrega_acuerdo = None
    
    # ======================
    # GESTIÓN DE INFORMACIÓN  
    # ======================
    st.subheader("Gestión de Información")
    col1, col2 = st.columns(2)
    
    with col1:
        acceso_value = get_safe_value(row, 'Gestion acceso a los datos y documentos requeridos ')
        acceso_index = 0
        if acceso_value in ["Si", "No"]:
            acceso_index = ["", "Si", "No"].index(acceso_value)
        
        acceso_datos = st.selectbox(
            "Acceso a datos:",
            options=["", "Si", "No"],
            index=acceso_index,
            key=f"acceso_{key_base}"
        )
        
        analisis_value = get_safe_value(row, ' Análisis de información')
        analisis_index = 0
        if analisis_value in ["Si", "No"]:
            analisis_index = ["", "Si", "No"].index(analisis_value)
        
        analisis_info = st.selectbox(
            "Análisis de información:",
            options=["", "Si", "No"],
            index=analisis_index,
            key=f"analisis_info_{key_base}"
        )
    
    with col2:
        cronograma_value = get_safe_value(row, 'Cronograma Concertado')
        cronograma_index = 0
        if cronograma_value in ["Si", "No"]:
            cronograma_index = ["", "Si", "No"].index(cronograma_value)
        
        cronograma = st.selectbox(
            "Cronograma Concertado:",
            options=["", "Si", "No"],
            index=cronograma_index,
            key=f"cronograma_{key_base}"
        )
        
        fecha_entrega_date = string_a_fecha(get_safe_value(row, 'Fecha de entrega de información'))
        fecha_entrega = st.date_input(
            "Fecha entrega información:",
            value=fecha_entrega_date,
            key=f"fecha_entrega_{key_base}"
        )
        
        if st.checkbox("Limpiar fecha entrega información", key=f"limpiar_fecha_entrega_{key_base}"):
            fecha_entrega = None
    
    # ======================
    # FECHAS Y CRONOGRAMA
    # ======================
    st.subheader("Fechas y Cronograma")
    col1, col2 = st.columns(2)
    
    with col1:
        # ANÁLISIS PROGRAMADA
        analisis_prog_date = string_a_fecha(get_safe_value(row, 'Análisis y cronograma (fecha programada)'))
        analisis_programada = st.date_input(
            "Análisis programada:",
            value=analisis_prog_date,
            key=f"analisis_prog_{key_base}"
        )
        
        if st.checkbox("Limpiar análisis programada", key=f"limpiar_analisis_prog_{key_base}"):
            analisis_programada = None
        
        # ANÁLISIS REAL
        analisis_real_date = string_a_fecha(get_safe_value(row, 'Análisis y cronograma'))
        analisis_real = st.date_input(
            "Análisis real:",
            value=analisis_real_date,
            key=f"analisis_real_{key_base}"
        )
        
        if st.checkbox("Limpiar análisis real", key=f"limpiar_analisis_real_{key_base}"):
            analisis_real = None
    
    with col2:
        # SEGUIMIENTO A LOS ACUERDOS
        seguimiento_value = get_safe_value(row, 'Seguimiento a los acuerdos')
        seguimiento = st.text_area(
            "Seguimiento a los acuerdos:",
            value=seguimiento_value,
            height=100,
            key=f"seguimiento_{key_base}"
        )
    
    # ======================
    # ESTÁNDARES
    # ======================
    st.subheader("Estándares")
    col1, col2, col3 = st.columns(3)
    
    estandares_opciones = ["", "Completo", "Incompleto", "No aplica"]
    
    with col1:
        # REGISTRO
        registro_value = get_safe_value(row, 'Registro (completo)')
        registro_index = 0
        if registro_value in estandares_opciones:
            registro_index = estandares_opciones.index(registro_value)
        
        registro = st.selectbox(
            "Registro:",
            options=estandares_opciones,
            index=registro_index,
            key=f"registro_{key_base}"
        )
        
        # ET
        et_value = get_safe_value(row, 'ET (completo)')
        et_index = 0
        if et_value in estandares_opciones:
            et_index = estandares_opciones.index(et_value)
        
        et = st.selectbox(
            "ET:",
            options=estandares_opciones,
            index=et_index,
            key=f"et_{key_base}"
        )
    
    with col2:
        # CO
        co_value = get_safe_value(row, 'CO (completo)')
        co_index = 0
        if co_value in estandares_opciones:
            co_index = estandares_opciones.index(co_value)
        
        co = st.selectbox(
            "CO:",
            options=estandares_opciones,
            index=co_index,
            key=f"co_{key_base}"
        )
        
        # DD
        dd_value = get_safe_value(row, 'DD (completo)')
        dd_index = 0
        if dd_value in estandares_opciones:
            dd_index = estandares_opciones.index(dd_value)
        
        dd = st.selectbox(
            "DD:",
            options=estandares_opciones,
            index=dd_index,
            key=f"dd_{key_base}"
        )
    
    with col3:
        # REC
        rec_value = get_safe_value(row, 'REC (completo)')
        rec_index = 0
        if rec_value in estandares_opciones:
            rec_index = estandares_opciones.index(rec_value)
        
        rec = st.selectbox(
            "REC:",
            options=estandares_opciones,
            index=rec_index,
            key=f"rec_{key_base}"
        )
        
        # SERVICIO
        servicio_value = get_safe_value(row, 'SERVICIO (completo)')
        servicio_index = 0
        if servicio_value in estandares_opciones:
            servicio_index = estandares_opciones.index(servicio_value)
        
        servicio = st.selectbox(
            "SERVICIO:",
            options=estandares_opciones,
            index=servicio_index,
            key=f"servicio_{key_base}"
        )
    
    # FECHAS DE ESTÁNDARES
    col1, col2 = st.columns(2)
    with col1:
        # ESTÁNDARES PROGRAMADA
        est_prog_date = string_a_fecha(get_safe_value(row, 'Estándares (fecha programada)'))
        estandares_prog = st.date_input(
            "Estándares programada:",
            value=est_prog_date,
            key=f"est_prog_{key_base}"
        )
        
        if st.checkbox("Limpiar estándares programada", key=f"limpiar_est_prog_{key_base}"):
            estandares_prog = None
    
    with col2:
        # ESTÁNDARES REAL
        est_real_date = string_a_fecha(get_safe_value(row, 'Estándares'))
        estandares_real = st.date_input(
            "Estándares real:",
            value=est_real_date,
            key=f"est_real_{key_base}"
        )
        
        if st.checkbox("Limpiar estándares real", key=f"limpiar_est_real_{key_base}"):
            estandares_real = None
    
    # ======================
    # VERIFICACIONES
    # ======================
    st.subheader("Verificaciones")
    col1, col2 = st.columns(2)
    
    opciones_si_no = ["", "Si", "No"]
    
    with col1:
        # ORIENTACIÓN TÉCNICA
        orientacion_value = get_safe_value(row, 'Resultados de orientación técnica')
        orientacion_index = 0
        if orientacion_value in opciones_si_no:
            orientacion_index = opciones_si_no.index(orientacion_value)
        
        orientacion = st.selectbox(
            "Orientación técnica:",
            options=opciones_si_no,
            index=orientacion_index,
            key=f"orientacion_{key_base}"
        )
        
        # VERIFICACIÓN SERVICIO WEB
        verificacion_value = get_safe_value(row, 'Verificación del servicio web geográfico')
        verificacion_index = 0
        if verificacion_value in opciones_si_no:
            verificacion_index = opciones_si_no.index(verificacion_value)
        
        verificacion_web = st.selectbox(
            "Verificación servicio web:",
            options=opciones_si_no,
            index=verificacion_index,
            key=f"verificacion_{key_base}"
        )
    
    with col2:
        # VERIFICAR APROBAR
        aprobar_value = get_safe_value(row, 'Verificar Aprobar Resultados')
        aprobar_index = 0
        if aprobar_value in opciones_si_no:
            aprobar_index = opciones_si_no.index(aprobar_value)
        
        verificar_aprobar = st.selectbox(
            "Verificar Aprobar:",
            options=opciones_si_no,
            index=aprobar_index,
            key=f"aprobar_{key_base}"
        )
        
        # REVISAR Y VALIDAR
        revisar_value = get_safe_value(row, 'Revisar y validar los datos cargados en la base de datos')
        revisar_index = 0
        if revisar_value in opciones_si_no:
            revisar_index = opciones_si_no.index(revisar_value)
        
        revisar_validar = st.selectbox(
            "Revisar y validar:",
            options=opciones_si_no,
            index=revisar_index,
            key=f"revisar_{key_base}"
        )
    
    # APROBACIÓN RESULTADOS
    aprobacion_value = get_safe_value(row, 'Aprobación resultados obtenidos en la orientación')
    aprobacion_index = 0
    if aprobacion_value in opciones_si_no:
        aprobacion_index = opciones_si_no.index(aprobacion_value)
    
    aprobacion = st.selectbox(
        "Aprobación resultados:",
        options=opciones_si_no,
        index=aprobacion_index,
        key=f"aprobacion_{key_base}"
    )
    
    # ======================
    # PUBLICACIÓN
    # ======================
    st.subheader("Publicación")
    col1, col2 = st.columns(2)
    
    with col1:
        # PUBLICACIÓN PROGRAMADA
        pub_prog_date = string_a_fecha(get_safe_value(row, 'Fecha de publicación programada'))
        pub_programada = st.date_input(
            "Publicación programada:",
            value=pub_prog_date,
            key=f"pub_prog_{key_base}"
        )
        
        if st.checkbox("Limpiar publicación programada", key=f"limpiar_pub_prog_{key_base}"):
            pub_programada = None
        
        # PUBLICACIÓN REAL
        pub_real_date = string_a_fecha(get_safe_value(row, 'Publicación'))
        publicacion = st.date_input(
            "Publicación real:",
            value=pub_real_date,
            key=f"publicacion_{key_base}"
        )
        
        if st.checkbox("Limpiar publicación real", key=f"limpiar_publicacion_{key_base}"):
            publicacion = None
    
    with col2:
        # DISPONER DATOS TEMÁTICOS
        disponer_value = get_safe_value(row, 'Disponer datos temáticos')
        disponer_index = 0
        if disponer_value in opciones_si_no:
            disponer_index = opciones_si_no.index(disponer_value)
        
        disponer_datos = st.selectbox(
            "Disponer datos temáticos:",
            options=opciones_si_no,
            index=disponer_index,
            key=f"disponer_{key_base}"
        )
        
        # CATÁLOGO RECURSOS
        catalogo_value = get_safe_value(row, 'Catálogo de recursos geográficos')
        catalogo_index = 0
        if catalogo_value in opciones_si_no:
            catalogo_index = opciones_si_no.index(catalogo_value)
        
        catalogo = st.selectbox(
            "Catálogo recursos:",
            options=opciones_si_no,
            index=catalogo_index,
            key=f"catalogo_{key_base}"
        )
    
    # ======================
    # CIERRE
    # ======================
    st.subheader("Cierre")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # OFICIOS DE CIERRE
        oficios_value = get_safe_value(row, 'Oficios de cierre')
        oficios_index = 0
        if oficios_value in opciones_si_no:
            oficios_index = opciones_si_no.index(oficios_value)
        
        oficios_cierre = st.selectbox(
            "Oficios de cierre:",
            options=opciones_si_no,
            index=oficios_index,
            key=f"oficios_{key_base}"
        )
    
    with col2:
        # FECHA OFICIO DE CIERRE
        fecha_oficio_date = string_a_fecha(get_safe_value(row, 'Fecha de oficio de cierre'))
        fecha_oficio = st.date_input(
            "Fecha oficio cierre:",
            value=fecha_oficio_date,
            key=f"fecha_oficio_{key_base}"
        )
        
        if st.checkbox("Limpiar fecha oficio cierre", key=f"limpiar_fecha_oficio_{key_base}"):
            fecha_oficio = None
    
    with col3:
        # ESTADO
        estado_value = get_safe_value(row, 'Estado')
        estado_opciones = ["", "Completado", "En proceso", "Pendiente"]
        estado_index = 0
        if estado_value in estado_opciones:
            estado_index = estado_opciones.index(estado_value)
        
        estado = st.selectbox(
            "Estado:",
            options=estado_opciones,
            index=estado_index,
            key=f"estado_{key_base}"
        )
    
    # ======================
    # PLAZOS CALCULADOS
    # ======================
    st.subheader("Plazos Calculados (Solo Lectura)")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.text_input(
            "Plazo análisis:",
            value=get_safe_value(row, 'Plazo de análisis'),
            disabled=True,
            key=f"plazo_analisis_{key_base}"
        )
    
    with col2:
        st.text_input(
            "Plazo cronograma:",
            value=get_safe_value(row, 'Plazo de cronograma'),
            disabled=True,
            key=f"plazo_cronograma_{key_base}"
        )
    
    with col3:
        st.text_input(
            "Plazo oficio cierre:",
            value=get_safe_value(row, 'Plazo de oficio de cierre'),
            disabled=True,
            key=f"plazo_oficio_{key_base}"
        )
    
    # ======================
    # OBSERVACIONES
    # ======================
    st.subheader("Observaciones")
    observacion = st.text_area(
        "Observaciones:",
        value=get_safe_value(row, 'Observación'),
        height=100,
        key=f"obs_{key_base}"
    )
    
    # ======================
    # AVANCE CALCULADO
    # ======================
    avance_actual = calcular_avance(row)
    st.text_input(
        "Porcentaje de Avance (Calculado):",
        value=f"{avance_actual}%",
        disabled=True,
        key=f"avance_{key_base}"
    )
    
    # RETORNAR TODOS LOS VALORES
    return {
        'Cod': codigo,
        'Funcionario': funcionario,
        'Entidad': entidad,
        'Nivel Información ': nivel_info,
        'Frecuencia actualizacion ': frecuencia,
        'TipoDato': tipo_dato,
        'Mes Proyectado': mes_proyectado,
        'Actas de acercamiento y manifestación de interés': actas_interes,
        'Suscripción acuerdo de compromiso': fecha_a_string(suscripcion) if suscripcion else "",
        'Entrega acuerdo de compromiso': fecha_a_string(entrega_acuerdo) if entrega_acuerdo else "",
        'Acuerdo de compromiso': acuerdo_compromiso,
        'Gestion acceso a los datos y documentos requeridos ': acceso_datos,
        ' Análisis de información': analisis_info,
        'Cronograma Concertado': cronograma,
        'Análisis y cronograma (fecha programada)': fecha_a_string(analisis_programada) if analisis_programada else "",
        'Fecha de entrega de información': fecha_a_string(fecha_entrega) if fecha_entrega else "",
        'Plazo de análisis': get_safe_value(row, 'Plazo de análisis'),
        'Análisis y cronograma': fecha_a_string(analisis_real) if analisis_real else "",
        'Seguimiento a los acuerdos': seguimiento,
        'Registro (completo)': registro,
        'ET (completo)': et,
        'CO (completo)': co,
        'DD (completo)': dd,
        'REC (completo)': rec,
        'SERVICIO (completo)': servicio,
        'Estándares (fecha programada)': fecha_a_string(estandares_prog) if estandares_prog else "",
        'Estándares': fecha_a_string(estandares_real) if estandares_real else "",
        'Resultados de orientación técnica': orientacion,
        'Verificación del servicio web geográfico': verificacion_web,
        'Verificar Aprobar Resultados': verificar_aprobar,
        'Revisar y validar los datos cargados en la base de datos': revisar_validar,
        'Aprobación resultados obtenidos en la orientación': aprobacion,
        'Disponer datos temáticos': disponer_datos,
        'Fecha de publicación programada': fecha_a_string(pub_programada) if pub_programada else "",
        'Publicación': fecha_a_string(publicacion) if publicacion else "",
        'Catálogo de recursos geográficos': catalogo,
        'Oficios de cierre': oficios_cierre,
        'Fecha de oficio de cierre': fecha_a_string(fecha_oficio) if fecha_oficio else "",
        'Plazo de cronograma': get_safe_value(row, 'Plazo de cronograma'),
        'Plazo de oficio de cierre': get_safe_value(row, 'Plazo de oficio de cierre'),
        'Estado': estado,
        'Observación': observacion
    }

def mostrar_edicion_registros(registros_df):
    """Editor principal"""
    st.subheader("Editor de Registros")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        total = len(registros_df) if not registros_df.empty else 0
        st.metric("Total Registros", total)
    
    with col2:
        if 'ultimo_guardado' in st.session_state:
            st.success(f"Último guardado: {st.session_state.ultimo_guardado}")
    
    if registros_df.empty:
        st.warning("No hay datos disponibles")
        return registros_df
    
    # Pestañas principales
    tab1, tab2 = st.tabs(["Editar Existente", "Crear Nuevo"])
    
    with tab1:
        st.subheader("Editar Registro Existente")
        
        # Búsqueda de registros
        termino = st.text_input(
            "Buscar registro:",
            placeholder="Código, entidad o nivel de información...",
            key="busqueda_editar"
        )
        
        # Filtrar opciones
        opciones = []
        for idx, row in registros_df.iterrows():
            codigo = get_safe_value(row, 'Cod', 'N/A')
            nivel = get_safe_value(row, 'Nivel Información ', 'Sin nivel')
            entidad = get_safe_value(row, 'Entidad', 'Sin entidad')
            opcion = f"{codigo} - {nivel} - {entidad}"
            
            if termino:
                if termino.lower() in opcion.lower():
                    opciones.append((idx, opcion))
            else:
                opciones.append((idx, opcion))
        
        if not opciones:
            st.warning("No hay registros disponibles")
            return registros_df
        
        # Selector de registro
        opciones_mostrar = [opcion for _, opcion in opciones]
        if termino:
            st.info(f"{len(opciones)} registros encontrados")
        
        seleccion = st.selectbox("Registro a editar:", opciones_mostrar, key="select_editar")
        
        # Obtener índice real
        indice_real = None
        for idx, opcion in opciones:
            if opcion == seleccion:
                indice_real = idx
                break
        
        if indice_real is not None:
            row_seleccionada = registros_df.iloc[indice_real]
            
            with st.form("form_editar_completo"):
                valores = mostrar_formulario_completo(row_seleccionada, indice_real, False, registros_df)
                
                if st.form_submit_button("Guardar Cambios", type="primary"):
                    if not valores['Funcionario'].strip():
                        st.error("El campo 'Funcionario' es obligatorio")
                    elif not valores['Entidad'].strip():
                        st.error("El campo 'Entidad' es obligatorio")
                    else:
                        try:
                            # Actualizar registro
                            for campo, valor in valores.items():
                                if campo in registros_df.columns:
                                    registros_df.iloc[indice_real, registros_df.columns.get_loc(campo)] = valor
                            
                            # Calcular avance
                            nuevo_avance = calcular_avance(registros_df.iloc[indice_real])
                            if 'Porcentaje Avance' in registros_df.columns:
                                registros_df.iloc[indice_real, registros_df.columns.get_loc('Porcentaje Avance')] = nuevo_avance
                            
                            # Guardar
                            exito, mensaje = guardar_en_sheets(registros_df)
                            
                            if exito:
                                st.success(f"Registro actualizado correctamente. Avance: {nuevo_avance}%")
                                st.session_state['registros_df'] = registros_df
                                st.session_state.ultimo_guardado = datetime.now().strftime("%H:%M:%S")
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error(f"Error: {mensaje}")
                        except Exception as e:
                            st.error(f"Error guardando: {e}")
    
    with tab2:
        st.subheader("Crear Nuevo Registro")
        
        # Generar código automático
        nuevo_codigo = generar_codigo(registros_df)
        st.info(f"Código automático: {nuevo_codigo}")
        
        # Registro vacío
        registro_vacio = pd.Series({col: '' for col in registros_df.columns})
        registro_vacio['Cod'] = nuevo_codigo
        
        with st.form("form_crear_completo"):
            valores_nuevo = mostrar_formulario_completo(registro_vacio, "nuevo", True, registros_df)
            
            if st.form_submit_button("Crear Registro", type="primary"):
                if not valores_nuevo['Funcionario'].strip():
                    st.error("El campo 'Funcionario' es obligatorio")
                elif not valores_nuevo['Entidad'].strip():
                    st.error("El campo 'Entidad' es obligatorio")
                else:
                    try:
                        # Crear nuevo registro
                        nuevo_registro = pd.Series({col: '' for col in registros_df.columns})
                        
                        # Asignar valores
                        for campo, valor in valores_nuevo.items():
                            if campo in nuevo_registro.index:
                                nuevo_registro[campo] = valor
                        
                        # Calcular avance inicial
                        avance = calcular_avance(nuevo_registro)
                        nuevo_registro['Porcentaje Avance'] = avance
                        
                        # Agregar al DataFrame
                        registros_df = pd.concat([registros_df, nuevo_registro.to_frame().T], ignore_index=True)
                        
                        # Guardar
                        exito, mensaje = guardar_en_sheets(registros_df)
                        
                        if exito:
                            st.success(f"Registro {nuevo_codigo} creado exitosamente!")
                            st.session_state['registros_df'] = registros_df
                            st.session_state.ultimo_guardado = datetime.now().strftime("%H:%M:%S")
                            st.balloons()
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error(f"Error: {mensaje}")
                    except Exception as e:
                        st.error(f"Error creando registro: {e}")
    
    return registros_df

def mostrar_edicion_registros_con_autenticacion(registros_df):
    """Wrapper con autenticación"""
    try:
        from auth_utils import verificar_autenticacion
        
        if verificar_autenticacion():
            # Usar datos actualizados
            if 'registros_df' in st.session_state:
                registros_df = st.session_state['registros_df']
            
            return mostrar_edicion_registros(registros_df)
        else:
            st.subheader("Acceso Restringido")
            st.warning("Se requiere autenticación para editar registros")
            return registros_df
            
    except ImportError:
        st.warning("Sistema de autenticación no disponible")
        return mostrar_edicion_registros(registros_df)
