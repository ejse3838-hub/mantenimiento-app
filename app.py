import streamlit as st
import streamlit_authenticator as stauth

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Mantenimiento Pro", layout="wide")

# --- 1. CONFIGURACIÓN DE USUARIOS (FORMATO EXACTO) ---
# La librería ahora necesita que todo esté envuelto en una llave 'credentials'
config = {
    "credentials": {
        "usernames": {
            "emilio123": {"name": "Emilio Silva", "password": "abc123"},
            "admin": {"name": "Admin Principal", "password": "admin123"}
        }
    },
    "cookie": {"expiry_days": 30, "key": "mantenimiento_key", "name": "mantenimiento_cookie"}
}

# Inicializar el autenticador con la estructura corregida
authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days']
)

# --- 2. PANTALLA DE LOGIN ---
# El método login ahora se encarga de todo el flujo
authenticator.login(location='main')

# Verificamos el estado de autenticación usando st.session_state
if st.session_state["authentication_status"]:
    authenticator.logout("Cerrar Sesión", "sidebar")
    st.sidebar.success(f"Bienvenido, {st.session_state['name']}")
    
    st.title("🛠️ Sistema de Gestión de Mantenimiento")
    
    # --- MENÚ DE NAVEGACIÓN ---
    menu = ["Órdenes de Trabajo (OT)", "Recursos Humanos", "Activos"]
    choice = st.sidebar.selectbox("Módulos", menu)
    
    if choice == "Recursos Humanos":
        st.header("👤 Gestión de Personal")
        with st.form("form_rrhh"):
            nombre_t = st.text_input("Nombre del Técnico")
            if st.form_submit_button("Guardar"):
                st.success(f"Registrado en la sesión de: {st.session_state['username']}")

elif st.session_state["authentication_status"] is False:
    st.error("Usuario o contraseña incorrectos")
elif st.session_state["authentication_status"] is None:
    st.warning("Por favor, ingresa tus credenciales para acceder")