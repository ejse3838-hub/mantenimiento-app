import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime
import plotly.express as px
from streamlit_drawable_canvas import st_canvas

# --- 1. CONFIGURACIÓN Y CONEXIÓN ---
st.set_page_config(page_title="CORMAIN CMMS PRO - Ingeniería Industrial", layout="wide", page_icon="🛠️")

try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except Exception as e:
    st.error(f"Error crítico de conexión: {e}")
    st.stop()

# --- 2. FUNCIONES DE CARGA Y ACTUALIZACIÓN ---
def cargar_datos(tabla):
    try:
        res = supabase.table(tabla).select("*").eq("creado_por", st.session_state.user).execute()
        return res.data if res.data else []
    except Exception:
        return []

def actualizar_estado(id_orden, nuevo_estado):
    try:
        supabase.table("ordenes").update({"estado": nuevo_estado}).eq("id", id_orden).execute()
        st.rerun()
    except Exception as e:
        st.error(f"Error al actualizar: {e}")

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
st.sidebar.title(f"👤 {st.session_state.user}")
st.sidebar.divider()
menu = st.sidebar.radio("Navegación", ["🏠 Inicio / Dashboard", "👥 Gestión de Personal", "⚙️ Ficha de Maquinaria", "📑 Órdenes de Producción"])

if st.sidebar.button("🚪 Cerrar Sesión"):
    st.session_state.auth = False
    st.rerun()

# --- 5. DASHBOARD ---
if menu == "🏠 Inicio / Dashboard":
    st.title("📊 Panel de Control Gerencial")
    df_o = pd.DataFrame(cargar_datos("ordenes"))
    etapas = ["Recepción", "En Proceso", "Finalizada", "Revisada por Jefe"]
    cols = st.columns(4)
    if not df_o.empty:
        for i, etapa in enumerate(etapas):
            conteo = len(df_o[df_o['estado'] == etapa]) if 'estado' in df_o.columns else 0
            cols[i].metric(label=etapa, value=conteo)
        st.divider()
        c_p1, c_p2 = st.columns(2)
        with c_p1:
            st.plotly_chart(px.pie(df_o, names='estado', title="Estado de Órdenes", hole=0.5), use_container_width=True)
        with c_p2:
            st.plotly_chart(px.pie(df_o, names='prioridad', title="Prioridad de Tareas", hole=0.5), use_container_width=True)
    else: st.info("Sin datos registrados.")

# --- 6. GESTIÓN DE PERSONAL ---
elif menu == "👥 Gestión de Personal":
    st.header("👥 Administración de Personal")
    with st.form("form_personal", clear_on_submit=True):
        c1, c2 = st.columns(2)
        n, a = c1.text_input("Nombre"), c2.text_input("Apellido")
        cod, mail = c1.text_input("Código"), c2.text_input("Email")
        car, esp = c1.text_input("Cargo"), c2.text_input("Especialidad")
        clasi, direc = c1.text_input("Clasificación"), c2.text_input("Dirección")
        st.write("Firma Digital")
        st_canvas(stroke_width=2, stroke_color="#000", background_color="#eee", height=100, key="cp")
        if st.form_submit_button("✅ Registrar"):
            supabase.table("personal").insert({"nombre": n, "apellido": a, "cargo": car, "especialidad": esp, "codigo_empleado": cod, "email": mail, "clasificacion1": clasi, "direccion": direc, "firma_path": "Reg", "creado_por": st.session_state.user}).execute()
            st.success("Guardado"); st.rerun()
    st.dataframe(pd.DataFrame(cargar_datos("personal")), use_container_width=True)

# --- 7. MAQUINARIA ---
elif menu == "⚙️ Ficha de Maquinaria":
    st.header("⚙️ Inventario de Maquinaria")
    with st.form("form_maq"):
        c1, c2, c3 = st.columns(3)
        nm, cod_m, ser = c1.text_input("Nombre"), c2.text_input("Código"), c3.text_input("Serial")
        ubi, est = c1.text_input("Ubicación"), c2.selectbox("Estado", ["Operativa", "Mantenimiento", "Falla"])
        fab, mod = c3.text_input("Fabricante"), c1.text_input("Modelo")
        hrs = c2.number_input("Horas", 0)
        f_c = c3.date_input("Compra")
        if st.form_submit_button("🛠️ Registrar"):
            supabase.table("maquinas").insert({"nombre_maquina": nm, "codigo": cod_m, "ubicacion": ubi, "estado": est, "serial": ser, "fabricante": fab, "modelo": mod, "horas_uso": hrs, "fecha_compra": str(f_c), "creado_por": st.session_state.user}).execute()
            st.success("Registrada"); st.rerun()
    st.dataframe(pd.DataFrame(cargar_datos("maquinas")), use_container_width=True)

