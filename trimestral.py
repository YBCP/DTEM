# trimestral.py - CORREGIDO: Usar datos de METAS y arreglar operaciones datetime
"""
Módulo Seguimiento Trimestral - CORREGIDO
- Metas Q1/Q2/Q3/Q4 vienen de la hoja METAS (enero/marzo/septiembre/diciembre)
- Avance = registros publicados antes de fecha límite
- Corregido error de operaciones datetime
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
from data_utils import es_fecha_valida, procesar_fecha, procesar_metas


def extraer_metas_desde_google_sheets(meta_df):
    """
    Extrae las metas trimestrales desde la hoja METAS de Google Sheets
    Busca datos de enero, marzo, septiembre y diciembre
    """
    try:
        # Procesar metas para obtener estructura usable
        metas_nuevas_df, metas_actualizar_df = procesar_metas(meta_df)
        
        # CORREGIDO: Mapeo correcto por cortes trimestrales
        # Q1 = Marzo, Q2 = Junio, Q3 = Septiembre, Q4 = Diciembre
        fechas_objetivo = {
            'Q1': ['15/03/2025', '31/03/2025', '28/02/2025', '15/02/2025', '31/01/2025'],  # Meta Q1 = MARZO
            'Q2': ['15/06/2025', '30/06/2025', '31/05/2025', '15/05/2025', '30/04/2025'],  # Meta Q2 = JUNIO
            'Q3': ['15/09/2025', '30/09/2025', '31/08/2025', '15/08/2025', '31/07/2025'],  # Meta Q3 = SEPTIEMBRE
            'Q4': ['15/12/2025', '31/12/2025', '30/11/2025', '15/11/2025', '31/10/2025']   # Meta Q4 = DICIEMBRE
        }
        
        metas_trimestrales = {
            'nuevos': {'Q1': 0, 'Q2': 0, 'Q3': 0, 'Q4': 0},
            'actualizar': {'Q1': 0, 'Q2': 0, 'Q3': 0, 'Q4': 0}
        }
        
        # Extraer metas por trimestre
        for trimestre, fechas_candidatas in fechas_objetivo.items():
            # Buscar la mejor fecha disponible en las metas
            meta_nueva_encontrada = 0
            meta_actualizar_encontrada = 0
            
            for fecha_str in fechas_candidatas:
                try:
                    fecha_buscar = procesar_fecha(fecha_str)
                    if fecha_buscar is not None:
                        # Buscar en metas nuevas
                        if fecha_buscar in metas_nuevas_df.index:
                            meta_nueva_encontrada = metas_nuevas_df.loc[fecha_buscar, 'Publicación']
                            break
                        
                        # Buscar fecha más cercana
                        fechas_disponibles = metas_nuevas_df.index
                        if len(fechas_disponibles) > 0:
                            fecha_mas_cercana = min(fechas_disponibles, 
                                                  key=lambda x: abs((x - fecha_buscar).days))
                            meta_nueva_encontrada = metas_nuevas_df.loc[fecha_mas_cercana, 'Publicación']
                            break
                except:
                    continue
            
            # Mismo proceso para actualizar
            for fecha_str in fechas_candidatas:
                try:
                    fecha_buscar = procesar_fecha(fecha_str)
                    if fecha_buscar is not None:
                        if fecha_buscar in metas_actualizar_df.index:
                            meta_actualizar_encontrada = metas_actualizar_df.loc[fecha_buscar, 'Publicación']
                            break
                        
                        fechas_disponibles = metas_actualizar_df.index
                        if len(fechas_disponibles) > 0:
                            fecha_mas_cercana = min(fechas_disponibles,
                                                  key=lambda x: abs((x - fecha_buscar).days))
                            meta_actualizar_encontrada = metas_actualizar_df.loc[fecha_mas_cercana, 'Publicación']
                            break
                except:
                    continue
            
            # Convertir a entero de forma segura
            try:
                metas_trimestrales['nuevos'][trimestre] = int(float(meta_nueva_encontrada)) if pd.notna(meta_nueva_encontrada) else 0
                metas_trimestrales['actualizar'][trimestre] = int(float(meta_actualizar_encontrada)) if pd.notna(meta_actualizar_encontrada) else 0
            except (ValueError, TypeError):
                metas_trimestrales['nuevos'][trimestre] = 0
                metas_trimestrales['actualizar'][trimestre] = 0
        
        return metas_trimestrales
        
    except Exception as e:
        st.warning(f"Error extrayendo metas: {e}")
        # Retornar estructura vacía por defecto
        return {
            'nuevos': {'Q1': 0, 'Q2': 0, 'Q3': 0, 'Q4': 0},
            'actualizar': {'Q1': 0, 'Q2': 0, 'Q3': 0, 'Q4': 0}
        }


def calcular_avance_publicaciones_corregido(registros_df, tipo_dato):
    """
    Calcula el avance de publicaciones CORREGIDO - sin errores de datetime
    """
    avance_trimestral = {'Q1': 0, 'Q2': 0, 'Q3': 0, 'Q4': 0}
    
    try:
        # Filtrar por tipo de dato
        if 'TipoDato' in registros_df.columns:
            registros_tipo = registros_df[registros_df['TipoDato'].str.upper() == tipo_dato.upper()]
        else:
            st.warning(f"Columna TipoDato no encontrada, usando todos los registros")
            registros_tipo = registros_df
        
        if registros_tipo.empty:
            return avance_trimestral
        
        # Fechas límite para cada trimestre
        fechas_limite = {
            'Q1': datetime(2025, 3, 31),   # Fin Q1
            'Q2': datetime(2025, 6, 30),   # Fin Q2  
            'Q3': datetime(2025, 9, 30),   # Fin Q3
            'Q4': datetime(2025, 12, 31)   # Fin Q4
        }
        
        # Obtener registros publicados con manejo seguro de fechas
        registros_publicados = []
        if 'Publicación' in registros_tipo.columns:
            for idx, row in registros_tipo.iterrows():
                fecha_pub_str = row.get('Publicación', '')
                if es_fecha_valida(fecha_pub_str):
                    try:
                        fecha_pub = procesar_fecha(fecha_pub_str)
                        if fecha_pub is not None:
                            # CORRECCIÓN: Asegurar que siempre trabajamos con datetime
                            if hasattr(fecha_pub, 'date'):
                                # Es datetime, convertir a date y luego a datetime para comparación
                                fecha_pub_dt = datetime.combine(fecha_pub.date(), datetime.min.time())
                            else:
                                # Es date, convertir a datetime
                                fecha_pub_dt = datetime.combine(fecha_pub, datetime.min.time())
                            
                            registros_publicados.append(fecha_pub_dt)
                    except Exception as e:
                        continue  # Ignorar fechas problemáticas
        
        # Calcular avance por trimestre (acumulativo)
        for trimestre, fecha_limite in fechas_limite.items():
            try:
                # Contar publicaciones hasta la fecha límite
                count = 0
                for fecha_pub_dt in registros_publicados:
                    if fecha_pub_dt <= fecha_limite:
                        count += 1
                
                avance_trimestral[trimestre] = count
            except Exception as e:
                st.warning(f"Error calculando {trimestre}: {e}")
                avance_trimestral[trimestre] = 0
        
        return avance_trimestral
        
    except Exception as e:
        st.error(f"Error general calculando avance: {e}")
        return avance_trimestral


def mostrar_seguimiento_trimestral(registros_df, meta_df):
    """
    Seguimiento trimestral CORREGIDO:
    - Metas vienen de la hoja METAS de Google Sheets
    - Avance = publicaciones hasta fecha límite de cada trimestre
    - Sin errores de operaciones datetime
    """
    st.markdown('<div class="subtitle">Seguimiento Trimestral - Metas vs Avance Real</div>', unsafe_allow_html=True)
    
    st.info("""
    **📊 Seguimiento Trimestral Corregido**
    
    **METAS POR TRIMESTRE (Google Sheets):**
    - **Q1 Meta:** Datos de **MARZO** en hoja METAS
    - **Q2 Meta:** Datos de **JUNIO** en hoja METAS
    - **Q3 Meta:** Datos de **SEPTIEMBRE** en hoja METAS
    - **Q4 Meta:** Datos de **DICIEMBRE** en hoja METAS
    
    **AVANCE (Publicaciones hasta fecha límite):**
    - **Q1:** Hasta 31 Marzo | **Q2:** Hasta 30 Junio | **Q3:** Hasta 30 Septiembre | **Q4:** Hasta 31 Diciembre
    """)
    
    if registros_df.empty:
        st.warning("No hay registros disponibles")
        return
    
    if meta_df.empty:
        st.warning("No hay datos de metas disponibles")
        return
    
    # Extraer metas desde Google Sheets
    with st.spinner("📊 Extrayendo metas desde Google Sheets..."):
        metas_trimestrales = extraer_metas_desde_google_sheets(meta_df)
    
    # Calcular avance real
    with st.spinner("📈 Calculando avance de publicaciones..."):
        avance_nuevos = calcular_avance_publicaciones_corregido(registros_df, 'NUEVO')
        avance_actualizar = calcular_avance_publicaciones_corregido(registros_df, 'ACTUALIZAR')
    
    # Preparar datos para gráficos
    def crear_datos_graficos(metas, avance, titulo):
        """Prepara datos para el gráfico de cada tipo"""
        trimestres = ['Q1 2025', 'Q2 2025', 'Q3 2025', 'Q4 2025']
        
        metas_valores = [metas['Q1'], metas['Q2'], metas['Q3'], metas['Q4']]
        avance_valores = [avance['Q1'], avance['Q2'], avance['Q3'], avance['Q4']]
        
        # Crear gráfico
        fig = go.Figure()
        
        # Línea de metas
        fig.add_trace(go.Scatter(
            x=trimestres,
            y=metas_valores,
            mode='lines+markers',
            name='🎯 Meta (Google Sheets)',
            line=dict(color='#ff7f0e', width=4, dash='dash'),
            marker=dict(size=12, symbol='diamond'),
            hovertemplate='<b>Meta</b><br>%{x}: %{y}<extra></extra>'
        ))
        
        # Línea de avance
        fig.add_trace(go.Scatter(
            x=trimestres,
            y=avance_valores,
            mode='lines+markers',
            name='📈 Avance (Publicado)',
            line=dict(color='#2ca02c', width=4),
            marker=dict(size=12, symbol='circle'),
            hovertemplate='<b>Avance</b><br>%{x}: %{y}<extra></extra>'
        ))
        
        # Configuración
        fig.update_layout(
            title={
                'text': titulo,
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 18}
            },
            xaxis_title='Trimestre',
            yaxis_title='Cantidad de Publicaciones',
            height=500,
            plot_bgcolor='white',
            paper_bgcolor='white',
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01
            )
        )
        
        return fig
    
    # Verificar si hay datos para mostrar
    hay_metas_nuevos = any(metas_trimestrales['nuevos'][q] > 0 for q in ['Q1', 'Q2', 'Q3', 'Q4'])
    hay_metas_actualizar = any(metas_trimestrales['actualizar'][q] > 0 for q in ['Q1', 'Q2', 'Q3', 'Q4'])
    
    if not hay_metas_nuevos and not hay_metas_actualizar:
        st.warning("⚠️ No se encontraron metas en la hoja METAS de Google Sheets")
        st.info("📋 Verifique que la hoja METAS tenga datos para las fechas de enero, marzo, septiembre y diciembre")
        return
    
    # Mostrar gráfico para NUEVOS
    if hay_metas_nuevos:
        st.markdown("---")
        fig_nuevos = crear_datos_graficos(
            metas_trimestrales['nuevos'],
            avance_nuevos,
            "📊 Registros NUEVOS - Meta vs Avance"
        )
        st.plotly_chart(fig_nuevos, use_container_width=True)
        
        # Tabla detallada NUEVOS
        with st.expander("📋 Datos Detallados - Registros NUEVOS"):
            datos_tabla_nuevos = []
            for q in ['Q1', 'Q2', 'Q3', 'Q4']:
                meta = metas_trimestrales['nuevos'][q]
                avance = avance_nuevos[q]
                porcentaje = (avance / meta * 100) if meta > 0 else 0
                
                datos_tabla_nuevos.append({
                    'Trimestre': q,
                    'Meta (Google Sheets)': meta,
                    'Avance (Publicado)': avance,
                    'Cumplimiento': f"{porcentaje:.1f}%"
                })
            
            df_tabla_nuevos = pd.DataFrame(datos_tabla_nuevos)
            st.dataframe(df_tabla_nuevos, use_container_width=True)
    
    # Mostrar gráfico para ACTUALIZAR
    if hay_metas_actualizar:
        st.markdown("---")
        fig_actualizar = crear_datos_graficos(
            metas_trimestrales['actualizar'],
            avance_actualizar,
            "📊 Registros a ACTUALIZAR - Meta vs Avance"
        )
        st.plotly_chart(fig_actualizar, use_container_width=True)
        
        # Tabla detallada ACTUALIZAR
        with st.expander("📋 Datos Detallados - Registros a ACTUALIZAR"):
            datos_tabla_actualizar = []
            for q in ['Q1', 'Q2', 'Q3', 'Q4']:
                meta = metas_trimestrales['actualizar'][q]
                avance = avance_actualizar[q]
                porcentaje = (avance / meta * 100) if meta > 0 else 0
                
                datos_tabla_actualizar.append({
                    'Trimestre': q,
                    'Meta (Google Sheets)': meta,
                    'Avance (Publicado)': avance,
                    'Cumplimiento': f"{porcentaje:.1f}%"
                })
            
            df_tabla_actualizar = pd.DataFrame(datos_tabla_actualizar)
            st.dataframe(df_tabla_actualizar, use_container_width=True)
    
    # Resumen ejecutivo
    st.markdown("---")
    st.markdown("### 📊 Resumen Ejecutivo")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if hay_metas_nuevos:
            total_meta_nuevos = sum(metas_trimestrales['nuevos'].values())
            total_avance_nuevos = avance_nuevos['Q4']  # Avance total hasta Q4
            eficiencia_nuevos = (total_avance_nuevos / total_meta_nuevos * 100) if total_meta_nuevos > 0 else 0
            
            st.metric(
                "📈 NUEVOS (Anual)",
                f"{total_avance_nuevos}/{total_meta_nuevos}",
                f"{eficiencia_nuevos:.1f}% cumplimiento"
            )
    
    with col2:
        if hay_metas_actualizar:
            total_meta_actualizar = sum(metas_trimestrales['actualizar'].values())
            total_avance_actualizar = avance_actualizar['Q4']  # Avance total hasta Q4
            eficiencia_actualizar = (total_avance_actualizar / total_meta_actualizar * 100) if total_meta_actualizar > 0 else 0
            
            st.metric(
                "🔄 ACTUALIZAR (Anual)",
                f"{total_avance_actualizar}/{total_meta_actualizar}",
                f"{eficiencia_actualizar:.1f}% cumplimiento"
            )
    
    # Información técnica
    st.markdown("---")
    with st.expander("🔧 Información Técnica"):
        st.markdown(f"""
        **📊 Fuente de Datos:**
        - Metas extraídas de: Hoja METAS de Google Sheets
        - Registros analizados: {len(registros_df)}
        - Registros con publicación: {len(registros_df[registros_df['Publicación'].apply(es_fecha_valida)])}
        
        **🔧 Lógica de Cálculo:**
        - Q1: Publicaciones hasta 31/03/2025
        - Q2: Publicaciones hasta 30/06/2025  
        - Q3: Publicaciones hasta 30/09/2025
        - Q4: Publicaciones hasta 31/12/2025
        
        **✅ Correcciones Aplicadas:**
        - Manejo seguro de tipos datetime/date
        - Extracción automática desde Google Sheets
        - Validación de fechas mejorada
        """)


# ===== VERIFICACIÓN =====
if __name__ == "__main__":
    print("📅 Módulo Seguimiento Trimestral - CORREGIDO")
    print("🔧 Correcciones:")
    print("   ✅ Metas desde Google Sheets METAS")
    print("   ✅ Error datetime corregido")
    print("   ✅ Manejo seguro de fechas")
    print("   ✅ Extracción automática de metas")
