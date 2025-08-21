# editor_mejorado.py - EDITOR LIMPIO CON AJUSTES SOLICITADOS
"""
Editor limpio y funcional con mejoras:
- Selector de registro: código + nivel de información
- Tipo de dato: solo "Actualizar" y "Nuevo"
- Funcionarios y entidades: listas desplegables editables
- Mes proyectado: lista desplegable de meses
- Campos de fecha: selectores de fecha
- Diseño visual limpio sin iconos ni texto innecesario
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date
import time

# MAPEO EXACTO DE COLUMNAS DEL ARCHIVO REAL
COLUMNAS_REALES = {
    'Cod': 'Cod',
    'Funcionario': 'Funcionario', 
    'Entidad': 'Entidad',
    'Nivel Información ': 'Nivel Información ',
    'Frecuencia actualizacion ': 'Frecuencia actualizacion ',
    'TipoDato': 'TipoDato',
    'Actas de acercamiento y manifestación de interés': 'Actas de acercamiento y manifestación de interés',
    'Suscripción acuerdo de compromiso': 'Suscripción acuerdo de compromiso',
    'Entrega acuerdo de compromiso': 'Entrega acuerdo de compromiso',
    'Acuerdo de compromiso': 'Acuerdo de compromiso',
    'Gestion acceso a los datos y documentos requeridos ': 'Gestion acceso a los datos y documentos requeridos ',
    ' Análisis de información': ' Análisis de información',
    'Cronograma Concertado': 'Cronograma Concertado',
    'Análisis y cronograma (fecha programada)': 'Análisis y cronograma (fecha programada)',
    'Fecha de entrega de información': 'Fecha de entrega de información',
    'Análisis de información': 'Análisis de información',
    'Plazo de cronograma': 'Plazo de cronograma',
    'Análisis y cronograma': 'Análisis y cronograma',
    'Seguimiento a los acuerdos': 'Seguimiento a los acuerdos',
    'Registro (completo)': 'Registro (completo)',
    'ET (completo)': 'ET (completo)',
    'CO (completo)': 'CO (completo)',
    'DD (completo)': 'DD (completo)',
    'REC (completo)': 'REC (completo)',
    'SERVICIO (completo)': 'SERVICIO (completo)',
    'Estándares': 'Estándares',
    'Resultados de orientación técnica': 'Resultados de orientación técnica',
    'Verificación del servicio web geográfico': 'Verificación del servicio web geográfico',
    'Verificar Aprobar Resultados': 'Verificar Aprobar Resultados',
    'Revisar y validar los datos cargados en la base de datos': 'Revisar y validar los datos cargados en la base de datos',
    'Aprobación resultados obtenidos en la orientación': 'Aprobación resultados obtenidos en la orientación',
    'Disponer datos temáticos': 'Disponer datos temáticos',
    'Fecha de publicación programada': 'Fecha de publicación programada',
    'Publicación': 'Publicación',
    'Catálogo de recursos geográficos': 'Catálogo de recursos geográficos',
    'Plazo de oficio de cierre': 'Plazo de oficio de cierre',
    'Oficios de cierre': 'Oficios de cierre',
    'Fecha de oficio de cierre': 'Fecha de oficio de cierre',
    'Estado': 'Estado',
    'Observación': 'Observación',
    'Porcentaje Avance': 'Porcentaje Avance',
    'Mes Proyectado': 'Mes Proyectado',
    'Plazo de análisis': 'Plazo de análisis',
    'Registro': 'Registro',
    'ET': 'ET',
    'CO': 'CO',
    'DD': 'DD',
    'REC': 'REC',
    'SERVICIO': 'SERVICIO',
    'Estándares (fecha programada)': 'Estándares (fecha programada)'
}

# LISTAS DE MESES
MESES = [
    "", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
]

# LISTAS DE FRECUENCIA
FRECUENCIAS = [
    "", "Diaria", "Semanal", "Quincenal", "Mensual", "Bimestral", 
    "Trimestral", "Semestral", "Anual", "Eventual"
]

# OPCIONES DE SEGUIMIENTO
SEGUIMIENTO_OPCIONES = [
    "", "En seguimiento", "Completado", "Pendiente", "En revisión", 
    "Requiere acción", "Sin novedad"
]

# IMPORTS SEGUROS
try:
    from sheets_utils import GoogleSheetsManager
except ImportError:
    st.error("Error: No se puede importar GoogleSheetsManager")
    GoogleSheetsManager = None

def get_safe_value(row, column_name, default=''):
    """Obtiene un valor de forma segura del DataFrame"""
    try:
        if column_name in row.index:
            value = row[column_name]
            if pd.isna(value) or value is None:
                return default
            return str(value)
        return default
    except:
        return default

def safe_set_value(df, index, column_name, value):
    """Establece un valor de forma segura en el DataFrame"""
    try:
        if column_name in df.columns:
            df.iloc[index, df.columns.get_loc(column_name)] = value
        else:
            st.warning(f"Columna no encontrada: {column_name}")
    except Exception as e:
        st.error(f"Error al establecer valor en {column_name}: {e}")

def obtener_funcionarios_unicos(df):
    """Obtiene lista única de funcionarios"""
    if 'Funcionario' not in df.columns:
        return []
    
    funcionarios = df['Funcionario'].dropna().unique().tolist()
    funcionarios = [f for f in funcionarios if str(f).strip() and str(f).strip().lower() != 'nan']
    return sorted(list(set(funcionarios)))

def obtener_entidades_unicas(df):
    """Obtiene lista única de entidades"""
    if 'Entidad' not in df.columns:
        return []
    
    entidades = df['Entidad'].dropna().unique().tolist()
    entidades = [e for e in entidades if str(e).strip() and str(e).strip().lower() != 'nan']
    return sorted(list(set(entidades)))

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
    """Convierte string a objeto date - CORREGIDO para manejar campos vacíos"""
    if not fecha_str or not fecha_str.strip() or fecha_str.strip() == "":
        return None
    
    try:
        # Intentar varios formatos
        formatos = ["%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"]
        for formato in formatos:
            try:
                return datetime.strptime(fecha_str.strip(), formato).date()
            except:
                continue
        return None
    except:
        return None

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

def borrar_registro(df, indice):
    """Borra un registro del DataFrame"""
    try:
        df_nuevo = df.drop(df.index[indice]).reset_index(drop=True)
        return df_nuevo
    except Exception as e:
        st.error(f"Error al borrar registro: {str(e)}")
        return df

def cargar_desde_sheets():
    """Carga datos desde Google Sheets"""
    if GoogleSheetsManager is None:
        st.error("GoogleSheetsManager no disponible")
        return pd.DataFrame()
    
    try:
        manager = GoogleSheetsManager()
        df = manager.leer_hoja("Registros")
        
        if df.empty:
            st.warning("La hoja Registros está vacía")
            return pd.DataFrame()
        
        st.success(f"Datos cargados: {len(df)} registros")
        return df
        
    except Exception as e:
        st.error(f"Error cargando datos: {str(e)}")
        return pd.DataFrame()

def guardar_en_sheets(df):
    """Guarda datos en Google Sheets - SOLO hoja Registros - MEJORADO"""
    if GoogleSheetsManager is None:
        return False, "GoogleSheetsManager no disponible"
    
    try:
        manager = GoogleSheetsManager()
        
        # Verificar que el DataFrame no esté vacío
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
        total_campos = 4
        
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

def mostrar_formulario(row, indice, es_nuevo=False, df=None):
    """Formulario limpio con mejoras solicitadas"""
    
    # Obtener listas únicas para desplegables
    funcionarios_existentes = obtener_funcionarios_unicos(df) if df is not None else []
    entidades_existentes = obtener_entidades_unicas(df) if df is not None else []
    frecuencias_existentes = obtener_frecuencias_unicas(df) if df is not None else []
    seguimientos_existentes = obtener_seguimientos_unicos(df) if df is not None else []
    
    # INFORMACIÓN BÁSICA
    st.subheader("Información Básica")
    col1, col2 = st.columns(2)
    
    with col1:
        codigo = st.text_input("Código", 
            value=get_safe_value(row, 'Cod'),
            disabled=es_nuevo,
            key=f"cod_{indice}")
        
        # ENTIDAD - Lista desplegable editable
        entidad_actual = get_safe_value(row, 'Entidad')
        if entidad_actual and entidad_actual not in entidades_existentes:
            entidades_existentes.insert(0, entidad_actual)
        
        entidad_index = entidades_existentes.index(entidad_actual) if entidad_actual in entidades_existentes else 0
        entidad = st.selectbox("Entidad",
            options=["-- Seleccionar --"] + entidades_existentes + ["-- Agregar nueva --"],
            index=entidad_index + 1 if entidad_actual in entidades_existentes else 0,
            key=f"entidad_select_{indice}")
        
        if entidad == "-- Agregar nueva --":
            entidad = st.text_input("Nueva entidad:",
                key=f"entidad_nueva_{indice}")
        elif entidad == "-- Seleccionar --":
            entidad = ""
        
        # FUNCIONARIO - Lista desplegable editable
        funcionario_actual = get_safe_value(row, 'Funcionario')
        if funcionario_actual and funcionario_actual not in funcionarios_existentes:
            funcionarios_existentes.insert(0, funcionario_actual)
        
        funcionario_index = funcionarios_existentes.index(funcionario_actual) if funcionario_actual in funcionarios_existentes else 0
        funcionario = st.selectbox("Funcionario",
            options=["-- Seleccionar --"] + funcionarios_existentes + ["-- Agregar nuevo --"],
            index=funcionario_index + 1 if funcionario_actual in funcionarios_existentes else 0,
            key=f"funcionario_select_{indice}")
        
        if funcionario == "-- Agregar nuevo --":
            funcionario = st.text_input("Nuevo funcionario:",
                key=f"funcionario_nuevo_{indice}")
        elif funcionario == "-- Seleccionar --":
            funcionario = ""
    
    with col2:
        nivel_info = st.text_input("Nivel de Información",
            value=get_safe_value(row, 'Nivel Información '),
            key=f"nivel_{indice}")
        
        # TIPO DE DATO - Solo "Actualizar" y "Nuevo"
        tipo_actual = get_safe_value(row, 'TipoDato')
        tipo_opciones = ["", "Actualizar", "Nuevo"]
        tipo_index = tipo_opciones.index(tipo_actual) if tipo_actual in tipo_opciones else 0
        
        tipo_dato = st.selectbox("Tipo de Dato",
            options=tipo_opciones,
            index=tipo_index,
            key=f"tipo_{indice}")
        
        # FRECUENCIA - Lista desplegable editable
        frecuencia_actual = get_safe_value(row, 'Frecuencia actualizacion ')
        
        # Combinar frecuencias predefinidas con existentes
        todas_frecuencias = FRECUENCIAS.copy()
        for freq in frecuencias_existentes:
            if freq and freq not in todas_frecuencias:
                todas_frecuencias.append(freq)
        
        frecuencia_index = todas_frecuencias.index(frecuencia_actual) if frecuencia_actual in todas_frecuencias else 0
        frecuencia = st.selectbox("Frecuencia",
            options=["-- Seleccionar --"] + todas_frecuencias[1:] + ["-- Agregar nueva --"],
            index=frecuencia_index if frecuencia_actual in todas_frecuencias[1:] else 0,
            key=f"freq_{indice}")
        
        if frecuencia == "-- Agregar nueva --":
            frecuencia = st.text_input("Nueva frecuencia:",
                key=f"freq_nueva_{indice}")
        elif frecuencia == "-- Seleccionar --":
            frecuencia = ""
    
    # MES PROYECTADO - Lista desplegable de meses
    mes_actual = get_safe_value(row, 'Mes Proyectado')
    mes_index = MESES.index(mes_actual) if mes_actual in MESES else 0
    
    mes_proyectado = st.selectbox("Mes Proyectado",
        options=MESES,
        index=mes_index,
        key=f"mes_{indice}")
    
    # ACUERDOS
    st.subheader("Acuerdos y Compromisos")
    col1, col2 = st.columns(2)
    
    with col1:
        actas_interes = st.selectbox("Actas de interés",
            options=["", "Si", "No"],
            index=0 if not get_safe_value(row, 'Actas de acercamiento y manifestación de interés') else
                  ["", "Si", "No"].index(get_safe_value(row, 'Actas de acercamiento y manifestación de interés'))
                  if get_safe_value(row, 'Actas de acercamiento y manifestación de interés') in ["", "Si", "No"] else 0,
            key=f"actas_{indice}")
        
        acuerdo_compromiso = st.selectbox("Acuerdo de compromiso",
            options=["", "Si", "No"],
            index=0 if not get_safe_value(row, 'Acuerdo de compromiso') else
                  ["", "Si", "No"].index(get_safe_value(row, 'Acuerdo de compromiso'))
                  if get_safe_value(row, 'Acuerdo de compromiso') in ["", "Si", "No"] else 0,
            key=f"acuerdo_{indice}")
    
    with col2:
        # FECHAS - Selectores de fecha (CORREGIDO para permitir borrado manual)
        suscripcion_fecha = string_a_fecha(get_safe_value(row, 'Suscripción acuerdo de compromiso'))
        suscripcion = st.date_input("Suscripción acuerdo",
            value=suscripcion_fecha,
            key=f"suscripcion_{indice}")
        # Permitir borrar fecha manualmente
        if st.checkbox(f"Borrar fecha suscripción", key=f"borrar_suscripcion_{indice}"):
            suscripcion = None
        
        entrega_fecha = string_a_fecha(get_safe_value(row, 'Entrega acuerdo de compromiso'))
        entrega_acuerdo = st.date_input("Entrega acuerdo",
            value=entrega_fecha,
            key=f"entrega_{indice}")
        # Permitir borrar fecha manualmente
        if st.checkbox(f"Borrar fecha entrega", key=f"borrar_entrega_{indice}"):
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
            key=f"acceso_{indice}")
        
        analisis_info = st.selectbox("Análisis de información",
            options=["", "Si", "No"],
            index=0 if not get_safe_value(row, ' Análisis de información') else
                  ["", "Si", "No"].index(get_safe_value(row, ' Análisis de información'))
                  if get_safe_value(row, ' Análisis de información') in ["", "Si", "No"] else 0,
            key=f"analisis_{indice}")
    
    with col2:
        cronograma = st.selectbox("Cronograma Concertado",
            options=["", "Si", "No"],
            index=0 if not get_safe_value(row, 'Cronograma Concertado') else
                  ["", "Si", "No"].index(get_safe_value(row, 'Cronograma Concertado'))
                  if get_safe_value(row, 'Cronograma Concertado') in ["", "Si", "No"] else 0,
            key=f"cronograma_{indice}")
        
        fecha_entrega_date = string_a_fecha(get_safe_value(row, 'Fecha de entrega de información'))
        fecha_entrega = st.date_input("Fecha entrega información",
            value=fecha_entrega_date,
            key=f"fecha_entrega_{indice}")
        # Permitir borrar fecha manualmente
        if st.checkbox(f"Borrar fecha entrega información", key=f"borrar_fecha_entrega_{indice}"):
            fecha_entrega = None
    
    # FECHAS PROGRAMADAS
    st.subheader("Fechas y Cronograma")
    col1, col2 = st.columns(2)
    
    with col1:
        analisis_prog_date = string_a_fecha(get_safe_value(row, 'Análisis y cronograma (fecha programada)'))
        analisis_programada = st.date_input("Análisis programada",
            value=analisis_prog_date,
            key=f"analisis_prog_{indice}")
        # Permitir borrar fecha manualmente
        if st.checkbox(f"Borrar fecha análisis programada", key=f"borrar_analisis_prog_{indice}"):
            analisis_programada = None
        
        analisis_real_date = string_a_fecha(get_safe_value(row, 'Análisis y cronograma'))
        analisis_real = st.date_input("Análisis real",
            value=analisis_real_date,
            key=f"analisis_real_{indice}")
        # Permitir borrar fecha manualmente
        if st.checkbox(f"Borrar fecha análisis real", key=f"borrar_analisis_real_{indice}"):
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
            options=["-- Seleccionar --"] + todos_seguimientos[1:] + ["-- Escribir otro --"],
            index=seguimiento_index if seguimiento_actual in todos_seguimientos[1:] else 0,
            key=f"seguimiento_select_{indice}")
        
        if seguimiento == "-- Escribir otro --":
            seguimiento = st.text_area("Otro seguimiento:",
                height=80,
                key=f"seguimiento_otro_{indice}")
        elif seguimiento == "-- Seleccionar --":
            seguimiento = ""
    
    # ESTÁNDARES
    st.subheader("Estándares")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        registro = st.selectbox("Registro",
            options=["", "Completo", "Incompleto"],
            index=0 if not get_safe_value(row, 'Registro (completo)') else
                  ["", "Completo", "Incompleto"].index(get_safe_value(row, 'Registro (completo)'))
                  if get_safe_value(row, 'Registro (completo)') in ["", "Completo", "Incompleto"] else 0,
            key=f"registro_{indice}")
        
        et = st.selectbox("ET",
            options=["", "Completo", "Incompleto"],
            index=0 if not get_safe_value(row, 'ET (completo)') else
                  ["", "Completo", "Incompleto"].index(get_safe_value(row, 'ET (completo)'))
                  if get_safe_value(row, 'ET (completo)') in ["", "Completo", "Incompleto"] else 0,
            key=f"et_{indice}")
    
    with col2:
        co = st.selectbox("CO",
            options=["", "Completo", "Incompleto"],
            index=0 if not get_safe_value(row, 'CO (completo)') else
                  ["", "Completo", "Incompleto"].index(get_safe_value(row, 'CO (completo)'))
                  if get_safe_value(row, 'CO (completo)') in ["", "Completo", "Incompleto"] else 0,
            key=f"co_{indice}")
        
        dd = st.selectbox("DD",
            options=["", "Completo", "Incompleto"],
            index=0 if not get_safe_value(row, 'DD (completo)') else
                  ["", "Completo", "Incompleto"].index(get_safe_value(row, 'DD (completo)'))
                  if get_safe_value(row, 'DD (completo)') in ["", "Completo", "Incompleto"] else 0,
            key=f"dd_{indice}")
    
    with col3:
        rec = st.selectbox("REC",
            options=["", "Completo", "Incompleto"],
            index=0 if not get_safe_value(row, 'REC (completo)') else
                  ["", "Completo", "Incompleto"].index(get_safe_value(row, 'REC (completo)'))
                  if get_safe_value(row, 'REC (completo)') in ["", "Completo", "Incompleto"] else 0,
            key=f"rec_{indice}")
        
        servicio = st.selectbox("SERVICIO",
            options=["", "Completo", "Incompleto"],
            index=0 if not get_safe_value(row, 'SERVICIO (completo)') else
                  ["", "Completo", "Incompleto"].index(get_safe_value(row, 'SERVICIO (completo)'))
                  if get_safe_value(row, 'SERVICIO (completo)') in ["", "Completo", "Incompleto"] else 0,
            key=f"servicio_{indice}")
    
    # FECHAS DE ESTÁNDARES
    col1, col2 = st.columns(2)
    with col1:
        est_prog_date = string_a_fecha(get_safe_value(row, 'Estándares (fecha programada)'))
        estandares_prog = st.date_input("Estándares programada",
            value=est_prog_date,
            key=f"est_prog_{indice}")
        # Permitir borrar fecha manualmente
        if st.checkbox(f"Borrar fecha estándares programada", key=f"borrar_est_prog_{indice}"):
            estandares_prog = None
    
    with col2:
        est_real_date = string_a_fecha(get_safe_value(row, 'Estándares'))
        estandares_real = st.date_input("Estándares real",
            value=est_real_date,
            key=f"est_real_{indice}")
        # Permitir borrar fecha manualmente
        if st.checkbox(f"Borrar fecha estándares real", key=f"borrar_est_real_{indice}"):
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
            key=f"orientacion_{indice}")
        
        verificacion_web = st.selectbox("Verificación servicio web",
            options=["", "Si", "No"],
            index=0 if not get_safe_value(row, 'Verificación del servicio web geográfico') else
                  ["", "Si", "No"].index(get_safe_value(row, 'Verificación del servicio web geográfico'))
                  if get_safe_value(row, 'Verificación del servicio web geográfico') in ["", "Si", "No"] else 0,
            key=f"verificacion_{indice}")
    
    with col2:
        verificar_aprobar = st.selectbox("Verificar Aprobar",
            options=["", "Si", "No"],
            index=0 if not get_safe_value(row, 'Verificar Aprobar Resultados') else
                  ["", "Si", "No"].index(get_safe_value(row, 'Verificar Aprobar Resultados'))
                  if get_safe_value(row, 'Verificar Aprobar Resultados') in ["", "Si", "No"] else 0,
            key=f"aprobar_{indice}")
        
        revisar_validar = st.selectbox("Revisar y validar",
            options=["", "Si", "No"],
            index=0 if not get_safe_value(row, 'Revisar y validar los datos cargados en la base de datos') else
                  ["", "Si", "No"].index(get_safe_value(row, 'Revisar y validar los datos cargados en la base de datos'))
                  if get_safe_value(row, 'Revisar y validar los datos cargados en la base de datos') in ["", "Si", "No"] else 0,
            key=f"revisar_{indice}")
    
    aprobacion = st.selectbox("Aprobación resultados",
        options=["", "Si", "No"],
        index=0 if not get_safe_value(row, 'Aprobación resultados obtenidos en la orientación') else
              ["", "Si", "No"].index(get_safe_value(row, 'Aprobación resultados obtenidos en la orientación'))
              if get_safe_value(row, 'Aprobación resultados obtenidos en la orientación') in ["", "Si", "No"] else 0,
        key=f"aprobacion_{indice}")
    
    # PUBLICACIÓN
    st.subheader("Publicación")
    col1, col2 = st.columns(2)
    
    with col1:
        pub_prog_date = string_a_fecha(get_safe_value(row, 'Fecha de publicación programada'))
        pub_programada = st.date_input("Publicación programada",
            value=pub_prog_date,
            key=f"pub_prog_{indice}")
        # Permitir borrar fecha manualmente
        if st.checkbox(f"Borrar fecha publicación programada", key=f"borrar_pub_prog_{indice}"):
            pub_programada = None
        
        pub_real_date = string_a_fecha(get_safe_value(row, 'Publicación'))
        publicacion = st.date_input("Publicación real",
            value=pub_real_date,
            key=f"publicacion_{indice}")
        # Permitir borrar fecha manualmente
        if st.checkbox(f"Borrar fecha publicación real", key=f"borrar_publicacion_{indice}"):
            publicacion = None
    
    with col2:
        disponer_datos = st.selectbox("Disponer datos temáticos",
            options=["", "Si", "No"],
            index=0 if not get_safe_value(row, 'Disponer datos temáticos') else
                  ["", "Si", "No"].index(get_safe_value(row, 'Disponer datos temáticos'))
                  if get_safe_value(row, 'Disponer datos temáticos') in ["", "Si", "No"] else 0,
            key=f"disponer_{indice}")
        
        catalogo = st.selectbox("Catálogo recursos",
            options=["", "Si", "No"],
            index=0 if not get_safe_value(row, 'Catálogo de recursos geográficos') else
                  ["", "Si", "No"].index(get_safe_value(row, 'Catálogo de recursos geográficos'))
                  if get_safe_value(row, 'Catálogo de recursos geográficos') in ["", "Si", "No"] else 0,
            key=f"catalogo_{indice}")
    
    # CIERRE
    st.subheader("Cierre")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        oficios_cierre = st.selectbox("Oficios de cierre",
            options=["", "Si", "No"],
            index=0 if not get_safe_value(row, 'Oficios de cierre') else
                  ["", "Si", "No"].index(get_safe_value(row, 'Oficios de cierre'))
                  if get_safe_value(row, 'Oficios de cierre') in ["", "Si", "No"] else 0,
            key=f"oficios_{indice}")
    
    with col2:
        fecha_oficio_date = string_a_fecha(get_safe_value(row, 'Fecha de oficio de cierre'))
        fecha_oficio = st.date_input("Fecha oficio cierre",
            value=fecha_oficio_date,
            key=f"fecha_oficio_{indice}")
        # Permitir borrar fecha manualmente
        if st.checkbox(f"Borrar fecha oficio cierre", key=f"borrar_fecha_oficio_{indice}"):
            fecha_oficio = None
    
    with col3:
        estado = st.selectbox("Estado",
            options=["", "Completado", "En proceso", "Pendiente"],
            index=0 if not get_safe_value(row, 'Estado') else
                  ["", "Completado", "En proceso", "Pendiente"].index(get_safe_value(row, 'Estado'))
                  if get_safe_value(row, 'Estado') in ["", "Completado", "En proceso", "Pendiente"] else 0,
            key=f"estado_{indice}")
    
    # PLAZOS (solo lectura)
    st.subheader("Plazos Calculados")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.text_input("Plazo análisis",
            value=get_safe_value(row, 'Plazo de análisis'),
            disabled=True)
    
    with col2:
        st.text_input("Plazo cronograma",
            value=get_safe_value(row, 'Plazo de cronograma'),
            disabled=True)
    
    with col3:
        st.text_input("Plazo oficio cierre",
            value=get_safe_value(row, 'Plazo de oficio de cierre'),
            disabled=True)
    
    # OBSERVACIONES
    st.subheader("Observaciones")
    observacion = st.text_area("Observaciones",
        value=get_safe_value(row, 'Observación'),
        height=100,
        key=f"obs_{indice}")
    
    # AVANCE (solo lectura)
    avance_actual = calcular_avance(row)
    st.text_input("Porcentaje de Avance",
        value=f"{avance_actual}%",
        disabled=True)
    
    # Retornar valores del formulario
    return {
        'Cod': codigo,
        'Funcionario': funcionario,
        'Entidad': entidad,
        'Nivel Información ': nivel_info,
        'Frecuencia actualizacion ': frecuencia,
        'TipoDato': tipo_dato,
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
        'Observación': observacion,
        'Mes Proyectado': mes_proyectado
    }

def mostrar_edicion_registros(registros_df):
    """Editor principal limpio"""
    
    st.title("Editor de Registros")
    
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
            key="busqueda_registro"
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
        
        seleccion = st.selectbox("Seleccionar registro:", opciones_mostrar)
        
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
            # BOTÓN DE BORRAR REGISTRO MEJORADO
            if st.button("Borrar Registro", type="secondary", help="Eliminar este registro permanentemente"):
                # Usar un modal simulado con session_state
                st.session_state.confirmar_borrado = True
                st.session_state.registro_a_borrar = indice_real
        
        # CONFIRMACIÓN DE BORRADO
        if st.session_state.get('confirmar_borrado', False):
            st.warning("⚠️ ADVERTENCIA: ¿Desea borrar este registro? Este cambio no se puede deshacer.")
            
            col_confirm1, col_confirm2 = st.columns(2)
            
            with col_confirm1:
                if st.button("SÍ, BORRAR", type="primary", key="confirmar_borrar_definitivo"):
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
                if st.button("Cancelar", key="cancelar_borrar"):
                    # Limpiar confirmación
                    del st.session_state.confirmar_borrado
                    if 'registro_a_borrar' in st.session_state:
                        del st.session_state.registro_a_borrar
                    st.rerun()
        
        # Formulario de edición (solo mostrar si no está en modo confirmación)
        if not st.session_state.get('confirmar_borrado', False):
            with st.form("form_editar"):
                valores = mostrar_formulario(row_seleccionada, indice_real, False, registros_df)
                
                if st.form_submit_button("Guardar Cambios", type="primary"):
                    try:
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
        
        with st.form("form_nuevo"):
            valores_nuevo = mostrar_formulario(registro_vacio, "nuevo", True, registros_df)
            
            if st.form_submit_button("Crear Registro", type="primary"):
                try:
                    # Validar campos obligatorios
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
                if st.button("Verificar Google Sheets"):
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
