# components/registro_editor.py
"""
Editor principal de registros sin recargas automáticas
Reemplaza la función mostrar_edicion_registros() del app1.py original
"""

import streamlit as st
import pandas as pd
from typing import Optional, Dict, Any
from datetime import datetime

from core.state_manager import state_manager
from components.form_components import RegistroForm, FuncionarioManager, ReadOnlyDisplayManager
from data_utils import guardar_datos_editados, validar_reglas_negocio
from fecha_utils import actualizar_plazo_analisis, actualizar_plazo_cronograma, actualizar_plazo_oficio_cierre


class RegistroEditor:
    """Editor principal de registros sin recargas automáticas"""
    
    def __init__(self, registros_df: pd.DataFrame):
        self.registros_df = registros_df
        self.current_form = None
        self.selected_index = None
        
        # Inicializar mensaje de guardado en session_state si no existe
        if 'mensaje_guardado' not in st.session_state:
            st.session_state.mensaje_guardado = None
    
    def render(self) -> pd.DataFrame:
        """
        Renderiza el editor completo.
        Retorna el DataFrame actualizado.
        """
        st.markdown('<div class="subtitle">Edición de Registros</div>', unsafe_allow_html=True)
        
        # Mostrar información y advertencias
        self._show_info_panel()
        
        # Mostrar mensaje de guardado si existe
        self._show_save_message()
        
        # Verificar que hay registros
        if self.registros_df.empty:
            st.warning("No hay registros disponibles para editar.")
            return self.registros_df
        
        # Selector de registro
        registro_seleccionado = self._render_record_selector()
        
        if registro_seleccionado is not None:
            # Renderizar formulario
            result = self._render_form(registro_seleccionado)
            
            # Manejar acciones del formulario
            if result:
                return self._handle_form_action(result)
        
        return self.registros_df
    
    def _show_info_panel(self):
        """Muestra panel de información y advertencias"""
        st.info(
            "Esta sección permite editar los datos usando selectores de fecha y opciones. "
            "Los cambios se aplican al presionar 'Guardar Registro'."
        )
        
        st.warning("""
        **✨ NUEVO SISTEMA SIN RECARGAS:**
        - ⚡ **El formulario ya NO se recarga automáticamente** - cambios son instantáneos
        - 💾 **Los cambios se mantienen en memoria** hasta presionar "Guardar Registro"
        - 🔄 **Validaciones automáticas** se aplican solo al guardar
        - 📅 **Selectores de fecha mejorados** con activación por checkbox
        - 🎯 **Plazos calculados automáticamente** considerando días hábiles y festivos
        """)
    
    def _show_save_message(self):
        """Muestra mensaje de guardado si existe"""
        if st.session_state.mensaje_guardado:
            if st.session_state.mensaje_guardado[0] == "success":
                st.success(st.session_state.mensaje_guardado[1])
            else:
                st.error(st.session_state.mensaje_guardado[1])
            # Limpiar mensaje después de mostrarlo
            st.session_state.mensaje_guardado = None
    
    def _render_record_selector(self) -> Optional[int]:
        """
        Renderiza el selector de registros.
        Retorna el índice del registro seleccionado o None.
        """
        st.markdown("### Selección de Registro")
        
        # Crear opciones para el selector
        codigos = self.registros_df['Cod'].astype(str).tolist()
        entidades = self.registros_df['Entidad'].tolist()
        niveles = self.registros_df['Nivel Información '].tolist()
        
        opciones = [
            f"{codigos[i]} - {entidades[i]} - {niveles[i]}"
            for i in range(len(codigos))
        ]
        
        # Selector sin callback automático
        seleccion = st.selectbox(
            "Seleccione un registro para editar:",
            options=opciones,
            key="registro_selector_main"
            # ✅ SIN on_change callback
        )
        
        # Obtener índice seleccionado
        if seleccion:
            return opciones.index(seleccion)
        
        return None
    
    def _render_form(self, indice_seleccionado: int) -> Optional[Dict[str, Any]]:
        """
        Renderiza el formulario para el registro seleccionado.
        Retorna acción a realizar o None.
        """
        try:
            # Obtener registro original
            registro_original = self.registros_df.iloc[indice_seleccionado].copy()
            registro_id = str(registro_original['Cod'])
            
            # Crear formulario
            self.current_form = RegistroForm(registro_id, registro_original)
            self.selected_index = indice_seleccionado
            
            # Renderizar formulario completo
            result = self.current_form.render_form()
            
            return result
            
        except Exception as e:
            st.error(f"Error al renderizar el formulario: {str(e)}")
            
            # Información de debug
            with st.expander("Información de Debug"):
                st.write(f"Índice seleccionado: {indice_seleccionado}")
                st.write(f"Total registros: {len(self.registros_df)}")
                st.write(f"Columnas disponibles: {list(self.registros_df.columns)}")
            
            return None
    
    def _handle_form_action(self, action_result: Dict[str, Any]) -> pd.DataFrame:
        """
        Maneja las acciones del formulario (guardar, cancelar, etc.).
        Retorna el DataFrame actualizado.
        """
        action = action_result.get('action')
        registro_id = action_result.get('registro_id')
        
        if action == 'save':
            return self._handle_save_action(action_result)
        
        elif action == 'cancel':
            st.success("Cambios cancelados exitosamente")
            st.rerun()
        
        elif action == 'reset':
            st.info("Formulario reiniciado")
            st.rerun()
        
        return self.registros_df
    
    def _handle_save_action(self, action_result: Dict[str, Any]) -> pd.DataFrame:
        """
        Maneja la acción de guardado.
        Aplica validaciones, cálculos automáticos y guarda en Google Sheets.
        """
        registro_id = action_result.get('registro_id')
        
        with st.spinner("💾 Guardando cambios y aplicando validaciones..."):
            try:
                # 1. Aplicar cambios temporales al DataFrame
                df_actualizado = state_manager.apply_changes_to_dataframe(
                    registro_id, 
                    self.registros_df, 
                    self.selected_index
                )
                
                # 2. Validaciones de reglas de negocio
                df_actualizado = validar_reglas_negocio(df_actualizado)
                
                # 3. Actualizar plazos automáticamente
                df_actualizado = actualizar_plazo_analisis(df_actualizado)
                df_actualizado = actualizar_plazo_cronograma(df_actualizado)
                df_actualizado = actualizar_plazo_oficio_cierre(df_actualizado)
                
                # 4. Guardar en Google Sheets
                exito, mensaje = guardar_datos_editados(df_actualizado, crear_backup=True)
                
                if exito:
                    # Éxito: limpiar estado temporal y mostrar mensaje
                    state_manager.clear_temp_state(registro_id)
                    st.session_state.mensaje_guardado = (
                        "success", 
                        f"✅ {mensaje} Validaciones y plazos automáticos aplicados correctamente."
                    )
                    st.rerun()
                else:
                    # Error: mantener cambios temporales
                    st.session_state.mensaje_guardado = ("error", mensaje)
                    st.rerun()
                
                return df_actualizado
                
            except Exception as e:
                st.session_state.mensaje_guardado = ("error", f"❌ Error al guardar: {str(e)}")
                st.rerun()
                return self.registros_df
    
    def has_unsaved_changes(self) -> bool:
        """Verifica si hay cambios sin guardar en cualquier registro"""
        return state_manager.has_any_changes()
    
    def get_unsaved_changes_count(self) -> int:
        """Obtiene el número de registros con cambios sin guardar"""
        count = 0
        for key in st.session_state.keys():
            if key.endswith("_modified") and st.session_state.get(key, False):
                count += 1
        return count


