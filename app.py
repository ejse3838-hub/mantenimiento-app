import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime
import plotly.express as px
from streamlit_drawable_canvas import st_canvas

# --- 1. CONFIGURACIÓN TÉCNICA ---
st.set_page_config(page_title="CORMAIN CMMS PRO - Ingeniería Industrial", layout="wide", page_icon="🛠️")

# Estilos personalizados para que se vea más profesional
st.markdown("""
    <style>
    .stMetric { background-color: #f0f2f6; padding: 10px; border-radius: 10px; border: 1px solid #d1d5db; }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { background-color: #f9fafb; border-radius: 5px; padding: 10px; }
    </style>
    """, unsafe_allow_html=True)

try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except Exception as e:
    st.error(f"Error crítico de conexión: {e}")
    st.stop()

# --- 2. MOTOR DE DATOS ---
def cargar_datos(tabla):
    try:
        res = supabase.table(tabla).select("*").eq("creado_por", st.session_state.user).execute()
        return res.data if res.data else []
    except: return []

def actualizar_flujo(id_op, nuevo_estado):
    try:
        # Usamos el id (int8) para mover la orden entre etapas como confirmaste
        supabase.table("ordenes").update({"estado": nuevo_estado}).eq("id", id_op).execute()
        st.toast(f"✅ Orden #{id_op} movida a {nuevo_estado}")
        st.rerun()
    except Exception as e:
        st.error(f"Error al mover flujo: {e}")

# --- 3. AUTENTICACIÓN ---
if 'auth' not in st.session_state: st.session_state.auth = False

if not st.session_state.auth:
    st.title("🛠️ COMAIN - Gestión de Mantenimiento")
    tab_log, tab_reg = st.tabs(["🔒 Ingreso", "📝 Registro"])
    with tab_log:
        u = st.text_input("Correo electrónico")
        p = st.text_input("Contraseña", type="password")
        if st.button("Acceder al Sistema", use_container_width=True):
            res = supabase.table("usuarios").select("*").eq("email", u).eq("password", p).execute()
            if res.data:
                st.session_state.auth = True
                st.session_state.user = res.data[0]['email']
                st.rerun()
            else: st.error("Usuario o clave incorrectos")
    with tab_reg:
        nu, np = st.text_input("Nuevo correo"), st.text_input("Nueva clave", type="password")
        if st.button("Crear Usuario"):
            supabase.table("usuarios").insert({"email": nu, "password": np, "creado_por": nu}).execute()
            st.success("Cuenta creada")
    st.stop()

# --- 4. MENÚ DE NAVEGACIÓN ---
st.sidebar.title(f"👤 {st.session_state.user}")
st.sidebar.divider()
menu = st.sidebar.radio("Módulos del Sistema", ["🏠 Dashboard Gerencial", "👥 Gestión de Personal", "⚙️ Ficha de Maquinaria", "📑 Órdenes de Trabajo (OP)"])

if st.sidebar.button("🚪 Salir"):
    st.session_state.auth = False
    st.rerun()

# --- 5. MÓDULO: DASHBOARD ---
if menu == "🏠 Dashboard Gerencial":
    st.title("📊 Indicadores Clave de Desempeño (KPIs)")
    df_o = pd.DataFrame(cargar_datos("ordenes"))
    etapas_lista = ["Recepción", "En Proceso", "Finalizada", "Revisada por Jefe"]
    
    cols = st.columns(4)
    if not df_o.empty:
        for i, etapa in enumerate(etapas_lista):
            conteo = len(df_o[df_o['estado'] == etapa]) if 'estado' in df_o.columns else 0
            cols[i].metric(label=etapa, value=conteo)
        
        st.divider()
        c1, c2 = st.columns(2)
        with c1:
            st.plotly_chart(px.pie(df_o, names='estado', title="Distribución de Estados", hole=0.5, color_discrete_sequence=px.colors.qualitative.Bold), use_container_width=True)
        with c2:
            st.plotly_chart(px.pie(df_o, names='prioridad', title="Prioridad de Tareas"), use_container_width=True)
    else: st.info("Registre órdenes para visualizar el dashboard.")

