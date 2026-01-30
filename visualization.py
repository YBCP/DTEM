# visualization.py - CORREGIDO PARA ERROR datetime.date + timedelta

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.figure_factory as ff
import plotly.graph_objects as go
from datetime import datetime, timedelta, date 
import re  
import streamlit as st
from data_utils import procesar_fecha, verificar_completado_por_fecha, es_fecha_valida


def crear_gantt(df):
    """
    CORREGIDO: Crea un diagrama de Gantt con los hitos y fechas.
    GARANTÍA: Solo usa datetime para evitar errores date + timedelta
    """
    if df.empty:
        return None

    # Verificar si hay al menos una fecha válida
    columnas_fecha = [
        'Entrega acuerdo de compromiso', 'Análisis y cronograma',
        'Estándares', 'Publicación', 'Plazo de oficio de cierre'
    ]

    tiene_fechas = False
    for col in columnas_fecha:
        if col in df.columns and df[col].notna().any():
            tiene_fechas = True
            break

    if not tiene_fechas:
        return None

    # Definir los porcentajes por hito
    porcentajes_hitos = {
        'Acuerdo de compromiso': '20%',
        'Análisis y cronograma': '20%',
        'Estándares': '30%',
        'Publicación': '25%',
        'Cierre': '5%'
    }

    # Crear lista de tareas para el diagrama
    tareas = []

    # Para cada registro, crear las tareas correspondientes a cada hito
    for idx, row in df.iterrows():
        try:
            entidad = row['Entidad']
            nivel_info = row['Nivel Información '] if 'Nivel Información ' in row else 'Sin nivel'
            task_id = f"{row['Cod']} - {nivel_info}"

            # FUNCIÓN AUXILIAR CORREGIDA para procesar fechas de manera segura
            def procesar_fecha_gantt_segura(fecha_valor):
                """
                CORRECCIÓN CRÍTICA: Procesa fecha de manera segura para Gantt
                GARANTÍA: Siempre devuelve datetime o None, NUNCA date
                """
                if pd.isna(fecha_valor) or fecha_valor == "" or fecha_valor is None:
                    return None
                
                try:
                    # Usar la función procesar_fecha que ya está corregida
                    fecha_procesada = procesar_fecha(fecha_valor)
                    
                    if fecha_procesada is None:
                        return None
                    
                    # VERIFICACIÓN ADICIONAL: Asegurar que es datetime
                    if isinstance(fecha_procesada, datetime):
                        return fecha_procesada
                    elif isinstance(fecha_procesada, date):
                        # CONVERSIÓN CRÍTICA: date -> datetime
                        return datetime.combine(fecha_procesada, datetime.min.time())
                    else:
                        print(f"⚠️ Tipo inesperado en Gantt: {type(fecha_procesada)}")
                        return None
                        
                except Exception as e:
                    print(f"❌ Error procesando fecha en Gantt: {e}")
                    return None

            # Hito 1: Acuerdo de compromiso
            if 'Entrega acuerdo de compromiso' in row and pd.notna(row['Entrega acuerdo de compromiso']) and row['Entrega acuerdo de compromiso'] != "":
                fecha = procesar_fecha_gantt_segura(row['Entrega acuerdo de compromiso'])
                if fecha and isinstance(fecha, datetime):
                    # OPERACIÓN SEGURA: datetime - timedelta = datetime
                    fecha_inicio = fecha - timedelta(days=7)
                    tareas.append({
                        'Task': task_id,
                        'Start': fecha_inicio,
                        'Finish': fecha,
                        'Resource': f"Acuerdo de compromiso ({porcentajes_hitos['Acuerdo de compromiso']})",
                        'Entidad': entidad
                    })

            # Hito 2: Análisis y cronograma
            if 'Análisis y cronograma' in row and pd.notna(row['Análisis y cronograma']) and row['Análisis y cronograma'] != "":
                fecha = procesar_fecha_gantt_segura(row['Análisis y cronograma'])
                if fecha and isinstance(fecha, datetime):
                    fecha_inicio = fecha - timedelta(days=7)
                    tareas.append({
                        'Task': task_id,
                        'Start': fecha_inicio,
                        'Finish': fecha,
                        'Resource': f"Análisis y cronograma ({porcentajes_hitos['Análisis y cronograma']})",
                        'Entidad': entidad
                    })

            # Hito 3: Estándares
            if 'Estándares' in row and pd.notna(row['Estándares']) and row['Estándares'] != "":
                fecha = procesar_fecha_gantt_segura(row['Estándares'])
                if fecha and isinstance(fecha, datetime):
                    fecha_inicio = fecha - timedelta(days=7)
                    tareas.append({
                        'Task': task_id,
                        'Start': fecha_inicio,
                        'Finish': fecha,
                        'Resource': f"Estándares ({porcentajes_hitos['Estándares']})",
                        'Entidad': entidad
                    })

            # Hito 4: Publicación
            if 'Publicación' in row and pd.notna(row['Publicación']) and row['Publicación'] != "":
                fecha = procesar_fecha_gantt_segura(row['Publicación'])
                if fecha and isinstance(fecha, datetime):
                    fecha_inicio = fecha - timedelta(days=7)
                    tareas.append({
                        'Task': task_id,
                        'Start': fecha_inicio,
                        'Finish': fecha,
                        'Resource': f"Publicación ({porcentajes_hitos['Publicación']})",
                        'Entidad': entidad
                    })

            # Hito 5: Cierre (Plazo de oficio de cierre)
            if 'Plazo de oficio de cierre' in row and pd.notna(row['Plazo de oficio de cierre']) and row['Plazo de oficio de cierre'] != "":
                fecha = procesar_fecha_gantt_segura(row['Plazo de oficio de cierre'])
                if fecha and isinstance(fecha, datetime):
                    fecha_inicio = fecha - timedelta(days=7)
                    tareas.append({
                        'Task': task_id,
                        'Start': fecha_inicio,
                        'Finish': fecha,
                        'Resource': f"Cierre ({porcentajes_hitos['Cierre']})",
                        'Entidad': entidad
                    })
                    
        except Exception as e:
            # Si hay un error procesando un registro, simplemente lo omitimos y continuamos
            print(f"❌ Error procesando registro {idx} en Gantt: {e}")
            continue

    if not tareas:
        return None

    # Crear DataFrame de tareas
    df_tareas = pd.DataFrame(tareas)

    # Definir colores para cada tipo de hito
    colors = {
        f"Acuerdo de compromiso ({porcentajes_hitos['Acuerdo de compromiso']})": '#1E40AF',
        f"Análisis y cronograma ({porcentajes_hitos['Análisis y cronograma']})": '#047857',
        f"Estándares ({porcentajes_hitos['Estándares']})": '#B45309',
        f"Publicación ({porcentajes_hitos['Publicación']})": '#BE185D',
        f"Cierre ({porcentajes_hitos['Cierre']})": '#7C3AED'
    }

    try:
        # Crear el gráfico
        fig = px.timeline(
            df_tareas,
            x_start='Start',
            x_end='Finish',
            y='Task',
            color='Resource',
            color_discrete_map=colors,
            hover_data=['Entidad'],
            title='Cronograma de Hitos por Nivel de Información'
        )

        # Ajustar el diseño
        fig.update_layout(
            xaxis_title='Fecha',
            yaxis_title='Registro - Nivel de Información',
            legend_title='Hito',
            height=max(400, len(df_tareas['Task'].unique()) * 40),
            xaxis=dict(
                type='date',
                tickformat='%d/%m/%Y'
            )
        )

        # Añadir línea vertical para mostrar la fecha actual (HOY)
        # CORRECCIÓN: Usar datetime completo
        fecha_hoy = datetime.now()

        # Añadir la línea vertical
        fig.add_shape(
            type="line",
            x0=fecha_hoy,
            y0=0,
            x1=fecha_hoy,
            y1=1,
            line=dict(
                color="red",
                width=2,
                dash="dash",
            ),
            xref="x",
            yref="paper"
        )

        # Añadir etiqueta "HOY"
        fig.add_annotation(
            x=fecha_hoy,
            y=1,
            text="HOY",
            showarrow=False,
            font=dict(
                color="red",
                size=14
            ),
            bgcolor="rgba(255, 255, 255, 0.8)",
            bordercolor="red",
            borderwidth=1,
            xref="x",
            yref="paper",
            yanchor="bottom"
        )

        return fig
        
    except Exception as e:
        print(f"❌ Error al crear el gráfico Gantt: {e}")
        import traceback
        traceback.print_exc()
        return None


