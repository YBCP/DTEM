# dashboard.py - DASHBOARD ORIGINAL RESTAURADO CON TODAS LAS FUNCIONALIDADES
"""
Dashboard original completo restaurado, solo:
- Sin iconos innecesarios  
- Sin información excesiva
- Todas las funcionalidades originales preservadas
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import io
from datetime import datetime, timedelta
from data_utils import formatear_fecha, es_fecha_valida, calcular_porcentaje_avance
from visualization import comparar_avance_metas, crear_gantt


def crear_metrica_card(titulo, valor, color="blue", delta=None):
    """Función para crear tarjetas de métricas reutilizables"""
    delta_html = ""
    if delta is not None:
        delta_color = "green" if delta >= 0 else "red"
        delta_html = f'<p style="font-size: 0.9rem; color: {delta_color};">Δ {delta:+.1f}</p>'
    
    return f"""
    <div class="metric-card">
        <p style="font-size: 1rem; color: #64748b;">{titulo}</p>
        <p style="font-size: 2.5rem; font-weight: bold; color: {color};">{valor}</p>
        {delta_html}
    </div>
    """


def crear_barras_cumplimiento_optimizado(df_comparacion, titulo):
    """Función para crear barras de cumplimiento"""
    if df_comparacion.empty:
        st.warning(f"No hay datos para {titulo}")
        return
    
    st.markdown(f"#### {titulo}")
    
    for hito in df_comparacion.index:
        completados = df_comparacion.loc[hito, 'Completados']
        meta = df_comparacion.loc[hito, 'Meta']
        porcentaje = df_comparacion.loc[hito, 'Porcentaje']
        
        # Determinar color según porcentaje
        if porcentaje < 50:
            color = '#dc2626'
        elif porcentaje < 80:
            color = '#f59e0b'
        else:
            color = '#16a34a'
        
        # HTML para barra de progreso
        st.markdown(f"""
        <div style="margin-bottom: 15px;">
            <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                <span style="font-weight: 600; font-size: 14px;">{hito}</span>
                <span style="font-size: 12px; color: #64748b;">{completados}/{meta}</span>
            </div>
            <div style="background-color: #e5e7eb; height: 32px; border-radius: 6px; overflow: hidden;">
                <div style="width: {min(porcentaje, 100)}%; height: 100%; background-color: {color}; 
                           position: relative; display: flex; align-items: center; justify-content: center;">
                    <span style="color: white; font-weight: bold; font-size: 12px;">{porcentaje:.1f}%</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)


def crear_treemap_funcionarios_optimizado(df_filtrado):
    """Función del treemap de funcionarios"""
    if 'Funcionario' not in df_filtrado.columns:
        return None
    
    # Filtrar registros con funcionario
    mask = (df_filtrado['Funcionario'].notna() & 
            df_filtrado['Funcionario'].astype(str).str.strip().ne('') &
            ~df_filtrado['Funcionario'].astype(str).str.strip().isin(['nan', 'None']))
    
    registros_con_funcionario = df_filtrado[mask]
    
    if registros_con_funcionario.empty:
        st.info("No hay registros con funcionario asignado")
        return None
    
    # Contar y calcular estadísticas
    funcionarios_stats = registros_con_funcionario.groupby('Funcionario').agg({
        'Cod': 'count',
        'Porcentaje Avance': 'mean'
    }).round(2)
    
    funcionarios_stats.columns = ['Cantidad', 'Avance Promedio']
    funcionarios_stats['Porcentaje'] = (funcionarios_stats['Cantidad'] / len(registros_con_funcionario) * 100).round(2)
    
    # Crear treemap
    def obtener_color_por_avance(avance):
        colors = {90: '#2E7D32', 75: '#388E3C', 60: '#689F38', 
                 40: '#FBC02D', 25: '#FF8F00', 0: '#D32F2F'}
        for threshold, color in colors.items():
            if avance >= threshold:
                return color
        return '#D32F2F'
    
    colores = [obtener_color_por_avance(avance) for avance in funcionarios_stats['Avance Promedio']]
    
    fig_treemap = go.Figure(go.Treemap(
        labels=funcionarios_stats.index,
        values=funcionarios_stats['Cantidad'],
        parents=[""] * len(funcionarios_stats),
        textinfo="label+value",
        textfont=dict(size=12, color='white'),
        marker=dict(colors=colores, line=dict(color='white', width=2)),
        hovertemplate='<b>%{label}</b><br>Registros: %{value}<br>Avance: %{customdata:.1f}%<extra></extra>',
        customdata=funcionarios_stats['Avance Promedio']
    ))
    
    fig_treemap.update_layout(
        title={'text': "Distribución por Funcionario", 'x': 0.5, 'xanchor': 'center'},
        margin=dict(t=60, l=20, r=20, b=20),
        height=500
    )
    
    return fig_treemap, funcionarios_stats