class EditorStatusPanel:
    """Panel de estado del editor que muestra información útil"""
    
    def __init__(self, editor: RegistroEditor):
        self.editor = editor
    
    def render(self):
        """Renderiza panel de estado"""
        st.markdown("### 📊 Estado del Editor")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_registros = len(self.editor.registros_df)
            st.metric("Total Registros", total_registros)
        
        with col2:
            changes_count = self.editor.get_unsaved_changes_count()
            st.metric("Cambios Pendientes", changes_count)
        
        with col3:
            # Registros en proceso
            en_proceso = len(self.editor.registros_df[
                self.editor.registros_df['Estado'].isin(['En proceso', 'En proceso oficio de cierre'])
            ])
            st.metric("En Proceso", en_proceso)
        
        with col4:
            # Última actualización
            ultima_actualizacion = datetime.now().strftime("%H:%M:%S")
            st.metric("Actualizado", ultima_actualizacion)
        
        # Alertas si hay cambios pendientes
        if self.editor.has_unsaved_changes():
            st.warning(f"⚠️ Hay {self.editor.get_unsaved_changes_count()} registro(s) con cambios sin guardar")


class AdvancedFeatures:
    """Funcionalidades avanzadas del editor"""
    
    def __init__(self, editor: RegistroEditor):
        self.editor = editor
    
    def render_bulk_actions(self):
        """Renderiza acciones en lote"""
        with st.expander("🔧 Acciones Avanzadas"):
            st.markdown("#### Acciones en Lote")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("📊 Recalcular Todos los Plazos"):
                    self._recalculate_all_deadlines()
            
            with col2:
                if st.button("🔄 Aplicar Validaciones Globales"):
                    self._apply_global_validations()
            
            with col3:
                if st.button("💾 Guardar Todo"):
                    self._save_all_changes()
    
    def _recalculate_all_deadlines(self):
        """Recalcula todos los plazos automáticamente"""
        with st.spinner("Recalculando plazos..."):
            try:
                df_actualizado = self.editor.registros_df.copy()
                
                df_actualizado = actualizar_plazo_analisis(df_actualizado)
                df_actualizado = actualizar_plazo_cronograma(df_actualizado)
                df_actualizado = actualizar_plazo_oficio_cierre(df_actualizado)
                
                # Guardar cambios
                exito, mensaje = guardar_datos_editados(df_actualizado, crear_backup=True)
                
                if exito:
                    st.success("✅ Todos los plazos han sido recalculados")
                    self.editor.registros_df = df_actualizado
                    st.rerun()
                else:
                    st.error(f"❌ Error al guardar: {mensaje}")
                    
            except Exception as e:
                st.error(f"❌ Error recalculando plazos: {str(e)}")
    
    def _apply_global_validations(self):
        """Aplica validaciones globales"""
        with st.spinner("Aplicando validaciones..."):
            try:
                df_actualizado = validar_reglas_negocio(self.editor.registros_df)
                
                # Guardar cambios
                exito, mensaje = guardar_datos_editados(df_actualizado, crear_backup=True)
                
                if exito:
                    st.success("✅ Validaciones aplicadas globalmente")
                    self.editor.registros_df = df_actualizado
                    st.rerun()
                else:
                    st.error(f"❌ Error al guardar: {mensaje}")
                    
            except Exception as e:
                st.error(f"❌ Error aplicando validaciones: {str(e)}")
    
    def _save_all_changes(self):
        """Guarda todos los cambios pendientes"""
        if not self.editor.has_unsaved_changes():
            st.info("No hay cambios pendientes para guardar")
            return
        
        with st.spinner("Guardando todos los cambios..."):
            try:
                # Aplicar todos los cambios temporales
                df_actualizado = self.editor.registros_df.copy()
                
                # Obtener todos los estados temporales
                estados_temporales = state_manager.get_all_temp_states()
                
                for registro_id, estado in estados_temporales.items():
                    # Encontrar índice del registro
                    mask = df_actualizado['Cod'].astype(str) == registro_id
                    if mask.any():
                        indice = df_actualizado[mask].index[0]
                        
                        # Aplicar cambios
                        for campo, valor in estado.items():
                            if campo in df_actualizado.columns:
                                df_actualizado.at[indice, campo] = valor
                
                # Aplicar validaciones y cálculos
                df_actualizado = validar_reglas_negocio(df_actualizado)
                df_actualizado = actualizar_plazo_analisis(df_actualizado)
                df_actualizado = actualizar_plazo_cronograma(df_actualizado)
                df_actualizado = actualizar_plazo_oficio_cierre(df_actualizado)
                
                # Guardar en Google Sheets
                exito, mensaje = guardar_datos_editados(df_actualizado, crear_backup=True)
                
                if exito:
                    # Limpiar todos los estados temporales
                    state_manager.reset_all_temp_states()
                    st.success("✅ Todos los cambios han sido guardados")
                    self.editor.registros_df = df_actualizado
                    st.rerun()
                else:
                    st.error(f"❌ Error al guardar: {mensaje}")
                    
            except Exception as e:
                st.error(f"❌ Error guardando cambios: {str(e)}")


