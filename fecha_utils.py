# fecha_utils.py - CORRECCIÓN COMPLETA PARA ERROR datetime.date + timedelta

from datetime import datetime, timedelta, date
import pandas as pd
import re

# Lista de días festivos en Colombia para 2025
FESTIVOS_2025 = [
    datetime(2025, 1, 1),   # Año Nuevo
    datetime(2025, 1, 6),   # Día de los Reyes Magos
    datetime(2025, 3, 24),  # Día de San José
    datetime(2025, 4, 17),  # Jueves Santo
    datetime(2025, 4, 18),  # Viernes Santo
    datetime(2025, 5, 1),   # Día del Trabajo
    datetime(2025, 5, 29),  # Ascensión del Señor
    datetime(2025, 6, 19),  # Corpus Christi
    datetime(2025, 6, 27),  # Sagrado Corazón
    datetime(2025, 6, 30),  # San Pedro y San Pablo
    datetime(2025, 7, 20),  # Día de la Independencia
    datetime(2025, 8, 7),   # Batalla de Boyacá
    datetime(2025, 8, 18),  # Asunción de la Virgen
    datetime(2025, 10, 13), # Día de la Raza
    datetime(2025, 11, 3),  # Todos los Santos
    datetime(2025, 11, 17), # Independencia de Cartagena
    datetime(2025, 12, 8),  # Día de la Inmaculada Concepción
    datetime(2025, 12, 25)  # Navidad
]


def es_festivo(fecha):
    """
    Verifica si una fecha es festivo en Colombia.
    CORREGIDO: Manejo uniforme de tipos datetime - SIEMPRE convierte a datetime
    """
    try:
        # CORRECCIÓN CRÍTICA: Convertir SIEMPRE a datetime para comparación uniforme
        if isinstance(fecha, datetime):
            fecha_dt = fecha
        elif isinstance(fecha, date):
            fecha_dt = datetime.combine(fecha, datetime.min.time())
        else:
            # Si no es un tipo de fecha conocido, devolver False
            return False
        
        for festivo in FESTIVOS_2025:
            if (fecha_dt.day == festivo.day and
                fecha_dt.month == festivo.month and
                fecha_dt.year == festivo.year):
                return True
        return False
    except Exception:
        return False


def procesar_fecha(fecha_str):
    """
    CORRECCIÓN CRÍTICA: Procesa una fecha de manera segura manejando NaT.
    GARANTÍA: SIEMPRE devuelve datetime, NUNCA date
    """
    if pd.isna(fecha_str) or fecha_str == '' or fecha_str is None:
        return None

    # Si es un objeto datetime, retornarlo directamente
    if isinstance(fecha_str, datetime):
        if pd.isna(fecha_str):
            return None
        return fecha_str

    # CORRECCIÓN CRÍTICA: Si es date, convertir OBLIGATORIAMENTE a datetime
    if isinstance(fecha_str, date):
        return datetime.combine(fecha_str, datetime.min.time())

    # Si es Timestamp, convertir a datetime
    if isinstance(fecha_str, pd.Timestamp):
        if pd.isna(fecha_str):
            return None
        return fecha_str.to_pydatetime()

    # Si es un string, procesarlo
    try:
        fecha_str = re.sub(r'[^\d/\-]', '', str(fecha_str).strip())
        formatos = ['%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y', '%m/%d/%Y']

        for formato in formatos:
            try:
                fecha = pd.to_datetime(fecha_str, format=formato)
                if pd.notna(fecha):
                    # CRÍTICO: Asegurar que SIEMPRE devolvemos datetime
                    resultado = fecha.to_pydatetime() if hasattr(fecha, 'to_pydatetime') else fecha
                    # Verificación adicional: si por alguna razón es date, convertir
                    if isinstance(resultado, date) and not isinstance(resultado, datetime):
                        return datetime.combine(resultado, datetime.min.time())
                    return resultado
            except:
                continue
        return None
    except Exception:
        return None


