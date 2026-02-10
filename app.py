import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime
import plotly.express as px

# --- 1. CONEXIÓN ---
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except:
    st.error("Error de conexión. Verifica tus Secrets en Streamlit.")
    st.stop()

# --- 2. FUNCIONES DE CARGA ---
def cargar(tabla):
    try:
        res = supabase.table(tabla).select("*").eq("creado_por", st.session_state.user).execute()
        return res.data if res.data else []
    except:
        return []

# --- 3. CONFIGURACIÓN ---
st.set_page_config(page_title="CORMAIN CMMS PRO", layout="wide")
if 'auth' not in st.session_state: st.session_state.auth = False

# --- 4. LOGIN ---
if not st.session_state.auth:
    st.title("🛠️ COMAIN - Gestión de Mantenimiento")
    tab1, tab2 = st.tabs(["🔑 Iniciar Sesión", "📝 Registrarse"])
    with tab1:
        u = st.text_input("Usuario (Email)")
        p = st.text_input("Clave", type="password")
        if st.button("Entrar"):
            res = supabase.table("usuarios").select("*").eq("email", u).eq("password", p).execute()
            if res.data:
                st.session_state.auth = True
                st.session_state.user = res.data[0]['email']
                st.rerun()
            else: st.error("Acceso denegado")
    with tab2:
        nu, np = st.text_input("Nuevo Email"), st.text_input("Nueva Clave", type="password")
        if st.button("Crear Cuenta"):
            supabase.table("usuarios").insert({"email": nu, "password": np, "creado_por": nu}).execute()
            st.success("¡Cuenta creada!")
    st.stop()

# --- 5. NAVEGACIÓN ---
st.sidebar.title(f"👤 {st.session_state.user}")
menu = st.sidebar.radio("Menú", ["🏠 Inicio", "👥 Personal", "⚙️ Maquinaria", "📑 Órdenes de Trabajo"])

# --- 6. PÁGINA: INICIO (DASHBOARD) ---
if menu == "🏠 Inicio":
    st.title("📊 Panel de Control")
    df_o = pd.DataFrame(cargar("ordenes"))
    if not df_o.empty:
        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(px.pie(df_o, names='estado', title="Estado de Órdenes", hole=0.4), use_container_width=True)
        with col2:
            st.plotly_chart(px.pie(df_o, names='tipo_tarea', title="Tipos de Mantenimiento", hole=0.4), use_container_width=True)
        st.metric("Total de Órdenes", len(df_o))
    else: st.info("No hay datos para mostrar gráficos.")

# --- 7. PÁGINA: PERSONAL (TUS COLUMNAS EXACTAS) ---
elif menu == "👥 Personal":
    st.header("Gestión de Personal")
    with st.form("f_p", clear_on_submit=True):
        c1, c2 = st.columns(2)
        n = c1.text_input("Nombre")
        a = c2.text_input("Apellido")
        car = c1.text_input("Cargo")
        esp = c2.text_input("Especialidad")
        cod_e = c1.text_input("Código Empleado")
        mail = c2.text_input("Email")
        clasi1 = c1.text_input("Clasificación 1")
        direc = c2.text_input("Dirección")
        f_path = st.text_input("Firma (Path/Nombre)")
        
        if st.form_submit_button("Guardar Personal"):
            data_p = {
                "nombre": n, "apellido": a, "cargo": car, "especialidad": esp,
                "codigo_empleado": cod_e, "email": mail, "clasificacion1": clasi1,
                "direccion": direc, "firma_path": f_path, "creado_por": st.session_state.user
            }
            try:
                supabase.table("personal").insert(data_p).execute()
                st.success("Personal guardado")
                st.rerun()
            except Exception as e: st.error(f"Error: {e}")
    st.dataframe(pd.DataFrame(cargar("personal")), use_container_width=True)

# --- 8. PÁGINA: MAQUINARIA (TUS COLUMNAS EXACTAS) ---
elif menu == "⚙️ Maquinaria":
    st.header("Ficha Técnica de Maquinaria")
    with st.form("f_m", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        nm = c1.text_input("Nombre de la Máquina")
        cod = c2.text_input("Código")
        ubi = c3.text_input("Ubicación")
        est = c1.selectbox("Estado", ["Operativa", "Mantenimiento", "Falla"])
        ser = c2.text_input("Serial")
        fab = c3.text_input("Fabricante")
        mod = c1.text_input("Modelo")
        hrs = c2.number_input("Horas de uso", 0)
        f_compra = c3.date_input("Fecha de Compra")
        apa1 = c1.text_input("Apartado 1")
        apa2 = c2.text_input("Apartado 2")
        
        if st.form_submit_button("Registrar Máquina"):
            data_m = {
                "nombre_maquina": nm, "codigo": cod, "ubicacion": ubi, "estado": est,
                "serial": ser, "fabricante": fab, "modelo": mod, "horas_uso": hrs,
                "fecha_compra": str(f_compra), "apartado1": apa1, "apartado2": apa2,
                "creado_por": st.session_state.user
            }
            try:
                supabase.table("maquinas").insert(data_m).execute()
                st.success("Máquina registrada")
                st.rerun()
            except Exception as e: st.error(f"Error: {e}")
    st.dataframe(pd.DataFrame(cargar("maquinas")), use_container_width=True)

# --- 9. PÁGINA: ÓRDENES DE TRABAJO (TUS COLUMNAS EXACTAS) ---
elif menu == "📑 Órdenes de Trabajo":
    st.header("Gestión de Órdenes")
    mqs = [m['nombre_maquina'] for m in cargar("maquinas")]
    pers = [f"{p['nombre']} {p['apellido']}" for p in cargar("personal")]
    
    with st.expander("➕ Lanzar Nueva OP"):
        with st.form("f_op"):
            desc = st.text_area("Descripción")
            c1, c2, c3 = st.columns(3)
            mq = c1.selectbox("ID Máquina", mqs) if mqs else c1.text_input("ID Máquina")
            tc = c2.selectbox("ID Técnico", pers) if pers else c2.text_input("ID Técnico")
            est_op = c3.selectbox("Estado", ["Proceso", "Finalizada"])
            tipo = c1.selectbox("Tipo Tarea", ["Correctiva", "Preventiva"])
            freq = c2.text_input("Frecuencia")
            dur = c3.text_input("Duración Estimada")
            paro = c1.selectbox("Requiere Paro", ["Sí", "No"])
            herr = c2.text_input("Herramientas")
            prio = c3.selectbox("Prioridad", ["ALTA", "NORMAL", "BAJA"])
            insu = c1.text_input("Insumos")
            cost = c2.number_input("Costo", 0.0)
            f_jefe = c3.text_input("Firma Jefe")
            
            if st.form_submit_button("Lanzar"):
                data_op = {
                    "descripcion": desc, "id_maquina": mq, "id_tecnico": tc, "estado": est_op,
                    "tipo_tarea": tipo, "frecuencia": freq, "duracion_estimada": dur,
                    "requiere_paro": paro, "herramientas": herr, "prioridad": prio,
                    "insumos": insu, "costo": cost, "firma_jefe": f_jefe,
                    "creado_por": st.session_state.user
                }
                try:
                    supabase.table("ordenes").insert(data_op).execute()
                    st.success("Orden enviada")
                    st.rerun()
                except Exception as e: st.error(f"Error: {e}")
    st.dataframe(pd.DataFrame(cargar("ordenes")), use_container_width=True)
