import streamlit as st
import pandas as pd
from supabase import create_client, Client

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

    # --- 1. INICIO (DASHBOARD) ---
    if menu == "🏠 Inicio":
        st.title("📊 Panel de Control CORMAIN")
        o_data = cargar("ordenes")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("En Proceso", len([o for o in o_data if o['estado'] == 'Proceso']))
        col2.metric("Realizadas", len([o for o in o_data if o['estado'] == 'Realizada']))
        col3.metric("Revisadas", len([o for o in o_data if o['estado'] == 'Revisada']))
        col4.metric("Finalizadas", len([o for o in o_data if o['estado'] == 'Finalizada']))

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

    # --- 4. ÓRDENES DE TRABAJO (FLUJO DINÁMICO) ---
    elif menu == "📑 Órdenes de Trabajo":
        st.header("Gestión de Órdenes de Producción")
        
        # Formulario de creación
        with st.expander("➕ Crear Nueva Orden"):
            maqs = [m['nombre_maquina'] for m in cargar("maquinas")]
            pers = [p['nombre'] for p in cargar("personal")]
            desc = st.text_area("Descripción")
            m_s = st.selectbox("Máquina", maqs)
            t_s = st.selectbox("Técnico", pers)
            if st.button("Lanzar Orden"):
                supabase.table("ordenes").insert({"descripcion": desc, "id_maquina": m_s, "id_tecnico": t_s, "estado": "Proceso"}).execute()
                st.rerun()

        st.divider()
        
        # Tablero de Control de Estados
        o_data = cargar("ordenes")
        if o_data:
            df = pd.DataFrame(o_data)
            
            # Definimos los pasos del flujo
            pasos = {
                "Proceso": "Realizada",
                "Realizada": "Revisada",
                "Revisada": "Finalizada"
            }
            
            for estado_actual in ["Proceso", "Realizada", "Revisada", "Finalizada"]:
                st.subheader(f"📍 Estado: {estado_actual}")
                filas = df[df['estado'] == estado_actual]
                
                if filas.empty:
                    st.info(f"No hay órdenes en {estado_actual}")
                else:
                    for _, row in filas.iterrows():
                        with st.container(border=True):
                            col_t, col_b = st.columns([4, 1])
                            col_t.write(f"**ID {row['id']}**: {row['descripcion']} | 🏗️ {row['id_maquina']} | 👤 {row['id_tecnico']}")
                            
                            # Botón para avanzar de estado
                            if estado_actual in pasos:
                                if col_b.button(f"➡️ Mover a {pasos[estado_actual]}", key=f"btn_{row['id']}"):
                                    supabase.table("ordenes").update({"estado": pasos[estado_actual]}).eq("id", row['id']).execute()
                                    st.rerun()
                            else:
                                col_b.write("✅ Completada")

    if st.sidebar.button("Cerrar Sesión"):
        st.session_state.auth = False
        st.rerun()
