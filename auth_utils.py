# auth_utils.py - Sistema de Autenticación Mejorado

import streamlit as st
import hashlib
from datetime import datetime, timedelta

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
        st.session_state.fecha_login = datetime.now()
        return True
    return False

def cerrar_sesion():
    """Cierra la sesión del usuario"""
    st.session_state.autenticado = False
    if 'usuario' in st.session_state:
        del st.session_state.usuario
    if 'fecha_login' in st.session_state:
        del st.session_state.fecha_login

def verificar_sesion_activa():
    """Verifica si la sesión sigue siendo válida (opcional: timeout de sesión)"""
    if not verificar_autenticacion():
        return False
    
    # Opcional: Verificar timeout de sesión (ejemplo: 8 horas)
    if 'fecha_login' in st.session_state:
        fecha_login = st.session_state.fecha_login
        tiempo_transcurrido = datetime.now() - fecha_login
        
        # Si han pasado más de 8 horas, cerrar sesión automáticamente
        if tiempo_transcurrido > timedelta(hours=8):
            cerrar_sesion()
            return False
    
    return True

def mostrar_login():
    """Muestra el formulario de login para funciones administrativas"""
    with st.sidebar.expander("🔐 Acceso Administrativo", expanded=not verificar_autenticacion()):
        
        if verificar_autenticacion():
            # Usuario ya autenticado - mostrar información y opción de logout
            st.success(f"✅ Sesión activa: {st.session_state.get('usuario', 'admin')}")
            
            # Mostrar tiempo de sesión
            if 'fecha_login' in st.session_state:
                tiempo_sesion = datetime.now() - st.session_state.fecha_login
                horas = int(tiempo_sesion.total_seconds() // 3600)
                minutos = int((tiempo_sesion.total_seconds() % 3600) // 60)
                st.info(f"⏱️ Sesión activa: {horas}h {minutos}m")
            
            # Privilegios del usuario
            st.markdown("""
            **🔓 Privilegios habilitados:**
            - ✏️ Edición de registros
            - 💾 Guardado en Google Sheets
            - 🔄 Actualización de plazos
            - ⚙️ Aplicación de validaciones
            """)
            
            # Botón de logout
            if st.button("🚪 Cerrar Sesión", type="secondary", use_container_width=True):
                cerrar_sesion()
                st.success("✅ Sesión cerrada exitosamente")
                st.rerun()
                
        else:
            # Usuario no autenticado - mostrar formulario de login
            st.markdown("### 🔐 Iniciar Sesión")
            st.info("🔒 Se requiere autenticación para editar registros")
            
            with st.form("login_form"):
                username = st.text_input("👤 Usuario", placeholder="Ingrese usuario")
                password = st.text_input("🔑 Contraseña", type="password", placeholder="Ingrese contraseña")
                submit_button = st.form_submit_button("🔓 Iniciar Sesión", type="primary", use_container_width=True)
                
                if submit_button:
                    if not username or not password:
                        st.error("❌ Por favor complete todos los campos")
                    elif autenticar_usuario(username, password):
                        st.success("✅ Autenticación exitosa")
                        st.balloons()
                        st.rerun()
                    else:
                        st.error("❌ Credenciales incorrectas")
                        st.warning("💡 Verifique usuario y contraseña")
            
            # Información sobre credenciales (solo para desarrollo)
            with st.expander("ℹ️ Información de Acceso"):
                st.markdown("""
                **Credenciales de prueba:**
                - Usuario: `admin`
                - Contraseña: `qwerty`
                
                **⚠️ Nota de seguridad:**
                En producción, estas credenciales deben ser cambiadas
                y almacenadas de forma segura.
                """)

def mostrar_estado_autenticacion():
    """Muestra el estado actual de autenticación en la sidebar"""
    if verificar_sesion_activa():
        st.sidebar.success(f"🔓 Conectado: {st.session_state.get('usuario', 'admin')}")
        
        # Mostrar funcionalidades disponibles
        st.sidebar.markdown("""
        **✅ Funcionalidades activas:**
        - Edición de registros
        - Guardado automático
        - Validaciones avanzadas
        """)
        
    else:
        st.sidebar.warning("🔒 No autenticado")
        st.sidebar.markdown("""
        **⚠️ Funcionalidades limitadas:**
        - Solo visualización
        - Sin edición de datos
        - Sin guardado
        """)

def requiere_autenticacion(func):
    """Decorador para funciones que requieren autenticación"""
    def wrapper(*args, **kwargs):
        if verificar_sesion_activa():
            return func(*args, **kwargs)
        else:
            st.error("🔒 Se requiere autenticación de administrador para esta función")
            st.info("💡 Use el panel 'Acceso Administrativo' en la barra lateral")
            return None
    return wrapper

def verificar_permisos_edicion():
    """Función específica para verificar permisos de edición de registros"""
    if not verificar_sesion_activa():
        return False, "Usuario no autenticado"
    
    # Aquí se pueden agregar más verificaciones de permisos específicos
    # Por ejemplo, verificar roles, permisos específicos, etc.
    
    return True, "Permisos de edición confirmados"

def mostrar_panel_seguridad():
    """Panel adicional de información de seguridad"""
    with st.sidebar.expander("🛡️ Información de Seguridad"):
        if verificar_autenticacion():
            st.success("🔐 Sistema protegido - Sesión activa")
            
            # Mostrar información de la sesión
            if 'fecha_login' in st.session_state:
                fecha_login = st.session_state.fecha_login
                st.info(f"🕐 Login: {fecha_login.strftime('%H:%M:%S')}")
            
            # Advertencia sobre seguridad
            st.warning("""
            **⚠️ Recordatorios de seguridad:**
            - Cierre sesión al terminar
            - No comparta credenciales
            - Reporte accesos no autorizados
            """)
            
        else:
            st.info("""
            **🔒 Datos protegidos**
            
            El sistema protege automáticamente:
            - ✏️ Edición de registros
            - 💾 Modificación de datos
            - 🔄 Operaciones críticas
            
            **Acceso libre:**
            - 📊 Visualización de dashboards
            - 📈 Reportes y estadísticas
            - 📋 Consulta de información
            """)

def log_actividad_usuario(accion, detalles=""):
    """Registra actividades del usuario para auditoría"""
    if verificar_autenticacion():
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        usuario = st.session_state.get('usuario', 'desconocido')
        
        # Guardar en session_state para mostrar actividades recientes
        if 'log_actividades' not in st.session_state:
            st.session_state.log_actividades = []
        
        entrada_log = {
            'timestamp': timestamp,
            'usuario': usuario,
            'accion': accion,
            'detalles': detalles
        }
        
        st.session_state.log_actividades.append(entrada_log)
        
        # Mantener solo las últimas 20 actividades
        if len(st.session_state.log_actividades) > 20:
            st.session_state.log_actividades = st.session_state.log_actividades[-20:]

def mostrar_log_actividades():
    """Muestra el log de actividades recientes del usuario"""
    if verificar_autenticacion() and 'log_actividades' in st.session_state:
        with st.expander("📋 Actividades Recientes"):
            actividades = st.session_state.log_actividades[-10:]  # Últimas 10
            
            if actividades:
                for actividad in reversed(actividades):  # Más recientes primero
                    st.text(f"{actividad['timestamp']} - {actividad['accion']}")
                    if actividad['detalles']:
                        st.caption(f"   └─ {actividad['detalles']}")
            else:
                st.info("No hay actividades registradas en esta sesión")

# Función para cambiar credenciales (solo para administradores)
def cambiar_credenciales():
    """Permite cambiar las credenciales de administrador"""
    if verificar_autenticacion():
        with st.expander("🔧 Cambiar Credenciales"):
            st.warning("⚠️ Funcionalidad en desarrollo - Contacte al administrador del sistema")
            st.info("""
            **Para cambiar credenciales en producción:**
            1. Modificar variables de entorno
            2. Usar base de datos segura
            3. Implementar hash de contraseñas
            4. Activar autenticación de dos factores
            """)

# Verificación adicional de seguridad para operaciones críticas
def verificar_operacion_critica(operacion):
    """Verificación adicional para operaciones que modifican datos importantes"""
    if not verificar_sesion_activa():
        return False, "Autenticación requerida"
    
    # Log de la operación crítica
    log_actividad_usuario(f"Operación crítica: {operacion}")
    
    return True, f"Operación {operacion} autorizada"
