# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.figure_factory as ff
import plotly.graph_objects as go
from datetime import datetime, timedelta, date
from validaciones_utils import validar_reglas_negocio, mostrar_estado_validaciones, verificar_condiciones_estandares, verificar_condiciones_oficio_cierre
import io
import matplotlib
import base64
import os
import re
from fecha_utils import calcular_plazo_analisis, actualizar_plazo_analisis, calcular_plazo_cronograma, actualizar_plazo_cronograma, calcular_plazo_oficio_cierre, actualizar_plazo_oficio_cierre
from auth_utils import verificar_autenticacion, mostrar_login, mostrar_estado_autenticacion, requiere_autenticacion

# Importar las funciones corregidas
from config import setup_page, load_css
from data_utils import (
    cargar_datos, procesar_metas, calcular_porcentaje_avance,
    verificar_estado_fechas, formatear_fecha, es_fecha_valida,
    validar_campos_fecha, guardar_datos_editados, guardar_datos_editados_rapido, procesar_fecha,
    contar_registros_completados_por_fecha, cargar_datos_desde_excel
)
from visualization import crear_gantt, comparar_avance_metas
from constants import REGISTROS_DATA, META_DATA
from sheets_utils import test_connection, get_sheets_manager

# ========== FUNCIONES AUXILIARES RESTAURADAS ==========

def string_a_fecha(fecha_str):
    """Convierte un string de fecha a objeto datetime para mostrar en el selector de fecha."""
    if not fecha_str or fecha_str == "":
        return None
    fecha = procesar_fecha(fecha_str)
    return fecha

def highlight_estado_fechas(s):
    """Función para aplicar estilo según el valor de 'Estado Fechas'"""
    if 'Estado Fechas' in s and s['Estado Fechas'] == 'vencido':
        return ['background-color: #fee2e2'] * len(s)
    elif 'Estado Fechas' in s and s['Estado Fechas'] == 'proximo':
        return ['background-color: #fef3c7'] * len(s)
    else:
        return ['background-color: #ffffff'] * len(s)

def on_change_callback():
    """Callback para marcar que hay cambios pendientes."""
    st.session_state.cambios_pendientes = True

def fecha_para_selector(fecha_str):
    """Convierte una fecha en string a un objeto datetime para el selector."""
    if not fecha_str or pd.isna(fecha_str) or fecha_str == '':
        return None
    try:
        fecha = procesar_fecha(fecha_str)
        if fecha is not None:
            return fecha
    except:
        pass
    return None

def fecha_desde_selector_a_string(fecha):
    """Convierte un objeto datetime del selector a string con formato DD/MM/AAAA."""
    if fecha is None:
        return ""
    return fecha.strftime('%d/%m/%Y')

# ========== FUNCIONES DE CONFIGURACIÓN RESTAURADAS ==========

def mostrar_configuracion_sheets():
    """Muestra la configuración y estado de Google Sheets"""
    with st.sidebar.expander("Configuración Google Sheets"):
        st.markdown("### Estado de Conexión")
        
        if st.button("Probar Conexión", help="Verifica la conexión con Google Sheets"):
            with st.spinner("Probando conexión..."):
                test_connection()
        
        try:
            manager = get_sheets_manager()
            hojas = manager.listar_hojas()
            st.markdown("**Hojas disponibles:**")
            for hoja in hojas:
                st.markdown(f"- {hoja}")
        except:
            st.warning("No se pudo obtener la lista de hojas")
        
        st.markdown("---")
        st.markdown("**¿Necesitas configurar Google Sheets?**")
        st.markdown("[Ver instrucciones completas](https://github.com/tu-repo/INSTRUCCIONES_CONFIGURACION.md)")
        st.info("Los datos se guardan de forma segura en Google Sheets con autenticación OAuth2")

@requiere_autenticacion
def cargar_datos_desde_excel_autenticado(uploaded_file):
    """Función protegida para cargar datos desde Excel"""
    return cargar_datos_desde_excel(uploaded_file)

def mostrar_carga_archivos():
    """Muestra la sección de carga de archivos Excel/CSV con autenticación"""
    with st.sidebar.expander("🔒 Cargar Datos desde Excel (Admin)"):
        st.markdown("### Subir Archivo Excel")
        
        if not verificar_autenticacion():
            st.warning("🔒 Función disponible solo para administradores")
            st.info("Inicia sesión en 'Acceso Administrativo' para usar esta función")
            return
        
        uploaded_file = st.file_uploader(
            "Selecciona un archivo Excel",
            type=['xlsx', 'xls'],
            help="El archivo se sincronizará automáticamente con Google Sheets"
        )
        
        if uploaded_file is not None:
            if st.button("🔄 Sincronizar con Google Sheets"):
                with st.spinner("Procesando y sincronizando archivo..."):
                    nuevos_registros, nuevas_metas = cargar_datos_desde_excel_autenticado(uploaded_file)
                    
                    if nuevos_registros is not None:
                        st.success("✅ Archivo sincronizado exitosamente!")
                        st.info("🔄 Recargando la aplicación con los nuevos datos...")
                        st.rerun()
                    else:
                        st.error("❌ Error al procesar el archivo")
        
        st.markdown("---")
        st.markdown("**Formato esperado:**")
        st.markdown("- **Hoja 'Registros':** Datos principales")
        st.markdown("- **Hoja 'Metas':** Metas quincenales")
        st.warning("⚠️ La sincronización sobrescribirá los datos existentes en Google Sheets")

