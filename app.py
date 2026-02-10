import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime
import plotly.express as px
from streamlit_drawable_canvas import st_canvas

# --- 1. CONFIGURACIÓN Y CONEXIÓN ---
st.set_page_config(page_title="CORMAIN CMMS PRO", layout="wide", page_icon="🛠️")

try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except Exception as e:
    st.error(f"Error de conexión: {e}")
    st.stop()

# --- 2. FUNCIONES DE CARGA Y FLUJO ---
def cargar_datos(tabla):
    try:
        res = supabase.table(tabla).select("*").eq("creado_por", st.session_state.user).execute()
        return res.data if res.data else []
    except: return []

def mover_estado(id_op, nuevo_estado):
    try:
        # Usamos 'id' en minúsculas como confirmaste
        supabase.table("ordenes").update({"estado": nuevo_estado}).eq("id", id_op).execute()
        st.success(f"Orden #{id_op} movida a {nuevo_estado}")
        st.rerun()
    except Exception as e:
        st.error(f"Error al mover etapa: {e}")

# --- 3. AUTENTICACIÓN ---
if 'auth' not in st.session_state: st.session_state.auth = False

if not st.session_state.auth:
    st.title("🛠️ COMAIN - Gestión de Mantenimiento")
    u = st.text_input("Usuario")
    p = st.text_input("Clave", type="password")
    if st.button("Entrar", use_container_width=True):
        res = supabase.table("usuarios").select("*").eq("email", u).eq("password", p).execute()
        if res.data:
            st.session_state.auth = True
            st.session_state.user = res.data[0]['email']
            st.rerun()
        else: st.error("Acceso incorrecto")
    st.stop()

# --- 4. MENÚ ---
st.sidebar.title(f"👤 {st.session_state.user}")
menu = st.sidebar.radio("Menú Principal", ["🏠 Inicio / Dashboard", "👥 Personal", "⚙️ Maquinaria", "📑 Órdenes de Producción"])

if st.sidebar.button("🚪 Cerrar Sesión"):
    st.session_state.auth = False
    st.rerun()

# --- 5. DASHBOARD (PANEL DE CONTROL) ---
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
        c1, c2 = st.columns(2)
        with c1: st.plotly_chart(px.pie(df_o, names='estado', title="Estado de Órdenes", hole=0.5), use_container_width=True)
        with c2: st.plotly_chart(px.pie(df_o, names='prioridad', title="Prioridad de Tareas"), use_container_width=True)
    else: st.info("Sin datos para mostrar estadísticas.")

# --- 6. GESTIÓN DE PERSONAL ---
elif menu == "👥 Personal":
    st.header("👥 Administración de Personal")
    with st.form("f_p", clear_on_submit=True):
        c1, c2 = st.columns(2)
        n, a = c1.text_input("Nombre"), c2.text_input("Apellido")
        car, esp = c1.text_input("Cargo"), c2.text_input("Especialidad")
        ce, mail = c1.text_input("Código Empleado"), c2.text_input("Email")
        cl1, dir_p = c1.text_input("Clasificación 1"), c2.text_input("Dirección")
        st.write("Firma Digital:")
        st_canvas(stroke_width=2, stroke_color="#000", background_color="#eee", height=100, key="fp")
        if st.form_submit_button("✅ Guardar"):
            try:
                supabase.table("personal").insert({
                    "nombre": n, "apellido": a, "cargo": car, "especialidad": esp, "codigo_empleado": ce, 
                    "email": mail, "clasificacion1": cl1, "direccion": dir_p, "creado_por": st.session_state.user
                }).execute()
                st.rerun()
            except Exception as e: st.error(f"Error: {e}")
    st.dataframe(pd.DataFrame(cargar_datos("personal")), use_container_width=True)

# --- 7. FICHA DE MAQUINARIA ---
elif menu == "⚙️ Maquinaria":
    st.header("⚙️ Ficha Técnica")
    with st.form("form_m"):
        c1, c2, c3 = st.columns(3)
        nm, cod, ser = c1.text_input("Máquina"), c2.text_input("Código"), c3.text_input("Serial")
        fab, mod, ubi = c1.text_input("Fabricante"), c2.text_input("Modelo"), c3.text_input("Ubicación")
        est = c1.selectbox("Estado", ["Operativa", "Mantenimiento", "Falla"])
        hrs = c2.number_input("Horas de uso", 0) # Campo int8
        fc = c3.date_input("Fecha Compra")
        apa1, apa2 = c1.text_input("Apartado 1"), c2.text_input("Apartado 2")
        if st.form_submit_button("🛠️ Registrar"):
            try:
                supabase.table("maquinas").insert({
                    "nombre_maquina": nm, "codigo": cod, "serial": ser, "fabricante": fab, "modelo": mod, 
                    "ubicacion": ubi, "estado": est, "horas_uso": int(hrs), "fecha_compra": str(fc), 
                    "apartado1": apa1, "apartado2": apa2, "creado_por": st.session_state.user
                }).execute()
                st.rerun()
            except Exception as e: st.error(f"Error: {e}")
    st.dataframe(pd.DataFrame(cargar_datos("maquinas")), use_container_width=True)

