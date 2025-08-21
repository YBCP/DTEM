# trimestral.py - CORREGIDO con MÉTRICAS/TARJETAS RESTAURADAS
"""
Módulo Seguimiento Trimestral - CON MÉTRICAS CLAVE RESTAURADAS
- Metas Q1/Q2/Q3/Q4 vienen de la hoja METAS (enero/marzo/septiembre/diciembre)
- Avance = registros publicados antes de fecha límite
- Corregido error de operaciones datetime
- RESTAURADAS: Tarjetas con métricas clave que faltaban
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, date
from data_utils import es_fecha_valida, procesar_fecha, procesar_metas


def crear_metricas_trimestrales(registros_df, meta_df):
    """
    NUEVA FUNCIÓN: Crea métricas clave trimestrales que estaban antes
    """
    try:
        # Calcular métricas generales
        total_registros = len(registros_df) if not registros_df.empty else 0
        
        # Registros con publicación
        registros_publicados = 0
        if 'Publicación' in registros_df.columns:
            registros_publicados = len(registros_df[registros_df['Publicación'].apply(es_fecha_valida)])
        
        # Porcentaje de cumplimiento general
        porcentaje_publicados = (registros_publicados / total_registros * 100) if total_registros > 0 else 0
        
        # Extraer metas del año
        metas_trimestrales = extraer_metas_desde_google_sheets(meta_df)
        
        # Calcular totales de metas
        total_meta_nuevos = sum(metas_trimestrales['nuevos'].values())
        total_meta_actualizar = sum(metas_trimestrales['actualizar'].values())
        total_metas = total_meta_nuevos + total_meta_actualizar
        
        # Avance actual
        avance_nuevos = calcular_avance_publicaciones_corregido(registros_df, 'NUEVO')
        avance_actualizar = calcular_avance_publicaciones_corregido(registros_df, 'ACTUALIZAR')
        
        # Avance total hasta Q4 (final del año)
        total_avance_nuevos = avance_nuevos.get('Q4', 0)
        total_avance_actualizar = avance_actualizar.get('Q4', 0)
        total_avance = total_avance_nuevos + total_avance_actualizar
        
        # Porcentaje de cumplimiento de metas
        porcentaje_meta = (total_avance / total_metas * 100) if total_metas > 0 else 0
        
        # Trimestre actual
        mes_actual = datetime.now().month
        if mes_actual <= 3:
            trimestre_actual = "Q1"
        elif mes_actual <= 6:
            trimestre_actual = "Q2"
        elif mes_actual <= 9:
            trimestre_actual = "Q3"
        else:
            trimestre_actual = "Q4"
        
        return {
            'total_registros': total_registros,
            'registros_publicados': registros_publicados,
            'porcentaje_publicados': porcentaje_publicados,
            'total_metas': total_metas,
            'total_avance': total_avance,
            'porcentaje_meta': porcentaje_meta,
            'trimestre_actual': trimestre_actual,
            'total_meta_nuevos': total_meta_nuevos,
            'total_meta_actualizar': total_meta_actualizar,
            'total_avance_nuevos': total_avance_nuevos,
            'total_avance_actualizar': total_avance_actualizar
        }
        
    except Exception as e:
        st.warning(f"Error calculando métricas: {e}")
        return {
            'total_registros': 0,
            'registros_publicados': 0,
            'porcentaje_publicados': 0,
            'total_metas': 0,
            'total_avance': 0,
            'porcentaje_meta': 0,
            'trimestre_actual': 'Q1',
            'total_meta_nuevos': 0,
            'total_meta_actualizar': 0,
            'total_avance_nuevos': 0,
            'total_avance_actualizar': 0
        }


def mostrar_tarjetas_metricas_clave(metricas):
    """
    FUNCIÓN RESTAURADA: Muestra las tarjetas con métricas clave que faltaban
    """
    st.markdown("### Métricas Clave del Año")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total Registros",
            metricas['total_registros'],
            help="Número total de registros en el sistema"
        )
        
        st.metric(
            "Publicados",
            metricas['registros_publicados'],
            delta=f"{metricas['porcentaje_publicados']:.1f}%",
            help="Registros con fecha de publicación"
        )
    
    with col2:
        st.metric(
            "Meta Anual Total",
            metricas['total_metas'],
            help="Meta total de publicaciones para el año"
        )
        
        st.metric(
            "Avance Anual",
            metricas['total_avance'],
            delta=f"{metricas['porcentaje_meta']:.1f}%",
            help="Avance actual vs meta anual"
        )
    
    with col3:
        st.metric(
            "Meta Nuevos",
            metricas['total_meta_nuevos'],
            help="Meta de registros nuevos para el año"
        )
        
        st.metric(
            "Avance Nuevos",
            metricas['total_avance_nuevos'],
            delta=f"{(metricas['total_avance_nuevos']/metricas['total_meta_nuevos']*100) if metricas['total_meta_nuevos'] > 0 else 0:.1f}%",
            help="Avance en registros nuevos"
        )
    
    with col4:
        st.metric(
            "Meta Actualizar",
            metricas['total_meta_actualizar'],
            help="Meta de registros a actualizar para el año"
        )
        
        st.metric(
            "Avance Actualizar", 
            metricas['total_avance_actualizar'],
            delta=f"{(metricas['total_avance_actualizar']/metricas['total_meta_actualizar']*100) if metricas['total_meta_actualizar'] > 0 else 0:.1f}%",
            help="Avance en registros a actualizar"
        )


def mostrar_indicadores_trimestre_actual(metricas, avance_nuevos, avance_actualizar, metas_trimestrales):
    """
    FUNCIÓN ADICIONAL: Muestra indicadores específicos del trimestre actual
    """
    trimestre = metricas['trimestre_actual']
    
    st.markdown(f"### Indicadores {trimestre} 2025 (Trimestre Actual)")
    
    # Métricas del trimestre actual
    meta_nuevos_q = metas_trimestrales['nuevos'][trimestre]
    meta_actualizar_q = metas_trimestrales['actualizar'][trimestre]
    avance_nuevos_q = avance_nuevos[trimestre]
    avance_actualizar_q = avance_actualizar[trimestre]
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.info(f"""
        **Registros Nuevos - {trimestre}**
        - Meta: {meta_nuevos_q}
        - Avance: {avance_nuevos_q}
        - Cumplimiento: {(avance_nuevos_q/meta_nuevos_q*100) if meta_nuevos_q > 0 else 0:.1f}%
        """)
    
    with col2:
        st.info(f"""
        **Registros Actualizar - {trimestre}**
        - Meta: {meta_actualizar_q}
        - Avance: {avance_actualizar_q}
        - Cumplimiento: {(avance_actualizar_q/meta_actualizar_q*100) if meta_actualizar_q > 0 else 0:.1f}%
        """)
    
    with col3:
        total_meta_q = meta_nuevos_q + meta_actualizar_q
        total_avance_q = avance_nuevos_q + avance_actualizar_q
        cumplimiento_total_q = (total_avance_q/total_meta_q*100) if total_meta_q > 0 else 0
        
        st.info(f"""
        **Total {trimestre}**
        - Meta: {total_meta_q}
        - Avance: {total_avance_q}
        - Cumplimiento: {cumplimiento_total_q:.1f}%
        """)


def extraer_metas_desde_google_sheets(meta_df):
    """
    Extrae las metas trimestrales desde la hoja METAS de Google Sheets
    Q1 = 31 enero, Q2 = 31 marzo, Q3 = 30 septiembre, Q4 = 31 diciembre
    """
    try:
        # Procesar metas para obtener estructura usable
        metas_nuevas_df, metas_actualizar_df = procesar_metas(meta_df)
        
        # Fechas EXACTAS por trimestre
        fechas_objetivo = {
            'Q1': ['31/03/2025'],  # Q1 = 31 marzo EXACTO
            'Q2': ['30/06/2025'],  # Q2 = 30 junio EXACTO
            'Q3': ['30/09/2025'],  # Q3 = 30 septiembre EXACTO
            'Q4': ['31/12/2025']   # Q4 = 31 diciembre EXACTO
        }
        
        metas_trimestrales = {
            'nuevos': {'Q1': 0, 'Q2': 0, 'Q3': 0, 'Q4': 0},
            'actualizar': {'Q1': 0, 'Q2': 0, 'Q3': 0, 'Q4': 0}
        }
        
        # Buscar metas por fecha EXACTA
        for trimestre, fechas_candidatas in fechas_objetivo.items():
            meta_nueva_encontrada = 0
            meta_actualizar_encontrada = 0
            
            for fecha_str in fechas_candidatas:
                try:
                    fecha_buscar = procesar_fecha(fecha_str)
                    if fecha_buscar is not None:
                        # Buscar coincidencia EXACTA por fecha
                        for fecha_disponible in metas_nuevas_df.index:
                            fecha_disponible_date = fecha_disponible.date() if hasattr(fecha_disponible, 'date') else fecha_disponible
                            fecha_buscar_date = fecha_buscar.date() if hasattr(fecha_buscar, 'date') else fecha_buscar
                            
                            if fecha_disponible_date == fecha_buscar_date:
                                meta_nueva_encontrada = metas_nuevas_df.loc[fecha_disponible, 'Publicación']
                                break
                        
                        # Mismo proceso para metas_actualizar_df
                        for fecha_disponible in metas_actualizar_df.index:
                            fecha_disponible_date = fecha_disponible.date() if hasattr(fecha_disponible, 'date') else fecha_disponible
                            fecha_buscar_date = fecha_buscar.date() if hasattr(fecha_buscar, 'date') else fecha_buscar
                            
                            if fecha_disponible_date == fecha_buscar_date:
                                meta_actualizar_encontrada = metas_actualizar_df.loc[fecha_disponible, 'Publicación']
                                break
                        
                        # Si encontramos coincidencia exacta, parar
                        if meta_nueva_encontrada > 0 or meta_actualizar_encontrada > 0:
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
        
        # CORREGIDO: Fechas límite EXACTAS para cada trimestre
        fechas_limite = {
            'Q1': datetime(2025, 3, 31),   # Q1 hasta 31 MARZO
            'Q2': datetime(2025, 6, 30),   # Q2 hasta 30 JUNIO
            'Q3': datetime(2025, 9, 30),   # Q3 hasta 30 SEPTIEMBRE
            'Q4': datetime(2025, 12, 31)   # Q4 hasta 31 DICIEMBRE
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
    Seguimiento trimestral CORREGIDO CON MÉTRICAS RESTAURADAS:
    - Metas vienen de la hoja METAS de Google Sheets
    - Avance = publicaciones hasta fecha límite de cada trimestre
    - Sin errores de operaciones datetime
    - MÉTRICAS CLAVE RESTAURADAS
    """
    

    if registros_df.empty:
        st.warning("No hay registros disponibles")
        return
    
    if meta_df.empty:
        st.warning("No hay datos de metas disponibles")
        return
    
    # ===== MÉTRICAS CLAVE RESTAURADAS =====
    with st.spinner("Calculando métricas clave..."):
        metricas = crear_metricas_trimestrales(registros_df, meta_df)
        metas_trimestrales = extraer_metas_desde_google_sheets(meta_df)
        avance_nuevos = calcular_avance_publicaciones_corregido(registros_df, 'NUEVO')
        avance_actualizar = calcular_avance_publicaciones_corregido(registros_df, 'ACTUALIZAR')
    
    # MOSTRAR TARJETAS CON MÉTRICAS CLAVE
    mostrar_tarjetas_metricas_clave(metricas)
    
    st.markdown("---")
    
    # INDICADORES DEL TRIMESTRE ACTUAL
    mostrar_indicadores_trimestre_actual(metricas, avance_nuevos, avance_actualizar, metas_trimestrales)
    
    st.markdown("---")
    
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
            name='Meta (Google Sheets)',
            line=dict(color='#ff7f0e', width=4, dash='dash'),
            marker=dict(size=12, symbol='diamond'),
            hovertemplate='<b>Meta</b><br>%{x}: %{y}<extra></extra>'
        ))
        
        # Línea de avance
        fig.add_trace(go.Scatter(
            x=trimestres,
            y=avance_valores,
            mode='lines+markers',
            name='Avance (Publicado)',
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
        st.warning("No se encontraron metas en la hoja METAS de Google Sheets")
        st.info("Verifique que la hoja METAS tenga datos para las fechas de enero, marzo, septiembre y diciembre")
        return
    
    # Mostrar gráfico para NUEVOS
    if hay_metas_nuevos:
        st.markdown("---")
        fig_nuevos = crear_datos_graficos(
            metas_trimestrales['nuevos'],
            avance_nuevos,
            "Registros NUEVOS - Meta vs Avance"
        )
        st.plotly_chart(fig_nuevos, use_container_width=True)
        
        # Tabla detallada NUEVOS
        with st.expander("Datos Detallados - Registros NUEVOS"):
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
            "Registros a ACTUALIZAR - Meta vs Avance"
        )
        st.plotly_chart(fig_actualizar, use_container_width=True)
        
        # Tabla detallada ACTUALIZAR
        with st.expander("Datos Detallados - Registros a ACTUALIZAR"):
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
    st.markdown("### Resumen Ejecutivo")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if hay_metas_nuevos:
            total_meta_nuevos = sum(metas_trimestrales['nuevos'].values())
            total_avance_nuevos = avance_nuevos['Q4']  # Avance total hasta Q4
            eficiencia_nuevos = (total_avance_nuevos / total_meta_nuevos * 100) if total_meta_nuevos > 0 else 0
            
            st.metric(
                "NUEVOS (Anual)",
                f"{total_avance_nuevos}/{total_meta_nuevos}",
                f"{eficiencia_nuevos:.1f}% cumplimiento"
            )
    
    with col2:
        if hay_metas_actualizar:
            total_meta_actualizar = sum(metas_trimestrales['actualizar'].values())
            total_avance_actualizar = avance_actualizar['Q4']  # Avance total hasta Q4
            eficiencia_actualizar = (total_avance_actualizar / total_meta_actualizar * 100) if total_meta_actualizar > 0 else 0
            
            st.metric(
                "ACTUALIZAR (Anual)",
                f"{total_avance_actualizar}/{total_meta_actualizar}",
                f"{eficiencia_actualizar:.1f}% cumplimiento"
            )
    
    # Información técnica
    st.markdown("---")
    with st.expander("Información Técnica"):
        st.markdown(f"""
        **Fuente de Datos:**
        - Metas extraídas de: Hoja METAS de Google Sheets
        - Registros analizados: {len(registros_df)}
        - Registros con publicación: {len(registros_df[registros_df['Publicación'].apply(es_fecha_valida)])}
        
        **Lógica de Cálculo:**
        - Q1: Publicaciones hasta 31/03/2025
        - Q2: Publicaciones hasta 30/06/2025  
        - Q3: Publicaciones hasta 30/09/2025
        - Q4: Publicaciones hasta 31/12/2025
        """)


# ===== VERIFICACIÓN =====
if __name__ == "__main__":
    print("Módulo Seguimiento Trimestral - CON MÉTRICAS RESTAURADAS")
