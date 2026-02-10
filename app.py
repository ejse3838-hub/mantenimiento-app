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

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="CORMAIN CMMS PRO", layout="wide")
if 'auth' not in st.session_state: st.session_state.auth = False

# --- LOGIN ---
if not st.session_state.auth:
    tab1, tab2 = st.tabs(["🔑 Iniciar Sesión", "📝 Registrarse"])
    with tab1:
        u = st.text_input("Usuario (Email)")
        p = st.text_input("Clave", type="password")
        if st.button("Entrar", use_container_width=True):
            res = supabase.table("usuarios").select("*").eq("email", u).eq("password", p).execute()
            if res.data: 
                st.session_state.auth = True
                st.session_state.user = res.data[0]['email']
                st.rerun()
            else: st.error("Datos incorrectos")
    with tab2:
        nu, np = st.text_input("Nuevo Email"), st.text_input("Nueva Clave", type="password")
        if st.button("Crear Cuenta", use_container_width=True):
            supabase.table("usuarios").insert({"email": nu, "password": np, "creado_por": nu}).execute()
            st.success("¡Cuenta creada!")

else:
    # --- MENÚ LATERAL ---
    st.sidebar.title(f"👤 {st.session_state.user}")
    menu = st.sidebar.radio("Menú Principal", ["🏠 Inicio", "👥 Personal", "⚙️ Maquinaria", "📑 Órdenes de Trabajo"])
    st.sidebar.divider()
    if st.sidebar.button("🚪 Cerrar Sesión", use_container_width=True):
        st.session_state.auth = False
        st.rerun()

    # --- 1. INICIO (DASHBOARD TOTAL) ---
    if menu == "🏠 Inicio":
        st.title("📊 Panel de Control e Indicadores")
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
            
            fig1 = px.pie(df, names='estado', title="Distribución de Órdenes por Estado", hole=0.4)
            col_a.plotly_chart(fig1, use_container_width=True)
            
            fig2 = px.bar(df, x='prioridad', color='prioridad', title="Carga de Trabajo por Prioridad")
            col_b.plotly_chart(fig2, use_container_width=True)
            
            if 'tipo_tarea' in df.columns:
                fig3 = px.pie(df, names='tipo_tarea', title="Mantenimiento: Correctivo vs Preventivo")
                st.plotly_chart(fig3, use_container_width=True)
        else: st.info("No hay órdenes registradas para mostrar estadísticas.")

    # --- 2. PERSONAL (9 CAMPOS + FIRMA) ---
    elif menu == "👥 Personal":
        st.header("Gestión de Personal Técnico")
        with st.form("f_personal"):
            c1, c2, c3 = st.columns(3)
            nom = c1.text_input("Nombre")
            ape = c2.text_input("Apellido")
            cod_e = c3.text_input("Código de Empleado")
            
            mail = c1.text_input("Email")
            car = c2.text_input("Cargo")
            esp = c3.text_input("Especialidad")
            
            cl1 = c1.selectbox("Clasificación", ["Interno", "Externo / Contratista"])
            dir_p = c2.text_input("Dirección de Residencia")
            
            st.write("✒️ **Firma Digital del Técnico**")
            st_canvas(stroke_width=2, stroke_color="black", height=100, width=400, key="p_sign")
            
            if st.form_submit_button("Guardar Registro"):
                supabase.table("personal").insert({
                    "nombre": nom, "apellido": ape, "codigo_empleado": cod_e,
                    "email": mail, "cargo": car, "especialidad": esp,
                    "clasificacion1": cl1, "direccion": dir_p, "firma_path": "SI",
                    "creado_por": st.session_state.user
                }).execute()
                st.rerun()
        st.dataframe(pd.DataFrame(cargar("personal")), use_container_width=True)

    # --- 3. MAQUINARIA (12 CAMPOS) ---
    elif menu == "⚙️ Maquinaria":
        st.header("Ficha Técnica de Equipos y Activos")
        with st.form("f_maq"):
            c1, c2, c3 = st.columns(3)
            nm = c1.text_input("Nombre de la Máquina")
            cod = c2.text_input("Código Interno")
            ubi = c3.text_input("Ubicación en Planta")
            
            ser = c1.text_input("Número de Serial")
            fab = c2.text_input("Fabricante")
            mod = c3.text_input("Modelo")
            
            est = c1.selectbox("Estado Actual", ["Operativa", "Falla Crítica", "Mantenimiento"])
            hu = c2.number_input("Horas de Uso Acumuladas", min_value=0)
            fc = c3.date_input("Fecha de Adquisición")
            
            a1 = st.text_area("Apartado 1: Especificaciones Mecánicas/Eléctricas")
            a2 = st.text_area("Apartado 2: Observaciones de Seguridad")
            
            if st.form_submit_button("Registrar Activo"):
                supabase.table("maquinas").insert({
                    "nombre_maquina": nm, "codigo": cod, "ubicacion": ubi, "estado": est,
                    "serial": ser, "fabricante": fab, "modelo": mod, "horas_uso": hu,
                    "fecha_compra": str(fc), "apartado1": a1, "apartado2": a2,
                    "creado_por": st.session_state.user
                }).execute()
                st.rerun()
        st.dataframe(pd.DataFrame(cargar("maquinas")), use_container_width=True)

    # --- 4. ÓRDENES (15 CAMPOS + FLUJO DE FIRMAS) ---
    elif menu == "📑 Órdenes de Trabajo":
        st.header("Gestión de Órdenes de Trabajo")
        m_data, p_data = cargar("maquinas"), cargar("personal")
        m_opts = [f"{m['nombre_maquina']} ({m['codigo']})" for m in m_data] if m_data else ["Sin máquinas"]
        p_opts = [f"{p['nombre']} {p['apellido']}" for p in p_data] if p_data else ["Sin personal"]

        with st.expander("➕ Lanzar Nueva Orden de Producción"):
            with st.form("f_op"):
                desc = st.text_area("Descripción de la Tarea")
                c1, c2, c3 = st.columns(3)
                mq = c1.selectbox("Equipo", m_opts)
                tc = c2.selectbox("Responsable", p_opts)
                pr = c3.selectbox("Prioridad", ["🔴 ALTA", "🟡 MEDIA", "🟢 BAJA"])
                
                c4, c5, c6 = st.columns(3)
                tt = c4.selectbox("Tipo", ["Correctiva", "Preventiva", "Predictiva"])
                fr = c5.selectbox("Frecuencia", ["Única", "Semanal", "Mensual", "Anual"])
                dur = c6.text_input("Tiempo Estimado", "1h")
                
                c7, c8, c9 = st.columns(3)
                paro = c7.selectbox("Requiere Parada", ["No", "Sí"])
                her = c8.text_input("Herramientas Necesarias")
                cos = c9.number_input("Costo Estimado ($)", 0.0)
                ins = st.text_input("Insumos / Repuestos")

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
            for _, row in df_o.iterrows():
                with st.container(border=True):
                    c1, c2 = st.columns([3, 1])
                    c1.write(f"### {row['id_maquina']} | {row['prioridad']}")
                    c1.write(f"**Descripción:** {row['descripcion']}")
                    st.write("✒️ **Validación Jefe de Planta**")
                    st_canvas(stroke_width=2, stroke_color="black", height=80, width=250, key=f"f_{row['id']}")
                    if st.button("🗑️ Eliminar Orden", key=f"del_{row['id']}"):
                        supabase.table("ordenes").delete().eq("id", row['id']).execute()
                        st.rerun()
