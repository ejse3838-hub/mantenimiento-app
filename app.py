import streamlit as st
import pandas as pd
from supabase import create_client, Client

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
        res = supabase.table(tabla).select("*").eq("creado_por", st.session_state.user).execute()
        return res.data if res.data else []
    except: return []

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
        new_u = st.text_input("Nuevo Email")
        new_p = st.text_input("Nueva Clave", type="password")
        if st.button("Crear Cuenta"):
            try:
                supabase.table("usuarios").insert({"email": new_u, "password": new_p}).execute()
                st.success("¡Cuenta creada!")
            except: st.error("Error al crear cuenta.")

else:
    # --- MENÚ LATERAL (BOTONES) ---
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

    # --- 1. INICIO (DASHBOARD) ---
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

    # --- 2. PERSONAL (NOMBRES, APELLIDOS, PUESTO) ---
    elif st.session_state.menu == "👥 Personal":
        st.header("Gestión de Personal")
        with st.form("f_pers"):
            c1, c2 = st.columns(2)
            nom = c1.text_input("Nombres")
            ape = c2.text_input("Apellidos")
            car = c1.text_input("Cargo")
            pue = c2.text_input("Puesto")
            if st.form_submit_button("Guardar"):
                supabase.table("personal").insert({
                    "nombre": f"{nom} {ape}", 
                    "cargo": car, 
                    "especialidad": pue, 
                    "creado_por": st.session_state.user
                }).execute()
                st.rerun()
        
        per_list = cargar("personal")
        if per_list:
            st.table(pd.DataFrame(per_list)[["nombre", "cargo", "especialidad"]])

    # --- 3. MAQUINARIA (NOMBRE + CÓDIGO) ---
    elif st.session_state.menu == "⚙️ Maquinaria":
        st.header("Gestión de Maquinas")
        with st.form("f_maq"):
            c1, c2 = st.columns(2)
            n_m = c1.text_input("Nombre Máquina")
            cod_m = c2.text_input("Código de Máquina")
            est = st.selectbox("Estado", ["Operativa", "Falla"])
            if st.form_submit_button("Registrar"):
                supabase.table("maquinas").insert({
                    "nombre_maquina": n_m, 
                    "codigo": cod_m,
                    "estado": est, 
                    "creado_por": st.session_state.user
                }).execute()
                st.rerun()
        
        maq_list = cargar("maquinas")
        if maq_list:
            st.table(pd.DataFrame(maq_list)[["nombre_maquina", "codigo", "estado"]])

    # --- 4. ÓRDENES DE TRABAJO (PERIODICIDAD) ---
    elif st.session_state.menu == "📑 Órdenes de Trabajo":
        st.header("Órdenes de Producción")
        
        with st.expander("➕ Crear Nueva"):
            maqs_data = cargar("maquinas")
            # Combinamos Nombre y Código para el selector
            maqs_opts = [f"{m['nombre_maquina']} ({m['codigo']})" for m in maqs_data]
            pers_data = cargar("personal")
            pers_opts = [p['nombre'] for p in pers_data]
            
            with st.form("f_orden"):
                desc = st.text_area("Descripción")
                c1, c2 = st.columns(2)
                maq = c1.selectbox("Máquina", maqs_opts)
                tec = c2.selectbox("Técnico", pers_opts)
                frec = st.selectbox("Periodicidad", ["Correctiva", "Diaria", "Semanal", "Mensual", "Anual"])
                
                if st.form_submit_button("Lanzar"):
                    supabase.table("ordenes").insert({
                        "descripcion": desc, 
                        "id_maquina": maq, 
                        "id_tecnico": tec,
                        "frecuencia": frec,
                        "estado": "Proceso", 
                        "creado_por": st.session_state.user
                    }).execute()
                    st.rerun()

        st.divider()
        df_o = pd.DataFrame(cargar("ordenes"))
        if not df_o.empty:
            pasos = {"Proceso": "Realizada", "Realizada": "Revisada", "Revisada": "Finalizada"}
            for est in ["Proceso", "Realizada", "Revisada", "Finalizada"]:
                st.subheader(f"📍 {est}")
                items = df_o[df_o['estado'] == est]
                for _, row in items.iterrows():
                    with st.container(border=True):
                        c1, c2, c3 = st.columns([3, 1, 1])
                        c1.write(f"**{row['id_maquina']}**: {row['descripcion']} ({row['id_tecnico']})")
                        c1.caption(f"⏱️ Periodicidad: {row.get('frecuencia', 'N/A')}")
                        
                        if est in pasos:
                            if c2.button(f"➡️ {pasos[est]}", key=f"av_{row['id']}"):
                                supabase.table("ordenes").update({"estado": pasos[est]}).eq("id", row['id']).execute()
                                st.rerun()
                        
                        if est in ["Proceso", "Finalizada"]:
                            if c3.button("🗑️ Eliminar", key=f"del_{row['id']}"):
                                supabase.table("ordenes").delete().eq("id", row['id']).execute()
                                st.rerun()
