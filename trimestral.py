# trimestral.py - REORGANIZADO: Gráfico primero, luego tarjetas por trimestre
"""
Módulo Seguimiento Trimestral - REORGANIZADO
- Gráfico resumen primero
- 4 tarjetas por trimestre (clickeables)
- Al hacer clic: muestra registros del campo "Trimestre proyectado"
- Orden de pestañas: Publicación, Estándares, Análisis y cronograma, Acuerdos de compromiso
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, date
from data_utils import es_fecha_valida, procesar_fecha, procesar_metas
from io import BytesIO


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
    Calcula el avance por hito para 2026
    Retorna Total histórico y avances acumulados por trimestre de 2026
    FILTRADO: Solo registros con Trabajar2026 = 1
    """
    resultados = {
        'Publicación': {'total': 0, 'Q1': 0, 'Q2': 0, 'Q3': 0, 'Q4': 0},
        'Estándares': {'total': 0, 'Q1': 0, 'Q2': 0, 'Q3': 0, 'Q4': 0},
        'Análisis y cronograma': {'total': 0, 'Q1': 0, 'Q2': 0, 'Q3': 0, 'Q4': 0},
        'Acuerdo de compromiso': {'total': 0, 'Q1': 0, 'Q2': 0, 'Q3': 0, 'Q4': 0}
    }

    try:
        # Filtrar por tipo de dato
        if 'TipoDato' in registros_df.columns:
            registros_tipo = registros_df[registros_df['TipoDato'].astype(str).str.upper() == tipo_dato.upper()]
        else:
            registros_tipo = registros_df

        # NUEVO: Filtrar solo registros con Trabajar2026 = 1
        if 'Trabajar2026' in registros_tipo.columns:
            registros_tipo = registros_tipo[registros_tipo['Trabajar2026'].astype(str).str.strip() == '1']

        if registros_tipo.empty:
            return resultados

        # NUEVO: Contar SOLO PUBLICADOS por Trimestre proyectado
        if 'Trimestre proyectado' in registros_tipo.columns and 'Publicación' in registros_tipo.columns:
            trimestre_map = {'Q1': '1', 'Q2': '2', 'Q3': '3', 'Q4': '4'}

            for trimestre in ['Q1', 'Q2', 'Q3', 'Q4']:
                # Mapear Q1->1, Q2->2, etc.
                trimestre_numero = trimestre_map[trimestre]

                # Filtrar registros del trimestre específico
                registros_trimestre = registros_tipo[
                    registros_tipo['Trimestre proyectado'].astype(str).str.strip() == trimestre_numero
                ]

                # Contar SOLO los PUBLICADOS (tienen fecha en Publicación)
                publicados = len(registros_trimestre[
                    registros_trimestre['Publicación'].apply(lambda x: es_fecha_valida(x))
                ])

                # Asignar el mismo valor a todos los hitos (porque la meta es para publicación)
                resultados['Publicación'][trimestre] = publicados
                resultados['Estándares'][trimestre] = 0
                resultados['Análisis y cronograma'][trimestre] = 0
                resultados['Acuerdo de compromiso'][trimestre] = 0

        # TOTALES HISTÓRICOS (todos los tiempos)
        # PUBLICACIÓN
        if 'Publicación' in registros_tipo.columns:
            resultados['Publicación']['total'] = len(registros_tipo[
                registros_tipo['Publicación'].apply(lambda x: es_fecha_valida(x))
            ])

        # ESTÁNDARES
        if 'Estándares' in registros_tipo.columns:
            resultados['Estándares']['total'] = len(registros_tipo[
                registros_tipo['Estándares'].apply(lambda x: es_fecha_valida(x))
            ])

        # ANÁLISIS Y CRONOGRAMA
        if 'Análisis y cronograma' in registros_tipo.columns:
            resultados['Análisis y cronograma']['total'] = len(registros_tipo[
                registros_tipo['Análisis y cronograma'].apply(lambda x: es_fecha_valida(x))
            ])

        # ACUERDO DE COMPROMISO
        if 'Acuerdo de compromiso' in registros_tipo.columns:
            resultados['Acuerdo de compromiso']['total'] = len(registros_tipo[
                registros_tipo['Acuerdo de compromiso'].astype(str).str.upper().isin(
                    ['SI', 'SÍ', 'S', 'YES', 'Y', 'COMPLETO'])
            ])

        return resultados

    except Exception as e:
        st.error(f"Error calculando avance por hito: {e}")
        return resultados


