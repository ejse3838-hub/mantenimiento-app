import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime
import plotly.express as px
from streamlit_drawable_canvas import st_canvas

# --- 1. CONFIGURACIÓN Y CONEXIÓN ---
st.set_page_config(page_title="CORMAIN CMMS PRO - Sistema de Gestión", layout="wide", page_icon="🛠️")

try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except Exception as e:
    st.error(f"Error crítico de conexión: {e}")
    st.stop()

# --- 2. FUNCIONES DE CARGA DE DATOS ---
def cargar_datos(tabla):
    try:
        res = supabase.table(tabla).select("*").eq("creado_por", st.session_state.user).execute()
        return res.data if res.data else []
    except Exception:
        return []

# --- 3. SISTEMA DE AUTENTICACIÓN ---
if 'auth' not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    st.title("🛠️ COMAIN - Gestión de Mantenimiento Industrial")
    tab_login, tab_reg = st.tabs(["🔑 Acceso", "📝 Registro Nuevo"])
    
    with tab_login:
        u = st.text_input("Correo Electrónico")
        p = st.text_input("Contraseña", type="password")
        if st.button("Iniciar Sesión", use_container_width=True):
            res = supabase.table("usuarios").select("*").eq("email", u).eq("password", p).execute()
            if res.data:
                st.session_state.auth = True
                st.session_state.user = res.data[0]['email']
                st.rerun()
            else:
                st.error("Credenciales incorrectas.")
    
    with tab_reg:
        nu = st.text_input("Nuevo Email")
        np = st.text_input("Nueva Clave", type="password")
        if st.button("Crear Nueva Cuenta"):
            supabase.table("usuarios").insert({"email": nu, "password": np, "creado_por": nu}).execute()
            st.success("Cuenta creada exitosamente.")
    st.stop()

# --- 4. INTERFAZ PRINCIPAL ---
st.sidebar.title(f"👤 Usuario: {st.session_state.user}")
st.sidebar.divider()
menu = st.sidebar.radio("Navegación del Sistema", ["🏠 Inicio / Dashboard", "👥 Gestión de Personal", "⚙️ Ficha de Maquinaria", "📑 Órdenes de Producción"])

if st.sidebar.button("🚪 Cerrar Sesión"):
    st.session_state.auth = False
    st.rerun()

# --- 5. DASHBOARD (PANEL DE CONTROL CON PASTELES) ---
if menu == "🏠 Inicio / Dashboard":
    st.title("📊 Panel de Control Gerencial")
    df_o = pd.DataFrame(cargar_datos("ordenes"))
    
    # Enumeración por Etapas Requeridas
    etapas_orden = ["Recepción", "En Proceso", "Finalizada", "Revisada por Jefe"]
    cols = st.columns(4)
    
    if not df_o.empty:
        for i, etapa in enumerate(etapas_orden):
            conteo = len(df_o[df_o['estado'] == etapa]) if 'estado' in df_o.columns else 0
            cols[i].metric(label=f"OT en {etapa}", value=conteo)
        
        st.divider()
        c_p1, c_p2 = st.columns(2)
        with c_p1:
            fig1 = px.pie(df_o, names='estado', title="Estado Global de Órdenes", hole=0.5, color_discrete_sequence=px.colors.qualitative.Pastel)
            st.plotly_chart(fig1, use_container_width=True)
        with c_p2:
            fig2 = px.pie(df_o, names='prioridad', title="Prioridad de Tareas Pendientes", hole=0.5)
            st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("Bienvenido al sistema. Registre datos para generar el análisis visual.")

# --- 6. GESTIÓN DE PERSONAL (9 CAMPOS + FIRMA) ---
elif menu == "👥 Gestión de Personal":
    st.header("👥 Administración de Personal")
    with st.form("form_personal", clear_on_submit=True):
        c1, c2 = st.columns(2)
        n = c1.text_input("Nombre")
        a = c2.text_input("Apellido")
        cod = c1.text_input("Código de Empleado")
        mail = c2.text_input("Email Corporativo")
        car = c1.text_input("Cargo / Puesto")
        esp = c2.text_input("Especialidad Técnica")
        clasi = c1.text_input("Clasificación 1")
        direc = c2.text_input("Dirección Domiciliaria")
        
        st.write("🖋️ Firma Digital del Personal")
        canvas_p = st_canvas(fill_color="rgba(255, 165, 0, 0.3)", stroke_width=2, stroke_color="#000", background_color="#eee", height=120, key="cp")
        
        if st.form_submit_button("✅ Registrar Personal"):
            data = {
                "nombre": n, "apellido": a, "cargo": car, "especialidad": esp,
                "codigo_empleado": cod, "email": mail, "clasificacion1": clasi,
                "direccion": direc, "firma_path": "Registrada", "creado_por": st.session_state.user
            }
            supabase.table("personal").insert(data).execute()
            st.success("Empleado guardado exitosamente.")
            st.rerun()
    
    st.subheader("Listado de Personal")
    st.dataframe(pd.DataFrame(cargar_datos("personal")), use_container_width=True)

