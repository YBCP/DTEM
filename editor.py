# editor.py - VERSIÓN SIN RECARGAS AUTOMÁTICAS
"""
Editor de registros COMPLETAMENTE SIN RECARGAS
- ELIMINADO: Todos los st.rerun()
- ELIMINADO: Todos los callbacks on_change
- ELIMINADO: Actualizaciones automáticas
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


def mostrar_edicion_registros(registros_df):
    """
    Editor COMPLETAMENTE SIN RECARGAS AUTOMÁTICAS
    
    ✅ CAMBIOS CRÍTICOS:
    - NO hay st.rerun() en ninguna parte
    - NO hay callbacks on_change
    - NO hay actualizaciones automáticas
    - Los cambios se aplican SOLO al presionar "Guardar"
    """
    
    st.markdown('<div class="subtitle">Editor de Registros (Sin Recargas)</div>', unsafe_allow_html=True)
    
    # NUEVO: Advertencia clara
    st.warning("⚠️ **MODO SIN RECARGAS:** Los cambios NO se aplican automáticamente. Presione 'Guardar Registro' para confirmar cambios.")
    
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
    
    # CRÍTICO: SIN on_change
    seleccion_registro = st.selectbox(
        "Seleccione un registro para editar:",
        options=opciones_registros,
        key="selector_registro_sin_reload"
        # ✅ NO HAY on_change
    )
    
    indice_seleccionado = opciones_registros.index(seleccion_registro)
    row_original = registros_df.iloc[indice_seleccionado].copy()
    
    # ===== ENCABEZADO DEL REGISTRO =====
    st.markdown("---")
    st.markdown(f"### Editando Registro #{row_original['Cod']} - {row_original['Entidad']}")
    st.markdown(f"**Nivel de Información:** {row_original['Nivel Información ']}")
    st.markdown("---")
    
    # ===== CREAR FORMULARIO SIN RECARGAS =====
    # Usar form para evitar recargas hasta que se presione submit
    with st.form(f"form_edicion_{indice_seleccionado}", clear_on_submit=False):
        
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
        
        # Frecuencia y Funcionario
        col1, col2 = st.columns(2)
        
        with col1:
            frecuencias = ["", "Diaria", "Semanal", "Mensual", "Trimestral", "Semestral", "Anual"]
            frecuencia = st.selectbox(
                "Frecuencia de actualización",
                options=frecuencias,
                index=frecuencias.index(row_original.get('Frecuencia actualizacion ', '')) if row_original.get('Frecuencia actualizacion ', '') in frecuencias else 0,
                key=f"frecuencia_{indice_seleccionado}"
            )
        
        with col2:
            # Funcionario simplificado
            funcionario_actual = row_original.get('Funcionario', '')
            funcionario = st.text_input(
                "Funcionario",
                value=funcionario_actual,
                key=f"funcionario_{indice_seleccionado}"
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
            
            # Fecha de suscripción
            fecha_suscripcion_str = row_original.get('Suscripción acuerdo de compromiso', '')
            if es_fecha_valida(fecha_suscripcion_str):
                try:
                    fecha_suscripcion_obj = procesar_fecha(fecha_suscripcion_str)
                    fecha_suscripcion_valor = fecha_suscripcion_obj.date() if isinstance(fecha_suscripcion_obj, datetime) else fecha_suscripcion_obj
                except:
                    fecha_suscripcion_valor = None
            else:
                fecha_suscripcion_valor = None
            
            fecha_suscripcion = st.date_input(
                "Suscripción acuerdo de compromiso",
                value=fecha_suscripcion_valor,
                key=f"fecha_suscripcion_{indice_seleccionado}"
            )
        
        with col2:
            # Fecha de entrega
            fecha_entrega_str = row_original.get('Entrega acuerdo de compromiso', '')
            if es_fecha_valida(fecha_entrega_str):
                try:
                    fecha_entrega_obj = procesar_fecha(fecha_entrega_str)
                    fecha_entrega_valor = fecha_entrega_obj.date() if isinstance(fecha_entrega_obj, datetime) else fecha_entrega_obj
                except:
                    fecha_entrega_valor = None
            else:
                fecha_entrega_valor = None
            
            fecha_entrega = st.date_input(
                "Entrega acuerdo de compromiso",
                value=fecha_entrega_valor,
                key=f"fecha_entrega_{indice_seleccionado}"
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
            # Fecha de entrega de información
            fecha_entrega_info_str = row_original.get('Fecha de entrega de información', '')
            if es_fecha_valida(fecha_entrega_info_str):
                try:
                    fecha_entrega_info_obj = procesar_fecha(fecha_entrega_info_str)
                    fecha_entrega_info_valor = fecha_entrega_info_obj.date() if isinstance(fecha_entrega_info_obj, datetime) else fecha_entrega_info_obj
                except:
                    fecha_entrega_info_valor = None
            else:
                fecha_entrega_info_valor = None
            
            fecha_entrega_info = st.date_input(
                "Fecha de entrega de información",
                value=fecha_entrega_info_valor,
                key=f"fecha_entrega_info_{indice_seleccionado}"
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
            # Análisis y cronograma fecha
            analisis_cronograma_str = row_original.get('Análisis y cronograma', '')
            if es_fecha_valida(analisis_cronograma_str):
                try:
                    analisis_cronograma_obj = procesar_fecha(analisis_cronograma_str)
                    analisis_cronograma_valor = analisis_cronograma_obj.date() if isinstance(analisis_cronograma_obj, datetime) else analisis_cronograma_obj
                except:
                    analisis_cronograma_valor = None
            else:
                analisis_cronograma_valor = None
            
            analisis_cronograma = st.date_input(
                "Análisis y cronograma (fecha real)",
                value=analisis_cronograma_valor,
                key=f"analisis_cronograma_{indice_seleccionado}"
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
            # Estándares fecha programada
            estandares_prog_str = row_original.get('Estándares (fecha programada)', '')
            if es_fecha_valida(estandares_prog_str):
                try:
                    estandares_prog_obj = procesar_fecha(estandares_prog_str)
                    estandares_prog_valor = estandares_prog_obj.date() if isinstance(estandares_prog_obj, datetime) else estandares_prog_obj
                except:
                    estandares_prog_valor = None
            else:
                estandares_prog_valor = None
            
            estandares_programada = st.date_input(
                "Estándares (fecha programada)",
                value=estandares_prog_valor,
                key=f"estandares_programada_{indice_seleccionado}"
            )
        
        with col2:
            # Estándares fecha real
            estandares_str = row_original.get('Estándares', '')
            if es_fecha_valida(estandares_str):
                try:
                    estandares_obj = procesar_fecha(estandares_str)
                    estandares_valor = estandares_obj.date() if isinstance(estandares_obj, datetime) else estandares_obj
                except:
                    estandares_valor = None
            else:
                estandares_valor = None
            
            estandares_real = st.date_input(
                "Estándares (fecha real)",
                value=estandares_valor,
                key=f"estandares_real_{indice_seleccionado}"
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
            # Fecha de publicación programada
            pub_prog_str = row_original.get('Fecha de publicación programada', '')
            if es_fecha_valida(pub_prog_str):
                try:
                    pub_prog_obj = procesar_fecha(pub_prog_str)
                    pub_prog_valor = pub_prog_obj.date() if isinstance(pub_prog_obj, datetime) else pub_prog_obj
                except:
                    pub_prog_valor = None
            else:
                pub_prog_valor = None
            
            publicacion_programada = st.date_input(
                "Fecha de publicación programada",
                value=pub_prog_valor,
                key=f"publicacion_programada_{indice_seleccionado}"
            )
        
        with col2:
            # Publicación fecha real
            publicacion_str = row_original.get('Publicación', '')
            if es_fecha_valida(publicacion_str):
                try:
                    publicacion_obj = procesar_fecha(publicacion_str)
                    publicacion_valor = publicacion_obj.date() if isinstance(publicacion_obj, datetime) else publicacion_obj
                except:
                    publicacion_valor = None
            else:
                publicacion_valor = None
            
            publicacion_real = st.date_input(
                "Publicación (fecha real)",
                value=publicacion_valor,
                key=f"publicacion_real_{indice_seleccionado}"
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
            # Fecha de oficio de cierre
            oficio_cierre_str = row_original.get('Fecha de oficio de cierre', '')
            if es_fecha_valida(oficio_cierre_str):
                try:
                    oficio_cierre_obj = procesar_fecha(oficio_cierre_str)
                    oficio_cierre_valor = oficio_cierre_obj.date() if isinstance(oficio_cierre_obj, datetime) else oficio_cierre_obj
                except:
                    oficio_cierre_valor = None
            else:
                oficio_cierre_valor = None
            
            fecha_oficio_cierre = st.date_input(
                "Fecha de oficio de cierre",
                value=oficio_cierre_valor,
                key=f"fecha_oficio_cierre_{indice_seleccionado}"
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
        st.markdown("### Guardar Cambios")
        
        # CRÍTICO: submit_button NO causa recargas
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
                    registros_df_actualizado.at[indice_seleccionado, 'Funcionario'] = funcionario
                    registros_df_actualizado.at[indice_seleccionado, 'Actas de acercamiento y manifestación de interés'] = actas_interes
                    registros_df_actualizado.at[indice_seleccionado, 'Acuerdo de compromiso'] = acuerdo_compromiso
                    registros_df_actualizado.at[indice_seleccionado, 'Gestion acceso a los datos y documentos requeridos '] = gestion_acceso
                    registros_df_actualizado.at[indice_seleccionado, 'Cronograma Concertado'] = cronograma_concertado
                    registros_df_actualizado.at[indice_seleccionado, 'Seguimiento a los acuerdos'] = seguimiento_acuerdos
                    registros_df_actualizado.at[indice_seleccionado, 'Oficios de cierre'] = oficios_cierre
                    registros_df_actualizado.at[indice_seleccionado, 'Estado'] = estado
                    registros_df_actualizado.at[indice_seleccionado, 'Observación'] = observacion
                    
                    # Fechas (convertir a formato string)
                    if fecha_suscripcion:
                        registros_df_actualizado.at[indice_seleccionado, 'Suscripción acuerdo de compromiso'] = fecha_suscripcion.strftime('%d/%m/%Y')
                    if fecha_entrega:
                        registros_df_actualizado.at[indice_seleccionado, 'Entrega acuerdo de compromiso'] = fecha_entrega.strftime('%d/%m/%Y')
                    if fecha_entrega_info:
                        registros_df_actualizado.at[indice_seleccionado, 'Fecha de entrega de información'] = fecha_entrega_info.strftime('%d/%m/%Y')
                    if analisis_cronograma:
                        registros_df_actualizado.at[indice_seleccionado, 'Análisis y cronograma'] = analisis_cronograma.strftime('%d/%m/%Y')
                    if estandares_programada:
                        registros_df_actualizado.at[indice_seleccionado, 'Estándares (fecha programada)'] = estandares_programada.strftime('%d/%m/%Y')
                    if estandares_real:
                        registros_df_actualizado.at[indice_seleccionado, 'Estándares'] = estandares_real.strftime('%d/%m/%Y')
                    if publicacion_programada:
                        registros_df_actualizado.at[indice_seleccionado, 'Fecha de publicación programada'] = publicacion_programada.strftime('%d/%m/%Y')
                    if publicacion_real:
                        registros_df_actualizado.at[indice_seleccionado, 'Publicación'] = publicacion_real.strftime('%d/%m/%Y')
                    if fecha_oficio_cierre:
                        registros_df_actualizado.at[indice_seleccionado, 'Fecha de oficio de cierre'] = fecha_oficio_cierre.strftime('%d/%m/%Y')
                    
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
                        # ACTUALIZAR EL DATAFRAME EN MEMORIA PARA REFLEJAR CAMBIOS
                        for col in registros_df_actualizado.columns:
                            registros_df.at[indice_seleccionado, col] = registros_df_actualizado.at[indice_seleccionado, col]
                    else:
                        st.error(mensaje)
                        
                except Exception as e:
                    st.error(f"❌ Error al guardar: {str(e)}")
    
    # ===== INFORMACIÓN ADICIONAL (FUERA DEL FORMULARIO) =====
    st.markdown("---")
    st.markdown("### ℹ️ Información del Editor")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.info("""
        **✅ Modo Sin Recargas:**
        - Los cambios NO se aplican automáticamente
        - Use el botón "Guardar" para confirmar
        - No hay interrupciones durante la edición
        """)
    
    with col2:
        st.info("""
        **🔄 Validaciones Automáticas:**
        - Reglas de negocio se aplican al guardar
        - Plazos se calculan automáticamente
        - Fechas se validan correctamente
        """)
    
    with col3:
        st.info("""
        **💾 Guardado Inteligente:**
        - Backup automático antes de guardar
        - Sincronización con Google Sheets
        - Preservación de integridad de datos
        """)
    
    return registros_df


def mostrar_edicion_registros_con_autenticacion(registros_df):
    """
    Wrapper del editor que incluye verificación de autenticación
    """
    if verificar_autenticacion():
        # Usuario autenticado - mostrar editor sin recargas
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


# ===== VERIFICACIÓN SIN RECARGAS =====
if __name__ == "__main__":
    print("📝 Editor SIN RECARGAS cargado correctamente")
    print("🔧 Características:")
    print("   ✅ ELIMINADO: Todos los st.rerun()")
    print("   ✅ ELIMINADO: Todos los callbacks on_change")
    print("   ✅ ELIMINADO: Actualizaciones automáticas")
    print("   ✅ Los cambios se procesan SOLO al presionar 'Guardar'")
    print("   ✅ Formulario completo sin interrupciones")
    print("\n📝 Uso: from editor import mostrar_edicion_registros_con_autenticacion")
    print("🔄 Reemplaza el editor.py actual")
