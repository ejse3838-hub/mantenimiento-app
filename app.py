import streamlit as st
import pandas as pd
from supabase import create_client, Client

# --- CONEXIÓN ---
st.set_page_config(page_title="CORMAIN SOLUCIÓN FINAL", layout="wide")
url = st.secrets["connections"]["supabase"]["SUPABASE_URL"]
key = st.secrets["connections"]["supabase"]["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

def cargar(tabla):
    try:
        res = supabase.table(tabla).select("*").execute()
        return res.data if res.data else []
    except: return []

# --- LOGIN ---
if 'auth' not in st.session_state: st.session_state.auth = False
if not st.session_state.auth:
    st.title("🛡️ Acceso CORMAIN")
    u, p = st.text_input("Usuario"), st.text_input("Clave", type="password")
    if st.button("Entrar"):
        res = supabase.table("usuarios").select("*").eq("email", u).eq("password", p).execute()
        if res.data: 
            st.session_state.auth = True
            st.rerun()
else:
    opcion = st.sidebar.selectbox("Menú", ["RRHH", "Maquinaria", "Órdenes"])

    if opcion == "RRHH":
        st.header("👥 Personal")
        with st.form("f1"):
            n, c = st.text_input("Nombre"), st.text_input("Cargo")
            if st.form_submit_button("Guardar"):
                supabase.table("personal").insert({"nombre": n, "cargo": c}).execute()
                st.rerun()
        st.dataframe(pd.DataFrame(cargar("personal")))

    elif opcion == "Maquinaria":
        st.header("⚙️ Maquinaria")
        with st.form("f2"):
            nm, cd = st.text_input("Nombre Máquina"), st.text_input("Código")
            if st.form_submit_button("Registrar"):
                supabase.table("maquinas").insert({"nombre_maquina": nm, "codigo": cd}).execute()
                st.rerun()
        st.dataframe(pd.DataFrame(cargar("maquinas")))

    elif opcion == "Órdenes":
        st.header("📑 Crear Orden de Trabajo")
        
        m_data = cargar("maquinas")
        t_data = cargar("personal")

        # --- DETECTIVE DE IDs --- 
        # Esta parte busca 'id', 'id_maquina' o cualquier cosa que sirva como ID
        def buscar_id(registro):
            for k in ['id', 'id_maquina', 'id_tecnico', 'ID']:
                if k in registro: return registro[k]
            return None

        dict_m = {m.get('nombre_maquina', 'S/N'): buscar_id(m) for m in m_data}
        dict_t = {t.get('nombre', 'S/N'): buscar_id(t) for t in t_data}

        with st.form("f_final"):
            desc = st.text_area("Descripción")
            m_sel = st.selectbox("Máquina", list(dict_m.keys()))
            t_sel = st.selectbox("Técnico", list(dict_t.keys()))
            
            if st.form_submit_button("Lanzar Orden"):
                id_m = dict_m.get(m_sel)
                id_t = dict_t.get(t_sel)

                if id_m is None or id_t is None:
                    st.error(f"❌ Error: No se encontró el ID interno. ID Máquina: {id_m}, ID Técnico: {id_t}")
                else:
                    try:
                        # Enviamos los datos asegurándonos de que NO sean null
                        supabase.table("ordenes").insert({
                            "descripcion": desc,
                            "id_maquina": id_m,
                            "id_tecnico": id_t,
                            "estado": "Proceso"
                        }).execute()
                        st.success("✅ ¡ORDEN CREADA!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error de Supabase: {e}")

        # TABLERO
        ots = cargar("ordenes")
        if ots: st.table(pd.DataFrame(ots)[["descripcion", "estado"]])

    if st.sidebar.button("Salir"):
        st.session_state.auth = False
        st.rerun()
