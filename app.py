import streamlit as st
import pandas as pd
from supabase import create_client, Client

# --- PROTECCIÓN PARA LOS GRÁFICOS (AUMENTO DE SEGURIDAD) ---
try:
    import plotly.express as px
    GRAFICOS_LISTOS = True
except ImportError:
    GRAFICOS_LISTOS = False

# --- CONEXIÓN ---
url = st.secrets["connections"]["supabase"]["SUPABASE_URL"]
key = st.secrets["connections"]["supabase"]["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

def cargar(tabla):
    try:
        res = supabase.table(tabla).select("*").execute()
        return res.data if res.data else []
    except: return []

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="CORMAIN CMMS PRO", layout="wide")

# --- SISTEMA DE LOGIN Y REGISTRO ---
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
                st.success("¡Cuenta creada! Ya puedes iniciar sesión.")
            except: st.error("El usuario ya existe.")

else:
    # --- MENÚ LATERAL ---
    menu = st.sidebar.selectbox("Navegación", ["🏠 Inicio", "👥 Personal", "⚙️ Maquinaria", "📑 Órdenes de Trabajo"])

    # --- 1. INICIO (DASHBOARD + KPI'S) ---
    if menu == "🏠 Inicio":
        st.title("📊 Panel de Control CORMAIN")
        o_data = cargar("ordenes")
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("En Proceso", len([o for o in o_data if o['estado'] == 'Proceso']))
        col2.metric("Realizadas", len([o for o in o_data if o['estado'] == 'Realizada']))
        col3.metric("Revisadas", len([o for o in o_data if o['estado'] == 'Revisada']))
        col4.metric("Finalizadas", len([o for o in o_data if o['estado'] == 'Finalizada']))

        st.divider()
        if o_data:
            if GRAFICOS_LISTOS:
                df = pd.DataFrame(o_data)
                col_graf1, col_graf2 = st.columns(2)
                with col_graf1:
                    st.subheader("Estado de Órdenes")
                    fig1 = px.pie(df, names='estado', hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
                    st.plotly_chart(fig1, use_container_width=True)
                with col_graf2:
                    st.subheader("Carga por Técnico")
                    # Manejo de error si id_tecnico está vacío
                    names_col = 'id_tecnico' if 'id_tecnico' in df.columns else 'estado'
                    fig2 = px.pie(df, names=names_col, hole=0.4)
                    st.plotly_chart(fig2, use_container_width=True)
            else:
                st.warning("⚠️ Los gráficos están listos, pero falta instalar 'plotly' en el archivo requirements.txt")

    # --- 2. PERSONAL ---
    elif menu == "👥 Personal":
        st.header("Gestión de Personal")
        with st.form("f_rrhh"):
            nom = st.text_input("Nombre (ID)")
            car = st.text_input("Cargo")
            esp = st.text_input("Especialidad")
            if st.form_submit_button("Guardar"):
                supabase.table("personal").insert({"nombre": nom, "cargo": car, "especialidad": esp}).execute()
                st.rerun()
        st.dataframe(pd.DataFrame(cargar("personal")), use_container_width=True)

    # --- 3. MAQUINARIA ---
    elif menu == "⚙️ Maquinaria":
        st.header("Gestión de Maquinaria")
        with st.form("f_maq"):
            n_m = st.text_input("Nombre Máquina")
            cod = st.text_input("Código")
            ubi = st.text_input("Ubicación")
            est = st.selectbox("Estado", ["Operativa", "Falla", "Mantenimiento"])
            if st.form_submit_button("Registrar"):
                supabase.table("maquinas").insert({"nombre_maquina": n_m, "codigo": cod, "ubicacion": ubi, "estado": est}).execute()
                st.rerun()
        st.dataframe(pd.DataFrame(cargar("maquinas")), use_container_width=True)

    # --- 4. ÓRDENES DE TRABAJO ---
    elif menu == "📑 Órdenes de Trabajo":
        st.header("Gestión de Órdenes de Producción")
        
        with st.expander("➕ Crear Nueva Orden"):
            maqs = [m['nombre_maquina'] for m in cargar("maquinas")]
            pers = [p['nombre'] for p in cargar("personal")]
            
            with st.form("f_crear_ot_emilio"):
                col_a, col_b = st.columns(2)
                desc = col_a.text_area("Descripción de la Tarea")
                m_s = col_a.selectbox("Seleccionar Máquina", maqs)
                t_s = col_b.selectbox("Asignar Técnico", pers)
                
                tipo_t = col_b.selectbox("Tipo de Tarea", ["Mecánica", "Eléctrica", "Lubricación", "Inspección"])
                dur = col_a.number_input("Duración Estimada (min)", value=30)
                frec = col_b.selectbox("Frecuencia", ["Correctiva", "Semanal", "Mensual"])
                paro = col_a.checkbox("¿Requiere paro de máquina?")
                herr = col_b.text_input("Herramientas/Insumos necesarios")
                
                if st.form_submit_button("Lanzar Orden"):
                    supabase.table("ordenes").insert({
                        "descripcion": desc, "id_maquina": m_s, "id_tecnico": t_s, 
                        "estado": "Proceso", "tipo_tarea": tipo_t, "frecuencia": frec,
                        "duracion_estimada": dur, "requiere_paro": paro, "herramientas": herr
                    }).execute()
                    st.rerun()

        st.divider()
        o_data = cargar("ordenes")
        if o_data:
            df = pd.DataFrame(o_data)
            pasos = {"Proceso": "Realizada", "Realizada": "Revisada", "Revisada": "Finalizada"}
            
            for estado_actual in ["Proceso", "Realizada", "Revisada", "Finalizada"]:
                st.subheader(f"📍 Estado: {estado_actual}")
                filas = df[df['estado'] == estado_actual]
                
                if filas.empty:
                    st.info(f"No hay órdenes en {estado_actual}")
                else:
                    for _, row in filas.iterrows():
                        with st.container(border=True):
                            col_txt, col_btn = st.columns([4, 1])
                            dur_txt = f" | ⏱️ {row.get('duracion_estimada', 0)} min"
                            col_txt.write(f"**ID {row['id']}**: {row['descripcion']} | 🏗️ {row['id_maquina']} | 👤 {row['id_tecnico']} {dur_txt}")
                            
                            if estado_actual in pasos:
                                if col_btn.button(f"➡️ {pasos[estado_actual]}", key=f"next_{row['id']}"):
                                    supabase.table("ordenes").update({"estado": pasos[estado_actual]}).eq("id", row['id']).execute()
                                    st.rerun()
                                if estado_actual == "Revisada":
                                    if col_btn.button(f"❌ Rechazar", key=f"rech_{row['id']}"):
                                        supabase.table("ordenes").update({"estado": "Proceso"}).eq("id", row['id']).execute()
                                        st.rerun()
                            else:
                                col_btn.write("✅ Completada")

    if st.sidebar.button("Cerrar Sesión"):
        st.session_state.auth = False
        st.rerun()
