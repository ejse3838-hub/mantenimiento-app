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

# Configuración del autenticador
authenticator = stauth.Authenticate(
    credentials,
    "mantenimiento_cookie",
    "signature_key",
    cookie_expiry_days=30
)

# --- 2. PANTALLA DE LOGIN (LÍNEA CORREGIDA) ---
# Quitamos el "main" que causaba el error
nombre, autenticado, usuario = authenticator.login("Login")

if autenticado:
    authenticator.logout("Cerrar Sesión", "sidebar")
    st.sidebar.success(f"Bienvenido, {nombre}")
    st.title("🛠️ Sistema de Gestión de Mantenimiento")
    
    # Aquí sigue tu menú de navegación...
    menu = ["Órdenes de Trabajo (OT)", "Recursos Humanos", "Activos"]
    choice = st.sidebar.selectbox("Módulos", menu)
    
    if choice == "Recursos Humanos":
        st.header("👤 Gestión de Personal")
        # Tu formulario aquí...

elif autenticado == False:
    st.error("Usuario o contraseña incorrectos.")
elif autenticado == None:
    st.warning("Por favor, ingresa tus credenciales.")