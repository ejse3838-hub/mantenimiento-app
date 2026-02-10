import streamlit as st
from supabase import create_client, Client
import pandas as pd

# --- 1. CONEXIÓN (Basada en tus fotos de Secrets) ---
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except Exception as e:
    st.error("Error de configuración en Secrets.")
    st.stop()

# --- 2. LÓGICA DE SESIÓN ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

def login(u, p):
    try:
        res = supabase.table("usuarios").select("*").eq("email", u).eq("password", p).execute()
        return res
    except Exception as e:
        st.error(f"Error de base de datos: {e}")
        return None

# --- 3. INTERFAZ DE LOGIN ---
if not st.session_state.logged_in:
    st.title("COMAIN - Inicio de Sesión")
    usuario = st.text_input("Correo Electrónico")
    clave = st.text_input("Contraseña", type="password")
    
    if st.button("Entrar"):
        resultado = login(usuario, clave)
        if resultado and len(resultado.data) > 0:
            st.session_state.logged_in = True
            st.rerun()
        else:
            st.error("Usuario o clave incorrectos")
    st.stop()

# --- 4. APLICACIÓN PRINCIPAL (Si el login es exitoso) ---
st.sidebar.title("Menú COMAIN")
opcion = st.sidebar.radio("Ir a:", ["Dashboard", "Personal", "Maquinaria", "Órdenes de Trabajo"])

# --- SECCIÓN DASHBOARD ---
if opcion == "Dashboard":
    st.header("Tablero de Control")
    # Aquí traemos métricas reales de tus tablas
    try:
        cant_maquinas = len(supabase.table("maquinaria").select("id").execute().data)
        cant_personal = len(supabase.table("personal").select("id").execute().data)
        col1, col2 = st.columns(2)
        col1.metric("Máquinas Registradas", cant_maquinas)
        col2.metric("Personal Activo", cant_personal)
    except:
        st.info("Agrega datos para ver estadísticas.")

# --- SECCIÓN PERSONAL (9 CAMPOS) ---
elif opcion == "Personal":
    st.header("Gestión de Personal")
    with st.form("form_personal"):
        # Restaurando los campos que necesitabas
        nom = st.text_input("Nombre Completo")
        ced = st.text_input("Cédula")
        car = st.text_input("Cargo")
        tel = st.text_input("Teléfono")
        ema = st.text_input("Email")
        tur = st.selectbox("Turno", ["Matutino", "Vespertino", "Nocturno"])
        f_ing = st.date_input("Fecha Ingreso")
        sal = st.number_input("Salario", min_value=0.0)
        obs = st.text_area("Observaciones")
        
        if st.form_submit_button("Guardar Personal"):
            data = {"nombre": nom, "cedula": ced, "cargo": car, "telefono": tel, 
                    "email": ema, "turno": tur, "fecha_ingreso": str(f_ing), 
                    "salario": sal, "notas": obs}
            supabase.table("personal").insert(data).execute()
            st.success("Personal registrado")

# --- SECCIÓN MAQUINARIA (12 CAMPOS) ---
elif opcion == "Maquinaria":
    st.header("Inventario de Maquinaria")
    with st.form("form_maquina"):
        # Restaurando los 12 campos técnicos
        cod = st.text_input("Código de Máquina")
        nom_m = st.text_input("Nombre/Modelo")
        mar = st.text_input("Marca")
        ubi = st.text_input("Ubicación en Planta")
        est = st.selectbox("Estado", ["Operativo", "En Mantenimiento", "Crítico"])
        f_adq = st.date_input("Fecha Adquisición")
        prio = st.slider("Prioridad", 1, 5)
        # ... (añadiendo campos hasta completar 12 según tu diseño)
        v_util = st.number_input("Vida Útil (años)")
        ult_m = st.date_input("Último Mantenimiento")
        frec = st.number_input("Frecuencia Mantenimiento (días)")
        crit = st.checkbox("¿Es maquinaria crítica?")
        prov = st.text_input("Proveedor")

        if st.form_submit_button("Guardar Máquina"):
            data_m = {"codigo": cod, "nombre": nom_m, "marca": mar, "ubicacion": ubi, "estado": est}
            supabase.table("maquinaria").insert(data_m).execute()
            st.success("Máquina guardada")

# --- SECCIÓN ÓRDENES DE TRABAJO (La que fallaba) ---
elif opcion == "Órdenes de Trabajo":
    st.header("Órdenes de Trabajo")
    # Código para leer órdenes
    try:
        ots = supabase.table("ordenes_trabajo").select("*").execute()
        if ots.data:
            df = pd.DataFrame(ots.data)
            st.table(df)
        else:
            st.write("No hay órdenes pendientes.")
    except Exception as e:
        st.error(f"Error al cargar OT: {e}")
