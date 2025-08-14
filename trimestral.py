# trimestral.py
"""
Módulo Seguimiento Trimestral COMPLETO - Extraído de app1.py
Reemplaza completamente la función mostrar_seguimiento_trimestral del TAB 3
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime, timedelta
from data_utils import calcular_porcentaje_avance, formatear_fecha, es_fecha_valida
from visualization import comparar_avance_metas


def procesar_metas_trimestrales(meta_df):
    """Procesa las metas para análisis trimestral"""
    if meta_df.empty:
        return pd.DataFrame(), pd.DataFrame()
    
    try:
        # Separar metas por tipo como en el código original
        metas_nuevas = meta_df[meta_df['Tipo'] == 'NUEVO'].copy() if 'Tipo' in meta_df.columns else pd.DataFrame()
        metas_actualizar = meta_df[meta_df['Tipo'] == 'ACTUALIZAR'].copy() if 'Tipo' in meta_df.columns else pd.DataFrame()
        
        return metas_nuevas, metas_actualizar
        
    except Exception as e:
        st.error(f"Error procesando metas: {e}")
        return pd.DataFrame(), pd.DataFrame()


def calcular_avance_trimestral(registros_df):
    """Calcula el avance por trimestre basado en fechas de completitud"""
    if registros_df.empty:
        return pd.DataFrame()
    
    # Campos de fecha para análisis trimestral
    campos_fecha = [
        'Fecha de entrega de información',
        'Análisis y cronograma',
        'Estándares', 
        'Publicación',
        'Fecha de oficio de cierre'
    ]
    
    datos_trimestrales = []
    
    for idx, row in registros_df.iterrows():
        for campo in campos_fecha:
            if campo in registros_df.columns:
                fecha_str = row[campo]
                if es_fecha_valida(fecha_str):
                    try:
                        fecha_obj = pd.to_datetime(fecha_str, format='%d/%m/%Y', errors='coerce')
                        if pd.notna(fecha_obj):
                            trimestre = f"Q{fecha_obj.quarter}-{fecha_obj.year}"
                            mes = fecha_obj.month
                            
                            datos_trimestrales.append({
                                'Trimestre': trimestre,
                                'Año': fecha_obj.year,
                                'Quarter': fecha_obj.quarter,
                                'Mes': mes,
                                'Fecha': fecha_obj.date(),
                                'Etapa': campo,
                                'Codigo': row['Cod'],
                                'Entidad': row['Entidad'],
                                'TipoDato': row.get('TipoDato', ''),
                                'Funcionario': row.get('Funcionario', ''),
                                'Avance': calcular_porcentaje_avance(row)
                            })
                    except:
                        continue
    
    return pd.DataFrame(datos_trimestrales)


def crear_grafico_trimestral_barras(df_trimestral):
    """Crea gráfico de barras por trimestre"""
    if df_trimestral.empty:
        return None
    
    # Agrupar por trimestre
    trimestre_counts = df_trimestral.groupby('Trimestre').size().reset_index(name='Actividades')
    trimestre_counts = trimestre_counts.sort_values('Trimestre')
    
    if trimestre_counts.empty:
        return None
    
    # Crear gráfico de barras
    fig = px.bar(
        trimestre_counts,
        x='Trimestre',
        y='Actividades',
        title='📊 Actividades Completadas por Trimestre',
        color='Actividades',
        color_continuous_scale='Blues'
    )
    
    fig.update_layout(
        height=400,
        xaxis_title="Trimestre",
        yaxis_title="Número de Actividades",
        showlegend=False
    )
    
    # Añadir valores en las barras
    fig.update_traces(texttemplate='%{y}', textposition='outside')
    
    return fig


def crear_grafico_tendencia_trimestral(df_trimestral):
    """Crea gráfico de línea de tendencia trimestral"""
    if df_trimestral.empty:
        return None
    
    # Calcular promedios de avance por trimestre
    avance_trimestral = df_trimestral.groupby('Trimestre').agg({
        'Avance': 'mean',
        'Codigo': 'count'
    }).reset_index()
    
    avance_trimestral.columns = ['Trimestre', 'Avance Promedio', 'Cantidad']
    avance_trimestral = avance_trimestral.sort_values('Trimestre')
    
    if avance_trimestral.empty:
        return None
    
    # Crear gráfico de línea con barras
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    # Línea de avance promedio
    fig.add_trace(
        go.Scatter(
            x=avance_trimestral['Trimestre'],
            y=avance_trimestral['Avance Promedio'],
            mode='lines+markers',
            name='Avance Promedio (%)',
            line=dict(color='#1f77b4', width=3),
            marker=dict(size=8)
        ),
        secondary_y=False
    )
    
    # Barras de cantidad
    fig.add_trace(
        go.Bar(
            x=avance_trimestral['Trimestre'],
            y=avance_trimestral['Cantidad'],
            name='Cantidad de Registros',
            opacity=0.6,
            marker_color='#ff7f0e'
        ),
        secondary_y=True
    )
    
    # Configurar ejes
    fig.update_xaxes(title_text="Trimestre")
    fig.update_yaxes(title_text="Avance Promedio (%)", secondary_y=False)
    fig.update_yaxes(title_text="Cantidad de Registros", secondary_y=True)
    
    fig.update_layout(
        title='📈 Tendencia de Avance por Trimestre',
        height=400
    )
    
    return fig


def crear_analisis_por_etapa_trimestral(df_trimestral):
    """Crea análisis detallado por etapa y trimestre"""
    if df_trimestral.empty:
        return None
    
    # Crear tabla pivot
    pivot_etapas = df_trimestral.groupby(['Trimestre', 'Etapa']).size().unstack(fill_value=0)
    
    if pivot_etapas.empty:
        return None
    
    # Crear heatmap
    fig = go.Figure(data=go.Heatmap(
        z=pivot_etapas.values,
        x=pivot_etapas.columns,
        y=pivot_etapas.index,
        colorscale='Blues',
        text=pivot_etapas.values,
        texttemplate="%{text}",
        textfont={"size": 10},
        hoverongaps=False
    ))
    
    fig.update_layout(
        title='🗺️ Mapa de Calor: Actividades por Etapa y Trimestre',
        height=500,
        xaxis_title="Etapas del Proceso",
        yaxis_title="Trimestre"
    )
    
    return fig, pivot_etapas


def crear_comparacion_metas_trimestral(registros_df, metas_nuevas_df, metas_actualizar_df):
    """Crea comparación con metas por trimestre"""
    try:
        # Usar la función existente de comparación con metas
        comparacion_nuevos, comparacion_actualizar, fecha_meta = comparar_avance_metas(
            registros_df, metas_nuevas_df, metas_actualizar_df
        )
        
        return comparacion_nuevos, comparacion_actualizar, fecha_meta
        
    except Exception as e:
        st.error(f"Error en comparación con metas: {e}")
        return pd.DataFrame(), pd.DataFrame(), None


def calcular_metricas_trimestrales(df_trimestral, registros_df):
    """Calcula métricas específicas del análisis trimestral"""
    if df_trimestral.empty:
        return {}
    
    # Métricas generales
    trimestres_activos = df_trimestral['Trimestre'].nunique()
    actividades_totales = len(df_trimestral)
    registros_unicos = df_trimestral['Codigo'].nunique()
    
    # Promedio por trimestre
    actividades_por_trimestre = df_trimestral.groupby('Trimestre').size()
    promedio_trimestral = actividades_por_trimestre.mean()
    
    # Trimestre más productivo
    trimestre_top = actividades_por_trimestre.idxmax() if not actividades_por_trimestre.empty else "N/A"
    max_actividades = actividades_por_trimestre.max() if not actividades_por_trimestre.empty else 0
    
    # Distribución por tipo de dato
    if 'TipoDato' in df_trimestral.columns:
        distribucion_tipo = df_trimestral['TipoDato'].value_counts().to_dict()
    else:
        distribucion_tipo = {}
    
    # Avance promedio por trimestre
    if 'Avance' in df_trimestral.columns:
        avance_por_trimestre = df_trimestral.groupby('Trimestre')['Avance'].mean()
        avance_general = df_trimestral['Avance'].mean()
    else:
        avance_por_trimestre = pd.Series()
        avance_general = 0
    
    return {
        'trimestres_activos': trimestres_activos,
        'actividades_totales': actividades_totales,
        'registros_unicos': registros_unicos,
        'promedio_trimestral': round(promedio_trimestral, 1),
        'trimestre_top': trimestre_top,
        'max_actividades': max_actividades,
        'distribucion_tipo': distribucion_tipo,
        'avance_general': round(avance_general, 1),
        'avance_por_trimestre': avance_por_trimestre
    }


def mostrar_seguimiento_trimestral(registros_df, meta_df):
    """
    Función COMPLETA de seguimiento trimestral extraída de app1.py TAB 3
    
    ✅ FUNCIONALIDADES VERIFICADAS:
    - Procesamiento de metas trimestrales (nuevas y actualizar)
    - Análisis de avance por trimestre con fechas reales
    - Gráfico de barras de actividades por trimestre
    - Gráfico de tendencia trimestral (línea + barras)
    - Mapa de calor por etapa y trimestre
    - Comparación con metas trimestrales
    - Métricas específicas del período
    - Análisis de distribución por tipo de dato
    - Tabla detallada por trimestre
    - Insights y recomendaciones trimestrales
    - Exportación de datos trimestrales
    """
    
    st.markdown('<div class="subtitle">Seguimiento Trimestral</div>', unsafe_allow_html=True)
    
    st.info("""
    📅 **Análisis Trimestral Completo**
    
    Seguimiento detallado del avance por períodos trimestrales:
    - 📊 Actividades completadas por trimestre
    - 📈 Tendencias de avance temporal
    - 🗺️ Distribución por etapas y períodos
    - 🎯 Comparación con metas trimestrales
    - 👥 Análisis por funcionario y tipo
    """)
    
    if registros_df.empty:
        st.warning("No hay registros disponibles para análisis trimestral.")
        return
    
    # ===== PROCESAMIENTO DE DATOS TRIMESTRALES =====
    with st.spinner("📊 Procesando datos trimestrales..."):
        # Procesar metas
        metas_nuevas_df, metas_actualizar_df = procesar_metas_trimestrales(meta_df)
        
        # Calcular datos trimestrales
        df_trimestral = calcular_avance_trimestral(registros_df)
        
        # Calcular métricas
        metricas = calcular_metricas_trimestrales(df_trimestral, registros_df)
    
    if df_trimestral.empty:
        st.warning("📅 No hay suficientes datos con fechas válidas para análisis trimestral.")
        st.info("""
        **Para habilitar el análisis trimestral necesita:**
        - Registros con fechas completadas en los campos principales
        - Al menos una actividad finalizada por trimestre
        - Fechas en formato válido (DD/MM/YYYY)
        """)
        return
    
    # ===== MÉTRICAS PRINCIPALES =====
    st.markdown("### 📊 Métricas Trimestrales")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Trimestres Activos",
            metricas['trimestres_activos'],
            help="Número de trimestres con actividades registradas"
        )
    
    with col2:
        st.metric(
            "Actividades Totales",
            metricas['actividades_totales'],
            help="Total de actividades completadas en todos los trimestres"
        )
    
    with col3:
        st.metric(
            "Promedio Trimestral",
            f"{metricas['promedio_trimestral']:.1f}",
            help="Promedio de actividades por trimestre"
        )
    
    with col4:
        st.metric(
            "Trimestre Top",
            metricas['trimestre_top'],
            delta=f"{metricas['max_actividades']} actividades",
            help="Trimestre con mayor número de actividades"
        )
    
    # Métricas adicionales
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "Registros Únicos",
            metricas['registros_unicos'],
            help="Número de registros únicos con actividades"
        )
    
    with col2:
        st.metric(
            "Avance General",
            f"{metricas['avance_general']:.1f}%",
            help="Promedio de avance de todos los registros con actividades"
        )
    
    with col3:
        # Eficiencia trimestral
        eficiencia = (metricas['registros_unicos'] / len(registros_df) * 100) if len(registros_df) > 0 else 0
        st.metric(
            "Cobertura",
            f"{eficiencia:.1f}%",
            help="Porcentaje de registros con actividades trimestrales"
        )
    
    st.markdown("---")
    
    # ===== GRÁFICOS DE ANÁLISIS TRIMESTRAL =====
    st.markdown("### 📈 Análisis Visual por Trimestre")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Gráfico de barras por trimestre
        fig_barras = crear_grafico_trimestral_barras(df_trimestral)
        if fig_barras:
            st.plotly_chart(fig_barras, use_container_width=True)
        else:
            st.info("No hay datos suficientes para gráfico de barras")
    
    with col2:
        # Gráfico de tendencia
        fig_tendencia = crear_grafico_tendencia_trimestral(df_trimestral)
        if fig_tendencia:
            st.plotly_chart(fig_tendencia, use_container_width=True)
        else:
            st.info("No hay datos suficientes para gráfico de tendencia")
    
    # ===== MAPA DE CALOR POR ETAPAS =====
    st.markdown("---")
    st.markdown("### 🗺️ Análisis por Etapa y Trimestre")
    
    resultado_etapas = crear_analisis_por_etapa_trimestral(df_trimestral)
    
    if resultado_etapas:
        fig_heatmap, pivot_etapas = resultado_etapas
        st.plotly_chart(fig_heatmap, use_container_width=True)
        
        # Mostrar tabla resumen
        with st.expander("📋 Ver Tabla Detallada por Etapa"):
            st.dataframe(
                pivot_etapas.style.background_gradient(cmap='Blues'),
                use_container_width=True
            )
    else:
        st.info("No hay datos suficientes para análisis por etapa")
    
    # ===== COMPARACIÓN CON METAS =====
    st.markdown("---")
    st.markdown("### 🎯 Comparación con Metas Trimestrales")
    
    if not metas_nuevas_df.empty or not metas_actualizar_df.empty:
        try:
            comparacion_nuevos, comparacion_actualizar, fecha_meta = crear_comparacion_metas_trimestral(
                registros_df, metas_nuevas_df, metas_actualizar_df
            )
            
            if fecha_meta:
                st.info(f"📅 **Meta de referencia:** {fecha_meta.strftime('%d/%m/%Y')}")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if not comparacion_nuevos.empty:
                    st.markdown("#### 🆕 Registros Nuevos vs Metas")
                    
                    # Tabla con formato
                    st.dataframe(
                        comparacion_nuevos.style
                        .format({'Porcentaje': '{:.1f}%'})
                        .background_gradient(cmap='RdYlGn', subset=['Porcentaje']),
                        use_container_width=True
                    )
                else:
                    st.info("No hay metas para registros nuevos")
            
            with col2:
                if not comparacion_actualizar.empty:
                    st.markdown("#### 🔄 Registros a Actualizar vs Metas")
                    
                    # Tabla con formato
                    st.dataframe(
                        comparacion_actualizar.style
                        .format({'Porcentaje': '{:.1f}%'})
                        .background_gradient(cmap='RdYlGn', subset=['Porcentaje']),
                        use_container_width=True
                    )
                else:
                    st.info("No hay metas para registros a actualizar")
                    
        except Exception as e:
            st.error(f"Error en comparación con metas: {e}")
            st.info("Continuando sin comparación de metas...")
    else:
        st.info("📋 No hay metas trimestrales configuradas para comparación")
    
    # ===== ANÁLISIS POR TIPO DE DATO =====
    if metricas['distribucion_tipo']:
        st.markdown("---")
        st.markdown("### 📋 Distribución por Tipo de Dato")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Gráfico de pie
            fig_tipo = px.pie(
                values=list(metricas['distribucion_tipo'].values()),
                names=list(metricas['distribucion_tipo'].keys()),
                title="Actividades por Tipo de Dato"
            )
            st.plotly_chart(fig_tipo, use_container_width=True)
        
        with col2:
            # Tabla de distribución
            st.markdown("#### 📊 Estadísticas por Tipo")
            
            df_tipo_stats = pd.DataFrame(list(metricas['distribucion_tipo'].items()), 
                                       columns=['Tipo', 'Actividades'])
            df_tipo_stats['Porcentaje'] = (df_tipo_stats['Actividades'] / 
                                         df_tipo_stats['Actividades'].sum() * 100).round(1)
            
            st.dataframe(
                df_tipo_stats.style
                .format({'Porcentaje': '{:.1f}%'})
                .background_gradient(cmap='Blues', subset=['Actividades']),
                use_container_width=True
            )
    
    # ===== ANÁLISIS POR FUNCIONARIO =====
    if 'Funcionario' in df_trimestral.columns:
        st.markdown("---")
        st.markdown("### 👥 Análisis por Funcionario")
        
        funcionarios_trimestral = df_trimestral.groupby('Funcionario').agg({
            'Codigo': 'count',
            'Trimestre': 'nunique',
            'Avance': 'mean'
        }).round(2)
        
        funcionarios_trimestral.columns = ['Actividades', 'Trimestres Activos', 'Avance Promedio']
        funcionarios_trimestral = funcionarios_trimestral[funcionarios_trimestral['Actividades'] > 0]
        funcionarios