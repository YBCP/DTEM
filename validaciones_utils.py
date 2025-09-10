# validaciones_utils.py - CORREGIDO: Elimina evaluaciones ambiguas de Series
import pandas as pd
import numpy as np
from data_utils import procesar_fecha, calcular_porcentaje_avance
from datetime import datetime

def verificar_condiciones_estandares(row):
    """
    CORREGIDO: Ya no se requiere validación estricta de estándares.
    Elimina evaluaciones ambiguas de Series.
    """
    # Nueva lógica: siempre permitir, ya que "No aplica" es válido
    return True, []

def verificar_condicion_publicacion(row):
    """
    CORREGIDO: Simplificado para ser más permisivo.
    Elimina evaluaciones ambiguas de Series.
    """
    return True

def verificar_condiciones_oficio_cierre(row):
    """
    CORREGIDO: Simplificado drásticamente.
    Solo verifica que la etapa de Publicación esté completada.
    Elimina evaluaciones ambiguas de Series.
    """
    campos_incompletos = []

    # Solo verificar que la Publicación esté completada
    if 'Publicación' in row:
        valor_publicacion = row['Publicación']
        
        # CORRECCIÓN CRÍTICA: Verificar que no sea Series
        if isinstance(valor_publicacion, pd.Series):
            campos_incompletos.append("Error: valor de Publicación es Series")
        else:
            if pd.isna(valor_publicacion) or str(valor_publicacion).strip() == "":
                campos_incompletos.append("Debe completar la etapa de Publicación (tener fecha)")
    else:
        campos_incompletos.append("El campo Publicación no existe")

    return len(campos_incompletos) == 0, campos_incompletos

def obtener_valor_seguro(row, campo, default=''):
    """
    NUEVA FUNCIÓN: Obtiene un valor de forma segura evitando Series
    """
    try:
        if campo in row:
            valor = row[campo]
            # CORRECCIÓN CRÍTICA: Si es Series, devolver default
            if isinstance(valor, pd.Series):
                return default
            return valor if pd.notna(valor) else default
        return default
    except:
        return default

