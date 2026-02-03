import streamlit as st
import pandas as pd
from supabase import create_client, Client

# --- CONEXIÓN ---
url = st.secrets["connections"]["supabase"]["SUPABASE_URL"]
key = st.secrets["connections"]["supabase"]["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

def cargar(tabla):
    try:
        res = supabase.table(tabla).select("*").execute()
        return res.data if res.data else []
    except: return []

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="CORMAIN CMMS PRO", layout="wide")

# --- LOGIN ---
if 'auth' not in st.session_state: st.session_state.auth = False
if not st.session_state.auth:
    st.title("🛡️ Sistema CORMAIN")
    u, p = st.text_input("Usuario"), st.text_input("Clave", type="password")
    if st.button("Entrar"):
        res = supabase.table("usuarios").select("*").eq("email", u).eq("password", p).execute()
        if res.data: 
            st.session_state.auth = True
            st.rerun()
else:
    # --- MENÚ LATERAL ---
    menu = st.sidebar.selectbox("Navegación", ["🏠 Inicio", "👥 Personal", "⚙️ Maquinaria", "📑 Órdenes de Trabajo"])

    # --- 1. PÁGINA DE INICIO (RESUMEN) ---
    if menu == "🏠 Inicio":
        st.title("📊 Panel de Control CORMAIN")
        col1, col2, col3 = st.columns(3)
        
        m_data = cargar("maquinas")
        p_data = cargar("personal")
        o_data = cargar("ordenes")

        col1.metric("Total Máquinas", len(m_data))
        col2.metric("Personal Activo", len(p_data))
        col3.metric("Órdenes Totales", len(o_data))

        st.subheader("📋 Resumen de Actividad Reciente")
        if o_data:
            df_o = pd.DataFrame(o_data)
            st.dataframe(df_o[["id", "descripcion", "id_maquina", "estado"]].tail(5), use_container_width=True)

    # --- 2. PERSONAL (RESTABLECIDO) ---
    elif menu == "👥 Personal":
        st.header("Gestión de Recursos Humanos")
        with st.form("f_rrhh"):
            nom = st.text_input("Nombre Completo (ID)")
            car = st.text_input("Cargo")
            esp = st.text_input("Especialidad")
            if st.form_submit_button("Registrar Empleado"):
                supabase.table("personal").insert({"nombre": nom, "cargo": car, "especialidad": esp}).execute()
                st.success("Personal guardado")
                st.rerun()
        
        st.subheader("Lista de Personal")
        st.dataframe(pd.DataFrame(cargar("personal")), use_container_width=True)

    # --- 3. MAQUINARIA (RESTABLECIDO) ---
    elif menu == "⚙️ Maquinaria":
        st.header("Control de Herramientas y Máquinas")
        with st.form("f_maq"):
            col_a, col_b = st.columns(2)
            n_m = col_a.text_input("Nombre Máquina")
            cod = col_b.text_input("Código de Inventario")
            ubi = col_a.text_input("Ubicación en Planta")
            est = col_b.selectbox("Estado", ["Operativa", "Falla", "Mantenimiento"])
            if st.form_submit_button("Guardar Máquina"):
                supabase.table("maquinas").insert({"nombre_maquina": n_m, "codigo": cod, "ubicacion": ubi, "estado": est}).execute()
                st.rerun()
        
        st.subheader("Inventario de Maquinaria")
        st.dataframe(pd.DataFrame(cargar("maquinas")), use_container_width=True)

    # --- 4. ÓRDENES (CON HISTORIAL COMPLETO) ---
    elif menu == "📑 Órdenes de Trabajo":
        st.header("Generación de Órdenes")
        
        m_list = [m['nombre_maquina'] for m in cargar("maquinas")]
        p_list = [p['nombre'] for p in cargar("personal")]

        with st.form("f_orden"):
            desc = st.text_area("Detalle del trabajo")
            maq_s = st.selectbox("Máquina", m_list)
            tec_s = st.selectbox("Técnico Asignado", p_list)
            if st.form_submit_button("Lanzar Orden"):
                try:
                    # Enviamos nombres como texto (Recuerda cambiar a TEXT en Supabase)
                    supabase.table("ordenes").insert({
                        "descripcion": desc,
                        "id_maquina": maq_s,
                        "id_tecnico": tec_s,
                        "estado": "Proceso"
                    }).execute()
                    st.success("✅ Orden registrada en la base de datos")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")

        st.divider()
        st.subheader("📜 Historial de Órdenes Realizadas")
        st.table(pd.DataFrame(cargar("ordenes")))

    if st.sidebar.button("Cerrar Sesión"):
        st.session_state.auth = False
        st.rerun()
