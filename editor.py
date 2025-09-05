# editor.py - Editor de Registros - Versión Limpia
"""
Editor de registros sin iconos ni texto informativo innecesario
Interfaz visual limpia y funcional
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import time

# Imports de utilidades
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

# Import opcional de Google Sheets
try:
    from sheets_utils import GoogleSheetsManager
except ImportError:
    GoogleSheetsManager = None

def mostrar_edicion_registros(registros_df):
    """
    Editor principal de registros - Interfaz limpia
    """
    
    if registros_df is None or registros_df.empty:
        st.warning("No hay datos disponibles para editar")
        return registros_df
    
    # === HEADER SIMPLE ===
    st.subheader("Editor de Registros")
    
    # === MÉTRICAS BÁSICAS ===
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_registros = len(registros_df)
        st.metric("Total", total_registros)
    
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
    
    with col4:
        if 'Funcionario' in registros_df.columns:
            funcionarios_activos = registros_df['Funcionario'].nunique()
            st.metric("Funcionarios", funcionarios_activos)
        else:
            st.metric("Funcionarios", "N/A")
    
    # === CONTROLES DE ACCIÓN ===
    col_izq, col_der = st.columns([2, 1])
    
    with col_izq:
        # Filtros básicos
        if 'Entidad' in registros_df.columns:
            entidades = ['Todas'] + sorted(registros_df['Entidad'].dropna().unique().tolist())
            entidad_filtro = st.selectbox("Filtrar por Entidad:", entidades, key="entidad_editor")
        else:
            entidad_filtro = 'Todas'
        
        if 'Funcionario' in registros_df.columns:
            funcionarios = ['Todos'] + sorted(registros_df['Funcionario'].dropna().unique().tolist())
            funcionario_filtro = st.selectbox("Filtrar por Funcionario:", funcionarios, key="funcionario_editor")
        else:
            funcionario_filtro = 'Todos'
    
    with col_der:
        # Acciones principales
        if st.button("Recalcular Avances", type="secondary"):
            recalcular_todos_avances(registros_df)
        
        if st.button("Guardar Cambios", type="primary"):
            guardar_cambios_generales(registros_df)
    
    # === APLICAR FILTROS ===
    df_filtrado = registros_df.copy()
    
    if entidad_filtro != 'Todas' and 'Entidad' in df_filtrado.columns:
        df_filtrado = df_filtrado[df_filtrado['Entidad'] == entidad_filtro]
    
    if funcionario_filtro != 'Todos' and 'Funcionario' in df_filtrado.columns:
        df_filtrado = df_filtrado[df_filtrado['Funcionario'] == funcionario_filtro]
    
    # === LISTA DE REGISTROS ===
    st.markdown("---")
    
    if df_filtrado.empty:
        st.warning("No hay registros que coincidan con los filtros")
        return registros_df
    
    # Mostrar registros con edición
    for idx, row in df_filtrado.iterrows():
        mostrar_registro_editable(registros_df, idx, row)
    
    # === AGREGAR NUEVO REGISTRO ===
    st.markdown("---")
    mostrar_creador_registro(registros_df)
    
    return registros_df


def mostrar_registro_editable(registros_df, idx, row):
    """
    Muestra un registro individual editable - Diseño limpio
    """
    
    # Contenedor del registro
    with st.container():
        # Header del registro
        col_header1, col_header2, col_header3, col_header4 = st.columns([3, 2, 2, 1])
        
        with col_header1:
            cod = row.get('Cod', f'Registro {idx}')
            entidad = row.get('Entidad', 'Sin entidad')
            st.markdown(f"**{cod}** - {entidad}")
        
        with col_header2:
            funcionario = row.get('Funcionario', 'Sin asignar')
            st.text(f"Funcionario: {funcionario}")
        
        with col_header3:
            avance = row.get('Porcentaje Avance', 0)
            st.text(f"Avance: {avance}%")
        
        with col_header4:
            # Botón para expandir/contraer
            expandir_key = f"expandir_{idx}"
            if expandir_key not in st.session_state:
                st.session_state[expandir_key] = False
            
            if st.button("Editar", key=f"toggle_{idx}", type="secondary"):
                st.session_state[expandir_key] = not st.session_state[expandir_key]
        
        # Panel de edición expandible
        if st.session_state.get(expandir_key, False):
            with st.expander("", expanded=True):
                editar_registro_completo(registros_df, idx, row)
        
        st.markdown("---")


def editar_registro_completo(registros_df, idx, row):
    """
    Editor completo de un registro - Formulario limpio
    """
    
    # Campos editables organizados en columnas
    col1, col2 = st.columns(2)
    
    # === INFORMACIÓN BÁSICA ===
    with col1:
        st.markdown("**Información Básica**")
        
        nuevo_cod = st.text_input(
            "Código",
            value=str(row.get('Cod', '')),
            key=f"cod_{idx}"
        )
        
        nuevo_funcionario = st.text_input(
            "Funcionario",
            value=str(row.get('Funcionario', '')),
            key=f"funcionario_{idx}"
        )
        
        nueva_entidad = st.text_input(
            "Entidad",
            value=str(row.get('Entidad', '')),
            key=f"entidad_{idx}"
        )
        
        nuevo_tipo_dato = st.selectbox(
            "Tipo de Dato",
            ['Actualizar', 'Nuevo'],
            index=0 if row.get('Tipo de Dato', 'Actualizar') == 'Actualizar' else 1,
            key=f"tipo_dato_{idx}"
        )
        
        nuevo_nombre_dato = st.text_area(
            "Nombre del Dato",
            value=str(row.get('Nombre del Dato', '')),
            height=100,
            key=f"nombre_dato_{idx}"
        )
    
    # === ESTADOS Y FECHAS ===
    with col2:
        st.markdown("**Estados y Fechas**")
        
        estados_opciones = ['Sin Iniciar', 'En proceso', 'Completo']
        
        nuevo_acuerdo = st.selectbox(
            "Acuerdo",
            estados_opciones,
            index=estados_opciones.index(row.get('Acuerdo', 'Sin Iniciar')) if row.get('Acuerdo') in estados_opciones else 0,
            key=f"acuerdo_{idx}"
        )
        
        nuevo_analisis = st.selectbox(
            "Análisis",
            estados_opciones,
            index=estados_opciones.index(row.get('Análisis', 'Sin Iniciar')) if row.get('Análisis') in estados_opciones else 0,
            key=f"analisis_{idx}"
        )
        
        nuevos_estandares = st.selectbox(
            "Estándares",
            estados_opciones,
            index=estados_opciones.index(row.get('Estándares', 'Sin Iniciar')) if row.get('Estándares') in estados_opciones else 0,
            key=f"estandares_{idx}"
        )
        
        nueva_publicacion = st.selectbox(
            "Publicación",
            estados_opciones,
            index=estados_opciones.index(row.get('Publicación', 'Sin Iniciar')) if row.get('Publicación') in estados_opciones else 0,
            key=f"publicacion_{idx}"
        )
        
        # Fechas de plazos
        try:
            fecha_analisis = pd.to_datetime(row.get('Plazo Análisis'), errors='coerce')
            nueva_fecha_analisis = st.date_input(
                "Plazo Análisis",
                value=fecha_analisis.date() if pd.notna(fecha_analisis) else datetime.now().date(),
                key=f"fecha_analisis_{idx}"
            )
        except:
            nueva_fecha_analisis = st.date_input(
                "Plazo Análisis",
                value=datetime.now().date(),
                key=f"fecha_analisis_{idx}"
            )
        
        try:
            fecha_cronograma = pd.to_datetime(row.get('Plazo Cronograma'), errors='coerce')
            nueva_fecha_cronograma = st.date_input(
                "Plazo Cronograma",
                value=fecha_cronograma.date() if pd.notna(fecha_cronograma) else datetime.now().date(),
                key=f"fecha_cronograma_{idx}"
            )
        except:
            nueva_fecha_cronograma = st.date_input(
                "Plazo Cronograma",
                value=datetime.now().date(),
                key=f"fecha_cronograma_{idx}"
            )
    
    # === OBSERVACIONES ===
    st.markdown("**Observaciones**")
    nuevas_observaciones = st.text_area(
        "Observaciones",
        value=str(row.get('Observaciones', '')),
        height=80,
        key=f"observaciones_{idx}"
    )
    
    # === BOTONES DE ACCIÓN ===
    col_btn1, col_btn2, col_btn3, col_btn4 = st.columns(4)
    
    with col_btn1:
        if st.button("Guardar", key=f"guardar_{idx}", type="primary"):
            actualizar_registro(registros_df, idx, {
                'Cod': nuevo_cod,
                'Funcionario': nuevo_funcionario,
                'Entidad': nueva_entidad,
                'Tipo de Dato': nuevo_tipo_dato,
                'Nombre del Dato': nuevo_nombre_dato,
                'Acuerdo': nuevo_acuerdo,
                'Análisis': nuevo_analisis,
                'Estándares': nuevos_estandares,
                'Publicación': nueva_publicacion,
                'Plazo Análisis': nueva_fecha_analisis,
                'Plazo Cronograma': nueva_fecha_cronograma,
                'Observaciones': nuevas_observaciones
            })
    
    with col_btn2:
        if st.button("Recalcular Avance", key=f"recalc_{idx}", type="secondary"):
            recalcular_avance_registro(registros_df, idx)
    
    with col_btn3:
        if st.button("Duplicar", key=f"duplicar_{idx}", type="secondary"):
            duplicar_registro(registros_df, idx)
    
    with col_btn4:
        if st.button("Eliminar", key=f"eliminar_{idx}", type="secondary"):
            eliminar_registro(registros_df, idx)


def mostrar_creador_registro(registros_df):
    """
    Formulario para crear nuevos registros - Diseño limpio
    """
    
    st.subheader("Agregar Nuevo Registro")
    
    with st.form("nuevo_registro", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            nuevo_cod = st.text_input("Código", placeholder="Ingrese código único")
            nuevo_funcionario = st.text_input("Funcionario", placeholder="Nombre del funcionario")
            nueva_entidad = st.text_input("Entidad", placeholder="Nombre de la entidad")
            nuevo_tipo_dato = st.selectbox("Tipo de Dato", ['Actualizar', 'Nuevo'])
        
        with col2:
            nuevo_acuerdo = st.selectbox("Acuerdo", ['Sin Iniciar', 'En proceso', 'Completo'])
            nuevo_analisis = st.selectbox("Análisis", ['Sin Iniciar', 'En proceso', 'Completo'])
            nuevos_estandares = st.selectbox("Estándares", ['Sin Iniciar', 'En proceso', 'Completo'])
            nueva_publicacion = st.selectbox("Publicación", ['Sin Iniciar', 'En proceso', 'Completo'])
        
        nuevo_nombre_dato = st.text_area("Nombre del Dato", placeholder="Descripción del dato")
        nuevas_observaciones = st.text_area("Observaciones", placeholder="Observaciones adicionales")
        
        submitted = st.form_submit_button("Crear Registro", type="primary")
        
        if submitted:
            crear_nuevo_registro(registros_df, {
                'Cod': nuevo_cod,
                'Funcionario': nuevo_funcionario,
                'Entidad': nueva_entidad,
                'Tipo de Dato': nuevo_tipo_dato,
                'Nombre del Dato': nuevo_nombre_dato,
                'Acuerdo': nuevo_acuerdo,
                'Análisis': nuevo_analisis,
                'Estándares': nuevos_estandares,
                'Publicación': nueva_publicacion,
                'Observaciones': nuevas_observaciones
            })


# === FUNCIONES DE PROCESAMIENTO ===

def actualizar_registro(registros_df, idx, valores):
    """Actualiza un registro específico"""
    try:
        # Validar campos obligatorios
        if not valores['Funcionario'] or not valores['Funcionario'].strip():
            st.error("El funcionario es obligatorio")
            return
        
        if not valores['Entidad'] or not valores['Entidad'].strip():
            st.error("La entidad es obligatoria")
            return
        
        # Actualizar valores en el DataFrame
        for campo, valor in valores.items():
            if campo in registros_df.columns:
                registros_df.at[idx, campo] = valor
        
        # Recalcular avance
        nuevo_avance = calcular_porcentaje_avance(registros_df.iloc[idx])
        if 'Porcentaje Avance' in registros_df.columns:
            registros_df.at[idx, 'Porcentaje Avance'] = nuevo_avance
        
        # Actualizar en session_state
        st.session_state['registros_df'] = registros_df
        
        # Intentar guardar
        try:
            exito, mensaje = guardar_datos_editados(registros_df, crear_backup=True)
            if exito:
                st.success(f"Registro {valores['Cod']} actualizado exitosamente")
                time.sleep(1)
                st.rerun()
            else:
                st.error(f"Error al guardar: {mensaje}")
        except Exception as e:
            st.warning(f"Guardado local exitoso. Error al sincronizar: {str(e)}")
        
    except Exception as e:
        st.error(f"Error al actualizar registro: {str(e)}")


def crear_nuevo_registro(registros_df, valores):
    """Crea un nuevo registro"""
    try:
        # Validaciones básicas
        if not valores['Cod'] or not valores['Cod'].strip():
            st.error("El código es obligatorio")
            return
        
        if not valores['Funcionario'] or not valores['Funcionario'].strip():
            st.error("El funcionario es obligatorio")
            return
        
        if not valores['Entidad'] or not valores['Entidad'].strip():
            st.error("La entidad es obligatoria")
            return
        
        # Verificar código único
        if 'Cod' in registros_df.columns and valores['Cod'] in registros_df['Cod'].values:
            st.error("El código ya existe. Use un código único.")
            return
        
        # Crear nuevo registro
        nuevo_registro = {
            'Cod': valores['Cod'],
            'Funcionario': valores['Funcionario'],
            'Entidad': valores['Entidad'],
            'Tipo de Dato': valores['Tipo de Dato'],
            'Nombre del Dato': valores['Nombre del Dato'],
            'Acuerdo': valores['Acuerdo'],
            'Análisis': valores['Análisis'],
            'Estándares': valores['Estándares'],
            'Publicación': valores['Publicación'],
            'Observaciones': valores['Observaciones'],
            'Plazo Análisis': datetime.now().date(),
            'Plazo Cronograma': datetime.now().date(),
            'Plazo Oficio Cierre': datetime.now().date()
        }
        
        # Calcular avance inicial
        avance = calcular_porcentaje_avance(pd.Series(nuevo_registro))
        nuevo_registro['Porcentaje Avance'] = avance
        
        # Agregar al DataFrame
        nuevo_df = pd.DataFrame([nuevo_registro])
        registros_df = pd.concat([registros_df, nuevo_df], ignore_index=True)
        
        # Actualizar session_state
        st.session_state['registros_df'] = registros_df
        
        # Guardar
        try:
            exito, mensaje = guardar_datos_editados(registros_df, crear_backup=True)
            if exito:
                st.success(f"Registro {valores['Cod']} creado exitosamente")
                time.sleep(1)
                st.rerun()
            else:
                st.error(f"Error al guardar: {mensaje}")
        except Exception as e:
            st.warning(f"Registro creado localmente. Error al sincronizar: {str(e)}")
        
    except Exception as e:
        st.error(f"Error al crear registro: {str(e)}")


def recalcular_avance_registro(registros_df, idx):
    """Recalcula el avance de un registro específico"""
    try:
        nuevo_avance = calcular_porcentaje_avance(registros_df.iloc[idx])
        registros_df.at[idx, 'Porcentaje Avance'] = nuevo_avance
        st.session_state['registros_df'] = registros_df
        st.success(f"Avance recalculado: {nuevo_avance}%")
        time.sleep(1)
        st.rerun()
    except Exception as e:
        st.error(f"Error al recalcular avance: {str(e)}")


def recalcular_todos_avances(registros_df):
    """Recalcula todos los avances"""
    try:
        registros_actualizados = 0
        
        for idx, row in registros_df.iterrows():
            avance_actual = row.get('Porcentaje Avance', 0)
            nuevo_avance = calcular_porcentaje_avance(row)
            
            if avance_actual != nuevo_avance:
                registros_df.at[idx, 'Porcentaje Avance'] = nuevo_avance
                registros_actualizados += 1
        
        st.session_state['registros_df'] = registros_df
        st.success(f"Avances recalculados. {registros_actualizados} registros actualizados.")
        
        if registros_actualizados > 0:
            time.sleep(1)
            st.rerun()
        
    except Exception as e:
        st.error(f"Error al recalcular avances: {str(e)}")


def duplicar_registro(registros_df, idx):
    """Duplica un registro existente"""
    try:
        registro_original = registros_df.iloc[idx].copy()
        
        # Generar nuevo código
        codigo_original = str(registro_original.get('Cod', ''))
        nuevo_codigo = f"{codigo_original}_copia_{datetime.now().strftime('%H%M%S')}"
        
        # Crear copia
        registro_copia = registro_original.copy()
        registro_copia['Cod'] = nuevo_codigo
        
        # Agregar al DataFrame
        nuevo_df = pd.DataFrame([registro_copia])
        registros_df = pd.concat([registros_df, nuevo_df], ignore_index=True)
        
        st.session_state['registros_df'] = registros_df
        st.success(f"Registro duplicado con código: {nuevo_codigo}")
        
        time.sleep(1)
        st.rerun()
        
    except Exception as e:
        st.error(f"Error al duplicar registro: {str(e)}")


def eliminar_registro(registros_df, idx):
    """Elimina un registro"""
    try:
        codigo = registros_df.iloc[idx].get('Cod', f'Registro {idx}')
        
        # Confirmación
        confirmar_key = f"confirmar_eliminar_{idx}"
        if confirmar_key not in st.session_state:
            st.session_state[confirmar_key] = False
        
        if not st.session_state[confirmar_key]:
            st.warning(f"¿Confirma eliminar el registro {codigo}?")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Sí, eliminar", key=f"si_eliminar_{idx}", type="primary"):
                    st.session_state[confirmar_key] = True
                    st.rerun()
            with col2:
                if st.button("Cancelar", key=f"cancelar_eliminar_{idx}"):
                    st.session_state[confirmar_key] = False
                    st.rerun()
        else:
            # Eliminar registro
            registros_df = registros_df.drop(index=idx).reset_index(drop=True)
            st.session_state['registros_df'] = registros_df
            st.session_state[confirmar_key] = False
            
            st.success(f"Registro {codigo} eliminado")
            time.sleep(1)
            st.rerun()
        
    except Exception as e:
        st.error(f"Error al eliminar registro: {str(e)}")


def guardar_cambios_generales(registros_df):
    """Guarda todos los cambios pendientes"""
    try:
        with st.spinner("Guardando cambios..."):
            exito, mensaje = guardar_datos_editados(registros_df, crear_backup=True)
            
            if exito:
                st.success("Todos los cambios guardados exitosamente")
                st.session_state.ultimo_guardado = datetime.now().strftime("%H:%M:%S")
            else:
                st.error(f"Error al guardar: {mensaje}")
        
    except Exception as e:
        st.error(f"Error al guardar cambios: {str(e)}")


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
        
        # Mostrar solo vista de lectura limpia
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
