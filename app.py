import streamlit as st
import pandas as pd
from supabase import create_client, Client
from streamlit_drawable_canvas import st_canvas

# --- CONEXIÓN DIRECTA (Tus credenciales de Supabase) ---
SUPABASE_URL = "https://cpxudkbukctfxvgoagla.supabase.co"
SUPABASE_KEY = "sb_publishable_vzYfQr8hxB1PAFB3bNPwIg_ZkY3sN_0"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- FUNCIÓN DE CARGA ---
def cargar(tabla):
    try:
        res = supabase.table(tabla).select("*").eq("creado_por", st.session_state.user).execute()
        return res.data if res.data else []
    except Exception:
        return []

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="CORMAIN CMMS PRO", layout="wide")
if 'auth' not in st.session_state: st.session_state.auth = False

# --- LOGIN ---
if not st.session_state.auth:
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
    # --- MENÚ LATERAL ---
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

    # --- PÁGINA INICIO: PANEL DE CONTROL (3 Gráficos) ---
    if st.session_state.menu == "🏠 Inicio":
        st.title("📊 Panel de Control Operativo")
        df = pd.DataFrame(cargar("ordenes"))
        if not df.empty:
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Órdenes Totales", len(df))
            c2.metric("En Proceso", len(df[df['estado'] == 'Proceso']))
            c3.metric("Finalizadas", len(df[df['estado'] == 'Finalizada']))
            if 'costo' in df.columns:
                c4.metric("Inversión Total", f"${df['costo'].sum():,.2f}")
            
            st.divider()
            import plotly.express as px
            col_a, col_b, col_c = st.columns(3)
            
            fig1 = px.pie(df, names='estado', hole=0.4, title="Estado de Órdenes")
            col_a.plotly_chart(fig1, use_container_width=True)
            
            fig2 = px.pie(df, names='prioridad', hole=0.4, title="Por Prioridad")
            col_b.plotly_chart(fig2, use_container_width=True)
            
            fig3 = px.pie(df, names='tipo_tarea', hole=0.4, title="Tipo de Tarea")
            col_c.plotly_chart(fig3, use_container_width=True)
        else: st.info("Sin datos registrados.")

    # --- PÁGINA PERSONAL (9 Campos + Firma) ---
    elif st.session_state.menu == "👥 Personal":
        st.header("Gestión de Personal")
        with st.form("f_p"):
            c1, c2, c3 = st.columns(3)
            nom = c1.text_input("Nombre")
            ape = c2.text_input("Apellido")
            cod_e = c3.text_input("Código Empleado")
            mail = c1.text_input("Email")
            car = c2.text_input("Cargo")
            esp = c3.text_input("Especialidad")
            cl1 = c1.selectbox("Clasificación", ["Interno", "Externo"])
            dir_p = c2.text_input("Dirección")
            
            st.write("✒️ **Firma Maestra del Técnico**")
            st_canvas(stroke_width=2, stroke_color="black", height=100, width=400, key="p_sign")
            
            if st.form_submit_button("Guardar Personal"):
                supabase.table("personal").insert({
                    "nombre": nom, "apellido": ape, "codigo_empleado": cod_e, 
                    "email": mail, "cargo": car, "especialidad": esp,
                    "clasificacion1": cl1, "direccion": dir_p, "firma_path": "REGISTRADA",
                    "creado_por": st.session_state.user
                }).execute()
                st.rerun()
        st.dataframe(pd.DataFrame(cargar("personal")), use_container_width=True)

    # --- PÁGINA MAQUINARIA (10 Campos) ---
    elif st.session_state.menu == "⚙️ Maquinaria":
        st.header("Ficha Técnica de Equipos")
        with st.form("f_m"):
            c1, c2, c3 = st.columns(3)
            nm = c1.text_input("Nombre Máquina")
            cod = c2.text_input("Código")
            ubi = c3.text_input("Ubicación")
            ser = c1.text_input("Serial")
            fab = c2.text_input("Fabricante")
            mod = c3.text_input("Modelo")
            est = c1.selectbox("Estado", ["Operativa", "Falla", "Mantenimiento"])
            hu = c2.number_input("Horas Uso", 0)
            fc = c3.date_input("Fecha Compra")
            obs = st.text_area("Notas Técnicas")
            
            if st.form_submit_button("Registrar Equipo"):
                supabase.table("maquinas").insert({
                    "nombre_maquina": nm, "codigo": cod, "ubicacion": ubi, 
                    "estado": est, "serial": ser, "fabricante": fab, "modelo": mod, 
                    "horas_uso": hu, "fecha_compra": str(fc), "apartado1": obs,
                    "creado_por": st.session_state.user
                }).execute()
                st.rerun()
        st.dataframe(pd.DataFrame(cargar("maquinas")), use_container_width=True)

    # --- PÁGINA ÓRDENES DE TRABAJO ---
    elif st.session_state.menu == "📑 Órdenes de Trabajo":
        st.header("Gestión de OP")
        m_data = cargar("maquinas")
        p_data = cargar("personal")
        m_list = [f"{m['nombre_maquina']} ({m['codigo']})" for m in m_data]
        p_list = [f"{p['nombre']} {p['apellido']}" for p in p_data]
        
        with st.expander("➕ Lanzar Nueva OP"):
            with st.form("f_op"):
                desc = st.text_area("Descripción")
                c1, c2, c3 = st.columns(3)
                mq = c1.selectbox("Máquina", m_list) if m_list else c1.text_input("Máquina")
                tc = c2.selectbox("Técnico", p_list) if p_list else c2.text_input("Técnico")
                pr = c3.selectbox("Prioridad", ["ALTA", "MEDIA", "BAJA"])
                tt = st.selectbox("Tipo", ["Correctiva", "Preventiva"])
                cos = st.number_input("Costo Estimado ($)", 0.0)
                
                if st.form_submit_button("Lanzar"):
                    supabase.table("ordenes").insert({
                        "descripcion": desc, "id_maquina": mq, "id_tecnico": tc, 
                        "prioridad": pr, "costo": cos, "tipo_tarea": tt,
                        "estado": "Proceso", "creado_por": st.session_state.user
                    }).execute()
                    st.rerun()

        st.divider()
        df_o = pd.DataFrame(cargar("ordenes"))
        if not df_o.empty:
            pasos = {"Proceso": "Realizada", "Realizada": "Revisada", "Revisada": "Finalizada"}
            for est_actual in ["Proceso", "Realizada", "Revisada", "Finalizada"]:
                st.subheader(f"📍 {est_actual}")
                filas = df_o[df_o['estado'] == est_actual]
                for _, row in filas.iterrows():
                    with st.container(border=True):
                        c1, c2, c3 = st.columns([3, 1, 1])
                        c1.write(f"**{row['id_maquina']}** | {row['prioridad']}")
                        c1.caption(f"🔧 {row['descripcion']}")
                        
                        if est_actual == "Revisada":
                            st.write("✒️ **Firma de Aprobación del Jefe**")
                            st_canvas(stroke_width=2, stroke_color="black", height=80, width=250, key=f"f_{row['id']}")
                            if c2.button("Finalizar", key=f"fbtn_{row['id']}"):
                                supabase.table("ordenes").update({"estado": "Finalizada", "firma_jefe": "OK"}).eq("id", row['id']).execute()
                                st.rerun()
                        elif est_actual in pasos:
                            if c2.button(f"➡️ Mover a {pasos[est_actual]}", key=f"av_{row['id']}"):
                                supabase.table("ordenes").update({"estado": pasos[est_actual]}).eq("id", row['id']).execute()
                                st.rerun()
                        
                        if c3.button("🗑️ Eliminar", key=f"del_{row['id']}"):
                            supabase.table("ordenes").delete().eq("id", row['id']).execute()
                            st.rerun()
