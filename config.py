# config.py - Configuración limpia sin iconos ni elementos innecesarios

import streamlit as st

def setup_page():
    """Configura la página de Streamlit."""
    st.set_page_config(
        page_title="Tablero de Control Datos Temáticos - Ideca",
        page_icon="📊",
        layout="wide"
    )


def load_css():
    """Carga estilos CSS personalizados limpios."""
    st.markdown("""
    <style>
    /* Estilos base limpios */
    .title {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1E40AF;
        margin-bottom: 1rem;
        text-align: center;
    }

    .subtitle {
        font-size: 1.5rem;
        font-weight: bold;
        color: #1E40AF;
        margin-top: 1.5rem;
        margin-bottom: 1rem;
        border-bottom: 2px solid #E5E7EB;
        padding-bottom: 0.5rem;
    }

    /* Métricas limpias */
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #E5E7EB;
        margin-bottom: 1rem;
        text-align: center;
    }

    /* Alertas limpias */
    .alert-card {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
    }

    .alert-vencido {
        background-color: #fee2e2;
        border-left: 4px solid #b91c1c;
    }

    .alert-proximo {
        background-color: #fef3c7;
        border-left: 4px solid #b45309;
    }

    .alert-retraso {
        background-color: #dbeafe;
        border-left: 4px solid #1e40af;
    }

    /* Estados simples */
    .estado-badge {
        display: inline-block;
        padding: 0.25rem 0.5rem;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: bold;
    }

    .estado-vencido {
        background-color: #fee2e2;
        color: #b91c1c;
    }

    .estado-proximo {
        background-color: #fef3c7;
        color: #b45309;
    }

    .estado-retraso {
        background-color: #dbeafe;
        color: #1e40af;
    }

    /* Tablas limpias */
    .stDataFrame {
        margin-bottom: 2rem;
    }

    /* Días de rezago visibles */
    .dias-rezago-positivo {
        color: #b91c1c;
        font-weight: bold;
    }

    .dias-rezago-negativo {
        color: #047857;
        font-weight: bold;
    }

    /* Botones limpios */
    .stButton > button {
        border-radius: 0.5rem;
        border: none;
        font-weight: 500;
    }

    /* Sidebar limpio */
    .css-1d391kg {
        background-color: #f8fafc;
    }

    /* Remover elementos innecesarios */
    .css-1rs6os {
        display: none;
    }

    /* Footer limpio */
    footer {
        visibility: hidden;
    }

    /* Headers limpios */
    h1, h2, h3 {
        color: #1E40AF;
        font-weight: 600;
    }

    /* Inputs limpios */
    .stSelectbox, .stTextInput, .stDateInput {
        margin-bottom: 1rem;
    }

    /* Expanders limpios */
    .streamlit-expanderHeader {
        background-color: #f8fafc;
        border-radius: 0.5rem;
    }

    /* Tabs limpios */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
    }

    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #f8fafc;
        border-radius: 4px 4px 0px 0px;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
    }

    .stTabs [aria-selected="true"] {
        background-color: #1E40AF;
        color: white;
    }

    /* Containers limpios */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }

    /* Spinner limpio */
    .stSpinner {
        text-align: center;
    }

    /* Progress bars limpios */
    .stProgress > div > div > div > div {
        background-color: #1E40AF;
    }
    </style>
    """, unsafe_allow_html=True)