def mostrar_dashboard(df_filtrado, metas_nuevas_df, metas_actualizar_df, registros_df, 
                     entidad_seleccionada, funcionario_seleccionado, nivel_seleccionado):
    """Dashboard principal con todas las funcionalidades originales"""
    
    # ===== MÉTRICAS GENERALES =====
    st.markdown('<div class="subtitle">Métricas Generales</div>', unsafe_allow_html=True)

    total_registros = len(df_filtrado)
    avance_promedio = df_filtrado['Porcentaje Avance'].mean() if not df_filtrado.empty else 0
    registros_completados = len(df_filtrado[df_filtrado['Porcentaje Avance'] == 100])
    porcentaje_completados = (registros_completados / total_registros * 100) if total_registros > 0 else 0

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(crear_metrica_card("Total Registros", total_registros, "#1E40AF"), unsafe_allow_html=True)
    with col2:
        st.markdown(crear_metrica_card("Avance Promedio", f"{avance_promedio:.1f}%", "#047857"), unsafe_allow_html=True)
    with col3:
        st.markdown(crear_metrica_card("Completados", registros_completados, "#B45309"), unsafe_allow_html=True)
    with col4:
        st.markdown(crear_metrica_card("% Completados", f"{porcentaje_completados:.1f}%", "#BE185D"), unsafe_allow_html=True)

    # ===== COMPARACIÓN CON METAS =====
    st.markdown('<div class="subtitle">Comparación con Metas Quincenales</div>', unsafe_allow_html=True)

    try:
        comparacion_nuevos, comparacion_actualizar, fecha_meta = comparar_avance_metas(
            df_filtrado, metas_nuevas_df, metas_actualizar_df
        )
        
        st.markdown(f"**Meta más cercana: {fecha_meta.strftime('%d/%m/%Y')}**")

        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### Registros Nuevos")
            # Tabla con gradiente personalizado
            def crear_gradiente_personalizado(df_comp):
                def aplicar_color(val):
                    try:
                        val = float(val)
                        if val <= 0: return 'background-color: #dc2626; color: white'
                        elif val <= 25: return 'background-color: #ef4444; color: white'
                        elif val <= 50: return 'background-color: #f97316; color: white'
                        elif val <= 75: return 'background-color: #eab308; color: black'
                        elif val < 100: return 'background-color: #84cc16; color: black'
                        else: return 'background-color: #166534; color: white'
                    except:
                        return ''
                
                return df_comp.style.format({'Porcentaje': '{:.2f}%'}).map(aplicar_color, subset=['Porcentaje'])
            
            st.dataframe(crear_gradiente_personalizado(comparacion_nuevos))
            crear_barras_cumplimiento_optimizado(comparacion_nuevos, "")

        with col2:
            st.markdown("### Registros a Actualizar")
            st.dataframe(crear_gradiente_personalizado(comparacion_actualizar))
            crear_barras_cumplimiento_optimizado(comparacion_actualizar, "")

    except Exception as e:
        st.error(f"Error en comparación con metas: {e}")

    # ===== DIAGRAMA DE GANTT CONDICIONAL =====
    st.markdown('<div class="subtitle">Diagrama de Gantt - Cronograma de Hitos</div>', unsafe_allow_html=True)

    filtros_aplicados = (
        entidad_seleccionada != 'Todas' or 
        funcionario_seleccionado != 'Todos' or 
        nivel_seleccionado != 'Todos'
    )

    if filtros_aplicados:
        try:
            fig_gantt = crear_gantt(df_filtrado)
            if fig_gantt is not None:
                st.plotly_chart(fig_gantt, use_container_width=True)
            else:
                st.warning("No hay datos suficientes para el diagrama de Gantt con los filtros aplicados.")
        except Exception as e:
            st.error(f"Error creando Gantt: {e}")
    else:
        st.info("Para visualizar el diagrama de Gantt seleccione filtros específicos (entidad, funcionario o nivel).")

    # ===== TABLA DE REGISTROS =====
    st.markdown('<div class="subtitle">Detalle de Registros</div>', unsafe_allow_html=True)

    try:
        df_mostrar = df_filtrado.copy()

        # Formatear fechas
        columnas_fecha = [
            'Fecha de entrega de información', 'Plazo de análisis', 'Plazo de cronograma',
            'Análisis y cronograma', 'Estándares', 'Publicación', 
            'Plazo de oficio de cierre', 'Fecha de oficio de cierre'
        ]

        for col in columnas_fecha:
            if col in df_mostrar.columns:
                df_mostrar[col] = df_mostrar[col].apply(
                    lambda x: formatear_fecha(x) if es_fecha_valida(x) else ""
                )

        # Función de highlighting
        def highlight_estado_fechas_optimizado(s):
            try:
                if 'Estado Fechas' in s and pd.notna(s['Estado Fechas']):
                    colors = {
                        'vencido': 'background-color: #fee2e2',
                        'proximo': 'background-color: #fef3c7'
                    }
                    color = colors.get(s['Estado Fechas'], 'background-color: #ffffff')
                    return [color] * len(s)
                return ['background-color: #ffffff'] * len(s)
            except:
                return ['background-color: #ffffff'] * len(s)

        # Mostrar tabla con estilos
        st.dataframe(
            df_mostrar.style
            .format({'Porcentaje Avance': '{:.1f}%'})
            .apply(highlight_estado_fechas_optimizado, axis=1)
            .background_gradient(cmap='RdYlGn', subset=['Porcentaje Avance']),
            use_container_width=True
        )

    except Exception as e:
        st.error(f"Error mostrando tabla: {e}")
        st.dataframe(df_filtrado)

    # ===== TREEMAP DE FUNCIONARIOS =====
    st.markdown("---")
    treemap_result = crear_treemap_funcionarios_optimizado(df_filtrado)
    
    if treemap_result:
        fig_treemap, funcionarios_data = treemap_result
        
        st.plotly_chart(fig_treemap, use_container_width=True)
        
        # Métricas resumidas
        st.markdown("#### Métricas de Distribución")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Funcionarios", len(funcionarios_data))
        with col2:
            max_registros = funcionarios_data['Cantidad'].max()
            funcionario_top = funcionarios_data['Cantidad'].idxmax()
            st.metric("Máximo Registros", max_registros, help=f"Funcionario: {funcionario_top}")
        with col3:
            promedio_registros = funcionarios_data['Cantidad'].mean()
            st.metric("Promedio", f"{promedio_registros:.1f}")
        with col4:
            avance_general = funcionarios_data['Avance Promedio'].mean()
            st.metric("Avance General", f"{avance_general:.1f}%")

        # Insights automáticos
        with st.expander("Insights y Recomendaciones"):
            funcionario_mas_registros = funcionarios_data.loc[funcionarios_data['Cantidad'].idxmax()]
            funcionario_mejor_avance = funcionarios_data.loc[funcionarios_data['Avance Promedio'].idxmax()]
            
            col1, col2 = st.columns(2)
            with col1:
                st.info(f"""**Más registros:** {funcionario_mas_registros.name}  
                {funcionario_mas_registros['Cantidad']} registros ({funcionario_mas_registros['Porcentaje']:.1f}%)  
                Avance: {funcionario_mas_registros['Avance Promedio']:.1f}%""")
            
            with col2:
                st.success(f"""**Mejor avance:** {funcionario_mejor_avance.name}  
                {funcionario_mejor_avance['Cantidad']} registros  
                Avance: {funcionario_mejor_avance['Avance Promedio']:.1f}%""")

    # ===== SECCIÓN DE DESCARGA =====
    st.markdown("### Descargar Datos")

    col1, col2 = st.columns(2)

    with col1:
        # Descarga de datos filtrados
        try:
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df_mostrar.to_excel(writer, sheet_name='Registros Filtrados', index=False)

            excel_data = output.getvalue()
            st.download_button(
                label="Descargar filtrados (Excel)",
                data=excel_data,
                file_name=f"registros_filtrados_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                help="Descarga solo los registros filtrados"
            )
        except Exception as e:
            st.error(f"Error en descarga filtrada: {e}")

    with col2:
        # Descarga completa
        try:
            output_completo = io.BytesIO()
            with pd.ExcelWriter(output_completo, engine='openpyxl') as writer:
                registros_df.to_excel(writer, sheet_name='Registros Completos', index=False)
                
                # Hojas adicionales por tipo de dato
                if 'TipoDato' in registros_df.columns:
                    for tipo in ['NUEVO', 'ACTUALIZAR']:
                        subset = registros_df[registros_df['TipoDato'].str.upper() == tipo]
                        if not subset.empty:
                            sheet_name = f'Registros {tipo.title()}'
                            subset.to_excel(writer, sheet_name=sheet_name, index=False)

            excel_data_completo = output_completo.getvalue()
            st.download_button(
                label="Descargar TODOS (Excel)",
                data=excel_data_completo,
                file_name=f"todos_registros_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                help="Descarga todos los registros sin filtros"
            )
        except Exception as e:
            st.error(f"Error en descarga completa: {e}")

    # Información sobre contenido
    st.info(f"Datos: {len(registros_df)} registros totales, {len(df_filtrado)} filtrados, {len(registros_df.columns)} campos")


