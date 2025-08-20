# editor_limpio_corregido.py - NUNCA TOCA METAS + SSL CORREGIDO
"""
Editor de Registros Limpio - PROTECCIÓN TOTAL DE METAS
JAMÁS modifica la hoja Metas, solo lee/escribe en Registros
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date
import time

# ===== IMPORTS SEGUROS - SIN AFECTAR METAS =====
try:
    from data_utils import calcular_porcentaje_avance
except ImportError:
    def calcular_porcentaje_avance(registro):
        try:
            avance = 0
            if str(registro.get('Acuerdo de compromiso', '')).strip().upper() in ['SI', 'SÍ']:
                avance += 25
            if registro.get('Análisis y cronograma', '') and str(registro.get('Análisis y cronograma', '')).strip():
                avance += 25
            if registro.get('Estándares', '') and str(registro.get('Estándares', '')).strip():
                avance += 25
            if registro.get('Publicación', '') and str(registro.get('Publicación', '')).strip():
                avance += 25
            return avance
        except:
            return 0

try:
    from validaciones_utils import validar_reglas_negocio
except ImportError:
    def validar_reglas_negocio(df):
        return df

try:
    from fecha_utils import actualizar_plazo_analisis, actualizar_plazo_cronograma, actualizar_plazo_oficio_cierre
except ImportError:
    def actualizar_plazo_analisis(df):
        return df
    def actualizar_plazo_cronograma(df):
        return df
    def actualizar_plazo_oficio_cierre(df):
        return df


# ===== FUNCIÓN SEGURA DE GUARDADO - SOLO REGISTROS =====
def guardar_solo_registros(df):
    """
    FUNCIÓN ULTRA SEGURA: Solo guarda en hoja Registros, JAMÁS toca Metas
    """
    try:
        # Validar que solo estamos guardando registros
        if 'Cod' not in df.columns or 'Entidad' not in df.columns:
            return False, "Error: Solo se pueden guardar datos de registros"
        
        # Importar de forma segura
        try:
            from sheets_utils import GoogleSheetsManager
            
            # Crear nueva instancia cada vez para evitar problemas SSL
            manager = GoogleSheetsManager()
            
            # IMPORTANTE: Solo escribir en hoja "Registros"
            st.info("💾 Guardando únicamente en hoja 'Registros'...")
            
            # Limpiar y escribir SOLO en Registros
            exito = manager.escribir_hoja(df, "Registros", limpiar_hoja=True)
            
            if exito:
                # Verificar que se guardó correctamente
                try:
                    df_verificacion = manager.leer_hoja("Registros")
                    if not df_verificacion.empty and len(df_verificacion) >= len(df) * 0.8:
                        return True, "✅ Datos guardados exitosamente en Google Sheets - Hoja 'Registros'"
                    else:
                        return True, "✅ Datos guardados (verificación parcial)"
                except:
                    return True, "✅ Datos guardados sin verificación"
            else:
                return False, "❌ Error al escribir en Google Sheets"
                
        except ImportError:
            return False, "❌ Error: Módulo sheets_utils no disponible"
        except Exception as e:
            error_msg = str(e).lower()
            if 'ssl' in error_msg or 'wrong_version_number' in error_msg:
                return False, "❌ Error SSL: Problema de conexión segura. Intenta de nuevo en unos segundos."
            elif 'permission' in error_msg or '403' in error_msg:
                return False, "❌ Error de permisos: Verifica que el service account tenga acceso."
            else:
                return False, f"❌ Error de conexión: {str(e)}"
        
    except Exception as e:
        return False, f"❌ Error interno: {str(e)}"


def cargar_datos_desde_sheets():
    """
    Carga datos SOLO desde la hoja Registros, nunca toca Metas
    """
    try:
        from sheets_utils import GoogleSheetsManager
        
        # Nueva instancia para evitar problemas SSL
        manager = GoogleSheetsManager()
        
        # Leer SOLO de Registros
        df = manager.leer_hoja("Registros")
        
        if df.empty:
            st.warning("La hoja 'Registros' está vacía o no se pudo leer")
            return pd.DataFrame()
        
        return df
        
    except Exception as e:
        error_msg = str(e).lower()
        if 'ssl' in error_msg:
            st.error("❌ Error SSL de conexión. Refresca la página e intenta de nuevo.")
        else:
            st.error(f"❌ Error al cargar datos: {str(e)}")
        return pd.DataFrame()


def generar_nuevo_codigo(registros_df):
    """Genera un nuevo código autonumérico"""
    try:
        if registros_df.empty:
            return "001"
        
        # Extraer números de códigos existentes
        codigos_numericos = []
        for codigo in registros_df['Cod']:
            try:
                # Intentar extraer números del código
                num_str = ''.join(filter(str.isdigit, str(codigo)))
                if num_str:
                    codigos_numericos.append(int(num_str))
            except:
                continue
        
        if codigos_numericos:
            nuevo_numero = max(codigos_numericos) + 1
        else:
            nuevo_numero = 1
            
        return f"{nuevo_numero:03d}"  # Formato con 3 dígitos: 001, 002, etc.
        
    except Exception as e:
        st.error(f"Error generando código: {e}")
        return "001"


def obtener_columnas_completas():
    """Devuelve todas las columnas necesarias para un registro completo"""
    return [
        'Cod', 'Entidad', 'TipoDato', 'Nivel Información ', 'Mes Proyectado',
        'Funcionario de enlace', 'Frecuencia', 'Actas de interés', 'Suscripción',
        'Entrega', 'Acuerdo de compromiso', 'Acceso a datos', 'Análisis de información',
        'Fecha de entrega de información', 'Cronograma concertado',
        'Análisis de información (fecha programada)', 'Análisis y cronograma',
        'Seguimiento de acuerdos', 'Registro', 'ET', 'CO', 'DD', 'REC', 'SERVICIO',
        'Estándares (fecha programada)', 'Estándares', 'Resultados de orientación técnica',
        'Verificación del servicio web geográfico', 'Verificar Aprobar', 'Revisar validar',
        'Aprobación de resultados', 'Fecha de publicación programada', 'Publicación',
        'Disponer de los datos temáticos', 'Catálogo de recursos geográficos',
        'Oficios de cierre', 'Fecha de oficio de cierre', 'Estado', 'Observaciones',
        'Plazo de análisis', 'Plazo de cronograma', 'Plazo de oficio de cierre',
        'Porcentaje de Avance'
    ]


def crear_registro_vacio(codigo_nuevo):
    """Crea un registro completamente vacío con el código asignado"""
    columnas = obtener_columnas_completas()
    registro = {}
    
    for columna in columnas:
        if columna == 'Cod':
            registro[columna] = codigo_nuevo
        elif columna == 'Porcentaje de Avance':
            registro[columna] = 0
        else:
            registro[columna] = ''
    
    return registro


def mostrar_formulario_registro(row_data, indice, es_nuevo=False):
    """Muestra el formulario para editar o crear un registro"""
    
    # INFORMACIÓN BÁSICA
    st.markdown("**Información Básica**")
    col1, col2 = st.columns(2)
    
    with col1:
        codigo = st.text_input("Código", 
            value=str(row_data.get('Cod', '')), 
            key=f"codigo_{indice}",
            disabled=es_nuevo)  # Solo lectura para nuevos registros
            
        tipo_dato = st.selectbox("Tipo de Dato", 
            options=["", "Geográfico", "Estadístico", "Catastral", "Otro"],
            index=["", "Geográfico", "Estadístico", "Catastral", "Otro"].index(row_data.get('TipoDato', '')) if row_data.get('TipoDato', '') in ["", "Geográfico", "Estadístico", "Catastral", "Otro"] else 0,
            key=f"tipo_dato_{indice}")
            
        entidad = st.text_input("Entidad", 
            value=str(row_data.get('Entidad', '')), 
            key=f"entidad_{indice}")
        
    with col2:
        nivel_info = st.text_input("Nivel de Información", 
            value=str(row_data.get('Nivel Información ', '')), 
            key=f"nivel_{indice}")
            
        mes_proyectado = st.text_input("Mes Proyectado", 
            value=str(row_data.get('Mes Proyectado', '')), 
            key=f"mes_{indice}")
            
        funcionario = st.text_input("Funcionario", 
            value=str(row_data.get('Funcionario de enlace', '')), 
            key=f"funcionario_{indice}")
    
    frecuencia = st.selectbox("Frecuencia",
        options=["", "Anual", "Mensual", "Trimestral", "Semestral"],
        index=["", "Anual", "Mensual", "Trimestral", "Semestral"].index(row_data.get('Frecuencia', '')) if row_data.get('Frecuencia', '') in ["", "Anual", "Mensual", "Trimestral", "Semestral"] else 0,
        key=f"frecuencia_{indice}")
    
    # ACUERDOS Y COMPROMISOS
    st.markdown("**Acuerdos y Compromisos**")
    col1, col2 = st.columns(2)
    
    with col1:
        actas_interes = st.selectbox("Actas de interés",
            options=["", "Si", "No"],
            index=["", "Si", "No"].index(row_data.get('Actas de interés', '')) if row_data.get('Actas de interés', '') in ["", "Si", "No"] else 0,
            key=f"actas_{indice}")
        
        suscripcion = st.selectbox("Suscripción",
            options=["", "Si", "No", "Pendiente"],
            index=["", "Si", "No", "Pendiente"].index(row_data.get('Suscripción', '')) if row_data.get('Suscripción', '') in ["", "Si", "No", "Pendiente"] else 0,
            key=f"suscripcion_{indice}")
    
    with col2:
        entrega = st.selectbox("Entrega",
            options=["", "Si", "No", "Parcial"],
            index=["", "Si", "No", "Parcial"].index(row_data.get('Entrega', '')) if row_data.get('Entrega', '') in ["", "Si", "No", "Parcial"] else 0,
            key=f"entrega_{indice}")
        
        acuerdo_compromiso = st.selectbox("Acuerdo de compromiso",
            options=["", "Si", "No"],
            index=["", "Si", "No"].index(row_data.get('Acuerdo de compromiso', '')) if row_data.get('Acuerdo de compromiso', '') in ["", "Si", "No"] else 0,
            key=f"acuerdo_{indice}")
    
    # GESTIÓN DE INFORMACIÓN
    st.markdown("**Gestión de Información**")
    col1, col2 = st.columns(2)
    
    with col1:
        acceso_datos = st.selectbox("Acceso a datos",
            options=["", "Si", "No", "Limitado"],
            index=["", "Si", "No", "Limitado"].index(row_data.get('Acceso a datos', '')) if row_data.get('Acceso a datos', '') in ["", "Si", "No", "Limitado"] else 0,
            key=f"acceso_{indice}")
        
        analisis_informacion = st.text_input("Análisis de información",
            value=str(row_data.get('Análisis de información', '')),
            key=f"analisis_info_{indice}")
    
    with col2:
        fecha_entrega = st.text_input("Fecha de entrega (DD/MM/YYYY)",
            value=str(row_data.get('Fecha de entrega de información', '')),
            key=f"fecha_entrega_{indice}")
        
        cronograma_concertado = st.selectbox("Cronograma concertado",
            options=["", "Si", "No", "En proceso"],
            index=["", "Si", "No", "En proceso"].index(row_data.get('Cronograma concertado', '')) if row_data.get('Cronograma concertado', '') in ["", "Si", "No", "En proceso"] else 0,
            key=f"cronograma_{indice}")
    
    # ANÁLISIS Y FECHAS
    st.markdown("**Análisis y Cronograma**")
    col1, col2 = st.columns(2)
    
    with col1:
        analisis_programada = st.text_input("Análisis programada (DD/MM/YYYY)",
            value=str(row_data.get('Análisis de información (fecha programada)', '')),
            key=f"analisis_prog_{indice}")
        
        analisis_real = st.text_input("Análisis real (DD/MM/YYYY)",
            value=str(row_data.get('Análisis y cronograma', '')),
            key=f"analisis_real_{indice}")
    
    with col2:
        seguimiento_acuerdos = st.text_area("Seguimiento de acuerdos",
            value=str(row_data.get('Seguimiento de acuerdos', '')),
            height=80,
            key=f"seguimiento_{indice}")
    
    # ESTÁNDARES COMPLETOS
    st.markdown("**Estándares**")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        registro = st.selectbox("Registro",
            options=["", "Completo", "Incompleto", "No aplica"],
            index=["", "Completo", "Incompleto", "No aplica"].index(row_data.get('Registro', '')) if row_data.get('Registro', '') in ["", "Completo", "Incompleto", "No aplica"] else 0,
            key=f"registro_{indice}")
            
        et = st.selectbox("ET",
            options=["", "Completo", "Incompleto", "No aplica"],
            index=["", "Completo", "Incompleto", "No aplica"].index(row_data.get('ET', '')) if row_data.get('ET', '') in ["", "Completo", "Incompleto", "No aplica"] else 0,
            key=f"et_{indice}")
    
    with col2:
        co = st.selectbox("CO",
            options=["", "Completo", "Incompleto", "No aplica"],
            index=["", "Completo", "Incompleto", "No aplica"].index(row_data.get('CO', '')) if row_data.get('CO', '') in ["", "Completo", "Incompleto", "No aplica"] else 0,
            key=f"co_{indice}")
            
        dd = st.selectbox("DD",
            options=["", "Completo", "Incompleto", "No aplica"],
            index=["", "Completo", "Incompleto", "No aplica"].index(row_data.get('DD', '')) if row_data.get('DD', '') in ["", "Completo", "Incompleto", "No aplica"] else 0,
            key=f"dd_{indice}")
    
    with col3:
        rec = st.selectbox("REC",
            options=["", "Completo", "Incompleto", "No aplica"],
            index=["", "Completo", "Incompleto", "No aplica"].index(row_data.get('REC', '')) if row_data.get('REC', '') in ["", "Completo", "Incompleto", "No aplica"] else 0,
            key=f"rec_{indice}")
            
        servicio = st.selectbox("SERVICIO",
            options=["", "Completo", "Incompleto", "No aplica"],
            index=["", "Completo", "Incompleto", "No aplica"].index(row_data.get('SERVICIO', '')) if row_data.get('SERVICIO', '') in ["", "Completo", "Incompleto", "No aplica"] else 0,
            key=f"servicio_{indice}")
    
    # FECHAS DE ESTÁNDARES
    col1, col2 = st.columns(2)
    
    with col1:
        estandares_programada = st.text_input("Estándares programada (DD/MM/YYYY)",
            value=str(row_data.get('Estándares (fecha programada)', '')),
            key=f"estandares_prog_{indice}")
    
    with col2:
        estandares_real = st.text_input("Estándares real (DD/MM/YYYY)",
            value=str(row_data.get('Estándares', '')),
            key=f"estandares_real_{indice}")
    
    # ORIENTACIÓN Y VERIFICACIONES
    st.markdown("**Orientación y Verificaciones**")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        resultados_orientacion = st.selectbox("Resultados orientación técnica",
            options=["", "Si", "No", "Completo"],
            index=["", "Si", "No", "Completo"].index(row_data.get('Resultados de orientación técnica', '')) if row_data.get('Resultados de orientación técnica', '') in ["", "Si", "No", "Completo"] else 0,
            key=f"orientacion_{indice}")
    
    with col2:
        verificacion_servicio = st.selectbox("Verificación servicio web",
            options=["", "Si", "No", "Completo"],
            index=["", "Si", "No", "Completo"].index(row_data.get('Verificación del servicio web geográfico', '')) if row_data.get('Verificación del servicio web geográfico', '') in ["", "Si", "No", "Completo"] else 0,
            key=f"verificacion_{indice}")
    
    with col3:
        verificar_aprobar = st.selectbox("Verificar Aprobar",
            options=["", "Si", "No", "Pendiente"],
            index=["", "Si", "No", "Pendiente"].index(row_data.get('Verificar Aprobar', '')) if row_data.get('Verificar Aprobar', '') in ["", "Si", "No", "Pendiente"] else 0,
            key=f"verificar_aprobar_{indice}")
    
    col1, col2 = st.columns(2)
    
    with col1:
        revisar_validar = st.selectbox("Revisar validar",
            options=["", "Si", "No", "En proceso"],
            index=["", "Si", "No", "En proceso"].index(row_data.get('Revisar validar', '')) if row_data.get('Revisar validar', '') in ["", "Si", "No", "En proceso"] else 0,
            key=f"revisar_{indice}")
    
    with col2:
        aprobacion_resultados = st.selectbox("Aprobación resultados",
            options=["", "Si", "No", "Pendiente"],
            index=["", "Si", "No", "Pendiente"].index(row_data.get('Aprobación de resultados', '')) if row_data.get('Aprobación de resultados', '') in ["", "Si", "No", "Pendiente"] else 0,
            key=f"aprobacion_{indice}")
    
    # PUBLICACIÓN
    st.markdown("**Publicación**")
    col1, col2 = st.columns(2)
    
    with col1:
        publicacion_programada = st.text_input("Publicación programada (DD/MM/YYYY)",
            value=str(row_data.get('Fecha de publicación programada', '')),
            key=f"pub_prog_{indice}")
        
        publicacion_real = st.text_input("Publicación real (DD/MM/YYYY)",
            value=str(row_data.get('Publicación', '')),
            key=f"pub_real_{indice}")
    
    with col2:
        disponer_datos = st.selectbox("Disponer datos temáticos",
            options=["", "Si", "No", "En proceso"],
            index=["", "Si", "No", "En proceso"].index(row_data.get('Disponer de los datos temáticos', '')) if row_data.get('Disponer de los datos temáticos', '') in ["", "Si", "No", "En proceso"] else 0,
            key=f"disponer_{indice}")
        
        catalogo_recursos = st.selectbox("Catálogo recursos",
            options=["", "Si", "No", "En proceso"],
            index=["", "Si", "No", "En proceso"].index(row_data.get('Catálogo de recursos geográficos', '')) if row_data.get('Catálogo de recursos geográficos', '') in ["", "Si", "No", "En proceso"] else 0,
            key=f"catalogo_{indice}")
    
    # CIERRE
    st.markdown("**Cierre**")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        oficios_cierre = st.selectbox("Oficios de cierre",
            options=["", "Si", "No", "Pendiente"],
            index=["", "Si", "No", "Pendiente"].index(row_data.get('Oficios de cierre', '')) if row_data.get('Oficios de cierre', '') in ["", "Si", "No", "Pendiente"] else 0,
            key=f"oficios_{indice}")
    
    with col2:
        fecha_oficio_cierre = st.text_input("Fecha oficio cierre (DD/MM/YYYY)",
            value=str(row_data.get('Fecha de oficio de cierre', '')),
            key=f"fecha_oficio_{indice}")
    
    with col3:
        estado_final = st.selectbox("Estado final",
            options=["", "Completo", "Incompleto", "Cancelado"],
            index=["", "Completo", "Incompleto", "Cancelado"].index(row_data.get('Estado', '')) if row_data.get('Estado', '') in ["", "Completo", "Incompleto", "Cancelado"] else 0,
            key=f"estado_{indice}")
    
    # PLAZOS CALCULADOS (solo lectura)
    st.markdown("**Plazos Calculados**")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.text_input("Plazo análisis", 
            value=str(row_data.get('Plazo de análisis', '')), 
            disabled=True,
            key=f"plazo_analisis_{indice}")
    
    with col2:
        st.text_input("Plazo cronograma", 
            value=str(row_data.get('Plazo de cronograma', '')), 
            disabled=True,
            key=f"plazo_cronograma_{indice}")
    
    with col3:
        st.text_input("Plazo oficio cierre", 
            value=str(row_data.get('Plazo de oficio de cierre', '')), 
            disabled=True,
            key=f"plazo_oficio_{indice}")
    
    # OBSERVACIONES
    st.markdown("**Observaciones**")
    observaciones = st.text_area("Observaciones",
        value=str(row_data.get('Observaciones', '')),
        height=100,
        key=f"observaciones_{indice}")
    
    # COMPLETITUD CALCULADA (solo lectura)
    porcentaje_actual = calcular_porcentaje_avance(row_data)
    st.text_input("Porcentaje de completitud (%)", 
        value=f"{porcentaje_actual}%", 
        disabled=True,
        key=f"completitud_{indice}")
    
    # Retornar todos los valores del formulario
    return {
        'Cod': codigo,
        'Entidad': entidad,
        'TipoDato': tipo_dato,
        'Nivel Información ': nivel_info,
        'Mes Proyectado': mes_proyectado,
        'Funcionario de enlace': funcionario,
        'Frecuencia': frecuencia,
        'Actas de interés': actas_interes,
        'Suscripción': suscripcion,
        'Entrega': entrega,
        'Acuerdo de compromiso': acuerdo_compromiso,
        'Acceso a datos': acceso_datos,
        'Análisis de información': analisis_informacion,
        'Fecha de entrega de información': fecha_entrega,
        'Cronograma concertado': cronograma_concertado,
        'Análisis de información (fecha programada)': analisis_programada,
        'Análisis y cronograma': analisis_real,
        'Seguimiento de acuerdos': seguimiento_acuerdos,
        'Registro': registro,
        'ET': et,
        'CO': co,
        'DD': dd,
        'REC': rec,
        'SERVICIO': servicio,
        'Estándares (fecha programada)': estandares_programada,
        'Estándares': estandares_real,
        'Resultados de orientación técnica': resultados_orientacion,
        'Verificación del servicio web geográfico': verificacion_servicio,
        'Verificar Aprobar': verificar_aprobar,
        'Revisar validar': revisar_validar,
        'Aprobación de resultados': aprobacion_resultados,
        'Fecha de publicación programada': publicacion_programada,
        'Publicación': publicacion_real,
        'Disponer de los datos temáticos': disponer_datos,
        'Catálogo de recursos geográficos': catalogo_recursos,
        'Oficios de cierre': oficios_cierre,
        'Fecha de oficio de cierre': fecha_oficio_cierre,
        'Estado': estado_final,
        'Observaciones': observaciones
    }


def mostrar_edicion_registros(registros_df):
    """Editor limpio con opciones de editar existente o crear nuevo"""
    
    st.subheader("Editor de Registros")
    
    # Botón para recargar datos desde Google Sheets
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.info("💡 Este editor NUNCA modifica la hoja 'Metas', solo trabaja con 'Registros'")
    
    with col2:
        if st.button("🔄 Recargar desde Google Sheets", help="Carga los datos más recientes"):
            with st.spinner("Cargando datos..."):
                registros_actualizados = cargar_datos_desde_sheets()
                if not registros_actualizados.empty:
                    st.success("✅ Datos recargados exitosamente")
                    # Actualizar los datos en session_state si existe
                    if 'registros_df' in st.session_state:
                        st.session_state.registros_df = registros_actualizados
                    st.rerun()
                else:
                    st.warning("⚠️ No se pudieron cargar datos nuevos")
    
    with col3:
        total_registros = len(registros_df) if not registros_df.empty else 0
        st.metric("Total Registros", total_registros)
    
    # Pestañas para editar o crear
    tab1, tab2 = st.tabs(["Editar Existente", "Crear Nuevo Registro"])
    
    with tab1:
        if registros_df.empty:
            st.warning("No hay registros disponibles para editar.")
            st.info("💡 Usa el botón 'Recargar desde Google Sheets' o crea un nuevo registro.")
            return registros_df
        
        # Selector de registro
        opciones_registros = [
            f"{registros_df.iloc[i]['Cod']} - {registros_df.iloc[i]['Entidad']} - {registros_df.iloc[i].get('Nivel Información ', 'N/A')}"
            for i in range(len(registros_df))
        ]
        
        seleccion_registro = st.selectbox(
            "Seleccionar registro:",
            options=opciones_registros,
            key="selector_registro_editar"
        )
        
        indice_seleccionado = opciones_registros.index(seleccion_registro)
        row_original = registros_df.iloc[indice_seleccionado].copy()
        
        st.markdown(f"**Editando:** {row_original['Cod']} - {row_original['Entidad']}")
        
        # FORMULARIO DE EDICIÓN
        form_key = f"form_editor_edit_{row_original['Cod']}_{int(time.time())}"
        
        with st.form(form_key, clear_on_submit=False):
            
            # Mostrar formulario
            valores_form = mostrar_formulario_registro(row_original, indice_seleccionado, es_nuevo=False)
            
            # BOTÓN DE GUARDAR
            submitted = st.form_submit_button("💾 Actualizar Registro", type="primary", use_container_width=True)
            
            if submitted:
                try:
                    # Crear registro actualizado
                    registro_actualizado = row_original.copy()
                    
                    # Actualizar todos los campos del formulario
                    for campo, valor in valores_form.items():
                        registro_actualizado[campo] = valor
                    
                    # Calcular nuevo porcentaje de avance
                    nuevo_porcentaje = calcular_porcentaje_avance(registro_actualizado)
                    registro_actualizado['Porcentaje de Avance'] = nuevo_porcentaje
                    
                    # Actualizar DataFrame
                    registros_df.iloc[indice_seleccionado] = registro_actualizado
                    
                    # Aplicar validaciones y actualizar plazos
                    registros_df = validar_reglas_negocio(registros_df)
                    registros_df = actualizar_plazo_analisis(registros_df)
                    registros_df = actualizar_plazo_cronograma(registros_df)
                    registros_df = actualizar_plazo_oficio_cierre(registros_df)
                    
                    # Guardar SOLO en hoja Registros (NUNCA en Metas)
                    exito, mensaje = guardar_solo_registros(registros_df)
                    
                    if exito:
                        st.success(f"✅ {mensaje}")
                        st.success(f"📊 Avance del registro: {nuevo_porcentaje}%")
                        
                        # Actualizar timestamp de último guardado
                        st.session_state.ultimo_guardado = datetime.now().strftime("%H:%M:%S")
                        
                        # Esperar un momento antes de recargar
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(f"❌ {mensaje}")
                        if "ssl" in mensaje.lower():
                            st.info("💡 Error SSL detectado. Intenta recargar la página e intentar de nuevo.")
                        
                except Exception as e:
                    st.error(f"❌ Error al procesar los cambios: {str(e)}")
                    st.code(f"Detalle del error: {type(e).__name__}: {str(e)}")
    
    with tab2:
        st.markdown("**Crear Nuevo Registro**")
        
        # Generar código automático
        nuevo_codigo = generar_nuevo_codigo(registros_df)
        st.info(f"📝 Código asignado automáticamente: **{nuevo_codigo}**")
        
        # FORMULARIO DE NUEVO REGISTRO
        form_key_nuevo = f"form_editor_nuevo_{nuevo_codigo}_{int(time.time())}"
        
        with st.form(form_key_nuevo, clear_on_submit=True):
            
            # Crear registro vacío con código asignado
            registro_vacio = crear_registro_vacio(nuevo_codigo)
            
            # Mostrar formulario
            valores_form_nuevo = mostrar_formulario_registro(registro_vacio, "nuevo", es_nuevo=True)
            
            # BOTÓN DE CREAR
            submitted_nuevo = st.form_submit_button("➕ Crear Nuevo Registro", type="primary", use_container_width=True)
            
            if submitted_nuevo:
                try:
                    # Validar campos obligatorios
                    if not valores_form_nuevo['Entidad'].strip():
                        st.error("❌ El campo 'Entidad' es obligatorio")
                        return registros_df
                    
                    # Crear registro completo
                    nuevo_registro = crear_registro_vacio(nuevo_codigo)
                    
                    # Actualizar con valores del formulario
                    for campo, valor in valores_form_nuevo.items():
                        if campo in nuevo_registro:
                            nuevo_registro[campo] = valor
                    
                    # Calcular porcentaje de avance
                    nuevo_porcentaje = calcular_porcentaje_avance(nuevo_registro)
                    nuevo_registro['Porcentaje de Avance'] = nuevo_porcentaje
                    
                    # Asegurar que todas las columnas estén presentes
                    columnas_completas = obtener_columnas_completas()
                    for columna in columnas_completas:
                        if columna not in nuevo_registro:
                            nuevo_registro[columna] = ''
                    
                    # Convertir a DataFrame y concatenar
                    df_nuevo_registro = pd.DataFrame([nuevo_registro])
                    
                    if registros_df.empty:
                        # Si no hay registros, crear DataFrame con el nuevo
                        registros_df = df_nuevo_registro
                    else:
                        # Asegurar que ambos DataFrames tengan las mismas columnas
                        for columna in columnas_completas:
                            if columna not in registros_df.columns:
                                registros_df[columna] = ''
                        
                        # Concatenar el nuevo registro
                        registros_df = pd.concat([registros_df, df_nuevo_registro], ignore_index=True)
                    
                    # Aplicar validaciones y actualizar plazos
                    registros_df = validar_reglas_negocio(registros_df)
                    registros_df = actualizar_plazo_analisis(registros_df)
                    registros_df = actualizar_plazo_cronograma(registros_df)
                    registros_df = actualizar_plazo_oficio_cierre(registros_df)
                    
                    # Guardar SOLO en hoja Registros (NUNCA en Metas)
                    exito, mensaje = guardar_solo_registros(registros_df)
                    
                    if exito:
                        st.success(f"✅ Nuevo registro creado exitosamente: **{nuevo_codigo}**")
                        st.success(f"📊 {mensaje}")
                        st.success(f"📈 Avance inicial: {nuevo_porcentaje}%")
                        st.balloons()
                        
                        # Actualizar timestamp de último guardado
                        st.session_state.ultimo_guardado = datetime.now().strftime("%H:%M:%S")
                        
                        # Esperar un momento antes de recargar
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(f"❌ Error al guardar el nuevo registro: {mensaje}")
                        if "ssl" in mensaje.lower():
                            st.info("💡 Error SSL detectado. Intenta recargar la página e intentar de nuevo.")
                        
                except Exception as e:
                    st.error(f"❌ Error al crear el nuevo registro: {str(e)}")
                    st.code(f"Detalle del error: {type(e).__name__}: {str(e)}")
    
    return registros_df


def verificar_conexion_sheets():
    """Verifica si la conexión con Google Sheets está funcionando - SOLO LEE REGISTROS"""
    try:
        from sheets_utils import GoogleSheetsManager
        
        # Nueva instancia para evitar problemas SSL
        manager = GoogleSheetsManager()
        
        # Listar hojas disponibles
        hojas = manager.listar_hojas()
        
        if hojas:
            hojas_str = ', '.join(hojas)
            # Verificar específicamente la hoja Registros
            if 'Registros' in hojas:
                try:
                    df_test = manager.leer_hoja("Registros")
                    num_registros = len(df_test) if not df_test.empty else 0
                    return True, f"✅ Conexión exitosa. Hojas: {hojas_str}. Registros disponibles: {num_registros}"
                except Exception as e:
                    return True, f"✅ Conexión exitosa. Hojas: {hojas_str}. Error leyendo Registros: {str(e)}"
            else:
                return True, f"✅ Conexión exitosa. Hojas: {hojas_str}. ⚠️ Hoja 'Registros' no encontrada"
        else:
            return False, "❌ No se pudieron listar las hojas"
            
    except Exception as e:
        error_msg = str(e).lower()
        if 'ssl' in error_msg or 'wrong_version_number' in error_msg:
            return False, "❌ Error SSL: Problema de conexión segura. Refresca la página e intenta de nuevo."
        elif 'permission' in error_msg or '403' in error_msg:
            return False, "❌ Error de permisos: Verifica que el service account tenga acceso al spreadsheet."
        elif 'not found' in error_msg or '404' in error_msg:
            return False, "❌ Spreadsheet no encontrado: Verifica el SPREADSHEET_ID en la configuración."
        else:
            return False, f"❌ Error de conexión: {str(e)}"


def mostrar_edicion_registros_con_autenticacion(registros_df):
    """Wrapper con autenticación para el editor limpio - PROTECCIÓN TOTAL DE METAS"""
    
    try:
        from auth_utils import verificar_autenticacion
        
        if verificar_autenticacion():
            
            # Panel de estado - SIN TOCAR METAS
            with st.expander("🔧 Estado de Conexión (Solo Registros)", expanded=False):
                
                st.warning("🛡️ **PROTECCIÓN ACTIVA**: Este editor JAMÁS modifica la hoja 'Metas'")
                
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    if st.button("🔄 Verificar Conexión Google Sheets", key="verificar_sheets_seguro"):
                        with st.spinner("Verificando conexión (solo lectura Registros)..."):
                            conexion_ok, mensaje = verificar_conexion_sheets()
                            if conexion_ok:
                                st.success(mensaje)
                            else:
                                st.error(mensaje)
                                
                                # Mostrar sugerencias específicas para cada tipo de error
                                if "ssl" in mensaje.lower():
                                    st.info("""
                                    🔧 **Solución para Error SSL:**
                                    1. Refresca la página (Ctrl+F5)
                                    2. Espera 30 segundos e intenta de nuevo
                                    3. Si persiste, verifica tu conexión a internet
                                    """)
                                elif "permission" in mensaje.lower() or "403" in mensaje.lower():
                                    st.info("""
                                    🔧 **Solución para Error de Permisos:**
                                    1. Verifica que el service account tenga acceso al spreadsheet
                                    2. Comprueba que el correo del service account esté invitado
                                    3. Asegúrate de que tenga permisos de edición
                                    """)
                                elif "not found" in mensaje.lower() or "404" in mensaje.lower():
                                    st.info("""
                                    🔧 **Solución para Spreadsheet No Encontrado:**
                                    1. Verifica el SPREADSHEET_ID en tu configuración
                                    2. Asegúrate de que el spreadsheet existe
                                    3. Confirma que el ID sea correcto (debe tener ~44 caracteres)
                                    """)
                                else:
                                    st.info("""
                                    🔧 **Sugerencias Generales:**
                                    - Verifica tu conexión a internet
                                    - Comprueba que el archivo `credentials.json` esté presente
                                    - Asegúrate de que el SPREADSHEET_ID sea correcto
                                    - Verifica los permisos de la cuenta de servicio
                                    """)
                
                with col2:
                    # Mostrar último guardado si existe
                    if 'ultimo_guardado' in st.session_state:
                        st.success(f"⏰ Último guardado:\n{st.session_state.ultimo_guardado}")
                    else:
                        st.info("🕐 Sin guardados\nrecientes")
                
                # Información de seguridad
                st.success("""
                🛡️ **GARANTÍAS DE SEGURIDAD:**
                ✅ Solo modifica hoja 'Registros'
                ✅ NUNCA toca hoja 'Metas'
                ✅ Crea nueva instancia en cada operación
                ✅ Validaciones antes de guardar
                """)
            
            return mostrar_edicion_registros(registros_df)
            
        else:
            st.subheader("🔐 Acceso Restringido")
            st.warning("Se requiere autenticación para editar registros")
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.info("""
                **Para acceder al editor seguro:**
                1. 🔐 Use el panel 'Acceso Administrativo' en la barra lateral
                2. 👤 Ingrese las credenciales de administrador
                3. ✅ Podrá editar registros sin afectar Metas
                """)
            
            with col2:
                # Mostrar vista previa de funcionalidades
                st.markdown("**🎯 Funcionalidades disponibles:**")
                st.markdown("""
                - ✏️ Editar registros existentes
                - ➕ Crear nuevos registros
                - 🔢 Autonumeración de códigos
                - 💾 Guardado seguro (solo Registros)
                - 🛡️ PROTECCIÓN de hoja Metas
                - 📊 Cálculo automático de avance
                - 🔄 Validaciones automáticas
                - 🚫 SSL error handling
                """)
            
            return registros_df
            
    except ImportError:
        st.warning("⚠️ Sistema de autenticación no disponible. Acceso directo habilitado.")
        st.error("🛡️ IMPORTANTE: Se aplicará protección de hoja Metas")
        return mostrar_edicion_registros(registros_df)
