import streamlit as st
from supabase import create_client, Client

# 1. Conexión con Supabase usando tus Secrets
url = st.secrets["connections"]["supabase"]["SUPABASE_URL"]
key = st.secrets["connections"]["supabase"]["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

def cargar_usuarios():
    # Buscamos en la tabla 'usuarios' que creamos en Supabase
    response = supabase.table("usuarios").select("*").execute()
    return response.data

st.title("Sistema de Mantenimiento CORMAIN")

# Lógica de Login
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    email_input = st.text_input("Correo electrónico")
    pass_input = st.text_input("Contraseña", type="password")
    
    if st.button("Entrar"):
        usuarios = cargar_usuarios()
        # Verificamos si los datos coinciden con lo que pusiste en Supabase
        usuario_valido = any(u['email'] == email_input and u['password'] == pass_input for u in usuarios)
        
        if usuario_valido:
            st.session_state.autenticado = True
            st.rerun()
        else:
            st.error("Usuario o contraseña incorrectos")
else:
    st.success(f"Bienvenido al sistema")
    if st.button("Cerrar Sesión"):
        st.session_state.autenticado = False
        st.rerun()

            st.error("Usuario o clave no encontrados.")



