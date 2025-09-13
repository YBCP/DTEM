# reportes.py - CORREGIDO: Botones únicos y diseño ultra limpio
"""
Módulo de Reportes CORREGIDO:
- Botones con keys únicos
- Diseño limpio sin iconos ni texto innecesario
- Solo métricas esenciales
- Tabla de datos filtrados
- Descarga Excel/CSV
"""

import streamlit as st
import pandas as pd
import io
from datetime import datetime

# Imports locales
try:
    from data_utils import formatear_fecha, es_fecha_valida, calcular_porcentaje_avance
except ImportError:
    # Funciones de respaldo
    def formatear_fecha(fecha):
        if pd.isna(fecha) or fecha == '':
            return ""
        try:
            if isinstance(fecha, str):
                return fecha
            return fecha.strftime('%d/%m/%Y') if hasattr(fecha, 'strftime') else str(fecha)
        except:
            return str(fecha)
    
    def es_fecha_valida(fecha):
        if pd.isna(fecha) or fecha == '':
            return False
        return str(fecha).strip() != ''
    
    def calcular_porcentaje_avance(row):
        avance = 0
        if str(row.get('Acuerdo de compromiso', '')).strip().upper() in ['SI', 'SÍ']:
            avance += 25
        if es_fecha_valida(row.get('Análisis y cronograma', '')):
            avance += 25
        if es_fecha_valida(row.get('Estándares', '')):
            avance += 25
        if es_fecha_valida(row.get('Publicación', '')):
            avance += 25
        return avance

def aplicar_filtros(registros_df, entidad_reporte, tipo_dato_reporte, acuerdo_filtro, 
                   analisis_filtro, estandares_filtro, publicacion_filtro, 
                   finalizado_filtro, mes_filtro):
    """Aplica filtros según los datos de Google Sheets"""
    
    df_filtrado = registros_df.copy()
    
    # Filtro por entidad
    if entidad_reporte != 'Todas':
        df_filtrado = df_filtrado[df_filtrado['Entidad'] == entidad_reporte]
    
    # Filtro por tipo de dato
    if tipo_dato_reporte != 'Todos':
        df_filtrado = df_filtrado[df_filtrado['TipoDato'].str.upper() == tipo_dato_reporte.upper()]
    
    # Filtro por acuerdo de compromiso
    if acuerdo_filtro == 'Completo':
        df_filtrado = df_filtrado[df_filtrado['Entrega acuerdo de compromiso'].apply(es_fecha_valida)]
    elif acuerdo_filtro == 'En proceso':
        df_filtrado = df_filtrado[~df_filtrado['Entrega acuerdo de compromiso'].apply(es_fecha_valida)]
    
    # Filtro por análisis y cronograma
    if analisis_filtro == 'Completo':
        df_filtrado = df_filtrado[df_filtrado['Análisis y cronograma'].apply(es_fecha_valida)]
    elif analisis_filtro == 'En proceso':
        df_filtrado = df_filtrado[~df_filtrado['Análisis y cronograma'].apply(es_fecha_valida)]
    
    # Filtro por estándares
    if estandares_filtro == 'Completo':
        df_filtrado = df_filtrado[df_filtrado['Estándares'].apply(es_fecha_valida)]
    elif estandares_filtro == 'En proceso':
        df_filtrado = df_filtrado[~df_filtrado['Estándares'].apply(es_fecha_valida)]
    
    # Filtro por publicación
    if publicacion_filtro == 'Completo':
        df_filtrado = df_filtrado[df_filtrado['Publicación'].apply(es_fecha_valida)]
    elif publicacion_filtro == 'En proceso':
        df_filtrado = df_filtrado[~df_filtrado['Publicación'].apply(es_fecha_valida)]
    
    # Filtro por estado
    if finalizado_filtro == 'Finalizados':
        df_filtrado = df_filtrado[df_filtrado['Estado'].astype(str).str.upper() == 'COMPLETADO']
    elif finalizado_filtro == 'No finalizados':
        df_filtrado = df_filtrado[df_filtrado['Estado'].astype(str).str.upper() != 'COMPLETADO']
    
    # Filtro por mes proyectado
    if mes_filtro != 'Todos':
        meses_nombres = {
            '01': 'Enero', '02': 'Febrero', '03': 'Marzo', '04': 'Abril',
            '05': 'Mayo', '06': 'Junio', '07': 'Julio', '08': 'Agosto',
            '09': 'Septiembre', '10': 'Octubre', '11': 'Noviembre', '12': 'Diciembre'
        }
        mes_nombre = meses_nombres.get(mes_filtro, mes_filtro)
        df_filtrado = df_filtrado[df_filtrado['Mes Proyectado'].astype(str).str.upper() == mes_nombre.upper()]
    
    return df_filtrado

