import streamlit as st
import pandas as pd
from supabase import create_client, Client

# --- CONEXIÓN ---
url = st.secrets["connections"]["supabase"]["SUPABASE_URL"]
key = st.secrets["connections"]["supabase"]["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="CORMAIN CMMS PRO", layout="wide")

if 'auth' not in st.session_state: st.session_state.auth = False

# --- LOGIN ---
if not st.session_state.auth:
    u = st.text_input("Usuario")
    p = st.text_input("Clave", type="password")
    if st.button("Entrar"):
        res = supabase.table("usuarios").select("*").eq("email", u).eq("password", p).execute()
        if res.data:
            st.session_state.auth = True
            st.session_state.user = res.data[0]['email']
            st.rerun()
        else: st.error("Error")
else:
    # --- MENÚ ---
    menu = st.sidebar.radio("Navegación", ["Inicio", "Personal", "Maquinas", "Ordenes"])
    
    # --- PÁGINA ORDENES (Donde estaba el error) ---
    if menu == "Ordenes":
        st.header("📑 Órdenes de Trabajo")
        
        # 1. Traemos la data cruda de Supabase
        m_res = supabase.table("maquinas").select("*").execute()
        p_res = supabase.table("personal").select("*").execute()
        
        # 2. Creamos las listas de nombres (SIN filtros complicados para evitar el error)
        lista_m = [i['nombre_maquina'] for i in m_res.data] if m_res.data else ["Vacio"]
        lista_p = [i['nombre'] for i in p_res.data] if p_res.data else ["Vacio"]
        
        with st.form("nueva_op"):
            tarea = st.text_area("Descripción")
            # Usamos las listas ya procesadas
            m_sel = st.selectbox("Máquina", lista_m)
            p_sel = st.selectbox("Técnico", lista_p)
            
            if st.form_submit_button("Crear"):
                supabase.table("ordenes").insert({
                    "descripcion": tarea, 
                    "id_maquina": m_sel, 
                    "id_tecnico": p_sel, 
                    "estado": "Proceso",
                    "creado_por": st.session_state.user # Aquí solo guardamos quién la hizo
                }).execute()
                st.rerun()