# --- 8. ÓRDENES DE PRODUCCIÓN (FLUJO DE 4 ETAPAS) ---
elif menu == "📑 Órdenes de Producción":
    st.header("📑 Gestión Integral de Órdenes")
    
    with st.expander("🚀 Lanzar Nueva Orden de Trabajo (OP)"):
        with st.form("f_op"):
            desc = st.text_area("Descripción")
            c1, c2, c3 = st.columns(3)
            mq = c1.selectbox("Máquina", [m['nombre_maquina'] for m in cargar_datos("maquinas")])
            tc = c2.selectbox("Técnico", [f"{p['nombre']} {p['apellido']}" for p in cargar_datos("personal")])
            prio = c3.selectbox("Prioridad", ["ALTA", "NORMAL", "BAJA"])
            tipo = c1.selectbox("Tipo de Tarea", ["Correctiva", "Preventiva"])
            freq = c2.selectbox("Frecuencia", ["Única", "Semanal", "Mensual", "Anual"])
            
            st.write("⏱️ Duración Estimada")
            h, m = st.columns(2)
            hrs, mins = h.number_input("Horas", 0), m.number_input("Minutos", 0)
            
            paro = c1.selectbox("¿Requiere Paro?", ["Sí", "No"])
            herr, insu = c2.text_input("Herramientas"), c3.text_input("Insumos")
            costo = st.number_input("Costo Estimado ($)", 0.0) # Campo float8
            
            if st.form_submit_button("Lanzar"):
                try:
                    supabase.table("ordenes").insert({
                        "descripcion": desc, "id_maquina": mq, "id_tecnico": tc, "estado": "Recepción",
                        "tipo_tarea": tipo, "frecuencia": freq, "duracion_estimada": f"{hrs}h {mins}m",
                        "requiere_paro": paro, "herramientas": herr, "prioridad": prio,
                        "insumos": insu, "costo": float(costo), "creado_por": st.session_state.user
                    }).execute()
                    st.success("Orden en Recepción")
                    st.rerun()
                except Exception as e: st.error(f"Error al guardar: {e}")

    # EL TABLERO DINÁMICO
    st.divider()
    df_op = pd.DataFrame(cargar_datos("ordenes"))
    if not df_op.empty:
        t1, t2, t3, t4 = st.tabs(["📥 Recepción", "⚙️ En Proceso", "✅ Finalizada", "👨‍🏫 Revisada"])
        
        with t1: # RECEPCIÓN
            for _, r in df_op[df_op['estado'] == "Recepción"].iterrows():
                with st.expander(f"OT #{r['id']} - {r['id_maquina']}"):
                    if st.button(f"Iniciar Orden #{r['id']}"): mover_estado(r['id'], "En Proceso")
        
        with t2: # EN PROCESO
            for _, r in df_op[df_op['estado'] == "En Proceso"].iterrows():
                with st.expander(f"OT #{r['id']} en ejecución"):
                    if st.button(f"Finalizar Trabajo #{r['id']}"): mover_estado(r['id'], "Finalizada")

        with t3: # FINALIZADAS
            for _, r in df_op[df_op['estado'] == "Finalizada"].iterrows():
                with st.container(border=True):
                    st.write(f"OT #{r['id']} - Máquina: {r['id_maquina']}")
                    st.write("🖋️ Firma de Revisión del Jefe")
                    st_canvas(stroke_width=2, stroke_color="#000", background_color="#fff", height=80, key=f"fj_{r['id']}")
                    if st.button(f"Aprobar y Archivar #{r['id']}"): mover_estado(r['id'], "Revisada por Jefe")

        with t4: # REVISADAS
            st.dataframe(df_op[df_op['estado'] == "Revisada por Jefe"], use_container_width=True)
    else: st.info("No hay órdenes activas.")
