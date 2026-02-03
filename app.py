import streamlit as st
import pandas as pd
from supabase import create_client, Client

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="CORMAIN FINAL", layout="wide")

url = st.secrets["connections"]["supabase"]["SUPABASE_URL"]
key = st.secrets["connections"]["supabase"]["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

# --- CARGA SEGURA ---
def cargar_tabla(nombre):
    res = supabase.table(nombre).select("*").execute()
    return res.data if res.data else []

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
    opcion = st.sidebar.selectbox("Área", ["RRHH", "Maquinaria", "Órdenes"])

    if opcion == "RRHH":
        st.header("👥 Personal")
        with st.form("f1"):
            n = st.text_input("Nombre")
            c = st.text_input("Cargo")
            if st.form_submit_button("Guardar"):
                supabase.table("personal").insert({"nombre": n, "cargo": c}).execute()
                st.rerun()
        st.data_editor(pd.DataFrame(cargar_tabla("personal")), use_container_width=True)

    elif opcion == "Maquinaria":
        st.header("⚙️ Maquinaria")
        with st.form("f2"):
            nm = st.text_input("Nombre Máquina")
            cd = st.text_input("Código")
            if st.form_submit_button("Registrar"):
                supabase.table("maquinas").insert({"nombre_maquina": nm, "codigo": cd}).execute()
                st.rerun()
        st.data_editor(pd.DataFrame(cargar_tabla("maquinas")), use_container_width=True)

    elif opcion == "Órdenes":
        st.header("📑 Nueva Orden")
        
        # LEER DATOS
        maqs = cargar_tabla("maquinas")
        tecs = cargar_tabla("personal")
        
        # MAPEO ULTRA SEGURO (Buscamos 'id' o cualquier columna que se le parezca)
        dict_m = {m.get('nombre_maquina', 'S/N'): m.get('id', m.get('ID', m.get('id_maquina'))) for m in maqs}
        dict_t = {t.get('nombre', 'S/N'): t.get('id', t.get('ID', t.get('id_tecnico'))) for t in tecs}

        with st.form("f_ot"):
            desc = st.text_area("Descripción")
            m_sel = st.selectbox("Máquina", list(dict_m.keys()))
            t_sel = st.selectbox("Asignar a", list(dict_t.keys()))
            
            if st.form_submit_button("Lanzar Orden"):
                id_m = dict_m.get(m_sel)
                id_t = dict_t.get(t_sel)
                
                # VALIDACIÓN ANTES DE ENVIAR (Para evitar el error de la imagen a6b2e4)
                if id_m is None or id_t is None:
                    st.error(f"❌ Error interno: No se encontró el ID de {m_sel} o {t_sel}. Revisa las tablas.")
                else:
                    try:
                        supabase.table("ordenes").insert({
                            "descripcion": desc,
                            "id_maquina": id_m,
                            "id_tecnico": id_t,
                            "estado": "Proceso"
                        }).execute()
                        st.success("✅ ¡Orden creada!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error de base de datos: {e}")

        # TABLERO DE CONTROL
        ots = cargar_tabla("ordenes")
        if ots:
            st.subheader("Órdenes Activas")
            st.dataframe(pd.DataFrame(ots), use_container_width=True)

    if st.sidebar.button("Salir"):
        st.session_state.auth = False
        st.rerun()
