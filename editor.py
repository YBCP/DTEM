# editor.py - VERSIÓN FINAL MEJORADA
"""
Editor de registros COMPLETAMENTE SIN RECARGAS + MEJORAS
- ELIMINADO: Todos los st.rerun()
- ELIMINADO: Todos los callbacks on_change  
- AGREGADO: Selector de funcionarios con dropdown + opción agregar nuevo
- AGREGADO: Botones para borrar fechas fácilmente
- Los cambios se procesan SOLO al presionar "Guardar"
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


def crear_selector_funcionario_mejorado(registros_df, indice_seleccionado, funcionario_actual):
    """
    Selector de funcionario mejorado:
    - Lista desplegable con funcionarios existentes
    - Opción para agregar funcionario nuevo
    - Simple y sin recargas
    """
    # Obtener lista de funcionarios únicos existentes
    funcionarios_existentes = []
    if 'Funcionario' in registros_df.columns:
        funcionarios_unicos = registros_df['Funcionario'].dropna().unique()
        funcionarios_existentes = [f for f in funcionarios_unicos if f and str(f).strip() and str(f).strip() not in ['nan', 'None']]
        funcionarios_existentes = sorted(set(funcionarios_existentes))
    
    st.markdown("**Funcionario Asignado:**")
    
    # Opción 1: Seleccionar de existentes
    opciones_funcionarios = ["(Seleccionar funcionario existente)"] + funcionarios_existentes
    
    # Determinar índice actual
    if funcionario_actual and funcionario_actual in funcionarios_existentes:
        indice_funcionario = opciones_funcionarios.index(funcionario_actual)
    else:
        indice_funcionario = 0
    
    funcionario_seleccionado = st.selectbox(
        "Funcionarios existentes:",
        options=opciones_funcionarios,
        index=indice_funcionario,
        key=f"funcionario_dropdown_{indice_seleccionado}"
    )
    
    # Opción 2: Agregar nuevo funcionario
    funcionario_nuevo = st.text_input(
        "O escribir funcionario nuevo:",
        value="" if funcionario_seleccionado != "(Seleccionar funcionario existente)" else funcionario_actual,
        placeholder="Escribir nombre del nuevo funcionario",
        key=f"funcionario_nuevo_{indice_seleccionado}"
    )
    
    # Determinar funcionario final
    if funcionario_nuevo.strip():
        funcionario_final = funcionario_nuevo.strip()
    elif funcionario_seleccionado != "(Seleccionar funcionario existente)":
        funcionario_final = funcionario_seleccionado
    else:
        funcionario_final = funcionario_actual
    
    # Mostrar funcionario final
    if funcionario_final:
        st.success(f"👤 **Funcionario asignado:** {funcionario_final}")
    else:
        st.info("👤 **Sin funcionario asignado**")
    
    return funcionario_final


def crear_selector_fecha_con_borrar(label, fecha_actual, key_base, help_text=None):
    """
    Selector de fecha mejorado con botón para borrar
    - date_input normal
    - Botón "Borrar" para limpiar la fecha fácilmente
    - Indicador visual del estado
    """
    col_label, col_fecha, col_borrar = st.columns([3, 4, 1])
    
    with col_label:
        st.markdown(f"**{label}:**")
    
    with col_fecha:
        # Convertir fecha actual a objeto date si es válida
        if es_fecha_valida(fecha_actual):
            try:
                fecha_obj = procesar_fecha(fecha_actual)
                fecha_valor = fecha_obj.date() if isinstance(fecha_obj, datetime) else fecha_obj
            except:
                fecha_valor = None
        else:
            fecha_valor = None
        
        # Mostrar date_input o placeholder
        if fecha_valor:
            fecha_seleccionada = st.date_input(
                label,
                value=fecha_valor,
                key=f"{key_base}_fecha",
                help=help_text,
                label_visibility="collapsed"
            )
        else:
            fecha_seleccionada = st.date_input(
                label,
                value=None,
                key=f"{key_base}_fecha",
                help=help_text,
                label_visibility="collapsed"
            )
    
    with col_borrar:
        # Botón para borrar fecha
        if st.button("🗑️", key=f"{key_base}_borrar", help="Borrar fecha", type="secondary"):
            # Marcar para borrar en el siguiente submit
            st.session_state[f"{key_base}_borrar_flag"] = True
            st.success("Fecha marcada para borrar")
    
    # Verificar si se marcó para borrar
    if st.session_state.get(f"{key_base}_borrar_flag", False):
        return None  # Devolver None para indicar fecha borrada
    
    return fecha_seleccionada


def mostrar_edicion_registros(registros_df):
    """
    Editor COMPLETAMENTE SIN RECARGAS + MEJORAS:
    - Selector de funcionarios mejorado
    - Botones para borrar fechas
    - Sin interrupciones durante edición
    """
    
    st.markdown('<div class="subtitle">Editor de Registros (Mejorado)</div>', unsafe_allow_html=True)
    
    # Información de mejoras
    st.info("""
    **🆕 MEJORAS EN ESTA VERSIÓN:**
    - 👥 **Funcionarios:** Lista desplegable + opción agregar nuevo
    - 🗑️ **Borrar fechas:** Botón "🗑️" para limpiar fechas fácilmente
    - ⚡ **Sin recargas:** Cambios se aplican solo al guardar
    """)
    
    # Verificar que hay registros
    if registros_df.empty:
        st.warning("No hay registros disponibles para editar.")
        return registros_df
    
    # ===== SELECTOR DE REGISTRO (SIN CALLBACK) =====
    st.markdown("### Selección de Registro")
    
    opciones_registros = [
        f"{registros_df.iloc[i]['Cod']} - {registros_df.iloc[i]['Entidad']} - {registros_df.iloc[i]['Nivel Información ']}"
        for i in range(len(registros_df))
    ]
    
    seleccion_registro = st.selectbox(
        "Seleccione un registro para editar:",
        options=opciones_registros,
        key="selector_registro_mejorado"
    )
    
    indice_seleccionado = opciones_registros.index(seleccion_registro)
    row_original = registros_df.iloc[indice_seleccionado].copy()
    
    # ===== ENCABEZADO DEL REGISTRO =====
    st.markdown("---")
    st.markdown(f"### Editando Registro #{row_original['Cod']} - {row_original['Entidad']}")
    st.markdown(f"**Nivel de Información:** {row_original['Nivel Información ']}")
    st.markdown("---")
    
    # ===== FORMULARIO MEJORADO SIN RECARGAS =====
    with st.form(f"form_edicion_mejorado_{indice_seleccionado}", clear_on_submit=False):
        
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
        
        # ===== FUNCIONARIO MEJORADO =====
        st.markdown("---")
        st.markdown("### 👥 Funcionario")
        funcionario_final = crear_selector_funcionario_mejorado(
            registros_df, 
            indice_seleccionado, 
            row_original.get('Funcionario', '')
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
            
            # Fecha de suscripción CON BOTÓN BORRAR
            fecha_suscripcion = crear_selector_fecha_con_borrar(
                "Suscripción acuerdo de compromiso",
                row_original.get('Suscripción acuerdo de compromiso', ''),
                f"suscripcion_{indice_seleccionado}"
            )
        
        with col2:
            # Fecha de entrega CON BOTÓN BORRAR
            fecha_entrega = crear_selector_fecha_con_borrar(
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
            # Fecha de entrega de información CON BOTÓN BORRAR
            fecha_entrega_info = crear_selector_fecha_con_borrar(
                "Fecha de entrega de información",
                row_original.get('Fecha de entrega de información', ''),
                f"entrega_info_{indice_seleccionado}"
            )
        
        with col3:
            # Plazo de análisis (solo lectura)
            plazo_analisis = row_original.get('Plazo de análisis', '')
            st.text_input(
                "Plazo de análisis (calculado automáticamente)",
                value=plazo_analisis,
                disabled=True,
                help="Se calcula automáticamente como 5 días hábiles después de la fecha de entrega"
            )
        
        # ===== SECCIÓN 4: ANÁLISIS Y CRONOGRAMA =====
        st.markdown("---")
        st.markdown("### 4. Análisis y Cronograma")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            # Análisis y cronograma fecha CON BOTÓN BORRAR
            analisis_cronograma = crear_selector_fecha_con_borrar(
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
                "Plazo de cronograma (calculado automáticamente)",
                value=plazo_cronograma,
                disabled=True,
                help="Se calcula como 3 días hábiles después del plazo de análisis"
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
            # Estándares fecha programada CON BOTÓN BORRAR
            estandares_programada = crear_selector_fecha_con_borrar(
                "Estándares (fecha programada)",
                row_original.get('Estándares (fecha programada)', ''),
                f"estandares_prog_{indice_seleccionado}"
            )
        
        with col2:
            # Estándares fecha real CON BOTÓN BORRAR
            estandares_real = crear_selector_fecha_con_borrar(
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
            # Fecha de publicación programada CON BOTÓN BORRAR
            publicacion_programada = crear_selector_fecha_con_borrar(
                "Fecha de publicación programada",
                row_original.get('Fecha de publicación programada', ''),
                f"pub_prog_{indice_seleccionado}"
            )
        
        with col2:
            # Publicación fecha real CON BOTÓN BORRAR
            publicacion_real = crear_selector_fecha_con_borrar(
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
                "Plazo de oficio de cierre (calculado automáticamente)",
                value=plazo_oficio,
                disabled=True,
                help="Se calcula como 7 días hábiles después de la fecha de publicación"
            )
            
            oficios_cierre = st.selectbox(
                "Oficios de cierre",
                options=["", "Si", "No"],
                index=["", "Si", "No"].index(row_original.get('Oficios de cierre', '')) if row_original.get('Oficios de cierre', '') in ["", "Si", "No"] else 0,
                key=f"oficios_cierre_{indice_seleccionado}"
            )
        
        with col2:
            # Fecha de oficio de cierre CON BOTÓN BORRAR
            fecha_oficio_cierre = crear_selector_fecha_con_borrar(
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
        
        # ===== INFORMACIÓN DE AVANCE (SOLO LECTURA) =====
        st.markdown("---")
        st.markdown("### Información de Avance Actual")
        
        porcentaje_original = calcular_porcentaje_avance(row_original)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Porcentaje de Avance Actual", f"{porcentaje_original}%")
        
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
        
        # ===== BOTÓN DE GUARDADO (ÚNICO PUNTO DE ACTUALIZACIÓN) =====
        st.markdown("---")
        st.markdown("### 💾 Guardar Cambios")
        
        submitted = st.form_submit_button("💾 Guardar Registro", type="primary", use_container_width=True)
        
        if submitted:
            # PROCESAR TODOS LOS CAMBIOS AQUÍ
            with st.spinner("💾 Guardando cambios y aplicando validaciones..."):
                try:
                    # Crear copia del DataFrame para modificar
                    registros_df_actualizado = registros_df.copy()
                    
                    # Aplicar TODOS los cambios del formulario
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
                    
                    # Fechas (convertir a formato string o vacío si se borró)
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
                            # Fecha fue marcada para borrar o está vacía
                            registros_df_actualizado.at[indice_seleccionado, campo] = ''
                        elif fecha_obj:
                            # Fecha válida, convertir a string
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
                        st.success(f"✅ {mensaje} Validaciones y plazos automáticos aplicados correctamente.")
                        st.balloons()
                        
                        # Limpiar flags de borrado para evitar conflictos
                        keys_to_clear = [key for key in st.session_state.keys() if key.endswith('_borrar_flag')]
                        for key in keys_to_clear:
                            del st.session_state[key]
                        
                        # ACTUALIZAR EL DATAFRAME EN MEMORIA PARA REFLEJAR CAMBIOS
                        for col in registros_df_actualizado.columns:
                            registros_df.at[indice_seleccionado, col] = registros_df_actualizado.at[indice_seleccionado, col]
                    else:
                        st.error(mensaje)
                        
                except Exception as e:
                    st.error(f"❌ Error al guardar: {str(e)}")
    
    # ===== INFORMACIÓN ADICIONAL (FUERA DEL FORMULARIO) =====
    st.markdown("---")
    st.markdown("### ℹ️ Información del Editor Mejorado")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.info("""
        **✅ Sin Recargas:**
        - Los cambios NO se aplican automáticamente
        - Use el botón "Guardar" para confirmar
        - Edición fluida sin interrupciones
        """)
    
    with col2:
        st.info("""
        **👥 Funcionarios Mejorado:**
        - Lista desplegable con existentes
        - Opción para agregar nuevo
        - Detección automática de duplicados
        """)
    
    with col3:
        st.info("""
        **🗑️ Borrar Fechas:**
        - Botón "🗑️" junto a cada fecha
        - Fácil limpieza de campos
        - Confirmación visual
        """)
    
    return registros_df


def mostrar_edicion_registros_con_autenticacion(registros_df):
    """
    Wrapper del editor que incluye verificación de autenticación
    """
    if verificar_autenticacion():
        # Usuario autenticado - mostrar editor mejorado
        return mostrar_edicion_registros(registros_df)
    else:
        # Usuario no autenticado - mostrar mensaje
        st.markdown('<div class="subtitle">🔐 Acceso Restringido - Edición de Registros</div>', unsafe_allow_html=True)
        
        st.warning("🔒 **Se requiere autenticación para acceder a la edición de registros**")
        
        st.info("""
        **Para acceder a esta funcionalidad:**
        1. 🔐 Use el panel "Acceso Administrativo" en la barra lateral
        2. 👤 Ingrese las credenciales de administrador
        3. ✅ Una vez autenticado, podrá editar registros
        
        **Funcionalidades disponibles sin autenticación:**
        - 📊 Dashboard y métricas
        - 📈 Seguimiento trimestral  
        - ⚠️ Alertas de vencimientos
        - 📋 Reportes y descargas
        """)
        
        st.markdown("""
        <div style="text-align: center; padding: 2rem;">
            <div style="font-size: 4rem; color: #64748b;">🔐</div>
            <p style="color: #64748b; font-style: italic;">Protección de datos habilitada</p>
        </div>
        """, unsafe_allow_html=True)
        
        return registros_df


# ===== VERIFICACIÓN FINAL =====
if __name__ == "__main__":
    print("📝 Editor MEJORADO FINAL cargado correctamente")
    print("🔧 Características:")
    print("   ✅ ELIMINADO: Todos los st.rerun()")
    print("   ✅ ELIMINADO: Todos los callbacks on_change")
    print("   ✅ AGREGADO: Selector de funcionarios con dropdown")
    print("   ✅ AGREGADO: Botones para borrar fechas fácilmente")
    print("   ✅ Los cambios se procesan SOLO al presionar 'Guardar'")
    print("   ✅ Experiencia de usuario optimizada")
    print("\n📝 Uso: from editor import mostrar_edicion_registros_con_autenticacion")
    print("🔄 Reemplaza el editor.py actual")
