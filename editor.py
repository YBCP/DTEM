# editor.py - VERSIÓN CON FUNCIONARIOS DROPDOWN Y BORRAR FECHAS SIMPLE
"""
Editor de registros MEJORADO:
- Sin recargas automáticas
- Funcionarios con dropdown + opción agregar nuevo
- Borrar fechas SIMPLE: solo dejar campo vacío
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date
from data_utils import (
    procesar_fecha, calcular_porcentaje_avance, guardar_datos_editados, 
    validar_campos_fecha, es_fecha_valida, formatear_fecha
)
from validaciones_utils import validar_reglas_negocio
from fecha_utils import (
    actualizar_plazo_analisis, actualizar_plazo_cronograma, 
    actualizar_plazo_oficio_cierre
)
from auth_utils import verificar_autenticacion


def crear_selector_funcionario_dropdown(registros_df, funcionario_actual, key_suffix):
    """
    Selector de funcionario con dropdown + opción nuevo
    SIMPLE y EFECTIVO
    """
    # Obtener funcionarios únicos existentes
    funcionarios_existentes = []
    if 'Funcionario' in registros_df.columns:
        funcionarios_unicos = registros_df['Funcionario'].dropna().unique()
        funcionarios_existentes = [
            f for f in funcionarios_unicos 
            if f and str(f).strip() and str(f).strip() not in ['nan', 'None', '']
        ]
        funcionarios_existentes = sorted(set(funcionarios_existentes))
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Opción 1: Dropdown con existentes
        opciones = ["(Sin asignar)"] + funcionarios_existentes + [">>> AGREGAR NUEVO <<<"]
        
        # Determinar índice actual
        if funcionario_actual and funcionario_actual in funcionarios_existentes:
            indice_seleccionado = opciones.index(funcionario_actual)
        elif funcionario_actual and funcionario_actual.strip():
            # Funcionario actual no está en la lista pero tiene valor
            opciones.insert(-1, funcionario_actual)  # Agregar antes de "AGREGAR NUEVO"
            indice_seleccionado = opciones.index(funcionario_actual)
        else:
            indice_seleccionado = 0
        
        funcionario_seleccionado = st.selectbox(
            "Funcionario asignado:",
            options=opciones,
            index=indice_seleccionado,
            key=f"funcionario_dropdown_{key_suffix}"
        )
    
    with col2:
        # Mostrar cantidad de funcionarios
        st.metric("Total", len(funcionarios_existentes))
    
    # Opción 2: Campo para nuevo funcionario
    if funcionario_seleccionado == ">>> AGREGAR NUEVO <<<":
        funcionario_nuevo = st.text_input(
            "Nombre del nuevo funcionario:",
            value="",
            placeholder="Escribir nombre completo",
            key=f"funcionario_nuevo_{key_suffix}"
        )
        if funcionario_nuevo.strip():
            st.success(f"✅ **Nuevo funcionario:** {funcionario_nuevo.strip()}")
            return funcionario_nuevo.strip()
        else:
            st.warning("⚠️ Escriba el nombre del nuevo funcionario")
            return funcionario_actual  # Mantener el actual si no hay nuevo
    elif funcionario_seleccionado == "(Sin asignar)":
        return ""
    else:
        return funcionario_seleccionado


def crear_fecha_input_con_borrar_simple(label, fecha_actual, key_suffix):
    """
    Campo de fecha SIMPLE con opción de borrar
    - date_input normal
    - Checkbox "Sin fecha" para borrar
    """
    col1, col2 = st.columns([4, 1])
    
    with col2:
        # Checkbox para borrar/sin fecha
        sin_fecha = st.checkbox(
            "Sin fecha", 
            value=not es_fecha_valida(fecha_actual),
            key=f"sin_fecha_{key_suffix}",
            help="Marcar para dejar sin fecha"
        )
    
    with col1:
        if sin_fecha:
            # Mostrar campo deshabilitado
            st.date_input(
                label,
                value=None,
                disabled=True,
                key=f"fecha_disabled_{key_suffix}"
            )
            return None  # Retornar None para indicar sin fecha
        else:
            # Campo de fecha normal
            if es_fecha_valida(fecha_actual):
                try:
                    fecha_obj = procesar_fecha(fecha_actual)
                    fecha_valor = fecha_obj.date() if isinstance(fecha_obj, datetime) else fecha_obj
                except:
                    fecha_valor = date.today()
            else:
                fecha_valor = date.today()
            
            fecha_seleccionada = st.date_input(
                label,
                value=fecha_valor,
                key=f"fecha_input_{key_suffix}"
            )
            return fecha_seleccionada


def mostrar_edicion_registros(registros_df):
    """
    Editor MEJORADO con:
    - Funcionarios dropdown + agregar nuevo
    - Borrar fechas SIMPLE con checkbox
    - Sin recargas automáticas
    """
    
    st.markdown('<div class="subtitle">Editor de Registros (Versión Mejorada)</div>', unsafe_allow_html=True)
    
    st.info("""
    **🎯 MEJORAS EN ESTA VERSIÓN:**
    - 👥 **Funcionarios:** Dropdown con existentes + opción agregar nuevo
    - 📅 **Fechas:** Checkbox "Sin fecha" para borrar fácilmente
    - ⚡ **Sin recargas:** Cambios se aplican solo al guardar
    """)
    
    # Verificar que hay registros
    if registros_df.empty:
        st.warning("No hay registros disponibles para editar.")
        return registros_df
    
    # ===== SELECTOR DE REGISTRO =====
    st.markdown("### Selección de Registro")
    
    opciones_registros = [
        f"{registros_df.iloc[i]['Cod']} - {registros_df.iloc[i]['Entidad']} - {registros_df.iloc[i]['Nivel Información ']}"
        for i in range(len(registros_df))
    ]
    
    seleccion_registro = st.selectbox(
        "Seleccione un registro para editar:",
        options=opciones_registros,
        key="selector_registro_mejorado_v2"
    )
    
    indice_seleccionado = opciones_registros.index(seleccion_registro)
    row_original = registros_df.iloc[indice_seleccionado].copy()
    
    # ===== ENCABEZADO DEL REGISTRO =====
    st.markdown("---")
    st.markdown(f"### Editando Registro #{row_original['Cod']} - {row_original['Entidad']}")
    st.markdown(f"**Nivel de Información:** {row_original['Nivel Información ']}")
    st.markdown("---")
    
    # ===== FORMULARIO MEJORADO =====
    with st.form(f"form_edicion_v2_{indice_seleccionado}", clear_on_submit=False):
        
        # ===== SECCIÓN 1: INFORMACIÓN BÁSICA =====
        st.markdown("### 1. Información Básica")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.text_input("Código", value=row_original['Cod'], disabled=True)
        
        with col2:
            tipo_dato = st.selectbox(
                "Tipo de Dato",
                options=["", "Nuevo", "Actualizar"],
                index=["", "Nuevo", "Actualizar"].index(row_original.get('TipoDato', '')) if row_original.get('TipoDato', '') in ["", "Nuevo", "Actualizar"] else 0,
                key=f"tipo_dato_{indice_seleccionado}"
            )
        
        with col3:
            meses = ["", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
                     "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
            mes_proyectado = st.selectbox(
                "Mes Proyectado",
                options=meses,
                index=meses.index(row_original.get('Mes Proyectado', '')) if row_original.get('Mes Proyectado', '') in meses else 0,
                key=f"mes_proyectado_{indice_seleccionado}"
            )
        
        # Frecuencia
        frecuencias = ["", "Diaria", "Semanal", "Mensual", "Trimestral", "Semestral", "Anual"]
        frecuencia = st.selectbox(
            "Frecuencia de actualización",
            options=frecuencias,
            index=frecuencias.index(row_original.get('Frecuencia actualizacion ', '')) if row_original.get('Frecuencia actualizacion ', '') in frecuencias else 0,
            key=f"frecuencia_{indice_seleccionado}"
        )
        
        # ===== FUNCIONARIO MEJORADO CON DROPDOWN =====
        st.markdown("---")
        st.markdown("### 👥 Funcionario")
        funcionario_final = crear_selector_funcionario_dropdown(
            registros_df, 
            row_original.get('Funcionario', ''),
            indice_seleccionado
        )
        
        # ===== SECCIÓN 2: ACUERDOS Y COMPROMISOS =====
        st.markdown("---")
        st.markdown("### 2. Acuerdos y Compromisos")
        
        col1, col2 = st.columns(2)
        
        with col1:
            actas_interes = st.selectbox(
                "Actas de acercamiento y manifestación de interés",
                options=["", "Si", "No"],
                index=["", "Si", "No"].index(row_original.get('Actas de acercamiento y manifestación de interés', '')) if row_original.get('Actas de acercamiento y manifestación de interés', '') in ["", "Si", "No"] else 0,
                key=f"actas_interes_{indice_seleccionado}"
            )
            
            # Fecha de suscripción CON BORRAR SIMPLE
            fecha_suscripcion = crear_fecha_input_con_borrar_simple(
                "Suscripción acuerdo de compromiso",
                row_original.get('Suscripción acuerdo de compromiso', ''),
                f"suscripcion_{indice_seleccionado}"
            )
        
        with col2:
            # Fecha de entrega CON BORRAR SIMPLE
            fecha_entrega = crear_fecha_input_con_borrar_simple(
                "Entrega acuerdo de compromiso",
                row_original.get('Entrega acuerdo de compromiso', ''),
                f"entrega_{indice_seleccionado}"
            )
            
            acuerdo_compromiso = st.selectbox(
                "Acuerdo de compromiso",
                options=["", "Si", "No"],
                index=["", "Si", "No"].index(row_original.get('Acuerdo de compromiso', '')) if row_original.get('Acuerdo de compromiso', '') in ["", "Si", "No"] else 0,
                key=f"acuerdo_compromiso_{indice_seleccionado}"
            )
        
        # ===== SECCIÓN 3: GESTIÓN DE INFORMACIÓN =====
        st.markdown("---")
        st.markdown("### 3. Gestión de Información")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            gestion_acceso = st.selectbox(
                "Gestión acceso a los datos y documentos requeridos",
                options=["", "Si", "No"],
                index=["", "Si", "No"].index(row_original.get('Gestion acceso a los datos y documentos requeridos ', '')) if row_original.get('Gestion acceso a los datos y documentos requeridos ', '') in ["", "Si", "No"] else 0,
                key=f"gestion_acceso_{indice_seleccionado}"
            )
        
        with col2:
            # Fecha de entrega de información CON BORRAR SIMPLE
            fecha_entrega_info = crear_fecha_input_con_borrar_simple(
                "Fecha de entrega de información",
                row_original.get('Fecha de entrega de información', ''),
                f"entrega_info_{indice_seleccionado}"
            )
        
        with col3:
            # Plazo de análisis (solo lectura)
            plazo_analisis = row_original.get('Plazo de análisis', '')
            st.text_input(
                "Plazo de análisis (calculado)",
                value=plazo_analisis,
                disabled=True,
                help="Se calcula automáticamente"
            )
        
        # ===== SECCIÓN 4: ANÁLISIS Y CRONOGRAMA =====
        st.markdown("---")
        st.markdown("### 4. Análisis y Cronograma")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            # Análisis y cronograma fecha CON BORRAR SIMPLE
            analisis_cronograma = crear_fecha_input_con_borrar_simple(
                "Análisis y cronograma (fecha real)",
                row_original.get('Análisis y cronograma', ''),
                f"analisis_cronograma_{indice_seleccionado}"
            )
        
        with col2:
            cronograma_concertado = st.selectbox(
                "Cronograma Concertado",
                options=["", "Si", "No"],
                index=["", "Si", "No"].index(row_original.get('Cronograma Concertado', '')) if row_original.get('Cronograma Concertado', '') in ["", "Si", "No"] else 0,
                key=f"cronograma_concertado_{indice_seleccionado}"
            )
        
        with col3:
            plazo_cronograma = row_original.get('Plazo de cronograma', '')
            st.text_input(
                "Plazo de cronograma (calculado)",
                value=plazo_cronograma,
                disabled=True,
                help="Se calcula automáticamente"
            )
        
        with col4:
            seguimiento_acuerdos = st.selectbox(
                "Seguimiento a los acuerdos",
                options=["", "Si", "No"],
                index=["", "Si", "No"].index(row_original.get('Seguimiento a los acuerdos', '')) if row_original.get('Seguimiento a los acuerdos', '') in ["", "Si", "No"] else 0,
                key=f"seguimiento_acuerdos_{indice_seleccionado}"
            )
        
        # ===== SECCIÓN 5: ESTÁNDARES =====
        st.markdown("---")
        st.markdown("### 5. Estándares")
        
        st.markdown("#### Completitud de Estándares")
        col1, col2, col3 = st.columns(3)
        
        campos_estandares = [
            'Registro (completo)', 'ET (completo)', 'CO (completo)',
            'DD (completo)', 'REC (completo)', 'SERVICIO (completo)'
        ]
        
        estandares_values = {}
        for i, campo in enumerate(campos_estandares):
            col = [col1, col2, col3][i % 3]
            with col:
                valor_actual = row_original.get(campo, '')
                index = 0
                if valor_actual in ["", "Completo", "No aplica"]:
                    index = ["", "Completo", "No aplica"].index(valor_actual)
                
                estandares_values[campo] = st.selectbox(
                    campo,
                    options=["", "Completo", "No aplica"],
                    index=index,
                    key=f"estandar_{campo.replace(' ', '_').replace('(', '').replace(')', '')}_{indice_seleccionado}"
                )
        
        st.markdown("#### Fechas de Estándares")
        col1, col2 = st.columns(2)
        
        with col1:
            # Estándares fecha programada CON BORRAR SIMPLE
            estandares_programada = crear_fecha_input_con_borrar_simple(
                "Estándares (fecha programada)",
                row_original.get('Estándares (fecha programada)', ''),
                f"estandares_prog_{indice_seleccionado}"
            )
        
        with col2:
            # Estándares fecha real CON BORRAR SIMPLE
            estandares_real = crear_fecha_input_con_borrar_simple(
                "Estándares (fecha real)",
                row_original.get('Estándares', ''),
                f"estandares_real_{indice_seleccionado}"
            )
        
        # ===== SECCIÓN 6: PUBLICACIÓN =====
        st.markdown("---")
        st.markdown("### 6. Publicación")
        
        st.markdown("#### Proceso de Publicación")
        col1, col2, col3 = st.columns(3)
        
        campos_publicacion = [
            'Resultados de orientación técnica',
            'Verificación del servicio web geográfico',
            'Verificar Aprobar Resultados',
            'Revisar y validar los datos cargados en la base de datos',
            'Aprobación resultados obtenidos en la rientación',
            'Disponer datos temáticos',
            'Catálogo de recursos geográficos'
        ]
        
        publicacion_values = {}
        for i, campo in enumerate(campos_publicacion):
            col = [col1, col2, col3][i % 3]
            with col:
                valor_actual = row_original.get(campo, '')
                index = 0
                if valor_actual in ["", "Si", "No"]:
                    index = ["", "Si", "No"].index(valor_actual)
                
                publicacion_values[campo] = st.selectbox(
                    campo,
                    options=["", "Si", "No"],
                    index=index,
                    key=f"pub_{campo.replace(' ', '_').replace('(', '').replace(')', '')}_{indice_seleccionado}"
                )
        
        st.markdown("#### Fechas de Publicación")
        col1, col2 = st.columns(2)
        
        with col1:
            # Fecha de publicación programada CON BORRAR SIMPLE
            publicacion_programada = crear_fecha_input_con_borrar_simple(
                "Fecha de publicación programada",
                row_original.get('Fecha de publicación programada', ''),
                f"pub_prog_{indice_seleccionado}"
            )
        
        with col2:
            # Publicación fecha real CON BORRAR SIMPLE
            publicacion_real = crear_fecha_input_con_borrar_simple(
                "Publicación (fecha real)",
                row_original.get('Publicación', ''),
                f"pub_real_{indice_seleccionado}"
            )
        
        # ===== SECCIÓN 7: CIERRE =====
        st.markdown("---")
        st.markdown("### 7. Cierre")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            plazo_oficio = row_original.get('Plazo de oficio de cierre', '')
            st.text_input(
                "Plazo de oficio de cierre (calculado)",
                value=plazo_oficio,
                disabled=True,
                help="Se calcula automáticamente"
            )
            
            oficios_cierre = st.selectbox(
                "Oficios de cierre",
                options=["", "Si", "No"],
                index=["", "Si", "No"].index(row_original.get('Oficios de cierre', '')) if row_original.get('Oficios de cierre', '') in ["", "Si", "No"] else 0,
                key=f"oficios_cierre_{indice_seleccionado}"
            )
        
        with col2:
            # Fecha de oficio de cierre CON BORRAR SIMPLE
            fecha_oficio_cierre = crear_fecha_input_con_borrar_simple(
                "Fecha de oficio de cierre",
                row_original.get('Fecha de oficio de cierre', ''),
                f"oficio_cierre_{indice_seleccionado}"
            )
        
        with col3:
            estado = st.selectbox(
                "Estado",
                options=["", "En proceso", "En proceso oficio de cierre", "Completado", "Finalizado"],
                index=["", "En proceso", "En proceso oficio de cierre", "Completado", "Finalizado"].index(row_original.get('Estado', '')) if row_original.get('Estado', '') in ["", "En proceso", "En proceso oficio de cierre", "Completado", "Finalizado"] else 0,
                key=f"estado_{indice_seleccionado}"
            )
        
        # Observaciones
        st.markdown("### 8. Observaciones")
        observacion = st.text_area(
            "Observación",
            value=row_original.get('Observación', ''),
            key=f"observacion_{indice_seleccionado}"
        )
        
        # ===== INFORMACIÓN DE AVANCE =====
        st.markdown("---")
        st.markdown("### Información de Avance Actual")
        
        porcentaje_original = calcular_porcentaje_avance(row_original)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Porcentaje de Avance", f"{porcentaje_original}%")
        
        with col2:
            if porcentaje_original == 100:
                estado_avance = "Completado"
            elif porcentaje_original >= 75:
                estado_avance = "Avanzado"
            elif porcentaje_original >= 50:
                estado_avance = "En progreso"
            elif porcentaje_original >= 25:
                estado_avance = "Inicial"
            else:
                estado_avance = "Sin iniciar"
            
            st.info(f"**Estado:** {estado_avance}")
        
        with col3:
            if porcentaje_original == 0:
                proxima_accion = "Iniciar acuerdo de compromiso"
            elif porcentaje_original == 20:
                proxima_accion = "Completar análisis y cronograma"
            elif porcentaje_original == 40:
                proxima_accion = "Completar estándares"
            elif porcentaje_original == 70:
                proxima_accion = "Realizar publicación"
            elif porcentaje_original == 95:
                proxima_accion = "Emitir oficio de cierre"
            else:
                proxima_accion = "Continuar con el proceso"
            
            st.info(f"**Próxima acción:** {proxima_accion}")
        
        # ===== BOTÓN DE GUARDADO =====
        st.markdown("---")
        submitted = st.form_submit_button("💾 Guardar Registro", type="primary", use_container_width=True)
        
        if submitted:
            with st.spinner("💾 Guardando cambios..."):
                try:
                    # Crear copia del DataFrame
                    registros_df_actualizado = registros_df.copy()
                    
                    # Aplicar cambios básicos
                    registros_df_actualizado.at[indice_seleccionado, 'TipoDato'] = tipo_dato
                    registros_df_actualizado.at[indice_seleccionado, 'Mes Proyectado'] = mes_proyectado
                    registros_df_actualizado.at[indice_seleccionado, 'Frecuencia actualizacion '] = frecuencia
                    registros_df_actualizado.at[indice_seleccionado, 'Funcionario'] = funcionario_final
                    registros_df_actualizado.at[indice_seleccionado, 'Actas de acercamiento y manifestación de interés'] = actas_interes
                    registros_df_actualizado.at[indice_seleccionado, 'Acuerdo de compromiso'] = acuerdo_compromiso
                    registros_df_actualizado.at[indice_seleccionado, 'Gestion acceso a los datos y documentos requeridos '] = gestion_acceso
                    registros_df_actualizado.at[indice_seleccionado, 'Cronograma Concertado'] = cronograma_concertado
                    registros_df_actualizado.at[indice_seleccionado, 'Seguimiento a los acuerdos'] = seguimiento_acuerdos
                    registros_df_actualizado.at[indice_seleccionado, 'Oficios de cierre'] = oficios_cierre
                    registros_df_actualizado.at[indice_seleccionado, 'Estado'] = estado
                    registros_df_actualizado.at[indice_seleccionado, 'Observación'] = observacion
                    
                    # Fechas (SIMPLE: None = campo vacío, date = formato string)
                    fechas_a_procesar = [
                        (fecha_suscripcion, 'Suscripción acuerdo de compromiso'),
                        (fecha_entrega, 'Entrega acuerdo de compromiso'),
                        (fecha_entrega_info, 'Fecha de entrega de información'),
                        (analisis_cronograma, 'Análisis y cronograma'),
                        (estandares_programada, 'Estándares (fecha programada)'),
                        (estandares_real, 'Estándares'),
                        (publicacion_programada, 'Fecha de publicación programada'),
                        (publicacion_real, 'Publicación'),
                        (fecha_oficio_cierre, 'Fecha de oficio de cierre')
                    ]
                    
                    for fecha_obj, campo in fechas_a_procesar:
                        if fecha_obj is None:
                            # Sin fecha = campo vacío
                            registros_df_actualizado.at[indice_seleccionado, campo] = ''
                        else:
                            # Fecha válida = formato string
                            registros_df_actualizado.at[indice_seleccionado, campo] = fecha_obj.strftime('%d/%m/%Y')
                    
                    # Estándares
                    for campo, valor in estandares_values.items():
                        registros_df_actualizado.at[indice_seleccionado, campo] = valor
                    
                    # Publicación
                    for campo, valor in publicacion_values.items():
                        registros_df_actualizado.at[indice_seleccionado, campo] = valor
                    
                    # Aplicar validaciones automáticas
                    registros_df_actualizado = validar_reglas_negocio(registros_df_actualizado)
                    registros_df_actualizado = actualizar_plazo_analisis(registros_df_actualizado)
                    registros_df_actualizado = actualizar_plazo_cronograma(registros_df_actualizado)
                    registros_df_actualizado = actualizar_plazo_oficio_cierre(registros_df_actualizado)
                    
                    # Guardar en Google Sheets
                    exito, mensaje = guardar_datos_editados(registros_df_actualizado, crear_backup=True)
                    
                    if exito:
                        st.success(f"✅ {mensaje} Validaciones aplicadas correctamente.")
                        st.balloons()
                        
                        # ACTUALIZAR DATAFRAME EN MEMORIA
                        for col in registros_df_actualizado.columns:
                            registros_df.at[indice_seleccionado, col] = registros_df_actualizado.at[indice_seleccionado, col]
                    else:
                        st.error(mensaje)
                        
                except Exception as e:
                    st.error(f"❌ Error al guardar: {str(e)}")
    
    # ===== INFORMACIÓN ADICIONAL =====
    st.markdown("---")
    st.markdown("### ℹ️ Guía de Uso")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.info("""
        **👥 Funcionarios:**
        - Dropdown con existentes
        - ">>> AGREGAR NUEVO <<<" para nuevo
        - Se guarda automáticamente en la lista
        """)
    
    with col2:
        st.info("""
        **📅 Fechas Editables:**
        - Checkbox "Sin fecha" para borrar
        - Dejar sin marcar para asignar fecha
        - Simple y directo
        """)
    
    with col3:
        st.info("""
        **💾 Guardado:**
        - Sin recargas automáticas
        - Cambios se aplican al guardar
        - Validaciones automáticas incluidas
        """)
    
    return registros_df


def mostrar_edicion_registros_con_autenticacion(registros_df):
    """Wrapper con autenticación"""
    if verificar_autenticacion():
        return mostrar_edicion_registros(registros_df)
    else:
        st.markdown('<div class="subtitle">🔐 Acceso Restringido - Edición de Registros</div>', unsafe_allow_html=True)
        st.warning("🔒 **Se requiere autenticación para acceder a la edición de registros**")
        
        st.info("""
        **Para acceder a esta funcionalidad:**
        1. 🔐 Use el panel "Acceso Administrativo" en la barra lateral
        2. 👤 Ingrese las credenciales de administrador
        3. ✅ Una vez autenticado, podrá editar registros
        """)
        
        st.markdown("""
        <div style="text-align: center; padding: 2rem;">
            <div style="font-size: 4rem; color: #64748b;">🔐</div>
            <p style="color: #64748b; font-style: italic;">Protección de datos habilitada</p>
        </div>
        """, unsafe_allow_html=True)
        
        return registros_df


# ===== VERIFICACIÓN =====
if __name__ == "__main__":
    print("📝 Editor con Funcionarios Dropdown y Borrar Fechas Simple")
    print("🔧 Características:")
    print("   ✅ Funcionarios: Dropdown + agregar nuevo")
    print("   ✅ Fechas: Checkbox 'Sin fecha' para borrar simple")
    print("   ✅ Sin recargas automáticas")
    print("   ✅ Guardado inteligente con validaciones")
