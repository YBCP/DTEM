# components/form_components.py
"""
Componentes de formulario especializados sin recargas automáticas
Reemplaza los widgets con callbacks que causan st.rerun()
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date
from typing import List, Any, Optional, Callable
from core.state_manager import state_manager, date_state_manager
from data_utils import procesar_fecha


class FormWidget:
    """Clase base para widgets de formulario sin recargas automáticas"""
    
    def __init__(self, registro_id: str, campo: str, label: str):
        self.registro_id = registro_id
        self.campo = campo
        self.label = label
        self.widget_key = state_manager.get_widget_key(registro_id, campo)
    
    def get_current_value(self, default: Any = ""):
        """Obtiene el valor actual del estado temporal"""
        return state_manager.get_field_value(self.registro_id, self.campo, default)
    
    def render_widget(self, **kwargs):
        """Método a ser sobrescrito por subclases"""
        raise NotImplementedError


class SelectboxWidget(FormWidget):
    """Selectbox sin callbacks automáticos"""
    
    def render(self, options: List[str], help_text: str = None, disabled: bool = False) -> Any:
        """Renderiza selectbox sin callback automático"""
        valor_actual = self.get_current_value()
        
        # Determinar índice actual
        try:
            index = options.index(valor_actual) if valor_actual in options else 0
        except (ValueError, TypeError):
            index = 0
        
        # Renderizar widget SIN on_change
        return st.selectbox(
            self.label,
            options=options,
            index=index,
            key=self.widget_key,
            help=help_text,
            disabled=disabled
            # ✅ NO HAY on_change - esta es la clave
        )


class TextInputWidget(FormWidget):
    """Text input sin callbacks automáticos"""
    
    def render(self, placeholder: str = "", help_text: str = None, disabled: bool = False) -> str:
        """Renderiza text input sin callback automático"""
        valor_actual = self.get_current_value()
        
        return st.text_input(
            self.label,
            value=valor_actual,
            key=self.widget_key,
            placeholder=placeholder,
            help=help_text,
            disabled=disabled
            # ✅ NO HAY on_change
        )


class TextAreaWidget(FormWidget):
    """Text area sin callbacks automáticos"""
    
    def render(self, height: int = 100, help_text: str = None, disabled: bool = False) -> str:
        """Renderiza text area sin callback automático"""
        valor_actual = self.get_current_value()
        
        return st.text_area(
            self.label,
            value=valor_actual,
            key=self.widget_key,
            height=height,
            help=help_text,
            disabled=disabled
            # ✅ NO HAY on_change
        )


class DateWidget(FormWidget):
    """Widget de fecha con checkbox para activar/desactivar SIN recargas"""
    
    def render(self, help_text: str = None, disabled: bool = False) -> tuple[bool, Any]:
        """
        Renderiza selector de fecha con checkbox.
        Retorna: (tiene_fecha, valor_fecha)
        """
        # Obtener estado actual
        tiene_fecha, valor_fecha = date_state_manager.get_date_state(self.registro_id, self.campo)
        
        # Crear contenedor
        with st.container():
            col_check, col_fecha, col_clear = st.columns([1, 6, 1])
            
            with col_check:
                # Checkbox para activar/desactivar fecha SIN callback
                checkbox_key = f"{self.widget_key}_checkbox"
                usar_fecha = st.checkbox(
                    "📅",
                    value=tiene_fecha,
                    key=checkbox_key,
                    help="Marcar para usar fecha"
                    # ✅ NO HAY on_change
                )
            
            with col_fecha:
                if usar_fecha:
                    # Convertir valor a date si es necesario
                    if valor_fecha:
                        try:
                            fecha_obj = procesar_fecha(valor_fecha)
                            if fecha_obj:
                                fecha_valor = fecha_obj.date() if isinstance(fecha_obj, datetime) else fecha_obj
                            else:
                                fecha_valor = datetime.now().date()
                        except:
                            fecha_valor = datetime.now().date()
                    else:
                        fecha_valor = datetime.now().date()
                    
                    # Date input SIN callback
                    fecha_input = st.date_input(
                        self.label,
                        value=fecha_valor,
                        key=self.widget_key,
                        help=help_text,
                        disabled=disabled
                        # ✅ NO HAY on_change
                    )
                    
                    return True, fecha_input
                else:
                    # Campo deshabilitado
                    st.text_input(
                        self.label,
                        value="(Sin fecha asignada)",
                        disabled=True,
                        key=f"{self.widget_key}_disabled"
                    )
                    return False, None
            
            with col_clear:
                if usar_fecha:
                    # Botón para limpiar fecha
                    if st.button("🗑️", key=f"{self.widget_key}_clear", help="Limpiar fecha"):
                        # Marcar para limpiar en el próximo guardado
                        st.session_state[f"{self.widget_key}_clear_flag"] = True
                        st.success("Fecha marcada para limpiar")
                else:
                    st.write("")  # Espaciador
        
        return False, None


class FormSection:
    """Sección de formulario que agrupa widgets relacionados"""
    
    def __init__(self, registro_id: str, titulo: str):
        self.registro_id = registro_id
        self.titulo = titulo
        self.widgets = []
    
    def add_selectbox(self, campo: str, label: str, options: List[str], **kwargs) -> SelectboxWidget:
        """Agrega un selectbox a la sección"""
        widget = SelectboxWidget(self.registro_id, campo, label)
        self.widgets.append((widget, 'selectbox', options, kwargs))
        return widget
    
    def add_text_input(self, campo: str, label: str, **kwargs) -> TextInputWidget:
        """Agrega un text input a la sección"""
        widget = TextInputWidget(self.registro_id, campo, label)
        self.widgets.append((widget, 'text_input', None, kwargs))
        return widget
    
    def add_text_area(self, campo: str, label: str, **kwargs) -> TextAreaWidget:
        """Agrega un text area a la sección"""
        widget = TextAreaWidget(self.registro_id, campo, label)
        self.widgets.append((widget, 'text_area', None, kwargs))
        return widget
    
    def add_date(self, campo: str, label: str, **kwargs) -> DateWidget:
        """Agrega un date widget a la sección"""
        widget = DateWidget(self.registro_id, campo, label)
        self.widgets.append((widget, 'date', None, kwargs))
        return widget
    
    def render_section(self):
        """Renderiza toda la sección"""
        if self.titulo:
            st.markdown(f"### {self.titulo}")
        
        # Renderizar widgets pero NO capturar valores aquí
        # Los valores se capturarán al momento de guardar
        for widget, tipo, options, kwargs in self.widgets:
            if tipo == 'selectbox':
                widget.render(options, **kwargs)
            elif tipo == 'text_input':
                widget.render(**kwargs)
            elif tipo == 'text_area':
                widget.render(**kwargs)
            elif tipo == 'date':
                widget.render(**kwargs)


class RegistroForm:
    """Formulario completo para edición de registros SIN recargas automáticas"""
    
    def __init__(self, registro_id: str, registro_original: pd.Series):
        self.registro_id = registro_id
        self.registro_original = registro_original
        
        # Inicializar estado temporal
        self.temp_key = state_manager.initialize_temp_state(registro_id, registro_original)
        
        # Crear secciones
        self.sections = []
        self._setup_sections()
    
    def _setup_sections(self):
        """Configura las secciones del formulario"""
        
        # Sección 1: Información Básica
        seccion_basica = FormSection(self.registro_id, "1. Información Básica")
        seccion_basica.add_selectbox(
            'TipoDato', 
            'Tipo de Dato', 
            ["", "Nuevo", "Actualizar"]
        )
        seccion_basica.add_selectbox(
            'Mes Proyectado',
            'Mes Proyectado',
            ["", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
             "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
        )
        seccion_basica.add_selectbox(
            'Frecuencia actualizacion ',
            'Frecuencia de actualización',
            ["", "Diaria", "Semanal", "Mensual", "Trimestral", "Semestral", "Anual"]
        )
        self.sections.append(seccion_basica)
        
        # Sección 2: Acuerdos y Compromisos
        seccion_acuerdos = FormSection(self.registro_id, "2. Acuerdos y Compromisos")
        seccion_acuerdos.add_selectbox(
            'Actas de acercamiento y manifestación de interés',
            'Actas de acercamiento y manifestación de interés',
            ["", "Si", "No"]
        )
        seccion_acuerdos.add_date(
            'Suscripción acuerdo de compromiso',
            'Suscripción acuerdo de compromiso'
        )
        seccion_acuerdos.add_date(
            'Entrega acuerdo de compromiso',
            'Entrega acuerdo de compromiso'
        )
        seccion_acuerdos.add_selectbox(
            'Acuerdo de compromiso',
            'Acuerdo de compromiso',
            ["", "Si", "No"]
        )
        self.sections.append(seccion_acuerdos)
        
        # Sección 3: Gestión de Información
        seccion_gestion = FormSection(self.registro_id, "3. Gestión de Información")
        seccion_gestion.add_selectbox(
            'Gestion acceso a los datos y documentos requeridos ',
            'Gestión acceso a los datos y documentos requeridos',
            ["", "Si", "No"]
        )
        seccion_gestion.add_date(
            'Fecha de entrega de información',
            'Fecha de entrega de información'
        )
        self.sections.append(seccion_gestion)
        
        # Sección 4: Análisis y Cronograma
        seccion_analisis = FormSection(self.registro_id, "4. Análisis y Cronograma")
        seccion_analisis.add_date(
            'Análisis y cronograma',
            'Análisis y cronograma (fecha real)'
        )
        seccion_analisis.add_selectbox(
            'Cronograma Concertado',
            'Cronograma Concertado',
            ["", "Si", "No"]
        )
        seccion_analisis.add_selectbox(
            'Seguimiento a los acuerdos',
            'Seguimiento a los acuerdos',
            ["", "Si", "No"]
        )
        self.sections.append(seccion_analisis)
        
        # Sección 5: Estándares
        seccion_estandares = FormSection(self.registro_id, "5. Estándares")
        
        # Campos de estándares completos
        campos_estandares = [
            'Registro (completo)', 'ET (completo)', 'CO (completo)',
            'DD (completo)', 'REC (completo)', 'SERVICIO (completo)'
        ]
        
        for campo in campos_estandares:
            seccion_estandares.add_selectbox(
                campo,
                campo,
                ["", "Completo", "No aplica"]
            )
        
        seccion_estandares.add_date(
            'Estándares (fecha programada)',
            'Estándares (fecha programada)'
        )
        seccion_estandares.add_date(
            'Estándares',
            'Estándares (fecha real)'
        )
        self.sections.append(seccion_estandares)
        
        # Sección 6: Publicación
        seccion_publicacion = FormSection(self.registro_id, "6. Publicación")
        
        campos_publicacion = [
            'Resultados de orientación técnica',
            'Verificación del servicio web geográfico',
            'Verificar Aprobar Resultados',
            'Revisar y validar los datos cargados en la base de datos',
            'Aprobación resultados obtenidos en la rientación',
            'Disponer datos temáticos',
            'Catálogo de recursos geográficos'
        ]
        
        for campo in campos_publicacion:
            seccion_publicacion.add_selectbox(
                campo,
                campo,
                ["", "Si", "No"]
            )
        
        seccion_publicacion.add_date(
            'Fecha de publicación programada',
            'Fecha de publicación programada'
        )
        seccion_publicacion.add_date(
            'Publicación',
            'Publicación (fecha real)'
        )
        self.sections.append(seccion_publicacion)
        
        # Sección 7: Cierre
        seccion_cierre = FormSection(self.registro_id, "7. Cierre")
        seccion_cierre.add_selectbox(
            'Oficios de cierre',
            'Oficios de cierre',
            ["", "Si", "No"]
        )
        seccion_cierre.add_date(
            'Fecha de oficio de cierre',
            'Fecha de oficio de cierre'
        )
        seccion_cierre.add_selectbox(
            'Estado',
            'Estado',
            ["", "En proceso", "En proceso oficio de cierre", "Completado", "Finalizado"]
        )
        self.sections.append(seccion_cierre)
        
        # Sección 8: Observaciones
        seccion_obs = FormSection(self.registro_id, "8. Observaciones")
        seccion_obs.add_text_area(
            'Observación',
            'Observación',
            height=100
        )
        self.sections.append(seccion_obs)
    
    def render_form(self):
        """Renderiza todo el formulario"""
        # Información del registro
        st.markdown(f"### Editando Registro #{self.registro_original['Cod']} - {self.registro_original['Entidad']}")
        st.markdown(f"**Nivel de Información:** {self.registro_original['Nivel Información ']}")
        
        # Mostrar indicador de cambios
        if state_manager.has_changes(self.registro_id):
            st.warning("⚠️ **Hay cambios sin guardar.** Presione 'Guardar Registro' para aplicar los cambios.")
        
        st.markdown("---")
        
        # Renderizar todas las secciones
        for section in self.sections:
            section.render_section()
            st.markdown("---")
        
        # Campos calculados automáticamente (solo lectura)
        self._render_calculated_fields()
        
        # Información de avance
        self._render_progress_info()
        
        # Botones de acción
        self._render_action_buttons()
    
    def _render_calculated_fields(self):
        """Renderiza campos calculados automáticamente"""
        st.markdown("### Campos Calculados Automáticamente")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            plazo_analisis = state_manager.get_field_value(self.registro_id, 'Plazo de análisis', '')
            st.text_input(
                "Plazo de análisis",
                value=plazo_analisis,
                disabled=True,
                help="Se calcula automáticamente como 5 días hábiles después de la fecha de entrega de información"
            )
        
        with col2:
            plazo_cronograma = state_manager.get_field_value(self.registro_id, 'Plazo de cronograma', '')
            st.text_input(
                "Plazo de cronograma",
                value=plazo_cronograma,
                disabled=True,
                help="Se calcula automáticamente como 3 días hábiles después del plazo de análisis"
            )
        
        with col3:
            plazo_oficio = state_manager.get_field_value(self.registro_id, 'Plazo de oficio de cierre', '')
            st.text_input(
                "Plazo de oficio de cierre",
                value=plazo_oficio,
                disabled=True,
                help="Se calcula automáticamente como 7 días hábiles después de la fecha de publicación"
            )
    
    def _render_progress_info(self):
        """Renderiza información de avance"""
        st.markdown("### Información de Avance")
        
        # Calcular porcentaje basado en valores temporales
        from data_utils import calcular_porcentaje_avance
        
        estado_temporal = st.session_state.get(self.temp_key, {})
        registro_temporal = pd.Series({**self.registro_original.to_dict(), **estado_temporal})
        porcentaje_temporal = calcular_porcentaje_avance(registro_temporal)
        porcentaje_original = calcular_porcentaje_avance(self.registro_original)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if state_manager.has_changes(self.registro_id) and porcentaje_temporal != porcentaje_original:
                st.metric(
                    "Porcentaje de Avance",
                    f"{porcentaje_temporal}%",
                    delta=f"{porcentaje_temporal - porcentaje_original}%"
                )
            else:
                st.metric("Porcentaje de Avance", f"{porcentaje_temporal}%")
        
        with col2:
            # Estado basado en porcentaje
            if porcentaje_temporal == 100:
                estado_avance = "Completado"
                color_avance = "green"
            elif porcentaje_temporal >= 75:
                estado_avance = "Avanzado"
                color_avance = "blue"
            elif porcentaje_temporal >= 50:
                estado_avance = "En progreso"
                color_avance = "orange"
            elif porcentaje_temporal >= 25:
                estado_avance = "Inicial"
                color_avance = "yellow"
            else:
                estado_avance = "Sin iniciar"
                color_avance = "red"
            
            st.markdown(f"""
            <div style="padding: 10px; border-radius: 5px; background-color: {color_avance}; color: white; text-align: center;">
                <strong>{estado_avance}</strong>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            # Próxima acción sugerida
            if porcentaje_temporal == 0:
                proxima_accion = "Iniciar acuerdo de compromiso"
            elif porcentaje_temporal == 20:
                proxima_accion = "Completar análisis y cronograma"
            elif porcentaje_temporal == 40:
                proxima_accion = "Completar estándares"
            elif porcentaje_temporal == 70:
                proxima_accion = "Realizar publicación"
            elif porcentaje_temporal == 95:
                proxima_accion = "Emitir oficio de cierre"
            else:
                proxima_accion = "Continuar con el proceso"
            
            st.info(f"**Próxima acción:** {proxima_accion}")
    
    def _render_action_buttons(self):
        """Renderiza botones de acción"""
        st.markdown("### Acciones")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            # Botón guardar
            if state_manager.has_changes(self.registro_id):
                if st.button("💾 Guardar Registro", type="primary", key=f"save_{self.registro_id}"):
                    return self._handle_save()
            else:
                st.button("💾 Guardar Registro", disabled=True, help="No hay cambios pendientes")
        
        with col2:
            # Botón cancelar
            if state_manager.has_changes(self.registro_id):
                if st.button("❌ Cancelar Cambios", key=f"cancel_{self.registro_id}"):
                    return self._handle_cancel()
            else:
                st.button("❌ Cancelar Cambios", disabled=True, help="No hay cambios pendientes")
        
        with col3:
            # Botón preview de cambios
            if state_manager.has_changes(self.registro_id):
                if st.button("👁️ Ver Cambios", key=f"preview_{self.registro_id}"):
                    self._show_changes_preview()
        
        with col4:
            # Botón reset
            if st.button("🔄 Reset Formulario", key=f"reset_{self.registro_id}"):
                return self._handle_reset()
        
        return None
    
    def _handle_save(self):
        """Maneja el guardado del formulario"""
        try:
            # 1. Sincronizar widgets al estado temporal
            state_manager.sync_widgets_to_temp_state(self.registro_id)
            
            # 2. Validar datos antes de guardar
            if not self._validate_form():
                return None
            
            # 3. Retornar señal de guardado (será manejado por el componente padre)
            return {
                'action': 'save',
                'registro_id': self.registro_id,
                'temp_key': self.temp_key
            }
            
        except Exception as e:
            st.error(f"Error preparando datos para guardar: {str(e)}")
            return None
    
    def _handle_cancel(self):
        """Maneja la cancelación de cambios"""
        state_manager.clear_temp_state(self.registro_id)
        st.success("Cambios cancelados")
        return {'action': 'cancel', 'registro_id': self.registro_id}
    
    def _handle_reset(self):
        """Maneja el reset del formulario"""
        state_manager.clear_temp_state(self.registro_id)
        return {'action': 'reset', 'registro_id': self.registro_id}
    
    def _validate_form(self) -> bool:
        """Valida el formulario antes de guardar"""
        # Obtener valores actuales
        fecha_oficio = state_manager.get_field_value(self.registro_id, 'Fecha de oficio de cierre', '')
        fecha_publicacion = state_manager.get_field_value(self.registro_id, 'Publicación', '')
        
        # Validación crítica: oficio de cierre requiere publicación
        if fecha_oficio and fecha_oficio.strip():
            if not (fecha_publicacion and fecha_publicacion.strip()):
                st.error("""
                ❌ **No se puede guardar:**
                
                Para introducir 'Fecha de oficio de cierre' debe completar primero la etapa de 'Publicación'
                
                **Pasos:**
                1. Complete la fecha en 'Publicación (fecha real)'
                2. Luego podrá introducir la 'Fecha de oficio de cierre'
                """)
                return False
        
        return True
    
    def _show_changes_preview(self):
        """Muestra preview de cambios pendientes"""
        cambios = state_manager.get_changes_summary(self.registro_id, self.registro_original)
        
        if cambios:
            st.markdown("### 📋 Cambios Pendientes")
            
            # Crear DataFrame de cambios
            df_cambios = pd.DataFrame(cambios)
            st.dataframe(df_cambios, use_container_width=True)
            
            st.info(f"📊 **{len(cambios)} campo(s) modificado(s)**")
        else:
            st.info("✅ No se detectaron cambios en los valores")
    
    def collect_all_values(self) -> dict:
        """Recolecta todos los valores actuales del formulario"""
        # Sincronizar widgets al estado temporal
        state_manager.sync_widgets_to_temp_state(self.registro_id)
        
        # Retornar estado temporal completo
        return st.session_state.get(self.temp_key, {})