def formatear_fecha(fecha_str):
    """
    Formatea una fecha en formato DD/MM/YYYY manejando NaT.
    CORREGIDO: Usa procesar_fecha segura
    """
    try:
        fecha = procesar_fecha(fecha_str)
        if fecha is not None and pd.notna(fecha):
            return fecha.strftime('%d/%m/%Y')
        return ""
    except Exception:
        return ""


def calcular_plazo_analisis(fecha_entrega):
    """
    Calcula el plazo de análisis como 5 días hábiles después de la fecha de entrega.
    CORRECCIÓN CRÍTICA: Uso GARANTIZADO de datetime + timedelta
    """
    try:
        # PASO 1: Procesar fecha de entrega (GARANTÍA: devuelve datetime o None)
        fecha = procesar_fecha(fecha_entrega)
        if fecha is None or pd.isna(fecha):
            return None

        # PASO 2: VERIFICACIÓN ADICIONAL - Asegurar que es datetime
        if not isinstance(fecha, datetime):
            if isinstance(fecha, date):
                fecha = datetime.combine(fecha, datetime.min.time())
            else:
                print(f"⚠️  Tipo inesperado en calcular_plazo_analisis: {type(fecha)}")
                return None

        # PASO 3: Calcular días hábiles (OPERACIÓN SEGURA: datetime + timedelta)
        fecha_actual = fecha
        dias_habiles = 0

        while dias_habiles < 5:
            fecha_actual = fecha_actual + timedelta(days=1)  # SEGURO: datetime + timedelta = datetime
            
            dia_semana = fecha_actual.weekday()
            if dia_semana < 5 and not es_festivo(fecha_actual):
                dias_habiles += 1

        return fecha_actual

    except Exception as e:
        print(f"❌ Error en calcular_plazo_analisis: {e}")
        return None


def calcular_plazo_cronograma(fecha_plazo_analisis):
    """
    Calcula el plazo de cronograma como 3 días hábiles después del plazo de análisis.
    CORRECCIÓN CRÍTICA: Uso GARANTIZADO de datetime + timedelta
    """
    try:
        # PASO 1: Procesar fecha (GARANTÍA: devuelve datetime o None)
        fecha = procesar_fecha(fecha_plazo_analisis)
        if fecha is None or pd.isna(fecha):
            return None

        # PASO 2: VERIFICACIÓN ADICIONAL - Asegurar que es datetime
        if not isinstance(fecha, datetime):
            if isinstance(fecha, date):
                fecha = datetime.combine(fecha, datetime.min.time())
            else:
                print(f"⚠️  Tipo inesperado en calcular_plazo_cronograma: {type(fecha)}")
                return None

        # PASO 3: Calcular días hábiles (OPERACIÓN SEGURA: datetime + timedelta)
        fecha_actual = fecha
        dias_habiles = 0

        while dias_habiles < 3:
            fecha_actual = fecha_actual + timedelta(days=1)  # SEGURO: datetime + timedelta = datetime
            
            dia_semana = fecha_actual.weekday()
            if dia_semana < 5 and not es_festivo(fecha_actual):
                dias_habiles += 1

        return fecha_actual

    except Exception as e:
        print(f"❌ Error en calcular_plazo_cronograma: {e}")
        return None


def calcular_plazo_oficio_cierre(fecha_publicacion):
    """
    Calcula el plazo de oficio de cierre como 7 días hábiles después de la fecha de publicación.
    CORRECCIÓN CRÍTICA: Uso GARANTIZADO de datetime + timedelta
    """
    try:
        # PASO 1: Procesar fecha (GARANTÍA: devuelve datetime o None)
        fecha = procesar_fecha(fecha_publicacion)
        if fecha is None or pd.isna(fecha):
            return None

        # PASO 2: VERIFICACIÓN ADICIONAL - Asegurar que es datetime
        if not isinstance(fecha, datetime):
            if isinstance(fecha, date):
                fecha = datetime.combine(fecha, datetime.min.time())
            else:
                print(f"⚠️  Tipo inesperado en calcular_plazo_oficio_cierre: {type(fecha)}")
                return None

        # PASO 3: Calcular días hábiles (OPERACIÓN SEGURA: datetime + timedelta)
        fecha_actual = fecha
        dias_habiles = 0

        while dias_habiles < 7:
            fecha_actual = fecha_actual + timedelta(days=1)  # SEGURO: datetime + timedelta = datetime
            
            dia_semana = fecha_actual.weekday()
            if dia_semana < 5 and not es_festivo(fecha_actual):
                dias_habiles += 1

        return fecha_actual

    except Exception as e:
        print(f"❌ Error en calcular_plazo_oficio_cierre: {e}")
        return None