def validar_reglas_negocio(df):
    """
    CORREGIDO: Aplica nuevas reglas de negocio simplificadas.
    Elimina evaluaciones ambiguas de Series.
    """
    df_actualizado = df.copy()

    # Iterar sobre cada fila
    for idx, row in df.iterrows():
        # Regla 1: Si suscripción o entrega acuerdo de compromiso no está vacío, acuerdo de compromiso = SI
        suscripcion_valor = obtener_valor_seguro(row, 'Suscripción acuerdo de compromiso')
        if suscripcion_valor and str(suscripcion_valor).strip() != '':
            df_actualizado.at[idx, 'Acuerdo de compromiso'] = 'Si'
            # Recalcular porcentaje de avance
            if 'Porcentaje Avance' in df_actualizado.columns:
                df_actualizado.at[idx, 'Porcentaje Avance'] = calcular_porcentaje_avance(df_actualizado.iloc[idx])

        entrega_valor = obtener_valor_seguro(row, 'Entrega acuerdo de compromiso')
        if entrega_valor and str(entrega_valor).strip() != '':
            df_actualizado.at[idx, 'Acuerdo de compromiso'] = 'Si'
            # Recalcular porcentaje de avance
            if 'Porcentaje Avance' in df_actualizado.columns:
                df_actualizado.at[idx, 'Porcentaje Avance'] = calcular_porcentaje_avance(df_actualizado.iloc[idx])

        # Regla 2: Si análisis y cronograma tiene fecha, análisis de información y cronograma concertado = SI
        analisis_valor = obtener_valor_seguro(row, 'Análisis y cronograma')
        if analisis_valor and str(analisis_valor).strip() != '':
            fecha = procesar_fecha(analisis_valor)
            if fecha is not None:
                if 'Análisis de información' in df_actualizado.columns:
                    df_actualizado.at[idx, 'Análisis de información'] = 'Si'
                if 'Cronograma Concertado' in df_actualizado.columns:
                    df_actualizado.at[idx, 'Cronograma Concertado'] = 'Si'
                # Recalcular porcentaje de avance
                if 'Porcentaje Avance' in df_actualizado.columns:
                    df_actualizado.at[idx, 'Porcentaje Avance'] = calcular_porcentaje_avance(df_actualizado.iloc[idx])

        # Regla 3: Al introducir fecha en estándares, actualizar campos no completos a "No aplica"
        estandares_valor = obtener_valor_seguro(row, 'Estándares')
        if estandares_valor and str(estandares_valor).strip() != '':
            fecha = procesar_fecha(estandares_valor)
            if fecha is not None:
                # Campos de estándares a verificar
                campos_estandares_completo = [
                    'Registro (completo)', 'ET (completo)', 'CO (completo)',
                    'DD (completo)', 'REC (completo)', 'SERVICIO (completo)'
                ]
                
                for campo in campos_estandares_completo:
                    if campo in df_actualizado.columns:
                        valor_actual = obtener_valor_seguro(df_actualizado.iloc[idx], campo)
                        # Si no está "Completo", actualizar a "No aplica"
                        if str(valor_actual).strip().upper() != "COMPLETO":
                            df_actualizado.at[idx, campo] = "No aplica"
                # Recalcular porcentaje de avance
                if 'Porcentaje Avance' in df_actualizado.columns:
                    df_actualizado.at[idx, 'Porcentaje Avance'] = calcular_porcentaje_avance(df_actualizado.iloc[idx])

        # Regla 4: Si publicación tiene fecha, disponer datos temáticos = SI automáticamente
        publicacion_valor = obtener_valor_seguro(row, 'Publicación')
        if publicacion_valor and str(publicacion_valor).strip() != '':
            fecha = procesar_fecha(publicacion_valor)
            if fecha is not None and 'Disponer datos temáticos' in df_actualizado.columns:
                df_actualizado.at[idx, 'Disponer datos temáticos'] = 'Si'
                # Recalcular porcentaje de avance
                if 'Porcentaje Avance' in df_actualizado.columns:
                    df_actualizado.at[idx, 'Porcentaje Avance'] = calcular_porcentaje_avance(df_actualizado.iloc[idx])

        # Regla 5: Si oficio de cierre tiene fecha, actualizar estado a "Completado"
        fecha_oficio_valor = obtener_valor_seguro(row, 'Fecha de oficio de cierre')
        if fecha_oficio_valor and str(fecha_oficio_valor).strip() != '':
            fecha = procesar_fecha(fecha_oficio_valor)
            if fecha is not None:
                # Solo verificar que Publicación esté completada
                publicacion_check = obtener_valor_seguro(row, 'Publicación')
                tiene_publicacion = publicacion_check and str(publicacion_check).strip() != ''
                
                if tiene_publicacion:
                    # Actualizar estado a "Completado"
                    if 'Estado' in df_actualizado.columns:
                        df_actualizado.at[idx, 'Estado'] = 'Completado'
                    # Recalcular porcentaje de avance (será 100% automáticamente)
                    if 'Porcentaje Avance' in df_actualizado.columns:
                        df_actualizado.at[idx, 'Porcentaje Avance'] = calcular_porcentaje_avance(df_actualizado.iloc[idx])
                else:
                    # Si no tiene publicación, eliminar la fecha de oficio de cierre
                    df_actualizado.at[idx, 'Fecha de oficio de cierre'] = ''
                    # Y cambiar estado a "En proceso" si era "Completado"
                    estado_actual = obtener_valor_seguro(df_actualizado.iloc[idx], 'Estado')
                    if 'Estado' in df_actualizado.columns and estado_actual == 'Completado':
                        df_actualizado.at[idx, 'Estado'] = 'En proceso'
                    # Recalcular porcentaje de avance
                    if 'Porcentaje Avance' in df_actualizado.columns:
                        df_actualizado.at[idx, 'Porcentaje Avance'] = calcular_porcentaje_avance(df_actualizado.iloc[idx])
        
        # Regla 6: Si Estado es "Completado" pero no hay fecha de oficio de cierre, cambiar Estado a "En proceso"
        elif 'Estado' in df_actualizado.columns:
            estado_actual = obtener_valor_seguro(df_actualizado.iloc[idx], 'Estado')
            if estado_actual == 'Completado':
                # Verificar si hay fecha de oficio de cierre válida
                fecha_oficio_check = obtener_valor_seguro(row, 'Fecha de oficio de cierre')
                if not fecha_oficio_check or str(fecha_oficio_check).strip() == '':
                    df_actualizado.at[idx, 'Estado'] = 'En proceso'
                    # Recalcular porcentaje de avance
                    if 'Porcentaje Avance' in df_actualizado.columns:
                        df_actualizado.at[idx, 'Porcentaje Avance'] = calcular_porcentaje_avance(df_actualizado.iloc[idx])

    return df_actualizado