class FuncionarioManager:
    """Gestor especializado para el campo de funcionario con funcionalidad dinámica"""
    
    def __init__(self, registro_id: str):
        self.registro_id = registro_id
        self.widget_key = f"funcionario_{registro_id}"
    
    def render(self, registros_df: pd.DataFrame) -> str:
        """Renderiza el selector de funcionario con opción de agregar nuevo"""
        
        # Inicializar lista de funcionarios si no existe
        if 'funcionarios' not in st.session_state:
            st.session_state.funcionarios = []
        
        # Obtener funcionarios únicos del DataFrame
        if st.session_state.funcionarios == []:
            funcionarios_unicos = registros_df['Funcionario'].dropna().unique().tolist()
            st.session_state.funcionarios = [f for f in funcionarios_unicos if f and str(f).strip()]
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            # Campo para nuevo funcionario
            nuevo_funcionario = st.text_input(
                "Nuevo funcionario (opcional)",
                key=f"{self.widget_key}_nuevo",
                placeholder="Escriba nombre del nuevo funcionario"
            )
        
        with col2:
            if nuevo_funcionario and st.button("➕ Agregar", key=f"{self.widget_key}_add"):
                if nuevo_funcionario not in st.session_state.funcionarios:
                    st.session_state.funcionarios.append(nuevo_funcionario)
                    st.success(f"Funcionario '{nuevo_funcionario}' agregado")
                    st.rerun()
        
        # Selector principal
        funcionarios_ordenados = sorted(st.session_state.funcionarios)
        opciones_funcionarios = [""] + funcionarios_ordenados
        
        valor_actual = state_manager.get_field_value(self.registro_id, 'Funcionario', '')
        
        try:
            index = opciones_funcionarios.index(valor_actual) if valor_actual in opciones_funcionarios else 0
        except (ValueError, TypeError):
            index = 0
        
        funcionario_seleccionado = st.selectbox(
            "Funcionario asignado",
            opciones_funcionarios,
            index=index,
            key=f"{self.widget_key}_select"
        )
        
        # Si hay nuevo funcionario, priorizarlo
        if nuevo_funcionario:
            return nuevo_funcionario
        else:
            return funcionario_seleccionado