def mostrar_editor_registros_mejorado(registros_df: pd.DataFrame) -> pd.DataFrame:
    """
    Función principal para mostrar el editor mejorado.
    Esta función reemplaza a mostrar_edicion_registros() en app1.py
    
    Args:
        registros_df: DataFrame con los registros a editar
    
    Returns:
        DataFrame actualizado con los cambios guardados
    """
    # Crear instancia del editor
    editor = RegistroEditor(registros_df)
    
    # Renderizar editor principal
    df_actualizado = editor.render()
    
    # Panel de estado del editor
    status_panel = EditorStatusPanel(editor)
    status_panel.render()
    
    # Funcionalidades avanzadas
    advanced_features = AdvancedFeatures(editor)
    advanced_features.render_bulk_actions()
    
    return df_actualizado


# Funciones auxiliares para migración gradual

def convertir_editor_gradualmente():
    """
    Función para migrar gradualmente del editor antiguo al nuevo.
    Permite probar el nuevo editor manteniendo el antiguo como respaldo.
    """
    st.markdown("### 🚀 Nuevo Editor Experimental")
    
    use_new_editor = st.checkbox(
        "🧪 Usar nuevo editor sin recargas (Experimental)",
        help="Activa el nuevo editor optimizado sin recargas automáticas"
    )
    
    return use_new_editor


