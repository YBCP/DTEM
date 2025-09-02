# editor.py - CÓDIGO COMPLETO FINAL
"""
Editor de registros con selectores FUERA del formulario
SOLUCIÓN DEFINITIVA: Los botones están fuera del st.form para que funcionen inmediatamente
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
    SOLUCIÓN DEFINITIVA: BOTONES FUERA DEL FORMULARIO
    """
    st.markdown("**Funcionario:**")
    
    # Estado para controlar si se está creando nuevo funcionario
    estado_nuevo_func = st.session_state.get(f"nuevo_func_{key_base}", False)
    
    if not estado_nuevo_func:
        # Modo normal: selectbox + botón para activar modo nuevo
        col1, col2 = st.columns([2, 1])
        
        with col1:
            opciones = [""] + funcionarios_existentes
            valor_inicial = 0
            if funcionario_actual and funcionario_actual in funcionarios_existentes:
                valor_inicial = funcionarios_existentes.index(funcionario_actual) + 1
            
            seleccion = st.selectbox(
                "Seleccionar funcionario existente:",
                opciones,
                index=valor_inicial,
                key=f"func_select_{key_base}"
            )
        
        with col2:
            # BOTÓN FUERA DEL FORM - Usando form_submit_button como botón normal
            if st.button("+ Nuevo", key=f"btn_nuevo_func_{key_base}", type="secondary"):
                st.session_state[f"nuevo_func_{key_base}"] = True
                st.rerun()
        
        return seleccion if seleccion else ""
    
    else:
        # Modo crear nuevo: campo de texto + botones
        st.info("Creando nuevo funcionario:")
        
        nuevo_funcionario = st.text_input(
            "Nombre del funcionario:",
            value="",
            placeholder="Escriba el nombre completo",
            key=f"func_nuevo_{key_base}"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✓ Confirmar", key=f"confirmar_func_{key_base}", type="primary"):
                if nuevo_funcionario and nuevo_funcionario.strip():
                    st.session_state[f"nuevo_func_{key_base}"] = False
                    return nuevo_funcionario.strip()
                else:
                    st.error("Debe escribir un nombre")
                    return ""
        
        with col2:
            if st.button("✗ Cancelar", key=f"cancelar_func_{key_base}"):
                st.session_state[f"nuevo_func_{key_base}"] = False
                st.rerun()
        
        return nuevo_funcionario.strip() if nuevo_funcionario else ""

def mostrar_selector_entidad(entidad_actual, entidades_existentes, key_base):
    """
    SOLUCIÓN DEFINITIVA: BOTONES FUERA DEL FORMULARIO
    """
    st.markdown("**Entidad:**")
    
    # Estado para controlar si se está creando nueva entidad
    estado_nueva_ent = st.session_state.get(f"nueva_ent_{key_base}", False)
    
    if not estado_nueva_ent:
        # Modo normal: selectbox + botón para activar modo nuevo
        col1, col2 = st.columns([2, 1])
        
        with col1:
            opciones = [""] + entidades_existentes
            valor_inicial = 0
            if entidad_actual and entidad_actual in entidades_existentes:
                valor_inicial = entidades_existentes.index(entidad_actual) + 1
            
            seleccion = st.selectbox(
                "Seleccionar entidad existente:",
                opciones,
                index=valor_inicial,
                key=f"ent_select_{key_base}"
            )
        
        with col2:
            # BOTÓN FUERA DEL FORM
            if st.button("+ Nueva", key=f"btn_nueva_ent_{key_base}", type="secondary"):
                st.session_state[f"nueva_ent_{key_base}"] = True
                st.rerun()
        
        return seleccion if seleccion else ""
    
    else:
        # Modo crear nueva: campo de texto + botones
        st.info("Creando nueva entidad:")
        
        nueva_entidad = st.text_input(
            "Nombre de la entidad:",
            value="",
            placeholder="Escriba el nombre completo",
            key=f"ent_nueva_{key_base}"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✓ Confirmar", key=f"confirmar_ent_{key_base}", type="primary"):
                if nueva_entidad and nueva_entidad.strip():
                    st.session_state[f"nueva_ent_{key_base}"] = False
                    return nueva_entidad.strip()
                else:
                    st.error("Debe escribir un nombre")
                    return ""
        
        with col2:
            if st.button("✗ Cancelar", key=f"cancelar_ent_{key_base}"):
                st.session_state[f"nueva_ent_{key_base}"] = False
                st.rerun()
        
        return nueva_entidad.strip() if nueva_entidad else ""

def mostrar_edicion_registros(registros_df):
    """Editor principal - BOTONES FUERA DEL FORMULARIO"""
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
        
        # SECCIÓN FUERA DEL FORMULARIO - SELECCIÓN DE REGISTRO
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
            
            # SELECTORES DE FUNCIONARIO Y ENTIDAD FUERA DEL FORM
            st.markdown("---")
            st.markdown("#### Seleccionar Funcionario y Entidad")
            
            col1, col2 = st.columns(2)
            with col1:
                funcionario_seleccionado = mostrar_selector_funcionario(
                    get_safe_value(row_seleccionada, 'Funcionario'), 
                    obtener_funcionarios_unicos(registros_df), 
                    f"edit_{indice_real}"
                )
            
            with col2:
                entidad_seleccionada = mostrar_selector_entidad(
                    get_safe_value(row_seleccionada, 'Entidad'),
                    obtener_entidades_unicas(registros_df),
                    f"edit_{indice_real}"
                )
            
            # FORMULARIO CON EL RESTO DE CAMPOS
            with st.form("form_editar_completo"):
                st.markdown("#### Resto de Información")
                
                # Usar valores seleccionados o actuales
                funcionario_final = funcionario_seleccionado or get_safe_value(row_seleccionada, 'Funcionario')
                entidad_final = entidad_seleccionada or get_safe_value(row_seleccionada, 'Entidad')
                
                # Mostrar información básica
                col1, col2 = st.columns(2)
                with col1:
                    codigo = st.text_input("Código:", value=get_safe_value(row_seleccionada, 'Cod'), disabled=True)
                    st.info(f"Funcionario: {funcionario_final}")
                
                with col2:
                    st.info(f"Entidad: {entidad_final}")
                    nivel_info = st.text_input("Nivel de Información:", value=get_safe_value(row_seleccionada, 'Nivel Información '))
                
                # Campos principales (resto del formulario simplificado)
                col1, col2, col3 = st.columns(3)
                with col1:
                    tipo_actual = get_safe_value(row_seleccionada, 'TipoDato')
                    tipo_opciones = ["", "Actualizar", "Nuevo"]
                    tipo_index = tipo_opciones.index(tipo_actual) if tipo_actual in tipo_opciones else 0
                    tipo_dato = st.selectbox("Tipo de Dato:", tipo_opciones, index=tipo_index)
                
                with col2:
                    mes_actual = get_safe_value(row_seleccionada, 'Mes Proyectado')
                    mes_index = MESES.index(mes_actual) if mes_actual in MESES else 0
                    mes_proyectado = st.selectbox("Mes Proyectado:", MESES, index=mes_index)
                
                with col3:
                    frecuencia_actual = get_safe_value(row_seleccionada, 'Frecuencia actualizacion ')
                    frecuencia_index = FRECUENCIAS.index(frecuencia_actual) if frecuencia_actual in FRECUENCIAS else 0
                    frecuencia = st.selectbox("Frecuencia:", FRECUENCIAS, index=frecuencia_index)
                
                # Fechas principales
                st.subheader("Fechas Principales")
                col1, col2 = st.columns(2)
                
                with col1:
                    analisis_real_date = string_a_fecha(get_safe_value(row_seleccionada, 'Análisis y cronograma'))
                    analisis_real = st.date_input("Análisis y cronograma:", value=analisis_real_date)
                    if st.checkbox("Limpiar análisis", key="limpiar_analisis_edit"):
                        analisis_real = None
                
                with col2:
                    est_real_date = string_a_fecha(get_safe_value(row_seleccionada, 'Estándares'))
                    estandares_real = st.date_input("Estándares:", value=est_real_date)
                    if st.checkbox("Limpiar estándares", key="limpiar_estandares_edit"):
                        estandares_real = None
                
                col1, col2 = st.columns(2)
                with col1:
                    pub_real_date = string_a_fecha(get_safe_value(row_seleccionada, 'Publicación'))
                    publicacion = st.date_input("Publicación:", value=pub_real_date)
                    if st.checkbox("Limpiar publicación", key="limpiar_pub_edit"):
                        publicacion = None
                
                with col2:
                    fecha_oficio_date = string_a_fecha(get_safe_value(row_seleccionada, 'Fecha de oficio de cierre'))
                    fecha_oficio = st.date_input("Fecha oficio cierre:", value=fecha_oficio_date)
                    if st.checkbox("Limpiar oficio", key="limpiar_oficio_edit"):
                        fecha_oficio = None
                
                # Estado y observaciones
                estado_value = get_safe_value(row_seleccionada, 'Estado')
                estado_opciones = ["", "Completado", "En proceso", "Pendiente"]
                estado_index = estado_opciones.index(estado_value) if estado_value in estado_opciones else 0
                estado = st.selectbox("Estado:", estado_opciones, index=estado_index)
                
                observacion = st.text_area("Observaciones:", value=get_safe_value(row_seleccionada, 'Observación'), height=100)
                
                # SUBMIT DEL FORMULARIO
                if st.form_submit_button("Guardar Cambios", type="primary"):
                    if not funcionario_final.strip():
                        st.error("Debe seleccionar un funcionario")
                    elif not entidad_final.strip():
                        st.error("Debe seleccionar una entidad")
                    else:
                        try:
                            # Crear valores actualizados
                            valores = {
                                'Cod': codigo,
                                'Funcionario': funcionario_final,
                                'Entidad': entidad_final,
                                'Nivel Información ': nivel_info,
                                'TipoDato': tipo_dato,
                                'Mes Proyectado': mes_proyectado,
                                'Frecuencia actualizacion ': frecuencia,
                                'Análisis y cronograma': fecha_a_string(analisis_real) if analisis_real else "",
                                'Estándares': fecha_a_string(estandares_real) if estandares_real else "",
                                'Publicación': fecha_a_string(publicacion) if publicacion else "",
                                'Fecha de oficio de cierre': fecha_a_string(fecha_oficio) if fecha_oficio else "",
                                'Estado': estado,
                                'Observación': observacion
                            }
                            
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
                                st.success(f"Registro actualizado. Avance: {nuevo_avance}%")
                                st.session_state['registros_df'] = registros_df
                                st.session_state.ultimo_guardado = datetime.now().strftime("%H:%M:%S")
                                # Limpiar estados de selección
                                if f"nuevo_func_edit_{indice_real}" in st.session_state:
                                    del st.session_state[f"nuevo_func_edit_{indice_real}"]
                                if f"nueva_ent_edit_{indice_real}" in st.session_state:
                                    del st.session_state[f"nueva_ent_edit_{indice_real}"]
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error(f"Error: {mensaje}")
                        except Exception as e:
                            st.error(f"Error guardando: {e}")
    
    with tab2:
        st.subheader("Crear Nuevo Registro")
        
        # SELECTORES FUERA DEL FORMULARIO
        nuevo_codigo = generar_codigo(registros_df)
        st.info(f"Código automático: {nuevo_codigo}")
        
        st.markdown("#### Seleccionar Funcionario y Entidad")
        col1, col2 = st.columns(2)
        
        with col1:
            funcionario_nuevo = mostrar_selector_funcionario("", obtener_funcionarios_unicos(registros_df), "nuevo")
        
        with col2:
            entidad_nueva = mostrar_selector_entidad("", obtener_entidades_unicas(registros_df), "nuevo")
        
        # FORMULARIO PARA CREAR
        with st.form("form_crear_completo"):
            st.markdown("#### Información del Registro")
            
            # Mostrar selecciones
            col1, col2 = st.columns(2)
            with col1:
                st.info(f"Funcionario: {funcionario_nuevo if funcionario_nuevo else 'No seleccionado'}")
            with col2:
                st.info(f"Entidad: {entidad_nueva if entidad_nueva else 'No seleccionada'}")
            
            # Campos principales
            nivel_info = st.text_input("Nivel de Información:")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                tipo_dato = st.selectbox("Tipo de Dato:", ["", "Actualizar", "Nuevo"])
            with col2:
                mes_proyectado = st.selectbox("Mes Proyectado:", MESES)
            with col3:
                frecuencia = st.selectbox("Frecuencia:", FRECUENCIAS)
            
            # Fechas
            st.subheader("Fechas")
            col1, col2 = st.columns(2)
            
            with col1:
                analisis_real = st.date_input("Análisis y cronograma:", value=None)
                if st.checkbox("Limpiar análisis", key="limpiar_analisis_nuevo"):
                    analisis_real = None
                
                estandares_real = st.date_input("Estándares:", value=None) 
                if st.checkbox("Limpiar estándares", key="limpiar_estandares_nuevo"):
                    estandares_real = None
            
            with col2:
                publicacion = st.date_input("Publicación:", value=None)
                if st.checkbox("Limpiar publicación", key="limpiar_pub_nuevo"):
                    publicacion = None
                
                fecha_oficio = st.date_input("Fecha oficio cierre:", value=None)
                if st.checkbox("Limpiar oficio", key="limpiar_oficio_nuevo"):
                    fecha_oficio = None
            
            estado = st.selectbox("Estado:", ["", "Completado", "En proceso", "Pendiente"])
            observacion = st.text_area("Observaciones:", height=100)
            
            # SUBMIT
            if st.form_submit_button("Crear Registro", type="primary"):
                if not funcionario_nuevo or not funcionario_nuevo.strip():
                    st.error("Debe seleccionar un funcionario")
                elif not entidad_nueva or not entidad_nueva.strip():
                    st.error("Debe seleccionar una entidad")
                else:
                    try:
                        # Crear nuevo registro
                        nuevo_registro = pd.Series({col: '' for col in registros_df.columns})
                        
                        valores_nuevo = {
                            'Cod': nuevo_codigo,
                            'Funcionario': funcionario_nuevo,
                            'Entidad': entidad_nueva,
                            'Nivel Información ': nivel_info,
                            'TipoDato': tipo_dato,
                            'Mes Proyectado': mes_proyectado,
                            'Frecuencia actualizacion ': frecuencia,
                            'Análisis y cronograma': fecha_a_string(analisis_real) if analisis_real else "",
                            'Estándares': fecha_a_string(estandares_real) if estandares_real else "",
                            'Publicación': fecha_a_string(publicacion) if publicacion else "",
                            'Fecha de oficio de cierre': fecha_a_string(fecha_oficio) if fecha_oficio else "",
                            'Estado': estado,
                            'Observación': observacion
                        }
                        
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
                            # Limpiar estados
                            if "nuevo_func_nuevo" in st.session_state:
                                del st.session_state["nuevo_func_nuevo"]
                            if "nueva_ent_nuevo" in st.session_state:
                                del st.session_state["nueva_ent_nuevo"]
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
