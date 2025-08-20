# editor_final.py - EDITOR LIMPIO Y FUNCIONAL
"""
Editor limpio que funciona con Google Sheets
Mapeo correcto de columnas del archivo real
"""

import streamlit as st
import pandas as pd
from datetime import datetime
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
    """Guarda datos en Google Sheets - SOLO hoja Registros"""
    if GoogleSheetsManager is None:
        return False, "GoogleSheetsManager no disponible"
    
    try:
        manager = GoogleSheetsManager()
        
        # SOLO escribir en Registros
        exito = manager.escribir_hoja(df, "Registros", limpiar_hoja=True)
        
        if exito:
            return True, "Datos guardados en Google Sheets"
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

def mostrar_formulario(row, indice, es_nuevo=False):
    """Formulario limpio sin íconos"""
    
    # INFORMACIÓN BÁSICA
    st.subheader("Información Básica")
    col1, col2 = st.columns(2)
    
    with col1:
        codigo = st.text_input("Código", 
            value=get_safe_value(row, 'Cod'),
            disabled=es_nuevo,
            key=f"cod_{indice}")
        
        entidad = st.text_input("Entidad",
            value=get_safe_value(row, 'Entidad'),
            key=f"entidad_{indice}")
        
        funcionario = st.text_input("Funcionario",
            value=get_safe_value(row, 'Funcionario'),
            key=f"funcionario_{indice}")
    
    with col2:
        nivel_info = st.text_input("Nivel de Información",
            value=get_safe_value(row, 'Nivel Información '),
            key=f"nivel_{indice}")
        
        tipo_dato = st.selectbox("Tipo de Dato",
            options=["", "Actualizar", "Crear", "Mantener"],
            index=0 if not get_safe_value(row, 'TipoDato') else 
                  ["", "Actualizar", "Crear", "Mantener"].index(get_safe_value(row, 'TipoDato')) 
                  if get_safe_value(row, 'TipoDato') in ["", "Actualizar", "Crear", "Mantener"] else 0,
            key=f"tipo_{indice}")
        
        frecuencia = st.text_input("Frecuencia",
            value=get_safe_value(row, 'Frecuencia actualizacion '),
            key=f"freq_{indice}")
    
    mes_proyectado = st.text_input("Mes Proyectado",
        value=get_safe_value(row, 'Mes Proyectado'),
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
        suscripcion = st.text_input("Suscripción acuerdo (fecha)",
            value=get_safe_value(row, 'Suscripción acuerdo de compromiso'),
            key=f"suscripcion_{indice}")
        
        entrega_acuerdo = st.text_input("Entrega acuerdo (fecha)",
            value=get_safe_value(row, 'Entrega acuerdo de compromiso'),
            key=f"entrega_{indice}")
    
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
        
        fecha_entrega = st.text_input("Fecha entrega información",
            value=get_safe_value(row, 'Fecha de entrega de información'),
            key=f"fecha_entrega_{indice}")
    
    # FECHAS PROGRAMADAS
    st.subheader("Fechas y Cronograma")
    col1, col2 = st.columns(2)
    
    with col1:
        analisis_programada = st.text_input("Análisis programada",
            value=get_safe_value(row, 'Análisis y cronograma (fecha programada)'),
            key=f"analisis_prog_{indice}")
        
        analisis_real = st.text_input("Análisis real",
            value=get_safe_value(row, 'Análisis y cronograma'),
            key=f"analisis_real_{indice}")
    
    with col2:
        seguimiento = st.text_area("Seguimiento acuerdos",
            value=get_safe_value(row, 'Seguimiento a los acuerdos'),
            height=80,
            key=f"seguimiento_{indice}")
    
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
        estandares_prog = st.text_input("Estándares programada",
            value=get_safe_value(row, 'Estándares (fecha programada)'),
            key=f"est_prog_{indice}")
    
    with col2:
        estandares_real = st.text_input("Estándares real",
            value=get_safe_value(row, 'Estándares'),
            key=f"est_real_{indice}")
    
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
        pub_programada = st.text_input("Publicación programada",
            value=get_safe_value(row, 'Fecha de publicación programada'),
            key=f"pub_prog_{indice}")
        
        publicacion = st.text_input("Publicación real",
            value=get_safe_value(row, 'Publicación'),
            key=f"publicacion_{indice}")
    
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
        fecha_oficio = st.text_input("Fecha oficio cierre",
            value=get_safe_value(row, 'Fecha de oficio de cierre'),
            key=f"fecha_oficio_{indice}")
    
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
        'Suscripción acuerdo de compromiso': suscripcion,
        'Entrega acuerdo de compromiso': entrega_acuerdo,
        'Acuerdo de compromiso': acuerdo_compromiso,
        'Gestion acceso a los datos y documentos requeridos ': acceso_datos,
        ' Análisis de información': analisis_info,
        'Cronograma Concertado': cronograma,
        'Análisis y cronograma (fecha programada)': analisis_programada,
        'Fecha de entrega de información': fecha_entrega,
        'Análisis y cronograma': analisis_real,
        'Seguimiento a los acuerdos': seguimiento,
        'Registro (completo)': registro,
        'ET (completo)': et,
        'CO (completo)': co,
        'DD (completo)': dd,
        'REC (completo)': rec,
        'SERVICIO (completo)': servicio,
        'Estándares (fecha programada)': estandares_prog,
        'Estándares': estandares_real,
        'Resultados de orientación técnica': orientacion,
        'Verificación del servicio web geográfico': verificacion_web,
        'Verificar Aprobar Resultados': verificar_aprobar,
        'Revisar y validar los datos cargados en la base de datos': revisar_validar,
        'Aprobación resultados obtenidos en la orientación': aprobacion,
        'Fecha de publicación programada': pub_programada,
        'Publicación': publicacion,
        'Disponer datos temáticos': disponer_datos,
        'Catálogo de recursos geográficos': catalogo,
        'Oficios de cierre': oficios_cierre,
        'Fecha de oficio de cierre': fecha_oficio,
        'Estado': estado,
        'Observación': observacion,
        'Mes Proyectado': mes_proyectado
    }