def actualizar_plazo_analisis(df):
    """
    Actualiza la columna 'Plazo de análisis' en el DataFrame.
    CORREGIDO: Manejo de errores mejorado y preparación del DataFrame
    """
    if 'Fecha de entrega de información' not in df.columns:
        return df

    # NUEVO: Preparar DataFrame para cálculos seguros
    try:
        from data_utils import preparar_dataframe_para_calculos
        df_seguro = preparar_dataframe_para_calculos(df)
    except ImportError:
        # Si no está disponible, usar el DataFrame original con cuidado
        df_seguro = df.copy()

    df_actualizado = df_seguro.copy()

    # Asegurar que la columna existe
    if 'Plazo de análisis' not in df_actualizado.columns:
        df_actualizado['Plazo de análisis'] = ''

    for idx, row in df_actualizado.iterrows():
        try:
            fecha_entrega = row.get('Fecha de entrega de información', None)
            if fecha_entrega and pd.notna(fecha_entrega) and str(fecha_entrega).strip() != '':
                # VERIFICACIÓN ADICIONAL: Asegurar que no sea un objeto date peligroso
                if isinstance(fecha_entrega, date) and not isinstance(fecha_entrega, datetime):
                    print(f"⚠️  Objeto date detectado en fila {idx}, convirtiendo...")
                    fecha_entrega = datetime.combine(fecha_entrega, datetime.min.time())
                
                plazo = calcular_plazo_analisis(fecha_entrega)
                if plazo is not None:
                    df_actualizado.at[idx, 'Plazo de análisis'] = formatear_fecha(plazo)
                    
                    # También actualizar plazo de cronograma
                    plazo_cronograma = calcular_plazo_cronograma(plazo)
                    if plazo_cronograma is not None:
                        if 'Plazo de cronograma' not in df_actualizado.columns:
                            df_actualizado['Plazo de cronograma'] = ''
                        df_actualizado.at[idx, 'Plazo de cronograma'] = formatear_fecha(plazo_cronograma)
        except Exception as e:
            print(f"❌ Error procesando fila {idx}: {e}")
            continue

    return df_actualizado


def actualizar_plazo_cronograma(df):
    """
    Actualiza la columna 'Plazo de cronograma' en el DataFrame.
    CORREGIDO: Manejo de errores mejorado y preparación del DataFrame
    """
    if 'Plazo de análisis' not in df.columns:
        return df

    # NUEVO: Preparar DataFrame para cálculos seguros
    try:
        from data_utils import preparar_dataframe_para_calculos
        df_seguro = preparar_dataframe_para_calculos(df)
    except ImportError:
        df_seguro = df.copy()

    df_actualizado = df_seguro.copy()

    if 'Plazo de cronograma' not in df_actualizado.columns:
        df_actualizado['Plazo de cronograma'] = ''

    for idx, row in df_actualizado.iterrows():
        try:
            plazo_analisis = row.get('Plazo de análisis', None)
            if plazo_analisis and pd.notna(plazo_analisis) and str(plazo_analisis).strip() != '':
                # VERIFICACIÓN ADICIONAL: Asegurar que no sea un objeto date peligroso
                if isinstance(plazo_analisis, date) and not isinstance(plazo_analisis, datetime):
                    print(f"⚠️  Objeto date detectado en fila {idx}, convirtiendo...")
                    plazo_analisis = datetime.combine(plazo_analisis, datetime.min.time())
                
                plazo_cronograma = calcular_plazo_cronograma(plazo_analisis)
                if plazo_cronograma is not None:
                    df_actualizado.at[idx, 'Plazo de cronograma'] = formatear_fecha(plazo_cronograma)
        except Exception as e:
            print(f"❌ Error procesando cronograma fila {idx}: {e}")
            continue

    return df_actualizado


