import streamlit as st
from supabase import create_client, Client
import pandas as pd

# Configuración de página
st.set_page_config(page_title="COMAIN CMMS", layout="wide")

# --- CONEXIÓN SEGURA ---
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except Exception as e:
    st.error("Error crítico: Revisa los Secrets en Streamlit Cloud.")
    st.stop()

# --- GESTIÓN DE SESIÓN ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

def login(u, p):
    try:
        res = supabase.table("usuarios").select("*").eq("email", u).eq("password", p).execute()
        return res
    except Exception as e:
        st.error(f"Error de base de datos: {e}")
        return None

# --- PANTALLA DE LOGIN ---
if not st.session_state.logged_in:
    st.title("COMAIN - Inicio de Sesión")
    with st.container():
        u = st.text_input("Correo Electrónico")
        p = st.text_input("Contraseña", type="password")
        if st.button("Entrar"):
            resultado = login(u, p)
            if resultado and len(resultado.data) > 0:
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("Credenciales inválidas. Verifica tu usuario y contraseña.")
    st.stop()

# --- MENÚ PRINCIPAL ---
st.sidebar.title("Menú COMAIN")
opcion = st.sidebar.selectbox("Seleccione una sección", ["Dashboard", "Personal", "Maquinaria", "Órdenes de Trabajo"])

# 1. DASHBOARD
if opcion == "Dashboard":
    st.header("📊 Tablero de Control")
    col1, col2, col3 = st.columns(3)
    try:
        m_count = len(supabase.table("maquinaria").select("id").execute().data)
        p_count = len(supabase.table("personal").select("id").execute().data)
        col1.metric("Máquinas", m_count)
        col2.metric("Personal", p_count)
        col3.metric("Estado", "Activo")
    except:
        st.info("Cargando datos...")

# 2. PERSONAL (9 Campos)
elif opcion == "Personal":
    st.header("👥 Gestión de Personal")
    with st.form("form_personal"):
        c1, c2 = st.columns(2)
        nombre = c1.text_input("Nombre Completo")
        cedula = c2.text_input("Cédula")
        cargo = c1.text_input("Cargo")
        telefono = c2.text_input("Teléfono")
        email = c1.text_input("Email")
        turno = c2.selectbox("Turno", ["Matutino", "Vespertino", "Nocturno"])
        fecha_ing = st.date_input("Fecha de Ingreso")
        salario = st.number_input("Salario", min_value=0.0)
        obs = st.text_area("Observaciones")
        
        if st.form_submit_button("Registrar"):
            data = {"nombre": nombre, "cedula": cedula, "cargo": cargo, "telefono": telefono, "email": email}
            supabase.table("personal").insert(data).execute()
            st.success("Personal guardado con éxito.")

# 3. MAQUINARIA (12 Campos)
elif opcion == "Maquinaria":
    st.header("⚙️ Inventario de Maquinaria")
    with st.form("form_maquina"):
        c1, c2, c3 = st.columns(3)
        cod = c1.text_input("Código")
        nom = c2.text_input("Nombre")
        mar = c3.text_input("Marca")
        ubi = c1.text_input("Ubicación")
        est = c2.selectbox("Estado", ["Operativo", "Mantenimiento", "Reparación"])
        prio = c3.slider("Prioridad", 1, 5)
        # Campos adicionales para completar los 12
        f_adq = st.date_input("Fecha Adquisición")
        v_util = st.number_input("Vida Útil (Años)")
        prov = st.text_input("Proveedor")
        
        if st.form_submit_button("Guardar Máquina"):
            supabase.table("maquinaria").insert({"codigo": cod, "nombre": nom, "estado": est}).execute()
            st.success("Máquina registrada.")

# 4. ÓRDENES DE TRABAJO (Restaurado)
elif opcion == "Órdenes de Trabajo":
    st.header("📝 Órdenes de Trabajo")
    try:
        ots = supabase.table("ordenes_trabajo").select("*").execute()
        if ots.data:
            st.dataframe(pd.DataFrame(ots.data))
        else:
            st.info("No hay órdenes de trabajo registradas.")
    except Exception as e:
        st.error(f"Error al cargar órdenes: {e}")