# --- 7. FICHA DE MAQUINARIA (10+ CAMPOS) ---
elif menu == "⚙️ Ficha de Maquinaria":
    st.header("⚙️ Inventario Técnico de Maquinaria")
    with st.form("form_maquinas", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        nm = c1.text_input("Nombre de la Máquina")
        cod_m = c2.text_input("Código de Activo")
        ser = c3.text_input("Número de Serial")
        ubi = c1.text_input("Ubicación en Planta")
        est = c2.selectbox("Estado Operativo", ["Operativa", "Mantenimiento", "Falla Crítica"])
        fab = c3.text_input("Fabricante")
        mod = c1.text_input("Modelo / Versión")
        hrs = c2.number_input("Horas de uso acumuladas", 0)
        f_compra = c3.date_input("Fecha de Adquisición")
        ap1 = c1.text_input("Apartado 1 (Notas)")
        ap2 = c2.text_input("Apartado 2 (Garantía)")
        
        if st.form_submit_button("🛠️ Registrar Maquina"):
            data_m = {
                "nombre_maquina": nm, "codigo": cod_m, "ubicacion": ubi, "estado": est,
                "serial": ser, "fabricante": fab, "modelo": mod, "horas_uso": hrs,
                "fecha_compra": str(f_compra), "apartado1": ap1, "apartado2": ap2,
                "creado_por": st.session_state.user
            }
            supabase.table("maquinas").insert(data_m).execute()
            st.success("Máquina registrada en la base de datos.")
            st.rerun()

    st.subheader("Inventario de Activos")
    st.dataframe(pd.DataFrame(cargar_datos("maquinas")), use_container_width=True)

# --- 8. ÓRDENES DE PRODUCCIÓN (4 ETAPAS Y CAMPOS TÉCNICOS) ---
elif menu == "📑 Órdenes de Producción":
    st.header("📑 Gestión de Órdenes de Producción (OP)")
    
    # Datos para listas desplegables
    mq_list = [m['nombre_maquina'] for m in cargar_datos("maquinas")]
    tec_list = [f"{p['nombre']} {p['apellido']}" for p in cargar_datos("personal")]
    
    with st.expander("🚀 Lanzar Nueva Orden de Trabajo", expanded=False):
        with st.form("form_op"):
            desc = st.text_area("Descripción detallada del problema o tarea")
            c1, c2, c3 = st.columns(3)
            mq = c1.selectbox("Máquina Afectada", mq_list if mq_list else ["Sin maquinas"])
            tc = c2.selectbox("Técnico Asignado", tec_list if tec_list else ["Sin personal"])
            est_op = c3.selectbox("Etapa de la Orden", ["Recepción", "En Proceso", "Finalizada", "Revisada por Jefe"])
            
            tipo = c1.selectbox("Tipo de Tarea", ["Correctiva", "Preventiva", "Predictiva"])
            freq = c2.text_input("Frecuencia (ej. Semanal)")
            dur = c3.text_input("Duración Estimada")
            
            paro = c1.selectbox("¿Requiere Paro de Planta?", ["Sí", "No"])
            herr = c2.text_input("Herramientas Necesarias")
            prio = c3.selectbox("Prioridad", ["ALTA", "NORMAL", "BAJA"])
            
            ins = c1.text_input("Insumos / Repuestos")
            cos = c2.number_input("Costo Estimado ($)", 0.0)
            
            st.write("✍️ Firma Digital de Autorización (Jefe de Planta)")
            canvas_jefe = st_canvas(fill_color="rgba(255, 165, 0, 0.3)", stroke_width=3, stroke_color="#000", background_color="#fff", height=150, key="cj")
            
            if st.form_submit_button("📡 Lanzar Orden de Trabajo"):
                data_op = {
                    "descripcion": desc, "id_maquina": mq, "id_tecnico": tc, "estado": est_op,
                    "tipo_tarea": tipo, "frecuencia": freq, "duracion_estimada": dur,
                    "requiere_paro": paro, "herramientas": herr, "prioridad": prio,
                    "insumos": ins, "costo": cos, "firma_jefe": "Firma Digital Jefe",
                    "creado_por": st.session_state.user
                }
                supabase.table("ordenes").insert(data_op).execute()
                st.success("✅ Orden de Trabajo lanzada y notificada.")
                st.rerun()

    st.divider()
    st.subheader("Historial de Órdenes de Producción")
    df_ver_op = pd.DataFrame(cargar_datos("ordenes"))
    if not df_ver_op.empty:
        st.dataframe(df_ver_op, use_container_width=True)