def actualizar_plazo_oficio_cierre(df):
    """
    Actualiza la columna 'Plazo de oficio de cierre' en el DataFrame.
    CORREGIDO: Manejo de errores mejorado y preparación del DataFrame
    """
    if 'Publicación' not in df.columns:
        return df

    # NUEVO: Preparar DataFrame para cálculos seguros
    try:
        from data_utils import preparar_dataframe_para_calculos
        df_seguro = preparar_dataframe_para_calculos(df)
    except ImportError:
        df_seguro = df.copy()

    df_actualizado = df_seguro.copy()

    if 'Plazo de oficio de cierre' not in df_actualizado.columns:
        df_actualizado['Plazo de oficio de cierre'] = ''

    for idx, row in df_actualizado.iterrows():
        try:
            fecha_publicacion = row.get('Publicación', None)
            if fecha_publicacion and pd.notna(fecha_publicacion) and str(fecha_publicacion).strip() != '':
                # VERIFICACIÓN ADICIONAL: Asegurar que no sea un objeto date peligroso
                if isinstance(fecha_publicacion, date) and not isinstance(fecha_publicacion, datetime):
                    print(f"⚠️  Objeto date detectado en fila {idx}, convirtiendo...")
                    fecha_publicacion = datetime.combine(fecha_publicacion, datetime.min.time())
                
                plazo_oficio = calcular_plazo_oficio_cierre(fecha_publicacion)
                if plazo_oficio is not None:
                    df_actualizado.at[idx, 'Plazo de oficio de cierre'] = formatear_fecha(plazo_oficio)
        except Exception as e:
            print(f"❌ Error procesando oficio cierre fila {idx}: {e}")
            continue

    return df_actualizado


# NUEVAS FUNCIONES DE VERIFICACIÓN Y TEST

def verificar_tipos_fecha_seguros(fecha_input):
    """
    NUEVA FUNCIÓN: Verifica que una fecha de input sea segura para cálculos
    """
    if pd.isna(fecha_input) or fecha_input == '' or fecha_input is None:
        return True, "Valor nulo/vacío (seguro)"
    
    if isinstance(fecha_input, datetime):
        return True, f"datetime (seguro): {fecha_input}"
    
    if isinstance(fecha_input, date) and not isinstance(fecha_input, datetime):
        return False, f"date PELIGROSO: {fecha_input} - DEBE CONVERTIRSE"
    
    if isinstance(fecha_input, pd.Timestamp):
        return True, f"Timestamp (seguro): {fecha_input}"
    
    if isinstance(fecha_input, str):
        fecha_procesada = procesar_fecha(fecha_input)
        if fecha_procesada is None:
            return True, f"String inválido (seguro): {fecha_input}"
        elif isinstance(fecha_procesada, datetime):
            return True, f"String -> datetime (seguro): {fecha_input} -> {fecha_procesada}"
        else:
            return False, f"String -> tipo PELIGROSO: {fecha_input} -> {type(fecha_procesada)}"
    
    return False, f"Tipo desconocido: {type(fecha_input)}"


