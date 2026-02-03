import streamlit as st
import pandas as pd
from supabase import create_client, Client

# --- CONEXIÓN ---
st.set_page_config(page_title="CORMAIN CMMS PRO", layout="wide")
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

    # --- SECCIÓN RRHH (CON ESPECIALIDAD) ---
    if opcion == "RRHH":
        st.header("👥 Gestión de Personal")
        with st.form("f_rrhh"):
            n = st.text_input("Nombre")
            c = st.text_input("Cargo")
            e = st.text_input("Especialidad") # Agregamos especialidad
            if st.form_submit_button("Guardar"):
                supabase.table("personal").insert({"nombre": n, "cargo": c, "especialidad": e}).execute()
                st.rerun()
        
        datos_p = cargar("personal")
        if datos_p:
            st.subheader("Personal Registrado")
            st.data_editor(pd.DataFrame(datos_p), use_container_width=True)

    # --- SECCIÓN MAQUINARIA (CON UBICACIÓN Y ESTADO) ---
    elif opcion == "Maquinaria":
        st.header("⚙️ Gestión de Maquinaria")
        with st.form("f_maq"):
            col1, col2 = st.columns(2)
            nm = col1.text_input("Nombre Máquina")
            cd = col2.text_input("Código")
            ub = col1.text_input("Ubicación") # Agregamos ubicación
            es = col2.selectbox("Estado", ["Operativa", "Mantenimiento", "Fuera de Servicio"]) # Agregamos estado
            if st.form_submit_button("Registrar Máquina"):
                supabase.table("maquinas").insert({
                    "nombre_maquina": nm, 
                    "codigo": cd, 
                    "ubicacion": ub, 
                    "estado": es
                }).execute()
                st.rerun()
        
        datos_m = cargar("maquinas")
        if datos_m:
            st.subheader("Inventario de Equipos")
            st.data_editor(pd.DataFrame(datos_m), use_container_width=True)

    # --- SECCIÓN ÓRDENES (CORRECCIÓN DE ERROR INTERNO) ---
    elif opcion == "Órdenes":
        st.header("📑 Órdenes de Trabajo")
        
        m_data = cargar("maquinas")
        t_data = cargar("personal")

        # Buscamos los índices de la fila para no depender del nombre de la columna ID
        # Esto soluciona el error de "ID no encontrado"
        dict_m = {m.get('nombre_maquina', 'S/N'): m.get('id', 0) for m in m_data}
        dict_t = {t.get('nombre', 'S/N'): t.get('id', 0) for t in t_data}

        with st.form("f_ot"):
            desc = st.text_area("Descripción de la tarea")
            m_sel = st.selectbox("Máquina", list(dict_m.keys()))
            t_sel = st.selectbox("Técnico", list(dict_t.keys()))
            
            if st.form_submit_button("Lanzar Orden"):
                id_m = dict_m.get(m_sel)
                id_t = dict_t.get(t_sel)
                
                try:
                    supabase.table("ordenes").insert({
                        "descripcion": desc,
                        "id_maquina": id_m,
                        "id_tecnico": id_t,
                        "estado": "Proceso"
                    }).execute()
                    st.success("✅ ¡Orden creada!")
                    st.rerun()
                except Exception as ex:
                    st.error(f"Error al guardar orden: {ex}")

    if st.sidebar.button("Salir"):
        st.session_state.auth = False
        st.rerun()
