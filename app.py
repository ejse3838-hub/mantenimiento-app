import streamlit as st
from supabase import create_client, Client

# Configuración de la conexión (usando los datos de tu foto)
try:
    # Estas líneas ahora coinciden con el formato directo de tus Secrets
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except Exception as e:
    st.error("Error al conectar con la base de datos. Verifica los Secrets en Streamlit.")
    st.stop()

# Función de Login corregida para evitar el error de la imagen
def login(u, p):
    try:
        # Buscamos en la tabla usuarios exactamente como lo tenías antes
        res = supabase.table("usuarios").select("*").eq("email", u).eq("password", p).execute()
        return res
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        return None
