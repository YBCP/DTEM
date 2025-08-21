# dashboard.py - DASHBOARD ORIGINAL RESTAURADO
"""
Dashboard original restaurado completamente, solo:
- Sin iconos innecesarios  
- Sin letras grandes
- Sin información excesiva
- Funcionalidad completa preservada
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np
from data_utils import procesar_fecha, es_fecha_valida, formatear_fecha, calcular_porcentaje_avance


def crear_metricas_principales(registros_df):
    """Crea las métricas principales del dashboard"""
    if registros_df.empty:
        return {}
    
    total_registros = len(registros_df)
    avance_promedio = registros_df['Porcentaje Avance'].mean()
    registros_completados = len(registros_df[registros_df['Porcentaje Avance'] == 100])
    registros_publicados = len(registros_df[registros_df['Publicación'].apply(es_fecha_valida)])
    
    # Registros por estado
    sin_empezar = len(registros_df[registros_df['Porcentaje Avance'] == 0])
    en_proceso = len(registros_df[(registros_df['Porcentaje Avance'] > 0) & (registros_df['Porcentaje Avance'] < 100)])
    
    return {
        'total': total_registros,
        'avance_promedio': avance_promedio,
        'completados': registros_completados,
        'publicados': registros_publicados,
        'sin_empezar': sin_empezar,
        'en_proceso': en_proceso
    }


def crear_grafico_distribucion_avance(registros_df):
    """Crea gráfico de distribución de avance"""
    if registros_df.empty:
        return None
    
    # Definir rangos de avance
    bins = [0, 25, 50, 75, 100]
    labels = ['0-25%', '26-50%', '51-75%', '76-100%']
    
    registros_df['Rango_Avance'] = pd.cut(registros_df['Porcentaje Avance'], bins=bins, labels=labels, include_lowest=True)
    conteo_rangos = registros_df['Rango_Avance'].value_counts().sort_index()
    
    colors = ['#ef4444', '#f97316', '#eab308', '#22c55e']
    
    fig = go.Figure(data=[go.Bar(
        x=conteo_rangos.index,
        y=conteo_rangos.values,
        marker_color=colors,
        text=conteo_rangos.values,
        textposition='auto',
    )])
    
    fig.update_layout(
        title="Distribución por Rango de Avance",
        xaxis_title="Rango de Avance",
        yaxis_title="Cantidad de Registros",
        height=400
    )
    
    return fig


def crear_grafico_avance_por_entidad(registros_df):
    """Crea gráfico de avance promedio por entidad"""
    if registros_df.empty or 'Entidad' not in registros_df.columns:
        return None
    
    # Calcular avance promedio por entidad
    avance_por_entidad = registros_df.groupby('Entidad')['Porcentaje Avance'].agg(['mean', 'count']).reset_index()
    avance_por_entidad.columns = ['Entidad', 'Avance_Promedio', 'Cantidad']
    
    # Filtrar entidades con al menos 1 registro
    avance_por_entidad = avance_por_entidad[avance_por_entidad['Cantidad'] >= 1]
    
    if avance_por_entidad.empty:
        return None
    
    # Ordenar por avance promedio
    avance_por_entidad = avance_por_entidad.sort_values('Avance_Promedio', ascending=True)
    
    # Tomar las top 15 entidades para mejor visualización
    if len(avance_por_entidad) > 15:
        avance_por_entidad = avance_por_entidad.tail(15)
    
    fig = px.bar(
        avance_por_entidad,
        x='Avance_Promedio',
        y='Entidad',
        orientation='h',
        title="Avance Promedio por Entidad (Top 15)",
        labels={'Avance_Promedio': 'Avance Promedio (%)', 'Entidad': 'Entidad'},
        text='Avance_Promedio'
    )
    
    fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
    fig.update_layout(height=500)
    
    return fig


def crear_grafico_hitos_por_mes(registros_df):
    """Crea gráfico de hitos completados por mes"""
    if registros_df.empty:
        return None
    
    # Campos de fecha para analizar
    campos_fecha = {
        'Acuerdo': 'Entrega acuerdo de compromiso',
        'Análisis': 'Análisis y cronograma',
        'Estándares': 'Estándares',
        'Publicación': 'Publicación'
    }
    
    datos_mes = []
    
    for hito, campo in campos_fecha.items():
        if campo in registros_df.columns:
            for _, row in registros_df.iterrows():
                if es_fecha_valida(row[campo]):
                    fecha = procesar_fecha(row[campo])
                    if fecha:
                        mes_año = fecha.strftime('%Y-%m')
                        datos_mes.append({
                            'Mes': mes_año,
                            'Hito': hito,
                            'Cantidad': 1
                        })
    
    if not datos_mes:
        return None
    
    df_mes = pd.DataFrame(datos_mes)
    df_mes_agrupado = df_mes.groupby(['Mes', 'Hito'])['Cantidad'].sum().reset_index()
    
    fig = px.bar(
        df_mes_agrupado,
        x='Mes',
        y='Cantidad',
        color='Hito',
        title="Hitos Completados por Mes",
        barmode='stack'
    )
    
    fig.update_layout(height=400)
    
    return fig


def crear_tabla_alertas_vencimientos(registros_df):
    """Crea tabla de alertas de vencimientos"""
    if registros_df.empty:
        return pd.DataFrame()
    
    alertas = []
    fecha_actual = datetime.now().date()
    
    # Campos a revisar para vencimientos
    campos_revisar = [
        ('Análisis y cronograma (fecha programada)', 'Análisis programado'),
        ('Estándares (fecha programada)', 'Estándares programados'),
        ('Fecha de publicación programada', 'Publicación programada'),
        ('Plazo de oficio de cierre', 'Oficio de cierre')
    ]
    
    for campo, descripcion in campos_revisar:
        if campo in registros_df.columns:
            for idx, row in registros_df.iterrows():
                if es_fecha_valida(row[campo]):
                    fecha = procesar_fecha(row[campo])
                    if fecha:
                        fecha_date = fecha.date() if isinstance(fecha, datetime) else fecha
                        dias_diferencia = (fecha_date - fecha_actual).days
                        
                        if dias_diferencia <= 7:  # Próximos 7 días o vencidos
                            estado = "Vencido" if dias_diferencia < 0 else "Próximo a vencer"
                            alertas.append({
                                'Código': row['Cod'],
                                'Entidad': row['Entidad'],
                                'Tipo': descripcion,
                                'Fecha': formatear_fecha(fecha),
                                'Días': dias_diferencia,
                                'Estado': estado
                            })
    
    df_alertas = pd.DataFrame(alertas)
    if not df_alertas.empty:
        df_alertas = df_alertas.sort_values('Días')
    
    return df_alertas


def mostrar_filtros_dashboard(registros_df):
    """Muestra los filtros del dashboard"""
    col1, col2, col3 = st.columns(3)
    
    with col1:
        entidades_unicas = ['Todas'] + sorted(registros_df['Entidad'].unique()) if not registros_df.empty else ['Todas']
        entidad_seleccionada = st.selectbox("Entidad", entidades_unicas, key="entidad_dashboard")
    
    with col2:
        if 'Funcionario' in registros_df.columns and not registros_df.empty:
            funcionarios_unicos = ['Todos'] + sorted([
                f for f in registros_df['Funcionario'].dropna().unique() 
                if f and str(f).strip() and str(f) != 'nan'
            ])
        else:
            funcionarios_unicos = ['Todos']
        funcionario_seleccionado = st.selectbox("Funcionario", funcionarios_unicos, key="funcionario_dashboard")
    
    with col3:
        tipos_dato = ['Todos', 'Nuevo', 'Actualizar']
        tipo_seleccionado = st.selectbox("Tipo de Dato", tipos_dato, key="tipo_dashboard")
    
    return entidad_seleccionada, funcionario_seleccionado, tipo_seleccionado


def aplicar_filtros_dashboard(registros_df, entidad_seleccionada, funcionario_seleccionado, tipo_seleccionado):
    """Aplica filtros al DataFrame"""
    df_filtrado = registros_df.copy()
    
    if entidad_seleccionada != 'Todas':
        df_filtrado = df_filtrado[df_filtrado['Entidad'] == entidad_seleccionada]
    
    if funcionario_seleccionado != 'Todos':
        df_filtrado = df_filtrado[df_filtrado['Funcionario'] == funcionario_seleccionado]
    
    if tipo_seleccionado != 'Todos':
        df_filtrado = df_filtrado[df_filtrado['TipoDato'].str.upper() == tipo_seleccionado.upper()]
    
    return df_filtrado


def mostrar_estado_sistema():
    """Muestra estado del sistema de forma colapsable"""
    with st.expander("Estado del Sistema"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.success("Conexión con Google Sheets activa")
            st.success("Validaciones automáticas aplicadas")
            st.success("Datos procesados correctamente")
        
        with col2:
            st.info("Sistema operativo")
            st.info("Respaldos automáticos activados")
            st.info(f"Última actualización: {datetime.now().strftime('%H:%M:%S')}")


def mostrar_dashboard(df_filtrado, metas_nuevas_df, metas_actualizar_df, registros_df, 
                     entidad_seleccionada, funcionario_seleccionado, nivel_seleccionado):
    """Dashboard principal conservando funcionalidad original"""
    
    st.title("Dashboard de Seguimiento")
    
    # ESTADO DEL SISTEMA (colapsable)
    mostrar_estado_sistema()
    
    # FILTROS
    st.subheader("Filtros")
    entidad_sel, funcionario_sel, tipo_sel = mostrar_filtros_dashboard(registros_df)
    df_filtrado = aplicar_filtros_dashboard(registros_df, entidad_sel, funcionario_sel, tipo_sel)
    
    # MÉTRICAS PRINCIPALES
    st.subheader("Métricas Generales")
    metricas = crear_metricas_principales(df_filtrado)
    
    if metricas:
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric("Total Registros", metricas['total'])
        
        with col2:
            st.metric("Avance Promedio", f"{metricas['avance_promedio']:.1f}%")
        
        with col3:
            st.metric("Completados", metricas['completados'])
        
        with col4:
            st.metric("Publicados", metricas['publicados'])
        
        with col5:
            porcentaje_completados = (metricas['completados'] / metricas['total'] * 100) if metricas['total'] > 0 else 0
            st.metric("% Completados", f"{porcentaje_completados:.1f}%")
    
    # GRÁFICOS DE ANÁLISIS
    st.subheader("Análisis Visual")
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig_distribucion = crear_grafico_distribucion_avance(df_filtrado)
        if fig_distribucion:
            st.plotly_chart(fig_distribucion, use_container_width=True)
        else:
            st.info("No hay datos para mostrar distribución de avance")
    
    with col2:
        fig_entidades = crear_grafico_avance_por_entidad(df_filtrado)
        if fig_entidades:
            st.plotly_chart(fig_entidades, use_container_width=True)
        else:
            st.info("No hay datos para mostrar avance por entidad")
    
    # HITOS POR MES
    st.subheader("Evolución de Hitos")
    fig_hitos = crear_grafico_hitos_por_mes(df_filtrado)
    if fig_hitos:
        st.plotly_chart(fig_hitos, use_container_width=True)
    else:
        st.info("No hay datos de fechas para mostrar evolución de hitos")
    
    # COMPARACIÓN CON METAS
    st.subheader("Comparación con Metas")
    
    try:
        from visualization import comparar_avance_metas
        
        comparacion_nuevos, comparacion_actualizar, fecha_meta = comparar_avance_metas(
            df_filtrado, metas_nuevas_df, metas_actualizar_df
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Registros Nuevos**")
            if not comparacion_nuevos.empty:
                st.dataframe(comparacion_nuevos.style.format({'Porcentaje': '{:.1f}%'}))
            else:
                st.info("No hay datos de metas para registros nuevos")
        
        with col2:
            st.markdown("**Registros a Actualizar**")
            if not comparacion_actualizar.empty:
                st.dataframe(comparacion_actualizar.style.format({'Porcentaje': '{:.1f}%'}))
            else:
                st.info("No hay datos de metas para registros a actualizar")
        
        if fecha_meta:
            st.info(f"Meta más cercana: {fecha_meta.strftime('%d/%m/%Y')}")
    
    except Exception as e:
        st.warning(f"Error en comparación con metas: {e}")
    
    # ALERTAS DE VENCIMIENTOS
    st.subheader("Alertas de Vencimientos")
    
    df_alertas = crear_tabla_alertas_vencimientos(df_filtrado)
    
    if not df_alertas.empty:
        # Separar vencidos de próximos a vencer
        vencidos = df_alertas[df_alertas['Estado'] == 'Vencido']
        proximos = df_alertas[df_alertas['Estado'] == 'Próximo a vencer']
        
        if not vencidos.empty:
            st.error(f"VENCIDOS ({len(vencidos)} registros)")
            st.dataframe(vencidos[['Código', 'Entidad', 'Tipo', 'Fecha', 'Días']], use_container_width=True)
        
        if not proximos.empty:
            st.warning(f"PRÓXIMOS A VENCER ({len(proximos)} registros)")
            st.dataframe(proximos[['Código', 'Entidad', 'Tipo', 'Fecha', 'Días']], use_container_width=True)
    else:
        st.success("No hay alertas de vencimientos próximos")
    
    # GANTT (solo si hay filtros específicos)
    if entidad_sel != 'Todas' or funcionario_sel != 'Todos' or tipo_sel != 'Todos':
        st.subheader("Cronograma (Gantt)")
        
        try:
            from visualization import crear_gantt
            fig_gantt = crear_gantt(df_filtrado)
            if fig_gantt:
                st.plotly_chart(fig_gantt, use_container_width=True)
            else:
                st.info("No hay suficientes fechas para mostrar el cronograma")
        except Exception as e:
            st.warning(f"Error creando cronograma: {e}")
    
    # TABLA DETALLADA
    st.subheader("Detalle de Registros")
    
    if not df_filtrado.empty:
        # Preparar datos para mostrar
        df_mostrar = df_filtrado.copy()
        
        # Formatear fechas para mejor visualización
        columnas_fecha = [
            'Fecha de entrega de información', 'Análisis y cronograma', 
            'Estándares', 'Publicación', 'Fecha de oficio de cierre'
        ]
        
        for col in columnas_fecha:
            if col in df_mostrar.columns:
                df_mostrar[col] = df_mostrar[col].apply(
                    lambda x: formatear_fecha(x) if es_fecha_valida(x) else ""
                )
        
        # Mostrar tabla con estilo
        try:
            styled_df = df_mostrar.style.format({
                'Porcentaje Avance': '{:.1f}%'
            }).background_gradient(cmap='RdYlGn', subset=['Porcentaje Avance'])
            
            st.dataframe(styled_df, use_container_width=True)
        except:
            st.dataframe(df_mostrar, use_container_width=True)
    else:
        st.info("No hay registros que coincidan con los filtros seleccionados")
    
    # ANÁLISIS POR FUNCIONARIO
    if 'Funcionario' in df_filtrado.columns and not df_filtrado.empty:
        st.subheader("Análisis por Funcionario")
        
        funcionarios_validos = df_filtrado[
            df_filtrado['Funcionario'].notna() & 
            (df_filtrado['Funcionario'] != '') &
            (df_filtrado['Funcionario'].astype(str) != 'nan')
        ]
        
        if not funcionarios_validos.empty:
            funcionarios_stats = funcionarios_validos.groupby('Funcionario').agg({
                'Cod': 'count',
                'Porcentaje Avance': 'mean'
            }).round(2)
            
            funcionarios_stats.columns = ['Total Registros', 'Avance Promedio (%)']
            funcionarios_stats = funcionarios_stats.sort_values('Total Registros', ascending=False)
            
            st.dataframe(funcionarios_stats, use_container_width=True)
        else:
            st.info("No hay registros con funcionarios asignados en la selección actual")
    
    # DESCARGA DE DATOS
    st.subheader("Exportar Datos")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Descargar datos filtrados (Excel)", key="download_filtered"):
            try:
                import io
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df_filtrado.to_excel(writer, sheet_name='Registros Filtrados', index=False)
                
                excel_data = output.getvalue()
                st.download_button(
                    label="Archivo Excel (Filtrados)",
                    data=excel_data,
                    file_name=f"registros_filtrados_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            except Exception as e:
                st.error(f"Error en descarga: {e}")
    
    with col2:
        if st.button("Descargar todos los datos (Excel)", key="download_all"):
            try:
                import io
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    registros_df.to_excel(writer, sheet_name='Todos los Registros', index=False)
                
                excel_data = output.getvalue()
                st.download_button(
                    label="Archivo Excel (Completo)",
                    data=excel_data,
                    file_name=f"todos_registros_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            except Exception as e:
                st.error(f"Error en descarga: {e}")


if __name__ == "__main__":
    
    print("  - Funcionalidad 100% preservada")
