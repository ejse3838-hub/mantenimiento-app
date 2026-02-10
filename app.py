import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime

# --- 1. CONEXIÓN (Ajustada a tu formato de Secrets) ---
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
st.set_page_config(page_title="CORMAIN CMMS PRO", layout="wide", page_icon="⚙️")
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

    # --- 6. PÁGINA: INICIO (DASHBOARD) ---
    if st.session_state.menu == "🏠 Inicio":
        st.title("📊 Panel de Control")
        df = pd.DataFrame(cargar("ordenes"))
        if not df.empty:
            c1, c2 = st.columns(2)
            c1.metric("Órdenes Totales", len(df))
            import plotly.express as px
            fig = px.pie(df, names='estado', hole=0.4, title="Estado de Órdenes")
            st.plotly_chart(fig, use_container_width=True)
        else: st.info("Sin datos registrados.")

    # --- 7. PÁGINA: PERSONAL (9 CAMPOS) ---
    elif st.session_state.menu == "👥 Personal":
        st.header("Gestión de Personal")
        with st.form("f_p", clear_on_submit=True):
            c1, c2 = st.columns(2)
            n = c1.text_input("Nombre")
            ap = c2.text_input("Apellido")
            cargo = c1.text_input("Cargo")
            tel = c2.text_input("Teléfono")
            em = c1.text_input("Email Personal")
            tur = c2.selectbox("Turno", ["Matutino", "Vespertino", "Nocturno"])
            f_ing = c1.date_input("Fecha de Ingreso")
            sal = c2.number_input("Salario ($)", min_value=0.0)
            obs = st.text_area("Observaciones/Habilidades")
            
            if st.form_submit_button("Guardar"):
                try:
                    supabase.table("personal").insert({
                        "nombre": n, "apellido": ap, "cargo": cargo, "telefono": tel,
                        "email": em, "turno": tur, "fecha_ingreso": str(f_ing),
                        "salario": sal, "notas": obs, "creado_por": st.session_state.user
                    }).execute()
                    st.success("Personal guardado")
                    st.rerun()
                except Exception as e: st.error(f"Error: {e}")
        
        st.dataframe(pd.DataFrame(cargar("personal")), use_container_width=True)

    # --- 8. PÁGINA: MAQUINARIA (10 CAMPOS) ---
    elif st.session_state.menu == "⚙️ Maquinaria":
        st.header("Ficha Técnica de Activos")
        with st.form("f_m", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            nm = c1.text_input("Máquina/Equipo")
            cod = c2.text_input("Código Interno")
            mar = c3.text_input("Marca/Fabricante")
            ubi = c1.text_input("Ubicación")
            est = c2.selectbox("Estado", ["Operativa", "Mantenimiento", "Falla Crítica"])
            f_adq = c3.date_input("Fecha Adquisición")
            prio = c1.selectbox("Prioridad", ["Alta", "Media", "Baja"])
            prov = c2.text_input("Proveedor")
            v_util = c3.number_input("Vida Útil (Años)", 1)
            espec = st.text_area("Especificaciones Técnicas")
            
            if st.form_submit_button("Registrar"):
                try:
                    supabase.table("maquinas").insert({
                        "nombre_maquina": nm, "codigo": cod, "marca": mar, "ubicacion": ubi, 
                        "estado": est, "fecha_adq": str(f_adq), "prioridad": prio,
                        "proveedor": prov, "vida_util": v_util, "especificaciones": espec,
                        "creado_por": st.session_state.user
                    }).execute()
                    st.success("Máquina registrada")
                    st.rerun()
                except Exception as e: st.error(f"Error: {e}")
        
        st.dataframe(pd.DataFrame(cargar("maquinas")), use_container_width=True)

    # --- 9. PÁGINA: ÓRDENES DE TRABAJO (CAMPOS SIMPLIFICADOS) ---
    elif st.session_state.menu == "📑 Órdenes de Trabajo":
        st.header("Gestión de OP")
        
        # Cargamos datos para los selectbox
        maquinas_data = cargar("maquinas")
        personal_data = cargar("personal")
        m_list = [f"{m['nombre_maquina']} ({m['codigo']})" for m in maquinas_data]
        p_list = [f"{p['nombre']} {p['apellido']}" for p in personal_data]
        
        with st.expander("➕ Lanzar Nueva OP"):
            with st.form("f_op", clear_on_submit=True):
                desc = st.text_area("Descripción de la falla o tarea")
                c1, c2 = st.columns(2)
                mq = c1.selectbox("Máquina", m_list)
                tc = c2.selectbox("Técnico Asignado", p_list)
                tt = c1.selectbox("Tipo", ["Correctiva", "Preventiva"])
                pr = c2.selectbox("Prioridad", ["URGENTE", "NORMAL"])
                
                if st.form_submit_button("Lanzar"):
                    try:
                        supabase.table("ordenes").insert({
                            "descripcion": desc, "maquina": mq, "tecnico": tc, 
                            "tipo": tt, "prioridad": pr, "estado": "Proceso", 
                            "fecha": str(datetime.now().date()),
                            "creado_por": st.session_state.user
                        }).execute()
                        st.success("✅ ¡Orden enviada!")
                        st.rerun()
                    except Exception as e: st.error(f"Error: {e}")

        st.divider()
        st.subheader("Historial de Órdenes")
        df_o = pd.DataFrame(cargar("ordenes"))
        if not df_o.empty:
            st.dataframe(df_o, use_container_width=True)
        else: st.info("No hay órdenes de trabajo activas.")
