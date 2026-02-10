import streamlit as st
import pandas as pd
from supabase import create_client, Client

# --- CONEXIÓN ---
url = st.secrets["connections"]["supabase"]["SUPABASE_URL"]
key = st.secrets["connections"]["supabase"]["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

# --- FUNCIÓN DE CARGA ---
def cargar(tabla):
    try:
        res = supabase.table(tabla).select("*").eq("creado_por", st.session_state.user).execute()
        return res.data if res.data else []
    except:
        return []

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="CORMAIN CMMS PRO", layout="wide")

if 'auth' not in st.session_state: st.session_state.auth = False

# --- LOGIN ---
if not st.session_state.auth:
    tab1, tab2 = st.tabs(["🔑 Login", "📝 Registro"])
    with tab1:
        u = st.text_input("Usuario")
        p = st.text_input("Clave", type="password")
        if st.button("Entrar"):
            res = supabase.table("usuarios").select("*").eq("email", u).eq("password", p).execute()
            if res.data: 
                st.session_state.auth = True
                st.session_state.user = res.data[0]['email']
                st.rerun()
            else: st.error("Datos incorrectos")
    with tab2:
        new_u = st.text_input("Nuevo Email")
        new_p = st.text_input("Nueva Clave", type="password")
        if st.button("Crear Cuenta"):
            try:
                supabase.table("usuarios").insert({"email": new_u, "password": new_p, "creado_por": new_u}).execute()
                st.success("¡Cuenta creada!")
            except: st.error("Error")

else:
    # --- MENÚ LATERAL ---
    st.sidebar.title(f"👤 {st.session_state.user}")
    if "menu" not in st.session_state: st.session_state.menu = "🏠 Inicio"

    if st.sidebar.button("🏠 Inicio", use_container_width=True): st.session_state.menu = "🏠 Inicio"
    if st.sidebar.button("👥 Personal", use_container_width=True): st.session_state.menu = "👥 Personal"
    if st.sidebar.button("⚙️ Maquinaria", use_container_width=True): st.session_state.menu = "⚙️ Maquinaria"
    if st.sidebar.button("📑 Órdenes de Trabajo", use_container_width=True): st.session_state.menu = "📑 Órdenes de Trabajo"
    
    st.sidebar.divider()
    if st.sidebar.button("🚪 Cerrar Sesión", use_container_width=True):
        st.session_state.auth = False
        st.rerun()

    # --- INICIO ---
    if st.session_state.menu == "🏠 Inicio":
        st.title("📊 Panel de Control")
        o_data = cargar("ordenes")
        if o_data:
            df = pd.DataFrame(o_data)
            st.metric("Total Órdenes", len(df))
            st.dataframe(df[['descripcion', 'estado', 'id_tecnico']], use_container_width=True)
        else: st.info("Sin datos")

    # --- PERSONAL (SIN TELÉFONO) ---
    elif st.session_state.menu == "👥 Personal":
        st.header("Gestión de Personal")
        with st.form("f_p"):
            nom = st.text_input("Nombre del Técnico")
            car = st.text_input("Cargo")
            if st.form_submit_button("Guardar"):
                supabase.table("personal").insert({"nombre": nom, "cargo": car, "creado_por": st.session_state.user}).execute()
                st.rerun()
        p_res = cargar("personal")
        if p_res: st.table(pd.DataFrame(p_res)[["nombre", "cargo"]])

    # --- MAQUINARIA ---
    elif st.session_state.menu == "⚙️ Maquinaria":
        st.header("Gestión de Maquinas")
        with st.form("f_m"):
            n_m = st.text_input("Máquina")
            if st.form_submit_button("Registrar"):
                supabase.table("maquinas").insert({"nombre_maquina": n_m, "creado_por": st.session_state.user}).execute()
                st.rerun()
        m_res = cargar("maquinas")
        if m_res: st.table(pd.DataFrame(m_res)[["nombre_maquina"]])

    # --- ORDENES (LÓGICA SIMPLIFICADA) ---
    elif st.session_state.menu == "📑 Órdenes de Trabajo":
        st.header("Órdenes de Producción")
        
        m_list = cargar("maquinas")
        p_list = cargar("personal")
        
        nombres_m = [m['nombre_maquina'] for m in m_list] if m_list else ["Registrar máquinas"]
        nombres_p = [p['nombre'] for p in p_list] if p_list else ["Registrar personal"]

        with st.expander("➕ Nueva Orden"):
            with st.form("f_o"):
                desc = st.text_area("Tarea")
                maq = st.selectbox("Máquina", nombres_m)
                tec = st.selectbox("Técnico", nombres_p)
                if st.form_submit_button("Lanzar"):
                    supabase.table("ordenes").insert({
                        "descripcion": desc, "id_maquina": maq, "id_tecnico": tec,
                        "estado": "Proceso", "creado_por": st.session_state.user
                    }).execute()
                    st.rerun()
        
        st.divider()
        o_data = cargar("ordenes")
        if o_data:
            df_o = pd.DataFrame(o_data)
            for est in ["Proceso", "Realizada", "Finalizada"]:
                st.subheader(f"📍 {est}")
                filas = df_o[df_o['estado'] == est]
                for _, row in filas.iterrows():
                    with st.container(border=True):
                        c1, c2 = st.columns([4, 1])
                        c1.write(f"**{row['id_maquina']}**: {row['descripcion']} ({row['id_tecnico']})")
                        
                        # Botón para borrar
                        if c2.button("🗑️ Borrar", key=f"del_{row['id']}"):
                            supabase.table("ordenes").delete().eq("id", row['id']).execute()
                            st.rerun()
                            