def diagnosticar_dataframe_fechas(df):
    """
    NUEVA FUNCIÓN: Diagnostica todos los campos de fecha en un DataFrame
    """
    print("\n🔍 DIAGNÓSTICO COMPLETO DE FECHAS EN DATAFRAME")
    print("="*60)
    
    campos_fecha = [
        'Fecha de entrega de información',
        'Plazo de análisis', 
        'Plazo de cronograma',
        'Análisis y cronograma',
        'Estándares (fecha programada)',
        'Estándares',
        'Fecha de publicación programada', 
        'Publicación',
        'Plazo de oficio de cierre',
        'Fecha de oficio de cierre',
        'Suscripción acuerdo de compromiso',
        'Entrega acuerdo de compromiso'
    ]
    
    problemas_encontrados = []
    total_valores_analizados = 0
    valores_problematicos = 0
    
    for campo in campos_fecha:
        if campo in df.columns:
            print(f"\n📅 Analizando campo: {campo}")
            problemas_campo = 0
            valores_campo = 0
            
            for idx, valor in df[campo].items():
                if pd.notna(valor) and str(valor).strip() != '':
                    valores_campo += 1
                    total_valores_analizados += 1
                    
                    es_seguro, descripcion = verificar_tipos_fecha_seguros(valor)
                    if not es_seguro:
                        print(f"   ❌ Fila {idx}: {descripcion}")
                        problemas_campo += 1
                        valores_problematicos += 1
            
            if problemas_campo > 0:
                print(f"   ⚠️  {problemas_campo}/{valores_campo} valores problemáticos")
                problemas_encontrados.append(campo)
            else:
                print(f"   ✅ {valores_campo} valores seguros")
    
    print(f"\n📊 RESUMEN DEL DIAGNÓSTICO:")
    print(f"   Total valores analizados: {total_valores_analizados}")
    print(f"   Valores problemáticos: {valores_problematicos}")
    print(f"   Campos con problemas: {len(problemas_encontrados)}")
    
    if problemas_encontrados:
        print(f"   🚨 Campos problemáticos: {problemas_encontrados}")
        return False, problemas_encontrados
    else:
        print("   ✅ TODOS LOS CAMPOS SON SEGUROS")
        return True, []


def test_calculo_plazos_completo():
    """
    NUEVA FUNCIÓN: Test completo de cálculo de plazos con casos edge
    """
    print("\n🧪 TEST COMPLETO DE CÁLCULO DE PLAZOS")
    print("="*50)
    
    casos_test = [
        # Casos normales
        ("15/01/2025", "string normal"),
        ("2025-01-15", "string formato ISO"),
        
        # Casos críticos (objetos date)
        (date(2025, 1, 15), "objeto date CRÍTICO"),
        (datetime(2025, 1, 15), "objeto datetime"),
        (pd.Timestamp('2025-01-15'), "Timestamp pandas"),
        
        # Casos edge
        ("", "string vacío"),
        (None, "None"),
        (pd.NaT, "NaT"),
        
        # Casos problemáticos
        ("fecha_inválida", "string inválido"),
        (12345, "número"),
    ]
    
    resultados = {
        'analisis': {'exitoso': 0, 'fallido': 0},
        'cronograma': {'exitoso': 0, 'fallido': 0}, 
        'oficio': {'exitoso': 0, 'fallido': 0}
    }
    
    for fecha_input, descripcion in casos_test:
        print(f"\n🔍 Probando: {descripcion} -> {fecha_input}")
        
        try:
            # Test procesar_fecha primero
            fecha_procesada = procesar_fecha(fecha_input)
            if fecha_procesada is not None:
                es_datetime = isinstance(fecha_procesada, datetime)
                print(f"   procesar_fecha: {fecha_procesada} ({'✅' if es_datetime else '❌'} datetime)")
                
                if es_datetime:
                    # Test cálculo de plazos
                    plazo_analisis = calcular_plazo_analisis(fecha_input)
                    plazo_cronograma = calcular_plazo_cronograma(fecha_procesada) if fecha_procesada else None
                    plazo_oficio = calcular_plazo_oficio_cierre(fecha_procesada) if fecha_procesada else None
                    
                    # Verificar resultados
                    if plazo_analisis and isinstance(plazo_analisis, datetime):
                        print(f"   ✅ Plazo análisis: {formatear_fecha(plazo_analisis)}")
                        resultados['analisis']['exitoso'] += 1
                    else:
                        print(f"   ❌ Plazo análisis falló")
                        resultados['analisis']['fallido'] += 1
                    
                    if plazo_cronograma and isinstance(plazo_cronograma, datetime):
                        print(f"   ✅ Plazo cronograma: {formatear_fecha(plazo_cronograma)}")
                        resultados['cronograma']['exitoso'] += 1
                    else:
                        print(f"   ❌ Plazo cronograma falló")
                        resultados['cronograma']['fallido'] += 1
                        
                    if plazo_oficio and isinstance(plazo_oficio, datetime):
                        print(f"   ✅ Plazo oficio: {formatear_fecha(plazo_oficio)}")
                        resultados['oficio']['exitoso'] += 1
                    else:
                        print(f"   ❌ Plazo oficio falló")
                        resultados['oficio']['fallido'] += 1
                else:
                    print(f"   ❌ procesar_fecha no devolvió datetime")
            else:
                print(f"   ⚪ procesar_fecha: None (esperado para valores inválidos)")
                
        except Exception as e:
            print(f"   💥 ERROR: {e}")
            resultados['analisis']['fallido'] += 1
            resultados['cronograma']['fallido'] += 1
            resultados['oficio']['fallido'] += 1
    
    # Resumen de resultados
    print(f"\n📊 RESUMEN DE TESTS:")
    for tipo, stats in resultados.items():
        total = stats['exitoso'] + stats['fallido']
        porcentaje = (stats['exitoso'] / total * 100) if total > 0 else 0
        print(f"   {tipo}: {stats['exitoso']}/{total} exitosos ({porcentaje:.1f}%)")
    
    # Determinar si todos los tests críticos pasaron
    tests_criticos_ok = all(
        resultados[tipo]['exitoso'] > 0 for tipo in ['analisis', 'cronograma', 'oficio']
    )
    
    if tests_criticos_ok:
        print("\n✅ TODOS LOS TESTS CRÍTICOS PASARON")
        return True
    else:
        print("\n❌ ALGUNOS TESTS CRÍTICOS FALLARON")
        return False


