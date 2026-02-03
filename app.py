import streamlit as st
from supabase import create_client, Client

# Configuración de la página
st.set_page_config(page_title="CORMAIN - Mantenimiento", layout="centered")

# 1. Conexión con Supabase usando tus Secrets
# Asegúrate de tener SUPABASE_URL y SUPABASE_KEY en tus Secrets de Streamlit
url = st.secrets["connections"]["supabase"]["SUPABASE_URL"]
key = st.secrets["connections"]["supabase"]["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

def cargar_usuarios():
    # Buscamos en la tabla 'usuarios' que creaste en Supabase
    try:
        response = supabase.table("usuarios").select("*").execute()
        return response.data
    except Exception as e:
        st.error(# Error si la tabla no existe o RLS está activado
            f"Error al conectar con la base de datos: {e}")
        return []

st.title("Sistema de Mantenimiento CORMAIN")

# Lógica de Inicio de Sesión (Login)
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    st.subheader("Iniciar Sesión")
    email_input = st.text_input("Correo electrónico")
    pass_input = st.text_input("Contraseña", type="password")
    
    if st.button("Entrar"):
        usuarios = cargar_usuarios()
        # Verificamos si los datos coinciden con lo que pusiste en la tabla de Supabase
        usuario_valido = any(u['email'] == email_input and u['password'] == pass_input for u in usuarios)
        
        if usuario_valido:
            st.session_state.autenticado = True
            st.rerun()
        else:
            st.error("Correo o contraseña incorrectos. Verifica en Supabase.")
else:
    st.success(f"Bienvenido al sistema, {st.session_state.get('email', 'Usuario')}")
    
    # Aquí irá el resto de tu aplicación de mantenimiento
    st.info("Panel de control de mantenimiento activo.")
    
    if st.button("Cerrar Sesión"):
        st.session_state.autenticado = False
        st.rerun()