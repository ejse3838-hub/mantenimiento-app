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

# --- FUNCIÓN DE CARGA SEGURA POR USUARIO ---
def cargar(tabla):
    try:
        # Solo trae datos donde creado_por coincida con el usuario logueado
        res = supabase.table(tabla).select("*").eq("creado_por", st.session_state.user).execute()
        return res.data if res.data else []
    except Exception as e:
        return []

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="CORMAIN CMMS PRO", layout="wide")

# --- SISTEMA DE LOGIN ---
if 'auth' not in st.session_state: st.session_state.auth = False

if not st.session_state.auth:
    tab1, tab2 = st.tabs(["🔑 Iniciar Sesión", "📝 Registrarse"])
    with tab1:
        u = st.text_input("Email/Usuario", value="ejse3838@hotmail.com")
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
                st.success("¡Cuenta creada! Ya puedes entrar.")
            except: st.error("Error al crear cuenta.")

else:
    # --- MENÚ LATERAL FIJO (Navegación Didáctica) ---
    st.sidebar.title(f"👤 {st.session_state.user}")
    if "menu" not in st.session_state: st.session_state.menu = "🏠 Inicio"

    st.sidebar.subheader("Menú Principal")
    # Botones fijos para evitar el selectbox desplegable
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
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("En Proceso", len(df[df['estado'] == 'Proceso']))
            col2.metric("Realizadas", len(df[df['estado'] == 'Realizada']))
            col3.metric("Revisadas", len(df[df['estado'] == 'Revisada']))
            col4.metric("Finalizadas", len(df[df['estado'] == 'Finalizada']))
            
            if GRAFICOS_LISTOS:
                st.divider()
                c_g1, c_g2 = st.columns(2)
                fig1 = px.pie(df, names='estado', hole=0.4, title="Estado de Órdenes")
                c_g1.plotly_chart(fig1, use_container_width=True)
                fig2 = px.pie(df, names='id_tecnico', hole=0.4, title="Tareas por Técnico")
                c_g2.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("No hay datos registrados aún.")

    # 2. PERSONAL (NOTIFICACIONES)
    elif st.session_state.menu == "👥 Personal":
        st.header("Gestión de Personal y Notificaciones")
        with st.form("f_rrhh"):
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
        st.subheader("Personal Registrado")
        p_data = cargar("personal")
        if p_data: st.table(pd.DataFrame(p_data)[["nombre", "cargo", "especialidad", "telefono"]])

    # 3. MAQUINARIA
    elif st.session_state.menu == "⚙️ Maquinaria":
        st.header("Gestión de Activos")
        with st.form("f_maq"):
            n_m = st.text_input("Nombre Máquina")
            est = st.selectbox("Estado", ["Operativa", "Falla"])
            if st.form_submit_button("Registrar"):
                supabase.table("maquinas").insert({
                    "nombre_maquina": n_m, "estado": est, "creado_por": st.session_state.user
                }).execute()
                st.rerun()
        st.table(pd.DataFrame(cargar("maquinas")))

    # 4. ÓRDENES DE TRABAJO (LIMPIEZA Y FLUJO)
    elif st.session_state.menu == "📑 Órdenes de Trabajo":
        st.header("Gestión de Órdenes de Producción")
        with st.expander("➕ Crear Nueva Orden"):
            maqs = [m['nombre_maquina'] for m in cargar("maquinas")]
            pers_list = cargar("personal")
            with st.form("f_ot"):
                desc = st.text_area("Descripción")
                maq = st.selectbox("Máquina", maqs)
                tec = st.selectbox("Técnico", [p['nombre'] for p in pers_list])
                if st.form_submit_button("Lanzar"):
                    supabase.table("ordenes").insert({
                        "descripcion": desc, "id_maquina": maq, "id_tecnico": tec,
                        "estado": "Proceso", "creado_por": st.session_state.user
                    }).execute()
                    st.rerun()

        st.divider()
        o_list = cargar("ordenes")
        if o_list:
            df_o = pd.DataFrame(o_list)
            pasos = {"Proceso": "Realizada", "Realizada": "Revisada", "Revisada": "Finalizada"}
            for est in ["Proceso", "Realizada", "Revisada", "Finalizada"]:
                st.subheader(f"📍 {est}")
                filas = df_o[df_o['estado'] == est]
                for _, row in filas.iterrows():
                    with st.container(border=True):
                        c1, c2, c3 = st.columns([3, 1, 1])
                        c1.write(f"**{row['id_maquina']}**: {row['descripcion']} ({row['id_tecnico']})")
                        
                        # AVANZAR ESTADO
                        if est in pasos:
                            if c2.button(f"➡️ {pasos[est]}", key=f"av_{row['id']}"):
                                supabase.table("ordenes").update({"estado": pasos[est]}).eq("id", row['id']).execute()
                                st.rerun()
                        
                        # ELIMINAR (Solo en Proceso o Finalizada para limpieza)
                        if est in ["Proceso", "Finalizada"]:
                            if c3.button("🗑️ Eliminar", key=f"del_{row['id']}"):
                                supabase.table("ordenes").delete().eq("id", row['id']).execute()
                                st.rerun()

                        # NOTIFICAR (WhatsApp)
                        if est == "Proceso":
                            tel_tec = next((p['telefono'] for p in pers_list if p['nombre'] == row['id_tecnico']), None)
                            if tel_tec:
                                msg = urllib.parse.quote(f"Hola {row['id_tecnico']}, tienes una orden en {row['id_maquina']}: {row['descripcion']}")
                                c2.link_button("📲 Notificar", f"https://wa.me/{tel_tec}?text={msg}")
                                
