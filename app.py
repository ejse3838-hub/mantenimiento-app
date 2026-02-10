import streamlit as st
import pandas as pd
from supabase import create_client, Client
from streamlit_drawable_canvas import st_canvas

# --- CONEXIÓN ---
url = st.secrets["connections"]["supabase"]["SUPABASE_URL"]
key = st.secrets["connections"]["supabase"]["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

# --- FUNCIÓN DE CARGA ---
def cargar(tabla):
    try:
        res = supabase.table(tabla).select("*").eq("creado_por", st.session_state.user).execute()
        return res.data if res.data else []
    except Exception:
        return []

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="CORMAIN CMMS PRO", layout="wide")
if 'auth' not in st.session_state: st.session_state.auth = False

# --- LOGIN ---
if not st.session_state.auth:
    tab1, tab2 = st.tabs(["🔑 Iniciar Sesión", "📝 Registrarse"])
    with tab1:
        u = st.text_input("Email/Usuario")
        p = st.text_input("Clave", type="password")
        if st.button("Entrar"):
            res = supabase.table("usuarios").select("*").eq("email", u).eq("password", p).execute()
            if res.data: 
                st.session_state.auth = True
                st.session_state.user = res.data[0]['email']
                st.rerun()
            else: st.error("Datos incorrectos")
    with tab2:
        nu, np = st.text_input("Nuevo Email"), st.text_input("Nueva Clave", type="password")
        if st.button("Crear Cuenta"):
            supabase.table("usuarios").insert({"email": nu, "password": np, "creado_por": nu}).execute()
            st.success("¡Cuenta creada!")

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

    # --- 1. INICIO ---
    if st.session_state.menu == "🏠 Inicio":
        st.title("📊 Panel de Control")
        df = pd.DataFrame(cargar("ordenes"))
        if not df.empty:
            c1, c2 = st.columns(2)
            c1.metric("Órdenes Totales", len(df))
            if 'costo' in df.columns:
                c2.metric("Inversión Total", f"${df['costo'].sum():,.2f}")
            import plotly.express as px
            fig = px.pie(df, names='estado', hole=0.4, title="Estado de Órdenes")
            st.plotly_chart(fig, use_container_width=True)
        else: st.info("Sin datos registrados.")

    # --- 2. PERSONAL ---
    elif st.session_state.menu == "👥 Personal":
        st.header("Gestión de Personal")
        with st.form("f_p"):
            c1, c2 = st.columns(2)
            n, a = c1.text_input("Nombre"), c2.text_input("Apellido")
            car, esp = c1.text_input("Cargo"), c2.text_input("Especialidad")
            if st.form_submit_button("Guardar"):
                supabase.table("personal").insert({
                    "nombre": n, "apellido": a, "cargo": car, "especialidad": esp,
                    "creado_por": st.session_state.user
                }).execute()
                st.rerun()
        st.dataframe(pd.DataFrame(cargar("personal")), use_container_width=True)

    # --- 3. MAQUINARIA ---
    elif st.session_state.menu == "⚙️ Maquinaria":
        st.header("Ficha Técnica")
        with st.form("f_m"):
            c1, c2 = st.columns(2)
            nm, cod = c1.text_input("Máquina"), c2.text_input("Código")
            ubi, est = c1.text_input("Ubicación"), c2.selectbox("Estado", ["Operativa", "Mantenimiento"])
            if st.form_submit_button("Registrar"):
                # Sincronizado con tus columnas reales
                supabase.table("maquinas").insert({
                    "nombre_maquina": nm, "codigo": cod, "ubicacion": ubi, 
                    "estado": est, "creado_por": st.session_state.user
                }).execute()
                st.rerun()
        st.dataframe(pd.DataFrame(cargar("maquinas")), use_container_width=True)

    # --- 4. ÓRDENES (VERSION SIMPLIFICADA PARA EVITAR ERRORES) ---
    elif st.session_state.menu == "📑 Órdenes de Trabajo":
        st.header("Gestión de OP")
        m_list = [f"{m['nombre_maquina']} ({m['codigo']})" for m in cargar("maquinas")]
        p_list = [p['nombre'] for p in cargar("personal")]
        
        with st.expander("➕ Lanzar Nueva OP"):
            with st.form("f_op"):
                desc = st.text_area("Descripción")
                c1, c2, c3 = st.columns(3)
                mq, tc, pr = c1.selectbox("Máquina", m_list), c2.selectbox("Técnico", p_list), c3.selectbox("Prioridad", ["ALTA", "BAJA"])
                
                # Campos adicionales que causaban errores si no estaban en Supabase
                tt = st.selectbox("Tipo", ["Correctiva", "Preventiva"])
                cos = st.number_input("Costo ($)", 0.0)

                if st.form_submit_button("Lanzar"):
                    # Si alguna de estas columnas no existe en Supabase, bórrala de aquí
                    supabase.table("ordenes").insert({
                        "descripcion": desc, "id_maquina": mq, "id_tecnico": tc, 
                        "prioridad": pr, "costo": cos, "tipo_tarea": tt,
                        "estado": "Proceso", "creado_por": st.session_state.user
                    }).execute()
                    st.rerun()

        st.divider()
        df_o = pd.DataFrame(cargar("ordenes"))
        if not df_o.empty:
            for _, row in df_o.iterrows():
                with st.container(border=True):
                    st.write(f"**{row['id_maquina']}** | {row['prioridad']}")
                    st.write(row['descripcion'])
                    # Firma simplificada para evitar errores de Script Execution
                    st.write("✒️ Firma Jefe")
                    st_canvas(stroke_width=2, stroke_color="black", height=80, width=250, key=f"f_{row['id']}")
                    if st.button("🗑️ Eliminar", key=f"del_{row['id']}"):
                        supabase.table("ordenes").delete().eq("id", row['id']).execute()
                        st.rerun()
