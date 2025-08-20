# editor_limpio.py - Editor sin íconos ni información innecesaria
"""
Editor de Registros Limpio - Solo formulario esencial
Incluye TODOS los campos: estándares, calculados y completitud
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date
import time

# ===== IMPORTS CON FALLBACKS =====
try:
    from data_utils import calcular_porcentaje_avance, guardar_datos_editados
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
    
    def guardar_datos_editados(df, crear_backup=True):
        try:
            from sheets_utils import get_sheets_manager
            manager = get_sheets_manager()
            exito = manager.escribir_hoja(df, "Registros", limpiar_hoja=True)
            return exito, "Datos guardados" if exito else "Error al guardar"
        except Exception as e:
            return False, f"Error: {str(e)}"

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


def mostrar_edicion_registros(registros_df):
    """Editor limpio sin íconos ni información innecesaria"""
    
    st.subheader("Editor de Registros")
    
    if registros_df.empty:
        st.warning("No hay registros disponibles para editar.")
        return registros_df
    
    # Selector de registro
    opciones_registros = [
        f"{registros_df.iloc[i]['Cod']} - {registros_df.iloc[i]['Entidad']} - {registros_df.iloc[i]['Nivel Información ']}"
        for i in range(len(registros_df))
    ]
    
    seleccion_registro = st.selectbox(
        "Seleccionar registro:",
        options=opciones_registros,
        key="selector_registro_limpio"
    )
    
    indice_seleccionado = opciones_registros.index(seleccion_registro)
    row_original = registros_df.iloc[indice_seleccionado].copy()
    
    st.markdown(f"**Editando:** {row_original['Cod']} - {row_original['Entidad']}")
    
    # FORMULARIO PRINCIPAL
    form_key = f"form_editor_limpio_{row_original['Cod']}_{int(time.time())}"
    
    with st.form(form_key, clear_on_submit=False):
        
        # INFORMACIÓN BÁSICA
        st.markdown("**Información Básica**")
        col1, col2 = st.columns(2)
        
        with col1:
            codigo = st.text_input("Código", value=str(row_original.get('Cod', '')), key=f"codigo_{indice_seleccionado}")
            tipo_dato = st.selectbox("Tipo de Dato", 
                options=["", "Geográfico", "Estadístico", "Catastral", "Otro"],
                index=["", "Geográfico", "Estadístico", "Catastral", "Otro"].index(row_original.get('TipoDato', '')) if row_original.get('TipoDato', '') in ["", "Geográfico", "Estadístico", "Catastral", "Otro"] else 0,
                key=f"tipo_dato_{indice_seleccionado}")
            
        with col2:
            mes_proyectado = st.text_input("Mes Proyectado", value=str(row_original.get('Mes Proyectado', '')), key=f"mes_{indice_seleccionado}")
            funcionario = st.text_input("Funcionario", value=str(row_original.get('Funcionario de enlace', '')), key=f"funcionario_{indice_seleccionado}")
        
        frecuencia = st.selectbox("Frecuencia",
            options=["", "Anual", "Mensual", "Trimestral", "Semestral"],
            index=["", "Anual", "Mensual", "Trimestral", "Semestral"].index(row_original.get('Frecuencia', '')) if row_original.get('Frecuencia', '') in ["", "Anual", "Mensual", "Trimestral", "Semestral"] else 0,
            key=f"frecuencia_{indice_seleccionado}")
        
        # ACUERDOS Y COMPROMISOS
        st.markdown("**Acuerdos y Compromisos**")
        col1, col2 = st.columns(2)
        
        with col1:
            actas_interes = st.selectbox("Actas de interés",
                options=["", "Si", "No"],
                index=["", "Si", "No"].index(row_original.get('Actas de interés', '')) if row_original.get('Actas de interés', '') in ["", "Si", "No"] else 0,
                key=f"actas_{indice_seleccionado}")
            
            suscripcion = st.selectbox("Suscripción",
                options=["", "Si", "No", "Pendiente"],
                index=["", "Si", "No", "Pendiente"].index(row_original.get('Suscripción', '')) if row_original.get('Suscripción', '') in ["", "Si", "No", "Pendiente"] else 0,
                key=f"suscripcion_{indice_seleccionado}")
        
        with col2:
            entrega = st.selectbox("Entrega",
                options=["", "Si", "No", "Parcial"],
                index=["", "Si", "No", "Parcial"].index(row_original.get('Entrega', '')) if row_original.get('Entrega', '') in ["", "Si", "No", "Parcial"] else 0,
                key=f"entrega_{indice_seleccionado}")
            
            acuerdo_compromiso = st.selectbox("Acuerdo de compromiso",
                options=["", "Si", "No"],
                index=["", "Si", "No"].index(row_original.get('Acuerdo de compromiso', '')) if row_original.get('Acuerdo de compromiso', '') in ["", "Si", "No"] else 0,
                key=f"acuerdo_{indice_seleccionado}")
        
        # GESTIÓN DE INFORMACIÓN
        st.markdown("**Gestión de Información**")
        col1, col2 = st.columns(2)
        
        with col1:
            acceso_datos = st.selectbox("Acceso a datos",
                options=["", "Si", "No", "Limitado"],
                index=["", "Si", "No", "Limitado"].index(row_original.get('Acceso a datos', '')) if row_original.get('Acceso a datos', '') in ["", "Si", "No", "Limitado"] else 0,
                key=f"acceso_{indice_seleccionado}")
            
            analisis_informacion = st.text_input("Análisis de información",
                value=str(row_original.get('Análisis de información', '')),
                key=f"analisis_info_{indice_seleccionado}")
        
        with col2:
            fecha_entrega = st.text_input("Fecha de entrega (DD/MM/YYYY)",
                value=str(row_original.get('Fecha de entrega de información', '')),
                key=f"fecha_entrega_{indice_seleccionado}")
            
            cronograma_concertado = st.selectbox("Cronograma concertado",
                options=["", "Si", "No", "En proceso"],
                index=["", "Si", "No", "En proceso"].index(row_original.get('Cronograma concertado', '')) if row_original.get('Cronograma concertado', '') in ["", "Si", "No", "En proceso"] else 0,
                key=f"cronograma_{indice_seleccionado}")
        
        # ANÁLISIS Y FECHAS
        st.markdown("**Análisis y Cronograma**")
        col1, col2 = st.columns(2)
        
        with col1:
            analisis_programada = st.text_input("Análisis programada (DD/MM/YYYY)",
                value=str(row_original.get('Análisis de información (fecha programada)', '')),
                key=f"analisis_prog_{indice_seleccionado}")
            
            analisis_real = st.text_input("Análisis real (DD/MM/YYYY)",
                value=str(row_original.get('Análisis y cronograma', '')),
                key=f"analisis_real_{indice_seleccionado}")
        
        with col2:
            seguimiento_acuerdos = st.text_area("Seguimiento de acuerdos",
                value=str(row_original.get('Seguimiento de acuerdos', '')),
                height=80,
                key=f"seguimiento_{indice_seleccionado}")
        
        # ESTÁNDARES COMPLETOS
        st.markdown("**Estándares**")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            registro = st.selectbox("Registro",
                options=["", "Completo", "Incompleto", "No aplica"],
                index=["", "Completo", "Incompleto", "No aplica"].index(row_original.get('Registro', '')) if row_original.get('Registro', '') in ["", "Completo", "Incompleto", "No aplica"] else 0,
                key=f"registro_{indice_seleccionado}")
                
            et = st.selectbox("ET",
                options=["", "Completo", "Incompleto", "No aplica"],
                index=["", "Completo", "Incompleto", "No aplica"].index(row_original.get('ET', '')) if row_original.get('ET', '') in ["", "Completo", "Incompleto", "No aplica"] else 0,
                key=f"et_{indice_seleccionado}")
        
        with col2:
            co = st.selectbox("CO",
                options=["", "Completo", "Incompleto", "No aplica"],
                index=["", "Completo", "Incompleto", "No aplica"].index(row_original.get('CO', '')) if row_original.get('CO', '') in ["", "Completo", "Incompleto", "No aplica"] else 0,
                key=f"co_{indice_seleccionado}")
                
            dd = st.selectbox("DD",
                options=["", "Completo", "Incompleto", "No aplica"],
                index=["", "Completo", "Incompleto", "No aplica"].index(row_original.get('DD', '')) if row_original.get('DD', '') in ["", "Completo", "Incompleto", "No aplica"] else 0,
                key=f"dd_{indice_seleccionado}")
        
        with col3:
            rec = st.selectbox("REC",
                options=["", "Completo", "Incompleto", "No aplica"],
                index=["", "Completo", "Incompleto", "No aplica"].index(row_original.get('REC', '')) if row_original.get('REC', '') in ["", "Completo", "Incompleto", "No aplica"] else 0,
                key=f"rec_{indice_seleccionado}")
                
            servicio = st.selectbox("SERVICIO",
                options=["", "Completo", "Incompleto", "No aplica"],
                index=["", "Completo", "Incompleto", "No aplica"].index(row_original.get('SERVICIO', '')) if row_original.get('SERVICIO', '') in ["", "Completo", "Incompleto", "No aplica"] else 0,
                key=f"servicio_{indice_seleccionado}")
        
        # FECHAS DE ESTÁNDARES
        col1, col2 = st.columns(2)
        
        with col1:
            estandares_programada = st.text_input("Estándares programada (DD/MM/YYYY)",
                value=str(row_original.get('Estándares (fecha programada)', '')),
                key=f"estandares_prog_{indice_seleccionado}")
        
        with col2:
            estandares_real = st.text_input("Estándares real (DD/MM/YYYY)",
                value=str(row_original.get('Estándares', '')),
                key=f"estandares_real_{indice_seleccionado}")
        
        # ORIENTACIÓN Y VERIFICACIONES
        st.markdown("**Orientación y Verificaciones**")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            resultados_orientacion = st.selectbox("Resultados orientación técnica",
                options=["", "Si", "No", "Completo"],
                index=["", "Si", "No", "Completo"].index(row_original.get('Resultados de orientación técnica', '')) if row_original.get('Resultados de orientación técnica', '') in ["", "Si", "No", "Completo"] else 0,
                key=f"orientacion_{indice_seleccionado}")
        
        with col2:
            verificacion_servicio = st.selectbox("Verificación servicio web",
                options=["", "Si", "No", "Completo"],
                index=["", "Si", "No", "Completo"].index(row_original.get('Verificación del servicio web geográfico', '')) if row_original.get('Verificación del servicio web geográfico', '') in ["", "Si", "No", "Completo"] else 0,
                key=f"verificacion_{indice_seleccionado}")
        
        with col3:
            verificar_aprobar = st.selectbox("Verificar Aprobar",
                options=["", "Si", "No", "Pendiente"],
                index=["", "Si", "No", "Pendiente"].index(row_original.get('Verificar Aprobar', '')) if row_original.get('Verificar Aprobar', '') in ["", "Si", "No", "Pendiente"] else 0,
                key=f"verificar_aprobar_{indice_seleccionado}")
        
        col1, col2 = st.columns(2)
        
        with col1:
            revisar_validar = st.selectbox("Revisar validar",
                options=["", "Si", "No", "En proceso"],
                index=["", "Si", "No", "En proceso"].index(row_original.get('Revisar validar', '')) if row_original.get('Revisar validar', '') in ["", "Si", "No", "En proceso"] else 0,
                key=f"revisar_{indice_seleccionado}")
        
        with col2:
            aprobacion_resultados = st.selectbox("Aprobación resultados",
                options=["", "Si", "No", "Pendiente"],
                index=["", "Si", "No", "Pendiente"].index(row_original.get('Aprobación de resultados', '')) if row_original.get('Aprobación de resultados', '') in ["", "Si", "No", "Pendiente"] else 0,
                key=f"aprobacion_{indice_seleccionado}")
        
        # PUBLICACIÓN
        st.markdown("**Publicación**")
        col1, col2 = st.columns(2)
        
        with col1:
            publicacion_programada = st.text_input("Publicación programada (DD/MM/YYYY)",
                value=str(row_original.get('Fecha de publicación programada', '')),
                key=f"pub_prog_{indice_seleccionado}")
            
            publicacion_real = st.text_input("Publicación real (DD/MM/YYYY)",
                value=str(row_original.get('Publicación', '')),
                key=f"pub_real_{indice_seleccionado}")
        
        with col2:
            disponer_datos = st.selectbox("Disponer datos temáticos",
                options=["", "Si", "No", "En proceso"],
                index=["", "Si", "No", "En proceso"].index(row_original.get('Disponer de los datos temáticos', '')) if row_original.get('Disponer de los datos temáticos', '') in ["", "Si", "No", "En proceso"] else 0,
                key=f"disponer_{indice_seleccionado}")
            
            catalogo_recursos = st.selectbox("Catálogo recursos",
                options=["", "Si", "No", "En proceso"],
                index=["", "Si", "No", "En proceso"].index(row_original.get('Catálogo de recursos geográficos', '')) if row_original.get('Catálogo de recursos geográficos', '') in ["", "Si", "No", "En proceso"] else 0,
                key=f"catalogo_{indice_seleccionado}")
        
        # CIERRE
        st.markdown("**Cierre**")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            oficios_cierre = st.selectbox("Oficios de cierre",
                options=["", "Si", "No", "Pendiente"],
                index=["", "Si", "No", "Pendiente"].index(row_original.get('Oficios de cierre', '')) if row_original.get('Oficios de cierre', '') in ["", "Si", "No", "Pendiente"] else 0,
                key=f"oficios_{indice_seleccionado}")
        
        with col2:
            fecha_oficio_cierre = st.text_input("Fecha oficio cierre (DD/MM/YYYY)",
                value=str(row_original.get('Fecha de oficio de cierre', '')),
                key=f"fecha_oficio_{indice_seleccionado}")
        
        with col3:
            estado_final = st.selectbox("Estado final",
                options=["", "Completo", "Incompleto", "Cancelado"],
                index=["", "Completo", "Incompleto", "Cancelado"].index(row_original.get('Estado', '')) if row_original.get('Estado', '') in ["", "Completo", "Incompleto", "Cancelado"] else 0,
                key=f"estado_{indice_seleccionado}")
        
        # PLAZOS CALCULADOS (solo lectura)
        st.markdown("**Plazos Calculados**")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.text_input("Plazo análisis", 
                value=str(row_original.get('Plazo de análisis', '')), 
                disabled=True,
                key=f"plazo_analisis_{indice_seleccionado}")
        
        with col2:
            st.text_input("Plazo cronograma", 
                value=str(row_original.get('Plazo de cronograma', '')), 
                disabled=True,
                key=f"plazo_cronograma_{indice_seleccionado}")
        
        with col3:
            st.text_input("Plazo oficio cierre", 
                value=str(row_original.get('Plazo de oficio de cierre', '')), 
                disabled=True,
                key=f"plazo_oficio_{indice_seleccionado}")
        
        # OBSERVACIONES
        st.markdown("**Observaciones**")
        observaciones = st.text_area("Observaciones",
            value=str(row_original.get('Observaciones', '')),
            height=100,
            key=f"observaciones_{indice_seleccionado}")
        
        # COMPLETITUD CALCULADA (solo lectura)
        porcentaje_actual = calcular_porcentaje_avance(row_original)
        st.text_input("Porcentaje de completitud (%)", 
            value=f"{porcentaje_actual}%", 
            disabled=True,
            key=f"completitud_{indice_seleccionado}")
        
        # BOTÓN DE GUARDAR
        submitted = st.form_submit_button("Guardar Cambios", type="primary", use_container_width=True)
        
        if submitted:
            try:
                # Crear registro actualizado
                registro_actualizado = row_original.copy()
                
                # Actualizar todos los campos
                registro_actualizado['Cod'] = codigo
                registro_actualizado['TipoDato'] = tipo_dato
                registro_actualizado['Mes Proyectado'] = mes_proyectado
                registro_actualizado['Funcionario de enlace'] = funcionario
                registro_actualizado['Frecuencia'] = frecuencia
                registro_actualizado['Actas de interés'] = actas_interes
                registro_actualizado['Suscripción'] = suscripcion
                registro_actualizado['Entrega'] = entrega
                registro_actualizado['Acuerdo de compromiso'] = acuerdo_compromiso
                registro_actualizado['Acceso a datos'] = acceso_datos
                registro_actualizado['Análisis de información'] = analisis_informacion
                registro_actualizado['Fecha de entrega de información'] = fecha_entrega
                registro_actualizado['Cronograma concertado'] = cronograma_concertado
                registro_actualizado['Análisis de información (fecha programada)'] = analisis_programada
                registro_actualizado['Análisis y cronograma'] = analisis_real
                registro_actualizado['Seguimiento de acuerdos'] = seguimiento_acuerdos
                registro_actualizado['Registro'] = registro
                registro_actualizado['ET'] = et
                registro_actualizado['CO'] = co
                registro_actualizado['DD'] = dd
                registro_actualizado['REC'] = rec
                registro_actualizado['SERVICIO'] = servicio
                registro_actualizado['Estándares (fecha programada)'] = estandares_programada
                registro_actualizado['Estándares'] = estandares_real
                registro_actualizado['Resultados de orientación técnica'] = resultados_orientacion
                registro_actualizado['Verificación del servicio web geográfico'] = verificacion_servicio
                registro_actualizado['Verificar Aprobar'] = verificar_aprobar
                registro_actualizado['Revisar validar'] = revisar_validar
                registro_actualizado['Aprobación de resultados'] = aprobacion_resultados
                registro_actualizado['Fecha de publicación programada'] = publicacion_programada
                registro_actualizado['Publicación'] = publicacion_real
                registro_actualizado['Disponer de los datos temáticos'] = disponer_datos
                registro_actualizado['Catálogo de recursos geográficos'] = catalogo_recursos
                registro_actualizado['Oficios de cierre'] = oficios_cierre
                registro_actualizado['Fecha de oficio de cierre'] = fecha_oficio_cierre
                registro_actualizado['Estado'] = estado_final
                registro_actualizado['Observaciones'] = observaciones
                
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
                
                # Guardar en Google Sheets
                exito, mensaje = guardar_datos_editados(registros_df, crear_backup=True)
                
                if exito:
                    st.success(f"Registro guardado exitosamente. Avance: {nuevo_porcentaje}%")
                else:
                    st.error(f"Error al guardar: {mensaje}")
                    
            except Exception as e:
                st.error(f"Error al procesar los cambios: {str(e)}")
    
    return registros_df


def mostrar_edicion_registros_con_autenticacion(registros_df):
    """Wrapper con autenticación para el editor limpio"""
    
    try:
        from auth_utils import verificar_autenticacion
        
        if verificar_autenticacion():
            return mostrar_edicion_registros(registros_df)
        else:
            st.subheader("Acceso Restringido")
            st.warning("Se requiere autenticación para editar registros")
            st.info("Use el panel 'Acceso Administrativo' en la barra lateral para autenticarse")
            return registros_df
            
    except ImportError:
        return mostrar_edicion_registros(registros_df)
