# fecha_utils.py - CORRECCIÓN PARA ERROR datetime.date + timedelta

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
    CORREGIDO: Manejo uniforme de tipos datetime
    """
    try:
        # Convertir SIEMPRE a datetime para comparación uniforme
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
    Procesa una fecha de manera segura manejando NaT.
    CORREGIDO: Siempre devuelve datetime, nunca date
    """
    if pd.isna(fecha_str) or fecha_str == '' or fecha_str is None:
        return None

    # Si es un objeto datetime, retornarlo directamente
    if isinstance(fecha_str, datetime):
        if pd.isna(fecha_str):
            return None
        return fecha_str

    # CORRECCIÓN CRÍTICA: Si es date, convertir SIEMPRE a datetime
    if isinstance(fecha_str, date):
        return datetime.combine(fecha_str, datetime.min.time())

    # Si es un string, procesarlo
    try:
        fecha_str = re.sub(r'[^\d/\-]', '', str(fecha_str).strip())
        formatos = ['%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y', '%m/%d/%Y']

        for formato in formatos:
            try:
                fecha = pd.to_datetime(fecha_str, format=formato)
                if pd.notna(fecha):
                    # ASEGURAR QUE SIEMPRE DEVOLVEMOS datetime
                    return fecha.to_pydatetime() if hasattr(fecha, 'to_pydatetime') else fecha
            except:
                continue
        return None
    except Exception:
        return None


def formatear_fecha(fecha_str):
    """
    Formatea una fecha en formato DD/MM/YYYY manejando NaT.
    CORREGIDO: Manejo uniforme de tipos
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
    CORRECCIÓN CRÍTICA: Uso correcto de datetime + timedelta
    """
    try:
        # Procesar fecha de entrega (SIEMPRE devuelve datetime o None)
        fecha = procesar_fecha(fecha_entrega)
        if fecha is None or pd.isna(fecha):
            return None

        # ASEGURAR que trabajamos SIEMPRE con datetime
        if not isinstance(fecha, datetime):
            if isinstance(fecha, date):
                fecha = datetime.combine(fecha, datetime.min.time())
            else:
                return None

        fecha_actual = fecha
        dias_habiles = 0

        # CORRECCIÓN: Operación datetime + timedelta (VÁLIDA)
        while dias_habiles < 5:
            fecha_actual = fecha_actual + timedelta(days=1)  # datetime + timedelta = datetime
            
            dia_semana = fecha_actual.weekday()
            if dia_semana < 5 and not es_festivo(fecha_actual):
                dias_habiles += 1

        return fecha_actual

    except Exception as e:
        print(f"Error en calcular_plazo_analisis: {e}")
        return None


def calcular_plazo_cronograma(fecha_plazo_analisis):
    """
    Calcula el plazo de cronograma como 3 días hábiles después del plazo de análisis.
    CORRECCIÓN CRÍTICA: Uso correcto de datetime + timedelta
    """
    try:
        # Procesar fecha (SIEMPRE devuelve datetime o None)
        fecha = procesar_fecha(fecha_plazo_analisis)
        if fecha is None or pd.isna(fecha):
            return None

        # ASEGURAR que trabajamos SIEMPRE con datetime
        if not isinstance(fecha, datetime):
            if isinstance(fecha, date):
                fecha = datetime.combine(fecha, datetime.min.time())
            else:
                return None

        fecha_actual = fecha
        dias_habiles = 0

        # CORRECCIÓN: Operación datetime + timedelta (VÁLIDA)
        while dias_habiles < 3:
            fecha_actual = fecha_actual + timedelta(days=1)  # datetime + timedelta = datetime
            
            dia_semana = fecha_actual.weekday()
            if dia_semana < 5 and not es_festivo(fecha_actual):
                dias_habiles += 1

        return fecha_actual

    except Exception as e:
        print(f"Error en calcular_plazo_cronograma: {e}")
        return None