class ReadOnlyDisplayManager:
    """Gestor para mostrar campos de solo lectura y información calculada"""
    
    def __init__(self, registro_id: str):
        self.registro_id = registro_id
    
    def show_calculated_field(self, campo: str, label: str, help_text: str = None):
        """Muestra un campo calculado automáticamente"""
        valor = state_manager.get_field_value(self.registro_id, campo, '')
        
        st.text_input(
            label,
            value=valor,
            disabled=True,
            key=f"readonly_{self.registro_id}_{campo}",
            help=help_text
        )
    
    def show_registro_info(self, registro: pd.Series):
        """Muestra información básica del registro"""
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.text_input("Código", value=registro['Cod'], disabled=True)
        
        with col2:
            st.text_input("Entidad", value=registro['Entidad'], disabled=True)
        
        with col3:
            st.text_input("Nivel de Información", value=registro['Nivel Información '], disabled=True)


class FormValidationHelper:
    """Asistente para validaciones de formulario"""
    
    @staticmethod
    def validate_fecha_oficio_cierre(registro_id: str) -> tuple[bool, str]:
        """Valida que se pueda introducir fecha de oficio de cierre"""
        fecha_oficio = state_manager.get_field_value(registro_id, 'Fecha de oficio de cierre', '')
        fecha_publicacion = state_manager.get_field_value(registro_id, 'Publicación', '')
        
        if fecha_oficio and fecha_oficio.strip():
            if not (fecha_publicacion and fecha_publicacion.strip()):
                return False, "Para introducir 'Fecha de oficio de cierre' debe completar primero la etapa de 'Publicación'"
        
        return True, ""
    
    @staticmethod
    def validate_all_fields(registro_id: str) -> tuple[bool, list]:
        """Valida todos los campos del formulario"""
        errores = []
        
        # Validar fecha de oficio de cierre
        valido, mensaje = FormValidationHelper.validate_fecha_oficio_cierre(registro_id)
        if not valido:
            errores.append(mensaje)
        
        # Aquí se pueden agregar más validaciones
        
        return len(errores) == 0, errores
    
    @staticmethod
    def show_validation_errors(errores: list):
        """Muestra errores de validación"""
        if errores:
            st.error("❌ **Errores de validación:**")
            for error in errores:
                st.error(f"• {error}")


# Factory para crear widgets fácilmente
class WidgetFactory:
    """Factory para crear widgets de formulario"""
    
    @staticmethod
    def create_selectbox(registro_id: str, campo: str, label: str, options: list, **kwargs):
        return SelectboxWidget(registro_id, campo, label).render(options, **kwargs)
    
    @staticmethod
    def create_text_input(registro_id: str, campo: str, label: str, **kwargs):
        return TextInputWidget(registro_id, campo, label).render(**kwargs)
    
    @staticmethod
    def create_text_area(registro_id: str, campo: str, label: str, **kwargs):
        return TextAreaWidget(registro_id, campo, label).render(**kwargs)
    
    @staticmethod
    def create_date_widget(registro_id: str, campo: str, label: str, **kwargs):
        return DateWidget(registro_id, campo, label).render(**kwargs)
    
    @staticmethod
    def create_funcionario_selector(registro_id: str, registros_df: pd.DataFrame):
        return FuncionarioManager(registro_id).render(registros_df)