# --- 6. MÓDULO: PERSONAL (9 CAMPOS + FIRMA) ---
elif menu == "👥 Gestión de Personal":
    st.header("👥 Administración de Talento Humano")
    with st.form("form_personal_full", clear_on_submit=True):
        c1, c2 = st.columns(2)
        nom, ape = c1.text_input("Nombre"), c2.text_input("Apellido")
        cod_e, mail = c1.text_input("Código de Empleado"), c2.text_input("Email Corporativo")
        car, esp = c1.text_input("Cargo"), c2.text_input("Especialidad")
        cl1, direc = c1.text_input("Clasificación 1"), c2.text_input("Dirección Domiciliaria")
        st.write("🖋️ Firma Digital del Colaborador")
        st_canvas(stroke_width=2, stroke_color="#000", background_color="#eee", height=100, key="can_p")
        if st.form_submit_button("✅ Guardar Colaborador"):
            supabase.table("personal").insert({
                "nombre": nom, "apellido": ape, "cargo": car, "especialidad": esp, "codigo_empleado": cod_e,
                "email": mail, "clasificacion1": cl1, "direccion": direc, "creado_por": st.session_state.user
            }).execute()
            st.success("Personal registrado"); st.rerun()
    st.subheader("Base de Datos de Personal")
    st.dataframe(pd.DataFrame(cargar_datos("personal")), use_container_width=True)

# --- 7. MÓDULO: MAQUINARIA (10 CAMPOS) ---
elif menu == "⚙️ Ficha de Maquinaria":
    st.header("⚙️ Inventario Técnico de Activos")
    with st.form("form_maq_full"):
        c1, c2, c3 = st.columns(3)
        nm, cod_m, ser = c1.text_input("Máquina"), c2.text_input("Código"), c3.text_input("Serial")
        ubi, est = c1.text_input("Ubicación"), c2.selectbox("Estado Actual", ["Operativa", "Mantenimiento", "Falla"])
        fab, mod = c3.text_input("Fabricante"), c1.text_input("Modelo")
        hrs = c2.number_input("Horas de uso acumuladas", 0)
        fc = c3.date_input("Fecha de Adquisición")
        ap1, ap2 = c1.text_input("Apartado 1"), c2.text_input("Apartado 2")
        if st.form_submit_button("🛠️ Registrar Activo"):
            supabase.table("maquinas").insert({
                "nombre_maquina": nm, "codigo": cod_m, "serial": ser, "fabricante": fab, "modelo": mod,
                "ubicacion": ubi, "estado": est, "horas_uso": int(hrs), "fecha_compra": str(fc),
                "apartado1": ap1, "apartado2": ap2, "creado_por": st.session_state.user
            }).execute()
            st.success("Activo registrado"); st.rerun()
    st.dataframe(pd.DataFrame(cargar_datos("maquinas")), use_container_width=True)