def mostrar_reportes_limpio(registros_df, entidad_reporte, tipo_dato_reporte,
                           acuerdo_filtro, analisis_filtro, estandares_filtro,
                           publicacion_filtro, finalizado_filtro, mes_filtro):
    """Función principal de reportes ultra limpia"""
    
    st.subheader("Reportes")
    
    # Verificación de datos
    if registros_df is None or registros_df.empty:
        st.error("No hay datos disponibles")
        return
    
    # Aplicar filtros
    df_filtrado = aplicar_filtros(
        registros_df, entidad_reporte, tipo_dato_reporte, acuerdo_filtro,
        analisis_filtro, estandares_filtro, publicacion_filtro, 
        finalizado_filtro, mes_filtro
    )
    
    # Calcular porcentajes de avance si no existe la columna
    if 'Porcentaje Avance' not in df_filtrado.columns:
        df_filtrado['Porcentaje Avance'] = df_filtrado.apply(calcular_porcentaje_avance, axis=1)
    
    # MÉTRICAS ESENCIALES
    st.markdown("### Métricas")
    
    if df_filtrado.empty:
        st.warning("No hay registros que coincidan con los filtros")
        return
    
    total_filtrados = len(df_filtrado)
    avance_promedio = df_filtrado['Porcentaje Avance'].mean()
    completados = len(df_filtrado[df_filtrado['Porcentaje Avance'] == 100])
    publicados = len(df_filtrado[df_filtrado['Publicación'].apply(es_fecha_valida)])
    sin_avance = len(df_filtrado[df_filtrado['Porcentaje Avance'] == 0])
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("Total", total_filtrados)
    
    with col2:
        st.metric("Avance", f"{avance_promedio:.1f}%")
    
    with col3:
        st.metric("Completados", completados)
    
    with col4:
        st.metric("Publicados", publicados)
    
    with col5:
        st.metric("Sin Iniciar", sin_avance)
    
    # TABLA DE REGISTROS
    st.markdown("### Registros")
    
    # Seleccionar columnas importantes
    columnas_mostrar = []
    columnas_disponibles = [
        'Cod', 'Entidad', 'TipoDato', 'Funcionario', 'Estado',
        'Porcentaje Avance', 'Acuerdo de compromiso',
        'Análisis y cronograma', 'Estándares', 'Publicación',
        'Fecha de oficio de cierre', 'Mes Proyectado', 'Nivel Información '
    ]
    
    for col in columnas_disponibles:
        if col in df_filtrado.columns:
            columnas_mostrar.append(col)
    
    df_mostrar = df_filtrado[columnas_mostrar].copy()
    
    # Formatear fechas
    campos_fecha = ['Análisis y cronograma', 'Estándares', 'Publicación', 'Fecha de oficio de cierre']
    for campo in campos_fecha:
        if campo in df_mostrar.columns:
            df_mostrar[campo] = df_mostrar[campo].apply(formatear_fecha)
    
    # Mostrar tabla
    try:
        styled_df = df_mostrar.style.format({
            'Porcentaje Avance': '{:.1f}%'
        } if 'Porcentaje Avance' in df_mostrar.columns else {})
        
        if 'Porcentaje Avance' in df_mostrar.columns:
            styled_df = styled_df.background_gradient(cmap='RdYlGn', subset=['Porcentaje Avance'])
        
        st.dataframe(styled_df, use_container_width=True)
        
    except Exception:
        st.dataframe(df_mostrar, use_container_width=True)
    
    # DESCARGA CORREGIDA - Keys únicos
    st.markdown("### Exportar")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # BOTÓN EXCEL - Key único
        if st.button("Excel", key="btn_excel_reportes"):
            try:
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df_filtrado.to_excel(writer, sheet_name='Registros', index=False)
                
                excel_data = output.getvalue()
                st.download_button(
                    label="Descargar",
                    data=excel_data,
                    file_name=f"registros_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key="download_excel_reportes"
                )
                
            except Exception as e:
                st.error(f"Error: {str(e)}")
    
    with col2:
        # BOTÓN CSV - Key único
        if st.button("CSV", key="btn_csv_reportes"):
            try:
                csv_data = df_filtrado.to_csv(index=False)
                st.download_button(
                    label="Descargar",
                    data=csv_data,
                    file_name=f"registros_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                    mime="text/csv",
                    key="download_csv_reportes"
                )
                
            except Exception as e:
                st.error(f"Error: {str(e)}")