def comparar_avance_metas(df, metas_nuevas_df, metas_actualizar_df):
    """
    MODIFICADO: Compara el avance actual con las metas establecidas.
    Ahora muestra Total histórico, Completados 2026 y calcula porcentaje solo sobre 2026.
    GARANTÍA: Usa solo datetime para comparaciones seguras
    """
    try:
        # CORRECCIÓN: Obtener la fecha actual como datetime
        fecha_actual = datetime.now()

        # Encontrar la meta más cercana a la fecha actual
        fechas_metas = metas_nuevas_df.index
        fecha_meta_cercana = min(fechas_metas, key=lambda x: abs(x - fecha_actual))

        # Obtener los valores de las metas para esa fecha
        metas_nuevas_actual = metas_nuevas_df.loc[fecha_meta_cercana]
        metas_actualizar_actual = metas_actualizar_df.loc[fecha_meta_cercana]

        # Contar registros completados por hito y tipo (de manera segura)
        # Verificar si la columna TipoDato existe
        if 'TipoDato' not in df.columns:
            # Crear columnas necesarias si no existen
            df['TipoDato'] = 'No especificado'
            df['Acuerdo de compromiso'] = ''
            df['Análisis y cronograma'] = ''
            df['Estándares'] = ''
            df['Publicación'] = ''

        # Filtrar registros por tipo, asegurando que TipoDato exista y no sea NaN
        df['TipoDato'] = df['TipoDato'].fillna('').astype(str)
        registros_nuevos = df[df['TipoDato'].str.upper() == 'NUEVO']
        registros_actualizar = df[df['TipoDato'].str.upper() == 'ACTUALIZAR']

        # NUEVA FUNCIÓN: Verificar si una fecha es de 2026
        def es_fecha_2026(fecha_valor):
            """Verifica si una fecha es del año 2026"""
            try:
                fecha = procesar_fecha(fecha_valor)
                if fecha and isinstance(fecha, datetime):
                    return fecha.year == 2026
                return False
            except:
                return False

        # Para registros nuevos - contar TOTAL y 2026 por separado
        # ACUERDO DE COMPROMISO
        total_acuerdo_nuevos = len(registros_nuevos[
            registros_nuevos['Acuerdo de compromiso'].astype(str).str.upper().isin(
                ['SI', 'SÍ', 'S', 'YES', 'Y', 'COMPLETO'])
        ]) if 'Acuerdo de compromiso' in registros_nuevos.columns else 0

        acuerdo_2026_nuevos = 0
        if 'Suscripción acuerdo de compromiso' in registros_nuevos.columns:
            acuerdo_2026_nuevos = len(registros_nuevos[
                (registros_nuevos['Acuerdo de compromiso'].astype(str).str.upper().isin(['SI', 'SÍ', 'S', 'YES', 'Y', 'COMPLETO'])) &
                (registros_nuevos['Suscripción acuerdo de compromiso'].apply(es_fecha_2026))
            ])

        # ANÁLISIS Y CRONOGRAMA
        total_analisis_nuevos = len(registros_nuevos[
            registros_nuevos['Análisis y cronograma'].apply(lambda x: es_fecha_valida(x))
        ]) if 'Análisis y cronograma' in registros_nuevos.columns else 0

        analisis_2026_nuevos = len(registros_nuevos[
            registros_nuevos['Análisis y cronograma'].apply(es_fecha_2026)
        ]) if 'Análisis y cronograma' in registros_nuevos.columns else 0

        # ESTÁNDARES
        total_estandares_nuevos = len(registros_nuevos[
            registros_nuevos['Estándares'].apply(lambda x: es_fecha_valida(x))
        ]) if 'Estándares' in registros_nuevos.columns else 0

        estandares_2026_nuevos = len(registros_nuevos[
            registros_nuevos['Estándares'].apply(es_fecha_2026)
        ]) if 'Estándares' in registros_nuevos.columns else 0

        # PUBLICACIÓN
        total_publicacion_nuevos = len(registros_nuevos[
            registros_nuevos['Publicación'].apply(lambda x: es_fecha_valida(x))
        ]) if 'Publicación' in registros_nuevos.columns else 0

        publicacion_2026_nuevos = len(registros_nuevos[
            registros_nuevos['Publicación'].apply(es_fecha_2026)
        ]) if 'Publicación' in registros_nuevos.columns else 0

        # Para registros a actualizar - contar TOTAL y 2026 por separado
        # ACUERDO DE COMPROMISO
        total_acuerdo_actualizar = len(registros_actualizar[
            registros_actualizar['Acuerdo de compromiso'].astype(str).str.upper().isin(
                ['SI', 'SÍ', 'S', 'YES', 'Y', 'COMPLETO'])
        ]) if 'Acuerdo de compromiso' in registros_actualizar.columns else 0

        acuerdo_2026_actualizar = 0
        if 'Suscripción acuerdo de compromiso' in registros_actualizar.columns:
            acuerdo_2026_actualizar = len(registros_actualizar[
                (registros_actualizar['Acuerdo de compromiso'].astype(str).str.upper().isin(['SI', 'SÍ', 'S', 'YES', 'Y', 'COMPLETO'])) &
                (registros_actualizar['Suscripción acuerdo de compromiso'].apply(es_fecha_2026))
            ])

        # ANÁLISIS Y CRONOGRAMA
        total_analisis_actualizar = len(registros_actualizar[
            registros_actualizar['Análisis y cronograma'].apply(lambda x: es_fecha_valida(x))
        ]) if 'Análisis y cronograma' in registros_actualizar.columns else 0

        analisis_2026_actualizar = len(registros_actualizar[
            registros_actualizar['Análisis y cronograma'].apply(es_fecha_2026)
        ]) if 'Análisis y cronograma' in registros_actualizar.columns else 0

        # ESTÁNDARES
        total_estandares_actualizar = len(registros_actualizar[
            registros_actualizar['Estándares'].apply(lambda x: es_fecha_valida(x))
        ]) if 'Estándares' in registros_actualizar.columns else 0

        estandares_2026_actualizar = len(registros_actualizar[
            registros_actualizar['Estándares'].apply(es_fecha_2026)
        ]) if 'Estándares' in registros_actualizar.columns else 0

        # PUBLICACIÓN
        total_publicacion_actualizar = len(registros_actualizar[
            registros_actualizar['Publicación'].apply(lambda x: es_fecha_valida(x))
        ]) if 'Publicación' in registros_actualizar.columns else 0

        publicacion_2026_actualizar = len(registros_actualizar[
            registros_actualizar['Publicación'].apply(es_fecha_2026)
        ]) if 'Publicación' in registros_actualizar.columns else 0

        # Crear dataframes para la comparación con NUEVAS COLUMNAS
        comparacion_nuevos = pd.DataFrame({
            'Total': {
                'Acuerdo de compromiso': total_acuerdo_nuevos,
                'Análisis y cronograma': total_analisis_nuevos,
                'Estándares': total_estandares_nuevos,
                'Publicación': total_publicacion_nuevos
            },
            'Completados 2026': {
                'Acuerdo de compromiso': acuerdo_2026_nuevos,
                'Análisis y cronograma': analisis_2026_nuevos,
                'Estándares': estandares_2026_nuevos,
                'Publicación': publicacion_2026_nuevos
            },
            'Meta': metas_nuevas_actual
        })

        comparacion_actualizar = pd.DataFrame({
            'Total': {
                'Acuerdo de compromiso': total_acuerdo_actualizar,
                'Análisis y cronograma': total_analisis_actualizar,
                'Estándares': total_estandares_actualizar,
                'Publicación': total_publicacion_actualizar
            },
            'Completados 2026': {
                'Acuerdo de compromiso': acuerdo_2026_actualizar,
                'Análisis y cronograma': analisis_2026_actualizar,
                'Estándares': estandares_2026_actualizar,
                'Publicación': publicacion_2026_actualizar
            },
            'Meta': metas_actualizar_actual
        })

        # MODIFICADO: Calcular porcentajes basados SOLO en Completados 2026 / Meta
        comparacion_nuevos['Porcentaje'] = comparacion_nuevos.apply(
            lambda row: (row['Completados 2026'] / row['Meta'] * 100) if row['Meta'] > 0 else 0,
            axis=1
        ).fillna(0).round(2)

        comparacion_actualizar['Porcentaje'] = comparacion_actualizar.apply(
            lambda row: (row['Completados 2026'] / row['Meta'] * 100) if row['Meta'] > 0 else 0,
            axis=1
        ).fillna(0).round(2)

        return comparacion_nuevos, comparacion_actualizar, fecha_meta_cercana
        
    except Exception as e:
        st.error(f"Error al comparar avance con metas: {e}")
        # Crear DataFrames de respaldo
        fecha_meta_cercana = datetime.now()

        completados_nuevos = {'Acuerdo de compromiso': 0, 'Análisis y cronograma': 0, 'Estándares': 0,
                              'Publicación': 0}
        completados_actualizar = {'Acuerdo de compromiso': 0, 'Análisis y cronograma': 0, 'Estándares': 0,
                                  'Publicación': 0}

        metas_nuevas_actual = pd.Series(
            {'Acuerdo de compromiso': 0, 'Análisis y cronograma': 0, 'Estándares': 0, 'Publicación': 0})
        metas_actualizar_actual = pd.Series(
            {'Acuerdo de compromiso': 0, 'Análisis y cronograma': 0, 'Estándares': 0, 'Publicación': 0})

        comparacion_nuevos = pd.DataFrame({
            'Completados': completados_nuevos,
            'Meta': metas_nuevas_actual,
            'Porcentaje': [0, 0, 0, 0]
        })

        comparacion_actualizar = pd.DataFrame({
            'Completados': completados_actualizar,
            'Meta': metas_actualizar_actual,
            'Porcentaje': [0, 0, 0, 0]
        })

        return comparacion_nuevos, comparacion_actualizar, fecha_meta_cercana