def mostrar_edicion_registros(registros_df):
    """Muestra la pestaña de edición de registros - VERSIÓN COMPLETA RESTAURADA CON TODAS LAS SECCIONES."""
    st.markdown('<div class="subtitle">Edición de Registros</div>', unsafe_allow_html=True)

    st.info(
        "Esta sección permite editar los datos usando selectores de fecha y opciones. Los cambios se guardan automáticamente en Google Sheets.")

    # Explicación adicional sobre las fechas y reglas de validación
    st.warning("""
    **Importante**: 
    - Para los campos de fecha, utilice el selector de calendario que aparece.
    - El campo "Plazo de análisis" se calcula automáticamente como 5 días hábiles después de la "Fecha de entrega de información", sin contar fines de semana ni festivos.
    - El campo "Plazo de cronograma" se calcula automáticamente como 3 días hábiles después del "Plazo de análisis", sin contar fines de semana ni festivos.
    - El campo "Plazo de oficio de cierre" se calcula automáticamente como 7 días hábiles después de la fecha real de "Publicación", sin contar fines de semana ni festivos.
    - Se aplicarán automáticamente las siguientes validaciones:
        1. Si 'Entrega acuerdo de compromiso' no está vacío, 'Acuerdo de compromiso' se actualizará a 'SI'
        2. Si 'Análisis y cronograma' tiene fecha, 'Análisis de información' se actualizará a 'SI'
        3. Al introducir fecha en 'Estándares', los campos que no estén 'Completo' se actualizarán automáticamente a 'No aplica'
        4. Si introduce fecha en 'Publicación', 'Disponer datos temáticos' se actualizará automáticamente a 'SI'
        5. Para introducir una fecha en 'Fecha de oficio de cierre', debe tener la etapa de Publicación completada (con fecha)
        6. Al introducir una fecha en 'Fecha de oficio de cierre', el campo 'Estado' se actualizará automáticamente a 'Completado'
        7. Si se elimina la fecha de oficio de cierre, el Estado se cambiará automáticamente a 'En proceso'
    """)
    
    # Mostrar mensaje de guardado si existe
    if 'mensaje_guardado' in st.session_state and st.session_state.mensaje_guardado:
        if st.session_state.mensaje_guardado[0] == "success":
            st.success(st.session_state.mensaje_guardado[1])
        else:
            st.error(st.session_state.mensaje_guardado[1])
        # Limpiar mensaje después de mostrarlo
        st.session_state.mensaje_guardado = None

    st.markdown("### Edición Individual de Registros")

    # Selector de registro - mostrar lista completa de registros para seleccionar
    codigos_registros = registros_df['Cod'].astype(str).tolist()
    entidades_registros = registros_df['Entidad'].tolist()
    niveles_registros = registros_df['Nivel Información '].tolist()

    # Crear opciones para el selector combinando información
    opciones_registros = [f"{codigos_registros[i]} - {entidades_registros[i]} - {niveles_registros[i]}"
                          for i in range(len(codigos_registros))]

    # Agregar el selector de registro
    seleccion_registro = st.selectbox(
        "Seleccione un registro para editar:",
        options=opciones_registros,
        key="selector_registro"
    )

    # Obtener el índice del registro seleccionado
    indice_seleccionado = opciones_registros.index(seleccion_registro)

    # Mostrar el registro seleccionado para edición
    try:
        # Obtener el registro seleccionado
        row = registros_df.iloc[indice_seleccionado].copy()

        # Flag para detectar cambios
        edited = False

        # Contenedor para los datos de edición
        with st.container():
            st.markdown("---")
            # Título del registro
            st.markdown(f"### Editando Registro #{row['Cod']} - {row['Entidad']}")
            st.markdown(f"**Nivel de Información:** {row['Nivel Información ']}")
            st.markdown("---")

            # ===== SECCIÓN 1: INFORMACIÓN BÁSICA =====
            st.markdown("### 1. Información Básica")
            col1, col2, col3 = st.columns(3)

            with col1:
                # Campos no editables
                st.text_input("Código", value=row['Cod'], disabled=True)

            with col2:
                # Tipo de Dato
                nuevo_tipo = st.selectbox(
                    "Tipo de Dato",
                    options=["Nuevo", "Actualizar"],
                    index=0 if row['TipoDato'].upper() == "NUEVO" else 1,
                    key=f"tipo_{indice_seleccionado}",
                    on_change=on_change_callback
                )
                if nuevo_tipo != row['TipoDato']:
                    registros_df.at[registros_df.index[indice_seleccionado], 'TipoDato'] = nuevo_tipo
                    edited = True

            with col3:
                # Mes Proyectado - NUEVA COLUMNA
                meses = ["", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", 
                        "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
                
                mes_actual = row.get('Mes Proyectado', '') if pd.notna(row.get('Mes Proyectado', '')) else ""
                mes_index = 0
                if mes_actual and mes_actual in meses:
                    mes_index = meses.index(mes_actual)
                
                nuevo_mes = st.selectbox(
                    "Mes Proyectado",
                    options=meses,
                    index=mes_index,
                    key=f"mes_proyectado_{indice_seleccionado}",
                    on_change=on_change_callback
                )
                if nuevo_mes != row.get('Mes Proyectado', ''):
                    registros_df.at[registros_df.index[indice_seleccionado], 'Mes Proyectado'] = nuevo_mes
                    edited = True

            # Información de avance al final
            st.markdown("---")
            st.markdown("### Información de Avance")
            
            # Calcular porcentaje de avance actual
            porcentaje_actual = calcular_porcentaje_avance(registros_df.iloc[indice_seleccionado])
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Porcentaje de Avance", f"{porcentaje_actual}%")
            
            with col2:
                # Estado basado en porcentaje
                if porcentaje_actual == 100:
                    estado_avance = "Completado"
                    color_avance = "green"
                elif porcentaje_actual >= 75:
                    estado_avance = "Avanzado"
                    color_avance = "blue"
                elif porcentaje_actual >= 50:
                    estado_avance = "En progreso"
                    color_avance = "orange"
                elif porcentaje_actual >= 25:
                    estado_avance = "Inicial"
                    color_avance = "yellow"
                else:
                    estado_avance = "Sin iniciar"
                    color_avance = "red"
                
                st.markdown(f"""
                <div style="padding: 10px; border-radius: 5px; background-color: {color_avance}; color: white; text-align: center;">
                    <strong>{estado_avance}</strong>
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                # Próxima acción sugerida
                if porcentaje_actual == 0:
                    proxima_accion = "Iniciar acuerdo de compromiso"
                elif porcentaje_actual == 20:
                    proxima_accion = "Completar análisis y cronograma"
                elif porcentaje_actual == 40:
                    proxima_accion = "Completar estándares"
                elif porcentaje_actual == 70:
                    proxima_accion = "Realizar publicación"
                elif porcentaje_actual == 95:
                    proxima_accion = "Emitir oficio de cierre"
                else:
                    proxima_accion = "Continuar con el proceso"
                
                st.info(f"**Próxima acción:** {proxima_accion}")

            # ===== BOTONES DE ACCIÓN =====
            st.markdown("---")
            st.markdown("### Acciones")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                # Botón para guardar cambios individuales
                if edited or st.session_state.get('cambios_pendientes', False):
                    if st.button("💾 Guardar Cambios", key=f"guardar_individual_{indice_seleccionado}", type="primary"):
                        # Aplicar validaciones de reglas de negocio antes de guardar
                        registros_df = validar_reglas_negocio(registros_df)

                        # Actualizar los plazos automáticamente
                        registros_df = actualizar_plazo_analisis(registros_df)
                        registros_df = actualizar_plazo_cronograma(registros_df)
                        registros_df = actualizar_plazo_oficio_cierre(registros_df)

                        # Guardar los datos en Google Sheets
                        with st.spinner("Guardando cambios en Google Sheets..."):
                            exito, mensaje = guardar_datos_editados(registros_df, crear_backup=True)

                        if exito:
                            st.session_state.mensaje_guardado = ("success", mensaje)
                            st.session_state.cambios_pendientes = False
                            st.rerun()
                        else:
                            st.session_state.mensaje_guardado = ("error", mensaje)

            with col2:
                # Botón para recalcular plazos
                if st.button("🔄 Recalcular Plazos", key=f"recalcular_{indice_seleccionado}"):
                    with st.spinner("Recalculando plazos automáticamente..."):
                        # Actualizar los plazos automáticamente
                        registros_df = actualizar_plazo_analisis(registros_df)
                        registros_df = actualizar_plazo_cronograma(registros_df)
                        registros_df = actualizar_plazo_oficio_cierre(registros_df)
                        
                        # Guardar cambios
                        exito, mensaje = guardar_datos_editados_rapido(registros_df)
                        if exito:
                            st.success("Plazos recalculados y guardados")
                            st.rerun()
                        else:
                            st.error("Error al guardar plazos recalculados")

            with col3:
                # Botón para aplicar validaciones
                if st.button("✅ Aplicar Validaciones", key=f"validar_{indice_seleccionado}"):
                    with st.spinner("Aplicando reglas de validación..."):
                        # Aplicar reglas de negocio
                        registros_df = validar_reglas_negocio(registros_df)
                        
                        # Guardar cambios
                        exito, mensaje = guardar_datos_editados_rapido(registros_df)
                        if exito:
                            st.success("Validaciones aplicadas y guardadas")
                            st.rerun()
                        else:
                            st.error("Error al guardar validaciones")

            with col4:
                # Botón para actualizar vista
                if st.button("🔄 Actualizar Vista", key=f"actualizar_{indice_seleccionado}"):
                    st.rerun()

    except Exception as e:
        st.error(f"Error al editar el registro: {e}")
        
        # Mostrar información de debug
        with st.expander("Información de Debug"):
            st.write(f"Índice seleccionado: {indice_seleccionado}")
            st.write(f"Registro seleccionado: {seleccion_registro}")
            st.write(f"Columnas disponibles: {list(registros_df.columns)}")
            
            # Mostrar traceback completo
            import traceback
            st.code(traceback.format_exc())

    return registros_df

# ========== FUNCIÓN DASHBOARD MODIFICADA ==========

def mostrar_dashboard(df_filtrado, metas_nuevas_df, metas_actualizar_df, registros_df, 
                     entidad_seleccionada, funcionario_seleccionado, nivel_seleccionado):
    """Muestra el dashboard principal con métricas y gráficos - VERSIÓN COMPLETA RESTAURADA CON MODIFICACIONES."""
    # Mostrar métricas generales
    st.markdown('<div class="subtitle">Métricas Generales</div>', unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        total_registros = len(df_filtrado)
        st.markdown(f"""
        <div class="metric-card">
            <p style="font-size: 1rem; color: #64748b;">Total Registros</p>
            <p style="font-size: 2.5rem; font-weight: bold; color: #1E40AF;">{total_registros}</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        avance_promedio = df_filtrado['Porcentaje Avance'].mean() if not df_filtrado.empty else 0
        st.markdown(f"""
        <div class="metric-card">
            <p style="font-size: 1rem; color: #64748b;">Avance Promedio</p>
            <p style="font-size: 2.5rem; font-weight: bold; color: #047857;">{avance_promedio:.2f}%</p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        registros_completados = len(df_filtrado[df_filtrado['Porcentaje Avance'] == 100])
        st.markdown(f"""
        <div class="metric-card">
            <p style="font-size: 1rem; color: #64748b;">Registros Completados</p>
            <p style="font-size: 2.5rem; font-weight: bold; color: #B45309;">{registros_completados}</p>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        porcentaje_completados = (registros_completados / total_registros * 100) if total_registros > 0 else 0
        st.markdown(f"""
        <div class="metric-card">
            <p style="font-size: 1rem; color: #64748b;">% Completados</p>
            <p style="font-size: 2.5rem; font-weight: bold; color: #BE185D;">{porcentaje_completados:.2f}%</p>
        </div>
        """, unsafe_allow_html=True)

    # Comparación con metas
    st.markdown('<div class="subtitle">Comparación con Metas Quincenales</div>', unsafe_allow_html=True)

    # Calcular comparación con metas
    comparacion_nuevos, comparacion_actualizar, fecha_meta = comparar_avance_metas(df_filtrado, metas_nuevas_df,
                                                                                   metas_actualizar_df)

    # Mostrar fecha de la meta
    st.markdown(f"**Meta más cercana a la fecha actual: {fecha_meta.strftime('%d/%m/%Y')}**")

    # MODIFICACIÓN 1: Crear función para gradiente personalizado
    def crear_gradiente_personalizado(df_comparacion):
        """Crea un gradiente personalizado de rojo a verde oscuro para porcentajes 0-100, verde oscuro para >100"""
        def aplicar_color(val):
            if pd.isna(val):
                return ''
            if val <= 0:
                return 'background-color: #dc2626; color: white'  # Rojo intenso
            elif val <= 25:
                return 'background-color: #ef4444; color: white'  # Rojo
            elif val <= 50:
                return 'background-color: #f97316; color: white'  # Naranja
            elif val <= 75:
                return 'background-color: #eab308; color: black'  # Amarillo
            elif val < 100:
                return 'background-color: #84cc16; color: black'  # Verde claro
            else:  # val >= 100
                return 'background-color: #166534; color: white'  # Verde oscuro
        
        return df_comparacion.style.format({
            'Porcentaje': '{:.2f}%'
        }).applymap(aplicar_color, subset=['Porcentaje'])

    # Mostrar comparación en dos columnas
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Registros Nuevos")
        # APLICAR GRADIENTE PERSONALIZADO
        st.dataframe(crear_gradiente_personalizado(comparacion_nuevos))

        # Gráfico de barras para registros nuevos
        fig_nuevos = px.bar(
            comparacion_nuevos.reset_index(),
            x='index',
            y=['Completados', 'Meta'],
            barmode='group',
            labels={'index': 'Hito', 'value': 'Cantidad', 'variable': 'Tipo'},
            title='Comparación de Avance vs. Meta - Registros Nuevos',
            color_discrete_map={'Completados': '#4B5563', 'Meta': '#1E40AF'}
        )
        st.plotly_chart(fig_nuevos, use_container_width=True)

    with col2:
        st.markdown("### Registros a Actualizar")
        # APLICAR GRADIENTE PERSONALIZADO
        st.dataframe(crear_gradiente_personalizado(comparacion_actualizar))

        # Gráfico de barras para registros a actualizar
        fig_actualizar = px.bar(
            comparacion_actualizar.reset_index(),
            x='index',
            y=['Completados', 'Meta'],
            barmode='group',
            labels={'index': 'Hito', 'value': 'Cantidad', 'variable': 'Tipo'},
            title='Comparación de Avance vs. Meta - Registros a Actualizar',
            color_discrete_map={'Completados': '#4B5563', 'Meta': '#047857'}
        )
        st.plotly_chart(fig_actualizar, use_container_width=True)

    # MODIFICACIÓN 2: Diagrama de Gantt condicionado
    st.markdown('<div class="subtitle">Diagrama de Gantt - Cronograma de Hitos por Nivel de Información</div>',
                unsafe_allow_html=True)

    # Verificar si hay filtros específicos aplicados
    filtros_aplicados = (
        entidad_seleccionada != 'Todas' or 
        funcionario_seleccionado != 'Todos' or 
        nivel_seleccionado != 'Todos'
    )

    if filtros_aplicados:
        # Crear el diagrama de Gantt solo si hay filtros
        fig_gantt = crear_gantt(df_filtrado)
        if fig_gantt is not None:
            st.plotly_chart(fig_gantt, use_container_width=True)
        else:
            st.warning("No hay datos suficientes para crear el diagrama de Gantt con los filtros aplicados.")
    else:
        # Mostrar mensaje cuando no hay filtros aplicados
        st.info("Para visualizar el diagrama de Gantt seleccione la entidad o funcionario de su interés.")

    # Tabla de registros con porcentaje de avance
    st.markdown('<div class="subtitle">Detalle de Registros</div>', unsafe_allow_html=True)

    # Definir el orden de las columnas
    columnas_mostrar = [
        'Cod', 'Entidad', 'Nivel Información ', 'Funcionario', 'Mes Proyectado',
        'Frecuencia actualizacion ', 'TipoDato',
        'Fecha de entrega de información', 'Plazo de análisis', 'Plazo de cronograma',
        'Análisis y cronograma',
        'Estándares', 'Publicación',
        'Plazo de oficio de cierre', 'Fecha de oficio de cierre',
        'Estado', 'Observación', 'Porcentaje Avance'
    ]

    # Mostrar tabla con colores por estado de fechas
    try:
        # Verificar que todas las columnas existan
        columnas_mostrar_existentes = [col for col in columnas_mostrar if col in df_filtrado.columns]
        df_mostrar = df_filtrado[columnas_mostrar_existentes].copy()

        # Aplicar formato a las fechas
        columnas_fecha = [
            'Fecha de entrega de información', 'Plazo de análisis', 'Plazo de cronograma',
            'Análisis y cronograma', 'Estándares',
            'Publicación', 'Plazo de oficio de cierre', 'Fecha de oficio de cierre'
        ]

        for col in columnas_fecha:
            if col in df_mostrar.columns:
                df_mostrar[col] = df_mostrar[col].apply(lambda x: formatear_fecha(x) if es_fecha_valida(x) else "")

        # Mostrar el dataframe con formato
        st.dataframe(
            df_mostrar
            .style.format({'Porcentaje Avance': '{:.2f}%'})
            .apply(highlight_estado_fechas, axis=1)
            .background_gradient(cmap='RdYlGn', subset=['Porcentaje Avance']),
            use_container_width=True
        )

        # SECCIÓN DE DESCARGA
        st.markdown("### Descargar Datos")

        col1, col2 = st.columns(2)

        with col1:
            # Botón para descargar los datos filtrados
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df_mostrar.to_excel(writer, sheet_name='Registros Filtrados', index=False)

            excel_data = output.getvalue()
            st.download_button(
                label="Descargar datos filtrados (Excel)",
                data=excel_data,
                file_name="registros_filtrados.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                help="Descarga los datos filtrados en formato Excel"
            )

        with col2:
            # BOTÓN PARA DESCARGAR TODOS LOS REGISTROS
            output_completo = io.BytesIO()
            with pd.ExcelWriter(output_completo, engine='openpyxl') as writer:
                registros_df.to_excel(writer, sheet_name='Registros Completos', index=False)

                # Añadir hojas adicionales con categorías
                if 'TipoDato' in registros_df.columns:
                    # Hoja para registros nuevos
                    registros_nuevos = registros_df[registros_df['TipoDato'].str.upper() == 'NUEVO']
                    if not registros_nuevos.empty:
                        registros_nuevos.to_excel(writer, sheet_name='Registros Nuevos', index=False)

                    # Hoja para registros a actualizar
                    registros_actualizar = registros_df[registros_df['TipoDato'].str.upper() == 'ACTUALIZAR']
                    if not registros_actualizar.empty:
                        registros_actualizar.to_excel(writer, sheet_name='Registros a Actualizar', index=False)

            excel_data_completo = output_completo.getvalue()

            # Botón para descargar todos los registros
            st.download_button(
                label="Descargar TODOS los registros (Excel)",
                data=excel_data_completo,
                file_name="todos_los_registros.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                help="Descarga todos los registros en formato Excel, sin filtros aplicados",
                use_container_width=True
            )

        # Información sobre el contenido
        num_registros = len(registros_df)
        num_campos = len(registros_df.columns)
        st.info(
            f"El archivo de TODOS los registros incluirá {num_registros} registros con {num_campos} campos originales.")

    except Exception as e:
        st.error(f"Error al mostrar la tabla de registros: {e}")
        if 'columnas_mostrar_existentes' in locals():
            st.dataframe(df_filtrado[columnas_mostrar_existentes])

# ========== FUNCIÓN ALERTAS COMPLETA ==========

def mostrar_alertas_vencimientos(registros_df):
    """Muestra alertas de vencimientos de fechas en los registros - VERSIÓN COMPLETA RESTAURADA."""
    st.markdown('<div class="subtitle">Alertas de Vencimientos</div>', unsafe_allow_html=True)

    # Fecha actual para comparaciones
    fecha_actual = datetime.now().date()

    # Función para calcular días hábiles entre fechas
    def calcular_dias_habiles(fecha_inicio, fecha_fin):
        if not fecha_inicio or not fecha_fin:
            return None

        # Convertir a objetos date si son datetime
        if isinstance(fecha_inicio, datetime):
            fecha_inicio = fecha_inicio.date()
        if isinstance(fecha_fin, datetime):
            fecha_fin = fecha_fin.date()

        # Si la fecha de inicio es posterior a la fecha fin, devolver días negativos
        if fecha_inicio > fecha_fin:
            return -calcular_dias_habiles(fecha_fin, fecha_inicio)

        # Calcular días hábiles
        dias = 0
        fecha_actual_calc = fecha_inicio
        while fecha_actual_calc <= fecha_fin:
            # Si no es fin de semana (0=lunes, 6=domingo)
            if fecha_actual_calc.weekday() < 5:
                dias += 1
            fecha_actual_calc += timedelta(days=1)

        return dias

    # Función para determinar si una fecha está próxima a vencer
    def es_proximo_vencimiento(fecha_limite):
        if not fecha_limite:
            return False

        # Convertir a objeto date si es datetime
        if isinstance(fecha_limite, datetime):
            fecha_limite = fecha_limite.date()

        # Si ya está vencido, no es "próximo a vencer"
        if fecha_limite < fecha_actual:
            return False

        # Calcular días hábiles hasta la fecha límite
        dias_habiles = calcular_dias_habiles(fecha_actual, fecha_limite)

        # Si está dentro de los próximos 5 días hábiles
        return dias_habiles is not None and 0 <= dias_habiles <= 5

    # Función para determinar si una fecha está vencida
    def es_vencido(fecha_limite):
        if not fecha_limite:
            return False

        # Convertir a objeto date si es datetime
        if isinstance(fecha_limite, datetime):
            fecha_limite = fecha_limite.date()

        return fecha_limite < fecha_actual

    # Función para calcular días de rezago
    def calcular_dias_rezago(fecha_limite):
        if not fecha_limite or not es_vencido(fecha_limite):
            return None

        # Convertir a objeto date si es datetime
        if isinstance(fecha_limite, datetime):
            fecha_limite = fecha_limite.date()

        return (fecha_actual - fecha_limite).days

    # Función para formatear fechas de manera segura
    def formatear_fecha_segura(fecha):
        if fecha is None or pd.isna(fecha):
            return ""
        try:
            return fecha.strftime('%d/%m/%Y')
        except:
            return ""

    # Preprocesar registros para el análisis
    registros_alertas = []

    for idx, row in registros_df.iterrows():
        try:
            # Procesar fechas de manera segura
            fecha_plazo_analisis = procesar_fecha(row.get('Plazo de análisis', ''))
            fecha_plazo_cronograma = procesar_fecha(row.get('Plazo de cronograma', ''))
            fecha_plazo_oficio_cierre = procesar_fecha(row.get('Plazo de oficio de cierre', ''))

            # Análisis de cada tipo de alerta
            alertas = []

            # Verificar plazo de análisis
            if fecha_plazo_analisis:
                if es_vencido(fecha_plazo_analisis):
                    dias_rezago = calcular_dias_rezago(fecha_plazo_analisis)
                    alertas.append({
                        'tipo': 'Plazo de Análisis Vencido',
                        'fecha': formatear_fecha_segura(fecha_plazo_analisis),
                        'dias_rezago': dias_rezago,
                        'prioridad': 'Alta'
                    })
                elif es_proximo_vencimiento(fecha_plazo_analisis):
                    alertas.append({
                        'tipo': 'Plazo de Análisis Próximo',
                        'fecha': formatear_fecha_segura(fecha_plazo_analisis),
                        'dias_rezago': 0,
                        'prioridad': 'Media'
                    })

            # Verificar plazo de cronograma
            if fecha_plazo_cronograma:
                if es_vencido(fecha_plazo_cronograma):
                    dias_rezago = calcular_dias_rezago(fecha_plazo_cronograma)
                    alertas.append({
                        'tipo': 'Plazo de Cronograma Vencido',
                        'fecha': formatear_fecha_segura(fecha_plazo_cronograma),
                        'dias_rezago': dias_rezago,
                        'prioridad': 'Alta'
                    })
                elif es_proximo_vencimiento(fecha_plazo_cronograma):
                    alertas.append({
                        'tipo': 'Plazo de Cronograma Próximo',
                        'fecha': formatear_fecha_segura(fecha_plazo_cronograma),
                        'dias_rezago': 0,
                        'prioridad': 'Media'
                    })

            # Verificar plazo de oficio de cierre
            if fecha_plazo_oficio_cierre:
                if es_vencido(fecha_plazo_oficio_cierre):
                    dias_rezago = calcular_dias_rezago(fecha_plazo_oficio_cierre)
                    alertas.append({
                        'tipo': 'Plazo de Oficio de Cierre Vencido',
                        'fecha': formatear_fecha_segura(fecha_plazo_oficio_cierre),
                        'dias_rezago': dias_rezago,
                        'prioridad': 'Crítica'
                    })
                elif es_proximo_vencimiento(fecha_plazo_oficio_cierre):
                    alertas.append({
                        'tipo': 'Plazo de Oficio de Cierre Próximo',
                        'fecha': formatear_fecha_segura(fecha_plazo_oficio_cierre),
                        'dias_rezago': 0,
                        'prioridad': 'Alta'
                    })

            # Si hay alertas para este registro, agregarlas
            for alerta in alertas:
                registros_alertas.append({
                    'Código': row['Cod'],
                    'Entidad': row['Entidad'],
                    'Nivel Información': row['Nivel Información '],
                    'Tipo de Alerta': alerta['tipo'],
                    'Fecha Límite': alerta['fecha'],
                    'Días de Rezago': alerta['dias_rezago'],
                    'Prioridad': alerta['prioridad']
                })

        except Exception as e:
            st.warning(f"Error procesando registro {row['Cod']}: {e}")
            continue

    # Mostrar alertas
    if registros_alertas:
        df_alertas = pd.DataFrame(registros_alertas)
        
        # Separar por tipo de prioridad
        alertas_criticas = df_alertas[df_alertas['Prioridad'] == 'Crítica']
        alertas_altas = df_alertas[df_alertas['Prioridad'] == 'Alta']
        alertas_medias = df_alertas[df_alertas['Prioridad'] == 'Media']

        if not alertas_criticas.empty:
            st.error(f"🚨 {len(alertas_criticas)} alertas críticas encontradas")
            st.dataframe(alertas_criticas, use_container_width=True)

        if not alertas_altas.empty:
            st.warning(f"⚠️ {len(alertas_altas)} alertas de alta prioridad encontradas")
            st.dataframe(alertas_altas, use_container_width=True)

        if not alertas_medias.empty:
            st.info(f"ℹ️ {len(alertas_medias)} alertas de prioridad media encontradas")
            st.dataframe(alertas_medias, use_container_width=True)

        # Gráfico de distribución de alertas
        st.markdown("### Distribución de Alertas por Prioridad")
        conteo_prioridades = df_alertas['Prioridad'].value_counts()
        fig_alertas = px.pie(
            values=conteo_prioridades.values,
            names=conteo_prioridades.index,
            title="Distribución de Alertas por Prioridad"
        )
        st.plotly_chart(fig_alertas, use_container_width=True)

    else:
        st.success("¡No hay alertas de vencimientos pendientes!")

# ========== FUNCIÓN REPORTES CON MES PROYECTADO ==========

def mostrar_reportes(registros_df, tipo_dato_filtro, acuerdo_filtro, analisis_filtro, 
                    estandares_filtro, publicacion_filtro, finalizado_filtro, mes_filtro):
    """Muestra la pestaña de reportes con tabla completa y filtros específicos - VERSIÓN COMPLETA CON MES."""
    st.markdown('<div class="subtitle">Reportes de Registros</div>', unsafe_allow_html=True)
    
    # Aplicar filtros
    df_filtrado = registros_df.copy()
    
    # Filtro por tipo de dato
    if tipo_dato_filtro != 'Todos':
        df_filtrado = df_filtrado[df_filtrado['TipoDato'].str.upper() == tipo_dato_filtro.upper()]
    
    # Filtro por acuerdo de compromiso suscrito
    if acuerdo_filtro != 'Todos':
        if acuerdo_filtro == 'Suscrito':
            df_filtrado = df_filtrado[
                (df_filtrado['Acuerdo de compromiso'].str.upper().isin(['SI', 'SÍ', 'S', 'YES', 'Y', 'COMPLETO']))
            ]
        else:  # No Suscrito
            df_filtrado = df_filtrado[
                ~(df_filtrado['Acuerdo de compromiso'].str.upper().isin(['SI', 'SÍ', 'S', 'YES', 'Y', 'COMPLETO']))
            ]
    
    # Filtro por análisis y cronograma
    if analisis_filtro != 'Todos':
        if analisis_filtro == 'Completado':
            df_filtrado = df_filtrado[
                (df_filtrado['Análisis y cronograma'].notna()) & 
                (df_filtrado['Análisis y cronograma'] != '')
            ]
        else:  # No Completado
            df_filtrado = df_filtrado[
                (df_filtrado['Análisis y cronograma'].isna()) | 
                (df_filtrado['Análisis y cronograma'] == '')
            ]
    
    # Filtro por estándares completado
    if estandares_filtro != 'Todos':
        if estandares_filtro == 'Completado':
            df_filtrado = df_filtrado[
                (df_filtrado['Estándares'].notna()) & 
                (df_filtrado['Estándares'] != '')
            ]
        else:  # No Completado
            df_filtrado = df_filtrado[
                (df_filtrado['Estándares'].isna()) | 
                (df_filtrado['Estándares'] == '')
            ]
    
    # Filtro por publicación
    if publicacion_filtro != 'Todos':
        if publicacion_filtro == 'Completado':
            df_filtrado = df_filtrado[
                (df_filtrado['Publicación'].notna()) & 
                (df_filtrado['Publicación'] != '')
            ]
        else:  # No Completado
            df_filtrado = df_filtrado[
                (df_filtrado['Publicación'].isna()) | 
                (df_filtrado['Publicación'] == '')
            ]
    
    # Filtro por finalizado
    if finalizado_filtro != 'Todos':
        if finalizado_filtro == 'Finalizado':
            df_filtrado = df_filtrado[
                (df_filtrado['Fecha de oficio de cierre'].notna()) & 
                (df_filtrado['Fecha de oficio de cierre'] != '')
            ]
        else:  # No Finalizado
            df_filtrado = df_filtrado[
                (df_filtrado['Fecha de oficio de cierre'].isna()) | 
                (df_filtrado['Fecha de oficio de cierre'] == '')
            ]
    
    # NUEVO FILTRO: Mes Proyectado
    if mes_filtro != 'Todos':
        df_filtrado = df_filtrado[df_filtrado['Mes Proyectado'] == mes_filtro]
    
    # Mostrar estadísticas del filtrado
    st.markdown("### Resumen de Registros Filtrados")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_filtrados = len(df_filtrado)
        st.markdown(f"""
        <div class="metric-card">
            <p style="font-size: 1rem; color: #64748b;">Total Filtrados</p>
            <p style="font-size: 2.5rem; font-weight: bold; color: #1E40AF;">{total_filtrados}</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        if total_filtrados > 0:
            avance_promedio = df_filtrado['Porcentaje Avance'].mean()
            st.markdown(f"""
            <div class="metric-card">
                <p style="font-size: 1rem; color: #64748b;">Avance Promedio</p>
                <p style="font-size: 2.5rem; font-weight: bold; color: #047857;">{avance_promedio:.1f}%</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="metric-card">
                <p style="font-size: 1rem; color: #64748b;">Avance Promedio</p>
                <p style="font-size: 2.5rem; font-weight: bold; color: #047857;">0%</p>
            </div>
            """, unsafe_allow_html=True)

    with col3:
        if total_filtrados > 0:
            completados = len(df_filtrado[df_filtrado['Porcentaje Avance'] == 100])
            st.markdown(f"""
            <div class="metric-card">
                <p style="font-size: 1rem; color: #64748b;">Completados</p>
                <p style="font-size: 2.5rem; font-weight: bold; color: #B45309;">{completados}</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="metric-card">
                <p style="font-size: 1rem; color: #64748b;">Completados</p>
                <p style="font-size: 2.5rem; font-weight: bold; color: #B45309;">0</p>
            </div>
            """, unsafe_allow_html=True)

    with col4:
        if total_filtrados > 0:
            porcentaje_completados = (len(df_filtrado[df_filtrado['Porcentaje Avance'] == 100]) / total_filtrados * 100)
            st.markdown(f"""
            <div class="metric-card">
                <p style="font-size: 1rem; color: #64748b;">% Completados</p>
                <p style="font-size: 2.5rem; font-weight: bold; color: #BE185D;">{porcentaje_completados:.1f}%</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="metric-card">
                <p style="font-size: 1rem; color: #64748b;">% Completados</p>
                <p style="font-size: 2.5rem; font-weight: bold; color: #BE185D;">0%</p>
            </div>
            """, unsafe_allow_html=True)

    # Mostrar tabla de registros filtrados
    st.markdown("### Tabla de Registros")
    
    if df_filtrado.empty:
        st.warning("No se encontraron registros que coincidan con los filtros seleccionados.")
        return
    
    # Definir columnas a mostrar
    columnas_mostrar = [
        'Cod', 'Entidad', 'Nivel Información ', 'Funcionario', 'Mes Proyectado',
        'Frecuencia actualizacion ', 'TipoDato',
        'Fecha de entrega de información', 'Plazo de análisis', 'Plazo de cronograma',
        'Análisis y cronograma', 'Estándares', 'Publicación',
        'Plazo de oficio de cierre', 'Fecha de oficio de cierre',
        'Estado', 'Observación', 'Porcentaje Avance'
    ]
    
    # Verificar que todas las columnas existan
    columnas_mostrar_existentes = [col for col in columnas_mostrar if col in df_filtrado.columns]
    df_mostrar = df_filtrado[columnas_mostrar_existentes].copy()
    
    # Aplicar formato a las fechas
    columnas_fecha = [
        'Fecha de entrega de información', 'Plazo de análisis', 'Plazo de cronograma',
        'Análisis y cronograma', 'Estándares', 'Publicación',
        'Plazo de oficio de cierre', 'Fecha de oficio de cierre'
    ]
    
    for col in columnas_fecha:
        if col in df_mostrar.columns:
            df_mostrar[col] = df_mostrar[col].apply(lambda x: formatear_fecha(x) if es_fecha_valida(x) else "")
    
    # Mostrar dataframe con formato
    st.dataframe(
        df_mostrar
        .style.format({'Porcentaje Avance': '{:.2f}%'})
        .apply(highlight_estado_fechas, axis=1)
        .background_gradient(cmap='RdYlGn', subset=['Porcentaje Avance']),
        use_container_width=True
    )
    
    # Botón para descargar reporte
    st.markdown("### Descargar Reporte")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Descargar como Excel
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_mostrar.to_excel(writer, sheet_name='Reporte Filtrado', index=False)

        excel_data = output.getvalue()
        st.download_button(
            label="Descargar reporte como Excel",
            data=excel_data,
            file_name=f"reporte_registros_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            help="Descarga el reporte filtrado en formato Excel"
        )
    
    with col2:
        # Descargar como CSV
        csv = df_mostrar.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Descargar reporte como CSV",
            data=csv,
            file_name=f"reporte_registros_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            help="Descarga el reporte filtrado en formato CSV"
        )
    
    # Información adicional sobre los filtros aplicados
    filtros_aplicados = []
    if tipo_dato_filtro != 'Todos':
        filtros_aplicados.append(f"Tipo de Dato: {tipo_dato_filtro}")
    if acuerdo_filtro != 'Todos':
        filtros_aplicados.append(f"Acuerdo de Compromiso: {acuerdo_filtro}")
    if analisis_filtro != 'Todos':
        filtros_aplicados.append(f"Análisis y Cronograma: {analisis_filtro}")
    if estandares_filtro != 'Todos':
        filtros_aplicados.append(f"Estándares: {estandares_filtro}")
    if publicacion_filtro != 'Todos':
        filtros_aplicados.append(f"Publicación: {publicacion_filtro}")
    if finalizado_filtro != 'Todos':
        filtros_aplicados.append(f"Finalizado: {finalizado_filtro}")
    if mes_filtro != 'Todos':
        filtros_aplicados.append(f"Mes Proyectado: {mes_filtro}")
    
    if filtros_aplicados:
        st.info(f"**Filtros aplicados:** {', '.join(filtros_aplicados)}")
    else:
        st.info("**Mostrando todos los registros** (sin filtros aplicados)")

# ========== FUNCIÓN PRINCIPAL ==========

def main():
    """Función principal de la aplicación"""
    try:
        # Configurar página
        setup_page()
        load_css()

        # Inicializar session state
        if 'cambios_pendientes' not in st.session_state:
            st.session_state.cambios_pendientes = False
        if 'funcionarios' not in st.session_state:
            st.session_state.funcionarios = []
        if 'mensaje_guardado' not in st.session_state:
            st.session_state.mensaje_guardado = None

        # ===== TÍTULO Y ESTADO =====
        st.markdown('<div class="title">🔐 Tablero de Control de Seguimiento de Datos Temáticos - Ideca</div>',
                    unsafe_allow_html=True)
        
        # Mostrar estado de Google Sheets y autenticación
        st.markdown("### Estado del Sistema")
        col1, col2, col3 = st.columns([2, 2, 1])
        
        with col1:
            st.info("📊 Datos sincronizados con Google Sheets en tiempo real")
        
        with col2:
            if verificar_autenticacion():
                st.success("🔐 Sesión administrativa activa")
            else:
                st.warning("⚠️ Sesión no administrativa")
        
        with col3:
            if st.button("🔄 Reconectar"):
                # Limpiar cache y reconectar
                if 'sheets_manager' in st.session_state:
                    del st.session_state.sheets_manager
                st.rerun()

        # ===== SIDEBAR CON AUTENTICACIÓN =====
        # Sistema de autenticación
        mostrar_login()
        mostrar_estado_autenticacion()
        
        # Configuración de Google Sheets
        mostrar_configuracion_sheets()
        
        # Carga de archivos Excel (PROTEGIDA)
        mostrar_carga_archivos()

        # Información sobre el tablero
        st.sidebar.markdown('<div class="subtitle">Información</div>', unsafe_allow_html=True)
        st.sidebar.markdown("""
        <div class="info-box">
        <p><strong>Tablero de Control de Cronogramas</strong></p>
        <p><strong>VERSIÓN COMPLETA CON MEJORAS Y AUTENTICACIÓN</strong></p>
        <p>• 🔐 Sistema de autenticación para admin</p>
        <p>• 📅 Campo "Mes Proyectado" agregado</p>
        <p>• 🔍 Filtro por mes en reportes</p>
        <p>• 🌈 Gradiente de metas mejorado</p>
        <p>• 📊 Diagrama de Gantt condicional</p>
        <p>• ✏️ Edición detallada de todos los campos</p>
        <p>• ✅ Validaciones automáticas completas</p>
        <p>• ⏰ Cálculo de plazos automático</p>
        <p>• 💾 Guardado inteligente en Google Sheets</p>
        <p>• 👥 Sistema de funcionarios dinámico</p>
        <p>• ⚠️ Alertas de vencimiento detalladas</p>
        </div>
        """, unsafe_allow_html=True)

        # ===== CARGA DE DATOS =====
        with st.spinner("Cargando datos desde Google Sheets..."):
            registros_df, meta_df = cargar_datos()

        # Verificar si los DataFrames están vacíos
        if registros_df.empty:
            st.warning("No hay datos de registros en Google Sheets.")
            
            # Crear estructura mínima para que la app funcione
            registros_df = pd.DataFrame(columns=[
                'Cod', 'Entidad', 'TipoDato', 'Nivel Información ', 'Mes Proyectado',
                'Acuerdo de compromiso', 'Análisis y cronograma',
                'Estándares', 'Publicación', 'Fecha de entrega de información',
                'Plazo de análisis', 'Plazo de cronograma', 'Plazo de oficio de cierre',
                'Funcionario', 'Frecuencia actualizacion ', 'Estado', 'Observación'
            ])
        else:
            st.success(f"✅ {len(registros_df)} registros cargados exitosamente desde Google Sheets")

        # ===== ASEGURAR COLUMNAS REQUERIDAS =====
        columnas_requeridas = [
            'Cod', 'Entidad', 'TipoDato', 'Acuerdo de compromiso',
            'Análisis y cronograma', 'Estándares', 'Publicación',
            'Nivel Información ', 'Mes Proyectado', 'Fecha de entrega de información',
            'Plazo de análisis', 'Plazo de cronograma', 'Plazo de oficio de cierre',
            'Funcionario', 'Frecuencia actualizacion ', 'Estado', 'Observación',
            'Fecha de oficio de cierre'
        ]

        for columna in columnas_requeridas:
            if columna not in registros_df.columns:
                registros_df[columna] = ''

        # ===== APLICAR VALIDACIONES Y CÁLCULOS =====
        with st.spinner("Aplicando validaciones y calculando plazos..."):
            # Aplicar reglas de negocio
            registros_df = validar_reglas_negocio(registros_df)

            # Actualizar plazos automáticamente
            registros_df = actualizar_plazo_analisis(registros_df)
            registros_df = actualizar_plazo_cronograma(registros_df)
            registros_df = actualizar_plazo_oficio_cierre(registros_df)

        # Procesar las metas
        metas_nuevas_df, metas_actualizar_df = procesar_metas(meta_df)

        # Agregar columnas calculadas
        registros_df['Porcentaje Avance'] = registros_df.apply(calcular_porcentaje_avance, axis=1)
        registros_df['Estado Fechas'] = registros_df.apply(verificar_estado_fechas, axis=1)

        # ===== MOSTRAR VALIDACIONES =====
        with st.expander("Validación de Reglas de Negocio"):
            st.markdown("### Estado de Validaciones")
            st.info("""
            **Reglas aplicadas automáticamente:**
            1. Si 'Entrega acuerdo de compromiso' no está vacío → 'Acuerdo de compromiso' = SI
            2. Si 'Análisis y cronograma' tiene fecha → 'Análisis de información' = SI
            3. Al introducir fecha en 'Estándares' → campos no completos = "No aplica"
            4. Si introduce fecha en 'Publicación' → 'Disponer datos temáticos' = SI
            5. Para 'Fecha de oficio de cierre' → requiere etapa de Publicación completada
            6. Al introducir 'Fecha de oficio de cierre' → Estado = "Completado" y avance = 100%
            7. Plazos calculados automáticamente considerando días hábiles y festivos
            
            **Nuevas funcionalidades implementadas:**
            8. 🔐 Sistema de autenticación para funciones administrativas
            9. 📅 Campo "Mes Proyectado" para organización temporal
            10. 🔍 Filtro por mes en reportes para análisis específicos
            11. 🌈 Gradiente de metas mejorado: rojo (0%) → verde oscuro (100%+)
            12. 📊 Diagrama de Gantt condicional: solo con filtros específicos
            """)
            mostrar_estado_validaciones(registros_df, st)

        # ===== CREAR PESTAÑAS =====
        tab1, tab2, tab3, tab4 = st.tabs([
            "Dashboard", 
            "Edición de Registros", 
            "Alertas de Vencimientos", 
            "Reportes"
        ])
     
        # ===== TAB 1: DASHBOARD =====
        with tab1:
            st.markdown("### Filtros")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                # Filtro por entidad
                entidades = ['Todas'] + sorted([e for e in registros_df['Entidad'].unique().tolist() if e])
                entidad_seleccionada = st.selectbox('Entidad', entidades, key="dash_entidad")
            
            with col2:
                # Filtro por funcionario
                funcionarios = ['Todos']
                if 'Funcionario' in registros_df.columns:
                    funcionarios_unicos = [f for f in registros_df['Funcionario'].dropna().unique().tolist() if f]
                    funcionarios += sorted(funcionarios_unicos)
                funcionario_seleccionado = st.selectbox('Funcionario', funcionarios, key="dash_funcionario")
            
            with col3:
                # Filtro por tipo de dato
                tipos_dato = ['Todos'] + sorted([t for t in registros_df['TipoDato'].dropna().unique().tolist() if t])
                tipo_dato_seleccionado = st.selectbox('Tipo de Dato', tipos_dato, key="dash_tipo")
            
            with col4:
                # Filtro por nivel de información dependiente de entidad
                if entidad_seleccionada != 'Todas':
                    niveles_entidad = registros_df[registros_df['Entidad'] == entidad_seleccionada]['Nivel Información '].dropna().unique().tolist()
                    niveles_entidad = [n for n in niveles_entidad if n]
                    niveles = ['Todos'] + sorted(niveles_entidad)
                    nivel_seleccionado = st.selectbox('Nivel de Información', niveles, key="dash_nivel")
                else:
                    nivel_seleccionado = 'Todos'
            
            # Aplicar filtros
            df_filtrado = registros_df.copy()
            
            if entidad_seleccionada != 'Todas':
                df_filtrado = df_filtrado[df_filtrado['Entidad'] == entidad_seleccionada]
            
            if funcionario_seleccionado != 'Todos' and 'Funcionario' in df_filtrado.columns:
                df_filtrado = df_filtrado[df_filtrado['Funcionario'] == funcionario_seleccionado]
            
            if tipo_dato_seleccionado != 'Todos':
                df_filtrado = df_filtrado[df_filtrado['TipoDato'].str.upper() == tipo_dato_seleccionado.upper()]
            
            if nivel_seleccionado != 'Todos':
                df_filtrado = df_filtrado[df_filtrado['Nivel Información '] == nivel_seleccionado]
            
            st.markdown("---")
            
            # Mostrar dashboard completo
            mostrar_dashboard(df_filtrado, metas_nuevas_df, metas_actualizar_df, registros_df,
                            entidad_seleccionada, funcionario_seleccionado, nivel_seleccionado)

        # ===== TAB 2: EDICIÓN =====
        with tab2:
            # Llamar a la función de edición
            registros_df = mostrar_edicion_registros(registros_df)

        # ===== TAB 3: ALERTAS =====
        with tab3:
            mostrar_alertas_vencimientos(registros_df)

        # ===== TAB 4: REPORTES =====
        with tab4:
            st.markdown("### Filtros de Reportes")
            
            # Primera fila de filtros
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                tipos_dato_reporte = ['Todos'] + sorted([t for t in registros_df['TipoDato'].dropna().unique().tolist() if t])
                tipo_dato_reporte = st.selectbox('Tipo de Dato', tipos_dato_reporte, key="reporte_tipo")
            
            with col2:
                acuerdo_opciones = ['Todos', 'Suscrito', 'No Suscrito']
                acuerdo_filtro = st.selectbox('Acuerdo de Compromiso', acuerdo_opciones, key="reporte_acuerdo")
            
            with col3:
                analisis_opciones = ['Todos', 'Completado', 'No Completado']
                analisis_filtro = st.selectbox('Análisis y Cronograma', analisis_opciones, key="reporte_analisis")
            
            with col4:
                # NUEVO FILTRO: Mes Proyectado
                meses_disponibles = ['Todos']
                if 'Mes Proyectado' in registros_df.columns:
                    meses_unicos = [m for m in registros_df['Mes Proyectado'].dropna().unique().tolist() if m]
                    meses_disponibles += sorted(meses_unicos)
                mes_filtro = st.selectbox('Mes Proyectado', meses_disponibles, key="reporte_mes")
            
            # Segunda fila de filtros
            col5, col6, col7 = st.columns(3)
            
            with col5:
                estandares_opciones = ['Todos', 'Completado', 'No Completado']
                estandares_filtro = st.selectbox('Estándares', estandares_opciones, key="reporte_estandares")
            
            with col6:
                publicacion_opciones = ['Todos', 'Completado', 'No Completado']
                publicacion_filtro = st.selectbox('Publicación', publicacion_opciones, key="reporte_publicacion")
            
            with col7:
                finalizado_opciones = ['Todos', 'Finalizado', 'No Finalizado']
                finalizado_filtro = st.selectbox('Finalizado', finalizado_opciones, key="reporte_finalizado")
            
            st.markdown("---")
            
            # Mostrar reportes
            mostrar_reportes(registros_df, tipo_dato_reporte, acuerdo_filtro, analisis_filtro, 
                           estandares_filtro, publicacion_filtro, finalizado_filtro, mes_filtro)

        # ===== FOOTER =====
        st.markdown("---")
        st.markdown("### Resumen del Sistema")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Campos", len(registros_df.columns))
        
        with col2:
            total_con_funcionario = len(registros_df[registros_df['Funcionario'].notna() & (registros_df['Funcionario'] != '')])
            st.metric("Con Funcionario", total_con_funcionario)
        
        with col3:
            en_proceso = len(registros_df[registros_df['Estado'].isin(['En proceso', 'En proceso oficio de cierre'])])
            st.metric("En Proceso", en_proceso)
        
        with col4:
            ultima_actualizacion = datetime.now().strftime("%d/%m/%Y %H:%M")
            st.metric("Última Actualización", ultima_actualizacion)

        # Información de versión
        st.info("""
        **Tablero de Control - Versión Completa con Mejoras y Autenticación**
        
        ✅ Todas las funcionalidades de edición han sido restauradas
        ✅ Sistema de validaciones completo
        ✅ Cálculo automático de plazos con días hábiles
        ✅ Gestión dinámica de funcionarios
        ✅ Guardado inteligente en Google Sheets
        ✅ Alertas de vencimiento detalladas
        ✅ Reportes avanzados con filtros
        
        **Mejoras Implementadas:**
        ✅ Gradiente de metas mejorado: rojo (0%) → verde oscuro (100%+)
        ✅ Diagrama de Gantt condicional: se muestra solo con filtros específicos
        ✅ Mensaje informativo para guiar al usuario sobre el Gantt
        
        **Nuevas Funcionalidades:**
        ✅ 🔐 Sistema de autenticación para administrador
        ✅ 📅 Campo "Mes Proyectado" en información básica
        ✅ 🔍 Filtro por mes proyectado en reportes
        ✅ 🔒 Protección de carga de datos Excel solo para admin
        """)
        
        # Mostrar estado de autenticación en footer
        if verificar_autenticacion():
            st.success("🔐 Sesión administrativa activa - Todas las funciones disponibles")
        else:
            st.warning("⚠️ Sesión no administrativa - Carga de datos restringida")

    except Exception as e:
        st.error(f"Error crítico: {str(e)}")
        
        # Información detallada del error para debugging
        import traceback
        with st.expander("Detalles del Error (para debugging)"):
            st.code(traceback.format_exc())
        
        st.markdown("### Solución de Problemas")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            **Problemas Comunes:**
            - Configuración de Google Sheets incorrecta
            - Credenciales faltantes o incorrectas
            - Estructura de datos incorrecta en Google Sheets
            - Problemas de conexión a internet
            - Problemas de autenticación
            """)
        
        with col2:
            st.markdown("""
            **Acciones Recomendadas:**
            - Usar el botón "Reconectar" arriba
            - Verificar configuración en el panel lateral
            - Revisar permisos del service account
            - Consultar las instrucciones de configuración
            - Verificar credenciales de autenticación admin
            """)
        
        # Botón de recuperación
        if st.button("🔄 Intentar Recuperación", type="primary"):
            # Limpiar estado y recargar
            for key in list(st.session_state.keys()):
                if key.startswith(('sheets_', 'registros_', 'meta_')):
                    del st.session_state[key]
            st.rerun()

if __name__ == "__main__":
    main()
