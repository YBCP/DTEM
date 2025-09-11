# reportes_simplificado.py - VERSIÓN LIMPIA SIN GRÁFICOS
"""
Módulo de Reportes SIMPLIFICADO:
- Solo métricas generales
- Tabla de datos filtrados
- Descarga Excel/CSV
- Sin gráficos, iconos o información innecesaria
- Filtros corregidos según Google Sheets
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
    """Aplica filtros según los datos de Google Sheets - CORREGIDO para fechas"""
    
    df_filtrado = registros_df.copy()
    
    # Filtro por entidad
    if entidad_reporte != 'Todas':
        df_filtrado = df_filtrado[df_filtrado['Entidad'] == entidad_reporte]
    
    # Filtro por tipo de dato (TipoDato en Google Sheets)
    if tipo_dato_reporte != 'Todos':
        df_filtrado = df_filtrado[df_filtrado['TipoDato'].str.upper() == tipo_dato_reporte.upper()]
    
    # CORREGIDO: Filtro por acuerdo de compromiso - basado en fecha de entrega
    if acuerdo_filtro == 'Completo':
        df_filtrado = df_filtrado[df_filtrado['Entrega acuerdo de compromiso'].apply(es_fecha_valida)]
    elif acuerdo_filtro == 'En proceso':
        df_filtrado = df_filtrado[~df_filtrado['Entrega acuerdo de compromiso'].apply(es_fecha_valida)]
    
    # Filtro por análisis y cronograma - basado en fecha real
    if analisis_filtro == 'Completo':
        df_filtrado = df_filtrado[df_filtrado['Análisis y cronograma'].apply(es_fecha_valida)]
    elif analisis_filtro == 'En proceso':
        df_filtrado = df_filtrado[~df_filtrado['Análisis y cronograma'].apply(es_fecha_valida)]
    
    # Filtro por estándares - basado en fecha real
    if estandares_filtro == 'Completo':
        df_filtrado = df_filtrado[df_filtrado['Estándares'].apply(es_fecha_valida)]
    elif estandares_filtro == 'En proceso':
        df_filtrado = df_filtrado[~df_filtrado['Estándares'].apply(es_fecha_valida)]
    
    # Filtro por publicación - basado en fecha real
    if publicacion_filtro == 'Completo':
        df_filtrado = df_filtrado[df_filtrado['Publicación'].apply(es_fecha_valida)]
    elif publicacion_filtro == 'En proceso':
        df_filtrado = df_filtrado[~df_filtrado['Publicación'].apply(es_fecha_valida)]
    
    # Filtro por estado (finalizado)
    if finalizado_filtro == 'Finalizados':
        df_filtrado = df_filtrado[df_filtrado['Estado'].astype(str).str.upper() == 'COMPLETADO']
    elif finalizado_filtro == 'No finalizados':
        df_filtrado = df_filtrado[df_filtrado['Estado'].astype(str).str.upper() != 'COMPLETADO']
    
    # Filtro por mes proyectado (corregido)
    if mes_filtro != 'Todos':
        meses_nombres = {
            '01': 'Enero', '02': 'Febrero', '03': 'Marzo', '04': 'Abril',
            '05': 'Mayo', '06': 'Junio', '07': 'Julio', '08': 'Agosto',
            '09': 'Septiembre', '10': 'Octubre', '11': 'Noviembre', '12': 'Diciembre'
        }
        mes_nombre = meses_nombres.get(mes_filtro, mes_filtro)
        df_filtrado = df_filtrado[df_filtrado['Mes Proyectado'].astype(str).str.upper() == mes_nombre.upper()]
    
    return df_filtrado

def mostrar_reportes_simplificado(registros_df, entidad_reporte, tipo_dato_reporte,
                                acuerdo_filtro, analisis_filtro, estandares_filtro,
                                publicacion_filtro, finalizado_filtro, mes_filtro):
    """Función principal de reportes simplificada"""
    
    st.markdown('<div class="subtitle">Reportes</div>', unsafe_allow_html=True)
    
    # Verificación de datos
    if registros_df is None or registros_df.empty:
        st.error("No hay datos disponibles para generar reportes")
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
    
    # MÉTRICAS GENERALES
    st.subheader("Métricas Generales")
    
    if df_filtrado.empty:
        st.warning("No hay registros que coincidan con los filtros seleccionados")
        return
    
    total_filtrados = len(df_filtrado)
    avance_promedio = df_filtrado['Porcentaje Avance'].mean()
    completados = len(df_filtrado[df_filtrado['Porcentaje Avance'] == 100])
    sin_avance = len(df_filtrado[df_filtrado['Porcentaje Avance'] == 0])
    # NUEVA MÉTRICA: Publicados
    publicados = len(df_filtrado[df_filtrado['Publicación'].apply(es_fecha_valida)])
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("Total Registros", total_filtrados)
    
    with col2:
        st.metric("Avance Promedio", f"{avance_promedio:.1f}%")
    
    with col3:
        st.metric("Completados", completados)
    
    with col4:
        st.metric("Publicados", publicados)
    
    with col5:
        st.metric("Sin Iniciar", sin_avance)
    
    # TABLA DE REGISTROS
    st.subheader("Registros")
    
    # Seleccionar columnas importantes para mostrar
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
    
    # DESCARGA DE DATOS
    st.subheader("Exportar Datos")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Descargar Excel"):
            try:
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df_filtrado.to_excel(writer, sheet_name='Registros Filtrados', index=False)
                
                excel_data = output.getvalue()
                st.download_button(
                    label="Archivo Excel",
                    data=excel_data,
                    file_name=f"registros_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
                
            except Exception as e:
                st.error(f"Error generando Excel: {str(e)}")
    
    with col2:
        if st.button("Descargar CSV"):
            try:
                csv_data = df_filtrado.to_csv(index=False)
                st.download_button(
                    label="Archivo CSV",
                    data=csv_data,
                    file_name=f"registros_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                    mime="text/csv"
                )
                
            except Exception as e:
                st.error(f"Error generando CSV: {str(e)}")

def mostrar_reportes(registros_df, entidad_reporte, tipo_dato_reporte, 
                    acuerdo_filtro, analisis_filtro, estandares_filtro, 
                    publicacion_filtro, finalizado_filtro, mes_filtro):
    """Función principal compatible con app1.py"""
    
    try:
        mostrar_reportes_simplificado(
            registros_df, entidad_reporte, tipo_dato_reporte,
            acuerdo_filtro, analisis_filtro, estandares_filtro,
            publicacion_filtro, finalizado_filtro, mes_filtro
        )
        
    except Exception as e:
        st.error(f"Error en módulo de reportes: {str(e)}")
        
        # Mostrar datos básicos como respaldo
        if registros_df is not None and not registros_df.empty:
            st.subheader("Vista Básica de Datos")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Registros", len(registros_df))
            
            with col2:
                if 'Porcentaje Avance' in registros_df.columns:
                    avance_promedio = registros_df['Porcentaje Avance'].mean()
                    st.metric("Avance Promedio", f"{avance_promedio:.1f}%")
                else:
                    st.metric("Avance Promedio", "N/A")
            
            with col3:
                if 'Estado' in registros_df.columns:
                    completados = len(registros_df[registros_df['Estado'] == 'Completado'])
                    st.metric("Completados", completados)
                else:
                    st.metric("Completados", "N/A")
            
            st.dataframe(registros_df.head(20))
        else:
            st.warning("No hay datos disponibles para mostrar")

# Función de prueba
def test_reportes_simplificado():
    """Función de test para verificar que el módulo funciona"""
    print("Probando módulo de reportes simplificado...")
    
    # Crear datos de prueba
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
    
    print(f"Datos de prueba creados: {len(df_test)} registros")
    print(f"Columnas disponibles: {list(df_test.columns)}")
    
    return df_test

if __name__ == "__main__":
    print("Módulo de Reportes Simplificado")
    print("Características:")
    print("- Solo métricas generales")
    print("- Tabla de datos filtrados")
    print("- Descarga Excel/CSV")
    print("- Sin gráficos ni iconos")
    print("- Filtros corregidos según Google Sheets")
    
    df_test = test_reportes_simplificado()
    print(f"Test completado: {len(df_test)} registros de prueba")
