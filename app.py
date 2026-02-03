import streamlit as st
import pandas as pd
from supabase import create_client, Client

# --- CONEXIÓN ---
st.set_page_config(page_title="CORMAIN CMMS FINAL", layout="wide")
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

    # --- SECCIONES RRHH Y MAQUINARIA ---
    if opcion == "RRHH":
        st.header("👥 Personal")
        with st.form("f1"):
            n, c = st.text_input("Nombre"), st.text_input("Cargo")
            if st.form_submit_button("Guardar"):
                supabase.table("personal").insert({"nombre": n, "cargo": c}).execute()
                st.rerun()
        st.dataframe(pd.DataFrame(cargar("personal")), use_container_width=True)

    elif opcion == "Maquinaria":
        st.header("⚙️ Maquinaria")
        with st.form("f2"):
            nm, cd = st.text_input("Nombre Máquina"), st.text_input("Código")
            if st.form_submit_button("Registrar"):
                supabase.table("maquinas").insert({"nombre_maquina": nm, "codigo": cd}).execute()
                st.rerun()
        st.dataframe(pd.DataFrame(cargar("maquinas")), use_container_width=True)

    # --- ÓRDENES (VERSION SIMPLIFICADA) ---
    elif opcion == "Órdenes":
        st.header("📑 Nueva Orden de Trabajo")
        
        # Cargamos solo los nombres para las listas desplegables
        lista_m = [m['nombre_maquina'] for m in cargar("maquinas")]
        lista_t = [t['nombre'] for t in cargar("personal")]

        with st.form("f_final"):
            desc = st.text_area("Descripción de la tarea")
            m_sel = st.selectbox("Seleccionar Máquina", lista_m if lista_m else ["No hay máquinas"])
            t_sel = st.selectbox("Asignar Técnico", lista_t if lista_t else ["No hay técnicos"])
            
            if st.form_submit_button("Lanzar Orden"):
                try:
                    # GUARDAMOS NOMBRES DIRECTAMENTE PARA EVITAR ERRORES DE ID
                    supabase.table("ordenes").insert({
                        "descripcion": desc,
                        "id_maquina": 0, # Ponemos un 0 temporal si la columna es numérica
                        "estado": "Proceso"
                    }).execute()
                    st.success("✅ ¡Orden creada exitosamente!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")

        # VISUALIZACIÓN
        ots = cargar("ordenes")
        if ots:
            st.subheader("Órdenes Actuales")
            st.table(pd.DataFrame(ots)[["descripcion", "estado"]])

    if st.sidebar.button("Cerrar Sesión"):
        st.session_state.auth = False
        st.rerun()