# --- 8. MÓDULO: ÓRDENES (EL FLUJO DE TRABAJO COMPLETO) ---
elif menu == "📑 Órdenes de Trabajo (OP)":
    st.header("📑 Sistema de Gestión de Órdenes de Producción")
    
    # DATOS PARA SELECTORES
    mq_list = [m['nombre_maquina'] for m in cargar_datos("maquinas")]
    tc_list = [f"{p['nombre']} {p['apellido']}" for p in cargar_datos("personal")]

    with st.expander("🚀 Lanzar Nueva Orden de Trabajo (OP)", expanded=False):
        with st.form("form_op_maestro"):
            desc = st.text_area("Descripción de la Tarea")
            c1, c2, c3 = st.columns(3)
            mq = c1.selectbox("Seleccionar Máquina", mq_list)
            tc = c2.selectbox("Asignar Técnico", tc_list)
            prio = c3.selectbox("Prioridad", ["ALTA", "NORMAL", "BAJA"])
            
            tipo = c1.selectbox("Tipo de Tarea", ["Correctiva", "Preventiva", "Predictiva"])
            freq = c2.selectbox("Frecuencia", ["Única", "Diaria", "Semanal", "Mensual", "Semestral", "Anual"])
            
            st.write("⏱️ Duración Estimada")
            h_c, m_c = st.columns(2)
            h_est = h_c.number_input("Horas", 0, 100)
            m_est = m_c.number_input("Minutos", 0, 59)
            
            paro = c1.selectbox("¿Requiere Paro?", ["Sí", "No"])
            herr = c2.text_input("Herramientas Necesarias")
            insu = c3.text_input("Insumos / Repuestos")
            costo = st.number_input("Costo Estimado ($)", 0.0)
            
            if st.form_submit_button("📡 Lanzar Orden a Recepción"):
                dur_total = f"{h_est}h {m_est}m"
                supabase.table("ordenes").insert({
                    "descripcion": desc, "id_maquina": mq, "id_tecnico": tc, "estado": "Recepción",
                    "tipo_tarea": tipo, "frecuencia": freq, "duracion_estimada": dur_total,
                    "requiere_paro": paro, "herramientas": herr, "prioridad": prio,
                    "insumos": insu, "costo": float(costo), "creado_por": st.session_state.user
                }).execute()
                st.success("Orden en etapa de Recepción"); st.rerun()

    st.divider()
    # TABLERO DE CONTROL POR ETAPAS (EL WORKFLOW)
    df_op = pd.DataFrame(cargar_datos("ordenes"))
    if not df_op.empty:
        t_rec, t_proc, t_fin, t_rev = st.tabs(["📥 Recepción", "⚙️ En Proceso", "✅ Finalizadas", "👨‍🏫 Revisadas por Jefe"])
        
        with t_rec:
            st.subheader("Órdenes por Iniciar")
            for _, r in df_op[df_op['estado'] == "Recepción"].iterrows():
                with st.expander(f"OT #{r['id']} - {r['id_maquina']}"):
                    st.write(f"**Tarea:** {r['descripcion']}")
                    if st.button(f"Comenzar Trabajo #{r['id']}", key=f"btn_s_{r['id']}"):
                        actualizar_flujo(r['id'], "En Proceso")

        with t_proc:
            st.subheader("Trabajos en Ejecución")
            for _, r in df_op[df_op['estado'] == "En Proceso"].iterrows():
                with st.expander(f"OT #{r['id']} - Ejecutando técnico: {r['id_tecnico']}"):
                    st.write(f"**Herramientas:** {r['herramientas']}")
                    if st.button(f"Finalizar Tarea #{r['id']}", key=f"btn_f_{r['id']}"):
                        actualizar_flujo(r['id'], "Finalizada")

        with t_fin:
            st.subheader("Control de Calidad y Firma de Jefatura")
            for _, r in df_op[df_op['estado'] == "Finalizada"].iterrows():
                with st.container(border=True):
                    st.write(f"**OT #{r['id']}** | **Costo Real:** ${r['costo']} | **Duración:** {r['duracion_estimada']}")
                    st.write("🖋️ Firma de Aprobación del Jefe")
                    st_canvas(stroke_width=2, stroke_color="#000", background_color="#fff", height=100, key=f"can_j_{r['id']}")
                    if st.button(f"Aprobar y Archivar #{r['id']}", key=f"btn_a_{r['id']}"):
                        actualizar_flujo(r['id'], "Revisada por Jefe")

        with t_rev:
            st.subheader("Histórico de Órdenes Cerradas")
            st.dataframe(df_op[df_op['estado'] == "Revisada por Jefe"], use_container_width=True)
    else:
        st.info("No hay órdenes de trabajo activas en este momento.")
