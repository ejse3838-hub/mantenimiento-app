import streamlit as st
from supabase import create_client, Client

# 1. Configuración de conexión segura
try:
    if "SUPABASE_URL" in st.secrets and "SUPABASE_KEY" in st.secrets:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        supabase: Client = create_client(url, key)
    else:
        st.error("Faltan las credenciales en los Secrets de Streamlit.")
        st.stop()
except Exception as e:
    st.error(f"Error fatal al conectar: {e}")
    st.stop()

# 2. Función de login simplificada
def login(u, p):
    try:
        # Esto busca en tu tabla 'usuarios' como lo tenías antes
        res = supabase.table("usuarios").select("*").eq("email", u).eq("password", p).execute()
        return res
    except Exception as e:
        st.error(f"Error en la base de datos: {e}")
        return None