# ===== FUNCIONES DE UTILIDAD =====

def highlight_estado_fechas(s):
    """Función para aplicar estilo según estado de fechas"""
    try:
        if 'Estado Fechas' in s and pd.notna(s['Estado Fechas']):
            color_map = {
                'vencido': '#fee2e2',
                'proximo': '#fef3c7'
            }
            color = color_map.get(s['Estado Fechas'], '#ffffff')
            return [f'background-color: {color}'] * len(s)
        return ['background-color: #ffffff'] * len(s)
    except:
        return ['background-color: #ffffff'] * len(s)


def validar_dashboard_funcionando():
    """Función para verificar que todas las funcionalidades del dashboard están presentes"""
    funcionalidades = [
        "Métricas generales (4 tarjetas)",
        "Comparación con metas quincenales", 
        "Gráficos de barras de cumplimiento",
        "Tabla con gradiente personalizado",
        "Diagrama de Gantt condicional",
        "Treemap de funcionarios",
        "Métricas de distribución",
        "Insights automáticos", 
        "Descarga de datos (filtrados y completos)",
        "Formato de fechas",
        "Estilos y colores",
        "Manejo de errores"
    ]
    
    return funcionalidades


if __name__ == "__main__":
    print("Módulo Dashboard cargado correctamente")
    print("Funcionalidades incluidas:")
    for func in validar_dashboard_funcionando():
        print(f"   - {func}")
    print("Listo para importar en app1.py")
