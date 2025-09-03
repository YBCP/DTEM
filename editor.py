# editor.py - CORREGIDO CON TODAS LAS SECCIONES - VERSIÓN LIMPIA
"""
Editor de registros CORREGIDO - Todas las secciones de Google Sheets
- Información básica
- Acuerdos y compromisos  
- Gestión de información
- Cronograma y fechas
- Estándares (todos los campos)
- Verificaciones
- Publicación
- Cierre
- Sin iconos innecesarios
- Interfaz limpia
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

ESTADOS_ESTANDARES = ["", "Completo", "Incompleto", "No aplica"]
OPCIONES_SI_NO = ["", "Si", "No"]
ESTADOS_REGISTRO = ["", "Completado", "En proceso", "Pendiente"]

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
    """Obtiene lista única de funcionarios"""
    if df is None or 'Funcionario' not in df.columns:
        return []
    
    funcionarios = []
    for func in df['Funcionario'].dropna().unique():
        func_str = str(func).strip()
        if func_str and func_str.lower() not in ['nan', 'none', '']:
            funcionarios.append(func_str)
    
    return sorted(list(set(funcionarios)))

def obtener_entidades_unicas(df):
    """Obtiene lista única de entidades"""
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
    if not fecha_str or not fecha_str.strip():
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

def mostrar_selector_con_nuevo(label, valor_actual, opciones_existentes, key_base, placeholder="nuevo"):
    """Selector con opción de agregar nuevo - LIMPIO"""
    
    opciones = [""] + opciones_existentes + [f"+ Nuevo {placeholder}"]
    
    valor_inicial = 0
    if valor_actual and valor_actual in opciones_existentes:
        valor_inicial = opciones_existentes.index(valor_actual) + 1
    
    seleccion = st.selectbox(
        label,
        opciones,
        index=valor_inicial,
        key=f"select_{key_base}"
    )
    
    es_nuevo = seleccion.startswith("+ Nuevo")
    
    nuevo_valor = st.text_input(
        f"Nombre del {placeholder}:",
        value="",
        placeholder=f"Escriba el nombre" if es_nuevo else f"Seleccione 'Nuevo {placeholder}' arriba",
        disabled=not es_nuevo,
        key=f"nuevo_{key_base}"
    )
    
    if es_nuevo:
        return nuevo_valor.strip() if nuevo_valor else ""
    elif seleccion == "":
        return ""
    else:
        return seleccion

def mostrar_campo_fecha_con_limpiar(label, fecha_actual, key_base):
    """Campo de fecha con opción de limpiar - LIMPIO"""
    col1, col2 = st.columns([3, 1])
    
    with col1:
        fecha_date = string_a_fecha(fecha_actual)
        fecha = st.date_input(label, value=fecha_date, key=f"fecha_{key_base}")
    
    with col2:
        st.write("")
        limpiar = st.checkbox("Limpiar", key=f"limpiar_{key_base}")
    
    return None if limpiar else fecha

def mostrar_formulario_completo_todas_secciones(row, indice, es_nuevo=False, df=None):
    """FORMULARIO COMPLETO CON TODAS LAS SECCIONES DE GOOGLE SHEETS"""
    
    funcionarios_existentes = obtener_funcionarios_unicos(df)
    entidades_existentes = obtener_entidades_unicas(df)
    key_base = f"{indice}_{datetime.now().microsecond}"
    
    # ==================== INFORMACIÓN BÁSICA ====================
    st.markdown("### Información Básica")
    
    col1, col2 = st.columns(2)
    
    with col1:
        codigo = st.text_input(
            "Código:",
            value=get_safe_value(row, 'Cod'),
            disabled=es_nuevo,
            key=f"cod_{key_base}"
        )
        
        funcionario = mostrar_selector_con_nuevo(
            "Funcionario:",
            get_safe_value(row, 'Funcionario'),
            funcionarios_existentes,
            f"func_{key_base}",
            "funcionario"
        )
    
    with col2:
        entidad = mostrar_selector_con_nuevo(
            "Entidad:",
            get_safe_value(row, 'Entidad'),
            entidades_existentes,
            f"ent_{key_base}",
            "entidad"
        )
        
        nivel_info = st.text_input(
            "Nivel de Información:",
            value=get_safe_value(row, 'Nivel Información '),
            key=f"nivel_{key_base}"
        )
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        tipo_actual = get_safe_value(row, 'TipoDato')
        tipo_index = 0
        if tipo_actual in ["Actualizar", "Nuevo"]:
            tipo_index = ["", "Actualizar", "Nuevo"].index(tipo_actual)
        
        tipo_dato = st.selectbox(
            "Tipo de Dato:",
            ["", "Actualizar", "Nuevo"],
            index=tipo_index,
            key=f"tipo_{key_base}"
        )
    
    with col2:
        mes_actual = get_safe_value(row, 'Mes Proyectado')
        mes_index = 0
        if mes_actual in MESES:
            mes_index = MESES.index(mes_actual)
        
        mes_proyectado = st.selectbox(
            "Mes Proyectado:",
            MESES,
            index=mes_index,
            key=f"mes_{key_base}"
        )
    
    with col3:
        freq_actual = get_safe_value(row, 'Frecuencia actualizacion ')
        freq_index = 0
        if freq_actual in FRECUENCIAS:
            freq_index = FRECUENCIAS.index(freq_actual)
        
        frecuencia = st.selectbox(
            "Frecuencia:",
            FRECUENCIAS,
            index=freq_index,
            key=f"freq_{key_base}"
        )
    
    # ==================== ACUERDOS Y COMPROMISOS ====================
    st.markdown("### Acuerdos y Compromisos")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # ACTAS DE INTERÉS
        actas_actual = get_safe_value(row, 'Actas de acercamiento y manifestación de interés')
        actas_index = 0
        if actas_actual in OPCIONES_SI_NO:
            actas_index = OPCIONES_SI_NO.index(actas_actual)
        
        actas_interes = st.selectbox(
            "Actas de interés:",
            OPCIONES_SI_NO,
            index=actas_index,
            key=f"actas_{key_base}"
        )
        
        # ACUERDO DE COMPROMISO
        acuerdo_actual = get_safe_value(row, 'Acuerdo de compromiso')
        acuerdo_index = 0
        if acuerdo_actual in OPCIONES_SI_NO:
            acuerdo_index = OPCIONES_SI_NO.index(acuerdo_actual)
        
        acuerdo_compromiso = st.selectbox(
            "Acuerdo de compromiso:",
            OPCIONES_SI_NO,
            index=acuerdo_index,
            key=f"acuerdo_{key_base}"
        )
    
    with col2:
        suscripcion = mostrar_campo_fecha_con_limpiar(
            "Suscripción acuerdo:",
            get_safe_value(row, 'Suscripción acuerdo de compromiso'),
            f"susc_{key_base}"
        )
        
        entrega_acuerdo = mostrar_campo_fecha_con_limpiar(
            "Entrega acuerdo:",
            get_safe_value(row, 'Entrega acuerdo de compromiso'),
            f"entrega_{key_base}"
        )
    
    # ==================== GESTIÓN DE INFORMACIÓN ====================
    st.markdown("### Gestión de Información")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # ACCESO A DATOS
        acceso_actual = get_safe_value(row, 'Gestion acceso a los datos y documentos requeridos ')
        acceso_index = 0
        if acceso_actual in OPCIONES_SI_NO:
            acceso_index = OPCIONES_SI_NO.index(acceso_actual)
        
        acceso_datos = st.selectbox(
            "Acceso a datos:",
            OPCIONES_SI_NO,
            index=acceso_index,
            key=f"acceso_{key_base}"
        )
        
        # ANÁLISIS DE INFORMACIÓN
        analisis_info_actual = get_safe_value(row, ' Análisis de información')
        analisis_info_index = 0
        if analisis_info_actual in OPCIONES_SI_NO:
            analisis_info_index = OPCIONES_SI_NO.index(analisis_info_actual)
        
        analisis_info = st.selectbox(
            "Análisis de información:",
            OPCIONES_SI_NO,
            index=analisis_info_index,
            key=f"analisis_info_{key_base}"
        )
    
    with col2:
        # CRONOGRAMA CONCERTADO
        cronograma_actual = get_safe_value(row, 'Cronograma Concertado')
        cronograma_index = 0
        if cronograma_actual in OPCIONES_SI_NO:
            cronograma_index = OPCIONES_SI_NO.index(cronograma_actual)
        
        cronograma = st.selectbox(
            "Cronograma Concertado:",
            OPCIONES_SI_NO,
            index=cronograma_index,
            key=f"cronograma_{key_base}"
        )
        
        fecha_entrega = mostrar_campo_fecha_con_limpiar(
            "Fecha entrega información:",
            get_safe_value(row, 'Fecha de entrega de información'),
            f"entrega_info_{key_base}"
        )
    
    # ==================== CRONOGRAMA Y FECHAS ====================
    st.markdown("### Cronograma y Fechas")
    
    col1, col2 = st.columns(2)
    
    with col1:
        analisis_programada = mostrar_campo_fecha_con_limpiar(
            "Análisis programada:",
            get_safe_value(row, 'Análisis y cronograma (fecha programada)'),
            f"analisis_prog_{key_base}"
        )
        
        analisis_real = mostrar_campo_fecha_con_limpiar(
            "Análisis real:",
            get_safe_value(row, 'Análisis y cronograma'),
            f"analisis_real_{key_base}"
        )
    
    with col2:
        # SEGUIMIENTO
        seguimiento = st.text_area(
            "Seguimiento a los acuerdos:",
            value=get_safe_value(row, 'Seguimiento a los acuerdos'),
            height=100,
            key=f"seguimiento_{key_base}"
        )
    
    # ==================== ESTÁNDARES (TODOS LOS CAMPOS) ====================
    st.markdown("### Estándares")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # REGISTRO
        registro_actual = get_safe_value(row, 'Registro (completo)')
        registro_index = 0
        if registro_actual in ESTADOS_ESTANDARES:
            registro_index = ESTADOS_ESTANDARES.index(registro_actual)
        
        registro = st.selectbox(
            "Registro:",
            ESTADOS_ESTANDARES,
            index=registro_index,
            key=f"registro_{key_base}"
        )
        
        # ET
        et_actual = get_safe_value(row, 'ET (completo)')
        et_index = 0
        if et_actual in ESTADOS_ESTANDARES:
            et_index = ESTADOS_ESTANDARES.index(et_actual)
        
        et = st.selectbox(
            "ET:",
            ESTADOS_ESTANDARES,
            index=et_index,
            key=f"et_{key_base}"
        )
    
    with col2:
        # CO
        co_actual = get_safe_value(row, 'CO (completo)')
        co_index = 0
        if co_actual in ESTADOS_ESTANDARES:
            co_index = ESTADOS_ESTANDARES.index(co_actual)
        
        co = st.selectbox(
            "CO:",
            ESTADOS_ESTANDARES,
            index=co_index,
            key=f"co_{key_base}"
        )
        
        # DD
        dd_actual = get_safe_value(row, 'DD (completo)')
        dd_index = 0
        if dd_actual in ESTADOS_ESTANDARES:
            dd_index = ESTADOS_ESTANDARES.index(dd_actual)
        
        dd = st.selectbox(
            "DD:",
            ESTADOS_ESTANDARES,
            index=dd_index,
            key=f"dd_{key_base}"
        )
    
    with col3:
        # REC
        rec_actual = get_safe_value(row, 'REC (completo)')
        rec_index = 0
        if rec_actual in ESTADOS_ESTANDARES:
            rec_index = ESTADOS_ESTANDARES.index(rec_actual)
        
        rec = st.selectbox(
            "REC:",
            ESTADOS_ESTANDARES,
            index=rec_index,
            key=f"rec_{key_base}"
        )
        
        # SERVICIO
        servicio_actual = get_safe_value(row, 'SERVICIO (completo)')
        servicio_index = 0
        if servicio_actual in ESTADOS_ESTANDARES:
            servicio_index = ESTADOS_ESTANDARES.index(servicio_actual)
        
        servicio = st.selectbox(
            "SERVICIO:",
            ESTADOS_ESTANDARES,
            index=servicio_index,
            key=f"servicio_{key_base}"
        )
    
    # FECHAS DE ESTÁNDARES
    col1, col2 = st.columns(2)
    
    with col1:
        estandares_programada = mostrar_campo_fecha_con_limpiar(
            "Estándares programada:",
            get_safe_value(row, 'Estándares (fecha programada)'),
            f"est_prog_{key_base}"
        )
    
    with col2:
        estandares_real = mostrar_campo_fecha_con_limpiar(
            "Estándares real:",
            get_safe_value(row, 'Estándares'),
            f"est_real_{key_base}"
        )
    
    # ==================== VERIFICACIONES ====================
    st.markdown("### Verificaciones")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # ORIENTACIÓN TÉCNICA
        orientacion_actual = get_safe_value(row, 'Resultados de orientación técnica')
        orientacion_index = 0
        if orientacion_actual in OPCIONES_SI_NO:
            orientacion_index = OPCIONES_SI_NO.index(orientacion_actual)
        
        orientacion = st.selectbox(
            "Orientación técnica:",
            OPCIONES_SI_NO,
            index=orientacion_index,
            key=f"orientacion_{key_base}"
        )
        
        # VERIFICACIÓN WEB
        verif_web_actual = get_safe_value(row, 'Verificación del servicio web geográfico')
        verif_web_index = 0
        if verif_web_actual in OPCIONES_SI_NO:
            verif_web_index = OPCIONES_SI_NO.index(verif_web_actual)
        
        verificacion_web = st.selectbox(
            "Verificación servicio web:",
            OPCIONES_SI_NO,
            index=verif_web_index,
            key=f"verif_web_{key_base}"
        )
        
        # VERIFICAR APROBAR
        aprobar_actual = get_safe_value(row, 'Verificar Aprobar Resultados')
        aprobar_index = 0
        if aprobar_actual in OPCIONES_SI_NO:
            aprobar_index = OPCIONES_SI_NO.index(aprobar_actual)
        
        verificar_aprobar = st.selectbox(
            "Verificar Aprobar:",
            OPCIONES_SI_NO,
            index=aprobar_index,
            key=f"aprobar_{key_base}"
        )
    
    with col2:
        # REVISAR Y VALIDAR
        revisar_actual = get_safe_value(row, 'Revisar y validar los datos cargados en la base de datos')
        revisar_index = 0
        if revisar_actual in OPCIONES_SI_NO:
            revisar_index = OPCIONES_SI_NO.index(revisar_actual)
        
        revisar_validar = st.selectbox(
            "Revisar y validar:",
            OPCIONES_SI_NO,
            index=revisar_index,
            key=f"revisar_{key_base}"
        )
        
        # APROBACIÓN RESULTADOS
        aprobacion_actual = get_safe_value(row, 'Aprobación resultados obtenidos en la orientación')
        aprobacion_index = 0
        if aprobacion_actual in OPCIONES_SI_NO:
            aprobacion_index = OPCIONES_SI_NO.index(aprobacion_actual)
        
        aprobacion = st.selectbox(
            "Aprobación resultados:",
            OPCIONES_SI_NO,
            index=aprobacion_index,
            key=f"aprobacion_{key_base}"
        )
    
    # ==================== PUBLICACIÓN ====================
    st.markdown("### Publicación")
    
    col1, col2 = st.columns(2)
    
    with col1:
        pub_programada = mostrar_campo_fecha_con_limpiar(
            "Publicación programada:",
            get_safe_value(row, 'Fecha de publicación programada'),
            f"pub_prog_{key_base}"
        )
        
        publicacion = mostrar_campo_fecha_con_limpiar(
            "Publicación real:",
            get_safe_value(row, 'Publicación'),
            f"pub_real_{key_base}"
        )
    
    with col2:
        # DISPONER DATOS
        disponer_actual = get_safe_value(row, 'Disponer datos temáticos')
        disponer_index = 0
        if disponer_actual in OPCIONES_SI_NO:
            disponer_index = OPCIONES_SI_NO.index(disponer_actual)
        
        disponer_datos = st.selectbox(
            "Disponer datos temáticos:",
            OPCIONES_SI_NO,
            index=disponer_index,
            key=f"disponer_{key_base}"
        )
        
        # CATÁLOGO
        catalogo_actual = get_safe_value(row, 'Catálogo de recursos geográficos')
        catalogo_index = 0
        if catalogo_actual in OPCIONES_SI_NO:
            catalogo_index = OPCIONES_SI_NO.index(catalogo_actual)
        
        catalogo = st.selectbox(
            "Catálogo recursos:",
            OPCIONES_SI_NO,
            index=catalogo_index,
            key=f"catalogo_{key_base}"
        )
    
    # ==================== CIERRE ====================
    st.markdown("### Cierre")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # OFICIOS DE CIERRE
        oficios_actual = get_safe_value(row, 'Oficios de cierre')
        oficios_index = 0
        if oficios_actual in OPCIONES_SI_NO:
            oficios_index = OPCIONES_SI_NO.index(oficios_actual)
        
        oficios_cierre = st.selectbox(
            "Oficios de cierre:",
            OPCIONES_SI_NO,
            index=oficios_index,
            key=f"oficios_{key_base}"
        )
    
    with col2:
        fecha_oficio = mostrar_campo_fecha_con_limpiar(
            "Fecha oficio cierre:",
            get_safe_value(row, 'Fecha de oficio de cierre'),
            f"oficio_{key_base}"
        )
    
    with col3:
        # ESTADO
        estado_actual = get_safe_value(row, 'Estado')
        estado_index = 0
        if estado_actual in ESTADOS_REGISTRO:
            estado_index = ESTADOS_REGISTRO.index(estado_actual)
        
        estado = st.selectbox(
            "Estado:",
            ESTADOS_REGISTRO,
            index=estado_index,
            key=f"estado_{key_base}"
        )
    
    # ==================== PLAZOS (SOLO LECTURA) ====================
    st.markdown("### Plazos Calculados")
    
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
    
    # ==================== OBSERVACIONES Y AVANCE ====================
    st.markdown("### Observaciones")
    
    observacion = st.text_area(
        "Observaciones:",
        value=get_safe_value(row, 'Observación'),
        height=100,
        key=f"obs_{key_base}"
    )
    
    # AVANCE CALCULADO
    avance_actual = calcular_avance(row)
    st.text_input(
        "Porcentaje de Avance:",
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
        'Estándares (fecha programada)': fecha_a_string(estandares_programada) if estandares_programada else "",
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
            return True, "Datos guardados"
        else:
            return False, "Error al escribir en Google Sheets"
            
    except Exception as e:
        return False, f"Error: {str(e)}"

def mostrar_edicion_registros(registros_df):
    """Editor principal - TODAS LAS SECCIONES - VERSIÓN LIMPIA"""
    st.subheader("Editor de Registros")
    
    # Métricas básicas
    col1, col2 = st.columns([2, 1])
    with col1:
        total = len(registros_df) if not registros_df.empty else 0
        st.metric("Total Registros", total)
    
    with col2:
        if 'ultimo_guardado' in st.session_state:
            st.info(f"Último guardado: {st.session_state.ultimo_guardado}")
    
    if registros_df.empty:
        st.warning("No hay datos disponibles")
        return registros_df
    
    # Pestañas principales
    tab1, tab2 = st.tabs(["Editar Existente", "Crear Nuevo"])
    
    with tab1:
        st.markdown("### Editar Registro Existente")
        
        # BÚSQUEDA Y SELECCIÓN
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
            
            # FORMULARIO COMPLETO DE EDICIÓN CON TODAS LAS SECCIONES
            with st.form("form_editar_completo"):
                st.markdown("### Información Completa del Registro")
                
                # USAR EL FORMULARIO COMPLETO CON TODAS LAS SECCIONES
                valores_editados = mostrar_formulario_completo_todas_secciones(
                    row_seleccionada, indice_real, es_nuevo=False, df=registros_df
                )
                
                # SUBMIT DEL FORMULARIO
                if st.form_submit_button("Guardar Cambios", type="primary"):
                    if not valores_editados['Funcionario'].strip():
                        st.error("Debe seleccionar un funcionario")
                    elif not valores_editados['Entidad'].strip():
                        st.error("Debe seleccionar una entidad")
                    else:
                        try:
                            # Actualizar registro
                            for campo, valor in valores_editados.items():
                                if campo in registros_df.columns:
                                    registros_df.iloc[indice_real, registros_df.columns.get_loc(campo)] = valor
                            
                            # Calcular avance
                            nuevo_avance = calcular_avance(registros_df.iloc[indice_real])
                            if 'Porcentaje Avance' in registros_df.columns:
                                registros_df.iloc[indice_real, registros_df.columns.get_loc('Porcentaje Avance')] = nuevo_avance
                            
                            # Guardar
                            exito, mensaje = guardar_en_sheets(registros_df)
                            
                            if exito:
                                st.success(f"Registro actualizado. Avance: {nuevo_avance}%")
                                st.session_state['registros_df'] = registros_df
                                st.session_state.ultimo_guardado = datetime.now().strftime("%H:%M:%S")
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error(f"Error: {mensaje}")
                        except Exception as e:
                            st.error(f"Error guardando: {e}")
    
    with tab2:
        st.markdown("### Crear Nuevo Registro")
        
        # CÓDIGO AUTOMÁTICO
        nuevo_codigo = generar_codigo(registros_df)
        st.info(f"Código automático: {nuevo_codigo}")
        
        # FORMULARIO COMPLETO PARA CREAR CON TODAS LAS SECCIONES
        with st.form("form_crear_completo"):
            st.markdown("### Información del Nuevo Registro")
            
            # Crear row vacío para el nuevo registro
            row_nuevo = pd.Series({col: '' for col in registros_df.columns})
            row_nuevo['Cod'] = nuevo_codigo
            
            # USAR EL FORMULARIO COMPLETO CON TODAS LAS SECCIONES
            valores_nuevo = mostrar_formulario_completo_todas_secciones(
                row_nuevo, "nuevo", es_nuevo=True, df=registros_df
            )
            
            # SUBMIT
            if st.form_submit_button("Crear Registro", type="primary"):
                if not valores_nuevo['Funcionario'].strip():
                    st.error("Debe seleccionar un funcionario")
                elif not valores_nuevo['Entidad'].strip():
                    st.error("Debe seleccionar una entidad")
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
                            st.success(f"Registro {nuevo_codigo} creado. Avance: {avance}%")
                            st.session_state['registros_df'] = registros_df
                            st.session_state.ultimo_guardado = datetime.now().strftime("%H:%M:%S")
                            st.balloons()
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error(f"Error: {mensaje}")
                    except Exception as e:
                        st.error(f"Error creando: {e}")
    
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