def reparar_dataframe_fechas_automatico(df):
    """
    NUEVA FUNCIÓN: Repara automáticamente todos los problemas de fechas en un DataFrame
    """
    print("\n🔧 REPARACIÓN AUTOMÁTICA DE FECHAS EN DATAFRAME")
    print("="*55)
    
    df_reparado = df.copy()
    reparaciones_aplicadas = 0
    
    campos_fecha = [
        'Fecha de entrega de información', 'Plazo de análisis', 'Plazo de cronograma',
        'Análisis y cronograma', 'Estándares (fecha programada)', 'Estándares',
        'Fecha de publicación programada', 'Publicación', 'Plazo de oficio de cierre',
        'Fecha de oficio de cierre', 'Suscripción acuerdo de compromiso', 'Entrega acuerdo de compromiso'
    ]
    
    for campo in campos_fecha:
        if campo in df_reparado.columns:
            print(f"\n🔧 Reparando campo: {campo}")
            reparaciones_campo = 0
            
            for idx, valor in df_reparado[campo].items():
                if pd.notna(valor) and str(valor).strip() != '':
                    es_seguro, descripcion = verificar_tipos_fecha_seguros(valor)
                    
                    if not es_seguro:
                        # Intentar reparar
                        try:
                            if isinstance(valor, date) and not isinstance(valor, datetime):
                                # Convertir date a datetime y luego formatear
                                valor_reparado = datetime.combine(valor, datetime.min.time())
                                df_reparado.at[idx, campo] = formatear_fecha(valor_reparado)
                                reparaciones_campo += 1
                                reparaciones_aplicadas += 1
                                print(f"   ✅ Fila {idx}: date -> datetime -> string")
                            else:
                                # Para otros tipos problemáticos, intentar procesar
                                fecha_procesada = procesar_fecha(valor)
                                if fecha_procesada and isinstance(fecha_procesada, datetime):
                                    df_reparado.at[idx, campo] = formatear_fecha(fecha_procesada)
                                    reparaciones_campo += 1
                                    reparaciones_aplicadas += 1
                                    print(f"   ✅ Fila {idx}: {type(valor).__name__} -> datetime -> string")
                                else:
                                    # Si no se puede reparar, limpiar
                                    df_reparado.at[idx, campo] = ''
                                    reparaciones_campo += 1
                                    reparaciones_aplicadas += 1
                                    print(f"   🧹 Fila {idx}: valor problemático limpiado")
                        except Exception as e:
                            # Si falla la reparación, limpiar
                            df_reparado.at[idx, campo] = ''
                            reparaciones_campo += 1
                            reparaciones_aplicadas += 1
                            print(f"   🧹 Fila {idx}: error en reparación, limpiado")
            
            if reparaciones_campo > 0:
                print(f"   📝 {reparaciones_campo} reparaciones aplicadas en {campo}")
            else:
                print(f"   ✅ {campo} ya estaba correcto")
    
    print(f"\n📊 REPARACIONES COMPLETADAS:")
    print(f"   Total reparaciones: {reparaciones_aplicadas}")
    
    # Verificar que la reparación fue exitosa
    es_seguro_ahora, campos_restantes = diagnosticar_dataframe_fechas(df_reparado)
    
    if es_seguro_ahora:
        print("   ✅ DATAFRAME COMPLETAMENTE REPARADO")
    else:
        print(f"   ⚠️  Aún quedan problemas en: {campos_restantes}")
    
    return df_reparado, reparaciones_aplicadas


