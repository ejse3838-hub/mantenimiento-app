import streamlit as st
from supabase import create_client, Client

# --- DIAGNÓSTICO INICIAL ---
st.title("COMAIN - Estado de Conexión")

try:
    # Intentamos leer los secrets
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    
    # Intentamos crear el cliente
    supabase: Client = create_client(url, key)
    
    # PRUEBA DE FUEGO: Intentar una lectura simple
    test = supabase.table("usuarios").select("count", count="exact").limit(1).execute()
    st.success("✅ Conexión establecida con éxito. La base de datos responde.")
    
except Exception as e:
    st.error(f"❌ Error de Conexión: {e}")
    st.info("Si ves el error 401 aquí, la API Key que copiaste de Supabase está mal generada o expiró.")
    st.stop()

# --- SI PASA EL DIAGNÓSTICO, MOSTRAR LOGIN ---
st.divider()
st.subheader("Inicio de Sesión")
u = st.text_input("Usuario (Email)")
p = st.text_input("Contraseña", type="password")

if st.button("Entrar"):
    try:
        res = supabase.table("usuarios").select("*").eq("email", u).eq("password", p).execute()
        if res.data:
            st.success("¡Bienvenido!")
            st.session_state.logged_in = True
        else:
            st.warning("Usuario no encontrado.")
    except Exception as e:
        st.error(f"Error al validar: {e}")
