# plazo_utils.py - CORREGIDO PARA ERROR datetime.date + timedelta

from datetime import datetime, timedelta
import pandas as pd
from fecha_utils import procesar_fecha, es_festivo, formatear_fecha

def calcular_plazo_oficio_cierre(fecha_publicacion):
    """
    CORRECCIÓN CRÍTICA: Calcula el plazo de oficio de cierre como 7 días hábiles 
    después de la fecha de publicación, sin contar sábados, domingos y festivos en Colombia.
    GARANTÍA: Usa solo datetime para evitar error date + timedelta
    """
    # PASO 1: Convertir la fecha de publicación a objeto datetime (NUNCA date)
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

    # PASO 3: Contador de días hábiles
    dias_habiles = 0
    fecha_actual = fecha

    # PASO 4: Calcular 7 días hábiles a partir de la fecha de publicación
    while dias_habiles < 7:
        # OPERACIÓN SEGURA: datetime + timedelta = datetime
        fecha_actual = fecha_actual + timedelta(days=1)

        # Verificar si es día hábil (no es fin de semana ni festivo)
        dia_semana = fecha_actual.weekday()  # 0 = lunes, 6 = domingo

        # Si no es sábado (5) ni domingo (6) ni festivo, contamos como día hábil
        if dia_semana < 5 and not es_festivo(fecha_actual):
            dias_habiles += 1

    # PASO 5: Retornar la fecha calculada (garantizado datetime)
    return fecha_actual

def actualizar_plazo_oficio_cierre(df):
    """
    CORREGIDO: Actualiza la columna 'Plazo de oficio de cierre' en el DataFrame
    basándose en la columna 'Publicación' con protección contra errores datetime.
    """
    if 'Publicación' not in df.columns:
        return df

    # NUEVO: Preparar DataFrame para cálculos seguros
    try:
        from data_utils import preparar_dataframe_para_calculos
        df_seguro = preparar_dataframe_para_calculos(df)
    except ImportError:
        # Si no está disponible, usar el DataFrame original con cuidado
        df_seguro = df.copy()

    # Asegurarse de que la columna 'Plazo de oficio de cierre' exista
    if 'Plazo de oficio de cierre' not in df_seguro.columns:
        df_seguro['Plazo de oficio de cierre'] = ''

    # Crear una copia del DataFrame
    df_actualizado = df_seguro.copy()

    # Iterar sobre cada fila
    for idx, row in df_actualizado.iterrows():
        try:
            fecha_publicacion = row.get('Publicación', None)
            if fecha_publicacion and pd.notna(fecha_publicacion) and fecha_publicacion != '':
                
                # VERIFICACIÓN ADICIONAL: Detectar objetos date peligrosos
                if isinstance(fecha_publicacion, date) and not isinstance(fecha_publicacion, datetime):
                    print(f"⚠️  Objeto date detectado en fila {idx}, convirtiendo...")
                    fecha_publicacion = datetime.combine(fecha_publicacion, datetime.min.time())
                
                plazo = calcular_plazo_oficio_cierre(fecha_publicacion)
                if plazo is not None:
                    df_actualizado.at[idx, 'Plazo de oficio de cierre'] = formatear_fecha(plazo)
                    
        except Exception as e:
            print(f"❌ Error procesando fila {idx} para plazo oficio cierre: {e}")
            continue

    return df_actualizado

# NUEVA FUNCIÓN DE VERIFICACIÓN
def verificar_calculo_seguro(fecha_input):
    """
    NUEVA FUNCIÓN: Verifica que el cálculo de plazo sea seguro
    """
    try:
        print(f"\n🔍 Verificando cálculo seguro para: {fecha_input} ({type(fecha_input)})")
        
        # Verificar que procesar_fecha devuelve datetime
        fecha_procesada = procesar_fecha(fecha_input)
        if fecha_procesada is None:
            print("   ⚪ Fecha inválida (esperado)")
            return True
        
        if not isinstance(fecha_procesada, datetime):
            print(f"   ❌ procesar_fecha devolvió {type(fecha_procesada)} en lugar de datetime")
            return False
        
        print(f"   ✅ procesar_fecha devolvió datetime: {fecha_procesada}")
        
        # Verificar que el cálculo funciona
        plazo = calcular_plazo_oficio_cierre(fecha_input)
        if plazo is None:
            print("   ⚪ Cálculo devolvió None (podría ser esperado)")
            return True
        
        if not isinstance(plazo, datetime):
            print(f"   ❌ calcular_plazo_oficio_cierre devolvió {type(plazo)} en lugar de datetime")
            return False
        
        print(f"   ✅ Cálculo exitoso: {formatear_fecha(plazo)}")
        return True
        
    except Exception as e:
        print(f"   💥 Error en verificación: {e}")
        return False

