import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime
import plotly.express as px

# --- 1. CONEXIÓN SEGURA ---
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except:
    st.error("Error de conexión. Revisa tus Secrets.")
    st.stop()

def cargar(tabla):
    try:
        res = supabase.table(tabla).select("*").eq("creado_por", st.session_state.user).execute()
        return res.data if res.data else []
    except: return []

# --- 2. CONFIGURACIÓN ---
st.set_page_config(page_title="CORMAIN CMMS PRO", layout="wide")
if 'auth' not in st.session_state: st.session_state.auth = False

# --- 3. LOGIN ---
if not st.session_state.auth:
    st.title("🛠️ COMAIN - Inicio de Sesión")
    u = st.text_input("Usuario")
    p = st.text_input("Clave", type="password")
    if st.button("Entrar"):
        res = supabase.table("usuarios").select("*").eq("email", u).eq("password", p).execute()
        if res.data:
            st.session_state.auth = True
            st.session_state.user = res.data[0]['email']
            st.rerun()
        else: st.error("Acceso incorrecto")
    st.stop()

# --- 4. MENÚ ---
st.sidebar.title(f"👤 {st.session_state.user}")
menu = st.sidebar.radio("Menú", ["🏠 Inicio", "👥 Personal", "⚙️ Maquinaria", "📑 Órdenes de Trabajo"])

# --- 5. PÁGINA: INICIO (GRÁFICOS DE PASTEL) ---
if menu == "🏠 Inicio":
    st.title("📊 Panel de Control")
    df_o = pd.DataFrame(cargar("ordenes"))
    if not df_o.empty:
        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(px.pie(df_o, names='estado', title="Estado de Órdenes", hole=0.4), use_container_width=True)
        with col2:
            # Si no tienes 'prioridad', intenta con 'tipo_tarea'
            st.plotly_chart(px.pie(df_o, names='tipo_tarea', title="Tipos de Tarea", hole=0.4), use_container_width=True)
    else: st.info("Ingresa datos para ver estadísticas.")

# --- 6. PÁGINA: PERSONAL (TUS 9 CAMPOS) ---
elif menu == "👥 Personal":
    st.header("Gestión de Personal")
    with st.form("f_p", clear_on_submit=True):
        c1, c2 = st.columns(2)
        n, a = c1.text_input("Nombre"), c2.text_input("Apellido")
        cod, mail = c1.text_input("Código de Empleado"), c2.text_input("Email")
        cargo, esp = c1.text_input("Cargo"), c2.text_input("Especialidad (Obligatorio)")
        clas = c1.text_input("Clasificación 1")
        dir_p = c2.text_input("Dirección")
        firma = st.text_input("Firma/Responsable")

        if st.form_submit_button("Guardar Personal"):
            try:
                supabase.table("personal").insert({
                    "nombre": n, "apellido": a, "cargo": cargo, "especialidad": esp,
                    "codigo_empleado": cod, "email": mail, "clasificacion_1": clas,
                    "direccion": dir_p, "firma": firma, "creado_por": st.session_state.user
                }).execute()
                st.success("Guardado con éxito")
                st.rerun()
            except Exception as e: st.error(f"Error: {e}")
    st.dataframe(pd.DataFrame(cargar("personal")), use_container_width=True)

# --- 7. PÁGINA: MAQUINARIA (TUS 10 CAMPOS) ---
elif menu == "⚙️ Maquinaria":
    st.header("Ficha Técnica de Maquinaria")
    with st.form("f_m", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        nm = c1.text_input("Nombre de la Máquina")
        cod_m = c2.text_input("Código (Obligatorio)")
        ubi = c3.text_input("Ubicación")
        est = c1.selectbox("Estado", ["Operativa", "Mantenimiento", "Falla"])
        fab, mod = c2.text_input("Fabricante"), c3.text_input("Modelo")
        hrs = c1.number_input("Horas de uso", 0)
        f_compra = c2.date_input("Fecha de Compra")
        ap1, ap2 = c3.text_input("Apartado 1"), c1.text_input("Apartado 2")
        
        if st.form_submit_button("Registrar Máquina"):
            try:
                supabase.table("maquinas").insert({
                    "nombre_maquina": nm, "codigo": cod_m, "ubicacion": ubi, "estado": est,
                    "fabricante": fab, "modelo": mod, "horas_uso": hrs, 
                    "fecha_compra": str(f_compra), "apartado_1": ap1, "apartado_2": ap2,
                    "creado_por": st.session_state.user
                }).execute()
                st.success("Máquina registrada")
                st.rerun()
            except Exception as e: st.error(f"Error: {e}")
    st.dataframe(pd.DataFrame(cargar("maquinas")), use_container_width=True)

# --- 8. PÁGINA: ÓRDENES DE TRABAJO ---
elif menu == "📑 Órdenes de Trabajo":
    st.header("Gestión de OP")
    mqs_data = cargar("maquinas")
    mqs = [m['nombre_maquina'] for m in mqs_data]
    if not mqs: st.warning("Registra una máquina primero"); st.stop()
    
    with st.form("f_op"):
        desc = st.text_area("Descripción")
        c1, c2, c3 = st.columns(3)
        mq = c1.selectbox("Máquina", mqs)
        tipo = c2.selectbox("Tipo", ["Preventiva", "Correctiva"])
        prio = c3.selectbox("Prioridad", ["ALTA", "NORMAL"])
        dur = c1.text_input("Duración Estimada")
        paro = c2.selectbox("Requiere Paro", ["Sí", "No"])
        costo = c3.number_input("Costo Estimado", 0.0)
        firma_j = st.text_input("Firma del Jefe")

        if st.form_submit_button("Lanzar Orden"):
            try:
                supabase.table("ordenes").insert({
                    "descripcion": desc, "id_maquina": mq, "prioridad": prio,
                    "tipo_tarea": tipo, "duracion_estimada": dur, "requiere_paro": paro,
                    "costo": costo, "firma_jefe": firma_j, "estado": "Proceso", 
                    "creado_por": st.session_state.user
                }).execute()
                st.success("Orden creada")
                st.rerun()
            except Exception as e: st.error(f"Error: {e}")
    st.dataframe(pd.DataFrame(cargar("ordenes")), use_container_width=True)
