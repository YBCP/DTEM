# editor.py - CORREGIDO: Permitir ingreso de funcionarios/entidades nuevas
"""
Editor CORREGIDO - Permite agregar funcionarios y entidades nuevas:
- Funcionarios: Selectbox + opción "Agregar nuevo" + campo texto
- Entidades: Selectbox + opción "Agregar nueva" + campo texto  
- Diseño limpio sin iconos innecesarios
- Todas las funcionalidades mantenidas
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
    'Oficios de cierre': 'Oficios de cierre',
    'Fecha de oficio de cierre': 'Fecha de oficio de cierre',
    'Plazo de oficio de cierre': 'Plazo de oficio de cierre',
    'Estado': 'Estado',
    'Observación': 'Observación',
    'Mes Proyectado': 'Mes Proyectado'
}

# Imports de utilidades
try:
    from data_utils import (
        calcular_porcentaje_avance, 
        guardar_datos_editados,
        cargar_datos,
        procesar_metas
    )
    from validaciones_utils import validar_reglas_negocio
    from fecha_utils import (
        actualizar_plazo_analisis,
        actualizar_plazo_cronograma,
        actualizar_plazo_oficio_cierre
    )
    from sheets_utils import GoogleSheetsManager
except ImportError as e:
    st.error(f"Error importando utilidades: {e}")

# FUNCIONES DE UTILIDAD
def get_safe_value(row, column):
    """Obtiene valor seguro de una columna"""
    try:
        if pd.isna(row[column]):
            return ""
        return str(row[column])
    except:
        return ""

def fecha_a_string(fecha):
    """Convierte fecha a string de forma segura"""
    try:
        if pd.isna(fecha):
            return ""
        if isinstance(fecha, str):
            return fecha
        return fecha.strftime('%Y-%m-%d')
    except:
        return ""

def string_a_fecha(fecha_str):
    """Convierte string a fecha de forma segura"""
    try:
        if not fecha_str or fecha_str == "":
            return None
        return pd.to_datetime(fecha_str).date()
    except:
        return None

def obtener_funcionarios_unicos(df):
    """Obtiene lista única de funcionarios"""
    try:
        if 'Funcionario' in df.columns:
            funcionarios = df['Funcionario'].dropna().astype(str).unique()
            return sorted([f for f in funcionarios if f and f.strip() != ''])
        return []
    except:
        return []

def obtener_entidades_unicas(df):
    """Obtiene lista única de entidades"""
    try:
        if 'Entidad' in df.columns:
            entidades = df['Entidad'].dropna().astype(str).unique()
            return sorted([e for e in entidades if e and e.strip() != ''])
        return []
    except:
        return []

def generar_codigo(df):
    """Genera un nuevo código automático"""
    try:
        codigos_existentes = df['Cod'].astype(str).tolist()
        max_codigo = 0
        
        for cod in codigos_existentes:
            try:
                numero = int(cod)
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
        
        # Nivel de información
        nivel_info = st.text_input(
            "Nivel de Información:",
            value=get_safe_value(row, 'Nivel Información '),
            key=f"nivel_info_{key_base}"
        )
    
    # Campos adicionales
    col3, col4 = st.columns(2)
    
    with col3:
        frecuencia = st.text_input(
            "Frecuencia de Actualización:",
            value=get_safe_value(row, 'Frecuencia actualizacion '),
            key=f"frecuencia_{key_base}"
        )
    
    with col4:
        tipo_dato = st.selectbox(
            "Tipo de Dato:",
            ["NUEVO", "ACTUALIZAR"],
            index=0 if get_safe_value(row, 'TipoDato') == 'NUEVO' else 1,
            key=f"tipo_dato_{key_base}"
        )
    
    # ======================
    # FECHAS Y ESTADOS
    # ======================
    st.markdown("#### Fechas y Estados")
    
    # Estados con selectbox
    estados_opciones = ["", "Completo", "En proceso", "Pendiente"]
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        acuerdo_compromiso = st.selectbox(
            "Acuerdo de compromiso:",
            estados_opciones,
            index=estados_opciones.index(get_safe_value(row, 'Acuerdo de compromiso')) if get_safe_value(row, 'Acuerdo de compromiso') in estados_opciones else 0,
            key=f"acuerdo_{key_base}"
        )
        
        seguimiento = st.selectbox(
            "Seguimiento a los acuerdos:",
            estados_opciones,
            index=estados_opciones.index(get_safe_value(row, 'Seguimiento a los acuerdos')) if get_safe_value(row, 'Seguimiento a los acuerdos') in estados_opciones else 0,
            key=f"seguimiento_{key_base}"
        )
    
    with col2:
        registro = st.selectbox(
            "Registro (completo):",
            estados_opciones,
            index=estados_opciones.index(get_safe_value(row, 'Registro (completo)')) if get_safe_value(row, 'Registro (completo)') in estados_opciones else 0,
            key=f"registro_{key_base}"
        )
        
        et = st.selectbox(
            "ET (completo):",
            estados_opciones,
            index=estados_opciones.index(get_safe_value(row, 'ET (completo)')) if get_safe_value(row, 'ET (completo)') in estados_opciones else 0,
            key=f"et_{key_base}"
        )
    
    with col3:
        co = st.selectbox(
            "CO (completo):",
            estados_opciones,
            index=estados_opciones.index(get_safe_value(row, 'CO (completo)')) if get_safe_value(row, 'CO (completo)') in estados_opciones else 0,
            key=f"co_{key_base}"
        )
        
        dd = st.selectbox(
            "DD (completo):",
            estados_opciones,
            index=estados_opciones.index(get_safe_value(row, 'DD (completo)')) if get_safe_value(row, 'DD (completo)') in estados_opciones else 0,
            key=f"dd_{key_base}"
        )
    
    # Más estados
    col4, col5, col6 = st.columns(3)
    
    with col4:
        rec = st.selectbox(
            "REC (completo):",
            estados_opciones,
            index=estados_opciones.index(get_safe_value(row, 'REC (completo)')) if get_safe_value(row, 'REC (completo)') in estados_opciones else 0,
            key=f"rec_{key_base}"
        )
        
        servicio = st.selectbox(
            "SERVICIO (completo):",
            estados_opciones,
            index=estados_opciones.index(get_safe_value(row, 'SERVICIO (completo)')) if get_safe_value(row, 'SERVICIO (completo)') in estados_opciones else 0,
            key=f"servicio_{key_base}"
        )
    
    with col5:
        orientacion = st.selectbox(
            "Resultados de orientación técnica:",
            estados_opciones,
            index=estados_opciones.index(get_safe_value(row, 'Resultados de orientación técnica')) if get_safe_value(row, 'Resultados de orientación técnica') in estados_opciones else 0,
            key=f"orientacion_{key_base}"
        )
        
        verificacion_web = st.selectbox(
            "Verificación del servicio web geográfico:",
            estados_opciones,
            index=estados_opciones.index(get_safe_value(row, 'Verificación del servicio web geográfico')) if get_safe_value(row, 'Verificación del servicio web geográfico') in estados_opciones else 0,
            key=f"verificacion_web_{key_base}"
        )
    
    with col6:
        verificar_aprobar = st.selectbox(
            "Verificar Aprobar Resultados:",
            estados_opciones,
            index=estados_opciones.index(get_safe_value(row, 'Verificar Aprobar Resultados')) if get_safe_value(row, 'Verificar Aprobar Resultados') in estados_opciones else 0,
            key=f"verificar_aprobar_{key_base}"
        )
        
        revisar_validar = st.selectbox(
            "Revisar y validar los datos cargados en la base de datos:",
            estados_opciones,
            index=estados_opciones.index(get_safe_value(row, 'Revisar y validar los datos cargados en la base de datos')) if get_safe_value(row, 'Revisar y validar los datos cargados en la base de datos') in estados_opciones else 0,
            key=f"revisar_validar_{key_base}"
        )
    
    # Estados finales
    col7, col8, col9 = st.columns(3)
    
    with col7:
        aprobacion = st.selectbox(
            "Aprobación resultados obtenidos en la orientación:",
            estados_opciones,
            index=estados_opciones.index(get_safe_value(row, 'Aprobación resultados obtenidos en la orientación')) if get_safe_value(row, 'Aprobación resultados obtenidos en la orientación') in estados_opciones else 0,
            key=f"aprobacion_{key_base}"
        )
        
        disponer_datos = st.selectbox(
            "Disponer datos temáticos:",
            estados_opciones,
            index=estados_opciones.index(get_safe_value(row, 'Disponer datos temáticos')) if get_safe_value(row, 'Disponer datos temáticos') in estados_opciones else 0,
            key=f"disponer_datos_{key_base}"
        )
    
    with col8:
        catalogo = st.selectbox(
            "Catálogo de recursos geográficos:",
            estados_opciones,
            index=estados_opciones.index(get_safe_value(row, 'Catálogo de recursos geográficos')) if get_safe_value(row, 'Catálogo de recursos geográficos') in estados_opciones else 0,
            key=f"catalogo_{key_base}"
        )
        
        oficios_cierre = st.selectbox(
            "Oficios de cierre:",
            estados_opciones,
            index=estados_opciones.index(get_safe_value(row, 'Oficios de cierre')) if get_safe_value(row, 'Oficios de cierre') in estados_opciones else 0,
            key=f"oficios_cierre_{key_base}"
        )
    
    with col9:
        estado = st.selectbox(
            "Estado:",
            ["", "Finalizado", "En proceso", "Pendiente"],
            index=["", "Finalizado", "En proceso", "Pendiente"].index(get_safe_value(row, 'Estado')) if get_safe_value(row, 'Estado') in ["", "Finalizado", "En proceso", "Pendiente"] else 0,
            key=f"estado_{key_base}"
        )
        
        mes_proyectado = st.selectbox(
            "Mes Proyectado:",
            ["", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"],
            index=["", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"].index(get_safe_value(row, 'Mes Proyectado')) if get_safe_value(row, 'Mes Proyectado') in ["", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"] else 0,
            key=f"mes_proyectado_{key_base}"
        )
    
    # ======================
    # FECHAS PROGRAMADAS Y REALES
    # ======================
    st.markdown("#### Fechas Programadas y Reales")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Fechas de análisis
        try:
            fecha_analisis_prog = string_a_fecha(get_safe_value(row, 'Análisis y cronograma (fecha programada)'))
            analisis_programada = st.date_input(
                "Análisis y cronograma (fecha programada):",
                value=fecha_analisis_prog if fecha_analisis_prog else date.today(),
                key=f"analisis_prog_{key_base}"
            )
        except:
            analisis_programada = st.date_input(
                "Análisis y cronograma (fecha programada):",
                value=date.today(),
                key=f"analisis_prog_{key_base}"
            )
        
        try:
            fecha_entrega = string_a_fecha(get_safe_value(row, 'Fecha de entrega de información'))
            fecha_entrega = st.date_input(
                "Fecha de entrega de información:",
                value=fecha_entrega if fecha_entrega else date.today(),
                key=f"fecha_entrega_{key_base}"
            )
        except:
            fecha_entrega = st.date_input(
                "Fecha de entrega de información:",
                value=date.today(),
                key=f"fecha_entrega_{key_base}"
            )
        
        try:
            fecha_analisis_real = string_a_fecha(get_safe_value(row, 'Análisis y cronograma'))
            analisis_real = st.date_input(
                "Análisis y cronograma:",
                value=fecha_analisis_real if fecha_analisis_real else date.today(),
                key=f"analisis_real_{key_base}"
            )
        except:
            analisis_real = st.date_input(
                "Análisis y cronograma:",
                value=date.today(),
                key=f"analisis_real_{key_base}"
            )
    
    with col2:
        # Fechas de estándares
        try:
            fecha_estandares_prog = string_a_fecha(get_safe_value(row, 'Estándares (fecha programada)'))
            estandares_prog = st.date_input(
                "Estándares (fecha programada):",
                value=fecha_estandares_prog if fecha_estandares_prog else date.today(),
                key=f"estandares_prog_{key_base}"
            )
        except:
            estandares_prog = st.date_input(
                "Estándares (fecha programada):",
                value=date.today(),
                key=f"estandares_prog_{key_base}"
            )
        
        try:
            fecha_estandares_real = string_a_fecha(get_safe_value(row, 'Estándares'))
            estandares_real = st.date_input(
                "Estándares:",
                value=fecha_estandares_real if fecha_estandares_real else date.today(),
                key=f"estandares_real_{key_base}"
            )
        except:
            estandares_real = st.date_input(
                "Estándares:",
                value=date.today(),
                key=f"estandares_real_{key_base}"
            )
    
    with col3:
        # Fechas de publicación
        try:
            fecha_pub_prog = string_a_fecha(get_safe_value(row, 'Fecha de publicación programada'))
            pub_programada = st.date_input(
                "Fecha de publicación programada:",
                value=fecha_pub_prog if fecha_pub_prog else date.today(),
                key=f"pub_prog_{key_base}"
            )
        except:
            pub_programada = st.date_input(
                "Fecha de publicación programada:",
                value=date.today(),
                key=f"pub_prog_{key_base}"
            )
        
        try:
            fecha_publicacion = string_a_fecha(get_safe_value(row, 'Publicación'))
            publicacion = st.date_input(
                "Publicación:",
                value=fecha_publicacion if fecha_publicacion else date.today(),
                key=f"publicacion_{key_base}"
            )
        except:
            publicacion = st.date_input(
                "Publicación:",
                value=date.today(),
                key=f"publicacion_{key_base}"
            )
        
        try:
            fecha_oficio = string_a_fecha(get_safe_value(row, 'Fecha de oficio de cierre'))
            fecha_oficio = st.date_input(
                "Fecha de oficio de cierre:",
                value=fecha_oficio if fecha_oficio else date.today(),
                key=f"fecha_oficio_{key_base}"
            )
        except:
            fecha_oficio = st.date_input(
                "Fecha de oficio de cierre:",
                value=date.today(),
                key=f"fecha_oficio_{key_base}"
            )
    
    # ======================
    # OBSERVACIONES
    # ======================
    st.markdown("#### Observaciones")
    observacion = st.text_area(
        "Observación:",
        value=get_safe_value(row, 'Observación'),
        height=100,
        key=f"observacion_{key_base}"
    )
    
    # Retornar todos los valores
    return {
        'Cod': codigo,
        'Funcionario': funcionario,
        'Entidad': entidad,
        'Nivel Información ': nivel_info,
        'Frecuencia actualizacion ': frecuencia,
        'TipoDato': tipo_dato,
        'Actas de acercamiento y manifestación de interés': get_safe_value(row, 'Actas de acercamiento y manifestación de interés'),
        'Suscripción acuerdo de compromiso': get_safe_value(row, 'Suscripción acuerdo de compromiso'),
        'Entrega acuerdo de compromiso': get_safe_value(row, 'Entrega acuerdo de compromiso'),
        'Acuerdo de compromiso': acuerdo_compromiso,
        'Gestion acceso a los datos y documentos requeridos ': get_safe_value(row, 'Gestion acceso a los datos y documentos requeridos '),
        ' Análisis de información': get_safe_value(row, ' Análisis de información'),
        'Cronograma Concertado': get_safe_value(row, 'Cronograma Concertado'),
        'Análisis y cronograma (fecha programada)': fecha_a_string(analisis_programada) if analisis_programada else "",
        'Fecha de entrega de información': fecha_a_string(fecha_entrega) if fecha_entrega else "",
        'Análisis de información': get_safe_value(row, 'Análisis de información'),
        'Plazo de cronograma': get_safe_value(row, 'Plazo de cronograma'),
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
        'Observación': observacion,
        'Mes Proyectado': mes_proyectado
    }

def mostrar_edicion_registros(registros_df):
    """Editor principal limpio"""
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
            key="busqueda_registro"
        )
        
        # SELECTOR DE REGISTRO MEJORADO CON INFORMACIÓN AMPLIADA
        if termino_busqueda:
            # Filtrar registros por búsqueda
            mask = (
                registros_df['Cod'].astype(str).str.contains(termino_busqueda, case=False, na=False) |
                registros_df['Entidad'].astype(str).str.contains(termino_busqueda, case=False, na=False) |
                registros_df['Funcionario'].astype(str).str.contains(termino_busqueda, case=False, na=False) |
                registros_df['Nivel Información '].astype(str).str.contains(termino_busqueda, case=False, na=False)
            )
            registros_filtrados = registros_df[mask]
        else:
            registros_filtrados = registros_df.head(20)  # Mostrar primeros 20 por defecto
        
        if registros_filtrados.empty:
            st.warning("No se encontraron registros")
        else:
            st.info(f"Mostrando {len(registros_filtrados)} registros")
            
            # Crear opciones del selectbox con información detallada
            opciones_registros = []
            for idx, row in registros_filtrados.iterrows():
                cod = get_safe_value(row, 'Cod')
                entidad = get_safe_value(row, 'Entidad')[:30] + "..." if len(get_safe_value(row, 'Entidad')) > 30 else get_safe_value(row, 'Entidad')
                funcionario = get_safe_value(row, 'Funcionario')
                nivel = get_safe_value(row, 'Nivel Información ')[:20] + "..." if len(get_safe_value(row, 'Nivel Información ')) > 20 else get_safe_value(row, 'Nivel Información ')
                
                opcion = f"{cod} | {entidad} | {funcionario} | {nivel}"
                opciones_registros.append((opcion, idx))
            
            # Selectbox para elegir registro
            if opciones_registros:
                registro_seleccionado = st.selectbox(
                    "Seleccionar registro para editar:",
                    options=[opcion[0] for opcion in opciones_registros],
                    key="selector_registro"
                )
                
                # Obtener el índice real del registro seleccionado
                indice_real = None
                for opcion, idx in opciones_registros:
                    if opcion == registro_seleccionado:
                        indice_real = idx
                        break
                
                if indice_real is not None:
                    # Mostrar información del registro seleccionado
                    row_seleccionada = registros_df.loc[indice_real]
                    
                    # INFORMACIÓN DEL REGISTRO SELECCIONADO
                    st.markdown("### Información del Registro")
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.info(f"**Código:** {get_safe_value(row_seleccionada, 'Cod')}")
                        st.info(f"**Funcionario:** {get_safe_value(row_seleccionada, 'Funcionario')}")
                    
                    with col2:
                        st.info(f"**Entidad:** {get_safe_value(row_seleccionada, 'Entidad')}")
                        st.info(f"**Nivel:** {get_safe_value(row_seleccionada, 'Nivel Información ')}")
                    
                    with col3:
                        st.info(f"**Estado:** {get_safe_value(row_seleccionada, 'Estado')}")
                        st.info(f"**Tipo:** {get_safe_value(row_seleccionada, 'TipoDato')}")
                    
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
    
    with tab2:
        mostrar_editor_nuevo_completo(registros_df)
    
    return st.session_state.get('registros_df', registros_df)

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
            st.session_state['registros_df'] = registros_df
            
            if cerrar:
                st.balloons()
                time.sleep(2)
            else:
                time.sleep(1)
            
            st.rerun()
        else:
            st.error(mensaje)
            
    except Exception as e:
        st.error(f"Error al procesar edición: {str(e)}")

def procesar_creacion_completa(registros_df, valores, crear_otro=False):
    """Procesa la creación de un nuevo registro"""
    try:
        # Validar campos obligatorios
        if not valores['Funcionario'] or not valores['Funcionario'].strip():
            st.error("El funcionario es obligatorio")
            return
        
        if not valores['Entidad'] or not valores['Entidad'].strip():
            st.error("La entidad es obligatoria")
            return
        
        # Verificar código único
        if valores['Cod'] in registros_df['Cod'].values:
            st.error("El código ya existe")
            return
        
        # Crear nuevo registro
        nuevo_registro = pd.DataFrame([valores])
        
        # Calcular avance inicial
        avance = calcular_porcentaje_avance(nuevo_registro.iloc[0])
        nuevo_registro.loc[0, 'Porcentaje Avance'] = avance
        
        # Agregar al DataFrame principal
        registros_df = pd.concat([registros_df, nuevo_registro], ignore_index=True)
        
        # Guardar cambios
        try:
            exito, mensaje = guardar_datos_editados(registros_df, crear_backup=True)
        except:
            exito, mensaje = guardar_en_sheets_local(registros_df)
        
        if exito:
            st.success(f"Registro {valores['Cod']} creado exitosamente. Avance inicial: {avance}%")
            st.session_state.ultimo_guardado = datetime.now().strftime("%H:%M:%S")
            st.session_state['registros_df'] = registros_df
            st.balloons()
            time.sleep(1)
            st.rerun()
        else:
            st.error(mensaje)
            
    except Exception as e:
        st.error(f"Error al crear registro: {str(e)}")

def procesar_creacion_multiple(registros_df, valores_base, cantidad, crear_otro=False):
    """Procesa la creación múltiple de registros"""
    try:
        registros_creados = 0
        
        for i in range(cantidad):
            # Clonar valores base
            valores = valores_base.copy()
            
            # Generar código único
            base_codigo = valores['Cod']
            if cantidad > 1:
                valores['Cod'] = f"{base_codigo}_{i+1:02d}"
            
            # Verificar que el código sea único
            if valores['Cod'] in registros_df['Cod'].values:
                continue
            
            # Crear registro
            nuevo_registro = pd.DataFrame([valores])
            avance = calcular_porcentaje_avance(nuevo_registro.iloc[0])
            nuevo_registro.loc[0, 'Porcentaje Avance'] = avance
            
            # Agregar al DataFrame
            registros_df = pd.concat([registros_df, nuevo_registro], ignore_index=True)
            registros_creados += 1
        
        # Guardar todos los cambios
        if registros_creados > 0:
            try:
                exito, mensaje = guardar_datos_editados(registros_df, crear_backup=True)
            except:
                exito, mensaje = guardar_en_sheets_local(registros_df)
            
            if exito:
                st.success(f"{registros_creados} registros creados exitosamente")
                st.session_state.ultimo_guardado = datetime.now().strftime("%H:%M:%S")
                st.session_state['registros_df'] = registros_df
                st.balloons()
                time.sleep(1)
                st.rerun()
            else:
                st.error(mensaje)
        else:
            st.warning("No se pudieron crear registros (códigos duplicados)")
            
    except Exception as e:
        st.error(f"Error en creación múltiple: {str(e)}")

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

def guardar_en_sheets_local(registros_df):
    """Función de respaldo para guardar localmente"""
    try:
        # Intentar guardar localmente
        st.session_state['registros_df'] = registros_df
        return True, "Guardado localmente"
    except Exception as e:
        return False, f"Error: {str(e)}"

def recalcular_todos_avances(registros_df):
    """Recalcula el avance de todos los registros"""
    try:
        registros_actualizados = 0
        
        for idx, row in registros_df.iterrows():
            avance_actual = row.get('Porcentaje Avance', 0) if 'Porcentaje Avance' in registros_df.columns else 0
            nuevo_avance = calcular_porcentaje_avance(row)
            
            if avance_actual != nuevo_avance:
                registros_df.at[idx, 'Porcentaje Avance'] = nuevo_avance
                registros_actualizados += 1
        
        st.session_state['registros_df'] = registros_df
        return registros_actualizados
        
    except Exception as e:
        st.error(f"Error recalculando avances: {str(e)}")
        return 0

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
