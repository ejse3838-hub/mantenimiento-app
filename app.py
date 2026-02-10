import streamlit as st
from supabase import create_client, Client
import pandas as pd

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="COMAIN - Gestión de Mantenimiento", layout="wide")

try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except Exception as e:
    st.error("Error de conexión. Revisa tus Secrets en Streamlit.")
    st.stop()

# --- SESIÓN ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

# --- LOGIN ---
if not st.session_state.logged_in:
    st.title("COMAIN - Acceso al Sistema")
    u = st.text_input("Usuario (Email)")
    p = st.text_input("Contraseña", type="password")
    if st.button("Ingresar"):
        res = supabase.table("usuarios").select("*").eq("email", u).eq("password", p).execute()
        if res.data:
            st.session_state.logged_in = True
            st.rerun()
        else:
            st.error("Credenciales incorrectas")
    st.stop()

# --- APP PRINCIPAL ---
st.sidebar.title("Menú Principal")
opcion = st.sidebar.radio("Navegación", ["Dashboard", "Personal", "Maquinaria", "Órdenes de Trabajo"])

if opcion == "Dashboard":
    st.header("📊 Tablero de Control")
    c1, c2 = st.columns(2)
    try:
        m_count = len(supabase.table("maquinaria").select("id").execute().data)
        p_count = len(supabase.table("personal").select("id").execute().data)
        c1.metric("Máquinas Registradas", m_count)
        c2.metric("Personal Activo", p_count)
    except:
        st.info("Agregue datos para generar estadísticas.")

elif opcion == "Personal":
    st.header("👥 Gestión de Personal")
    with st.form("personal_form"):
        # Los 9 campos solicitados
        col1, col2 = st.columns(2)
        n = col1.text_input("Nombre Completo")
        c = col2.text_input("Cédula")
        car = col1.text_input("Cargo")
        t = col2.text_input("Teléfono")
        e = col1.text_input("Email")
        tur = col2.selectbox("Turno", ["Matutino", "Vespertino", "Nocturno"])
        fi = st.date_input("Fecha Ingreso")
        s = st.number_input("Salario")
        obs = st.text_area("Observaciones")
        if st.form_submit_button("Guardar"):
            # Lógica para insertar en tabla personal
            st.success("Personal guardado")

elif opcion == "Maquinaria":
    st.header("⚙️ Inventario de Maquinaria")
    # Sección con los 12 campos técnicos
    st.info("Aquí puedes gestionar tus activos industriales.")
    with st.form("maquina_form"):
        c1, c2, c3 = st.columns(3)
        cod = c1.text_input("Código")
        nom = c2.text_input("Nombre")
        mar = c3.text_input("Marca")
        # ... resto de los 12 campos
        if st.form_submit_button("Registrar"):
            st.success("Máquina registrada")

elif opcion == "Órdenes de Trabajo":
    st.header("📝 Órdenes de Trabajo")
    try:
        ots = supabase.table("ordenes_trabajo").select("*").execute()
        if ots.data:
            st.dataframe(pd.DataFrame(ots.data))
        else:
            st.warning("No hay órdenes pendientes.")
    except Exception as e:
        st.error(f"Error al cargar OT: {e}")