# --- 8. ÓRDENES DE PRODUCCIÓN (FLUJO POR ETAPAS REFORZADO) ---
elif menu == "📑 Órdenes de Producción":
    st.header("📑 Flujo de Trabajo de Órdenes (OP)")
    
    # --- CREACIÓN DE ORDEN ---
    with st.expander("🚀 Lanzar Nueva Orden de Trabajo"):
        with st.form("form_op"):
            desc = st.text_area("Descripción de la tarea")
            c1, c2, c3 = st.columns(3)
            mq = c1.selectbox("Máquina", [m['nombre_maquina'] for m in cargar_datos("maquinas")])
            tc = c2.selectbox("Técnico", [f"{p['nombre']} {p['apellido']}" for p in cargar_datos("personal")])
            prio = c3.selectbox("Prioridad", ["ALTA", "NORMAL", "BAJA"])
            
            tipo = c1.selectbox("Tipo", ["Correctiva", "Preventiva"])
            freq = c2.selectbox("Frecuencia", ["Única", "Diaria", "Semanal", "Quincenal", "Mensual", "Semestral", "Anual"])
            
            st.write("⏱️ Duración Estimada")
            col_h, col_m = st.columns(2)
            hrs_est = col_h.number_input("Horas", 0, 48)
            min_est = col_m.number_input("Minutos", 0, 59)
            
            cos = st.number_input("Costo Estimado ($)", 0.0)
            
            if st.form_submit_button("📡 Lanzar Orden"):
                duracion_str = f"{hrs_est}h {min_est}m"
                data_op = {"descripcion": desc, "id_maquina": mq, "id_tecnico": tc, "estado": "Recepción", "tipo_tarea": tipo, "frecuencia": freq, "duracion_estimada": duracion_str, "prioridad": prio, "costo": cos, "creado_por": st.session_state.user}
                supabase.table("ordenes").insert(data_op).execute()
                st.success("Orden en Recepción"); st.rerun()

    # --- TABLERO DE CONTROL POR ETAPAS ---
    st.divider()
    df_op = pd.DataFrame(cargar_datos("ordenes"))
    
    if not df_op.empty:
        # Usamos pestañas para organizar las etapas del proceso
        tab_rec, tab_proc, tab_fin, tab_rev = st.tabs(["📥 Recepción", "⚙️ En Proceso", "✅ Finalizadas", "👨‍🏫 Revisadas por Jefe"])
        
        with tab_rec:
            st.subheader("Órdenes Recién Ingresadas")
            recept = df_op[df_op['estado'] == "Recepción"]
            for _, r in recept.iterrows():
                with st.expander(f"OT #{r['id']} - {r['id_maquina']}"):
                    st.write(f"**Descripción:** {r['descripcion']}")
                    if st.button(f"Iniciar Proceso #{r['id']}"):
                        actualizar_estado(r['id'], "En Proceso")

        with tab_proc:
            st.subheader("Trabajos en Ejecución")
            proceso = df_op[df_op['estado'] == "En Proceso"]
            for _, r in proceso.iterrows():
                with st.expander(f"OT #{r['id']} - {r['id_maquina']}"):
                    st.write(f"**Técnico:** {r['id_tecnico']}")
                    if st.button(f"Marcar como Finalizada #{r['id']}"):
                        actualizar_estado(r['id'], "Finalizada")

        with tab_fin:
            st.subheader("Esperando Revisión de Jefatura")
            final = df_op[df_op['estado'] == "Finalizada"]
            for _, r in final.iterrows():
                with st.container(border=True):
                    st.write(f"**OT #{r['id']}** | **Máquina:** {r['id_maquina']} | **Costo:** ${r['costo']}")
                    st.write(f"**Técnico:** {r['id_tecnico']}")
                    
                    # Espacio para firma del jefe antes de cerrar
                    st.write("🖋️ Firma de Revisión del Jefe")
                    st_canvas(stroke_width=2, stroke_color="#000", background_color="#fff", height=80, key=f"f_j_{r['id']}")
                    
                    if st.button(f"Aprobar y Archivar #{r['id']}"):
                        actualizar_estado(r['id'], "Revisada por Jefe")

        with tab_rev:
            st.subheader("Histórico de Órdenes Cerradas")
            revisadas = df_op[df_op['estado'] == "Revisada por Jefe"]
            st.table(revisadas[['id', 'id_maquina', 'tipo_tarea', 'duracion_estimada']])
    else:
        st.info("No hay órdenes activas.")