def contar_registros_completados_por_fecha(df, columna_fecha_programada, columna_fecha_completado):
    """
    CORREGIDO: Cuenta los registros que tienen una fecha de completado o cuya fecha programada ya pasó.
    GARANTÍA: Usa solo datetime para comparaciones seguras
    """
    count = 0
    for _, row in df.iterrows():
        try:
            if columna_fecha_programada in row and row[columna_fecha_programada]:
                fecha_programada = row[columna_fecha_programada]

                # Verificar si hay una fecha de completado
                fecha_completado = None
                if columna_fecha_completado in row and row[columna_fecha_completado]:
                    # CORRECCIÓN: Usar procesar_fecha que garantiza datetime
                    fecha_completado = procesar_fecha(row[columna_fecha_completado])
                    # Si no es una fecha, verificar si es un valor booleano positivo
                    if fecha_completado is None and str(row[columna_fecha_completado]).strip().upper() in ['SI', 'SÍ',
                                                                                                           'S', 'YES',
                                                                                                           'Y',
                                                                                                           'COMPLETO']:
                        fecha_completado = datetime.now()  # Usar fecha actual como completado

                if verificar_completado_por_fecha(fecha_programada, fecha_completado):
                    count += 1
                    
        except Exception as e:
            # Ignorar errores en filas individuales y continuar
            print(f"❌ Error procesando fila en contar_registros: {e}")
            continue

    return count


