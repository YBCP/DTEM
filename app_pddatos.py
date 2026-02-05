"""
Plan de Datos - Seguimiento
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from sheets_utils import get_sheets_manager

st.set_page_config(page_title="Plan de Datos", layout="wide")

@st.cache_data(ttl=60)
def cargar_datos():
    manager = get_sheets_manager()
    registros_df = manager.leer_hoja('Registros')
    seguimiento_df = manager.leer_hoja('SeguimientoPDD')

    # Filtrar solo registros marcados con 1 en Pddatos
    registros_pdd = registros_df[registros_df['Pddatos'].astype(str).str.strip() == '1'].copy()

    # Extraer fase de la etapa
    seguimiento_df['Fase'] = seguimiento_df['Etapa'].str.extract(r'(Etapa \d+)')[0]

    return registros_pdd, seguimiento_df

st.title("Plan de Datos")

registros_pdd, seguimiento_df = cargar_datos()

# Inicializar session state para filtro de fase
if 'fase_seleccionada' not in st.session_state:
    st.session_state.fase_seleccionada = None

tab1, tab2, tab3 = st.tabs(["Resumen General", "Detalle", "Editor"])

# ========== TAB 1: RESUMEN GENERAL ==========
with tab1:
    st.header("Resumen General")

    # MÉTRICAS GENERALES
    col1, col2 = st.columns(2)

    with col1:
        total_registros = len(registros_pdd)
        st.metric("Registros en Plan de Datos", total_registros)

    with col2:
        total_entidades = registros_pdd['Entidad'].nunique()
        st.metric("Entidades", total_entidades)

    st.markdown("---")

    # DIVIDIR EN DOS COLUMNAS
    col_grafico, col_tarjetas = st.columns(2)

    # ========== COLUMNA IZQUIERDA: GRÁFICO DE BARRAS ==========
    with col_grafico:
        st.subheader("Avance por Etapa")

        # Calcular datos por etapa
        etapas_unicas = seguimiento_df['Etapa'].unique()
        datos_etapas = []

        for etapa in sorted(etapas_unicas):
            datos_etapa = seguimiento_df[seguimiento_df['Etapa'] == etapa]

            # REGLA: "No aplica" no cuenta para el cálculo
            aplicables = datos_etapa[datos_etapa['Estado'] != 'No aplica']
            total_aplicables = len(aplicables)
            completas = len(aplicables[aplicables['Estado'] == 'Completa'])
            pendientes = total_aplicables - completas
            pct = (completas / total_aplicables * 100) if total_aplicables > 0 else 0

            # Extraer nombre y número de etapa
            if 'Etapa 0' in etapa:
                nombre = 'Etapa 0: No requiere acción'
                num_etapa = 0
            elif 'Etapa 1' in etapa:
                nombre = 'Etapa 1: Generar nuevo dato'
                num_etapa = 1
            elif 'Etapa 2' in etapa:
                nombre = 'Etapa 2: Aperturar (abrir) el dato'
                num_etapa = 2
            elif 'Etapa 3' in etapa:
                nombre = 'Etapa 3: Gestionar (procesamiento)'
                num_etapa = 3
            elif 'Etapa 4' in etapa:
                nombre = 'Etapa 4: Archivar / Preservar'
                num_etapa = 4
            elif 'Etapa 5' in etapa:
                nombre = 'Etapa 5: Eliminar'
                num_etapa = 5
            else:
                nombre = etapa
                num_etapa = 0

            datos_etapas.append({
                'Etapa': nombre,
                'NumEtapa': num_etapa,
                'Total': total_aplicables,
                'Completas': completas,
                'Pendientes': pendientes,
                'Porcentaje': pct
            })

        df_etapas = pd.DataFrame(datos_etapas)

        # Crear gráfico de barras horizontales
        fig = go.Figure()

        # Barra completa (gris)
        fig.add_trace(go.Bar(
            y=df_etapas['Etapa'],
            x=[100] * len(df_etapas),
            orientation='h',
            marker=dict(color='#e0e0e0'),
            showlegend=False,
            hoverinfo='skip'
        ))

        # Barra de progreso (todas en azul)
        fig.add_trace(go.Bar(
            y=df_etapas['Etapa'],
            x=df_etapas['Porcentaje'],
            orientation='h',
            marker=dict(
                color='#4a90e2'  # Azul para todas las barras
            ),
            showlegend=False,
            text=[f"{p:.0f}%" for p in df_etapas['Porcentaje']],
            textposition='inside',
            textfont=dict(color='white', size=18, family='Arial'),
            hovertemplate='<b>%{y}</b><br>Avance: %{x:.1f}%<br>Completas: %{customdata[0]}<br>Total: %{customdata[1]}<extra></extra>',
            customdata=df_etapas[['Completas', 'Total']].values
        ))

        fig.update_layout(
            barmode='overlay',
            height=max(300, len(df_etapas) * 80),
            margin=dict(l=20, r=20, t=20, b=20),
            xaxis=dict(
                range=[0, 100],
                showticklabels=False,
                showgrid=False,
                zeroline=False
            ),
            yaxis=dict(
                showgrid=False,
                zeroline=False
            ),
            plot_bgcolor='white',
            paper_bgcolor='white'
        )

        st.plotly_chart(fig, use_container_width=True)

    # ========== COLUMNA DERECHA: TREEMAP POR FASE ==========
    with col_tarjetas:
        st.subheader("Distribución de Registros por Fase")

        # Calcular cantidad de registros por fase
        fases_unicas = sorted(seguimiento_df['Fase'].dropna().unique())
        registros_por_fase = []

        for fase in fases_unicas:
            datos_fase = seguimiento_df[seguimiento_df['Fase'] == fase]
            cod_registros_fase = datos_fase['Cod_Registro'].unique()
            num_registros = len(cod_registros_fase)

            registros_por_fase.append({
                'Fase': fase,
                'Cantidad': num_registros
            })

        df_reg_fase = pd.DataFrame(registros_por_fase)

        # Crear treemap con colores de la imagen
        fig_treemap = px.treemap(
            df_reg_fase,
            path=['Fase'],
            values='Cantidad',
            color='Cantidad',
            color_continuous_scale=[
                '#d4e157',  # Amarillo lima
                '#26a69a',  # Teal
                '#5c6bc0',  # Morado azulado
                '#5e92cf',  # Azul
                '#66bb6a',  # Verde claro
                '#26c6da'   # Verde turquesa
            ],
            title='',
            hover_data={'Cantidad': True}
        )

        fig_treemap.update_traces(
            texttemplate='%{label}<br>%{value}',
            textposition='middle center',
            textfont=dict(size=18, color='white', family='Arial'),
            marker=dict(
                line=dict(width=1, color='white'),
                cornerradius=5
            ),
            hovertemplate='<b>%{label}</b><br>Registros: %{value}<extra></extra>'
        )

        fig_treemap.update_layout(
            height=max(400, len(df_etapas) * 80),
            margin=dict(l=0, r=0, t=0, b=0),
            paper_bgcolor='white',
            plot_bgcolor='white',
            font=dict(color='#333333'),
            coloraxis_showscale=False,  # Ocultar la barra de colores
            treemapcolorway=['#d4e157', '#26a69a', '#5c6bc0', '#5e92cf', '#66bb6a', '#26c6da']
        )

        st.plotly_chart(fig_treemap, use_container_width=True)

        # Botones para filtrar por fase
        st.markdown("**Filtrar por fase:**")
        cols_botones = st.columns(min(3, len(df_reg_fase)))

        for idx, (col, row) in enumerate(zip(cols_botones * ((len(df_reg_fase) // len(cols_botones)) + 1), df_reg_fase.iterrows())):
            if idx >= len(df_reg_fase):
                break
            _, row_data = row
            with col:
                seleccionada = st.session_state.fase_seleccionada == row_data['Fase']
                label = f"✓ {row_data['Fase']}" if seleccionada else row_data['Fase']
                tipo = "secondary" if seleccionada else "primary"

                if st.button(label, key=f"btn_fase_{idx}", use_container_width=True, type=tipo):
                    if seleccionada:
                        st.session_state.fase_seleccionada = None
                    else:
                        st.session_state.fase_seleccionada = row_data['Fase']
                    st.rerun()

    st.markdown("---")

    # FILTROS
    st.subheader("Listado de Registros")

    col_filtro1, col_filtro2, col_filtro3 = st.columns(3)

    with col_filtro1:
        # Obtener entidades que tienen datos en seguimiento
        entidades_con_datos = seguimiento_df['Entidad'].unique()
        entidades_filtradas = sorted([e for e in registros_pdd['Entidad'].unique() if e in entidades_con_datos])
        entidades_opciones = ['Todas'] + entidades_filtradas
        entidad_filtro = st.selectbox("Filtrar por Entidad:", entidades_opciones)

    with col_filtro2:
        # FILTRO EN CASCADA: Solo se activa si hay entidad seleccionada
        if entidad_filtro != 'Todas':
            # Obtener registros de esa entidad
            registros_entidad = registros_pdd[registros_pdd['Entidad'] == entidad_filtro]
            registros_opciones = ['Todos']
            for _, reg in registros_entidad.iterrows():
                cod = reg['Cod']
                nombre = reg['Nivel Información'] if pd.notna(reg['Nivel Información']) else f"Registro {cod}"
                registros_opciones.append(f"[{cod}] {nombre[:50]}")

            registro_filtro = st.selectbox("Filtrar por Registro:", registros_opciones)
        else:
            st.selectbox("Filtrar por Registro:", ['Seleccione primero una entidad'], disabled=True)
            registro_filtro = 'Todos'

    with col_filtro3:
        fases = ['Todas'] + sorted(seguimiento_df['Fase'].dropna().unique().tolist())
        # Si hay fase seleccionada por tarjeta, usarla; si no, usar el selectbox
        if st.session_state.fase_seleccionada:
            fase_filtro_index = fases.index(st.session_state.fase_seleccionada) if st.session_state.fase_seleccionada in fases else 0
        else:
            fase_filtro_index = 0
        fase_filtro = st.selectbox("Filtrar por Fase:", fases, index=fase_filtro_index, disabled=st.session_state.fase_seleccionada is not None)

    # TABLA DE REGISTROS
    datos_tabla = []

    # Usar el filtro de tarjeta si existe, si no usar el selectbox
    fase_filtro_activo = st.session_state.fase_seleccionada if st.session_state.fase_seleccionada else fase_filtro

    # Extraer código de registro si hay filtro
    cod_registro_filtro = None
    if entidad_filtro != 'Todas' and registro_filtro != 'Todos':
        # Extraer código como string (mantener el tipo original)
        cod_registro_filtro = registro_filtro.split(']')[0].replace('[', '').strip()

    for _, reg in registros_pdd.iterrows():
        cod = str(reg['Cod']).strip()  # Asegurar que es string
        nivel_info = reg['Nivel Información'] if pd.notna(reg['Nivel Información']) else f"Registro {cod}"
        entidad = reg['Entidad']

        # Aplicar filtro de entidad
        if entidad_filtro != 'Todas' and entidad != entidad_filtro:
            continue

        # Aplicar filtro de registro
        if cod_registro_filtro is not None and cod != cod_registro_filtro:
            continue

        # Obtener actividades de este registro
        actividades_reg = seguimiento_df[seguimiento_df['Cod_Registro'] == cod].copy()

        # Si no hay actividades, saltar
        if len(actividades_reg) == 0:
            continue

        # Aplicar filtro de fase
        if fase_filtro_activo != 'Todas':
            actividades_reg = actividades_reg[actividades_reg['Fase'] == fase_filtro_activo]
            if len(actividades_reg) == 0:
                continue

        # Una fila por cada actividad del registro
        for _, act in actividades_reg.iterrows():
            datos_tabla.append({
                'Nivel de Información': nivel_info,
                'Entidad': entidad,
                'Fase': act['Fase'] if pd.notna(act['Fase']) else '-',
                'Etapa': act['Etapa'],
                'Subetapa': act['Subetapa'] if pd.notna(act['Subetapa']) and str(act['Subetapa']).strip() != '' else '-',
                'Actividad': act['Actividad'],
                'Estado': act['Estado']
            })

    if datos_tabla:
        df_tabla = pd.DataFrame(datos_tabla)

        # Mostrar filtros activos
        filtros_activos = []
        if fase_filtro_activo != 'Todas':
            filtros_activos.append(f"Fase: {fase_filtro_activo}")
        if entidad_filtro != 'Todas':
            filtros_activos.append(f"Entidad: {entidad_filtro}")
        if cod_registro_filtro is not None:
            filtros_activos.append(f"Registro: {registro_filtro}")

        if filtros_activos:
            st.info(f"Filtros activos: {' | '.join(filtros_activos)}")

        # Mostrar tabla
        st.dataframe(
            df_tabla,
            hide_index=True,
            use_container_width=True,
            height=500
        )

        st.caption(f"Total de filas: {len(df_tabla)}")
    else:
        st.warning("No hay registros que coincidan con los filtros seleccionados")

# ========== TAB 2: DETALLE ==========
with tab2:
    st.header("Detalle por Registro")

    # FILTROS
    col_filtro_det1, col_filtro_det2 = st.columns(2)

    with col_filtro_det1:
        # Filtro por entidad
        entidades_det = ['Todas'] + sorted(registros_pdd['Entidad'].unique().tolist())
        entidad_detalle = st.selectbox("Filtrar por Entidad:", entidades_det, key="entidad_detalle")

    with col_filtro_det2:
        # Buscador por nombre
        busqueda_nombre = st.text_input("Buscar por nombre de registro:", placeholder="Escribe para buscar...", key="busqueda_detalle")

    st.markdown("---")

    # Filtrar registros
    registros_filtrados = registros_pdd.copy()

    if entidad_detalle != 'Todas':
        registros_filtrados = registros_filtrados[registros_filtrados['Entidad'] == entidad_detalle]

    if busqueda_nombre:
        registros_filtrados = registros_filtrados[
            registros_filtrados['Nivel Información'].astype(str).str.contains(busqueda_nombre, case=False, na=False)
        ]

    # Mostrar resultados
    if len(registros_filtrados) == 0:
        st.warning("No se encontraron registros con los filtros aplicados")
    else:
        st.subheader(f"Registros encontrados: {len(registros_filtrados)}")

        # Mostrar cada registro en una tarjeta
        for _, reg in registros_filtrados.iterrows():
            cod = str(reg['Cod']).strip()
            nombre = reg['Nivel Información'] if pd.notna(reg['Nivel Información']) else f"Registro {cod}"
            entidad = reg['Entidad']

            # Obtener datos de seguimiento
            seg_reg = seguimiento_df[seguimiento_df['Cod_Registro'] == cod]

            with st.expander(f"[{cod}] {nombre}", expanded=False):
                # Información básica
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.markdown(f"**Código:** {cod}")
                    st.markdown(f"**Entidad:** {entidad}")

                with col2:
                    if len(seg_reg) > 0:
                        etapa = seg_reg['Etapa'].iloc[0]
                        fase = seg_reg['Fase'].iloc[0] if pd.notna(seg_reg['Fase'].iloc[0]) else 'N/A'
                        st.markdown(f"**Fase:** {fase}")
                        st.markdown(f"**Etapa:** {etapa[:50]}...")

                with col3:
                    if len(seg_reg) > 0:
                        aplicables = len(seg_reg[seg_reg['Estado'] != 'No aplica'])
                        completas = len(seg_reg[seg_reg['Estado'] == 'Completa'])
                        pct = (completas / aplicables * 100) if aplicables > 0 else 0
                        st.metric("Avance", f"{pct:.1f}%")

                # Tabla de actividades
                if len(seg_reg) > 0:
                    st.markdown("---")
                    st.markdown("**Actividades:**")

                    datos_actividades = []
                    for _, act in seg_reg.iterrows():
                        datos_actividades.append({
                            'Subetapa': act['Subetapa'] if pd.notna(act['Subetapa']) and str(act['Subetapa']).strip() != '' else '-',
                            'Actividad': act['Actividad'],
                            'Estado': act['Estado'],
                            'Última actualización': act['Fecha_Actualizacion']
                        })

                    df_actividades = pd.DataFrame(datos_actividades)

                    # Aplicar estilos según estado
                    def colorear_estado(row):
                        if row['Estado'] == 'Completa':
                            return ['background-color: #d4edda'] * len(row)
                        elif row['Estado'] == 'Iniciada':
                            return ['background-color: #fff3cd'] * len(row)
                        elif row['Estado'] == 'Sin iniciar':
                            return ['background-color: #f8d7da'] * len(row)
                        else:
                            return ['background-color: #e2e3e5'] * len(row)

                    st.dataframe(
                        df_actividades.style.apply(colorear_estado, axis=1),
                        hide_index=True,
                        use_container_width=True
                    )
                else:
                    st.info("Este registro no tiene actividades de seguimiento")

# ========== TAB 3: EDITOR (VACÍO) ==========
with tab3:
    st.header("Editor")
    st.info("En construcción")
