import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime
import plotly.express as px

# --- 1. CONEXIÓN SEGURA ---
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except:
    st.error("Error de conexión. Revisa tus Secrets.")
    st.stop()

def cargar(tabla):
    try:
        res = supabase.table(tabla).select("*").eq("creado_por", st.session_state.user).execute()
        return res.data if res.data else []
    except: return []

# --- 2. CONFIGURACIÓN ---
st.set_page_config(page_title="CORMAIN CMMS PRO", layout="wide")
if 'auth' not in st.session_state: st.session_state.auth = False

# --- 3. LOGIN ---
if not st.session_state.auth:
    st.title("🛠️ COMAIN - Inicio de Sesión")
    u = st.text_input("Usuario")
    p = st.text_input("Clave", type="password")
    if st.button("Entrar"):
        res = supabase.table("usuarios").select("*").eq("email", u).eq("password", p).execute()
        if res.data:
            st.session_state.auth = True
            st.session_state.user = res.data[0]['email']
            st.rerun()
        else: st.error("Acceso incorrecto")
    st.stop()

# --- 4. MENÚ ---
st.sidebar.title(f"👤 {st.session_state.user}")
menu = st.sidebar.radio("Menú", ["🏠 Inicio", "👥 Personal", "⚙️ Maquinaria", "📑 Órdenes de Trabajo"])

# --- 5. PÁGINA: INICIO (GRÁFICOS) ---
if menu == "🏠 Inicio":
    st.title("📊 Panel de Control")
    df_o = pd.DataFrame(cargar("ordenes"))
    if not df_o.empty:
        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(px.pie(df_o, names='estado', title="Estado de Órdenes", hole=0.4), use_container_width=True)
        with col2:
            st.plotly_chart(px.pie(df_o, names='prioridad', title="Prioridad de Tareas", hole=0.4), use_container_width=True)
    else: st.info("Ingresa datos para ver estadísticas.")

# --- 6. PÁGINA: PERSONAL ---
elif menu == "👥 Personal":
    st.header("Gestión de Personal")
    with st.form("f_p", clear_on_submit=True):
        c1, c2 = st.columns(2)
        n, a = c1.text_input("Nombre"), c2.text_input("Apellido")
        cod, mail = c1.text_input("Código"), c2.text_input("Email")
        car = c1.text_input("Cargo")
        if st.form_submit_button("Guardar"):
            # Solo enviamos campos básicos confirmados para evitar el error PGRST204
            try:
                supabase.table("personal").insert({
                    "nombre": n, "apellido": a, "cargo": car, "creado_por": st.session_state.user
                }).execute()
                st.success("Guardado con éxito")
                st.rerun()
            except Exception as e: st.error(f"Error: {e}")
    st.dataframe(pd.DataFrame(cargar("personal")), use_container_width=True)

# --- 7. PÁGINA: MAQUINARIA ---
elif menu == "⚙️ Maquinaria":
    st.header("Ficha Técnica")
    with st.form("f_m", clear_on_submit=True):
        c1, c2 = st.columns(2)
        nm = c1.text_input("Nombre de la Máquina")
        ubi = c2.text_input("Ubicación")
        est = c1.selectbox("Estado", ["Operativa", "Mantenimiento", "Falla"])
        hrs = c2.number_input("Horas de uso", 0)
        if st.form_submit_button("Registrar"):
            try:
                supabase.table("maquinas").insert({
                    "nombre_maquina": nm, "ubicacion": ubi, "estado": est, 
                    "creado_por": st.session_state.user
                }).execute()
                st.success("Máquina registrada")
                st.rerun()
            except Exception as e: st.error(f"Error: {e}")
    st.dataframe(pd.DataFrame(cargar("maquinas")), use_container_width=True)

# --- 8. PÁGINA: ÓRDENES ---
elif menu == "📑 Órdenes de Trabajo":
    st.header("Gestión de OP")
    mqs = [m['nombre_maquina'] for m in cargar("maquinas")]
    if not mqs: st.warning("Registra una máquina primero"); st.stop()
    
    with st.form("f_op"):
        desc = st.text_area("Descripción")
        c1, c2 = st.columns(2)
        mq = c1.selectbox("Máquina", mqs)
        prio = c2.selectbox("Prioridad", ["ALTA", "NORMAL"])
        if st.form_submit_button("Lanzar"):
            try:
                supabase.table("ordenes").insert({
                    "descripcion": desc, "id_maquina": mq, "prioridad": prio,
                    "estado": "Proceso", "creado_por": st.session_state.user
                }).execute()
                st.success("Orden creada")
                st.rerun()
            except Exception as e: st.error(f"Error: {e}")