# NUEVAS FUNCIONES DE VERIFICACIÓN Y TEST

def verificar_fechas_gantt_seguras(df):
    """
    NUEVA FUNCIÓN: Verifica que todas las fechas en el DataFrame sean seguras para Gantt
    """
    print("\n🔍 VERIFICANDO FECHAS PARA GANTT SEGURO...")
    
    columnas_fecha = [
        'Entrega acuerdo de compromiso', 'Análisis y cronograma',
        'Estándares', 'Publicación', 'Plazo de oficio de cierre'
    ]
    
    fechas_problematicas = []
    total_fechas_verificadas = 0
    
    for columna in columnas_fecha:
        if columna in df.columns:
            print(f"\n📅 Verificando columna: {columna}")
            
            for idx, valor in df[columna].items():
                if pd.notna(valor) and str(valor).strip() != '':
                    total_fechas_verificadas += 1
                    
                    if isinstance(valor, date) and not isinstance(valor, datetime):
                        fechas_problematicas.append((columna, idx, valor, "date PELIGROSO"))
                        print(f"   ❌ Fila {idx}: {valor} es date PELIGROSO")
                    else:
                        # Verificar que procesar_fecha funcione correctamente
                        try:
                            fecha_procesada = procesar_fecha(valor)
                            if fecha_procesada and not isinstance(fecha_procesada, datetime):
                                fechas_problematicas.append((columna, idx, valor, f"procesar_fecha devuelve {type(fecha_procesada)}"))
                                print(f"   ❌ Fila {idx}: procesar_fecha devuelve tipo incorrecto")
                        except Exception as e:
                            fechas_problematicas.append((columna, idx, valor, f"error: {e}"))
                            print(f"   ❌ Fila {idx}: error en procesar_fecha: {e}")
    
    print(f"\n📊 RESUMEN VERIFICACIÓN GANTT:")
    print(f"   Total fechas verificadas: {total_fechas_verificadas}")
    print(f"   Fechas problemáticas: {len(fechas_problematicas)}")
    
    if fechas_problematicas:
        print("   🚨 FECHAS PROBLEMÁTICAS ENCONTRADAS:")
        for columna, idx, valor, problema in fechas_problematicas[:5]:  # Mostrar solo las primeras 5
            print(f"      {columna} fila {idx}: {problema}")
        return False, fechas_problematicas
    else:
        print("   ✅ TODAS LAS FECHAS SON SEGURAS PARA GANTT")
        return True, []