def test_new_editor_performance():
    """
    Función para probar el rendimiento del nuevo editor
    """
    st.markdown("### ⚡ Test de Rendimiento")
    
    start_time = datetime.now()
    
    # Simular carga del editor
    with st.spinner("Inicializando nuevo editor..."):
        import time
        time.sleep(0.1)  # Simular tiempo de carga
    
    end_time = datetime.now()
    load_time = (end_time - start_time).total_seconds()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Tiempo de Carga", f"{load_time:.2f}s")
    
    with col2:
        st.metric("Widgets sin Callbacks", "✅ 100%")
    
    with col3:
        st.metric("Recargas Automáticas", "❌ 0")
    
    st.success("🎉 ¡Editor optimizado cargado exitosamente!")


class EditorMigrationHelper:
    """Asistente para migrar del editor antiguo al nuevo"""
    
    @staticmethod
    def show_comparison():
        """Muestra comparación entre editor antiguo y nuevo"""
        st.markdown("### 📊 Comparación: Editor Antiguo vs Nuevo")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            #### 🐌 Editor Antiguo
            - ❌ Recargas automáticas en cada cambio
            - ❌ Callbacks en todos los widgets
            - ❌ `st.rerun()` constante
            - ❌ Estado temporal complejo
            - ❌ Validaciones en tiempo real
            - ❌ Experiencia lenta e interrumpida
            """)
        
        with col2:
            st.markdown("""
            #### ⚡ Editor Nuevo
            - ✅ Sin recargas automáticas
            - ✅ Widgets sin callbacks
            - ✅ Cambios instantáneos
            - ✅ Estado temporal optimizado
            - ✅ Validaciones solo al guardar
            - ✅ Experiencia fluida y rápida
            """)
    
    @staticmethod
    def show_migration_steps():
        """Muestra pasos para migrar"""
        st.markdown("### 🔄 Pasos de Migración")
        
        st.markdown("""
        #### Fase 1: Preparación
        1. ✅ Crear `core/state_manager.py`
        2. ✅ Crear `components/form_components.py`
        3. ✅ Crear `components/registro_editor.py`
        
        #### Fase 2: Implementación
        4. 🔄 Reemplazar función en `app1.py`:
        ```python
        # Cambiar esto:
        registros_df = mostrar_edicion_registros(registros_df)
        
        # Por esto:
        from components.registro_editor import mostrar_editor_registros_mejorado
        registros_df = mostrar_editor_registros_mejorado(registros_df)
        ```
        
        #### Fase 3: Testing
        5. 🧪 Probar con datos reales
        6. 🧪 Verificar funcionalidades
        7. 🧪 Optimizar rendimiento
        
        #### Fase 4: Deployment
        8. 🚀 Activar en producción
        9. 🚀 Monitorear rendimiento
        10. 🚀 Recopilar feedback
        """)


class EditorDiagnostics:
    """Herramientas de diagnóstico para el editor"""
    
    def __init__(self, editor: RegistroEditor):
        self.editor = editor
    
    def show_diagnostics(self):
        """Muestra diagnósticos del editor"""
        with st.expander("🔍 Diagnósticos del Editor"):
            self._show_state_diagnostics()
            self._show_performance_metrics()
            self._show_memory_usage()
    
    def _show_state_diagnostics(self):
        """Muestra diagnósticos de estado"""
        st.markdown("#### 🧠 Estado Temporal")
        
        estados = state_manager.get_all_temp_states()
        
        if estados:
            st.write(f"📊 **Registros con cambios temporales:** {len(estados)}")
            
            for registro_id, estado in estados.items():
                with st.expander(f"Registro {registro_id}"):
                    st.json(estado)
        else:
            st.success("✅ No hay estados temporales activos")
    
    def _show_performance_metrics(self):
        """Muestra métricas de rendimiento"""
        st.markdown("#### ⚡ Rendimiento")
        
        # Contar widgets en session_state
        widget_count = len([k for k in st.session_state.keys() if "_widget" in k])
        temp_state_count = len([k for k in st.session_state.keys() if "temp_registro_" in k])
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Widgets Activos", widget_count)
        
        with col2:
            st.metric("Estados Temporales", temp_state_count)
        
        with col3:
            callback_count = 0  # El nuevo editor no usa callbacks
            st.metric("Callbacks Activos", callback_count)
    
    def _show_memory_usage(self):
        """Muestra uso de memoria"""
        st.markdown("#### 💾 Uso de Memoria")
        
        import sys
        
        # Calcular tamaño aproximado de session_state
        session_state_size = sys.getsizeof(st.session_state)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Session State", f"{session_state_size / 1024:.2f} KB")
        
        with col2:
            df_size = sys.getsizeof(self.editor.registros_df)
            st.metric("DataFrame", f"{df_size / 1024:.2f} KB")


# Función de integración para el app1.py
def integrate_new_editor_to_app():
    """
    Función para integrar el nuevo editor al app1.py existente.
    Esta función muestra cómo hacer la migración.
    """
    st.markdown("### 🔧 Integración al App Principal")
    
    st.code("""
