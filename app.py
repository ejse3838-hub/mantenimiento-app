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
        supabase.table("ordenes").update({"estado": nuevo_estado}).eq("id", id_op).execute()
        st.success(f"Orden #{id_op} movida a {nuevo_estado}")
        st.rerun()
    except Exception as e:
        st.error(f"Error al mover etapa: {e}")

# --- 3. AUTENTICACIÓN ---
if 'auth' not in st.session_state: st.session_state.auth = False

if not st.session_state.auth:
    st.title("🛠️ CORMAIN - Gestión de Mantenimiento")
    
    # Pestañas para Login y Registro
    tab_login, tab_registro = st.tabs(["🔑 Iniciar Sesión", "📝 Registrarse"])
    
    with tab_login:
        u = st.text_input("Usuario", key="login_user")
        p = st.text_input("Clave", type="password", key="login_pass")
        if st.button("Entrar", use_container_width=True):
            res = supabase.table("usuarios").select("*").eq("email", u).eq("password", p).execute()
            if res.data:
                st.session_state.auth = True
                st.session_state.user = res.data[0]['email']
                st.rerun()
            else: st.error("Acceso incorrecto")
            
    with tab_registro:
        st.subheader("Crear nueva cuenta")
        new_u = st.text_input("Nuevo Usuario (Email)", key="reg_user")
        new_p = st.text_input("Nueva Clave", type="password", key="reg_pass")
        confirm_p = st.text_input("Confirmar Clave", type="password", key="reg_pass_conf")
        
        if st.button("Registrar Cuenta", use_container_width=True):
            if new_u and new_p:
                if new_p == confirm_p:
                    try:
                        # Insertamos el nuevo usuario con 'creado_por' igual a su propio email
                        supabase.table("usuarios").insert({
                            "email": new_u, 
                            "password": new_p, 
                            "creado_por": new_u
                        }).execute()
                        st.success("✅ ¡Cuenta creada con éxito! Ya puedes iniciar sesión.")
                    except Exception as e:
                        st.error(f"Error al registrar: {e}")
                else:
                    st.warning("Las contraseñas no coinciden.")
            else:
                st.warning("Por favor completa todos los campos.")
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
        hrs = c2.number_input("Horas de uso", 0) 
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

# --- 8. MÓDULO: ÓRDENES ---
elif menu == "📑 Órdenes de Producción":
    st.header("📑 Gestión de Órdenes")
    mq_list = [m['nombre_maquina'] for m in cargar_datos("maquinas")]
    tc_list = [f"{p['nombre']} {p['apellido']}" for p in cargar_datos("personal")]

    with st.expander("🚀 Lanzar Nueva Orden", expanded=True):
        with st.form("f_op_final"):
            desc = st.text_area("Descripción de la Tarea")
            c1, c2, c3 = st.columns(3)
            mq = c1.selectbox("Máquina", mq_list if mq_list else [""])
            tc = c2.selectbox("Técnico", tc_list if tc_list else [""])
            prio = c3.selectbox("Prioridad", ["ALTA", "NORMAL", "BAJA"])
            tipo = c1.text_input("Tipo (ej: Correctiva)")
            freq = c2.text_input("Frecuencia (ej: Semanal)")
            dur = c3.text_input("Duración Estimada (ej: 2 horas)")
            paro = c1.selectbox("¿Requiere Paro?", ["Sí", "No"])
            herr = c2.text_input("Herramientas")
            insu = c3.text_input("Insumos")
            costo = st.number_input("Costo ($)", value=0.0, step=0.1)
            
            if st.form_submit_button("📡 Lanzar Orden"):
                datos_para_enviar = {
                    "descripcion": str(desc),
                    "id_maquina": str(mq),
                    "id_tecnico": str(tc),
                    "estado": "Recepción",
                    "tipo_tarea": str(tipo),
                    "frecuencia": str(freq),
                    "duracion_estimada": str(dur),
                    "requiere_paro": str(paro),
                    "herramientas": str(herr),
                    "prioridad": str(prio),
                    "insumos": str(insu),
                    "costo": float(costo),
                    "creado_por": str(st.session_state.user)
                }
                try:
                    supabase.table("ordenes").insert(datos_para_enviar).execute()
                    st.success("✅ Orden creada con éxito")
                    st.rerun()
                except Exception as error:
                    st.error(f"Error detectado: {error}")
                    
    st.divider()
    df_op = pd.DataFrame(cargar_datos("ordenes"))
    if not df_op.empty:
        t1, t2, t3, t4 = st.tabs(["📥 Recepción", "⚙️ En Proceso", "✅ Finalizada", "👨‍🏫 Revisada"])
        
        with t1: 
            for _, r in df_op[df_op['estado'] == "Recepción"].iterrows():
                with st.expander(f"OT #{r['id']} - {r['id_maquina']}"):
                    if st.button(f"Iniciar Orden #{r['id']}"): mover_estado(r['id'], "En Proceso")
        
        with t2: 
            for _, r in df_op[df_op['estado'] == "En Proceso"].iterrows():
                with st.expander(f"OT #{r['id']} en ejecución"):
                    if st.button(f"Finalizar Trabajo #{r['id']}"): mover_estado(r['id'], "Finalizada")

        with t3: 
            for _, r in df_op[df_op['estado'] == "Finalizada"].iterrows():
                with st.container(border=True):
                    st.write(f"OT #{r['id']} - Máquina: {r['id_maquina']}")
                    st.write("🖋️ Firma de Revisión del Jefe")
                    st_canvas(stroke_width=2, stroke_color="#000", background_color="#fff", height=80, key=f"fj_{r['id']}")
                    if st.button(f"Aprobar y Archivar #{r['id']}"): mover_estado(r['id'], "Revisada por Jefe")

        with t4: 
            st.dataframe(df_op[df_op['estado'] == "Revisada por Jefe"], use_container_width=True)
    else: st.info("No hay órdenes activas.")

