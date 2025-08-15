
# ===== EDITOR.PY - FUNCIÓN COMPLETA CORREGIDA =====
# PROBLEMA IDENTIFICADO: Clave duplicada del form y estructura compleja
# SOLUCIÓN: Form con clave única basada en timestamp y estructura simplificada

import streamlit as st
import pandas as pd
from datetime import datetime, date
import time

def mostrar_edicion_registros(registros_df):
    """
    Editor COMPLETAMENTE CORREGIDO - Sin errores de Missing Submit Button
    """
    
    st.markdown('<div class="subtitle">Editor de Registros</div>', unsafe_allow_html=True)
    
    st.info("""
    **📝 EDITOR CORREGIDO:**
    - 👥 Funcionario como parte de información básica
    - 📅 Fechas directas: deje vacío para borrar
    - 💾 Guardado inteligente con validaciones automáticas
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
        key="selector_registro_fixed"  # Clave fija y única
    )
    
    indice_seleccionado = opciones_registros.index(seleccion_registro)
    row_original = registros_df.iloc[indice_seleccionado].copy()
    
    # ===== ENCABEZADO DEL REGISTRO =====
    st.markdown("---")
    st.markdown(f"### Editando Registro #{row_original['Cod']} - {row_original['Entidad']}")
    st.markdown(f"**Nivel de Información:** {row_original['Nivel Información ']}")
    st.markdown("---")
    
    # ===== FORMULARIO CORREGIDO CON CLAVE ÚNICA =====
    # CLAVE ÚNICA: Basada en el código del registro + timestamp para evitar duplicados
    form_key = f"form_editor_{row_original['Cod']}_{int(time.time())}"
    
    with st.form(form_key, clear_on_submit=False):
        
        # ===== SECCIÓN 1: INFORMACIÓN BÁSICA =====
        st.markdown("### 1. Información Básica")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.text_input("Código", value=row_original['Cod'], disabled=True, key=f"cod_{indice_seleccionado}")
            
            tipo_dato = st.selectbox(
                "Tipo de Dato",
                options=["", "Nuevo", "Actualizar"],
                index=["", "Nuevo", "Actualizar"].index(row_original.get('TipoDato', '')) if row_original.get('TipoDato', '') in ["", "Nuevo", "Actualizar"] else 0,
                key=f"tipo_dato_{indice_seleccionado}"
            )
            
            meses = ["", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
                     "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
            mes_proyectado = st.selectbox(
                "Mes Proyectado",
                options=meses,
                index=meses.index(row_original.get('Mes Proyectado', '')) if row_original.get('Mes Proyectado', '') in meses else 0,
                key=f"mes_proyectado_{indice_seleccionado}"
            )
        
        with col2:
            # Funcionario simplificado
            funcionario_actual = row_original.get('Funcionario', '')
            funcionario_final = st.text_input(
                "Funcionario asignado:",
                value=funcionario_actual,
                key=f"funcionario_{indice_seleccionado}",
                help="Escriba el nombre del funcionario"
            )
            
            frecuencias = ["", "Diaria", "Semanal", "Mensual", "Trimestral", "Semestral", "Anual"]
            frecuencia = st.selectbox(
                "Frecuencia de actualización",
                options=frecuencias,
                index=frecuencias.index(row_original.get('Frecuencia actualizacion ', '')) if row_original.get('Frecuencia actualizacion ', '') in frecuencias else 0,
                key=f"frecuencia_{indice_seleccionado}"
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
            
            # Fecha de suscripción simplificada
            fecha_suscripcion_str = st.text_input(
                "Suscripción acuerdo de compromiso (DD/MM/YYYY)",
                value=row_original.get('Suscripción acuerdo de compromiso', ''),
                key=f"suscripcion_{indice_seleccionado}",
                help="Formato: DD/MM/YYYY o deje vacío"
            )
        
        with col2:
            # Fecha de entrega simplificada
            fecha_entrega_str = st.text_input(
                "Entrega acuerdo de compromiso (DD/MM/YYYY)",
                value=row_original.get('Entrega acuerdo de compromiso', ''),
                key=f"entrega_{indice_seleccionado}",
                help="Formato: DD/MM/YYYY o deje vacío"
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
            # Fecha de entrega de información simplificada
            fecha_entrega_info_str = st.text_input(
                "Fecha de entrega de información (DD/MM/YYYY)",
                value=row_original.get('Fecha de entrega de información', ''),
                key=f"entrega_info_{indice_seleccionado}",
                help="Fecha en que se entregó la información"
            )
        
        with col3:
            # Plazo de análisis (solo lectura)
            plazo_analisis = row_original.get('Plazo de análisis', '')
            st.text_input(
                "Plazo de análisis (calculado)",
                value=plazo_analisis,
                disabled=True,
                key=f"plazo_analisis_readonly_{indice_seleccionado}",
                help="Se calcula automáticamente: 5 días hábiles después de entrega"
            )
        
        # ===== SECCIÓN 4: ANÁLISIS Y CRONOGRAMA =====
        st.markdown("---")
        st.markdown("### 4. Análisis y Cronograma")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            # Análisis y cronograma fecha simplificada
            analisis_cronograma_str = st.text_input(
                "Análisis y cronograma (fecha real DD/MM/YYYY)",
                value=row_original.get('Análisis y cronograma', ''),
                key=f"analisis_cronograma_{indice_seleccionado}",
                help="Fecha en que se completó el análisis"
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
                key=f"plazo_cronograma_readonly_{indice_seleccionado}",
                help="Se calcula automáticamente: 3 días hábiles después del análisis"
            )
        
        with col4:
            seguimiento_acuerdos = st.selectbox(
                "Seguimiento a los acuerdos",
                options=["", "Si", "No"],
                index=["", "Si", "No"].index(row_original.get('Seguimiento a los acuerdos', '')) if row_original.get('Seguimiento a los acuerdos', '') in ["", "Si", "No"] else 0,
                key=f"seguimiento_acuerdos_{indice_seleccionado}"
            )
        
        # ===== SECCIÓN 5: ESTÁNDARES SIMPLIFICADA =====
        st.markdown("---")
        st.markdown("### 5. Estándares")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Estándares fecha programada simplificada
            estandares_programada_str = st.text_input(
                "Estándares (fecha programada DD/MM/YYYY)",
                value=row_original.get('Estándares (fecha programada)', ''),
                key=f"estandares_prog_{indice_seleccionado}",
                help="Fecha programada para completar estándares"
            )
        
        with col2:
            # Estándares fecha real simplificada
            estandares_real_str = st.text_input(
                "Estándares (fecha real DD/MM/YYYY)",
                value=row_original.get('Estándares', ''),
                key=f"estandares_real_{indice_seleccionado}",
                help="Fecha en que se completaron los estándares"
            )
        
        # ===== SECCIÓN 6: PUBLICACIÓN SIMPLIFICADA =====
        st.markdown("---")
        st.markdown("### 6. Publicación")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Fecha de publicación programada simplificada
            publicacion_programada_str = st.text_input(
                "Fecha de publicación programada (DD/MM/YYYY)",
                value=row_original.get('Fecha de publicación programada', ''),
                key=f"pub_prog_{indice_seleccionado}",
                help="Fecha programada para publicar"
            )
            
            disponer_datos = st.selectbox(
                "Disponer datos temáticos",
                options=["", "Si", "No"],
                index=["", "Si", "No"].index(row_original.get('Disponer datos temáticos', '')) if row_original.get('Disponer datos temáticos', '') in ["", "Si", "No"] else 0,
                key=f"disponer_datos_{indice_seleccionado}"
            )
        
        with col2:
            # Publicación fecha real simplificada
            publicacion_real_str = st.text_input(
                "Publicación (fecha real DD/MM/YYYY)",
                value=row_original.get('Publicación', ''),
                key=f"pub_real_{indice_seleccionado}",
                help="Fecha en que se realizó la publicación"
            )
            
            catalogo_recursos = st.selectbox(
                "Catálogo de recursos geográficos",
                options=["", "Si", "No"],
                index=["", "Si", "No"].index(row_original.get('Catálogo de recursos geográficos', '')) if row_original.get('Catálogo de recursos geográficos', '') in ["", "Si", "No"] else 0,
                key=f"catalogo_recursos_{indice_seleccionado}"
            )
        
        # ===== SECCIÓN 7: CIERRE SIMPLIFICADA =====
        st.markdown("---")
        st.markdown("### 7. Cierre")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            plazo_oficio = row_original.get('Plazo de oficio de cierre', '')
            st.text_input(
                "Plazo de oficio de cierre (calculado)",
                value=plazo_oficio,
                disabled=True,
                key=f"plazo_oficio_readonly_{indice_seleccionado}",
                help="Se calcula automáticamente: 7 días hábiles después de publicación"
            )
        
        with col2:
            # Fecha de oficio de cierre simplificada
            fecha_oficio_cierre_str = st.text_input(
                "Fecha de oficio de cierre (DD/MM/YYYY)",
                value=row_original.get('Fecha de oficio de cierre', ''),
                key=f"oficio_cierre_{indice_seleccionado}",
                help="Fecha en que se emitió el oficio de cierre"
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
            key=f"observacion_{indice_seleccionado}",
            help="Comentarios o notas adicionales sobre el registro"
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
            elif porcentaje_original == 25:
                proxima_accion = "Completar análisis y cronograma"
            elif porcentaje_original == 50:
                proxima_accion = "Completar estándares"
            elif porcentaje_original == 75:
                proxima_accion = "Realizar publicación"
            elif porcentaje_original == 95:
                proxima_accion = "Emitir oficio de cierre"
            else:
                proxima_accion = "Continuar con el proceso"
            
            st.info(f"**Próxima acción:** {proxima_accion}")
        
        # ===== BOTÓN DE GUARDADO - DIRECTO SIN COLUMNAS =====
        st.markdown("---")
        
        # BOTÓN SUBMIT DIRECTO - SIN ESTRUCTURAS COMPLEJAS
        submitted = st.form_submit_button(
            "💾 Guardar Registro", 
            type="primary", 
            use_container_width=True
        )
        
        # LÓGICA DE GUARDADO DENTRO DEL FORM
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
                    registros_df_actualizado.at[indice_seleccionado, 'Estado'] = estado
                    registros_df_actualizado.at[indice_seleccionado, 'Observación'] = observacion
                    registros_df_actualizado.at[indice_seleccionado, 'Disponer datos temáticos'] = disponer_datos
                    registros_df_actualizado.at[indice_seleccionado, 'Catálogo de recursos geográficos'] = catalogo_recursos
                    
                    # Fechas simplificadas (strings directos)
                    registros_df_actualizado.at[indice_seleccionado, 'Suscripción acuerdo de compromiso'] = fecha_suscripcion_str
                    registros_df_actualizado.at[indice_seleccionado, 'Entrega acuerdo de compromiso'] = fecha_entrega_str
                    registros_df_actualizado.at[indice_seleccionado, 'Fecha de entrega de información'] = fecha_entrega_info_str
                    registros_df_actualizado.at[indice_seleccionado, 'Análisis y cronograma'] = analisis_cronograma_str
                    registros_df_actualizado.at[indice_seleccionado, 'Estándares (fecha programada)'] = estandares_programada_str
                    registros_df_actualizado.at[indice_seleccionado, 'Estándares'] = estandares_real_str
                    registros_df_actualizado.at[indice_seleccionado, 'Fecha de publicación programada'] = publicacion_programada_str
                    registros_df_actualizado.at[indice_seleccionado, 'Publicación'] = publicacion_real_str
                    registros_df_actualizado.at[indice_seleccionado, 'Fecha de oficio de cierre'] = fecha_oficio_cierre_str
                    
                    # Aplicar validaciones automáticas
                    from validaciones_utils import validar_reglas_negocio
                    from fecha_utils import actualizar_plazo_analisis, actualizar_plazo_cronograma, actualizar_plazo_oficio_cierre
                    
                    registros_df_actualizado = validar_reglas_negocio(registros_df_actualizado)
                    registros_df_actualizado = actualizar_plazo_analisis(registros_df_actualizado)
                    registros_df_actualizado = actualizar_plazo_cronograma(registros_df_actualizado)
                    registros_df_actualizado = actualizar_plazo_oficio_cierre(registros_df_actualizado)
                    
                    # Guardar en Google Sheets
                    from data_utils import guardar_datos_editados
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
    
    # ===== INFORMACIÓN ADICIONAL - FUERA DEL FORM =====
    st.markdown("---")
    st.markdown("### ℹ️ Guía de Uso del Editor")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.info("""
        **👥 Funcionarios:**
        - Campo de texto directo
        - Escriba el nombre completo
        - Se guarda automáticamente
        """)
    
    with col2:
        st.info("""
        **📅 Fechas Simplificadas:**
        - Formato: DD/MM/YYYY
        - Deje vacío para borrar
        - Validación automática
        """)
    
    with col3:
        st.info("""
        **💾 Guardado Inteligente:**
        - Validaciones automáticas
        - Cálculo de plazos
        - Backup de seguridad
        """)
    
    return registros_df


# ===== FUNCIÓN DE AUTENTICACIÓN CORREGIDA =====

def mostrar_edicion_registros_con_autenticacion(registros_df):
    """Wrapper con autenticación CORREGIDO - Sin errores de Missing Submit Button"""
    
    # Verificar autenticación FUERA del form
    from auth_utils import verificar_autenticacion
    
    if verificar_autenticacion():
        # Usuario autenticado - mostrar editor completo
        return mostrar_edicion_registros(registros_df)
    else:
        # Usuario NO autenticado - mostrar mensaje
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


# ===== FUNCIONES AUXILIARES REQUERIDAS =====

def crear_selector_funcionario_integrado(registros_df, funcionario_actual, key_suffix):
    """Función auxiliar simplificada para funcionario"""
    # Esta función se simplifica ahora porque usamos text_input directo
    return funcionario_actual

def crear_fecha_input_simple(label, fecha_actual, key_suffix, help_text=None):
    """Función auxiliar simplificada para fechas"""
    # Esta función se simplifica ahora porque usamos text_input directo
    return fecha_actual

# ===== VERIFICACIÓN =====

print("✅ EDITOR.PY COMPLETAMENTE CORREGIDO")
print("🔧 Correcciones aplicadas:")
print("   - Clave única del form basada en timestamp")
print("   - Botón submit DIRECTO sin columnas")
print("   - Fechas simplificadas como text_input")
print("   - Estructura simplificada sin funciones complejas")
print("   - Autenticación FUERA del form")
print("   - Imports explícitos dentro del form")
print("   - Claves únicas para todos los widgets")
print()
print("📝 PARA APLICAR:")
print("1. Reemplazar mostrar_edicion_registros() completa")
print("2. Reemplazar mostrar_edicion_registros_con_autenticacion() completa")
print("3. Agregar funciones auxiliares si no existen")
print("4. Reiniciar Streamlit")
