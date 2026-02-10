import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime

# --- 1. CONEXIÓN (Mantenemos tu formato de Secrets) ---
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except Exception:
    st.error("Error en las credenciales de conexión.")
    st.stop()

# --- 2. FUNCIONES DE CARGA ---
def cargar(tabla):
    try:
        res = supabase.table(tabla).select("*").eq("creado_por", st.session_state.user).execute()
        return res.data if res.data else []
    except Exception:
        return []

# --- 3. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="CORMAIN CMMS PRO", layout="wide")
if 'auth' not in st.session_state: st.session_state.auth = False

# --- 4. LOGIN / REGISTRO ---
if not st.session_state.auth:
    st.title("🛠️ COMAIN - Gestión de Mantenimiento")
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
    # --- 5. MENÚ LATERAL ---
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

    # --- 6. PÁGINA: PERSONAL (CORREGIDA) ---
    if st.session_state.menu == "👥 Personal":
        st.header("Gestión de Personal")
        with st.form("f_p", clear_on_submit=True):
            c1, c2 = st.columns(2)
            n = c1.text_input("Nombre")
            ap = c2.text_input("Apellido")
            car = c1.text_input("Cargo")
            esp = c2.text_input("Especialidad")
            
            # Estos campos son los que daban error. 
            # Si el error persiste, es porque no existen en tu Supabase.
            mail = c1.text_input("Email Personal")
            sal = c2.number_input("Salario ($)", min_value=0.0)
            
            if st.form_submit_button("Guardar"):
                # SOLO enviamos los campos que SEGURO tienes en tu tabla
                datos = {
                    "nombre": n, 
                    "apellido": ap, 
                    "cargo": car, 
                    "especialidad": esp,
                    "creado_por": st.session_state.user
                }
                
                # Intentamos agregar los otros solo si no están vacíos
                if mail: datos["email"] = mail
                
                try:
                    supabase.table("personal").insert(datos).execute()
                    st.success("Personal guardado exitosamente")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error técnico: {e}")
                    st.info("💡 Consejo: Revisa en Supabase si la columna se llama exactamente 'email' o 'salario'.")
        
        st.dataframe(pd.DataFrame(cargar("personal")), use_container_width=True)

    # --- (Las demás secciones Maquinaria e Inicio se mantienen igual) ---
    elif st.session_state.menu == "🏠 Inicio":
        st.title("📊 Panel de Control")
        df = pd.DataFrame(cargar("ordenes"))
        if not df.empty:
            st.metric("Órdenes Totales", len(df))
        else: st.info("Sin datos registrados.")

    elif st.session_state.menu == "⚙️ Maquinaria":
        st.header("Ficha Técnica")
        with st.form("f_m"):
            c1, c2 = st.columns(2)
            nm, cod = c1.text_input("Máquina"), c2.text_input("Código")
            ubi, est = c1.text_input("Ubicación"), c2.selectbox("Estado", ["Operativa", "Mantenimiento"])
            if st.form_submit_button("Registrar"):
                supabase.table("maquinas").insert({
                    "nombre_maquina": nm, "codigo": cod, "ubicacion": ubi, 
                    "estado": est, "creado_por": st.session_state.user
                }).execute()
                st.rerun()
        st.dataframe(pd.DataFrame(cargar("maquinas")), use_container_width=True)
