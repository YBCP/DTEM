# editor.py - VERSIÓN COMPLETA con aparición automática de campos
"""
Editor COMPLETO CORREGIDO:
- TODOS los campos y secciones originales
- Funcionarios y entidades nuevas aparecen automáticamente
- Diseño limpio sin iconos
- Funcionalidad completa garantizada
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

SEGUIMIENTO_OPCIONES = ["", "En seguimiento", "Completado", "Pendiente", "En revisión", 
                       "Requiere acción", "Sin novedad"]

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
    if 'Funcionario' not in df.columns:
        return []
    
    funcionarios = []
    for func in df['Funcionario'].dropna().unique():
        func_str = str(func).strip()
        if func_str and func_str.lower() not in ['nan', 'none', '']:
            funcionarios.append(func_str)
    
    return sorted(list(set(funcionarios)))

def obtener_entidades_unicas(df):
    """Obtiene lista única de entidades limpias"""
    if 'Entidad' not in df.columns:
        return []
    
    entidades = []
    for ent in df['Entidad'].dropna().unique():
        ent_str = str(ent).strip()
        if ent_str and ent_str.lower() not in ['nan', 'none', '']:
            entidades.append(ent_str)
    
    return sorted(list(set(entidades)))

def obtener_frecuencias_unicas(df):
    """Obtiene lista única de frecuencias"""
    if 'Frecuencia actualizacion ' not in df.columns:
        return []
    
    frecuencias = df['Frecuencia actualizacion '].dropna().unique().tolist()
    frecuencias = [f for f in frecuencias if str(f).strip() and str(f).strip().lower() != 'nan']
    return sorted(list(set(frecuencias)))

def obtener_seguimientos_unicos(df):
    """Obtiene lista única de seguimientos"""
    if 'Seguimiento a los acuerdos' not in df.columns:
        return []
    
    seguimientos = df['Seguimiento a los acuerdos'].dropna().unique().tolist()
    seguimientos = [s for s in seguimientos if str(s).strip() and str(s).strip().lower() != 'nan']
    return sorted(list(set(seguimientos)))

def fecha_a_string(fecha):
    """Convierte fecha a string en formato DD/MM/YYYY"""
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
    """Convierte string a objeto date"""
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
    """Guarda datos en Google Sheets - SOLO hoja Registros"""
    if GoogleSheetsManager is None:
        return False, "GoogleSheetsManager no disponible"
    
    try:
        manager = GoogleSheetsManager()
        
        if df.empty:
            return False, "No se puede guardar un DataFrame vacío"
        
        # Limpiar datos antes de guardar
        df_clean = df.copy()
        df_clean = df_clean.fillna('')
        df_clean = df_clean.astype(str)
        df_clean = df_clean.replace('nan', '').replace('None', '')
        
        # SOLO escribir en Registros
        exito = manager.escribir_hoja(df_clean, "Registros", limpiar_hoja=True)
        
        if exito:
            # Forzar actualización en session_state
            st.session_state['registros_df'] = df_clean
            return True, "Datos guardados y sincronizados en Google Sheets"
        else:
            return False, "Error al escribir en Google Sheets"
            
    except Exception as e:
        error_msg = str(e).lower()
        if 'ssl' in error_msg:
            return False, "Error SSL - Refresca la página e intenta de nuevo"
        elif 'permission' in error_msg or '403' in error_msg:
            return False, "Error de permisos - Verifica acceso al spreadsheet"
        else:
            return False, f"Error: {str(e)}"

def calcular_avance(row):
    """Calcula el porcentaje de avance basado en campos clave"""
    try:
        avance = 0
        
        # Acuerdo de compromiso
        if get_safe_value(row, 'Acuerdo de compromiso', '').lower() in ['si', 'sí']:
            avance += 25
            
        # Análisis y cronograma
        if get_safe_value(row, 'Análisis y cronograma', '').strip():
            avance += 25
            
        # Estándares
        if get_safe_value(row, 'Estándares', '').strip():
            avance += 25
            
        # Publicación
        if get_safe_value(row, 'Publicación', '').strip():
            avance += 25
        
        return min(avance, 100)
    except:
        return 0

def generar_codigo(df):
    """Genera nuevo código autonumérico"""
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

def mostrar_formulario_completo(row, indice, es_nuevo=False, df=None):
    """
    FORMULARIO COMPLETO CON TODOS LOS CAMPOS Y SECCIONES
    """
    
    # Obtener listas únicas para desplegables
    funcionarios_existentes = obtener_funcionarios_unicos(df) if df is not None else []
    entidades_existentes = obtener_entidades_unicas(df) if df is not None else []
    frecuencias_existentes = obtener_frecuencias_unicas(df) if df is not None else []
    seguimientos_existentes = obtener_seguimientos_unicos(df) if df is not None else []
    
    # Sufijo único para keys
    key_suffix = f"_{indice}_{'nuevo' if es_nuevo else 'editar'}"
    
    # INFORMACIÓN BÁSICA
    st.subheader("Información Básica")
    col1, col2 = st.columns(2)
    
    with col1:
        codigo = st.text_input("Código", 
            value=get_safe_value(row, 'Cod'),
            disabled=es_nuevo,
            key=f"cod{key_suffix}")
        
        # FUNCIONARIO - CORREGIDO: Con aparición automática
        st.write("**Funcionario:**")
        opciones_funcionario = ["Seleccionar existente"] + funcionarios_existentes + ["AGREGAR NUEVO FUNCIONARIO"]
        
        funcionario_actual = get_safe_value(row, 'Funcionario')
        indice_inicial = 0
        if funcionario_actual and funcionario_actual in funcionarios_existentes:
            indice_inicial = funcionarios_existentes.index(funcionario_actual) + 1
        
        opcion_funcionario = st.selectbox(
            "Seleccione:",
            opciones_funcionario,
            index=indice_inicial,
            key=f"func_select{key_suffix}"
        )
        
        # CAMPO APARECE AUTOMÁTICAMENTE
        if opcion_funcionario == "AGREGAR NUEVO FUNCIONARIO":
            funcionario = st.text_input(
                "Escriba el nombre del funcionario:",
                value="",
                placeholder="Nombre completo del funcionario",
                key=f"func_nuevo{key_suffix}"
            )
            if not funcionario.strip():
                st.warning("Debe escribir el nombre del funcionario")
        elif opcion_funcionario == "Seleccionar existente":
            funcionario = ""
        else:
            funcionario = opcion_funcionario
    
    with col2:
        # ENTIDAD - CORREGIDO: Con aparición automática
        st.write("**Entidad:**")
        opciones_entidad = ["Seleccionar existente"] + entidades_existentes + ["AGREGAR NUEVA ENTIDAD"]
        
        entidad_actual = get_safe_value(row, 'Entidad')
        indice_inicial_ent = 0
        if entidad_actual and entidad_actual in entidades_existentes:
            indice_inicial_ent = entidades_existentes.index(entidad_actual) + 1
        
        opcion_entidad = st.selectbox(
            "Seleccione:",
            opciones_entidad,
            index=indice_inicial_ent,
            key=f"ent_select{key_suffix}"
        )
        
        # CAMPO APARECE AUTOMÁTICAMENTE
        if opcion_entidad == "AGREGAR NUEVA ENTIDAD":
            entidad = st.text_input(
                "Escriba el nombre de la entidad:",
                value="",
                placeholder="Nombre completo de la entidad",
                key=f"ent_nueva{key_suffix}"
            )
            if not entidad.strip():
                st.warning("Debe escribir el nombre de la entidad")
        elif opcion_entidad == "Seleccionar existente":
            entidad = ""
        else:
            entidad = opcion_entidad
        
        nivel_info = st.text_input("Nivel de Información",
            value=get_safe_value(row, 'Nivel Información '),
            key=f"nivel{key_suffix}")
        
        # TIPO DE DATO - Solo "Actualizar" y "Nuevo"
        tipo_actual = get_safe_value(row, 'TipoDato')
        tipo_opciones = ["", "Actualizar", "Nuevo"]
        tipo_index = tipo_opciones.index(tipo_actual) if tipo_actual in tipo_opciones else 0
        
        tipo_dato = st.selectbox("Tipo de Dato",
            options=tipo_opciones,
            index=tipo_index,
            key=f"tipo{key_suffix}")
    
    # FRECUENCIA - Lista desplegable editable
    frecuencia_actual = get_safe_value(row, 'Frecuencia actualizacion ')
    
    # Combinar frecuencias predefinidas con existentes
    todas_frecuencias = FRECUENCIAS.copy()
    for freq in frecuencias_existentes:
        if freq and freq not in todas_frecuencias:
            todas_frecuencias.append(freq)
    
    frecuencia_index = todas_frecuencias.index(frecuencia_actual) if frecuencia_actual in todas_frecuencias else 0
    frecuencia = st.selectbox("Frecuencia",
        options=["Seleccionar"] + todas_frecuencias[1:] + ["Escribir otra"],
        index=frecuencia_index if frecuencia_actual in todas_frecuencias[1:] else 0,
        key=f"freq{key_suffix}")
    
    if frecuencia == "Escribir otra":
        frecuencia = st.text_input("Nueva frecuencia:",
            placeholder="Ej: Quincenal, Bimestral, etc.",
            key=f"freq_nueva{key_suffix}")
    elif frecuencia == "Seleccionar":
        frecuencia = ""
    
    # MES PROYECTADO - Lista desplegable de meses
    mes_actual = get_safe_value(row, 'Mes Proyectado')
    mes_index = MESES.index(mes_actual) if mes_actual in MESES else 0
    
    mes_proyectado = st.selectbox("Mes Proyectado",
        options=MESES,
        index=mes_index,
        key=f"mes{key_suffix}")
    
    # ACUERDOS
    st.subheader("Acuerdos y Compromisos")
    col1, col2 = st.columns(2)
    
    with col1:
        actas_interes = st.selectbox("Actas de interés",
            options=["", "Si", "No"],
            index=0 if not get_safe_value(row, 'Actas de acercamiento y manifestación de interés') else
                  ["", "Si", "No"].index(get_safe_value(row, 'Actas de acercamiento y manifestación de interés'))
                  if get_safe_value(row, 'Actas de acercamiento y manifestación de interés') in ["", "Si", "No"] else 0,
            key=f"actas{key_suffix}")
        
        acuerdo_compromiso = st.selectbox("Acuerdo de compromiso",
            options=["", "Si", "No"],
            index=0 if not get_safe_value(row, 'Acuerdo de compromiso') else
                  ["", "Si", "No"].index(get_safe_value(row, 'Acuerdo de compromiso'))
                  if get_safe_value(row, 'Acuerdo de compromiso') in ["", "Si", "No"] else 0,
            key=f"acuerdo{key_suffix}")
    
    with col2:
        # FECHAS - Selectores de fecha
        suscripcion_fecha = string_a_fecha(get_safe_value(row, 'Suscripción acuerdo de compromiso'))
        suscripcion = st.date_input("Suscripción acuerdo",
            value=suscripcion_fecha,
            key=f"suscripcion{key_suffix}")
        
        if st.checkbox(f"Borrar fecha suscripción", key=f"borrar_suscripcion{key_suffix}"):
            suscripcion = None
        
        entrega_fecha = string_a_fecha(get_safe_value(row, 'Entrega acuerdo de compromiso'))
        entrega_acuerdo = st.date_input("Entrega acuerdo",
            value=entrega_fecha,
            key=f"entrega{key_suffix}")
        
        if st.checkbox(f"Borrar fecha entrega", key=f"borrar_entrega{key_suffix}"):
            entrega_acuerdo = None
    
    # GESTIÓN DE DATOS
    st.subheader("Gestión de Información")
    col1, col2 = st.columns(2)
    
    with col1:
        acceso_datos = st.selectbox("Acceso a datos",
            options=["", "Si", "No"],
            index=0 if not get_safe_value(row, 'Gestion acceso a los datos y documentos requeridos ') else
                  ["", "Si", "No"].index(get_safe_value(row, 'Gestion acceso a los datos y documentos requeridos '))
                  if get_safe_value(row, 'Gestion acceso a los datos y documentos requeridos ') in ["", "Si", "No"] else 0,
            key=f"acceso{key_suffix}")
        
        analisis_info = st.selectbox("Análisis de información",
            options=["", "Si", "No"],
            index=0 if not get_safe_value(row, ' Análisis de información') else
                  ["", "Si", "No"].index(get_safe_value(row, ' Análisis de información'))
                  if get_safe_value(row, ' Análisis de información') in ["", "Si", "No"] else 0,
            key=f"analisis{key_suffix}")
    
    with col2:
        cronograma = st.selectbox("Cronograma Concertado",
            options=["", "Si", "No"],
            index=0 if not get_safe_value(row, 'Cronograma Concertado') else
                  ["", "Si", "No"].index(get_safe_value(row, 'Cronograma Concertado'))
                  if get_safe_value(row, 'Cronograma Concertado') in ["", "Si", "No"] else 0,
            key=f"cronograma{key_suffix}")
        
        fecha_entrega_date = string_a_fecha(get_safe_value(row, 'Fecha de entrega de información'))
        fecha_entrega = st.date_input("Fecha entrega información",
            value=fecha_entrega_date,
            key=f"fecha_entrega{key_suffix}")
        
        if st.checkbox(f"Borrar fecha entrega información", key=f"borrar_fecha_entrega{key_suffix}"):
            fecha_entrega = None
    
    # FECHAS PROGRAMADAS
    st.subheader("Fechas y Cronograma")
    col1, col2 = st.columns(2)
    
    with col1:
        analisis_prog_date = string_a_fecha(get_safe_value(row, 'Análisis y cronograma (fecha programada)'))
        analisis_programada = st.date_input("Análisis programada",
            value=analisis_prog_date,
            key=f"analisis_prog{key_suffix}")
        
        if st.checkbox(f"Borrar fecha análisis programada", key=f"borrar_analisis_prog{key_suffix}"):
            analisis_programada = None
        
        analisis_real_date = string_a_fecha(get_safe_value(row, 'Análisis y cronograma'))
        analisis_real = st.date_input("Análisis real",
            value=analisis_real_date,
            key=f"analisis_real{key_suffix}")
        
        if st.checkbox(f"Borrar fecha análisis real", key=f"borrar_analisis_real{key_suffix}"):
            analisis_real = None
    
    with col2:
        # SEGUIMIENTO - Lista desplegable editable
        seguimiento_actual = get_safe_value(row, 'Seguimiento a los acuerdos')
        
        # Combinar seguimientos predefinidos con existentes
        todos_seguimientos = SEGUIMIENTO_OPCIONES.copy()
        for seg in seguimientos_existentes:
            if seg and seg not in todos_seguimientos:
                todos_seguimientos.append(seg)
        
        seguimiento_index = todos_seguimientos.index(seguimiento_actual) if seguimiento_actual in todos_seguimientos else 0
        seguimiento = st.selectbox("Seguimiento acuerdos",
            options=["Seleccionar"] + todos_seguimientos[1:] + ["Escribir otro"],
            index=seguimiento_index if seguimiento_actual in todos_seguimientos[1:] else 0,
            key=f"seguimiento_select{key_suffix}")
        
        if seguimiento == "Escribir otro":
            seguimiento = st.text_area("Otro seguimiento:",
                height=80,
                key=f"seguimiento_otro{key_suffix}")
        elif seguimiento == "Seleccionar":
            seguimiento = ""
    
    # ESTÁNDARES
    st.subheader("Estándares")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        registro = st.selectbox("Registro",
            options=["", "Completo", "Incompleto", "No aplica"],
            index=0 if not get_safe_value(row, 'Registro (completo)') else
                  ["", "Completo", "Incompleto", "No aplica"].index(get_safe_value(row, 'Registro (completo)'))
                  if get_safe_value(row, 'Registro (completo)') in ["", "Completo", "Incompleto", "No aplica"] else 0,
            key=f"registro{key_suffix}")
        
        et = st.selectbox("ET",
            options=["", "Completo", "Incompleto", "No aplica"],
            index=0 if not get_safe_value(row, 'ET (completo)') else
                  ["", "Completo", "Incompleto", "No aplica"].index(get_safe_value(row, 'ET (completo)'))
                  if get_safe_value(row, 'ET (completo)') in ["", "Completo", "Incompleto", "No aplica"] else 0,
            key=f"et{key_suffix}")
    
    with col2:
        co = st.selectbox("CO",
            options=["", "Completo", "Incompleto", "No aplica"],
            index=0 if not get_safe_value(row, 'CO (completo)') else
                  ["", "Completo", "Incompleto", "No aplica"].index(get_safe_value(row, 'CO (completo)'))
                  if get_safe_value(row, 'CO (completo)') in ["", "Completo", "Incompleto", "No aplica"] else 0,
            key=f"co{key_suffix}")
        
        dd = st.selectbox("DD",
            options=["", "Completo", "Incompleto", "No aplica"],
            index=0 if not get_safe_value(row, 'DD (completo)') else
                  ["", "Completo", "Incompleto", "No aplica"].index(get_safe_value(row, 'DD (completo)'))
                  if get_safe_value(row, 'DD (completo)') in ["", "Completo", "Incompleto", "No aplica"] else 0,
            key=f"dd{key_suffix}")
    
    with col3:
        rec = st.selectbox("REC",
            options=["", "Completo", "Incompleto", "No aplica"],
            index=0 if not get_safe_value(row, 'REC (completo)') else
                  ["", "Completo", "Incompleto", "No aplica"].index(get_safe_value(row, 'REC (completo)'))
                  if get_safe_value(row, 'REC (completo)') in ["", "Completo", "Incompleto", "No aplica"] else 0,
            key=f"rec{key_suffix}")
        
        servicio = st.selectbox("SERVICIO",
            options=["", "Completo", "Incompleto", "No aplica"],
            index=0 if not get_safe_value(row, 'SERVICIO (completo)') else
                  ["", "Completo", "Incompleto", "No aplica"].index(get_safe_value(row, 'SERVICIO (completo)'))
                  if get_safe_value(row, 'SERVICIO (completo)') in ["", "Completo", "Incompleto", "No aplica"] else 0,
            key=f"servicio{key_suffix}")
    
    # FECHAS DE ESTÁNDARES
    col1, col2 = st.columns(2)
    with col1:
        est_prog_date = string_a_fecha(get_safe_value(row, 'Estándares (fecha programada)'))
        estandares_prog = st.date_input("Estándares programada",
            value=est_prog_date,
            key=f"est_prog{key_suffix}")
        
        if st.checkbox(f"Borrar fecha estándares programada", key=f"borrar_est_prog{key_suffix}"):
            estandares_prog = None
    
    with col2:
        est_real_date = string_a_fecha(get_safe_value(row, 'Estándares'))
        estandares_real = st.date_input("Estándares real",
            value=est_real_date,
            key=f"est_real{key_suffix}")
        
        if st.checkbox(f"Borrar fecha estándares real", key=f"borrar_est_real{key_suffix}"):
            estandares_real = None
    
    # VERIFICACIONES
    st.subheader("Verificaciones")
    col1, col2 = st.columns(2)
    
    with col1:
        orientacion = st.selectbox("Orientación técnica",
            options=["", "Si", "No"],
            index=0 if not get_safe_value(row, 'Resultados de orientación técnica') else
                  ["", "Si", "No"].index(get_safe_value(row, 'Resultados de orientación técnica'))
                  if get_safe_value(row, 'Resultados de orientación técnica') in ["", "Si", "No"] else 0,
            key=f"orientacion{key_suffix}")
        
        verificacion_web = st.selectbox("Verificación servicio web",
            options=["", "Si", "No"],
            index=0 if not get_safe_value(row, 'Verificación del servicio web geográfico') else
                  ["", "Si", "No"].index(get_safe_value(row, 'Verificación del servicio web geográfico'))
                  if get_safe_value(row, 'Verificación del servicio web geográfico') in ["", "Si", "No"] else 0,
            key=f"verificacion{key_suffix}")
    
    with col2:
        verificar_aprobar = st.selectbox("Verificar Aprobar",
            options=["", "Si", "No"],
            index=0 if not get_safe_value(row, 'Verificar Aprobar Resultados') else
                  ["", "Si", "No"].index(get_safe_value(row, 'Verificar Aprobar Resultados'))
                  if get_safe_value(row, 'Verificar Aprobar Resultados') in ["", "Si", "No"] else 0,
            key=f"aprobar{key_suffix}")
        
        revisar_validar = st.selectbox("Revisar y validar",
            options=["", "Si", "No"],
            index=0 if not get_safe_value(row, 'Revisar y validar los datos cargados en la base de datos') else
                  ["", "Si", "No"].index(get_safe_value(row, 'Revisar y validar los datos cargados en la base de datos'))
                  if get_safe_value(row, 'Revisar y validar los datos cargados en la base de datos') in ["", "Si", "No"] else 0,
            key=f"revisar{key_suffix}")
    
    aprobacion = st.selectbox("Aprobación resultados",
        options=["", "Si", "No"],
        index=0 if not get_safe_value(row, 'Aprobación resultados obtenidos en la orientación') else
              ["", "Si", "No"].index(get_safe_value(row, 'Aprobación resultados obtenidos en la orientación'))
              if get_safe_value(row, 'Aprobación resultados obtenidos en la orientación') in ["", "Si", "No"] else 0,
        key=f"aprobacion{key_suffix}")
    
    # PUBLICACIÓN
    st.subheader("Publicación")
    col1, col2 = st.columns(2)
    
    with col1:
        pub_prog_date = string_a_fecha(get_safe_value(row, 'Fecha de publicación programada'))
        pub_programada = st.date_input("Publicación programada",
            value=pub_prog_date,
            key=f"pub_prog{key_suffix}")
        
        if st.checkbox(f"Borrar fecha publicación programada", key=f"borrar_pub_prog{key_suffix}"):
            pub_programada = None
        
        pub_real_date = string_a_fecha(get_safe_value(row, 'Publicación'))
        publicacion = st.date_input("Publicación real",
            value=pub_real_date,
            key=f"publicacion{key_suffix}")
        
        if st.checkbox(f"Borrar fecha publicación real", key=f"borrar_publicacion{key_suffix}"):
            publicacion = None
    
    with col2:
        disponer_datos = st.selectbox("Disponer datos temáticos",
            options=["", "Si", "No"],
            index=0 if not get_safe_value(row, 'Disponer datos temáticos') else
                  ["", "Si", "No"].index(get_safe_value(row, 'Disponer datos temáticos'))
                  if get_safe_value(row, 'Disponer datos temáticos') in ["", "Si", "No"] else 0,
            key=f"disponer{key_suffix}")
        
        catalogo = st.selectbox("Catálogo recursos",
            options=["", "Si", "No"],
            index=0 if not get_safe_value(row, 'Catálogo de recursos geográficos') else
                  ["", "Si", "No"].index(get_safe_value(row, 'Catálogo de recursos geográficos'))
                  if get_safe_value(row, 'Catálogo de recursos geográficos') in ["", "Si", "No"] else 0,
            key=f"catalogo{key_suffix}")
    
    # CIERRE
    st.subheader("Cierre")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        oficios_cierre = st.selectbox("Oficios de cierre",
            options=["", "Si", "No"],
            index=0 if not get_safe_value(row, 'Oficios de cierre') else
                  ["", "Si", "No"].index(get_safe_value(row, 'Oficios de cierre'))
                  if get_safe_value(row, 'Oficios de cierre') in ["", "Si", "No"] else 0,
            key=f"oficios{key_suffix}")
    
    with col2:
        fecha_oficio_date = string_a_fecha(get_safe_value(row, 'Fecha de oficio de cierre'))
        fecha_oficio = st.date_input("Fecha oficio cierre",
            value=fecha_oficio_date,
            key=f"fecha_oficio{key_suffix}")
        
        if st.checkbox(f"Borrar fecha oficio cierre", key=f"borrar_fecha_oficio{key_suffix}"):
            fecha_oficio = None
    
    with col3:
        estado = st.selectbox("Estado",
            options=["", "Completado", "En proceso", "Pendiente"],
            index=0 if not get_safe_value(row, 'Estado') else
                  ["", "Completado", "En proceso", "Pendiente"].index(get_safe_value(row, 'Estado'))
                  if get_safe_value(row, 'Estado') in ["", "Completado", "En proceso", "Pendiente"] else 0,
            key=f"estado{key_suffix}")
    
    # PLAZOS (solo lectura)
    st.subheader("Plazos Calculados")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.text_input("Plazo análisis",
            value=get_safe_value(row, 'Plazo de análisis'),
            disabled=True,
            key=f"plazo_analisis_display{key_suffix}")
    
    with col2:
        st.text_input("Plazo cronograma",
            value=get_safe_value(row, 'Plazo de cronograma'),
            disabled=True,
            key=f"plazo_cronograma_display{key_suffix}")
    
    with col3:
        st.text_input("Plazo oficio cierre",
            value=get_safe_value(row, 'Plazo de oficio de cierre'),
            disabled=True,
            key=f"plazo_oficio_display{key_suffix}")
    
    # OBSERVACIONES
    st.subheader("Observaciones")
    observacion = st.text_area("Observaciones",
        value=get_safe_value(row, 'Observación'),
        height=100,
        key=f"obs{key_suffix}")
    
    # AVANCE (solo lectura)
    avance_actual = calcular_avance(row)
    st.text_input("Porcentaje de Avance",
        value=f"{avance_actual}%",
        disabled=True,
        key=f"avance_display{key_suffix}")
    
    # Retornar valores del formulario COMPLETO
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
        'Fecha de publicación programada': fecha_a_string(pub_programada) if pub_programada else "",
        'Publicación': fecha_a_string(publicacion) if publicacion else "",
        'Disponer datos temáticos': disponer_datos,
        'Catálogo de recursos geográficos': catalogo,
        'Oficios de cierre': oficios_cierre,
        'Fecha de oficio de cierre': fecha_a_string(fecha_oficio) if fecha_oficio else "",
        'Estado': estado,
        'Observación': observacion
    }

def mostrar_edicion_registros(registros_df):
    """Editor principal limpio con formulario completo"""
    st.subheader("Editor de Registros")
    
    # Controles principales simplificados
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
    
    # Pestañas
    tab1, tab2 = st.tabs(["Editar Existente", "Crear Nuevo"])
    
    with tab1:
        # CAMPO DE BÚSQUEDA SIMPLIFICADO
        st.subheader("Buscar Registro")
        
        termino_busqueda = st.text_input(
            "Buscar por código, entidad o nivel:",
            placeholder="Escriba para filtrar registros...",
            key="busqueda_registro_editar"
        )
        
        # SELECTOR DE REGISTRO MEJORADO CON BÚSQUEDA
        opciones_filtradas = []
        
        for idx, row in registros_df.iterrows():
            codigo = get_safe_value(row, 'Cod', 'N/A')
            nivel = get_safe_value(row, 'Nivel Información ', 'Sin nivel')
            entidad = get_safe_value(row, 'Entidad', 'Sin entidad')
            opcion_completa = f"{codigo} - {nivel} - {entidad}"
            
            # Filtrar según término de búsqueda
            if termino_busqueda:
                termino_lower = termino_busqueda.lower()
                if (termino_lower in codigo.lower() or 
                    termino_lower in nivel.lower() or 
                    termino_lower in entidad.lower()):
                    opciones_filtradas.append((idx, opcion_completa))
            else:
                opciones_filtradas.append((idx, opcion_completa))
        
        if not opciones_filtradas:
            if termino_busqueda:
                st.warning(f"No se encontraron registros que coincidan con '{termino_busqueda}'")
                return registros_df
            else:
                st.warning("No hay registros para editar")
                return registros_df
        
        # Mostrar solo las opciones filtradas
        opciones_mostrar = [opcion for _, opcion in opciones_filtradas]
        
        if termino_busqueda:
            st.info(f"Mostrando {len(opciones_filtradas)} registros de {len(registros_df)} total")
        
        seleccion = st.selectbox("Seleccionar registro:", opciones_mostrar, key="seleccion_editar_tab1")
        
        # Obtener el índice real del registro seleccionado
        indice_real = None
        for idx, opcion in opciones_filtradas:
            if opcion == seleccion:
                indice_real = idx
                break
        
        if indice_real is None:
            st.error("Error al seleccionar registro")
            return registros_df
        
        row_seleccionada = registros_df.iloc[indice_real]
        
        # Información del registro seleccionado y botón de borrar
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.write(f"Editando: {get_safe_value(row_seleccionada, 'Cod')} - {get_safe_value(row_seleccionada, 'Nivel Información ')}")
        
        with col2:
            # BOTÓN DE BORRAR REGISTRO
            if st.button("Borrar Registro", type="secondary", key="btn_borrar_tab1"):
                st.session_state.confirmar_borrado = True
                st.session_state.registro_a_borrar = indice_real
        
        # CONFIRMACIÓN DE BORRADO
        if st.session_state.get('confirmar_borrado', False):
            st.warning("ADVERTENCIA: ¿Desea borrar este registro? Este cambio no se puede deshacer.")
            
            col_confirm1, col_confirm2 = st.columns(2)
            
            with col_confirm1:
                if st.button("SÍ, BORRAR", type="primary", key="confirmar_borrar_definitivo_tab1"):
                    try:
                        # Borrar registro del DataFrame
                        registros_df_actualizado = registros_df.drop(registros_df.index[st.session_state.registro_a_borrar]).reset_index(drop=True)
                        
                        # Guardar en Google Sheets
                        exito, mensaje = guardar_en_sheets(registros_df_actualizado)
                        
                        if exito:
                            st.success(f"Registro borrado exitosamente. {mensaje}")
                            st.session_state.ultimo_guardado = datetime.now().strftime("%H:%M:%S")
                            st.session_state['registros_df'] = registros_df_actualizado
                            
                            # Limpiar confirmación
                            del st.session_state.confirmar_borrado
                            del st.session_state.registro_a_borrar
                            
                            # Forzar actualización completa
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error(mensaje)
                            
                    except Exception as e:
                        st.error(f"Error al borrar registro: {str(e)}")
            
            with col_confirm2:
                if st.button("Cancelar", key="cancelar_borrar_tab1"):
                    # Limpiar confirmación
                    del st.session_state.confirmar_borrado
                    if 'registro_a_borrar' in st.session_state:
                        del st.session_state.registro_a_borrar
                    st.rerun()
        
        # Formulario de edición (solo mostrar si no está en modo confirmación)
        if not st.session_state.get('confirmar_borrado', False):
            with st.form("form_editar_completo"):
                valores = mostrar_formulario_completo(row_seleccionada, indice_real, False, registros_df)
                
                if st.form_submit_button("Guardar Cambios", type="primary"):
                    try:
                        # Validar que funcionario y entidad no estén vacíos
                        if not valores['Funcionario'].strip():
                            st.error("El campo 'Funcionario' es obligatorio")
                            return registros_df
                        
                        if not valores['Entidad'].strip():
                            st.error("El campo 'Entidad' es obligatorio")
                            return registros_df
                        
                        # Actualizar registro
                        for campo, valor in valores.items():
                            if campo in registros_df.columns:
                                registros_df.iloc[indice_real, registros_df.columns.get_loc(campo)] = valor
                        
                        # Calcular nuevo avance
                        nuevo_avance = calcular_avance(registros_df.iloc[indice_real])
                        if 'Porcentaje Avance' in registros_df.columns:
                            registros_df.iloc[indice_real, registros_df.columns.get_loc('Porcentaje Avance')] = nuevo_avance
                        
                        # Guardar en Google Sheets
                        exito, mensaje = guardar_en_sheets(registros_df)
                        
                        if exito:
                            st.success(f"{mensaje}. Avance: {nuevo_avance}%")
                            st.session_state.ultimo_guardado = datetime.now().strftime("%H:%M:%S")
                            st.session_state['registros_df'] = registros_df
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error(mensaje)
                            
                    except Exception as e:
                        st.error(f"Error al guardar: {str(e)}")
    
    with tab2:
        # Crear nuevo registro
        st.subheader("Crear Nuevo Registro")
        
        nuevo_codigo = generar_codigo(registros_df)
        st.info(f"Código asignado: {nuevo_codigo}")
        
        # Crear registro vacío
        registro_vacio = pd.Series({col: '' for col in registros_df.columns})
        registro_vacio['Cod'] = nuevo_codigo
        
        with st.form("form_nuevo_completo"):
            valores_nuevo = mostrar_formulario_completo(registro_vacio, "nuevo", True, registros_df)
            
            if st.form_submit_button("Crear Registro", type="primary"):
                try:
                    # Validar campos obligatorios
                    if not valores_nuevo['Funcionario'].strip():
                        st.error("El campo 'Funcionario' es obligatorio")
                        return registros_df
                    
                    if not valores_nuevo['Entidad'].strip():
                        st.error("El campo 'Entidad' es obligatorio")
                        return registros_df
                    
                    # Crear nuevo registro
                    nuevo_registro = pd.Series({col: '' for col in registros_df.columns})
                    
                    # Asignar valores del formulario
                    for campo, valor in valores_nuevo.items():
                        if campo in nuevo_registro.index:
                            nuevo_registro[campo] = valor
                    
                    # Calcular avance
                    avance = calcular_avance(nuevo_registro)
                    nuevo_registro['Porcentaje Avance'] = avance
                    
                    # Agregar al DataFrame
                    registros_df = pd.concat([registros_df, nuevo_registro.to_frame().T], ignore_index=True)
                    
                    # Guardar en Google Sheets
                    exito, mensaje = guardar_en_sheets(registros_df)
                    
                    if exito:
                        st.success(f"Registro {nuevo_codigo} creado exitosamente")
                        st.success(f"{mensaje}. Avance inicial: {avance}%")
                        st.session_state.ultimo_guardado = datetime.now().strftime("%H:%M:%S")
                        st.session_state['registros_df'] = registros_df
                        st.balloons()
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(mensaje)
                        
                except Exception as e:
                    st.error(f"Error al crear registro: {str(e)}")
    
    return registros_df

def mostrar_edicion_registros_con_autenticacion(registros_df):
    """Wrapper con autenticación"""
    
    try:
        from auth_utils import verificar_autenticacion
        
        if verificar_autenticacion():
            # Panel de diagnóstico minimalista
            with st.expander("Diagnóstico de Conexión"):
                if st.button("Verificar Google Sheets", key="verificar_sheets_completo"):
                    if GoogleSheetsManager:
                        try:
                            manager = GoogleSheetsManager()
                            hojas = manager.listar_hojas()
                            st.success(f"Conexión exitosa. Hojas: {', '.join(hojas)}")
                        except Exception as e:
                            st.error(f"Error de conexión: {str(e)}")
                    else:
                        st.error("GoogleSheetsManager no disponible")
            
            # Usar datos de session_state si están disponibles
            if 'registros_df' in st.session_state:
                registros_df = st.session_state['registros_df']
            
            return mostrar_edicion_registros(registros_df)
        else:
            st.subheader("Acceso Restringido")
            st.warning("Se requiere autenticación para editar registros")
            return registros_df
            
    except ImportError:
        st.warning("Sistema de autenticación no disponible - Acceso directo")
        return mostrar_edicion_registros(registros_df)
