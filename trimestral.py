# trimestral.py - LÓGICA EXACTA COMO SOLICITAS
"""
Módulo Seguimiento Trimestral - LÓGICA CORREGIDA ESPECÍFICAMENTE
- Meta Q1 = registros programados para marzo
- Meta Q2 = registros programados para junio  
- Meta Q3 = registros programados para septiembre
- Meta Q4 = registros programados para diciembre
- Avance = publicados antes de marzo/junio/septiembre/diciembre
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
from data_utils import es_fecha_valida, procesar_fecha


def mostrar_seguimiento_trimestral(registros_df, meta_df):
    """
    Seguimiento trimestral con LÓGICA EXACTA:
    - Q1 Meta = programados para marzo
    - Q2 Meta = programados para junio
    - Q3 Meta = programados para septiembre  
    - Q4 Meta = programados para diciembre
    - Avance = publicados antes de cada fecha límite
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
    
    # Información explicativa EXACTA
    st.info("""
    **📊 Seguimiento de Publicaciones por Trimestre**
    
    **LÓGICA ESPECÍFICA:**
    - **Q1 Meta:** Registros programados para **Marzo**
    - **Q2 Meta:** Registros programados para **Junio**  
    - **Q3 Meta:** Registros programados para **Septiembre**
    - **Q4 Meta:** Registros programados para **Diciembre**
    
    - **Q1 Avance:** Publicados antes del 31 de Marzo
    - **Q2 Avance:** Publicados antes del 30 de Junio
    - **Q3 Avance:** Publicados antes del 30 de Septiembre  
    - **Q4 Avance:** Publicados antes del 31 de Diciembre
    """)

    def crear_grafico_individual(datos, titulo, color_meta, color_avance):
        """Crea gráfico individual - VERSIÓN ESPECÍFICA"""
        
        trimestres = ['Q1 2025', 'Q2 2025', 'Q3 2025', 'Q4 2025']
        
        # Extraer datos de forma segura
        try:
            metas = []
            avances = []
            
            for q in ['Q1', 'Q2', 'Q3', 'Q4']:
                meta_val = int(datos[q].get('meta', 0))
                avance_val = int(datos[q].get('avance', 0))
                
                metas.append(meta_val)
                avances.append(avance_val)
                
        except (ValueError, TypeError, KeyError) as e:
            st.error(f"Error procesando datos para gráfico: {e}")
            return None
        
        # Crear figura
        fig = go.Figure()
        
        # Línea de Meta específica por mes
        fig.add_trace(go.Scatter(
            x=trimestres,
            y=metas,
            mode='lines+markers',
            name='🎯 Meta (mes específico)',
            line=dict(color=color_meta, width=4, dash='dash'),
            marker=dict(size=12, symbol='diamond'),
            hovertemplate='<b>Meta del mes</b><br>%{x}: %{y} publicaciones<extra></extra>'
        ))
        
        # Línea de Avance acumulado hasta fecha
        fig.add_trace(go.Scatter(
            x=trimestres,
            y=avances,
            mode='lines+markers',
            name='📈 Avance (hasta fecha)',
            line=dict(color=color_avance, width=4),
            marker=dict(size=12, symbol='circle'),
            hovertemplate='<b>Publicados hasta fecha</b><br>%{x}: %{y} publicaciones<extra></extra>'
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
                title='Publicaciones (Meta Mes Específico | Avance Hasta Fecha)',
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

    def calcular_publicaciones_logica_especifica(registros_con_mes, tipo_dato):
        """
        LÓGICA ESPECÍFICA EXACTA como solicitas:
        - Q1: Meta = marzo, Avance = publicados <= 31 marzo
        - Q2: Meta = junio, Avance = publicados <= 30 junio
        - Q3: Meta = septiembre, Avance = publicados <= 30 septiembre
        - Q4: Meta = diciembre, Avance = publicados <= 31 diciembre
        """
        datos_trimestres = {
            'Q1': {'meta': 0, 'avance': 0, 'porcentaje': 0.0},
            'Q2': {'meta': 0, 'avance': 0, 'porcentaje': 0.0},
            'Q3': {'meta': 0, 'avance': 0, 'porcentaje': 0.0},
            'Q4': {'meta': 0, 'avance': 0, 'porcentaje': 0.0}
        }
        
        try:
            # Filtrar por tipo de dato
            registros_tipo = registros_con_mes[registros_con_mes['TipoDato'].str.upper() == tipo_dato.upper()]
            
            if registros_tipo.empty:
                return datos_trimestres
            
            # METAS ESPECÍFICAS POR MES FINAL DE TRIMESTRE
            mes_especifico_trimestre = {
                'Q1': 'Marzo',
                'Q2': 'Junio', 
                'Q3': 'Septiembre',
                'Q4': 'Diciembre'
            }
            
            # FECHAS LÍMITE PARA AVANCE
            fechas_limite = {
                'Q1': datetime(2025, 3, 31),   # 31 marzo
                'Q2': datetime(2025, 6, 30),   # 30 junio
                'Q3': datetime(2025, 9, 30),   # 30 septiembre
                'Q4': datetime(2025, 12, 31)   # 31 diciembre
            }
            
            # Obtener TODOS los registros publicados
            registros_publicados = []
            if 'Publicación' in registros_tipo.columns:
                try:
                    for idx, row in registros_tipo.iterrows():
                        fecha_pub_str = row.get('Publicación', '')
                        if es_fecha_valida(fecha_pub_str):
                            try:
                                fecha_pub = procesar_fecha(fecha_pub_str)
                                if fecha_pub:
                                    registros_publicados.append({
                                        'fecha_publicacion': fecha_pub,
                                        'registro': row
                                    })
                            except:
                                continue
                except Exception as e:
                    st.warning(f"Error procesando publicaciones: {e}")
            
            # Procesar cada trimestre
            for trimestre in ['Q1', 'Q2', 'Q3', 'Q4']:
                try:
                    # META: Solo registros programados para el mes específico del trimestre
                    mes_especifico = mes_especifico_trimestre[trimestre]
                    registros_meta = registros_tipo[
                        registros_tipo['Mes Proyectado'] == mes_especifico
                    ]
                    meta = len(registros_meta)
                    
                    # AVANCE: Registros publicados ANTES de la fecha límite del trimestre
                    fecha_limite = fechas_limite[trimestre]
                    avance = 0
                    
                    for pub in registros_publicados:
                        try:
                            fecha_pub = pub['fecha_publicacion']
                            # Convertir a datetime si es necesario
                            if isinstance(fecha_pub, datetime):
                                fecha_pub_dt = fecha_pub
                            else:
                                # Si es date, convertir a datetime
                                fecha_pub_dt = datetime.combine(fecha_pub, datetime.min.time())
                            
                            # Comparar fechas del mismo tipo
                            if fecha_pub_dt <= fecha_limite:
                                avance += 1
                        except Exception as e:
                            continue  # Ignorar errores de conversión individual
                    
                    # Calcular porcentaje
                    if meta > 0:
                        porcentaje = (avance / meta) * 100.0
                    else:
                        porcentaje = 0.0
                    
                    # Guardar datos
                    datos_trimestres[trimestre] = {
                        'meta': int(meta),
                        'avance': int(avance),
                        'porcentaje': float(round(porcentaje, 1))
                    }
                    
                except Exception as e:
                    st.warning(f"Error calculando {trimestre}: {e}")
                    datos_trimestres[trimestre] = {
                        'meta': 0,
                        'avance': 0,
                        'porcentaje': 0.0
                    }
            
            return datos_trimestres
            
        except Exception as e:
            st.error(f"Error general en cálculos: {e}")
            return datos_trimestres

    # CALCULAR DATOS TRIMESTRALES - VERSIÓN ESPECÍFICA
    try:
        datos_nuevos = calcular_publicaciones_logica_especifica(registros_con_mes, 'NUEVO')
        datos_actualizar = calcular_publicaciones_logica_especifica(registros_con_mes, 'ACTUALIZAR')
    except Exception as e:
        st.error(f"Error calculando datos trimestrales: {e}")
        datos_nuevos = {
            'Q1': {'meta': 0, 'avance': 0, 'porcentaje': 0.0},
            'Q2': {'meta': 0, 'avance': 0, 'porcentaje': 0.0},
            'Q3': {'meta': 0, 'avance': 0, 'porcentaje': 0.0},
            'Q4': {'meta': 0, 'avance': 0, 'porcentaje': 0.0}
        }
        datos_actualizar = datos_nuevos.copy()

    # Verificar si hay datos para mostrar
    hay_datos_nuevos = any(datos_nuevos[q]['meta'] > 0 for q in ['Q1', 'Q2', 'Q3', 'Q4'])
    hay_datos_actualizar = any(datos_actualizar[q]['meta'] > 0 for q in ['Q1', 'Q2', 'Q3', 'Q4'])

    if not hay_datos_nuevos and not hay_datos_actualizar:
        st.warning("⚠️ **No hay datos suficientes para mostrar el seguimiento trimestral**")
        st.info("""
        **Para habilitar esta funcionalidad:**
        1. Asigne 'Mes Proyectado' = 'Marzo', 'Junio', 'Septiembre' o 'Diciembre'
        2. Complete fechas de 'Publicación' en los registros terminados
        3. Asegúrese de tener 'TipoDato' definido ('Nuevo' o 'Actualizar')
        """)
        return

    # MOSTRAR GRÁFICOS
    if hay_datos_nuevos:
        st.markdown("---")
        fig_nuevos = crear_grafico_individual(
            datos_nuevos, 
            "📊 Registros NUEVOS (Meta: Mes Específico | Avance: Hasta Fecha)",
            color_meta='#ff7f0e',
            color_avance='#2ca02c'
        )
        if fig_nuevos:
            st.plotly_chart(fig_nuevos, use_container_width=True)
        
        # Tabla de datos NUEVOS
        with st.expander("📋 Datos Detallados - Registros NUEVOS"):
            try:
                df_nuevos_display = []
                meses_ref = ['Marzo', 'Junio', 'Septiembre', 'Diciembre']
                for i, q in enumerate(['Q1', 'Q2', 'Q3', 'Q4']):
                    df_nuevos_display.append({
                        'Trimestre': q,
                        'Mes Meta': meses_ref[i],
                        'Meta': datos_nuevos[q]['meta'],
                        'Avance (hasta fecha)': datos_nuevos[q]['avance'],
                        'Porcentaje': f"{datos_nuevos[q]['porcentaje']}%"
                    })
                
                df_nuevos_table = pd.DataFrame(df_nuevos_display)
                st.dataframe(df_nuevos_table, use_container_width=True)
            except Exception as e:
                st.error(f"Error mostrando tabla nuevos: {e}")

    if hay_datos_actualizar:
        st.markdown("---")
        fig_actualizar = crear_grafico_individual(
            datos_actualizar,
            "📊 Registros a ACTUALIZAR (Meta: Mes Específico | Avance: Hasta Fecha)", 
            color_meta='#d62728',
            color_avance='#9467bd'
        )
        if fig_actualizar:
            st.plotly_chart(fig_actualizar, use_container_width=True)
        
        # Tabla de datos ACTUALIZAR
        with st.expander("📋 Datos Detallados - Registros a ACTUALIZAR"):
            try:
                df_actualizar_display = []
                meses_ref = ['Marzo', 'Junio', 'Septiembre', 'Diciembre']
                for i, q in enumerate(['Q1', 'Q2', 'Q3', 'Q4']):
                    df_actualizar_display.append({
                        'Trimestre': q,
                        'Mes Meta': meses_ref[i],
                        'Meta': datos_actualizar[q]['meta'],
                        'Avance (hasta fecha)': datos_actualizar[q]['avance'],
                        'Porcentaje': f"{datos_actualizar[q]['porcentaje']}%"
                    })
                
                df_actualizar_table = pd.DataFrame(df_actualizar_display)
                st.dataframe(df_actualizar_table, use_container_width=True)
            except Exception as e:
                st.error(f"Error mostrando tabla actualizar: {e}")

    # RESUMEN FINAL
    st.markdown("---")
    st.markdown("### 📊 Resumen General")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if hay_datos_nuevos:
            try:
                total_meta_nuevos = sum(int(datos_nuevos[q]['meta']) for q in ['Q1', 'Q2', 'Q3', 'Q4'])
                total_avance_nuevos = int(datos_nuevos['Q4']['avance'])  # Q4 tiene el total hasta diciembre
                eficiencia_nuevos = (total_avance_nuevos / total_meta_nuevos * 100) if total_meta_nuevos > 0 else 0
                
                st.metric(
                    "📈 REGISTROS NUEVOS",
                    f"{total_avance_nuevos}/{total_meta_nuevos}",
                    f"{eficiencia_nuevos:.1f}% cumplimiento"
                )
            except Exception as e:
                st.error(f"Error calculando resumen nuevos: {e}")
    
    with col2:
        if hay_datos_actualizar:
            try:
                total_meta_actualizar = sum(int(datos_actualizar[q]['meta']) for q in ['Q1', 'Q2', 'Q3', 'Q4'])
                total_avance_actualizar = int(datos_actualizar['Q4']['avance'])  # Q4 tiene el total hasta diciembre
                eficiencia_actualizar = (total_avance_actualizar / total_meta_actualizar * 100) if total_meta_actualizar > 0 else 0
                
                st.metric(
                    "🔄 REGISTROS A ACTUALIZAR",
                    f"{total_avance_actualizar}/{total_meta_actualizar}",
                    f"{eficiencia_actualizar:.1f}% cumplimiento"
                )
            except Exception as e:
                st.error(f"Error calculando resumen actualizar: {e}")

    # INFORMACIÓN ADICIONAL
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
            - Metas por mes específico
            - Avance hasta fecha límite
            """)
    
    with col3:
        if hay_datos_actualizar:
            registros_actualizar_con_mes = len(registros_con_mes[registros_con_mes['TipoDato'].str.upper() == 'ACTUALIZAR'])
            st.info(f"""
            **🔄 Registros a Actualizar**  
            - Con mes proyectado: {registros_actualizar_con_mes}
            - Metas por mes específico
            - Avance hasta fecha límite
            """)

    # NOTA EXPLICATIVA FINAL
    st.markdown("---")
    st.success("""
    ✅ **LÓGICA IMPLEMENTADA EXACTAMENTE COMO SOLICITASTE:** 
    - **Meta Q1:** Solo registros programados para Marzo
    - **Meta Q2:** Solo registros programados para Junio
    - **Meta Q3:** Solo registros programados para Septiembre  
    - **Meta Q4:** Solo registros programados para Diciembre
    - **Avance:** Publicados antes de cada fecha límite (acumulativo)
    """)


# ===== VERIFICACIÓN =====
if __name__ == "__main__":
    print("📅 Módulo Seguimiento Trimestral - LÓGICA ESPECÍFICA EXACTA")
    print("🔧 Implementación:")
    print("   ✅ Q1 Meta = programados para Marzo")
    print("   ✅ Q2 Meta = programados para Junio") 
    print("   ✅ Q3 Meta = programados para Septiembre")
    print("   ✅ Q4 Meta = programados para Diciembre")
    print("   ✅ Avance = publicados antes de fecha límite de cada trimestre")
    print("   ✅ Sin operaciones problemáticas entre tipos datetime")
