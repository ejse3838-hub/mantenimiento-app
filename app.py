import streamlit as st
from supabase import create_client, Client

# 1. Conexión con Supabase usando tus Secrets
# El código buscará estos datos en la pestaña de Secrets de Streamlit
url = st.secrets["connections"]["supabase"]["SUPABASE_URL"]
key = st.secrets["connections"]["supabase"]["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

def cargar_usuarios():
    # Buscamos en la tabla 'usuarios' que creaste en Supabase
    try:
        response = supabase.table("usuarios").select("*").execute()
        return response.data
    except Exception as e:
        return []

st.title("Sistema de Mantenimiento CORMAIN")

# Lógica de Login
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    st.subheader("Iniciar Sesión")
    email_input = st.text_input("Correo electrónico")
    pass_input = st.text_input("Contraseña", type="password")
    
    if st.button("Entrar"):
        usuarios = cargar_usuarios()
        # Verificamos si los datos coinciden con lo que pusiste en la tabla
        usuario_valido = any(u['email'] == email_input and u['password'] == pass_input for u in usuarios)
        
        if usuario_valido:
            st.session_state.autenticado = True
            st.session_state.email = email_input
            st.rerun()
        else:
            st.error("Correo o contraseña incorrectos. Revisa tu tabla en Supabase.")
else:
    st.success(f"Bienvenido al sistema, {st.session_state.email}")
    if st.button("Cerrar Sesión"):
        st.session_state.autenticado = False
        st.rerun()