def mostrar_edicion_registros(registros_df):
    """Editor principal limpio"""
    
    st.title("Editor de Registros")
    
    # Controles principales
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        if st.button("Cargar desde Google Sheets"):
            with st.spinner("Cargando datos..."):
                registros_df = cargar_desde_sheets()
                if not registros_df.empty:
                    st.session_state['registros_df'] = registros_df
                    st.rerun()
    
    with col2:
        total = len(registros_df) if not registros_df.empty else 0
        st.metric("Total Registros", total)
    
    with col3:
        if 'ultimo_guardado' in st.session_state:
            st.success(f"Último guardado: {st.session_state.ultimo_guardado}")
    
    if registros_df.empty:
        st.warning("No hay datos disponibles. Usa 'Cargar desde Google Sheets'")
        return registros_df
    
    # Pestañas
    tab1, tab2 = st.tabs(["Editar Existente", "Crear Nuevo"])
    
    with tab1:
        # Selector de registro
        opciones = [
            f"{row['Cod']} - {row['Entidad']}"
            for _, row in registros_df.iterrows()
        ]
        
        if not opciones:
            st.warning("No hay registros para editar")
            return registros_df
        
        seleccion = st.selectbox("Seleccionar registro:", opciones)
        indice = opciones.index(seleccion)
        row_seleccionada = registros_df.iloc[indice]
        
        st.write(f"Editando: {row_seleccionada['Cod']} - {row_seleccionada['Entidad']}")
        
        # Formulario de edición
        with st.form("form_editar"):
            valores = mostrar_formulario(row_seleccionada, indice, False)
            
            if st.form_submit_button("Guardar Cambios", type="primary"):
                try:
                    # Actualizar registro
                    for campo, valor in valores.items():
                        if campo in registros_df.columns:
                            registros_df.iloc[indice, registros_df.columns.get_loc(campo)] = valor
                    
                    # Calcular nuevo avance
                    nuevo_avance = calcular_avance(registros_df.iloc[indice])
                    if 'Porcentaje Avance' in registros_df.columns:
                        registros_df.iloc[indice, registros_df.columns.get_loc('Porcentaje Avance')] = nuevo_avance
                    
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
            valores_nuevo = mostrar_formulario(registro_vacio, "nuevo", True)
            
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
            # Panel de diagnóstico
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
                
                st.info("Este editor SOLO modifica la hoja 'Registros', nunca 'Metas'")
            
            # Usar datos de session_state si están disponibles
            if 'registros_df' in st.session_state:
                registros_df = st.session_state['registros_df']
            
            return mostrar_edicion_registros(registros_df)
        else:
            st.subheader("Acceso Restringido")
            st.warning("Se requiere autenticación para editar registros")
            st.info("Use el panel 'Acceso Administrativo' en la barra lateral")
            return registros_df
            
    except ImportError:
        st.warning("Sistema de autenticación no disponible - Acceso directo")
        return mostrar_edicion_registros(registros_df)