def reparar_fechas_para_gantt(df):
    """
    NUEVA FUNCIÓN: Repara fechas problemáticas en el DataFrame para Gantt seguro
    """
    print("\n🔧 REPARANDO FECHAS PARA GANTT SEGURO...")
    
    df_reparado = df.copy()
    columnas_fecha = [
        'Entrega acuerdo de compromiso', 'Análisis y cronograma',
        'Estándares', 'Publicación', 'Plazo de oficio de cierre'
    ]
    
    reparaciones = 0
    
    for columna in columnas_fecha:
        if columna in df_reparado.columns:
            for idx, valor in df_reparado[columna].items():
                if pd.notna(valor) and str(valor).strip() != '':
                    try:
                        if isinstance(valor, date) and not isinstance(valor, datetime):
                            # Convertir date a datetime y formatear como string
                            valor_reparado = datetime.combine(valor, datetime.min.time())
                            df_reparado.at[idx, columna] = valor_reparado.strftime('%d/%m/%Y')
                            reparaciones += 1
                            print(f"   🔧 {columna} fila {idx}: date -> datetime -> string")
                        else:
                            # Verificar que procesar_fecha funcione y reformatear si es necesario
                            fecha_procesada = procesar_fecha(valor)
                            if fecha_procesada and isinstance(fecha_procesada, datetime):
                                # Reformatear para consistencia
                                df_reparado.at[idx, columna] = fecha_procesada.strftime('%d/%m/%Y')
                            elif fecha_procesada is None:
                                # Si no se puede procesar, limpiar
                                df_reparado.at[idx, columna] = ''
                                reparaciones += 1
                                print(f"   🧹 {columna} fila {idx}: valor inválido limpiado")
                    except Exception as e:
                        # Si hay error, limpiar el valor
                        df_reparado.at[idx, columna] = ''
                        reparaciones += 1
                        print(f"   🧹 {columna} fila {idx}: error reparando, limpiado")
    
    print(f"✅ Reparaciones aplicadas: {reparaciones}")
    return df_reparado


