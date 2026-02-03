import streamlit as st
from supabase import create_client, Client

# Conexión con Supabase usando tus Secrets
url = st.secrets["connections"]["supabase"]["SUPABASE_URL"]
key = st.secrets["connections"]["supabase"]["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

st.title("Sistema de Mantenimiento CORMAIN")

# Función para leer los usuarios de la tabla que creamos
def cargar_usuarios():
    try:
        response = supabase.table("usuarios").select("*").execute()
        return response.data
    except Exception:
        return []

# Lógica de Login
if 'auth' not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    email_log = st.text_input("Correo electrónico")
    pass_log = st.text_input("Contraseña", type="password")
    
    if st.button("Entrar"):
        datos = cargar_usuarios()
        # Busca si el correo y clave coinciden con lo que insertaste en Supabase
        if any(u['email'] == email_log and u['password'] == pass_log for u in datos):
            st.session_state.auth = True
            st.rerun()
        else:
            st.error("Credenciales incorrectas. Revisa tu tabla en Supabase.")
else:
    st.success("¡Bienvenido al sistema!")
    if st.button("Cerrar Sesión"):
        st.session_state.auth = False
        st.rerun()