def extraer_metas_por_hito_2026(meta_df):
    """
    Extrae las metas trimestrales de 2026 por hito
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

        # Estructura de metas por hito y trimestre (orden reorganizado)
        metas_hitos = {
            'nuevos': {
                'Publicación': {'Q1': 0, 'Q2': 0, 'Q3': 0, 'Q4': 0},
                'Estándares': {'Q1': 0, 'Q2': 0, 'Q3': 0, 'Q4': 0},
                'Análisis y cronograma': {'Q1': 0, 'Q2': 0, 'Q3': 0, 'Q4': 0},
                'Acuerdo de compromiso': {'Q1': 0, 'Q2': 0, 'Q3': 0, 'Q4': 0}
            },
            'actualizar': {
                'Publicación': {'Q1': 0, 'Q2': 0, 'Q3': 0, 'Q4': 0},
                'Estándares': {'Q1': 0, 'Q2': 0, 'Q3': 0, 'Q4': 0},
                'Análisis y cronograma': {'Q1': 0, 'Q2': 0, 'Q3': 0, 'Q4': 0},
                'Acuerdo de compromiso': {'Q1': 0, 'Q2': 0, 'Q3': 0, 'Q4': 0}
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
                                for hito in ['Publicación', 'Estándares', 'Análisis y cronograma', 'Acuerdo de compromiso']:
                                    if hito in metas_nuevas_df.columns:
                                        valor = metas_nuevas_df.loc[fecha_disponible, hito]
                                        metas_hitos['nuevos'][hito][trimestre] = int(float(valor)) if pd.notna(valor) else 0
                                break

                        # Buscar en metas_actualizar_df
                        for fecha_disponible in metas_actualizar_df.index:
                            fecha_disponible_date = fecha_disponible.date() if hasattr(fecha_disponible, 'date') else fecha_disponible
                            fecha_buscar_date = fecha_buscar.date() if hasattr(fecha_buscar, 'date') else fecha_buscar

                            if fecha_disponible_date == fecha_buscar_date:
                                for hito in ['Publicación', 'Estándares', 'Análisis y cronograma', 'Acuerdo de compromiso']:
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
                'Publicación': {'Q1': 0, 'Q2': 0, 'Q3': 0, 'Q4': 0},
                'Estándares': {'Q1': 0, 'Q2': 0, 'Q3': 0, 'Q4': 0},
                'Análisis y cronograma': {'Q1': 0, 'Q2': 0, 'Q3': 0, 'Q4': 0},
                'Acuerdo de compromiso': {'Q1': 0, 'Q2': 0, 'Q3': 0, 'Q4': 0}
            },
            'actualizar': {
                'Publicación': {'Q1': 0, 'Q2': 0, 'Q3': 0, 'Q4': 0},
                'Estándares': {'Q1': 0, 'Q2': 0, 'Q3': 0, 'Q4': 0},
                'Análisis y cronograma': {'Q1': 0, 'Q2': 0, 'Q3': 0, 'Q4': 0},
                'Acuerdo de compromiso': {'Q1': 0, 'Q2': 0, 'Q3': 0, 'Q4': 0}
            }
        }


def obtener_registros_por_trimestre(registros_df, trimestre, tipo_dato):
    """
    Obtiene los registros que tienen el trimestre especificado en el campo 'Trimestre proyectado'
    FILTRADO: Solo registros con Trabajar2026 = 1 Y Trimestre proyectado = 1/2/3/4
    """
    try:
        # Mapear Q1->1, Q2->2, Q3->3, Q4->4
        trimestre_map = {'Q1': '1', 'Q2': '2', 'Q3': '3', 'Q4': '4'}
        trimestre_numero = trimestre_map.get(trimestre, trimestre)

        # Filtrar por tipo de dato
        if 'TipoDato' in registros_df.columns:
            registros_tipo = registros_df[registros_df['TipoDato'].astype(str).str.upper() == tipo_dato.upper()]
        else:
            registros_tipo = registros_df

        # NUEVO: Filtrar solo registros con Trabajar2026 = 1
        if 'Trabajar2026' in registros_tipo.columns:
            registros_tipo = registros_tipo[registros_tipo['Trabajar2026'].astype(str).str.strip() == '1']

        if registros_tipo.empty:
            return pd.DataFrame()

        # Filtrar por trimestre proyectado (valores 1, 2, 3, 4)
        if 'Trimestre proyectado' in registros_tipo.columns:
            registros_trimestre = registros_tipo[
                registros_tipo['Trimestre proyectado'].astype(str).str.strip() == trimestre_numero
            ]
            return registros_trimestre
        else:
            return pd.DataFrame()

    except Exception as e:
        st.error(f"Error obteniendo registros por trimestre: {e}")
        return pd.DataFrame()


def calcular_porcentaje_hito(row, hito):
    """Calcula si un hito está completado (100%) o no (0%)"""
    from data_utils import es_fecha_valida

    try:
        if hito == 'Acuerdo de compromiso':
            # Acceder al valor de la columna
            if hito in row.index:
                valor = str(row[hito]).upper()
                return 100 if valor in ['SI', 'SÍ', 'S', 'YES', 'Y', 'COMPLETO', '1'] else 0
            return 0
        else:
            # Para otros hitos, verificar si hay fecha válida
            if hito in row.index:
                valor = row[hito]
                return 100 if es_fecha_valida(valor) else 0
            return 0
    except Exception as e:
        return 0


def mostrar_tarjeta_trimestre(trimestre, avances_dict, metas_dict, registros_df, tipo_dato):
    """
    Muestra una tarjeta para un trimestre específico
    Calcula: registros PUBLICADOS del trimestre / meta del trimestre
    """
    # Obtener registros del trimestre
    registros_trimestre = obtener_registros_por_trimestre(registros_df, trimestre, tipo_dato)

    # Contar registros PUBLICADOS (tienen fecha en campo Publicación)
    registros_publicados = 0
    if not registros_trimestre.empty and 'Publicación' in registros_trimestre.columns:
        from data_utils import es_fecha_valida
        registros_publicados = len(registros_trimestre[
            registros_trimestre['Publicación'].apply(lambda x: es_fecha_valida(x))
        ])

    # Meta del trimestre para PUBLICACIÓN específicamente
    meta_publicacion = metas_dict.get('Publicación', {}).get(trimestre, 0)

    # Porcentaje = publicados / meta de publicación
    porcentaje = (registros_publicados / meta_publicacion * 100) if meta_publicacion > 0 else 0

    # Determinar color según porcentaje
    if porcentaje >= 80:
        color = "#16a34a"
    elif porcentaje >= 50:
        color = "#f59e0b"
    else:
        color = "#dc2626"

    with st.container():
        # Encabezado de la tarjeta
        col1, col2, col3 = st.columns([2, 1, 1])

        with col1:
            st.markdown(f"### {trimestre} 2026")

        with col2:
            st.metric("Publicados", f"{registros_publicados}/{meta_publicacion}")

        with col3:
            st.markdown(f"<h3 style='color: {color};'>{porcentaje:.1f}%</h3>", unsafe_allow_html=True)

        # Expander para mostrar registros (sin causar recarga)
        with st.expander(f"Ver registros de {trimestre}", expanded=False):
            if not registros_trimestre.empty:
                st.markdown(f"**Registros programados para {trimestre}:** {len(registros_trimestre)}")

                # Resetear índice para evitar problemas
                registros_reset = registros_trimestre.reset_index(drop=True).copy()

                # Crear DataFrame con columnas específicas
                datos_detalle = []

                for idx, row in registros_reset.iterrows():
                    fila = {}

                    # Entidad
                    if 'Entidad' in row.index:
                        fila['Entidad'] = str(row['Entidad'])
                    else:
                        fila['Entidad'] = ''

                    # Nivel de Información - probar TODAS las variantes posibles
                    nivel = ''
                    posibles_nombres = ['Nivel Información ', 'Nivel de Información', 'Nivel Información',
                                       'nivel información ', 'nivel de información', 'Nivel informacion',
                                       'Nivel de informacion']

                    for nombre in posibles_nombres:
                        if nombre in row.index:
                            nivel = str(row[nombre]) if pd.notna(row[nombre]) else ''
                            if nivel and nivel not in ['', 'nan', 'None']:
                                break

                    fila['Nivel de Información'] = nivel

                    # Calcular % de avance por hito
                    fila['% Acuerdo'] = calcular_porcentaje_hito(row, 'Acuerdo de compromiso')
                    fila['% Análisis'] = calcular_porcentaje_hito(row, 'Análisis y cronograma')
                    fila['% Estándares'] = calcular_porcentaje_hito(row, 'Estándares')
                    fila['% Publicación'] = calcular_porcentaje_hito(row, 'Publicación')

                    # % Avance Total
                    if 'Porcentaje Avance' in row.index:
                        fila['% Avance Total'] = row['Porcentaje Avance']
                    else:
                        fila['% Avance Total'] = 0

                    datos_detalle.append(fila)

                # Crear DataFrame y mostrar
                df_detalle = pd.DataFrame(datos_detalle)
                st.dataframe(df_detalle, use_container_width=True, hide_index=True)
            else:
                st.info(f"No hay registros programados para {trimestre}")


def generar_excel_seguimiento(registros_df):
    """
    Genera un archivo Excel con los datos de seguimiento trimestral
    Columnas: Trimestre, Cod, Nivel de Información, % Acuerdo, % Análisis, % Estándares, % Publicación, % Avance Total
    """
    datos_excel = []

    # Filtrar solo registros 2026
    registros_2026 = registros_df.copy()
    if 'Trabajar2026' in registros_2026.columns:
        registros_2026 = registros_2026[registros_2026['Trabajar2026'].astype(str).str.strip() == '1']

    # Procesar cada registro
    for _, row in registros_2026.iterrows():
        # Obtener trimestre proyectado
        trimestre = ''
        if 'Trimestre proyectado' in row.index:
            trimestre_val = str(row['Trimestre proyectado']).strip()
            if trimestre_val in ['1', '2', '3', '4']:
                trimestre = f'Q{trimestre_val}'

        # Si no tiene trimestre proyectado, omitir
        if not trimestre:
            continue

        # Cod
        cod = str(row['Cod']) if 'Cod' in row.index else ''

        # Nivel de Información
        nivel = ''
        posibles_nombres = ['Nivel Información ', 'Nivel de Información', 'Nivel Información',
                           'nivel información ', 'nivel de información', 'Nivel informacion']
        for nombre in posibles_nombres:
            if nombre in row.index:
                nivel = str(row[nombre]) if pd.notna(row[nombre]) else ''
                if nivel and nivel not in ['', 'nan', 'None']:
                    break

        # Entidad
        entidad = str(row['Entidad']) if 'Entidad' in row.index and pd.notna(row['Entidad']) else ''

        # Calcular porcentajes por hito
        pct_acuerdo = calcular_porcentaje_hito(row, 'Acuerdo de compromiso')
        pct_analisis = calcular_porcentaje_hito(row, 'Análisis y cronograma')
        pct_estandares = calcular_porcentaje_hito(row, 'Estándares')
        pct_publicacion = calcular_porcentaje_hito(row, 'Publicación')

        # % Avance Total
        pct_total = row['Porcentaje Avance'] if 'Porcentaje Avance' in row.index else 0

        datos_excel.append({
            'Trimestre': trimestre,
            'Cod': cod,
            'Entidad': entidad,
            'Nivel de Información': nivel,
            '% Acuerdo de compromiso': pct_acuerdo,
            '% Análisis y cronograma': pct_analisis,
            '% Estándares': pct_estandares,
            '% Publicación': pct_publicacion,
            '% Avance Total': pct_total
        })

    # Crear DataFrame
    df_excel = pd.DataFrame(datos_excel)

    # Ordenar por trimestre y entidad
    df_excel = df_excel.sort_values(['Trimestre', 'Entidad', 'Cod'])

    # Convertir a Excel en memoria
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_excel.to_excel(writer, index=False, sheet_name='Seguimiento Trimestral')

        # Ajustar ancho de columnas
        worksheet = writer.sheets['Seguimiento Trimestral']
        for idx, col in enumerate(df_excel.columns):
            max_length = max(
                df_excel[col].astype(str).apply(len).max(),
                len(col)
            )
            worksheet.column_dimensions[chr(65 + idx)].width = min(max_length + 2, 50)

    output.seek(0)
    return output


def mostrar_seguimiento_trimestral(registros_df, meta_df):
    """
    REORGANIZADO: Muestra primero el gráfico resumen, luego las 4 tarjetas por trimestre
    """
    # Encabezado con botón de exportación
    col_titulo, col_boton = st.columns([3, 1])

    with col_titulo:
        st.subheader("Seguimiento Trimestral 2026 por Hito")

    with col_boton:
        if not registros_df.empty:
            try:
                excel_data = generar_excel_seguimiento(registros_df)
                st.download_button(
                    label="📥 Exportar a Excel",
                    data=excel_data,
                    file_name=f"seguimiento_trimestral_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            except Exception as e:
                st.error(f"Error generando Excel: {str(e)}")

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

        # GRÁFICO RESUMEN PRIMERO - SOLO PUBLICACIÓN
        st.markdown("### Gráfico Resumen - Registros Publicados por Trimestre")

        fig = go.Figure()

        # Solo mostrar Publicación (los otros hitos están en 0)
        avances_publicacion = [avances_nuevos['Publicación'][q] for q in ['Q1', 'Q2', 'Q3', 'Q4']]
        metas_publicacion = [metas_hitos['nuevos']['Publicación'][q] for q in ['Q1', 'Q2', 'Q3', 'Q4']]

        # Barras de avance
        fig.add_trace(go.Bar(
            name='Publicados',
            x=['Q1 2026', 'Q2 2026', 'Q3 2026', 'Q4 2026'],
            y=avances_publicacion,
            text=avances_publicacion,
            textposition='auto',
            marker_color='#10B981'
        ))

        # Línea de meta
        fig.add_trace(go.Scatter(
            name='Meta',
            x=['Q1 2026', 'Q2 2026', 'Q3 2026', 'Q4 2026'],
            y=metas_publicacion,
            mode='lines+markers+text',
            text=metas_publicacion,
            textposition='top center',
            line=dict(color='#DC2626', width=2, dash='dash'),
            marker=dict(size=10)
        ))

        fig.update_layout(
            title='Registros Publicados vs Meta por Trimestre - NUEVOS',
            xaxis_title='Trimestre',
            yaxis_title='Cantidad de Registros',
            height=500,
            showlegend=True
        )

        st.plotly_chart(fig, use_container_width=True)

        # TARJETAS POR TRIMESTRE
        st.markdown("---")
        st.markdown("### Detalle por Trimestre")

        for trimestre in ['Q1', 'Q2', 'Q3', 'Q4']:
            mostrar_tarjeta_trimestre(trimestre, avances_nuevos, metas_hitos['nuevos'], registros_df, 'NUEVO')
            st.markdown("---")

        # DETALLE POR HITO
        st.markdown("---")
        st.markdown("### Detalle por Trimestre y Hito")

        # Aplicar estilos
        def aplicar_estilos(row):
            if row['Concepto'] == 'Meta':
                return ['background-color: #fff3e0'] * len(row)
            elif row['Concepto'] == 'Completados':
                return ['background-color: #e8f5e9'] * len(row)
            elif row['Concepto'] == '% Cumplimiento':
                return ['background-color: #f3e5f5'] * len(row)
            return [''] * len(row)

        # Crear tabs por hito
        tab_acuerdo, tab_analisis, tab_estandares, tab_publicacion = st.tabs([
            "Acuerdo de compromiso",
            "Análisis y cronograma",
            "Estándares",
            "Publicación"
        ])

        # Tab Acuerdo de compromiso
        with tab_acuerdo:
            datos_tabla = []

            # Fila de Meta
            meta_row = {'Concepto': 'Meta'}
            for trimestre in ['Q1', 'Q2', 'Q3', 'Q4']:
                meta_row[f'{trimestre} 2026'] = metas_hitos['nuevos']['Acuerdo de compromiso'][trimestre]
            datos_tabla.append(meta_row)

            # Fila de Completados
            avance_row = {'Concepto': 'Completados'}
            for trimestre in ['Q1', 'Q2', 'Q3', 'Q4']:
                avance_row[f'{trimestre} 2026'] = avances_nuevos['Acuerdo de compromiso'][trimestre]
            datos_tabla.append(avance_row)

            # Fila de Porcentaje
            porcentaje_row = {'Concepto': '% Cumplimiento'}
            for trimestre in ['Q1', 'Q2', 'Q3', 'Q4']:
                meta_val = metas_hitos['nuevos']['Acuerdo de compromiso'][trimestre]
                avance_val = avances_nuevos['Acuerdo de compromiso'][trimestre]
                porcentaje = (avance_val / meta_val * 100) if meta_val > 0 else 0
                porcentaje_row[f'{trimestre} 2026'] = f'{porcentaje:.1f}%'
            datos_tabla.append(porcentaje_row)

            df_tabla = pd.DataFrame(datos_tabla)
            st.dataframe(df_tabla.style.apply(aplicar_estilos, axis=1), use_container_width=True, hide_index=True)

        # Tab Análisis y cronograma
        with tab_analisis:
            datos_tabla = []

            meta_row = {'Concepto': 'Meta'}
            for trimestre in ['Q1', 'Q2', 'Q3', 'Q4']:
                meta_row[f'{trimestre} 2026'] = metas_hitos['nuevos']['Análisis y cronograma'][trimestre]
            datos_tabla.append(meta_row)

            avance_row = {'Concepto': 'Completados'}
            for trimestre in ['Q1', 'Q2', 'Q3', 'Q4']:
                avance_row[f'{trimestre} 2026'] = avances_nuevos['Análisis y cronograma'][trimestre]
            datos_tabla.append(avance_row)

            porcentaje_row = {'Concepto': '% Cumplimiento'}
            for trimestre in ['Q1', 'Q2', 'Q3', 'Q4']:
                meta_val = metas_hitos['nuevos']['Análisis y cronograma'][trimestre]
                avance_val = avances_nuevos['Análisis y cronograma'][trimestre]
                porcentaje = (avance_val / meta_val * 100) if meta_val > 0 else 0
                porcentaje_row[f'{trimestre} 2026'] = f'{porcentaje:.1f}%'
            datos_tabla.append(porcentaje_row)

            df_tabla = pd.DataFrame(datos_tabla)
            st.dataframe(df_tabla.style.apply(aplicar_estilos, axis=1), use_container_width=True, hide_index=True)

        # Tab Estándares
        with tab_estandares:
            datos_tabla = []

            meta_row = {'Concepto': 'Meta'}
            for trimestre in ['Q1', 'Q2', 'Q3', 'Q4']:
                meta_row[f'{trimestre} 2026'] = metas_hitos['nuevos']['Estándares'][trimestre]
            datos_tabla.append(meta_row)

            avance_row = {'Concepto': 'Completados'}
            for trimestre in ['Q1', 'Q2', 'Q3', 'Q4']:
                avance_row[f'{trimestre} 2026'] = avances_nuevos['Estándares'][trimestre]
            datos_tabla.append(avance_row)

            porcentaje_row = {'Concepto': '% Cumplimiento'}
            for trimestre in ['Q1', 'Q2', 'Q3', 'Q4']:
                meta_val = metas_hitos['nuevos']['Estándares'][trimestre]
                avance_val = avances_nuevos['Estándares'][trimestre]
                porcentaje = (avance_val / meta_val * 100) if meta_val > 0 else 0
                porcentaje_row[f'{trimestre} 2026'] = f'{porcentaje:.1f}%'
            datos_tabla.append(porcentaje_row)

            df_tabla = pd.DataFrame(datos_tabla)
            st.dataframe(df_tabla.style.apply(aplicar_estilos, axis=1), use_container_width=True, hide_index=True)

        # Tab Publicación
        with tab_publicacion:
            datos_tabla = []

            meta_row = {'Concepto': 'Meta'}
            for trimestre in ['Q1', 'Q2', 'Q3', 'Q4']:
                meta_row[f'{trimestre} 2026'] = metas_hitos['nuevos']['Publicación'][trimestre]
            datos_tabla.append(meta_row)

            avance_row = {'Concepto': 'Completados'}
            for trimestre in ['Q1', 'Q2', 'Q3', 'Q4']:
                avance_row[f'{trimestre} 2026'] = avances_nuevos['Publicación'][trimestre]
            datos_tabla.append(avance_row)

            porcentaje_row = {'Concepto': '% Cumplimiento'}
            for trimestre in ['Q1', 'Q2', 'Q3', 'Q4']:
                meta_val = metas_hitos['nuevos']['Publicación'][trimestre]
                avance_val = avances_nuevos['Publicación'][trimestre]
                porcentaje = (avance_val / meta_val * 100) if meta_val > 0 else 0
                porcentaje_row[f'{trimestre} 2026'] = f'{porcentaje:.1f}%'
            datos_tabla.append(porcentaje_row)

            df_tabla = pd.DataFrame(datos_tabla)
            st.dataframe(df_tabla.style.apply(aplicar_estilos, axis=1), use_container_width=True, hide_index=True)

    with tab2:
        st.markdown("## Registros a ACTUALIZAR")

        # GRÁFICO RESUMEN PRIMERO - SOLO PUBLICACIÓN
        st.markdown("### Gráfico Resumen - Registros Publicados por Trimestre")

        fig = go.Figure()

        # Solo mostrar Publicación
        avances_publicacion = [avances_actualizar['Publicación'][q] for q in ['Q1', 'Q2', 'Q3', 'Q4']]
        metas_publicacion = [metas_hitos['actualizar']['Publicación'][q] for q in ['Q1', 'Q2', 'Q3', 'Q4']]

        # Barras de avance
        fig.add_trace(go.Bar(
            name='Publicados',
            x=['Q1 2026', 'Q2 2026', 'Q3 2026', 'Q4 2026'],
            y=avances_publicacion,
            text=avances_publicacion,
            textposition='auto',
            marker_color='#10B981'
        ))

        # Línea de meta
        fig.add_trace(go.Scatter(
            name='Meta',
            x=['Q1 2026', 'Q2 2026', 'Q3 2026', 'Q4 2026'],
            y=metas_publicacion,
            mode='lines+markers+text',
            text=metas_publicacion,
            textposition='top center',
            line=dict(color='#DC2626', width=2, dash='dash'),
            marker=dict(size=10)
        ))

        fig.update_layout(
            title='Registros Publicados vs Meta por Trimestre - ACTUALIZAR',
            xaxis_title='Trimestre',
            yaxis_title='Cantidad de Registros',
            height=500,
            showlegend=True
        )

        st.plotly_chart(fig, use_container_width=True)

        # TARJETAS POR TRIMESTRE
        st.markdown("---")
        st.markdown("### Detalle por Trimestre")

        for trimestre in ['Q1', 'Q2', 'Q3', 'Q4']:
            mostrar_tarjeta_trimestre(trimestre, avances_actualizar, metas_hitos['actualizar'], registros_df, 'ACTUALIZAR')
            st.markdown("---")

        # DETALLE POR HITO
        st.markdown("---")
        st.markdown("### Detalle por Trimestre y Hito")

        # Aplicar estilos
        def aplicar_estilos(row):
            if row['Concepto'] == 'Meta':
                return ['background-color: #fff3e0'] * len(row)
            elif row['Concepto'] == 'Completados':
                return ['background-color: #e8f5e9'] * len(row)
            elif row['Concepto'] == '% Cumplimiento':
                return ['background-color: #f3e5f5'] * len(row)
            return [''] * len(row)

        # Crear tabs por hito
        tab_acuerdo, tab_analisis, tab_estandares, tab_publicacion = st.tabs([
            "Acuerdo de compromiso",
            "Análisis y cronograma",
            "Estándares",
            "Publicación"
        ])

        # Tab Acuerdo de compromiso
        with tab_acuerdo:
            datos_tabla = []

            meta_row = {'Concepto': 'Meta'}
            for trimestre in ['Q1', 'Q2', 'Q3', 'Q4']:
                meta_row[f'{trimestre} 2026'] = metas_hitos['actualizar']['Acuerdo de compromiso'][trimestre]
            datos_tabla.append(meta_row)

            avance_row = {'Concepto': 'Completados'}
            for trimestre in ['Q1', 'Q2', 'Q3', 'Q4']:
                avance_row[f'{trimestre} 2026'] = avances_actualizar['Acuerdo de compromiso'][trimestre]
            datos_tabla.append(avance_row)

            porcentaje_row = {'Concepto': '% Cumplimiento'}
            for trimestre in ['Q1', 'Q2', 'Q3', 'Q4']:
                meta_val = metas_hitos['actualizar']['Acuerdo de compromiso'][trimestre]
                avance_val = avances_actualizar['Acuerdo de compromiso'][trimestre]
                porcentaje = (avance_val / meta_val * 100) if meta_val > 0 else 0
                porcentaje_row[f'{trimestre} 2026'] = f'{porcentaje:.1f}%'
            datos_tabla.append(porcentaje_row)

            df_tabla = pd.DataFrame(datos_tabla)
            st.dataframe(df_tabla.style.apply(aplicar_estilos, axis=1), use_container_width=True, hide_index=True)

        # Tab Análisis y cronograma
        with tab_analisis:
            datos_tabla = []

            meta_row = {'Concepto': 'Meta'}
            for trimestre in ['Q1', 'Q2', 'Q3', 'Q4']:
                meta_row[f'{trimestre} 2026'] = metas_hitos['actualizar']['Análisis y cronograma'][trimestre]
            datos_tabla.append(meta_row)

            avance_row = {'Concepto': 'Completados'}
            for trimestre in ['Q1', 'Q2', 'Q3', 'Q4']:
                avance_row[f'{trimestre} 2026'] = avances_actualizar['Análisis y cronograma'][trimestre]
            datos_tabla.append(avance_row)

            porcentaje_row = {'Concepto': '% Cumplimiento'}
            for trimestre in ['Q1', 'Q2', 'Q3', 'Q4']:
                meta_val = metas_hitos['actualizar']['Análisis y cronograma'][trimestre]
                avance_val = avances_actualizar['Análisis y cronograma'][trimestre]
                porcentaje = (avance_val / meta_val * 100) if meta_val > 0 else 0
                porcentaje_row[f'{trimestre} 2026'] = f'{porcentaje:.1f}%'
            datos_tabla.append(porcentaje_row)

            df_tabla = pd.DataFrame(datos_tabla)
            st.dataframe(df_tabla.style.apply(aplicar_estilos, axis=1), use_container_width=True, hide_index=True)

        # Tab Estándares
        with tab_estandares:
            datos_tabla = []

            meta_row = {'Concepto': 'Meta'}
            for trimestre in ['Q1', 'Q2', 'Q3', 'Q4']:
                meta_row[f'{trimestre} 2026'] = metas_hitos['actualizar']['Estándares'][trimestre]
            datos_tabla.append(meta_row)

            avance_row = {'Concepto': 'Completados'}
            for trimestre in ['Q1', 'Q2', 'Q3', 'Q4']:
                avance_row[f'{trimestre} 2026'] = avances_actualizar['Estándares'][trimestre]
            datos_tabla.append(avance_row)

            porcentaje_row = {'Concepto': '% Cumplimiento'}
            for trimestre in ['Q1', 'Q2', 'Q3', 'Q4']:
                meta_val = metas_hitos['actualizar']['Estándares'][trimestre]
                avance_val = avances_actualizar['Estándares'][trimestre]
                porcentaje = (avance_val / meta_val * 100) if meta_val > 0 else 0
                porcentaje_row[f'{trimestre} 2026'] = f'{porcentaje:.1f}%'
            datos_tabla.append(porcentaje_row)

            df_tabla = pd.DataFrame(datos_tabla)
            st.dataframe(df_tabla.style.apply(aplicar_estilos, axis=1), use_container_width=True, hide_index=True)

        # Tab Publicación
        with tab_publicacion:
            datos_tabla = []

            meta_row = {'Concepto': 'Meta'}
            for trimestre in ['Q1', 'Q2', 'Q3', 'Q4']:
                meta_row[f'{trimestre} 2026'] = metas_hitos['actualizar']['Publicación'][trimestre]
            datos_tabla.append(meta_row)

            avance_row = {'Concepto': 'Completados'}
            for trimestre in ['Q1', 'Q2', 'Q3', 'Q4']:
                avance_row[f'{trimestre} 2026'] = avances_actualizar['Publicación'][trimestre]
            datos_tabla.append(avance_row)

            porcentaje_row = {'Concepto': '% Cumplimiento'}
            for trimestre in ['Q1', 'Q2', 'Q3', 'Q4']:
                meta_val = metas_hitos['actualizar']['Publicación'][trimestre]
                avance_val = avances_actualizar['Publicación'][trimestre]
                porcentaje = (avance_val / meta_val * 100) if meta_val > 0 else 0
                porcentaje_row[f'{trimestre} 2026'] = f'{porcentaje:.1f}%'
            datos_tabla.append(porcentaje_row)

            df_tabla = pd.DataFrame(datos_tabla)
            st.dataframe(df_tabla.style.apply(aplicar_estilos, axis=1), use_container_width=True, hide_index=True)


if __name__ == "__main__":
    print("Módulo Seguimiento Trimestral - REORGANIZADO: Gráfico primero, tarjetas por trimestre")
