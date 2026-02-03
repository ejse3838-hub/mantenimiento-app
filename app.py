import streamlit as st
import pandas as pd
from supabase import create_client, Client

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="CORMAIN CMMS FINAL", layout="wide")

url = st.secrets["connections"]["supabase"]["SUPABASE_URL"]
key = st.secrets["connections"]["supabase"]["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

# --- CARGA DE DATOS SEGURA ---
def cargar_datos(tabla):
    try:
        res = supabase.table(tabla).select("*").execute()
        return res.data if res.data else []
    except:
        return []

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
    opcion = st.sidebar.selectbox("Área", ["Inicio", "RRHH", "Maquinaria", "Órdenes"])

    # --- RRHH ---
    if opcion == "RRHH":
        st.header("👥 Gestión de Personal")
        with st.form("f_rrhh"):
            nom = st.text_input("Nombre")
            car = st.text_input("Cargo")
            if st.form_submit_button("Guardar"):
                supabase.table("personal").insert({"nombre": nom, "cargo": car}).execute()
                st.rerun()
        df_p = pd.DataFrame(cargar_datos("personal"))
        if not df_p.empty: st.data_editor(df_p, use_container_width=True)

    # --- MAQUINARIA ---
    elif opcion == "Maquinaria":
        st.header("⚙️ Gestión de Activos")
        with st.form("f_maq"):
            n_m = st.text_input("Nombre Máquina")
            c_m = st.text_input("Código")
            if st.form_submit_button("Registrar"):
                supabase.table("maquinas").insert({"nombre_maquina": n_m, "codigo": c_m}).execute()
                st.rerun()
        df_m = pd.DataFrame(cargar_datos("maquinas"))
        if not df_m.empty: st.data_editor(df_m, use_container_width=True)

    # --- ÓRDENES (EL CORAZÓN DEL PROBLEMA) ---
    elif opcion == "Órdenes":
        st.header("📑 Órdenes de Producción")
        
        # Obtenemos los IDs reales de las otras tablas
        maqs = cargar_datos("maquinas")
        tecs = cargar_datos("personal")
        
        # Diccionarios blindados contra KeyError
        dict_m = {m.get('nombre_maquina', 'S/N'): m.get('id') for m in maqs}
        dict_t = {t.get('nombre', 'S/N'): t.get('id') for t in tecs}

        with st.form("f_ot"):
            desc = st.text_area("Descripción")
            m_sel = st.selectbox("Máquina", list(dict_m.keys()))
            t_sel = st.selectbox("Asignar a", list(dict_t.keys()))
            if st.form_submit_button("Lanzar Orden"):
                # Enviamos solo lo básico para que el Default Value de Supabase trabaje
                try:
                    supabase.table("ordenes").insert({
                        "descripcion": desc,
                        "id_maquina": dict_m[m_sel],
                        "id_tecnico": dict_t[t_sel],
                        "estado": "Proceso"
                    }).execute()
                    st.success("✅ ¡Orden creada!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error de base de datos: {e}")

        # TABLERO KANBAN
        st.divider()
        c1, c2, c3 = st.columns(3)
        for est, col in [("Proceso", c1), ("Revisión", c2), ("Finalizada", c3)]:
            with col:
                st.subheader(f"📍 {est}")
                ots = supabase.table("ordenes").select("*").eq("estado", est).execute()
                for ot in ots.data:
                    with st.container(border=True):
                        st.write(ot['descripcion'])
                        if est == "Proceso":
                            if st.button("➡️ Revisar", key=f"r_{ot.get('id', ot.get('descripcion'))}"):
                                supabase.table("ordenes").update({"estado": "Revisión"}).eq("descripcion", ot['descripcion']).execute()
                                st.rerun()

    if st.sidebar.button("Salir"):
        st.session_state.auth = False
        st.rerun()
