import streamlit as st
import pandas as pd
from supabase import create_client, Client

# --- CONEXIÓN ---
url = st.secrets["connections"]["supabase"]["SUPABASE_URL"]
key = st.secrets["connections"]["supabase"]["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

# --- FUNCIÓN DE CARGA ---
def cargar(tabla):
    try:
        res = supabase.table(tabla).select("*").eq("creado_por", st.session_state.user).execute()
        return res.data if res.data else []
    except:
        return []

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="CORMAIN CMMS PRO", layout="wide")

if 'auth' not in st.session_state: st.session_state.auth = False

# --- LOGIN ---
if not st.session_state.auth:
    tab1, tab2 = st.tabs(["🔑 Iniciar Sesión", "📝 Registro"])
    with tab1:
        u = st.text_input("Usuario (Email)")
        p = st.text_input("Clave", type="password")
        if st.button("Entrar"):
            res = supabase.table("usuarios").select("*").eq("email", u).eq("password", p).execute()
            if res.data: 
                st.session_state.auth = True
                st.session_state.user = res.data[0]['email']
                st.rerun()
            else: st.error("Usuario o clave incorrectos")
    with tab2:
        nu = st.text_input("Nuevo Email")
        np = st.text_input("Nueva Clave", type="password")
        if st.button("Crear Cuenta"):
            try:
                supabase.table("usuarios").insert({"email": nu, "password": np, "creado_por": nu}).execute()
                st.success("¡Cuenta creada con éxito!")
            except: st.error("Error al crear cuenta")

else:
    # --- MENÚ LATERAL ---
    st.sidebar.title(f"👤 {st.session_state.user}")
    if "menu" not in st.session_state: st.session_state.menu = "🏠 Inicio"

    if st.sidebar.button("🏠 Inicio", use_container_width=True): st.session_state.menu = "🏠 Inicio"
    if st.sidebar.button("👥 Personal", use_container_width=True): st.session_state.menu = "👥 Personal"
    if st.sidebar.button("⚙️ Maquinaria", use_container_width=True): st.session_state.menu = "⚙️ Maquinaria"
    if st.sidebar.button("📑 Órdenes de Trabajo", use_container_width=True): st.session_state.menu = "📑 Órdenes de Trabajo"
    
    st.sidebar.divider()
    if st.sidebar.button("🚪 Cerrar Sesión", use_container_width=True):
        st.session_state.auth = False
        st.rerun()

    # --- 1. INICIO ---
    if st.session_state.menu == "🏠 Inicio":
        st.title("📊 Panel de Control CORMAIN")
        o_data = cargar("ordenes")
        if o_data:
            df = pd.DataFrame(o_data)
            col1, col2, col3 = st.columns(3)
            col1.metric("Órdenes Totales", len(df))
            col2.metric("En Proceso", len(df[df['estado'] == 'Proceso']))
            col3.metric("Finalizadas", len(df[df['estado'] == 'Finalizada']))
            st.dataframe(df, use_container_width=True)
        else: st.info("No hay órdenes registradas.")

    # --- 2. PERSONAL (AUMENTADO) ---
    elif st.session_state.menu == "👥 Personal":
        st.header("Gestión de Personal")
        with st.form("f_personal"):
            c1, c2 = st.columns(2)
            nom = c1.text_input("Nombres")
            ape = c2.text_input("Apellidos")
            car = c1.text_input("Cargo")
            pue = c2.text_input("Puesto de Trabajo")
            if st.form_submit_button("Guardar Técnico"):
                supabase.table("personal").insert({
                    "nombre": f"{nom} {ape}", 
                    "cargo": car, 
                    "especialidad": pue, # Usamos especialidad como puesto
                    "creado_por": st.session_state.user
                }).execute()
                st.rerun()
        p_res = cargar("personal")
        if p_res: st.table(pd.DataFrame(p_res)[["nombre", "cargo", "especialidad"]])

    # --- 3. MAQUINARIA (CON CÓDIGO) ---
    elif st.session_state.menu == "⚙️ Maquinaria":
        st.header("Gestión de Maquinaria")
        with st.form("f_maquina"):
            col1, col2 = st.columns(2)
            n_m = col1.text_input("Nombre de la Máquina")
            cod = col2.text_input("Código de Máquina (ID)")
            if st.form_submit_button("Registrar Equipo"):
                supabase.table("maquinas").insert({
                    "nombre_maquina": n_m, 
                    "codigo": cod, 
                    "creado_por": st.session_state.user
                }).execute()
                st.rerun()
        m_res = cargar("maquinas")
        if m_res: st.table(pd.DataFrame(m_res)[["nombre_maquina", "codigo"]])

    # --- 4. ORDENES (CON PERIODICIDAD) ---
    elif st.session_state.menu == "📑 Órdenes de Trabajo":
        st.header("Órdenes de Producción")
        
        m_list = cargar("maquinas")
        p_list = cargar("personal")
        
        # Listas para selectbox
        nombres_m = [f"{m['nombre
