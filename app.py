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
except Exception:
    st.error("Error de conexión. Verifica tus Secrets.")
    st.stop()

# --- 2. FUNCIONES DE CARGA ---
def cargar(tabla):
    try:
        res = supabase.table(tabla).select("*").eq("creado_por", st.session_state.user).execute()
        return res.data if res.data else []
    except Exception:
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

# --- 6. PÁGINA: INICIO (DASHBOARD CON PASTELES) ---
if menu == "🏠 Inicio":
    st.title("📊 Panel de Control")
    df_o = pd.DataFrame(cargar("ordenes"))
    
    if not df_o.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            fig_estado = px.pie(df_o, names='estado', title="Distribución por Estado", hole=0.4)
            st.plotly_chart(fig_estado, use_container_width=True)
            
        with col2:
            fig_tipo = px.pie(df_o, names='tipo_tarea', title="Tipos de Mantenimiento", hole=0.4)
            st.plotly_chart(fig_tipo, use_container_width=True)
            
        st.metric("Total de Órdenes", len(df_o))
    else:
        st.info("No hay datos suficientes para generar los gráficos.")

# --- 7. PÁGINA: PERSONAL (TUS COLUMNAS) ---
elif menu == "👥 Personal":
    st.header("Gestión de Personal")
    with st.form("f_p", clear_on_submit=True):
        c1, c2 = st.columns(2)
        n = c1.text_input("Nombre")
        a = c2.text_input("Apellido")
        cod = c1.text_input("Código")
        mail = c2.text_input("Email")
        clasi = c1.text_input("Clasificación 1")
        dir_p = c2.text_input("Dirección")
        car = c1.text_input("Cargo")
        st.write("Firma: (Campo de texto para nombre de responsable)")
        firma = st.text_input("Firma de registro")
        
        if st.form_submit_button("Guardar Personal"):
            data = {
                "nombre": n, "apellido": a, "codigo": cod, "email": mail,
                "clasificacion_1": clasi, "direccion": dir_p, "cargo": car,
                "firma": firma, "creado_por": st.session_state.user
            }
            supabase.table("personal").insert(data).execute()
            st.rerun()
    st.dataframe(pd.DataFrame(cargar("personal")), use_container_width=True)

# --- 8. PÁGINA: MAQUINARIA (TUS COLUMNAS) ---
elif menu == "⚙️ Maquinaria":
    st.header("Ficha Técnica de Maquinaria")
    with st.form("f_m", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        nm = c1.text_input("Nombre de la Máquina")
        ubi = c2.text_input("Ubicación")
        est = c3.selectbox("Estado", ["Operativa", "Mantenimiento", "Falla"])
        fab = c1.text_input("Fabricante")
        mod = c2.text_input("Modelo")
        hrs = c3.number_input("Horas de uso", 0)
        f_compra = c1.date_input("Fecha de Compra")
        ap1 = c2.text_input("Apartado 1")
        ap2 = c3.text_input("Apartado 2")
        
        if st.form_submit_button("Registrar Máquina"):
            data_m = {
                "nombre_maquina": nm, "ubicacion": ubi, "estado": est,
                "fabricante": fab, "modelo": mod, "horas_uso": hrs,
                "fecha_compra": str(f_compra), "apartado_1": ap1, "apartado_2": ap2,
                "creado_por": st.session_state.user
            }
            supabase.table("maquinas").insert(data_m).execute()
            st.rerun()
    st.dataframe(pd.DataFrame(cargar("maquinas")), use_container_width=True)

# --- 9. PÁGINA: ÓRDENES DE TRABAJO (TUS COLUMNAS) ---
elif menu == "📑 Órdenes de Trabajo":
    st.header("Gestión de Órdenes")
    m_list = [m['nombre_maquina'] for m in cargar("maquinas")]
    p_list = [f"{p['nombre']} {p['apellido']}" for p in cargar("personal")]
    
    with st.expander("➕ Lanzar Nueva OP"):
        with st.form("f_op"):
            desc = st.text_area("Descripción")
            c1, c2, c3 = st.columns(3)
            mq = c1.selectbox("ID Máquina", m_list)
            tc = c2.selectbox("ID Técnico", p_list)
            est_op = c3.selectbox("Estado", ["Proceso", "Finalizada"])
            
            tipo = c1.selectbox("Tipo de Tarea", ["Preventiva", "Correctiva"])
            freq = c2.text_input("Frecuencia")
            dur = c3.text_input("Duración Estimada")
            
            paro = c1.selectbox("Requiere Paro", ["Sí", "No"])
            herr = c2.text_input("Herramientas")
            prio = c3.selectbox("Prioridad", ["ALTA", "NORMAL", "BAJA"])
            
            ins = c1.text_input("Insumos")
            cos = c2.number_input("Costo", 0.0)
            f_jefe = c3.text_input("Firma del Jefe")
            
            if st.form_submit_button("Lanzar"):
                data_op = {
                    "descripcion": desc, "id_maquina": mq, "id_tecnico": tc,
                    "estado": est_op, "tipo_tarea": tipo, "frecuencia": freq,
                    "duracion_estimada": dur, "requiere_paro": paro,
                    "herramientas": herr, "prioridad": prio, "insumos": ins,
                    "costo": cos, "firma_jefe": f_jefe, "creado_por": st.session_state.user
                }
                supabase.table("ordenes").insert(data_op).execute()
                st.rerun()
    
    st.dataframe(pd.DataFrame(cargar("ordenes")), use_container_width=True)