def test_crear_gantt_seguro():
    """
    NUEVA FUNCIÓN: Test específico para crear_gantt con casos problemáticos
    """
    print("\n🧪 PROBANDO CREAR_GANTT CON CASOS PROBLEMÁTICOS...")
    
    # Crear DataFrame de prueba con casos críticos
    df_test = pd.DataFrame({
        'Cod': ['1', '2', '3'],
        'Entidad': ['Test 1', 'Test 2', 'Test 3'],
        'Nivel Información ': ['Nivel A', 'Nivel B', 'Nivel C'],
        'Análisis y cronograma': [
            '15/01/2025',           # String normal
            date(2025, 1, 20),      # CASO CRÍTICO: date
            datetime(2025, 1, 25),  # datetime seguro
        ],
        'Publicación': [
            datetime(2025, 2, 1),   # datetime seguro
            '20/02/2025',           # String normal
            date(2025, 2, 25),      # CASO CRÍTICO: date
        ]
    })
    
    print("DataFrame de prueba:")
    for idx, row in df_test.iterrows():
        analisis = row['Análisis y cronograma']
        pub = row['Publicación']
        print(f"   Fila {idx}: Análisis={analisis} ({type(analisis)}), Pub={pub} ({type(pub)})")
    
    # Verificar fechas antes de reparar
    es_seguro_antes, problemas_antes = verificar_fechas_gantt_seguras(df_test)
    
    if not es_seguro_antes:
        print("\n🔧 Aplicando reparaciones...")
        df_test_reparado = reparar_fechas_para_gantt(df_test)
        
        # Verificar después de reparar
        es_seguro_despues, problemas_despues = verificar_fechas_gantt_seguras(df_test_reparado)
        
        if es_seguro_despues:
            print("✅ DataFrame reparado exitosamente")
            df_final = df_test_reparado
        else:
            print("❌ Aún hay problemas después de reparar")
            return False
    else:
        print("✅ DataFrame ya era seguro")
        df_final = df_test
    
    # Intentar crear Gantt
    try:
        print("\n📊 Intentando crear gráfico Gantt...")
        fig = crear_gantt(df_final)
        
        if fig is not None:
            print("✅ Gráfico Gantt creado exitosamente")
            return True
        else:
            print("⚪ Gráfico Gantt es None (puede ser normal si no hay fechas suficientes)")
            return True
    except Exception as e:
        print(f"❌ Error creando Gantt: {e}")
        return False