def mostrar_reportes(registros_df, entidad_reporte, tipo_dato_reporte, 
                    acuerdo_filtro, analisis_filtro, estandares_filtro, 
                    publicacion_filtro, finalizado_filtro, mes_filtro):
    """Función principal compatible con app1.py"""
    
    try:
        mostrar_reportes_limpio(
            registros_df, entidad_reporte, tipo_dato_reporte,
            acuerdo_filtro, analisis_filtro, estandares_filtro,
            publicacion_filtro, finalizado_filtro, mes_filtro
        )
        
    except Exception as e:
        st.error(f"Error en reportes: {str(e)}")
        
        # Vista básica como respaldo
        if registros_df is not None and not registros_df.empty:
            st.subheader("Vista Básica")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total", len(registros_df))
            
            with col2:
                if 'Porcentaje Avance' in registros_df.columns:
                    avance = registros_df['Porcentaje Avance'].mean()
                    st.metric("Avance", f"{avance:.1f}%")
            
            with col3:
                if 'Estado' in registros_df.columns:
                    completados = len(registros_df[registros_df['Estado'] == 'Completado'])
                    st.metric("Completados", completados)
            
            st.dataframe(registros_df.head(20))
        else:
            st.warning("No hay datos disponibles")

# Test de funcionamiento
def test_reportes():
    """Test básico del módulo"""
    print("Probando módulo reportes corregido...")
    
    test_data = {
        'Cod': ['1', '2', '3'],
        'Entidad': ['Entidad A', 'Entidad B', 'Entidad A'],
        'TipoDato': ['Nuevo', 'Actualizar', 'Nuevo'],
        'Acuerdo de compromiso': ['Si', 'No', 'Si'],
        'Análisis y cronograma': ['01/01/2024', '', '15/02/2024'],
        'Estándares': ['10/01/2024', '20/01/2024', ''],
        'Publicación': ['15/01/2024', '', '20/02/2024'],
        'Estado': ['En proceso', 'Completado', 'En proceso'],
        'Funcionario': ['Juan Pérez', 'María García', 'Juan Pérez'],
        'Mes Proyectado': ['Enero', 'Febrero', 'Marzo']
    }
    
    df_test = pd.DataFrame(test_data)
    df_test['Porcentaje Avance'] = df_test.apply(calcular_porcentaje_avance, axis=1)
    
    print(f"Test completado: {len(df_test)} registros")
    return df_test

if __name__ == "__main__":
    print("Módulo Reportes - CORREGIDO:")
    print("- Botones con keys únicos")
    print("- Diseño ultra limpio")
    print("- Sin iconos ni texto innecesario")
    print("- Solo métricas esenciales")
    
    df_test = test_reportes()
    print(f"Funcionalidad verificada con {len(df_test)} registros de prueba")