def mostrar_estado_validaciones(df, st_obj=None):
    """
    CORREGIDO: Muestra el estado actual de las validaciones simplificadas.
    Elimina evaluaciones ambiguas de Series.
    """
    resultados = []

    for idx, row in df.iterrows():
        resultado = {
            'Cod': obtener_valor_seguro(row, 'Cod'),
            'Entidad': obtener_valor_seguro(row, 'Entidad'),
            'Nivel Información ': obtener_valor_seguro(row, 'Nivel Información ')
        }

        # Validar Acuerdo de compromiso
        entrega_valor = obtener_valor_seguro(row, 'Entrega acuerdo de compromiso')
        tiene_entrega = entrega_valor and str(entrega_valor).strip() != ''

        acuerdo_valor = obtener_valor_seguro(row, 'Acuerdo de compromiso')
        tiene_acuerdo = acuerdo_valor and str(acuerdo_valor).strip().upper() in ['SI', 'SÍ', 'S', 'YES', 'Y', 'COMPLETO']

        if tiene_entrega and not tiene_acuerdo:
            resultado['Estado Acuerdo'] = 'Inconsistente'
        else:
            resultado['Estado Acuerdo'] = 'Correcto'

        # Validar Análisis de información
        analisis_fecha_valor = obtener_valor_seguro(row, 'Análisis y cronograma')
        tiene_fecha_analisis = analisis_fecha_valor and str(analisis_fecha_valor).strip() != ''

        analisis_info_valor = obtener_valor_seguro(row, 'Análisis de información')
        tiene_analisis_info = analisis_info_valor and str(analisis_info_valor).strip().upper() in ['SI', 'SÍ', 'S', 'YES', 'Y', 'COMPLETO']

        if tiene_fecha_analisis and not tiene_analisis_info:
            resultado['Estado Análisis'] = 'Inconsistente'
        else:
            resultado['Estado Análisis'] = 'Correcto'

        # Validar Estándares (ahora más permisivo)
        estandares_fecha_valor = obtener_valor_seguro(row, 'Estándares')
        tiene_fecha_estandares = estandares_fecha_valor and str(estandares_fecha_valor).strip() != ''

        if tiene_fecha_estandares:
            resultado['Estado Estándares'] = 'Correcto'
            resultado['Campos Incompletos'] = ''
        else:
            resultado['Estado Estándares'] = 'No aplicable'
            resultado['Campos Incompletos'] = ''

        # Validar Publicación (ahora automático)
        publicacion_fecha_valor = obtener_valor_seguro(row, 'Publicación')
        tiene_fecha_publicacion = publicacion_fecha_valor and str(publicacion_fecha_valor).strip() != ''

        if tiene_fecha_publicacion:
            resultado['Estado Publicación'] = 'Correcto'
        else:
            resultado['Estado Publicación'] = 'No aplicable'

        # Validar Oficio de cierre (solo Publicación requerida)
        oficio_fecha_valor = obtener_valor_seguro(row, 'Fecha de oficio de cierre')
        tiene_fecha_oficio = oficio_fecha_valor and str(oficio_fecha_valor).strip() != ''

        if tiene_fecha_oficio:
            valido, campos_incompletos = verificar_condiciones_oficio_cierre(row)
            if not valido:
                resultado['Estado Oficio Cierre'] = 'Inconsistente'
                resultado['Oficio Incompletos'] = ', '.join(campos_incompletos)
            else:
                resultado['Estado Oficio Cierre'] = 'Correcto'
                resultado['Oficio Incompletos'] = ''
        else:
            resultado['Estado Oficio Cierre'] = 'No aplicable'
            resultado['Oficio Incompletos'] = ''
            
        # Validar Estado "Completado" sin fecha de oficio de cierre
        estado_valor = obtener_valor_seguro(row, 'Estado')
        tiene_estado_completado = estado_valor == 'Completado'
        
        if tiene_estado_completado and not tiene_fecha_oficio:
            resultado['Estado Inconsistente'] = 'Sí (Completado sin fecha oficio)'
        else:
            resultado['Estado Inconsistente'] = 'No'

        resultados.append(resultado)

    # Crear DataFrame con los resultados
    resultados_df = pd.DataFrame(resultados)

    # Si hay un objeto Streamlit, mostrar advertencias
    if st_obj is not None:
        # Filtrar solo los registros con oficio de cierre inconsistentes
        oficio_inconsistentes = resultados_df[resultados_df['Estado Oficio Cierre'] == 'Inconsistente']

        if not oficio_inconsistentes.empty:
            st_obj.error(
                "No es posible diligenciar la Fecha de oficio de cierre. Debe tener la etapa de Publicación completada.")

            # Crear DataFrame para mostrar los registros con problemas
            df_oficio = oficio_inconsistentes[['Cod', 'Entidad', 'Nivel Información ', 'Oficio Incompletos']]
            st_obj.dataframe(df_oficio)

        # Filtrar registros con Estado "Completado" sin fecha de oficio de cierre
        estado_inconsistentes = resultados_df[resultados_df['Estado Inconsistente'] == 'Sí (Completado sin fecha oficio)']
        
        if not estado_inconsistentes.empty:
            st_obj.error(
                "Hay registros con Estado 'Completado' sin fecha de oficio de cierre. El Estado se cambiará a 'En proceso'.")
            
            # Crear DataFrame para mostrar los registros con problemas
            df_estado = estado_inconsistentes[['Cod', 'Entidad', 'Nivel Información ']]
            st_obj.dataframe(df_estado)

        # Filtrar registros con otras inconsistencias menores
        otras_inconsistencias = resultados_df[
            (resultados_df['Estado Acuerdo'] == 'Inconsistente') |
            (resultados_df['Estado Análisis'] == 'Inconsistente')
            ]

        if not otras_inconsistencias.empty:
            if oficio_inconsistentes.empty and estado_inconsistentes.empty:
                st_obj.warning("Se detectaron inconsistencias menores que se corregirán automáticamente:")
            else:
                st_obj.warning("Además, se detectaron inconsistencias menores que se corregirán automáticamente:")

            # Filtrar solo las columnas relevantes
            df_otras = otras_inconsistencias[
                ['Cod', 'Entidad', 'Nivel Información ', 'Estado Acuerdo', 'Estado Análisis']]
            st_obj.dataframe(df_otras)
        elif oficio_inconsistentes.empty and estado_inconsistentes.empty:
            # No hay inconsistencias
            st_obj.success("Todos los registros cumplen con las reglas de validación simplificadas.")

    return resultados_df
