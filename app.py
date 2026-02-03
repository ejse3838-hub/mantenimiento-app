import streamlit as st
import pandas as pd
from supabase import create_client, Client

# 1. CONEXIÓN
st.set_page_config(page_title="CORMAIN CMMS v2.0", layout="wide")
url = st.secrets["connections"]["supabase"]["SUPABASE_URL"]
key = st.secrets["connections"]["supabase"]["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

def obtener_datos(tabla):
    res = supabase.table(tabla).select("*").execute()
    return res.data

# --- LOGIN ---
if 'auth' not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    st.title("🛡️ Acceso CORMAIN")
    u = st.text_input("Email")
    p = st.text_input("Password", type="password")
    if st.button("Entrar"):
        res = supabase.table("usuarios").select("*").eq("email", u).eq("password", p).execute()
        if res.data:
            st.session_state.auth = True
            st.rerun()
else:
    opcion = st.sidebar.selectbox("Área", ["Recursos Humanos", "Maquinaria", "Órdenes de Trabajo"])

    # --- RRHH (AQUÍ ESTÁ TU ID DE TÉCNICO) ---
    if opcion == "Recursos Humanos":
        st.header("👥 Gestión de Personal")
        with st.expander("➕ Registrar"):
            with st.form("f1"):
                n = st.text_input("Nombre")
                c = st.text_input("Cargo")
                if st.form_submit_button("Guardar"):
                    supabase.table("personal").insert({"nombre": n, "cargo": c}).execute()
                    st.rerun()
        
        datos = obtener_datos("personal")
        if datos:
            # Mostramos el ID para que veas que sí existe internamente
            st.data_editor(pd.DataFrame(datos), key="ed_p", use_container_width=True)

    # --- MAQUINARIA (AQUÍ ESTÁ TU ID DE MÁQUINA) ---
    elif opcion == "Maquinaria":
        st.header("⚙️ Gestión de Activos")
        with st.expander("➕ Registrar"):
            with st.form("f2"):
                n_m = st.text_input("Nombre Máquina")
                cod = st.text_input("Código")
                if st.form_submit_button("Guardar"):
                    supabase.table("maquinas").insert({"nombre_maquina": n_m, "codigo": cod}).execute()
                    st.rerun()
        
        datos_m = obtener_datos("maquinas")
        if datos_m:
            st.data_editor(pd.DataFrame(datos_m), key="ed_m", use_container_width=True)

    # --- ÓRDENES (LA SOLUCIÓN AL PROBLEMA) ---
    elif opcion == "Órdenes de Trabajo":
        st.header("📑 Órdenes de Producción")
        
        # 1. Jalamos los datos para obtener los IDs "escondidos"
        maqs = obtener_datos("maquinas")
        tecs = obtener_datos("personal")
        
        # Creamos diccionarios para traducir NOMBRES a IDs
        dict_m = {m['nombre_maquina']: m['id'] for m in maqs} if maqs else {}
        dict_t = {t['nombre']: t['id'] for t in tecs} if tecs else {}

        with st.expander("🆕 Crear Nueva Orden"):
            with st.form("ot_form"):
                desc = st.text_area("Descripción")
                m_nom = st.selectbox("Seleccionar Máquina", list(dict_m.keys()) if dict_m else ["No hay máquinas"])
                t_nom = st.selectbox("Asignar Técnico", list(dict_t.keys()) if dict_t else ["No hay técnicos"])
                
                if st.form_submit_button("Lanzar Orden"):
                    if dict_m and dict_t:
                        # ENVIAMOS LOS IDS QUE SUPABASE EXIGE
                        res = supabase.table("ordenes").insert({
                            "descripcion": desc,
                            "id_maquina": dict_m[m_nom], # Aquí está la magia
                            "id_tecnico": dict_t[t_nom], # Y aquí también
                            "estado": "Proceso"
                        }).execute()
                        st.success("✅ Orden creada con éxito")
                        st.rerun()
                    else:
                        st.error("Debes tener máquinas y personal registrados primero.")

        # Kanban simple para ver que funciona
        ots = obtener_datos("ordenes")
        if ots:
            st.subheader("Estado de Órdenes")
            st.table(pd.DataFrame(ots)[["id", "descripcion", "estado"]])

    if st.sidebar.button("Cerrar Sesión"):
        st.session_state.auth = False
        st.rerun()
