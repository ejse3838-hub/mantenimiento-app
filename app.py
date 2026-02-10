import streamlit as st
import pandas as pd
from supabase import create_client, Client
import urllib.parse

# --- PROTECCIÓN PARA LOS GRÁFICOS ---
try:
    import plotly.express as px
    GRAFICOS_LISTOS = True
except ImportError:
    GRAFICOS_LISTOS = False

# --- CONEXIÓN ---
url = st.secrets["connections"]["supabase"]["SUPABASE_URL"]
key = st.secrets["connections"]["supabase"]["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

# --- FUNCIÓN DE CARGA DINÁMICA ---
# Esta función es la que evita que los datos se mezclen entre usuarios
def cargar(tabla):
    try:
        res = supabase.table(tabla).select("*").eq("creado_por", st.session_state.user).execute()
        return res.data if res.data else []
    except:
        return []

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="CORMAIN CMMS PRO", layout="wide")

if 'auth' not in st.session_state: st.session_state.auth = False

# --- LOGIN Y REGISTRO ---
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
        new_u = st.text_input("Nuevo Email")
        new_p = st.text_input("Nueva Clave", type="password")
        if st.button("Crear Cuenta"):
            try:
                supabase.table("usuarios").insert({"email": new_u, "password": new_p, "creado_por": new_u}).execute()
                st.success("¡Cuenta creada!")
            except: st.error("Error al crear cuenta.")

else:
    # --- MENÚ LATERAL (BOTONES FIJOS - MÁS DIDÁCTICO) ---
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

    # --- PÁGINAS ---
    
    # 1. INICIO (DASHBOARD)
    if st.session_state.menu == "🏠 Inicio":
        st.title("📊 Panel de Control CORMAIN")
        o_data = cargar("ordenes")
        if o_data:
            df = pd.DataFrame(o_data)
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("En Proceso", len(df[df['estado'] == 'Proceso']))
            c2.metric("Realizadas", len(df[df['estado'] == 'Realizada']))
            c3.metric("Revisadas", len(df[df['estado'] == 'Revisada']))
            c4.metric("Finalizadas", len(df[df['estado'] == 'Finalizada']))
            if GRAFICOS_LISTOS:
                st.divider()
                colg1, colg2 = st.columns(2)
                fig1 = px.pie(df, names='estado', hole=0.4, title="Estado Global")
                colg1.plotly_chart(fig1, use_container_width=True)
                fig2 = px.pie(df, names='id_tecnico', hole=0.4, title="Carga por Técnico")
                colg2.plotly_chart(fig2, use_container_width=True)
        else: st.info("Bienvenido. Registra personal y maquinaria para comenzar.")

    # 2. PERSONAL
    elif st.session_state.menu == "👥 Personal":
        st.header("Gestión de Personal")
        with st.form("f_p"):
            c1, c2 = st.columns(2)
            nom = c1.text_input("Nombre")
            tel = c2.text_input("WhatsApp (ej: 593987654321)")
            car = c1.text_input("Cargo")
            esp = c2.text_input("Especialidad")
            if st.form_submit_button("Guardar"):
                supabase.table("personal").insert({
                    "nombre": nom, "cargo": car, "telefono": tel, 
                    "especialidad": esp, "creado_por": st.session_state.user
                }).execute()
                st.rerun()
        p_res = cargar("personal")
        if p_res: st.table(pd.DataFrame(p_res)[["nombre", "cargo", "telefono"]])

    # 3. MAQUINARIA
    elif st.session_state.menu == "⚙️ Maquinaria":
        st.header("Gestión de Maquinas")
        with st.form("f_m"):
            n_m = st.text_input("Máquina")
            est = st.selectbox("Estado", ["Operativa", "Falla"])
            if st.form_submit_button("Registrar"):
                supabase.table("maquinas").insert({
                    "nombre_maquina": n_m, "estado": est, "creado_por": st.session_state.user
                }).execute()
                st.rerun()
        m_res = cargar("maquinas")
        if m_res: st.table(pd.DataFrame(m_res)[["nombre_maquina", "estado"]])

    # 4. ÓRDENES DE TRABAJO
    elif st.session_state.menu == "📑 Órdenes de Trabajo":
        st.header("Órdenes de Producción")
        
        # CARGAMOS DATOS PARA LOS SELECTORES
        m_list = cargar("maquinas")
        p_list = cargar("personal")
        
        # Validamos que no estén vacíos para evitar el error de la línea 100
        nombres_m = [m['nombre_maquina'] for m in m_list] if m_list else ["Debe registrar maquinaria"]
        nombres_p = [p['nombre'] for p in p_list] if p_list else ["Debe registrar personal"]

        with st.expander("➕ Crear Nueva Orden"):
            with st.form("f_o"):
                desc = st.text_area("Descripción")
                maq = st.selectbox("Seleccionar Máquina", nombres_m)
                tec = st.selectbox("Asignar Técnico", nombres_p)
                if st.form_submit_button("Lanzar"):
                    if "Debe registrar" in nombres_m[0] or "Debe registrar" in nombres_p[0]:
                        st.error("No puedes crear una orden sin maquinaria o personal.")
                    else:
                        supabase.table("ordenes").insert({
                            "descripcion": desc, "id_maquina": maq, "id_tecnico": tec,
                            "estado": "Proceso", "creado_por": st.session_state.user
                        }).execute()
                        st.rerun()
        
        st.divider()
        o_data = cargar("ordenes")
        if o_data:
            df_o = pd.DataFrame(o_data)
            pasos = {"Proceso": "Realizada", "Realizada": "Revisada", "Revisada": "Finalizada"}
            for est_actual in ["Proceso", "Realizada", "Revisada", "Finalizada"]:
                st.subheader(f"📍 {est_actual}")
                items = df_o[df_o['estado'] == est_actual]
                for _, row in items.iterrows():
                    with st.container(border=True):
                        c1, c2, c3 = st.columns([3, 1, 1])
                        c1.write(f"**{row['id_maquina']}**: {row['descripcion']} ({row['id_tecnico']})")
                        
                        # Botón de avance
                        if est_actual in pasos:
                            if c2.button(f"➡️ {pasos[est_actual]}", key=f"av_{row['id']}"):
                                supabase.table("ordenes").update({"estado": pasos[est_actual]}).eq("id", row['id']).execute()
                                st.rerun()
                        
                        # Botón de eliminar (🗑️)
                        if est_actual in ["Proceso", "Finalizada"]:
                            if c3.button("🗑️", key=f"del_{row['id']}"):
                                supabase.table("ordenes").delete().eq("id", row['id']).execute()
                                st.rerun()

                        # Botón de WhatsApp (📲)
                        if est_actual == "Proceso":
                            # Buscamos el teléfono del técnico asignado
                            t_info = next((p for p in p_list if p['nombre'] == row['id_tecnico']), None)
                            if t_info and t_info.get('telefono'):
                                msg = urllib.parse.quote(f"Hola {row['id_tecnico']}, tienes una orden pendiente: {row['descripcion']} en la máquina {row['id_maquina']}.")
                                c2.link_button("📲 Notificar", f"https://wa.me/{t_info['telefono']}?text={msg}")
