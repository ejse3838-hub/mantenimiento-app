import streamlit as st
import pandas as pd
from supabase import create_client, Client
from streamlit_drawable_canvas import st_canvas

# --- CONEXIÓN ---
url = st.secrets["connections"]["supabase"]["SUPABASE_URL"]
key = st.secrets["connections"]["supabase"]["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

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

    # --- 1. INICIO (DASHBOARD COMPLETO) ---
    if st.session_state.menu == "🏠 Inicio":
        st.title("📊 Panel de Control Operativo")
        df = pd.DataFrame(cargar("ordenes"))
        if not df.empty:
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Total Órdenes", len(df))
            c2.metric("En Proceso", len(df[df['estado'] == 'Proceso']))
            c3.metric("Finalizadas", len(df[df['estado'] == 'Finalizada']))
            if 'costo' in df.columns:
                c4.metric("Inversión Total", f"${df['costo'].sum():,.2f}")
            
            st.divider()
            import plotly.express as px
            col_a, col_b = st.columns(2)
            fig1 = px.pie(df, names='estado', title="Distribución por Estado", hole=0.4)
            col_a.plotly_chart(fig1, use_container_width=True)
            
            fig2 = px.bar(df, x='prioridad', color='prioridad', title="Órdenes por Prioridad")
            col_b.plotly_chart(fig2, use_container_width=True)
        else: st.info("Sin datos para mostrar estadísticas.")

    # --- 2. PERSONAL (RESTAURADO 9 CAMPOS + FIRMA) ---
    elif st.session_state.menu == "👥 Personal":
        st.header("Gestión de Talento Humano")
        with st.form("f_personal_full"):
            c1, c2, c3 = st.columns(3)
            nom = c1.text_input("Nombre")
            ape = c2.text_input("Apellido")
            cod_e = c3.text_input("Código Empleado")
            
            mail = c1.text_input("Email")
            car = c2.text_input("Cargo")
            esp = c3.text_input("Especialidad")
            
            cl1 = c1.selectbox("Clasificación 1", ["Interno", "Externo"])
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

    # --- 3. MAQUINARIA (RESTAURADO 12 CAMPOS) ---
    elif st.session_state.menu == "⚙️ Maquinaria":
        st.header("Ficha Técnica de Activos")
        with st.form("f_maq_full"):
            c1, c2, c3 = st.columns(3)
            nm = c1.text_input("Nombre Máquina")
            cod = c2.text_input("Código")
            ubi = c3.text_input("Ubicación")
            
            ser = c1.text_input("Serial")
            fab = c2.text_input("Fabricante")
            mod = c3.text_input("Modelo")
            
            est = c1.selectbox("Estado", ["Operativa", "Falla", "Mantenimiento"])
            hu = c2.number_input("Horas Uso", min_value=0)
            fc = c3.date_input("Fecha Compra")
            
            a1 = st.text_area("Apartado 1 (Especificaciones)")
            a2 = st.text_area("Apartado 2 (Notas/Garantía)")
            
            if st.form_submit_button("Registrar Equipo"):
                supabase.table("maquinas").insert({
                    "nombre_maquina": nm, "codigo": cod, "ubicacion": ubi, "estado": est,
                    "serial": ser, "fabricante": fab, "modelo": mod, "horas_uso": hu,
                    "fecha_compra": str(fc), "apartado1": a1, "apartado2": a2,
                    "creado_por": st.session_state.user
                }).execute()
                st.rerun()
        st.dataframe(pd.DataFrame(cargar("maquinas")), use_container_width=True)

    # --- 4. ÓRDENES (REVISADO CON TUS 15 COLUMNAS) ---
    elif st.session_state.menu == "📑 Órdenes de Trabajo":
        st.header("Gestión de Órdenes")
        m_data, p_data = cargar("maquinas"), cargar("personal")
        m_opts = [f"{m['nombre_maquina']} ({m['codigo']})" for m in m_data] if m_data else ["Registrar máquinas"]
        p_opts = [f"{p['nombre']} {p['apellido']}" for p in p_data] if p_data else ["Registrar personal"]

        with st.expander("➕ Lanzar Nueva OP"):
            with st.form("f_op"):
                desc = st.text_area("Descripción de la Falla/Tarea")
                c1, c2, c3 = st.columns(3)
                mq, tc, pr = c1.selectbox("Máquina", m_opts), c2.selectbox("Técnico", p_opts), c3.selectbox("Prioridad", ["🔴 ALTA", "🟡 MEDIA", "🟢 BAJA"])
                
                c4, c5, c6 = st.columns(3)
                tt, fr, dur = c4.selectbox("Tipo Tarea", ["Correctiva", "Preventiva"]), c5.selectbox("Frecuencia", ["Mensual", "Semanal", "Única"]), c6.text_input("Duración Estimada", "1h")
                
                c7, c8, c9 = st.columns(3)
                paro, her, cos = c7.selectbox("Requiere Paro", ["No", "Sí"]), c8.text_input("Herramientas"), c9.number_input("Costo Estimado", 0.0)
                ins = st.text_input("Insumos/Repuestos")

                if st.form_submit_button("Lanzar"):
                    supabase.table("ordenes").insert({
                        "descripcion": desc, "id_maquina": mq, "id_tecnico": tc, "estado": "Proceso",
                        "tipo_tarea": tt, "frecuencia": fr, "duracion_estimada": dur, "requiere_paro": paro,
                        "herramientas": her, "prioridad": pr, "insumos": ins, "costo": cos,
                        "creado_por": st.session_state.user
                    }).execute()
                    st.rerun()

        st.divider()
        df_o = pd.DataFrame(cargar("ordenes"))
        if not df_o.empty:
            pasos = {"Proceso": "Realizada", "Realizada": "Revisada", "Revisada": "Finalizada"}
            for est_actual in ["Proceso", "Realizada", "Revisada