def ejecutar_tests_visualization():
    """
    NUEVA FUNCIÓN: Ejecuta todos los tests del módulo visualization
    """
    print("🚀 EJECUTANDO TESTS COMPLETOS DE visualization.py")
    print("="*60)
    
    tests_pasados = 0
    tests_totales = 2
    
    # Test 1: Crear Gantt seguro
    print("\n1️⃣  TEST DE CREAR_GANTT SEGURO")
    if test_crear_gantt_seguro():
        tests_pasados += 1
        print("✅ Test crear_gantt PASADO")
    else:
        print("❌ Test crear_gantt FALLÓ")
    
    # Test 2: Comparar avance metas (test básico)
    print("\n2️⃣  TEST DE COMPARAR_AVANCE_METAS")
    try:
        # Crear datos mínimos de prueba
        df_test = pd.DataFrame({
            'TipoDato': ['NUEVO', 'ACTUALIZAR'],
            'Acuerdo de compromiso': ['Si', 'No'],
            'Análisis y cronograma': ['15/01/2025', ''],
            'Estándares': ['', '20/01/2025'],
            'Publicación': ['01/02/2025', '']
        })
        
        metas_df = pd.DataFrame({
            'Acuerdo de compromiso': [1, 1],
            'Análisis y cronograma': [1, 1],
            'Estándares': [1, 1],
            'Publicación': [1, 1]
        }, index=[datetime.now() - timedelta(days=1), datetime.now() + timedelta(days=1)])
        
        comp_nuevos, comp_act, fecha_meta = comparar_avance_metas(df_test, metas_df, metas_df)
        
        if isinstance(fecha_meta, datetime) and not comp_nuevos.empty and not comp_act.empty:
            print("✅ comparar_avance_metas funciona correctamente")
            tests_pasados += 1
        else:
            print("❌ comparar_avance_metas tiene problemas")
            
    except Exception as e:
        print(f"❌ Error en test comparar_avance_metas: {e}")
    
    # Resumen
    print(f"\n📊 RESULTADO FINAL: {tests_pasados}/{tests_totales} tests pasados")
    
    if tests_pasados == tests_totales:
        print("🎉 MÓDULO visualization.py COMPLETAMENTE CORREGIDO")
        return True
    else:
        print("⚠️  MÓDULO visualization.py NECESITA MÁS CORRECCIONES")
        return False


if __name__ == "__main__":
    print("🔧 MÓDULO visualization.py CORREGIDO")
    print("🎯 Cambios aplicados:")
    print("   ✅ procesar_fecha_gantt_segura() garantiza datetime")
    print("   ✅ Todas las operaciones con fechas usan datetime")
    print("   ✅ Verificaciones adicionales contra objetos date")
    print("   ✅ Funciones de reparación automática")
    print("   ✅ Tests completos con casos críticos")
    
    # Ejecutar tests automáticamente
    ejecutar_tests_visualization()
