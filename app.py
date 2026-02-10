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

# --- FUNCIÓN DE CARGA FILTRADA POR USUARIO ---
def cargar(tabla):
    try:
        # Filtramos para que solo traiga los datos del usuario logueado
        res = supabase.table(tabla).select("*").eq("creado_por", st.session_state.user).execute()
        return res.data if res.data else []
    except: return []

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="CORMAIN CMMS PRO", layout="wide")

# --- LOGIN ---
if 'auth' not in st.session_state: st.session_state.auth = False

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
                supabase.table("usuarios").insert({"email": new_u, "password": new_p}).execute()
                st.success("¡Cuenta creada!")
            except: st.error("Error al crear cuenta.")

else:
    # --- MENÚ LATERAL MEJORADO (Botones en lugar de selectbox) ---
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

    # --- LÓGICA DE PÁGINAS ---
    
    # 1. INICIO
    if st.session_state.menu == "🏠 Inicio":
        st.title("📊 Panel de Control")
        o_data = cargar("ordenes")
        df = pd.DataFrame(o_data)
        if not df.empty:
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
        else:
            st.info("No hay datos para mostrar.")

    # 2. PERSONAL
    elif st.session_state.menu == "👥 Personal":
        st.header("Gestión de Personal")
        with st.form("f_pers"):
            c1, c2 = st.columns(2)
            nom = c1.text_input("Nombre")
            car = c2.text_input("Cargo")
            tel = c1.text_input("WhatsApp (ej: +593987654321)")
            esp = c2.text_input("Especialidad")
            if st.form_submit_button("Guardar"):
                supabase.table("personal").insert({
                    "nombre": nom, "cargo": car, "telefono": tel, 
                    "especialidad": esp, "creado_por": st.session_state.user
                }).execute()
                st.rerun()
        st.table(pd.DataFrame(cargar("personal")))

    # 3. MAQUINARIA
    elif st.session_state.menu == "⚙️ Maquinaria":
        st.header("Gestión de Maquinas")
        with st.form("f_maq"):
            n_m = st.text_input("Máquina")
            est = st.selectbox("Estado", ["Operativa", "Falla"])
            if st.form_submit_button("Registrar"):
                supabase.table("maquinas").insert({
                    "nombre_maquina": n_m, "estado": est, "creado_por": st.session_state.user
                }).execute()
                st.rerun()
        st.table(pd.DataFrame(cargar("maquinas")))

    # 4. ÓRDENES DE TRABAJO
    elif st.session_state.menu == "📑 Órdenes de Trabajo":
        st.header("Órdenes de Producción")
        
        with st.expander("➕ Crear Nueva"):
            maqs = [m['nombre_maquina'] for m in cargar("maquinas")]
            pers_data = cargar("personal")
            pers_dict = {p['nombre']: p['telefono'] for p in pers_data} # Para sacar el tel después
            
            with st.form("f_orden"):
                desc = st.text_area("Descripción")
                maq = st.selectbox("Máquina", maqs)
                tec = st.selectbox("Técnico", list(pers_dict.keys()))
                if st.form_submit_button("Lanzar"):
                    supabase.table("ordenes").insert({
                        "descripcion": desc, "id_maquina": maq, "id_tecnico": tec,
                        "estado": "Proceso", "creado_por": st.session_state.user
                    }).execute()
                    st.rerun()

        st.divider()
        df_o = pd.DataFrame(cargar("ordenes"))
        if not df_o.empty:
            for est in ["Proceso", "Realizada", "Revisada", "Finalizada"]:
                st.subheader(f"📍 {est}")
                items = df_o[df_o['estado'] == est]
                for _, row in items.iterrows():
                    with st.container(border=True):
                        c1, c2, c3 = st.columns([3, 1, 1])
                        c1.write(f"**{row['id_maquina']}**: {row['descripcion']} ({row['id_tecnico']})")
                        
                        # Botón de Avanzar
                        pasos = {"Proceso": "Realizada", "Realizada": "Revisada", "Revisada": "Finalizada"}
                        if est in pasos:
                            if c2.button(f"➡️ {pasos[est]}", key=f"av_{row['id']}"):
                                supabase.table("ordenes").update({"estado": pasos[est]}).eq("id", row['id']).execute()
                                st.rerun()
                        
                        # Botón ELIMINAR (Para Proceso y Finalizada)
                        if est in ["Proceso", "Finalizada"]:
                            if c3.button("🗑️ Eliminar", key=f"del_{row['id']}"):
                                supabase.table("ordenes").delete().eq("id", row['id']).execute()
                                st.rerun()
                        
                        # Botón NOTIFICAR WHATSAPP (Aparece en Proceso)
                        if est == "Proceso":
                            tel_tec = next((p['telefono'] for p in cargar("personal") if p['nombre'] == row['id_tecnico']), None)
                            if tel_tec:
                                msg = urllib.parse.quote(f"Hola {row['id_tecnico']}, tienes una nueva orden: {row['descripcion']} en la máquina {row['id_maquina']}.")
                                wa_url = f"https://wa.me/{tel_tec}?text={msg}"
                                c2.link_button("📲 Notificar", wa_url)