def calcular_plazo_oficio_cierre(fecha_publicacion):
    """
    Calcula el plazo de oficio de cierre como 7 días hábiles después de la fecha de publicación.
    CORRECCIÓN CRÍTICA: Uso correcto de datetime + timedelta
    """
    try:
        # Procesar fecha (SIEMPRE devuelve datetime o None)
        fecha = procesar_fecha(fecha_publicacion)
        if fecha is None or pd.isna(fecha):
            return None

        # ASEGURAR que trabajamos SIEMPRE con datetime
        if not isinstance(fecha, datetime):
            if isinstance(fecha, date):
                fecha = datetime.combine(fecha, datetime.min.time())
            else:
                return None

        fecha_actual = fecha
        dias_habiles = 0

        # CORRECCIÓN: Operación datetime + timedelta (VÁLIDA)
        while dias_habiles < 7:
            fecha_actual = fecha_actual + timedelta(days=1)  # datetime + timedelta = datetime
            
            dia_semana = fecha_actual.weekday()
            if dia_semana < 5 and not es_festivo(fecha_actual):
                dias_habiles += 1

        return fecha_actual

    except Exception as e:
        print(f"Error en calcular_plazo_oficio_cierre: {e}")
        return None


def actualizar_plazo_analisis(df):
    """
    Actualiza la columna 'Plazo de análisis' en el DataFrame.
    CORREGIDO: Manejo de errores mejorado
    """
    if 'Fecha de entrega de información' not in df.columns:
        return df

    df_actualizado = df.copy()

    # Asegurar que la columna existe
    if 'Plazo de análisis' not in df_actualizado.columns:
        df_actualizado['Plazo de análisis'] = ''

    for idx, row in df.iterrows():
        try:
            fecha_entrega = row.get('Fecha de entrega de información', None)
            if fecha_entrega and pd.notna(fecha_entrega) and str(fecha_entrega).strip() != '':
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
            print(f"Error procesando fila {idx}: {e}")
            continue

    return df_actualizado


def actualizar_plazo_cronograma(df):
    """
    Actualiza la columna 'Plazo de cronograma' en el DataFrame.
    CORREGIDO: Manejo de errores mejorado
    """
    if 'Plazo de análisis' not in df.columns:
        return df

    df_actualizado = df.copy()

    if 'Plazo de cronograma' not in df_actualizado.columns:
        df_actualizado['Plazo de cronograma'] = ''

    for idx, row in df.iterrows():
        try:
            plazo_analisis = row.get('Plazo de análisis', None)
            if plazo_analisis and pd.notna(plazo_analisis) and str(plazo_analisis).strip() != '':
                plazo_cronograma = calcular_plazo_cronograma(plazo_analisis)
                if plazo_cronograma is not None:
                    df_actualizado.at[idx, 'Plazo de cronograma'] = formatear_fecha(plazo_cronograma)
        except Exception as e:
            print(f"Error procesando cronograma fila {idx}: {e}")
            continue

    return df_actualizado


def actualizar_plazo_oficio_cierre(df):
    """
    Actualiza la columna 'Plazo de oficio de cierre' en el DataFrame.
    CORREGIDO: Manejo de errores mejorado
    """
    if 'Publicación' not in df.columns:
        return df

    df_actualizado = df.copy()

    if 'Plazo de oficio de cierre' not in df_actualizado.columns:
        df_actualizado['Plazo de oficio de cierre'] = ''

    for idx, row in df.iterrows():
        try:
            fecha_publicacion = row.get('Publicación', None)
            if fecha_publicacion and pd.notna(fecha_publicacion) and str(fecha_publicacion).strip() != '':
                plazo_oficio = calcular_plazo_oficio_cierre(fecha_publicacion)
                if plazo_oficio is not None:
                    df_actualizado.at[idx, 'Plazo de oficio de cierre'] = formatear_fecha(plazo_oficio)
        except Exception as e:
            print(f"Error procesando oficio cierre fila {idx}: {e}")
            continue

    return df_actualizado


# Funciones de prueba para verificar que todo funciona
def test_calcular_plazo_analisis():
    """Función de prueba corregida"""
    fechas_prueba = [
        "15/01/2025",
        "27/03/2025", 
        "30/04/2025",
        "20/12/2025"
    ]

    print("🧪 PROBANDO CORRECCIÓN DE PLAZOS...")
    for fecha in fechas_prueba:
        try:
            plazo = calcular_plazo_analisis(fecha)
            if plazo:
                print(f"✅ Fecha entrega: {fecha} -> Plazo análisis: {formatear_fecha(plazo)}")
            else:
                print(f"❌ Fecha entrega: {fecha} -> No se pudo calcular")
        except Exception as e:
            print(f"❌ Error con {fecha}: {e}")


if __name__ == "__main__":
    test_calcular_plazo_analisis()
    print("\n✅ CORRECCIÓN APLICADA:")
    print("   - procesar_fecha() siempre devuelve datetime")
    print("   - Todas las operaciones usan datetime + timedelta")
    print("   - Manejo de errores mejorado")
    print("   - Conversiones seguras date -> datetime")
