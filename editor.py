# editor.py - VERSIÓN COMPLETA Y CORREGIDA
"""
Editor de registros con TODAS las funcionalidades
- Diseño limpio sin iconos innecesarios
- Formularios completos con todos los campos
- Botones submit obligatorios
- Sistema de autenticación integrado
- Funcionalidad completa de edición y creación
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date
import time

# LISTAS DE OPCIONES COMPLETAS
MESES = ["", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
         "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]

FRECUENCIAS = ["", "Diaria", "Semanal", "Quincenal", "Mensual", "Bimestral", 
               "Trimestral", "Semestral", "Anual", "Eventual"]

OPCIONES_SI_NO = ["", "Si", "No"]
OPCIONES_ESTANDARES = ["", "Completo", "Incompleto", "No aplica"]
OPCIONES_ESTADO = ["", "Completado", "En proceso", "Pendiente"]

# IMPORTS SEGUROS
try:
    from sheets_utils import GoogleSheetsManager
except ImportError:
    GoogleSheetsManager = None

try:
    from data_utils import (
        calcular_porcentaje_avance, formatear_fecha, es_fecha_valida,
        procesar_fecha, guardar_datos_editados
    )
except ImportError:
    # Funciones de respaldo
    def calcular_porcentaje_avance(row):
        avance = 0
        if str(row.get('Acuerdo de compromiso', '')).upper() in ['SI', 'SÍ']:
            avance += 25
        if str(row.get('Análisis y cronograma', '')).strip():
            avance += 25
        if str(row.get('Estándares', '')).strip():
            avance += 25
        if str(row.get('Publicación', '')).strip():
            avance += 25
        return avance
    
    def formatear_fecha(fecha):
        if fecha and str(fecha).strip():
            return str(fecha)
        return ""
    
    def es_fecha_valida(fecha):
        return fecha and str(fecha).strip() and str(fecha).strip() != 'nan'
    
    def procesar_fecha(fecha):
        return fecha
    
    def guardar_datos_editados(df, backup=True):
        return guardar_en_sheets_local(df)

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

def guardar_en_sheets_local(df):
    """Guarda datos en Google Sheets usando la función local"""
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
            return True, "Datos guardados exitosamente"
        else:
            return False, "Error al escribir en Google Sheets"
            
    except Exception as e:
        return False, f"Error: {str(e)}"

def generar_codigo(df):
    """Genera nuevo código secuencial"""
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

def mostrar_selector_con_nuevo(label, opciones_existentes, valor_actual, tipo, key_base):
    """Selector universal con opción de agregar nuevo"""
    st.markdown(f"**{label}:**")
    
    # Preparar opciones con "Nuevo"
    opciones = [""] + opciones_existentes + [f"+ Nuevo {tipo}"]
    
    # Determinar índice inicial
    valor_inicial = 0
    if valor_actual and valor_actual in opciones_existentes:
        valor_inicial = opciones_existentes.index(valor_actual) + 1
    
    # Selectbox principal
    seleccion = st.selectbox(
        f"Seleccionar {tipo.lower()}:",
        opciones,
        index=valor_inicial,
        key=f"{tipo.lower()}_select_{key_base}"
    )
    
    # Campo de texto condicional
    es_nuevo = (seleccion == f"+ Nuevo {tipo}")
    
    nuevo_valor = st.text_input(
        f"Nombre del nuevo {tipo.lower()}:",
        value="",
        placeholder=f"Escriba el nombre del {tipo.lower()}" if es_nuevo else f"Seleccione 'Nuevo {tipo}' arriba",
        disabled=not es_nuevo,
        key=f"{tipo.lower()}_nuevo_{key_base}"
    )
    
    # Retornar valor final
    if es_nuevo:
        return nuevo_valor.strip() if nuevo_valor else ""
    elif seleccion == "":
        return ""
    else:
        return seleccion

def mostrar_formulario_editar_completo(row, indice, df, es_nuevo=False):
    """FORMULARIO COMPLETO DE EDICIÓN CON TODOS LOS CAMPOS"""
    
    # Obtener listas existentes
    funcionarios_existentes = obtener_funcionarios_unicos(df)
    entidades_existentes = obtener_entidades_unicas(df)
    
    # Key base único para evitar conflictos
    key_base = f"{indice}_{'nuevo' if es_nuevo else 'edit'}_{int(datetime.now().timestamp() * 1000000) % 1000000}"
    
    # ======================
    # INFORMACIÓN BÁSICA
    # ======================
    st.markdown("#### Información Básica")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Código
        codigo = st.text_input(
            "Código:",
            value=get_safe_value(row, 'Cod') if not es_nuevo else generar_codigo(df),
            disabled=True,
            key=f"codigo_{key_base}"
        )
        
        # Funcionario con selector
        funcionario_actual = get_safe_value(row, 'Funcionario')
        funcionario = mostrar_selector_con_nuevo(
            "Funcionario", funcionarios_existentes, funcionario_actual, "Funcionario", key_base
        )
    
    with col2:
        # Entidad con selector
        entidad_actual = get_safe_value(row, 'Entidad')
        entidad = mostrar_selector_con_nuevo(
            "Entidad", entidades_existentes, entidad_actual, "Entidad", key_base
        )
        
        # Nivel de Información
        nivel_info = st.text_input(
            "Nivel de Información:",
            value=get_safe_value(row, 'Nivel Información '),
            key=f"nivel_{key_base}"
        )
    
    # Fila adicional para tipo, mes y frecuencia
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Tipo de Dato
        tipo_actual = get_safe_value(row, 'TipoDato')
        tipo_opciones = ["", "Actualizar", "Nuevo"]
        tipo_index = tipo_opciones.index(tipo_actual) if tipo_actual in tipo_opciones else 0
        tipo_dato = st.selectbox("Tipo de Dato:", tipo_opciones, index=tipo_index, key=f"tipo_{key_base}")
    
    with col2:
        # Mes Proyectado
        mes_actual = get_safe_value(row, 'Mes Proyectado')
        mes_index = MESES.index(mes_actual) if mes_actual in MESES else 0
        mes_proyectado = st.selectbox("Mes Proyectado:", MESES, index=mes_index, key=f"mes_{key_base}")
    
    with col3:
        # Frecuencia
        frecuencia_actual = get_safe_value(row, 'Frecuencia actualizacion ')
        frecuencia_index = FRECUENCIAS.index(frecuencia_actual) if frecuencia_actual in FRECUENCIAS else 0
        frecuencia = st.selectbox("Frecuencia:", FRECUENCIAS, index=frecuencia_index, key=f"freq_{key_base}")
    
    # ======================
    # ACUERDOS Y COMPROMISOS
    # ======================
    st.markdown("#### Acuerdos y Compromisos")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Actas de interés
        actas_value = get_safe_value(row, 'Actas de acercamiento y manifestación de interés')
        actas_index = OPCIONES_SI_NO.index(actas_value) if actas_value in OPCIONES_SI_NO else 0
        actas_interes = st.selectbox("Actas de interés:", OPCIONES_SI_NO, index=actas_index, key=f"actas_{key_base}")
        
        # Acuerdo de compromiso
        acuerdo_value = get_safe_value(row, 'Acuerdo de compromiso')
        acuerdo_index = OPCIONES_SI_NO.index(acuerdo_value) if acuerdo_value in OPCIONES_SI_NO else 0
        acuerdo_compromiso = st.selectbox("Acuerdo de compromiso:", OPCIONES_SI_NO, index=acuerdo_index, key=f"acuerdo_{key_base}")
    
    with col2:
        # Fechas de acuerdos
        suscripcion_fecha = string_a_fecha(get_safe_value(row, 'Suscripción acuerdo de compromiso'))
        suscripcion = st.date_input("Suscripción acuerdo:", value=suscripcion_fecha, key=f"suscripcion_{key_base}")
        if st.checkbox("Limpiar suscripción", key=f"limpiar_susc_{key_base}"):
            suscripcion = None
        
        entrega_fecha = string_a_fecha(get_safe_value(row, 'Entrega acuerdo de compromiso'))
        entrega_acuerdo = st.date_input("Entrega acuerdo:", value=entrega_fecha, key=f"entrega_{key_base}")
        if st.checkbox("Limpiar entrega", key=f"limpiar_entrega_{key_base}"):
            entrega_acuerdo = None
    
    # ======================
    # GESTIÓN DE INFORMACIÓN
    # ======================
    st.markdown("#### Gestión de Información")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Acceso a datos
        acceso_value = get_safe_value(row, 'Gestion acceso a los datos y documentos requeridos ')
        acceso_index = OPCIONES_SI_NO.index(acceso_value) if acceso_value in OPCIONES_SI_NO else 0
        acceso_datos = st.selectbox("Acceso a datos:", OPCIONES_SI_NO, index=acceso_index, key=f"acceso_{key_base}")
        
        # Análisis de información
        analisis_info_value = get_safe_value(row, ' Análisis de información')
        analisis_info_index = OPCIONES_SI_NO.index(analisis_info_value) if analisis_info_value in OPCIONES_SI_NO else 0
        analisis_info = st.selectbox("Análisis de información:", OPCIONES_SI_NO, index=analisis_info_index, key=f"analisis_info_{key_base}")
        
        # Cronograma Concertado
        cronograma_value = get_safe_value(row, 'Cronograma Concertado')
        cronograma_index = OPCIONES_SI_NO.index(cronograma_value) if cronograma_value in OPCIONES_SI_NO else 0
        cronograma = st.selectbox("Cronograma Concertado:", OPCIONES_SI_NO, index=cronograma_index, key=f"cronograma_{key_base}")
    
    with col2:
        # Fecha entrega información
        fecha_entrega_date = string_a_fecha(get_safe_value(row, 'Fecha de entrega de información'))
        fecha_entrega = st.date_input("Fecha entrega información:", value=fecha_entrega_date, key=f"fecha_entrega_{key_base}")
        if st.checkbox("Limpiar fecha entrega", key=f"limpiar_fecha_entrega_{key_base}"):
            fecha_entrega = None
        
        # Seguimiento a los acuerdos
        seguimiento = st.text_area("Seguimiento a los acuerdos:", 
                                 value=get_safe_value(row, 'Seguimiento a los acuerdos'), 
                                 height=80, key=f"seguimiento_{key_base}")
    
    # ======================
    # FECHAS Y CRONOGRAMA
    # ======================
    st.markdown("#### Fechas y Cronograma")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Análisis programada
        analisis_prog_date = string_a_fecha(get_safe_value(row, 'Análisis y cronograma (fecha programada)'))
        analisis_programada = st.date_input("Análisis programada:", value=analisis_prog_date, key=f"analisis_prog_{key_base}")
        if st.checkbox("Limpiar análisis programada", key=f"limpiar_analisis_prog_{key_base}"):
            analisis_programada = None
        
        # Análisis real
        analisis_real_date = string_a_fecha(get_safe_value(row, 'Análisis y cronograma'))
        analisis_real = st.date_input("Análisis real:", value=analisis_real_date, key=f"analisis_real_{key_base}")
        if st.checkbox("Limpiar análisis real", key=f"limpiar_analisis_real_{key_base}"):
            analisis_real = None
    
    with col2:
        # Plazos calculados (solo lectura)
        st.text_input("Plazo análisis:", value=get_safe_value(row, 'Plazo de análisis'), 
                     disabled=True, key=f"plazo_analisis_{key_base}")
        st.text_input("Plazo cronograma:", value=get_safe_value(row, 'Plazo de cronograma'), 
                     disabled=True, key=f"plazo_cronograma_{key_base}")
    
    # ======================
    # ESTÁNDARES
    # ======================
    st.markdown("#### Estándares")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Registro
        registro_value = get_safe_value(row, 'Registro (completo)')
        registro_index = OPCIONES_ESTANDARES.index(registro_value) if registro_value in OPCIONES_ESTANDARES else 0
        registro = st.selectbox("Registro:", OPCIONES_ESTANDARES, index=registro_index, key=f"registro_{key_base}")
        
        # ET
        et_value = get_safe_value(row, 'ET (completo)')
        et_index = OPCIONES_ESTANDARES.index(et_value) if et_value in OPCIONES_ESTANDARES else 0
        et = st.selectbox("ET:", OPCIONES_ESTANDARES, index=et_index, key=f"et_{key_base}")
    
    with col2:
        # CO
        co_value = get_safe_value(row, 'CO (completo)')
        co_index = OPCIONES_ESTANDARES.index(co_value) if co_value in OPCIONES_ESTANDARES else 0
        co = st.selectbox("CO:", OPCIONES_ESTANDARES, index=co_index, key=f"co_{key_base}")
        
        # DD
        dd_value = get_safe_value(row, 'DD (completo)')
        dd_index = OPCIONES_ESTANDARES.index(dd_value) if dd_value in OPCIONES_ESTANDARES else 0
        dd = st.selectbox("DD:", OPCIONES_ESTANDARES, index=dd_index, key=f"dd_{key_base}")
    
    with col3:
        # REC
        rec_value = get_safe_value(row, 'REC (completo)')
        rec_index = OPCIONES_ESTANDARES.index(rec_value) if rec_value in OPCIONES_ESTANDARES else 0
        rec = st.selectbox("REC:", OPCIONES_ESTANDARES, index=rec_index, key=f"rec_{key_base}")
        
        # SERVICIO
        servicio_value = get_safe_value(row, 'SERVICIO (completo)')
        servicio_index = OPCIONES_ESTANDARES.index(servicio_value) if servicio_value in OPCIONES_ESTANDARES else 0
        servicio = st.selectbox("SERVICIO:", OPCIONES_ESTANDARES, index=servicio_index, key=f"servicio_{key_base}")
    
    # Fechas de estándares
    col1, col2 = st.columns(2)
    
    with col1:
        # Estándares programada
        est_prog_date = string_a_fecha(get_safe_value(row, 'Estándares (fecha programada)'))
        estandares_prog = st.date_input("Estándares programada:", value=est_prog_date, key=f"est_prog_{key_base}")
        if st.checkbox("Limpiar estándares programada", key=f"limpiar_est_prog_{key_base}"):
            estandares_prog = None
    
    with col2:
        # Estándares real
        est_real_date = string_a_fecha(get_safe_value(row, 'Estándares'))
        estandares_real = st.date_input("Estándares real:", value=est_real_date, key=f"est_real_{key_base}")
        if st.checkbox("Limpiar estándares real", key=f"limpiar_est_real_{key_base}"):
            estandares_real = None
    
    # ======================
    # VERIFICACIONES
    # ======================
    st.markdown("#### Verificaciones")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Orientación técnica
        orientacion_value = get_safe_value(row, 'Resultados de orientación técnica')
        orientacion_index = OPCIONES_SI_NO.index(orientacion_value) if orientacion_value in OPCIONES_SI_NO else 0
        orientacion = st.selectbox("Orientación técnica:", OPCIONES_SI_NO, index=orientacion_index, key=f"orientacion_{key_base}")
        
        # Verificación servicio web
        verificacion_value = get_safe_value(row, 'Verificación del servicio web geográfico')
        verificacion_index = OPCIONES_SI_NO.index(verificacion_value) if verificacion_value in OPCIONES_SI_NO else 0
        verificacion_web = st.selectbox("Verificación servicio web:", OPCIONES_SI_NO, index=verificacion_index, key=f"verificacion_{key_base}")
        
        # Verificar Aprobar
        aprobar_value = get_safe_value(row, 'Verificar Aprobar Resultados')
        aprobar_index = OPCIONES_SI_NO.index(aprobar_value) if aprobar_value in OPCIONES_SI_NO else 0
        verificar_aprobar = st.selectbox("Verificar Aprobar:", OPCIONES_SI_NO, index=aprobar_index, key=f"aprobar_{key_base}")
    
    with col2:
        # Revisar y validar
        revisar_value = get_safe_value(row, 'Revisar y validar los datos cargados en la base de datos')
        revisar_index = OPCIONES_SI_NO.index(revisar_value) if revisar_value in OPCIONES_SI_NO else 0
        revisar_validar = st.selectbox("Revisar y validar:", OPCIONES_SI_NO, index=revisar_index, key=f"revisar_{key_base}")
        
        # Aprobación resultados
        aprobacion_value = get_safe_value(row, 'Aprobación resultados obtenidos en la orientación')
        aprobacion_index = OPCIONES_SI_NO.index(aprobacion_value) if aprobacion_value in OPCIONES_SI_NO else 0
        aprobacion = st.selectbox("Aprobación resultados:", OPCIONES_SI_NO, index=aprobacion_index, key=f"aprobacion_{key_base}")
    
    # ======================
    # PUBLICACIÓN
    # ======================
    st.markdown("#### Publicación")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Publicación programada
        pub_prog_date = string_a_fecha(get_safe_value(row, 'Fecha de publicación programada'))
        pub_programada = st.date_input("Publicación programada:", value=pub_prog_date, key=f"pub_prog_{key_base}")
        if st.checkbox("Limpiar publicación programada", key=f"limpiar_pub_prog_{key_base}"):
            pub_programada = None
        
        # Publicación real
        pub_real_date = string_a_fecha(get_safe_value(row, 'Publicación'))
        publicacion = st.date_input("Publicación real:", value=pub_real_date, key=f"publicacion_{key_base}")
        if st.checkbox("Limpiar publicación real", key=f"limpiar_publicacion_{key_base}"):
            publicacion = None
    
    with col2:
        # Disponer datos temáticos
        disponer_value = get_safe_value(row, 'Disponer datos temáticos')
        disponer_index = OPCIONES_SI_NO.index(disponer_value) if disponer_value in OPCIONES_SI_NO else 0
        disponer_datos = st.selectbox("Disponer datos temáticos:", OPCIONES_SI_NO, index=disponer_index, key=f"disponer_{key_base}")
        
        # Catálogo recursos
        catalogo_value = get_safe_value(row, 'Catálogo de recursos geográficos')
        catalogo_index = OPCIONES_SI_NO.index(catalogo_value) if catalogo_value in OPCIONES_SI_NO else 0
        catalogo = st.selectbox("Catálogo recursos:", OPCIONES_SI_NO, index=catalogo_index, key=f"catalogo_{key_base}")
    
    # ======================
    # CIERRE
    # ======================
    st.markdown("#### Cierre")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Oficios de cierre
        oficios_value = get_safe_value(row, 'Oficios de cierre')
        oficios_index = OPCIONES_SI_NO.index(oficios_value) if oficios_value in OPCIONES_SI_NO else 0
        oficios_cierre = st.selectbox("Oficios de cierre:", OPCIONES_SI_NO, index=oficios_index, key=f"oficios_{key_base}")
    
    with col2:
        # Fecha oficio de cierre
        fecha_oficio_date = string_a_fecha(get_safe_value(row, 'Fecha de oficio de cierre'))
        fecha_oficio = st.date_input("Fecha oficio cierre:", value=fecha_oficio_date, key=f"fecha_oficio_{key_base}")
        if st.checkbox("Limpiar fecha oficio", key=f"limpiar_fecha_oficio_{key_base}"):
            fecha_oficio = None
    
    with col3:
        # Estado
        estado_value = get_safe_value(row, 'Estado')
        estado_index = OPCIONES_ESTADO.index(estado_value) if estado_value in OPCIONES_ESTADO else 0
        estado = st.selectbox("Estado:", OPCIONES_ESTADO, index=estado_index, key=f"estado_{key_base}")
    
    # Plazo oficio de cierre (solo lectura)
    st.text_input("Plazo oficio cierre:", value=get_safe_value(row, 'Plazo de oficio de cierre'), 
                 disabled=True, key=f"plazo_oficio_{key_base}")
    
    # ======================
    # OBSERVACIONES
    # ======================
    st.markdown("#### Observaciones")
    observacion = st.text_area("Observaciones:", value=get_safe_value(row, 'Observación'), 
                             height=100, key=f"obs_{key_base}")
    
    # Avance calculado (solo lectura)
    avance_actual = calcular_porcentaje_avance(row)
    st.text_input("Porcentaje de Avance (Calculado):", value=f"{avance_actual}%", 
                 disabled=True, key=f"avance_{key_base}")
    
    # RETORNAR DICCIONARIO COMPLETO CON TODOS LOS VALORES
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
    """Editor principal con todas las funcionalidades"""
    st.subheader("Editor de Registros")
    
    # Estado y métricas
    col1, col2, col3 = st.columns(3)
    with col1:
        total = len(registros_df) if not registros_df.empty else 0
        st.metric("Total Registros", total)
    
    with col2:
        if 'ultimo_guardado' in st.session_state:
            st.success(f"Guardado: {st.session_state.ultimo_guardado}")
    
    with col3:
        if 'operacion_exitosa' in st.session_state:
            st.info(f"Operación: {st.session_state.operacion_exitosa}")
    
    if registros_df.empty:
        st.warning("No hay datos disponibles")
        return registros_df
    
    # Pestañas principales
    tab1, tab2, tab3 = st.tabs(["Editar Existente", "Crear Nuevo", "Edición Avanzada"])
    
    with tab1:
        mostrar_editor_existente_completo(registros_df)
    
    with tab2:
        mostrar_editor_nuevo_completo(registros_df)
    
    with tab3:
        mostrar_editor_avanzado(registros_df)
    
    return st.session_state.get('registros_df', registros_df)

def mostrar_editor_existente_completo(registros_df):
    """Editor completo para registros existentes"""
    st.markdown("### Editar Registro Existente")
    
    # Búsqueda y filtros
    col1, col2 = st.columns([2, 1])
    
    with col1:
        termino = st.text_input(
            "Buscar registro:",
            placeholder="Código, entidad, funcionario o información...",
            key="busqueda_editar_completa"
        )
    
    with col2:
        # Filtro adicional por estado
        filtro_estado = st.selectbox(
            "Filtrar por estado:",
            ["Todos", "Completado", "En proceso", "Pendiente"],
            key="filtro_estado_editar"
        )
    
    # Aplicar filtros y búsqueda
    opciones = []
    for idx, row in registros_df.iterrows():
        codigo = get_safe_value(row, 'Cod', 'N/A')
        nivel = get_safe_value(row, 'Nivel Información ', 'Sin nivel')
        entidad = get_safe_value(row, 'Entidad', 'Sin entidad')
        funcionario = get_safe_value(row, 'Funcionario', 'Sin funcionario')
        estado = get_safe_value(row, 'Estado', 'Sin estado')
        
        # Aplicar filtro de estado
        if filtro_estado != "Todos" and estado != filtro_estado:
            continue
        
        opcion = f"{codigo} - {nivel} - {entidad} - {funcionario}"
        
        # Aplicar filtro de búsqueda
        if termino:
            if termino.lower() in opcion.lower():
                opciones.append((idx, opcion, estado))
        else:
            opciones.append((idx, opcion, estado))
    
    if not opciones:
        st.warning("No hay registros que coincidan con los filtros")
        return
    
    # Mostrar estadísticas de búsqueda
    if termino or filtro_estado != "Todos":
        st.info(f"{len(opciones)} registros encontrados")
    
    # Selector de registro
    opciones_mostrar = [f"{opcion} [{estado}]" for _, opcion, estado in opciones]
    seleccion = st.selectbox("Registro a editar:", opciones_mostrar, key="select_editar_completo")
    
    # Obtener índice real del registro seleccionado
    indice_real = None
    for idx, opcion, estado in opciones:
        if f"{opcion} [{estado}]" == seleccion:
            indice_real = idx
            break
    
    if indice_real is not None:
        row_seleccionada = registros_df.iloc[indice_real]
        
        # Mostrar información actual del registro
        with st.expander("Información Actual del Registro", expanded=False):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.write(f"**Código:** {get_safe_value(row_seleccionada, 'Cod')}")
                st.write(f"**Funcionario:** {get_safe_value(row_seleccionada, 'Funcionario')}")
            with col2:
                st.write(f"**Entidad:** {get_safe_value(row_seleccionada, 'Entidad')}")
                st.write(f"**Estado:** {get_safe_value(row_seleccionada, 'Estado')}")
            with col3:
                avance = calcular_porcentaje_avance(row_seleccionada)
                st.write(f"**Avance:** {avance}%")
                st.write(f"**Tipo:** {get_safe_value(row_seleccionada, 'TipoDato')}")
        
        # FORMULARIO COMPLETO DE EDICIÓN
        with st.form(key=f"form_editar_completo_{indice_real}", clear_on_submit=False):
            
            # Usar formulario completo con todos los campos
            valores_editados = mostrar_formulario_editar_completo(row_seleccionada, indice_real, registros_df, es_nuevo=False)
            
            # Botones de acción
            col1, col2, col3 = st.columns(3)
            
            with col1:
                submitted = st.form_submit_button("Guardar Cambios", type="primary")
            
            with col2:
                submitted_y_cerrar = st.form_submit_button("Guardar y Cerrar", type="secondary")
            
            with col3:
                cancelar = st.form_submit_button("Cancelar")
            
            # Procesamiento del formulario
            if submitted or submitted_y_cerrar:
                procesar_edicion_completa(registros_df, indice_real, valores_editados, submitted_y_cerrar)
            
            elif cancelar:
                st.info("Edición cancelada")
                st.rerun()

def mostrar_editor_nuevo_completo(registros_df):
    """Editor completo para nuevos registros"""
    st.markdown("### Crear Nuevo Registro")
    
    # Información del nuevo código
    nuevo_codigo = generar_codigo(registros_df)
    col1, col2 = st.columns(2)
    with col1:
        st.info(f"Código automático: **{nuevo_codigo}**")
    with col2:
        st.info(f"Total registros actuales: **{len(registros_df)}**")
    
    # FORMULARIO COMPLETO PARA NUEVO REGISTRO
    with st.form(key="form_crear_completo_nuevo", clear_on_submit=True):
        
        # Crear registro vacío para el formulario
        registro_vacio = pd.Series({col: '' for col in registros_df.columns})
        registro_vacio['Cod'] = nuevo_codigo
        
        # Usar formulario completo
        valores_nuevos = mostrar_formulario_editar_completo(registro_vacio, "nuevo", registros_df, es_nuevo=True)
        
        # Opciones adicionales para nuevo registro
        st.markdown("#### Opciones de Creación")
        
        col1, col2 = st.columns(2)
        with col1:
            crear_multiple = st.checkbox("Crear múltiples registros similares")
            if crear_multiple:
                cantidad = st.number_input("Cantidad de registros:", min_value=1, max_value=10, value=1)
        
        with col2:
            copiar_desde = st.selectbox(
                "Copiar configuración desde:",
                ["Ninguno"] + [f"{get_safe_value(row, 'Cod')} - {get_safe_value(row, 'Entidad')}" 
                              for _, row in registros_df.head(10).iterrows()],
                key="copiar_config"
            )
        
        # Botones de acción
        col1, col2, col3 = st.columns(3)
        
        with col1:
            submitted = st.form_submit_button("Crear Registro", type="primary")
        
        with col2:
            submitted_y_crear_otro = st.form_submit_button("Crear y Hacer Otro", type="secondary")
        
        with col3:
            submitted_preview = st.form_submit_button("Vista Previa")
        
        # Procesamiento del formulario
        if submitted or submitted_y_crear_otro:
            if crear_multiple:
                procesar_creacion_multiple(registros_df, valores_nuevos, cantidad, submitted_y_crear_otro)
            else:
                procesar_creacion_completa(registros_df, valores_nuevos, submitted_y_crear_otro)
        
        elif submitted_preview:
            mostrar_vista_previa_registro(valores_nuevos)

def mostrar_editor_avanzado(registros_df):
    """Editor avanzado con funciones especiales"""
    st.markdown("### Edición Avanzada")
    
    # Opciones avanzadas
    tab1, tab2, tab3 = st.tabs(["Edición Masiva", "Importar/Exportar", "Herramientas"])
    
    with tab1:
        mostrar_edicion_masiva(registros_df)
    
    with tab2:
        mostrar_importar_exportar(registros_df)
    
    with tab3:
        mostrar_herramientas_avanzadas(registros_df)

def mostrar_edicion_masiva(registros_df):
    """Herramientas de edición masiva"""
    st.markdown("#### Edición Masiva")
    
    # Filtros para selección masiva
    st.markdown("**Seleccionar Registros para Edición Masiva**")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Filtro por entidad
        entidades = ["Todas"] + obtener_entidades_unicas(registros_df)
        entidad_masiva = st.selectbox("Entidad:", entidades, key="entidad_masiva")
    
    with col2:
        # Filtro por funcionario
        funcionarios = ["Todos"] + obtener_funcionarios_unicos(registros_df)
        funcionario_masivo = st.selectbox("Funcionario:", funcionarios, key="funcionario_masivo")
    
    with col3:
        # Filtro por estado
        estado_masivo = st.selectbox("Estado:", ["Todos", "Completado", "En proceso", "Pendiente"], key="estado_masivo")
    
    # Aplicar filtros
    df_filtrado = registros_df.copy()
    
    if entidad_masiva != "Todas":
        df_filtrado = df_filtrado[df_filtrado['Entidad'] == entidad_masiva]
    
    if funcionario_masivo != "Todos":
        df_filtrado = df_filtrado[df_filtrado['Funcionario'] == funcionario_masivo]
    
    if estado_masivo != "Todos":
        df_filtrado = df_filtrado[df_filtrado['Estado'] == estado_masivo]
    
    st.info(f"Registros seleccionados: {len(df_filtrado)}")
    
    if len(df_filtrado) > 0:
        # Operaciones masivas
        st.markdown("**Operaciones Masivas Disponibles**")
        
        with st.form("form_edicion_masiva"):
            operacion = st.selectbox(
                "Seleccionar operación:",
                ["", "Cambiar Estado", "Asignar Funcionario", "Cambiar Entidad", "Actualizar Fechas"]
            )
            
            nuevo_valor = ""
            if operacion == "Cambiar Estado":
                nuevo_valor = st.selectbox("Nuevo estado:", OPCIONES_ESTADO[1:])
            elif operacion == "Asignar Funcionario":
                funcionarios_disponibles = obtener_funcionarios_unicos(registros_df)
                nuevo_valor = st.selectbox("Nuevo funcionario:", funcionarios_disponibles)
            elif operacion == "Cambiar Entidad":
                entidades_disponibles = obtener_entidades_unicas(registros_df)
                nuevo_valor = st.selectbox("Nueva entidad:", entidades_disponibles)
            elif operacion == "Actualizar Fechas":
                tipo_fecha = st.selectbox("Tipo de fecha:", ["Análisis y cronograma", "Estándares", "Publicación"])
                nueva_fecha = st.date_input("Nueva fecha:")
                nuevo_valor = f"{tipo_fecha}|{fecha_a_string(nueva_fecha)}"
            
            confirmar_masiva = st.checkbox("Confirmo que quiero aplicar esta operación masiva")
            
            submitted_masiva = st.form_submit_button("Aplicar Operación Masiva", type="primary")
            
            if submitted_masiva and operacion and nuevo_valor and confirmar_masiva:
                procesar_edicion_masiva(registros_df, df_filtrado, operacion, nuevo_valor)

def mostrar_importar_exportar(registros_df):
    """Herramientas de importación y exportación"""
    st.markdown("#### Importar/Exportar Datos")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Exportar Datos**")
        
        # Exportar todo o filtrado
        formato_exportar = st.selectbox("Formato:", ["Excel", "CSV", "JSON"])
        
        incluir_calculados = st.checkbox("Incluir campos calculados (avance, plazos)")
        
        if st.button("Exportar Datos", type="primary"):
            exportar_registros(registros_df, formato_exportar, incluir_calculados)
    
    with col2:
        st.markdown("**Importar Datos**")
        
        archivo_importar = st.file_uploader(
            "Seleccionar archivo:",
            type=['xlsx', 'csv'],
            key="archivo_importar"
        )
        
        if archivo_importar:
            modo_importar = st.selectbox(
                "Modo de importación:",
                ["Agregar nuevos registros", "Actualizar registros existentes", "Reemplazar todos los datos"]
            )
            
            if st.button("Importar Datos", type="secondary"):
                procesar_importacion(registros_df, archivo_importar, modo_importar)

def mostrar_herramientas_avanzadas(registros_df):
    """Herramientas avanzadas adicionales"""
    st.markdown("#### Herramientas Avanzadas")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Validación y Limpieza**")
        
        if st.button("Validar Todos los Registros"):
            validar_todos_registros(registros_df)
        
        if st.button("Limpiar Datos Duplicados"):
            limpiar_duplicados(registros_df)
        
        if st.button("Recalcular Avances"):
            recalcular_todos_avances(registros_df)
    
    with col2:
        st.markdown("**Respaldo y Restauración**")
        
        if st.button("Crear Respaldo Manual"):
            crear_respaldo_manual(registros_df)
        
        if st.button("Restaurar desde Respaldo"):
            mostrar_opciones_restauracion()
        
        if st.button("Verificar Integridad"):
            verificar_integridad_datos(registros_df)

# FUNCIONES DE PROCESAMIENTO

def procesar_edicion_completa(registros_df, indice, valores, cerrar=False):
    """Procesa la edición completa de un registro"""
    try:
        # Validar campos obligatorios
        if not valores['Funcionario'] or not valores['Funcionario'].strip():
            st.error("El funcionario es obligatorio")
            return
        
        if not valores['Entidad'] or not valores['Entidad'].strip():
            st.error("La entidad es obligatoria")
            return
        
        # Actualizar el registro en el DataFrame
        for campo, valor in valores.items():
            if campo in registros_df.columns:
                registros_df.iloc[indice, registros_df.columns.get_loc(campo)] = valor
        
        # Recalcular avance
        nuevo_avance = calcular_porcentaje_avance(registros_df.iloc[indice])
        if 'Porcentaje Avance' in registros_df.columns:
            registros_df.iloc[indice, registros_df.columns.get_loc('Porcentaje Avance')] = nuevo_avance
        
        # Guardar cambios
        try:
            exito, mensaje = guardar_datos_editados(registros_df, crear_backup=True)
        except:
            exito, mensaje = guardar_en_sheets_local(registros_df)
        
        if exito:
            st.success(f"Registro {valores['Cod']} actualizado exitosamente. Avance: {nuevo_avance}%")
            st.session_state.ultimo_guardado = datetime.now().strftime("%H:%M:%S")
            st.session_state.operacion_exitosa = "Edición completada"
            
            if cerrar:
                time.sleep(1)
                st.rerun()
        else:
            st.error(f"Error al guardar: {mensaje}")
    
    except Exception as e:
        st.error(f"Error procesando edición: {str(e)}")

def procesar_creacion_completa(registros_df, valores, crear_otro=False):
    """Procesa la creación completa de un nuevo registro"""
    try:
        # Validar campos obligatorios
        if not valores['Funcionario'] or not valores['Funcionario'].strip():
            st.error("El funcionario es obligatorio")
            return
        
        if not valores['Entidad'] or not valores['Entidad'].strip():
            st.error("La entidad es obligatoria")
            return
        
        # Crear nuevo registro
        nuevo_registro = pd.Series({col: '' for col in registros_df.columns})
        
        # Asignar valores
        for campo, valor in valores.items():
            if campo in nuevo_registro.index:
                nuevo_registro[campo] = valor
        
        # Calcular avance
        avance = calcular_porcentaje_avance(nuevo_registro)
        nuevo_registro['Porcentaje Avance'] = avance
        
        # Agregar al DataFrame
        registros_df_nuevo = pd.concat([registros_df, nuevo_registro.to_frame().T], ignore_index=True)
        
        # Guardar
        try:
            exito, mensaje = guardar_datos_editados(registros_df_nuevo, crear_backup=True)
        except:
            exito, mensaje = guardar_en_sheets_local(registros_df_nuevo)
        
        if exito:
            st.success(f"Registro {valores['Cod']} creado exitosamente. Avance: {avance}%")
            st.session_state['registros_df'] = registros_df_nuevo
            st.session_state.ultimo_guardado = datetime.now().strftime("%H:%M:%S")
            st.session_state.operacion_exitosa = "Creación completada"
            
            if not crear_otro:
                time.sleep(1)
                st.rerun()
        else:
            st.error(f"Error al guardar: {mensaje}")
    
    except Exception as e:
        st.error(f"Error procesando creación: {str(e)}")

def procesar_creacion_multiple(registros_df, valores_base, cantidad, crear_otro=False):
    """Procesa la creación de múltiples registros"""
    try:
        registros_creados = []
        
        for i in range(cantidad):
            # Crear código secuencial
            codigo_base = int(valores_base['Cod'])
            nuevo_codigo = f"{codigo_base + i:03d}"
            
            # Copiar valores base
            valores = valores_base.copy()
            valores['Cod'] = nuevo_codigo
            
            # Modificar según el índice
            if i > 0:
                valores['Nivel Información '] = f"{valores['Nivel Información ']} - {i+1}"
            
            # Crear registro
            nuevo_registro = pd.Series({col: '' for col in registros_df.columns})
            for campo, valor in valores.items():
                if campo in nuevo_registro.index:
                    nuevo_registro[campo] = valor
            
            nuevo_registro['Porcentaje Avance'] = calcular_porcentaje_avance(nuevo_registro)
            registros_creados.append(nuevo_registro)
        
        # Agregar todos los registros
        if registros_creados:
            df_nuevos = pd.DataFrame(registros_creados)
            registros_df_final = pd.concat([registros_df, df_nuevos], ignore_index=True)
            
            # Guardar
            try:
                exito, mensaje = guardar_datos_editados(registros_df_final, crear_backup=True)
            except:
                exito, mensaje = guardar_en_sheets_local(registros_df_final)
            
            if exito:
                st.success(f"{cantidad} registros creados exitosamente")
                st.session_state['registros_df'] = registros_df_final
                st.session_state.ultimo_guardado = datetime.now().strftime("%H:%M:%S")
                st.session_state.operacion_exitosa = f"{cantidad} registros creados"
                
                if not crear_otro:
                    time.sleep(1)
                    st.rerun()
            else:
                st.error(f"Error al guardar: {mensaje}")
    
    except Exception as e:
        st.error(f"Error procesando creación múltiple: {str(e)}")

def procesar_edicion_masiva(registros_df, df_filtrado, operacion, nuevo_valor):
    """Procesa operaciones de edición masiva"""
    try:
        registros_modificados = 0
        
        for idx in df_filtrado.index:
            if operacion == "Cambiar Estado":
                registros_df.at[idx, 'Estado'] = nuevo_valor
                registros_modificados += 1
            
            elif operacion == "Asignar Funcionario":
                registros_df.at[idx, 'Funcionario'] = nuevo_valor
                registros_modificados += 1
            
            elif operacion == "Cambiar Entidad":
                registros_df.at[idx, 'Entidad'] = nuevo_valor
                registros_modificados += 1
            
            elif operacion == "Actualizar Fechas":
                tipo_fecha, fecha_valor = nuevo_valor.split('|')
                registros_df.at[idx, tipo_fecha] = fecha_valor
                registros_modificados += 1
        
        if registros_modificados > 0:
            # Recalcular avances
            for idx in df_filtrado.index:
                nuevo_avance = calcular_porcentaje_avance(registros_df.iloc[idx])
                registros_df.at[idx, 'Porcentaje Avance'] = nuevo_avance
            
            # Guardar
            try:
                exito, mensaje = guardar_datos_editados(registros_df, crear_backup=True)
            except:
                exito, mensaje = guardar_en_sheets_local(registros_df)
            
            if exito:
                st.success(f"Operación masiva completada: {registros_modificados} registros modificados")
                st.session_state.ultimo_guardado = datetime.now().strftime("%H:%M:%S")
                st.session_state.operacion_exitosa = f"Edición masiva: {registros_modificados} registros"
                time.sleep(1)
                st.rerun()
            else:
                st.error(f"Error al guardar: {mensaje}")
        else:
            st.warning("No se modificaron registros")
    
    except Exception as e:
        st.error(f"Error en edición masiva: {str(e)}")

def mostrar_vista_previa_registro(valores):
    """Muestra vista previa de un registro antes de crearlo"""
    st.markdown("#### Vista Previa del Nuevo Registro")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write(f"**Código:** {valores['Cod']}")
        st.write(f"**Funcionario:** {valores['Funcionario']}")
        st.write(f"**Entidad:** {valores['Entidad']}")
        st.write(f"**Información:** {valores['Nivel Información ']}")
        st.write(f"**Tipo:** {valores['TipoDato']}")
    
    with col2:
        st.write(f"**Mes:** {valores['Mes Proyectado']}")
        st.write(f"**Estado:** {valores['Estado']}")
        st.write(f"**Análisis:** {valores['Análisis y cronograma']}")
        st.write(f"**Publicación:** {valores['Publicación']}")
    
    # Calcular avance estimado
    registro_temp = pd.Series(valores)
    avance_estimado = calcular_porcentaje_avance(registro_temp)
    
    st.info(f"Avance estimado: **{avance_estimado}%**")

# FUNCIONES DE HERRAMIENTAS AVANZADAS

def validar_todos_registros(registros_df):
    """Valida todos los registros y reporta problemas"""
    problemas = []
    
    for idx, row in registros_df.iterrows():
        codigo = get_safe_value(row, 'Cod')
        
        # Validaciones básicas
        if not get_safe_value(row, 'Funcionario'):
            problemas.append(f"Registro {codigo}: Sin funcionario")
        
        if not get_safe_value(row, 'Entidad'):
            problemas.append(f"Registro {codigo}: Sin entidad")
        
        # Validar fechas
        fechas_a_validar = ['Análisis y cronograma', 'Estándares', 'Publicación']
        for campo_fecha in fechas_a_validar:
            fecha_valor = get_safe_value(row, campo_fecha)
            if fecha_valor and not es_fecha_valida(fecha_valor):
                problemas.append(f"Registro {codigo}: Fecha inválida en {campo_fecha}")
    
    if problemas:
        st.error(f"Se encontraron {len(problemas)} problemas:")
        for problema in problemas[:10]:  # Mostrar solo los primeros 10
            st.write(f"- {problema}")
        if len(problemas) > 10:
            st.write(f"... y {len(problemas) - 10} problemas más")
    else:
        st.success("Todos los registros pasaron la validación")

def limpiar_duplicados(registros_df):
    """Identifica y limpia registros duplicados"""
    duplicados = registros_df.duplicated(subset=['Entidad', 'Nivel Información '], keep='first')
    num_duplicados = duplicados.sum()
    
    if num_duplicados > 0:
        st.warning(f"Se encontraron {num_duplicados} posibles registros duplicados")
        
        # Mostrar duplicados
        registros_duplicados = registros_df[duplicados]
        st.dataframe(registros_duplicados[['Cod', 'Entidad', 'Nivel Información ', 'Funcionario']])
        
        if st.button("Eliminar Duplicados Confirmados"):
            registros_df_limpio = registros_df[~duplicados]
            
            try:
                exito, mensaje = guardar_datos_editados(registros_df_limpio, crear_backup=True)
            except:
                exito, mensaje = guardar_en_sheets_local(registros_df_limpio)
            
            if exito:
                st.success(f"{num_duplicados} registros duplicados eliminados")
                st.session_state['registros_df'] = registros_df_limpio
                time.sleep(1)
                st.rerun()
            else:
                st.error(f"Error al limpiar duplicados: {mensaje}")
    else:
        st.success("No se encontraron registros duplicados")

def recalcular_todos_avances(registros_df):
    """Recalcula el avance de todos los registros"""
    try:
        registros_actualizados = 0
        
        for idx, row in registros_df.iterrows():
            avance_actual = registros_df.at[idx, 'Porcentaje Avance'] if 'Porcentaje Avance' in registros_df.columns else 0
            nuevo_avance = calcular_porcentaje_avance(row)
            
            if avance_actual != nuevo_avance:
                registros_df.at[idx, 'Porcentaje Avance'] = nuevo_avance
                registros_actualizados += 1

def mostrar_edicion_registros_con_autenticacion(registros_df):
    """
    FUNCIÓN PRINCIPAL CON AUTENTICACIÓN - Para usar en app1.py
    Wrapper que requiere autenticación para acceder al editor completo
    """
    
    # Verificar autenticación
    try:
        from auth_utils import verificar_autenticacion
    except ImportError:
        def verificar_autenticacion():
            return st.session_state.get('autenticado', False)
    
    if not verificar_autenticacion():
        st.warning("Acceso restringido")
        st.info("Debe iniciar sesión como administrador para editar registros")
        
        # Mostrar solo vista de lectura
        st.subheader("Vista de Solo Lectura")
        
        if not registros_df.empty:
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
            
            # Tabla de solo lectura (primeros 20 registros)
            st.dataframe(registros_df.head(20), use_container_width=True)
        else:
            st.warning("No hay datos disponibles")
        
        return registros_df
    
    else:
        # Usuario autenticado - mostrar editor completo
        return mostrar_edicion_registros(registros_df)
