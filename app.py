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

st.title("🛠️ CORMAIN - Sistema de Control")

menu = st.sidebar.selectbox("Ir a:", ["RRHH", "Maquinaria", "Órdenes"])

if menu == "RRHH":
    st.header("Personal")
    with st.form("rrhh_form"):
        nom = st.text_input("Nombre")
        car = st.text_input("Cargo")
        esp = st.text_input("Especialidad")
        if st.form_submit_button("Registrar"):
            # Insertamos solo lo básico para asegurar éxito
            supabase.table("personal").insert({"nombre": nom, "cargo": car, "especialidad": esp}).execute()
            st.rerun()
    st.write(cargar("personal"))

elif menu == "Maquinaria":
    st.header("Equipos")
    with st.form("maq_form"):
        n_m = st.text_input("Máquina")
        cod = st.text_input("Código")
        ubi = st.text_input("Ubicación")
        if st.form_submit_button("Guardar"):
            # Insertamos con los nombres exactos de tus columnas
            supabase.table("maquinas").insert({"nombre_maquina": n_m, "codigo": cod, "ubicacion": ubi}).execute()
            st.rerun()
    st.write(cargar("maquinas"))

elif menu == "Órdenes":
    st.header("Nueva Orden")
    maqs = cargar("maquinas")
    pers = cargar("personal")
    
    # Usamos el nombre como identificador para evitar el error de ID
    nombres_m = [m['nombre_maquina'] for m in maqs] if maqs else ["Sin datos"]
    nombres_p = [p['nombre'] for p in pers] if pers else ["Sin datos"]

    with st.form("ot_form"):
        desc = st.text_area("Descripción")
        m_sel = st.selectbox("Máquina", nombres_m)
        t_sel = st.selectbox("Técnico", nombres_p)
        
        if st.form_submit_button("Crear Orden"):
            try:
                # MANDAMOS LOS NOMBRES DIRECTAMENTE
                # Asegúrate que id_maquina e id_tecnico sean tipo TEXT en Supabase
                supabase.table("ordenes").insert({
                    "descripcion": desc,
                    "id_maquina": m_sel, 
                    "id_tecnico": t_sel,
                    "estado": "Proceso"
                }).execute()
                st.success("✅ Orden guardada")
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")
