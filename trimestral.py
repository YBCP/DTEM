# trimestral.py - VERSIÓN CORREGIDA
"""
Módulo Seguimiento Trimestral - ERRORES CORREGIDOS
- Fix: Error de tipos (int + datetime.date)
- Fix: Metas NO acumuladas (individuales por trimestre)
- Lógica de cálculo mejorada
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
from data_utils import es_fecha_valida, procesar_fecha


def mostrar_seguimiento_trimestral(registros_df, meta_df):
    """
    Seguimiento trimestral CORREGIDO - Sin errores de tipos y metas NO acumuladas
    """
    st.markdown('<div class="subtitle">Seguimiento Trimestral - Publicaciones: Meta vs Avance Real</div>', unsafe_allow_html=True)
    
    # Verificar disponibilidad de la columna Mes Proyectado
    if 'Mes Proyectado' not in registros_df.columns:
        st.error("❌ La columna 'Mes Proyectado' no está disponible en los datos")
        st.info("📋 Verifique que la hoja de Google Sheets tenga la columna 'Mes Proyectado'")
        return
    
    # Filtrado de registros con Mes Proyectado válido
    registros_con_mes = registros_df[
        (registros_df['Mes Proyectado'].notna()) & 
        (registros_df['Mes Proyectado'].astype(str).str.strip() != '') &
        (~registros_df['Mes Proyectado'].astype(str).str.strip().isin(['nan', 'None', 'NaN']))
    ]
    
    if registros_con_mes.empty:
        st.warning("⚠️ No hay registros con 'Mes Proyectado' válido")
        st.info("📝 Para usar el seguimiento trimestral, asigne un mes proyectado a los registros en la sección de Edición")
        return
    
    # Información explicativa CORREGIDA
    st.info("""
    **📊 Seguimiento de Publicaciones por Trimestre**
    
    Este dashboard muestra el avance de **publicaciones reales** versus las **metas individuales** para cada trimestre:
    - **Meta:** Número de registros programados PARA CADA trimestre (NO acumulado)
    - **Avance:** Número de registros con fecha real de publicación completada PARA CADA trimestre (NO acumulado)
    - **Porcentaje:** (Publicaciones del trimestre / Meta del trimestre) × 100
    """)

    def crear_grafico_individual(datos, titulo, color_meta, color_avance):
        """Crea gráfico individual para un tipo de registro - VERSIÓN CORREGIDA"""
        
        trimestres = ['Q1 2025', 'Q2 2025', 'Q3 2025', 'Q4 2025']
        
        # Extraer datos - CORREGIDO: Usar datos NO acumulados
        metas = [datos[q]['meta_trimestre'] for q in ['Q1', 'Q2', 'Q3', 'Q4']]
        avance = [datos[q]['avance_trimestre'] for q in ['Q1', 'Q2', 'Q3', 'Q4']]
        
        # Crear figura
        fig = go.Figure()
        
        # Línea de Meta - POR TRIMESTRE
        fig.add_trace(go.Scatter(
            x=trimestres,
            y=metas,
            mode='lines+markers',
            name='🎯 Meta (por trimestre)',
            line=dict(color=color_meta, width=4, dash='dash'),
            marker=dict(size=12, symbol='diamond'),
            hovertemplate='<b>Meta del trimestre</b><br>%{x}: %{y} publicaciones<extra></extra>'
        ))
        
        # Línea de Avance - POR TRIMESTRE
        fig.add_trace(go.Scatter(
            x=trimestres,
            y=avance,
            mode='lines+markers',
            name='📈 Avance Real (por trimestre)',
            line=dict(color=color_avance, width=4),
            marker=dict(size=12, symbol='circle'),
            hovertemplate='<b>Avance del trimestre</b><br>%{x}: %{y} publicaciones<extra></extra>'
        ))
        
        # Configuración del gráfico
        fig.update_layout(
            title={
                'text': titulo,
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 18, 'color': '#2c3e50'}
            },
            xaxis=dict(
                title='Trimestre',
                showgrid=True,
                gridcolor='lightgray'
            ),
            yaxis=dict(
                title='Número de Publicaciones (Por Trimestre)',  # CORREGIDO
                showgrid=True,
                gridcolor='lightgray'
            ),
            plot_bgcolor='white',
            paper_bgcolor='white',
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01,
                bgcolor="rgba(255,255,255,0.8)"
            ),
            height=500,
            margin=dict(t=80, l=60, r=60, b=60)
        )
        
        return fig

    def crear_datos_trimestre_vacio():
        """Crea estructura de datos vacía para trimestres - CORREGIDA"""
        return {
            'Q1': {'meta_trimestre': 0, 'avance_trimestre': 0, 'porcentaje': 0},
            'Q2': {'meta_trimestre': 0, 'avance_trimestre': 0, 'porcentaje': 0},
            'Q3': {'meta_trimestre': 0, 'avance_trimestre': 0, 'porcentaje': 0},
            'Q4': {'meta_trimestre': 0, 'avance_trimestre': 0, 'porcentaje': 0}
        }

    def calcular_publicaciones_trimestrales_corregido(registros_con_mes, tipo_dato):
        """
        VERSIÓN CORREGIDA - Calcula publicaciones por trimestre individual (NO acumulado)
        Fix: Error de tipos y lógica de acumulación
        """
        datos_trimestres = crear_datos_trimestre_vacio()
        
        # Filtrar por tipo de dato
        registros_tipo = registros_con_mes[registros_con_mes['TipoDato'].str.upper() == tipo_dato.upper()]
        
        if registros_tipo.empty:
            return datos_trimestres
        
        # Mapeo de meses a trimestres
        meses_trimestre = {
            'Q1': ['Enero', 'Febrero', 'Marzo'],
            'Q2': ['Abril', 'Mayo', 'Junio'], 
            'Q3': ['Julio', 'Agosto', 'Septiembre'],
            'Q4': ['Octubre', 'Noviembre', 'Diciembre']
        }
        
        # Trimestres ordenados
        trimestres = ['Q1', 'Q2', 'Q3', 'Q4']
        
        # NUEVA LÓGICA: Calcular SOLO para cada trimestre individual
        for trimestre in trimestres:
            try:
                # CORREGIDO: Solo meses de ESTE trimestre (no acumulado)
                meses_este_trimestre = meses_trimestre[trimestre]
                
                # META: registros programados SOLO para este trimestre
                registros_programados_trimestre = registros_tipo[
                    registros_tipo['Mes Proyectado'].isin(meses_este_trimestre)
                ]
                meta_este_trimestre = len(registros_programados_trimestre)
                
                # AVANCE: registros PUBLICADOS que estaban programados para este trimestre
                if 'Publicación' in registros_tipo.columns:
                    try:
                        # CORREGIDO: Solo los que tienen publicación Y estaban programados para este trimestre
                        publicaciones_este_trimestre = registros_programados_trimestre[
                            registros_programados_trimestre['Publicación'].apply(es_fecha_valida)
                        ]
                        avance_este_trimestre = len(publicaciones_este_trimestre)
                            
                    except Exception as e:
                        st.warning(f"Error procesando publicaciones en {trimestre}: {e}")
                        avance_este_trimestre = 0
                else:
                    avance_este_trimestre = 0
                
                # Calcular porcentaje SOLO para este trimestre
                porcentaje = (avance_este_trimestre / meta_este_trimestre * 100) if meta_este_trimestre > 0 else 0
                
                # CORREGIDO: Guardar datos NO acumulados
                datos_trimestres[trimestre] = {
                    'meta_trimestre': meta_este_trimestre,
                    'avance_trimestre': avance_este_trimestre,
                    'porcentaje': round(porcentaje, 1)
                }
                
            except Exception as e:
                st.warning(f"Error calculando {trimestre}: {e}")
                datos_trimestres[trimestre] = {
                    'meta_trimestre': 0, 'avance_trimestre': 0, 'porcentaje': 0
                }
        
        return datos_trimestres

    # CALCULAR DATOS TRIMESTRALES - VERSIÓN CORREGIDA
    try:
        datos_nuevos = calcular_publicaciones_trimestrales_corregido(registros_con_mes, 'NUEVO')
        datos_actualizar = calcular_publicaciones_trimestrales_corregido(registros_con_mes, 'ACTUALIZAR')
    except Exception as e:
        st.error(f"Error calculando datos trimestrales: {e}")
        datos_nuevos = crear_datos_trimestre_vacio()
        datos_actualizar = crear_datos_trimestre_vacio()

    # Verificar si hay datos para mostrar
    hay_datos_nuevos = any(datos_nuevos[q]['meta_trimestre'] > 0 for q in ['Q1', 'Q2', 'Q3', 'Q4'])
    hay_datos_actualizar = any(datos_actualizar[q]['meta_trimestre'] > 0 for q in ['Q1', 'Q2', 'Q3', 'Q4'])

    if not hay_datos_nuevos and not hay_datos_actualizar:
        st.warning("⚠️ **No hay datos suficientes para mostrar el seguimiento trimestral**")
        st.info("""
        **Para habilitar esta funcionalidad:**
        1. Asegúrese de tener registros con 'TipoDato' definido ('Nuevo' o 'Actualizar')
        2. Asigne 'Mes Proyectado' a los registros
        3. Complete fechas de 'Publicación' en los registros terminados
        """)
        return

    # MOSTRAR GRÁFICOS - VERSIÓN CORREGIDA
    if hay_datos_nuevos:
        st.markdown("---")
        fig_nuevos = crear_grafico_individual(
            datos_nuevos, 
            "📊 Seguimiento Trimestral - Registros NUEVOS (Por Trimestre)",
            color_meta='#ff7f0e',
            color_avance='#2ca02c'
        )
        st.plotly_chart(fig_nuevos, use_container_width=True)
        
        # Tabla de datos NUEVOS - CORREGIDA
        with st.expander("📋 Datos Detallados - Registros NUEVOS"):
            df_nuevos = pd.DataFrame.from_dict(datos_nuevos, orient='index')
            df_nuevos.index.name = 'Trimestre'
            df_nuevos.columns = ['Meta (Trimestre)', 'Avance (Trimestre)', 'Porcentaje']
            df_nuevos['Porcentaje'] = df_nuevos['Porcentaje'].apply(lambda x: f"{x}%")
            st.dataframe(df_nuevos, use_container_width=True)

    if hay_datos_actualizar:
        st.markdown("---")
        fig_actualizar = crear_grafico_individual(
            datos_actualizar,
            "📊 Seguimiento Trimestral - Registros a ACTUALIZAR (Por Trimestre)", 
            color_meta='#d62728',
            color_avance='#9467bd'
        )
        st.plotly_chart(fig_actualizar, use_container_width=True)
        
        # Tabla de datos ACTUALIZAR - CORREGIDA
        with st.expander("📋 Datos Detallados - Registros a ACTUALIZAR"):
            df_actualizar = pd.DataFrame.from_dict(datos_actualizar, orient='index')
            df_actualizar.index.name = 'Trimestre'
            df_actualizar.columns = ['Meta (Trimestre)', 'Avance (Trimestre)', 'Porcentaje']
            df_actualizar['Porcentaje'] = df_actualizar['Porcentaje'].apply(lambda x: f"{x}%")
            st.dataframe(df_actualizar, use_container_width=True)

    # RESUMEN FINAL - VERSIÓN CORREGIDA
    st.markdown("---")
    st.markdown("### 📊 Resumen General (Totales)")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if hay_datos_nuevos:
            # CORREGIDO: Sumar por trimestres individuales
            total_meta_nuevos = sum(datos_nuevos[q]['meta_trimestre'] for q in ['Q1', 'Q2', 'Q3', 'Q4'])
            total_avance_nuevos = sum(datos_nuevos[q]['avance_trimestre'] for q in ['Q1', 'Q2', 'Q3', 'Q4'])
            eficiencia_nuevos = (total_avance_nuevos / total_meta_nuevos * 100) if total_meta_nuevos > 0 else 0
            
            st.metric(
                "📈 REGISTROS NUEVOS (Total Anual)",
                f"{total_avance_nuevos}/{total_meta_nuevos}",
                f"{eficiencia_nuevos:.1f}% cumplimiento"
            )
    
    with col2:
        if hay_datos_actualizar:
            # CORREGIDO: Sumar por trimestres individuales
            total_meta_actualizar = sum(datos_actualizar[q]['meta_trimestre'] for q in ['Q1', 'Q2', 'Q3', 'Q4'])
            total_avance_actualizar = sum(datos_actualizar[q]['avance_trimestre'] for q in ['Q1', 'Q2', 'Q3', 'Q4'])
            eficiencia_actualizar = (total_avance_actualizar / total_meta_actualizar * 100) if total_meta_actualizar > 0 else 0
            
            st.metric(
                "🔄 REGISTROS A ACTUALIZAR (Total Anual)",
                f"{total_avance_actualizar}/{total_meta_actualizar}",
                f"{eficiencia_actualizar:.1f}% cumplimiento"
            )

    # INFORMACIÓN ADICIONAL - VERSIÓN CORREGIDA
    st.markdown("---")
    st.markdown("### ℹ️ Información del Análisis")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        registros_validos = len(registros_con_mes)
        total_registros = len(registros_df)
        st.info(f"""
        **📊 Datos del Análisis**
        - Registros con mes: {registros_validos}
        - Total registros: {total_registros}
        - Cobertura: {(registros_validos/total_registros*100):.1f}%
        """)
    
    with col2:
        if hay_datos_nuevos:
            registros_nuevos_con_mes = len(registros_con_mes[registros_con_mes['TipoDato'].str.upper() == 'NUEVO'])
            st.info(f"""
            **🆕 Registros Nuevos**
            - Con mes proyectado: {registros_nuevos_con_mes}
            - Meta anual: {total_meta_nuevos if hay_datos_nuevos else 0}
            - Publicados: {total_avance_nuevos if hay_datos_nuevos else 0}
            """)
    
    with col3:
        if hay_datos_actualizar:
            registros_actualizar_con_mes = len(registros_con_mes[registros_con_mes['TipoDato'].str.upper() == 'ACTUALIZAR'])
            st.info(f"""
            **🔄 Registros a Actualizar**
            - Con mes proyectado: {registros_actualizar_con_mes}
            - Meta anual: {total_meta_actualizar if hay_datos_actualizar else 0}
            - Publicados: {total_avance_actualizar if hay_datos_actualizar else 0}
            """)

    # NOTA INFORMATIVA ADICIONAL
    st.markdown("---")
    st.success("""
    ✅ **CORRECCIÓN APLICADA:** 
    - Metas y avances se muestran POR TRIMESTRE individual (no acumulado)
    - Error de tipos datetime.date corregido
    - Lógica de cálculo optimizada
    """)


# ===== VERIFICACIÓN DE CORRECCIÓN =====
if __name__ == "__main__":
    print("📅 Módulo Seguimiento Trimestral CORREGIDO cargado correctamente")
    print("🔧 Correcciones aplicadas:")
    print("   ✅ Error de tipos (int + datetime.date) solucionado")
    print("   ✅ Metas NO acumuladas (individuales por trimestre)")
    print("   ✅ Lógica de cálculo mejorada")
    print("   ✅ Visualización corregida")
    print("\n📝 Uso: from trimestral import mostrar_seguimiento_trimestral")
    print("🔄 Reemplaza el trimestral.py actual")