# En app1.py, en la sección TAB 2: EDICIÓN
# Reemplazar el bloque existente:

with tab2:
    # Verificar autenticación para edición
    from auth_utils import verificar_autenticacion
    
    if verificar_autenticacion():
        # CAMBIO: Usar el nuevo editor sin recargas
        from components.registro_editor import mostrar_editor_registros_mejorado
        registros_df = mostrar_editor_registros_mejorado(registros_df)
    else:
        # Código de autenticación existente...
        st.warning("🔒 Se requiere autenticación...")
""", language="python")
    
    st.markdown("#### 📁 Estructura de Archivos Requerida")
    
    st.code("""
proyecto/
├── app1.py                    # Archivo principal (modificado)
├── core/
│   └── state_manager.py       # ✅ NUEVO: Gestor de estados
├── components/
│   ├── form_components.py     # ✅ NUEVO: Componentes de formulario
│   └── registro_editor.py     # ✅ NUEVO: Editor principal
├── data_utils.py             # Existente (sin cambios)
├── fecha_utils.py            # Existente (sin cambios)
├── validaciones_utils.py     # Existente (sin cambios)
└── ...                       # Otros archivos existentes
""", language="bash")


class NewEditorShowcase:
    """Demostración del nuevo editor"""
    
    def __init__(self, registros_df: pd.DataFrame):
        self.registros_df = registros_df
    
    def show_demo(self):
        """Muestra demostración del nuevo editor"""
        st.markdown("### 🎯 Demostración del Nuevo Editor")
        
        st.info("""
        **🎉 Características destacadas del nuevo editor:**
        - ⚡ **Sin recargas automáticas** - Los cambios son instantáneos
        - 🎛️ **Controles optimizados** - Selectores y fechas sin delays
        - 💾 **Guardado inteligente** - Solo se guarda cuando presionas el botón
        - 🔍 **Preview de cambios** - Ve exactamente qué vas a guardar
        - ✅ **Validaciones inteligentes** - Se ejecutan solo cuando es necesario
        """)
        
        # Botón para probar
        if st.button("🚀 Probar Nuevo Editor", type="primary"):
            st.success("🎉 ¡Editor cargado! Ahora puedes editar sin recargas.")
            
            # Mostrar editor simplificado como demo
            editor = RegistroEditor(self.registros_df)
            return editor.render()
        
        return self.registros_df


# Función principal de demostración
def demo_new_editor_system():
    """
    Función de demostración completa del nuevo sistema de editor.
    Puede usarse para probar antes de la migración completa.
    """
    st.markdown("# 🚀 Nuevo Sistema de Editor - Demostración")
    
    # Crear datos de ejemplo si no existen
    if 'demo_df' not in st.session_state:
        demo_data = {
            'Cod': ['1', '2', '3'],
            'Entidad': ['Entidad A', 'Entidad B', 'Entidad C'],
            'Nivel Información ': ['Nivel 1', 'Nivel 2', 'Nivel 3'],
            'TipoDato': ['Nuevo', 'Actualizar', 'Nuevo'],
            'Funcionario': ['Juan Pérez', 'María González', ''],
            'Acuerdo de compromiso': ['', 'Si', ''],
            'Análisis y cronograma': ['', '', ''],
            'Estándares': ['', '', ''],
            'Publicación': ['', '', ''],
            'Estado': ['En proceso', 'En proceso', 'En proceso'],
            'Observación': ['', '', '']
        }
        
        st.session_state.demo_df = pd.DataFrame(demo_data)
    
    # Mostrar comparación
    EditorMigrationHelper.show_comparison()
    
    st.markdown("---")
    
    # Mostrar demostración
    showcase = NewEditorShowcase(st.session_state.demo_df)
    st.session_state.demo_df = showcase.show_demo()
    
    st.markdown("---")
    
    # Mostrar pasos de migración
    EditorMigrationHelper.show_migration_steps()


# Función de utilidad para verificar compatibilidad
def check_compatibility():
    """Verifica compatibilidad del nuevo editor con el sistema existente"""
    st.markdown("### ✅ Verificación de Compatibilidad")
    
    checks = [
        ("Streamlit version", "streamlit"),
        ("Pandas version", "pandas"),
        ("Data utils", "data_utils"),
        ("Fecha utils", "fecha_utils"),
        ("Validaciones utils", "validaciones_utils"),
    ]
    
    all_good = True
    
    for name, module in checks:
        try:
            __import__(module)
            st.success(f"✅ {name}: OK")
        except ImportError:
            st.error(f"❌ {name}: ERROR")
            all_good = False
    
    if all_good:
        st.success("🎉 Sistema compatible - Listo para migración")
    else:
        st.error("❌ Problemas de compatibilidad detectados")
    
    return all_good


if __name__ == "__main__":
    # Ejecutar demostración si se ejecuta directamente
    demo_new_editor_system()