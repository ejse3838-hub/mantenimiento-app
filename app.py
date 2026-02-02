import streamlit as st
import streamlit_authenticator as stauth

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Software Mantenimiento Pro", layout="wide")

# --- 1. CONFIGURACIÓN DE USUARIOS ---
credentials = {
    "usernames": {
        "emilio123": {"name": "Emilio Silva", "password": "abc123"},
        "admin": {"name": "Admin Principal", "password": "admin123"}
    }
}

authenticator = stauth.Authenticate(
    credentials, "mantenimiento_cookie", "signature_key", cookie_expiry_days=30
)

# --- 2. PANTALLA DE LOGIN (CORREGIDA) ---
# Usamos location='main' para que sepa que va en el centro de la pantalla
# La nueva versión devuelve los valores directamente
nombre, autenticado, usuario = authenticator.login(label="Iniciar Sesión", location="main")

if st.session_state["authentication_status"]:
    authenticator.logout("Cerrar Sesión", "sidebar")
    st.sidebar.success(f"Bienvenido, {st.session_state['name']}")
    
    st.title("🛠️ Sistema de Gestión de Mantenimiento")
    
    menu = ["Órdenes de Trabajo (OT)", "Recursos Humanos", "Activos"]
    choice = st.sidebar.selectbox("Módulos del Sistema", menu)
    
    if choice == "Recursos Humanos":
        st.header("👤 Gestión de Personal")
        with st.form("form_rrhh"):
            c1, c2 = st.columns(2)
            nombre_p = c1.text_input("Nombre")
            codigo = c1.text_input("Código")
            email = c2.text_input("Email")
            celular = c2.text_input("Celular")
            if st.form_submit_button("Guardar Datos"):
                st.success(f"¡Empleado {nombre_p} registrado!")

elif st.session_state["authentication_status"] is False:
    st.error("Usuario o contraseña incorrectos")
elif st.session_state["authentication_status"] is None:
    st.warning("Por favor, ingresa tus credenciales")