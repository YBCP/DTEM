# auth_utils.py - Sistema de Autenticación

import streamlit as st
import hashlib

def verificar_autenticacion():
    """Verifica si el usuario está autenticado como admin"""
    return st.session_state.get('autenticado', False)

def autenticar_usuario(username, password):
    """Autentica al usuario con credenciales admin"""
    # Credenciales hardcodeadas para admin
    ADMIN_USERNAME = "admin"
    ADMIN_PASSWORD = "qwerty"
    
    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        st.session_state.autenticado = True
        st.session_state.usuario = username
        return True
    return False

def cerrar_sesion():
    """Cierra la sesión del usuario"""
    st.session_state.autenticado = False
    if 'usuario' in st.session_state:
        del st.session_state.usuario

def mostrar_login():
    """Muestra el formulario de login para funciones administrativas"""
    with st.sidebar.expander("🔐 Acceso Administrativo"):
        st.markdown("### Login de Administrador")
        st.info("Se requiere autenticación para cargar datos desde Excel")
        
        username = st.text_input("Usuario", key="login_username")
        password = st.text_input("Contraseña", type="password", key="login_password")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Iniciar Sesión", type="primary"):
                if autenticar_usuario(username, password):
                    st.success("✅ Autenticación exitosa")
                    st.rerun()
                else:
                    st.error("❌ Credenciales incorrectas")
        
        with col2:
            if verificar_autenticacion():
                if st.button("Cerrar Sesión"):
                    cerrar_sesion()
                    st.rerun()

def mostrar_estado_autenticacion():
    """Muestra el estado actual de autenticación"""
    if verificar_autenticacion():
        st.sidebar.success(f"✅ Conectado como: {st.session_state.get('usuario', 'admin')}")
    else:
        st.sidebar.warning("⚠️ No autenticado - Funciones admin limitadas")

def requiere_autenticacion(func):
    """Decorador para funciones que requieren autenticación"""
    def wrapper(*args, **kwargs):
        if verificar_autenticacion():
            return func(*args, **kwargs)
        else:
            st.error("🔒 Se requiere autenticación de administrador para esta función")
            st.info("Usa el panel 'Acceso Administrativo' en la barra lateral")
            return None
    return wrapper