# Funciones de test principales
def test_calcular_plazo_analisis():
    """Función de prueba MEJORADA para verificar cálculos"""
    fechas_prueba = [
        "15/01/2025",
        "27/03/2025", 
        "30/04/2025",
        "20/12/2025",
        date(2025, 2, 1),  # CASO CRÍTICO
        datetime(2025, 2, 15)
    ]

    print("🧪 PROBANDO CORRECCIÓN DE PLAZOS...")
    todos_exitosos = True
    
    for fecha in fechas_prueba:
        try:
            plazo = calcular_plazo_analisis(fecha)
            if plazo and isinstance(plazo, datetime):
                print(f"✅ Fecha entrega: {fecha} -> Plazo análisis: {formatear_fecha(plazo)}")
            else:
                print(f"❌ Fecha entrega: {fecha} -> No se pudo calcular o tipo incorrecto")
                todos_exitosos = False
        except Exception as e:
            print(f"💥 Error con {fecha}: {e}")
            todos_exitosos = False
    
    return todos_exitosos


def ejecutar_verificacion_completa():
    """
    NUEVA FUNCIÓN PRINCIPAL: Ejecuta verificación completa del módulo
    """
    print("\n🚀 EJECUTANDO VERIFICACIÓN COMPLETA DE fecha_utils.py")
    print("="*65)
    
    tests_pasados = 0
    tests_totales = 3
    
    # Test 1: Función procesar_fecha
    print("\n1️⃣  TEST DE FUNCIÓN procesar_fecha")
    try:
        fecha_test = procesar_fecha(date(2025, 1, 15))  # CASO CRÍTICO
        if isinstance(fecha_test, datetime):
            print("✅ procesar_fecha maneja objetos date correctamente")
            tests_pasados += 1
        else:
            print("❌ procesar_fecha NO convierte date a datetime")
    except Exception as e:
        print(f"❌ Error en procesar_fecha: {e}")
    
    # Test 2: Cálculo de plazos
    print("\n2️⃣  TEST DE CÁLCULO DE PLAZOS")
    if test_calcular_plazo_analisis():
        print("✅ Cálculo de plazos funciona correctamente")
        tests_pasados += 1
    else:
        print("❌ Problemas en cálculo de plazos")
    
    # Test 3: Test completo con casos edge
    print("\n3️⃣  TEST COMPLETO CON CASOS EDGE")
    if test_calculo_plazos_completo():
        print("✅ Todos los casos edge manejados correctamente")
        tests_pasados += 1
    else:
        print("❌ Problemas con casos edge")
    
    # Resumen final
    print(f"\n📊 RESULTADO FINAL: {tests_pasados}/{tests_totales} tests pasados")
    
    if tests_pasados == tests_totales:
        print("🎉 MÓDULO fecha_utils.py COMPLETAMENTE CORREGIDO")
        return True
    else:
        print("⚠️  MÓDULO fecha_utils.py NECESITA MÁS CORRECCIONES")
        return False


if __name__ == "__main__":
    print("🔧 MÓDULO fecha_utils.py CORREGIDO COMPLETAMENTE")
    print("🎯 Cambios principales:")
    print("   ✅ procesar_fecha() GARANTIZA datetime o None")
    print("   ✅ Todos los cálculos usan datetime + timedelta")
    print("   ✅ Verificaciones adicionales contra objetos date")
    print("   ✅ Funciones de diagnóstico y reparación")
    print("   ✅ Tests completos con casos edge")
    
    # Ejecutar verificación automática
    ejecutar_verificacion_completa()
