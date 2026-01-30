# trimestral.py - MODIFICADO: Seguimiento por hito con avance 2026
"""
Módulo Seguimiento Trimestral - MODIFICADO
- Muestra avance por cada hito (Acuerdo, Análisis, Estándares, Publicación)
- Para cada hito: Total histórico + Metas y Avances 2026 por trimestre
- Diseño limpio y claro
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, date
from data_utils import es_fecha_valida, procesar_fecha, procesar_metas


def es_fecha_2026(fecha_valor):
    """Verifica si una fecha es del año 2026"""
    try:
        fecha = procesar_fecha(fecha_valor)
        if fecha and isinstance(fecha, datetime):
            return fecha.year == 2026
        return False
    except:
        return False


def es_fecha_trimestre_2026(fecha_valor, trimestre):
    """Verifica si una fecha está en el trimestre especificado de 2026"""
    try:
        fecha = procesar_fecha(fecha_valor)
        if fecha and isinstance(fecha, datetime) and fecha.year == 2026:
            mes = fecha.month
            if trimestre == 'Q1' and mes <= 3:
                return True
            elif trimestre == 'Q2' and mes <= 6:
                return True
            elif trimestre == 'Q3' and mes <= 9:
                return True
            elif trimestre == 'Q4' and mes <= 12:
                return True
        return False
    except:
        return False


def calcular_avance_por_hito_2026(registros_df, tipo_dato):
    """
    NUEVA FUNCIÓN: Calcula el avance por hito para 2026
    Retorna Total histórico y avances acumulados por trimestre de 2026
    """
    resultados = {
        'Acuerdo de compromiso': {'total': 0, 'Q1': 0, 'Q2': 0, 'Q3': 0, 'Q4': 0},
        'Análisis y cronograma': {'total': 0, 'Q1': 0, 'Q2': 0, 'Q3': 0, 'Q4': 0},
        'Estándares': {'total': 0, 'Q1': 0, 'Q2': 0, 'Q3': 0, 'Q4': 0},
        'Publicación': {'total': 0, 'Q1': 0, 'Q2': 0, 'Q3': 0, 'Q4': 0}
    }

    try:
        # Filtrar por tipo de dato
        if 'TipoDato' in registros_df.columns:
            registros_tipo = registros_df[registros_df['TipoDato'].astype(str).str.upper() == tipo_dato.upper()]
        else:
            registros_tipo = registros_df

        if registros_tipo.empty:
            return resultados

        # ACUERDO DE COMPROMISO
        # Total histórico
        if 'Acuerdo de compromiso' in registros_tipo.columns:
            resultados['Acuerdo de compromiso']['total'] = len(registros_tipo[
                registros_tipo['Acuerdo de compromiso'].astype(str).str.upper().isin(
                    ['SI', 'SÍ', 'S', 'YES', 'Y', 'COMPLETO'])
            ])

        # Avance 2026 por trimestre (acumulado)
        if 'Suscripción acuerdo de compromiso' in registros_tipo.columns:
            for trimestre in ['Q1', 'Q2', 'Q3', 'Q4']:
                resultados['Acuerdo de compromiso'][trimestre] = len(registros_tipo[
                    (registros_tipo['Acuerdo de compromiso'].astype(str).str.upper().isin(['SI', 'SÍ', 'S', 'YES', 'Y', 'COMPLETO'])) &
                    (registros_tipo['Suscripción acuerdo de compromiso'].apply(lambda x: es_fecha_trimestre_2026(x, trimestre)))
                ])

        # ANÁLISIS Y CRONOGRAMA
        if 'Análisis y cronograma' in registros_tipo.columns:
            # Total histórico
            resultados['Análisis y cronograma']['total'] = len(registros_tipo[
                registros_tipo['Análisis y cronograma'].apply(lambda x: es_fecha_valida(x))
            ])

            # Avance 2026 por trimestre (acumulado)
            for trimestre in ['Q1', 'Q2', 'Q3', 'Q4']:
                resultados['Análisis y cronograma'][trimestre] = len(registros_tipo[
                    registros_tipo['Análisis y cronograma'].apply(lambda x: es_fecha_trimestre_2026(x, trimestre))
                ])

        # ESTÁNDARES
        if 'Estándares' in registros_tipo.columns:
            # Total histórico
            resultados['Estándares']['total'] = len(registros_tipo[
                registros_tipo['Estándares'].apply(lambda x: es_fecha_valida(x))
            ])

            # Avance 2026 por trimestre (acumulado)
            for trimestre in ['Q1', 'Q2', 'Q3', 'Q4']:
                resultados['Estándares'][trimestre] = len(registros_tipo[
                    registros_tipo['Estándares'].apply(lambda x: es_fecha_trimestre_2026(x, trimestre))
                ])

        # PUBLICACIÓN
        if 'Publicación' in registros_tipo.columns:
            # Total histórico
            resultados['Publicación']['total'] = len(registros_tipo[
                registros_tipo['Publicación'].apply(lambda x: es_fecha_valida(x))
            ])

            # Avance 2026 por trimestre (acumulado)
            for trimestre in ['Q1', 'Q2', 'Q3', 'Q4']:
                resultados['Publicación'][trimestre] = len(registros_tipo[
                    registros_tipo['Publicación'].apply(lambda x: es_fecha_trimestre_2026(x, trimestre))
                ])

        return resultados

    except Exception as e:
        st.error(f"Error calculando avance por hito: {e}")
        return resultados


def extraer_metas_por_hito_2026(meta_df):
    """
    NUEVA FUNCIÓN: Extrae las metas trimestrales de 2026 por hito
    Retorna metas acumuladas para cada trimestre
    """
    try:
        # Procesar metas para obtener estructura usable
        metas_nuevas_df, metas_actualizar_df = procesar_metas(meta_df)

        # Fechas objetivo por trimestre de 2026
        fechas_objetivo = {
            'Q1': ['31/03/2026'],
            'Q2': ['30/06/2026'],
            'Q3': ['30/09/2026'],
            'Q4': ['31/12/2026']
        }

        # Estructura de metas por hito y trimestre
        metas_hitos = {
            'nuevos': {
                'Acuerdo de compromiso': {'Q1': 0, 'Q2': 0, 'Q3': 0, 'Q4': 0},
                'Análisis y cronograma': {'Q1': 0, 'Q2': 0, 'Q3': 0, 'Q4': 0},
                'Estándares': {'Q1': 0, 'Q2': 0, 'Q3': 0, 'Q4': 0},
                'Publicación': {'Q1': 0, 'Q2': 0, 'Q3': 0, 'Q4': 0}
            },
            'actualizar': {
                'Acuerdo de compromiso': {'Q1': 0, 'Q2': 0, 'Q3': 0, 'Q4': 0},
                'Análisis y cronograma': {'Q1': 0, 'Q2': 0, 'Q3': 0, 'Q4': 0},
                'Estándares': {'Q1': 0, 'Q2': 0, 'Q3': 0, 'Q4': 0},
                'Publicación': {'Q1': 0, 'Q2': 0, 'Q3': 0, 'Q4': 0}
            }
        }

        # Buscar metas por fecha
        for trimestre, fechas_candidatas in fechas_objetivo.items():
            for fecha_str in fechas_candidatas:
                try:
                    fecha_buscar = procesar_fecha(fecha_str)
                    if fecha_buscar is not None:
                        # Buscar en metas_nuevas_df
                        for fecha_disponible in metas_nuevas_df.index:
                            fecha_disponible_date = fecha_disponible.date() if hasattr(fecha_disponible, 'date') else fecha_disponible
                            fecha_buscar_date = fecha_buscar.date() if hasattr(fecha_buscar, 'date') else fecha_buscar

                            if fecha_disponible_date == fecha_buscar_date:
                                for hito in ['Acuerdo de compromiso', 'Análisis y cronograma', 'Estándares', 'Publicación']:
                                    if hito in metas_nuevas_df.columns:
                                        valor = metas_nuevas_df.loc[fecha_disponible, hito]
                                        metas_hitos['nuevos'][hito][trimestre] = int(float(valor)) if pd.notna(valor) else 0
                                break

                        # Buscar en metas_actualizar_df
                        for fecha_disponible in metas_actualizar_df.index:
                            fecha_disponible_date = fecha_disponible.date() if hasattr(fecha_disponible, 'date') else fecha_disponible
                            fecha_buscar_date = fecha_buscar.date() if hasattr(fecha_buscar, 'date') else fecha_buscar

                            if fecha_disponible_date == fecha_buscar_date:
                                for hito in ['Acuerdo de compromiso', 'Análisis y cronograma', 'Estándares', 'Publicación']:
                                    if hito in metas_actualizar_df.columns:
                                        valor = metas_actualizar_df.loc[fecha_disponible, hito]
                                        metas_hitos['actualizar'][hito][trimestre] = int(float(valor)) if pd.notna(valor) else 0
                                break
                except:
                    continue

        return metas_hitos

    except Exception as e:
        st.warning(f"Error extrayendo metas por hito: {e}")
        return {
            'nuevos': {
                'Acuerdo de compromiso': {'Q1': 0, 'Q2': 0, 'Q3': 0, 'Q4': 0},
                'Análisis y cronograma': {'Q1': 0, 'Q2': 0, 'Q3': 0, 'Q4': 0},
                'Estándares': {'Q1': 0, 'Q2': 0, 'Q3': 0, 'Q4': 0},
                'Publicación': {'Q1': 0, 'Q2': 0, 'Q3': 0, 'Q4': 0}
            },
            'actualizar': {
                'Acuerdo de compromiso': {'Q1': 0, 'Q2': 0, 'Q3': 0, 'Q4': 0},
                'Análisis y cronograma': {'Q1': 0, 'Q2': 0, 'Q3': 0, 'Q4': 0},
                'Estándares': {'Q1': 0, 'Q2': 0, 'Q3': 0, 'Q4': 0},
                'Publicación': {'Q1': 0, 'Q2': 0, 'Q3': 0, 'Q4': 0}
            }
        }


def mostrar_tabla_por_hito(hito_nombre, avances, metas, tipo):
    """
    NUEVA FUNCIÓN: Muestra tabla con Total, Meta y Avance por trimestre para un hito
    """
    st.markdown(f"### {hito_nombre} - {tipo}")

    # Crear datos para la tabla
    datos_tabla = []

    # Fila de Total
    datos_tabla.append({
        'Concepto': 'Total Histórico',
        'Q1 2026': avances['total'],
        'Q2 2026': '',
        'Q3 2026': '',
        'Q4 2026': ''
    })

    # Fila de Meta Acumulada
    meta_row = {'Concepto': 'Meta Acumulada 2026'}
    for trimestre in ['Q1', 'Q2', 'Q3', 'Q4']:
        meta_row[f'{trimestre} 2026'] = metas[trimestre]
    datos_tabla.append(meta_row)

    # Fila de Avance Acumulado 2026
    avance_row = {'Concepto': 'Avance Acumulado 2026'}
    for trimestre in ['Q1', 'Q2', 'Q3', 'Q4']:
        avance_row[f'{trimestre} 2026'] = avances[trimestre]
    datos_tabla.append(avance_row)

    # Fila de Porcentaje de Cumplimiento
    porcentaje_row = {'Concepto': '% Cumplimiento'}
    for trimestre in ['Q1', 'Q2', 'Q3', 'Q4']:
        meta_val = metas[trimestre]
        avance_val = avances[trimestre]
        porcentaje = (avance_val / meta_val * 100) if meta_val > 0 else 0
        porcentaje_row[f'{trimestre} 2026'] = f'{porcentaje:.1f}%'
    datos_tabla.append(porcentaje_row)

    # Crear DataFrame y mostrar
    df_tabla = pd.DataFrame(datos_tabla)

    # Aplicar estilos
    def aplicar_estilos(row):
        if row['Concepto'] == 'Total Histórico':
            return ['background-color: #e3f2fd'] * len(row)
        elif row['Concepto'] == 'Meta Acumulada 2026':
            return ['background-color: #fff3e0'] * len(row)
        elif row['Concepto'] == 'Avance Acumulado 2026':
            return ['background-color: #e8f5e9'] * len(row)
        elif row['Concepto'] == '% Cumplimiento':
            return ['background-color: #f3e5f5'] * len(row)
        return [''] * len(row)

    st.dataframe(
        df_tabla.style.apply(aplicar_estilos, axis=1),
        use_container_width=True,
        hide_index=True
    )


def mostrar_seguimiento_trimestral(registros_df, meta_df):
    """
    MODIFICADO: Seguimiento trimestral por hito con avance 2026
    """
    st.subheader("Seguimiento Trimestral 2026 por Hito")

    if registros_df.empty:
        st.warning("No hay registros disponibles")
        return

    if meta_df.empty:
        st.warning("No hay datos de metas disponibles")
        return

    # Calcular avances y metas
    with st.spinner("Calculando avances por hito..."):
        avances_nuevos = calcular_avance_por_hito_2026(registros_df, 'NUEVO')
        avances_actualizar = calcular_avance_por_hito_2026(registros_df, 'ACTUALIZAR')
        metas_hitos = extraer_metas_por_hito_2026(meta_df)

    # Crear tabs para Nuevos y Actualizar
    tab1, tab2 = st.tabs(["Registros NUEVOS", "Registros a ACTUALIZAR"])

    with tab1:
        st.markdown("## Registros NUEVOS")

        # Mostrar tabla para cada hito
        for hito in ['Acuerdo de compromiso', 'Análisis y cronograma', 'Estándares', 'Publicación']:
            with st.expander(f"📊 {hito}", expanded=True):
                mostrar_tabla_por_hito(
                    hito,
                    avances_nuevos[hito],
                    metas_hitos['nuevos'][hito],
                    'NUEVOS'
                )

        # Gráfico resumen
        st.markdown("---")
        st.markdown("### Gráfico Resumen - NUEVOS")

        fig = go.Figure()

        for hito in ['Acuerdo de compromiso', 'Análisis y cronograma', 'Estándares', 'Publicación']:
            avances_valores = [avances_nuevos[hito][q] for q in ['Q1', 'Q2', 'Q3', 'Q4']]
            fig.add_trace(go.Bar(
                name=hito,
                x=['Q1 2026', 'Q2 2026', 'Q3 2026', 'Q4 2026'],
                y=avances_valores,
                text=avances_valores,
                textposition='auto'
            ))

        fig.update_layout(
            barmode='group',
            title='Avance Acumulado 2026 por Hito - NUEVOS',
            xaxis_title='Trimestre',
            yaxis_title='Cantidad',
            height=500
        )

        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        st.markdown("## Registros a ACTUALIZAR")

        # Mostrar tabla para cada hito
        for hito in ['Acuerdo de compromiso', 'Análisis y cronograma', 'Estándares', 'Publicación']:
            with st.expander(f"📊 {hito}", expanded=True):
                mostrar_tabla_por_hito(
                    hito,
                    avances_actualizar[hito],
                    metas_hitos['actualizar'][hito],
                    'ACTUALIZAR'
                )

        # Gráfico resumen
        st.markdown("---")
        st.markdown("### Gráfico Resumen - ACTUALIZAR")

        fig = go.Figure()

        for hito in ['Acuerdo de compromiso', 'Análisis y cronograma', 'Estándares', 'Publicación']:
            avances_valores = [avances_actualizar[hito][q] for q in ['Q1', 'Q2', 'Q3', 'Q4']]
            fig.add_trace(go.Bar(
                name=hito,
                x=['Q1 2026', 'Q2 2026', 'Q3 2026', 'Q4 2026'],
                y=avances_valores,
                text=avances_valores,
                textposition='auto'
            ))

        fig.update_layout(
            barmode='group',
            title='Avance Acumulado 2026 por Hito - ACTUALIZAR',
            xaxis_title='Trimestre',
            yaxis_title='Cantidad',
            height=500
        )

        st.plotly_chart(fig, use_container_width=True)


if __name__ == "__main__":
    print("Módulo Seguimiento Trimestral - MODIFICADO: Seguimiento por hito 2026")
