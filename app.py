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
def cargar(tabla):
    try:
        # Aquí sí usamos .execute() porque es una consulta a la base de datos
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
            # Aquí también usamos .execute() correctamente
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

    # --- PÁGINAS ---
    if st.session_state.menu == "🏠 Inicio":
        st.title("📊 Panel de Control")
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
                fig1 = px.pie(df, names='estado', hole=0.4, title="Estado de Órdenes")
                colg1.plotly_chart(fig1, use_container_width=True)
                fig2 = px.pie(df, names='id_tecnico', hole=0.4, title="Carga por Técnico")
                colg2.plotly_chart(fig2, use_container_width=True)
        else: st.info("No hay datos para mostrar.")

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
        # CARGA SEGURA
        p_data = cargar("personal")
        if p_data: st.table(pd.DataFrame(p_data))

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
        # CARGA SEGURA
        m_data = cargar("maquinas")
        if m_data: st.table(pd.DataFrame(m_data))

    elif st.session_state.menu == "📑 Órdenes de Trabajo":
        st.header("Órdenes de Producción")
        
        # Obtenemos los datos primero
        lista_maquinas = cargar("maquinas")
        lista_personal = cargar("personal")

        # Filtramos los nombres (ESTO YA NO TIENE .execute())
        nombres_m = [m['nombre_maquina'] for m in lista_maquinas] if lista_maquinas else ["Registrar máquinas primero"]
        nombres_p = [p['nombre'] for p in lista_personal] if lista_personal else ["Registrar personal primero"]

        with st.expander("➕ Crear Nueva"):
            with st.form("f_o"):
                desc = st.text_area("Descripción")
                maq = st.selectbox("Máquina", nombres_m)
                tec = st.selectbox("Técnico", nombres_p)
                
                if st.form_submit_button("Lanzar"):
                    if "Registrar" in nombres_m[0] or "Registrar" in nombres_p[0]:
                        st.error("Faltan datos en Maquinaria o Personal")
                    else:
                        supabase.table("ordenes").insert({
                            "descripcion": desc, "id_maquina": maq, "id_tecnico": tec,
                            "estado": "Proceso", "creado_por": st.session_state.user
                        }).execute()
                        st.rerun()
        
        st.divider()
        todas_las_ordenes = cargar("ordenes")
        if todas_las_ordenes:
            df_o = pd.DataFrame(todas_las_ordenes)
            pasos = {"Proceso": "Realizada", "Realizada": "Revisada", "Revisada": "Finalizada"}
            for est in ["Proceso", "Realizada", "Revisada", "Finalizada"]:
                st.subheader(f"📍 {est}")
                filas = df_o[df_o['estado'] == est]
                for _, row in filas.iterrows():
                    with st.container(border=True):
                        c1, c2, c3 = st.columns([3, 1, 1])
                        c1.write(f"**{row['id_maquina']}**: {row['descripcion']} ({row['id_tecnico']})")
                        
                        if est in pasos:
                            if c2.button(f"➡️ {pasos[est]}", key=f"av_{row['id']}"):
                                supabase.table("ordenes").update({"estado": pasos[est]}).eq("id", row['id']).execute()
                                st.rerun()
                        
                        if est in ["Proceso", "Finalizada"]:
                            if c3.button("🗑️ Eliminar", key=f"del_{row['id']}"):
                                supabase.table("ordenes").delete().eq("id", row['id']).execute()
                                st.rerun()
                        
                        if est == "Proceso":
                            # Buscamos el teléfono de forma segura en la lista de personal que ya cargamos
                            tel_t = next((p['telefono'] for p in lista_personal if p['nombre'] == row['id_tecnico']), None)
                            if tel_t:
                                msg = urllib.parse.quote(f"Orden: {row['descripcion']} en {row['id_maquina']}")
                                c2.link_button("📲 Notificar", f"https://wa.me/{tel_t}?text={msg}")
