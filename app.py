import streamlit as st
import streamlit_authenticator as stauth

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Mantenimiento Pro", layout="wide")

# --- 1. CONFIGURACIÓN DE USUARIOS ---
config = {
    "usernames": {
        "emilio123": {"name": "Emilio Silva", "password": "abc123"},
        "admin": {"name": "Admin Principal", "password": "admin123"}
    },
    "cookie": {"expiry_days": 30, "key": "mantenimiento_key", "name": "mantenimiento_cookie"},
    "pre-authorized": {"emails": []}
}

# Nueva forma de crear el objeto
authenticator = stauth.Authenticate(
    config['usernames'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days']
)

# --- 2. PANTALLA DE LOGIN ---
# En las versiones más nuevas, solo llamamos al método y él maneja el st.session_state
authenticator.login(location='main')

if st.session_state["authentication_status"]:
    # --- ZONA SEGURA ---
    authenticator.logout("Cerrar Sesión", "sidebar")
    st.sidebar.success(f"Bienvenido, {st.session_state['name']}")
    
    st.title("🛠️ Sistema de Gestión de Mantenimiento")
    
    menu = ["Órdenes de Trabajo (OT)", "Recursos Humanos", "Activos"]
    choice = st.sidebar.selectbox("Módulos", menu)
    
    if choice == "Recursos Humanos":
        st.header("👤 Gestión de Personal")
        with st.form("form_rrhh"):
            nombre_p = st.text_input("Nombre del técnico")
            if st.form_submit_button("Guardar"):
                st.success(f"Registrado por: {st.session_state['username']}")

elif st.session_state["authentication_status"] is False:
    st.error("Usuario o contraseña incorrectos")
elif st.session_state["authentication_status"] is None:
    st.warning("Por favor, ingresa tus credenciales")