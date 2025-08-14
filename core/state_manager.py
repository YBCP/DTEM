# core/state_manager.py
"""
Sistema de gestión de estados temporales sin recargas automáticas
Reemplaza el sistema actual que causa rerun() en cada cambio
"""

import streamlit as st
import pandas as pd
from typing import Dict, Any, Optional, List
from datetime import datetime


class StateManager:
    """Gestor de estados temporales para formularios sin recargas automáticas"""
    
    def __init__(self):
        self.prefix = "temp_registro_"
        self.modified_suffix = "_modified"
        self.widget_suffix = "_widget"
    
    def get_temp_key(self, registro_id: str) -> str:
        """Genera la clave temporal para un registro"""
        return f"{self.prefix}{registro_id}"
    
    def get_modified_key(self, registro_id: str) -> str:
        """Genera la clave de modificación para un registro"""
        return f"{self.prefix}{registro_id}{self.modified_suffix}"
    
    def get_widget_key(self, registro_id: str, campo: str) -> str:
        """Genera la clave del widget para un campo específico"""
        return f"{self.prefix}{registro_id}_{campo}{self.widget_suffix}"
    
    def initialize_temp_state(self, registro_id: str, registro_original: pd.Series) -> str:
        """
        Inicializa el estado temporal para un registro.
        Retorna la clave temporal.
        """
        temp_key = self.get_temp_key(registro_id)
        
        # Solo inicializar si no existe
        if temp_key not in st.session_state:
            st.session_state[temp_key] = registro_original.to_dict()
            st.session_state[self.get_modified_key(registro_id)] = False
        
        return temp_key
    
    def get_field_value(self, registro_id: str, campo: str, default: Any = "") -> Any:
        """
        Obtiene el valor actual de un campo desde el estado temporal.
        """
        temp_key = self.get_temp_key(registro_id)
        
        if temp_key in st.session_state and campo in st.session_state[temp_key]:
            valor = st.session_state[temp_key][campo]
            # Manejar valores None o NaN
            if valor is None or (isinstance(valor, float) and pd.isna(valor)):
                return default
            return str(valor).strip() if valor != "" else default
        
        return default
    
    def update_field_silent(self, registro_id: str, campo: str, nuevo_valor: Any) -> None:
        """
        Actualiza un campo en el estado temporal SIN causar rerun.
        Esta es la clave para evitar recargas automáticas.
        """
        temp_key = self.get_temp_key(registro_id)
        
        if temp_key in st.session_state:
            # Solo marcar como modificado si realmente cambió
            valor_actual = st.session_state[temp_key].get(campo, "")
            if str(valor_actual) != str(nuevo_valor):
                st.session_state[temp_key][campo] = nuevo_valor
                st.session_state[self.get_modified_key(registro_id)] = True
    
    def has_changes(self, registro_id: str) -> bool:
        """Verifica si hay cambios pendientes en el registro"""
        modified_key = self.get_modified_key(registro_id)
        return st.session_state.get(modified_key, False)
    
    def get_changes_summary(self, registro_id: str, registro_original: pd.Series) -> List[Dict[str, Any]]:
        """
        Obtiene un resumen de los cambios realizados.
        Retorna lista de diccionarios con los cambios detectados.
        """
        temp_key = self.get_temp_key(registro_id)
        
        if temp_key not in st.session_state:
            return []
        
        cambios = []
        estado_temporal = st.session_state[temp_key]
        
        for campo, valor_temp in estado_temporal.items():
            valor_original = registro_original.get(campo, "")
            
            # Normalizar valores para comparación
            valor_temp_str = str(valor_temp).strip() if valor_temp not in [None, "", pd.NaT] else ""
            valor_original_str = str(valor_original).strip() if valor_original not in [None, "", pd.NaT] else ""
            
            if valor_temp_str != valor_original_str:
                cambios.append({
                    'Campo': campo,
                    'Valor Original': valor_original_str,
                    'Nuevo Valor': valor_temp_str
                })
        
        return cambios
    
    def apply_changes_to_dataframe(self, registro_id: str, df: pd.DataFrame, indice: int) -> pd.DataFrame:
        """
        Aplica los cambios temporales al DataFrame principal.
        """
        temp_key = self.get_temp_key(registro_id)
        
        if temp_key in st.session_state:
            df_actualizado = df.copy()
            estado_temporal = st.session_state[temp_key]
            
            for campo, valor in estado_temporal.items():
                if campo in df_actualizado.columns:
                    df_actualizado.at[df_actualizado.index[indice], campo] = valor
            
            return df_actualizado
        
        return df
    
    def clear_temp_state(self, registro_id: str) -> None:
        """Limpia el estado temporal de un registro"""
        temp_key = self.get_temp_key(registro_id)
        modified_key = self.get_modified_key(registro_id)
        
        # Limpiar estado principal
        if temp_key in st.session_state:
            del st.session_state[temp_key]
        if modified_key in st.session_state:
            del st.session_state[modified_key]
        
        # Limpiar widgets relacionados
        keys_to_remove = []
        for key in st.session_state.keys():
            if key.startswith(f"{self.prefix}{registro_id}_") and key != temp_key:
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            try:
                del st.session_state[key]
            except KeyError:
                pass
    
    def collect_widget_values(self, registro_id: str) -> Dict[str, Any]:
        """
        Recolecta todos los valores de widgets para un registro.
        Se usa al momento de guardar para obtener los valores actuales.
        """
        valores = {}
        widget_prefix = f"{self.prefix}{registro_id}_"
        
        for key, value in st.session_state.items():
            if key.startswith(widget_prefix) and key.endswith(self.widget_suffix):
                # Extraer nombre del campo
                campo = key.replace(widget_prefix, "").replace(self.widget_suffix, "")
                valores[campo] = value
        
        return valores
    
    def sync_widgets_to_temp_state(self, registro_id: str) -> None:
        """
        Sincroniza los valores de los widgets al estado temporal.
        Se llama antes de guardar para asegurar que todos los cambios estén capturados.
        """
        valores_widgets = self.collect_widget_values(registro_id)
        
        for campo, valor in valores_widgets.items():
            self.update_field_silent(registro_id, campo, valor)
    
    def get_all_temp_states(self) -> Dict[str, Dict[str, Any]]:
        """Obtiene todos los estados temporales (para debugging)"""
        estados = {}
        
        for key, value in st.session_state.items():
            if key.startswith(self.prefix) and not key.endswith(self.modified_suffix):
                registro_id = key.replace(self.prefix, "")
                estados[registro_id] = value
        
        return estados
    
    def has_any_changes(self) -> bool:
        """Verifica si hay cambios pendientes en cualquier registro"""
        for key in st.session_state.keys():
            if key.endswith(self.modified_suffix) and st.session_state.get(key, False):
                return True
        return False
    
    def reset_all_temp_states(self) -> None:
        """Limpia todos los estados temporales (para emergencias)"""
        keys_to_remove = []
        
        for key in st.session_state.keys():
            if key.startswith(self.prefix):
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            try:
                del st.session_state[key]
            except KeyError:
                pass


class DateStateManager:
    """Gestor especializado para campos de fecha con checkbox"""
    
    def __init__(self, state_manager: StateManager):
        self.state_manager = state_manager
    
    def get_date_state(self, registro_id: str, campo: str) -> tuple[bool, Any]:
        """
        Retorna el estado de una fecha: (tiene_fecha, valor_fecha)
        """
        valor = self.state_manager.get_field_value(registro_id, campo, "")
        tiene_fecha = bool(valor and valor.strip())
        
        return tiene_fecha, valor if tiene_fecha else None
    
    def update_date_state(self, registro_id: str, campo: str, tiene_fecha: bool, valor_fecha: Any = None) -> None:
        """
        Actualiza el estado de una fecha
        """
        if tiene_fecha and valor_fecha is not None:
            self.state_manager.update_field_silent(registro_id, campo, valor_fecha)
        else:
            self.state_manager.update_field_silent(registro_id, campo, "")
    
    def clear_date(self, registro_id: str, campo: str) -> None:
        """Limpia una fecha específica"""
        self.state_manager.update_field_silent(registro_id, campo, "")


# Instancia global del gestor de estados
state_manager = StateManager()
date_state_manager = DateStateManager(state_manager)