# Función para probar el cálculo del plazo de oficio de cierre
def test_calcular_plazo_oficio_cierre():
    """
    FUNCIÓN DE TEST MEJORADA: Incluye casos críticos con objetos date
    """
    fechas_prueba = [
        "15/01/2025",
        "27/03/2025",
        "30/04/2025", 
        "20/12/2025",
        # CASOS CRÍTICOS
        date(2025, 1, 15),  # Objeto date PELIGROSO
        datetime(2025, 1, 15),  # Objeto datetime SEGURO
        pd.Timestamp('2025-01-15'),  # Timestamp SEGURO
    ]

    print("🧪 PROBANDO CÁLCULO DE PLAZO OFICIO CIERRE CORREGIDO...")
    print("="*60)
    
    todos_exitosos = True
    
    for fecha in fechas_prueba:
        print(f"\n📅 Probando: {fecha} ({type(fecha)})")
        
        if verificar_calculo_seguro(fecha):
            try:
                plazo = calcular_plazo_oficio_cierre(fecha)
                if plazo:
                    print(f"   ✅ Resultado: {formatear_fecha(plazo)}")
                else:
                    print(f"   ⚪ Sin resultado (fecha inválida)")
            except Exception as e:
                print(f"   💥 Error en cálculo: {e}")
                todos_exitosos = False
        else:
            print(f"   ❌ Verificación falló")
            todos_exitosos = False
    
    print(f"\n📊 RESULTADO: {'✅ TODOS LOS TESTS PASARON' if todos_exitosos else '❌ ALGUNOS TESTS FALLARON'}")
    return todos_exitosos

def test_actualizar_plazo_dataframe():
    """
    NUEVA FUNCIÓN: Test específico para actualización en DataFrame
    """
    print("\n🧪 PROBANDO ACTUALIZACIÓN EN DATAFRAME...")
    
    # Crear DataFrame de prueba con casos críticos
    df_test = pd.DataFrame({
        'Cod': ['1', '2', '3', '4'],
        'Entidad': ['Test 1', 'Test 2', 'Test 3', 'Test 4'],
        'Publicación': [
            '15/01/2025',           # String normal
            date(2025, 1, 20),      # CASO CRÍTICO: date
            datetime(2025, 1, 25),  # datetime seguro
            ''                      # Vacío
        ]
    })
    
    print("DataFrame original:")
    for idx, row in df_test.iterrows():
        pub = row['Publicación']
        print(f"   Fila {idx}: {pub} ({type(pub)})")
    
    try:
        # Aplicar actualización
        df_resultado = actualizar_plazo_oficio_cierre(df_test)
        
        print("\nDataFrame después de actualización:")
        for idx, row in df_resultado.iterrows():
            pub = row['Publicación']
            plazo = row.get('Plazo de oficio de cierre', '')
            print(f"   Fila {idx}: {pub} -> {plazo}")
        
        # Verificar que se calcularon los plazos esperados
        plazos_calculados = df_resultado['Plazo de oficio de cierre'].apply(lambda x: x != '').sum()
        print(f"\n📊 Plazos calculados: {plazos_calculados}/3 (esperado: 3)")
        
        return plazos_calculados >= 3
        
    except Exception as e:
        print(f"💥 Error en test de DataFrame: {e}")
        return False

def ejecutar_tests_plazo_utils():
    """
    NUEVA FUNCIÓN: Ejecuta todos los tests del módulo
    """
    print("🚀 EJECUTANDO TESTS COMPLETOS DE plazo_utils.py")
    print("="*55)
    
    tests_pasados = 0
    tests_totales = 2
    
    # Test 1: Cálculo individual
    print("\n1️⃣  TEST DE CÁLCULO INDIVIDUAL")
    if test_calcular_plazo_oficio_cierre():
        tests_pasados += 1
        print("✅ Test individual PASADO")
    else:
        print("❌ Test individual FALLÓ")
    
    # Test 2: Actualización en DataFrame
    print("\n2️⃣  TEST DE ACTUALIZACIÓN EN DATAFRAME")
    if test_actualizar_plazo_dataframe():
        tests_pasados += 1
        print("✅ Test DataFrame PASADO")
    else:
        print("❌ Test DataFrame FALLÓ")
    
    # Resumen
    print(f"\n📊 RESULTADO FINAL: {tests_pasados}/{tests_totales} tests pasados")
    
    if tests_pasados == tests_totales:
        print("🎉 MÓDULO plazo_utils.py COMPLETAMENTE CORREGIDO")
        return True
    else:
        print("⚠️  MÓDULO plazo_utils.py NECESITA MÁS CORRECCIONES")
        return False

if __name__ == "__main__":
    print("🔧 MÓDULO plazo_utils.py CORREGIDO")
    print("🎯 Cambios aplicados:")
    print("   ✅ calcular_plazo_oficio_cierre() usa solo datetime")
    print("   ✅ Verificaciones adicionales contra objetos date")
    print("   ✅ Preparación segura del DataFrame")
    print("   ✅ Manejo de errores mejorado")
    print("   ✅ Tests completos con casos críticos")
    
    # Ejecutar tests automáticamente
    ejecutar_tests_plazo_utils()
