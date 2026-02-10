import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime

# --- 1. CONEXIÓN ---
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except Exception:
    st.error("Error de conexión. Revisa tus Secrets.")
    st.stop()

# --- 2. FUNCIÓN DE CARGA SEGURA ---
def cargar(tabla):
    try:
        res = supabase.table(tabla).select("*").eq("creado_por", st.session_state.user).execute()
        return res.data if res.data else []
    except Exception:
        return []

# --- 3. CONFIGURACIÓN ---
st.set_page_config(page_title="CORMAIN CMMS PRO", layout="wide")
if 'auth' not in st.session_state: st.session_state.auth = False

# --- 4. LOGIN (Simplificado) ---
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
        else: st.error("Acceso denegado")
    st.stop()

# --- 5. NAVEGACIÓN ---
st.sidebar.title(f"👤 {st.session_state.user}")
menu = st.sidebar.radio("Menú", ["🏠 Inicio", "👥 Personal", "⚙️ Maquinaria", "📑 Órdenes de Trabajo"])

# --- 6. SECCIÓN ÓRDENES DE TRABAJO (CORREGIDA) ---
if menu == "📑 Órdenes de Trabajo":
    st.header("Gestión de Órdenes de Trabajo")
    
    # Intentamos obtener datos para los selectores
    maquinas_raw = cargar("maquinas")
    personal_raw = cargar("personal")
    
    # Verificación para evitar la pantalla en negro
    if not maquinas_raw:
        st.warning("⚠️ No puedes crear órdenes porque no hay MÁQUINAS registradas.")
    if not personal_raw:
        st.warning("⚠️ No puedes crear órdenes porque no hay PERSONAL registrado.")
        
    if maquinas_raw and personal_raw:
        m_list = [f"{m['nombre_maquina']} ({m.get('codigo', 'S/C')})" for m in maquinas_raw]
        p_list = [f"{p['nombre']} {p.get('apellido', '')}" for p in personal_raw]
        
        with st.expander("➕ Lanzar Nueva Orden (OP)"):
            with st.form("f_op"):
                desc = st.text_area("Descripción de la tarea")
                c1, c2 = st.columns(2)
                mq = c1.selectbox("Seleccionar Máquina", m_list)
                tc = c2.selectbox("Asignar Técnico", p_list)
                tt = c1.selectbox("Tipo de Tarea", ["Correctiva", "Preventiva"])
                pr = c2.selectbox("Prioridad", ["ALTA", "NORMAL"])
                
                if st.form_submit_button("Crear Orden"):
                    try:
                        supabase.table("ordenes").insert({
                            "descripcion": desc,
                            "id_maquina": mq,
                            "id_tecnico": tc,
                            "tipo_tarea": tt,
                            "prioridad": pr,
                            "estado": "Proceso",
                            "creado_por": st.session_state.user
                        }).execute()
                        st.success("✅ Orden creada exitosamente")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error al insertar en la base de datos: {e}")

    # Visualización de la tabla
    st.divider()
    st.subheader("Historial de Órdenes")
    df_o = pd.DataFrame(cargar("ordenes"))
    if not df_o.empty:
        st.dataframe(df_o, use_container_width=True)
    else:
        st.info("No hay órdenes de trabajo registradas para este usuario.")

# --- 7. RESTO DE SECCIONES (Resumen) ---
elif menu == "🏠 Inicio":
    st.title("📊 Panel de Control")
    st.write(f"Bienvenido, {st.session_state.user}")

elif menu == "👥 Personal":
    st.header("Registro de Personal")
    with st.form("f_p"):
        n = st.text_input("Nombre")
        a = st.text_input("Apellido")
        if st.form_submit_button("Guardar"):
            supabase.table("personal").insert({"nombre": n, "apellido": a, "creado_por": st.session_state.user}).execute()
            st.rerun()

elif menu == "⚙️ Maquinaria":
    st.header("Registro de Máquinas")
    with st.form("f_m"):
        nm = st.text_input("Nombre de Máquina")
        if st.form_submit_button("Registrar"):
            supabase.table("maquinas").insert({"nombre_maquina": nm, "creado_por": st.session_state.user}).execute()
            st.rerun()
