import streamlit as st
import pandas as pd
from supabase import create_client, Client
from streamlit_drawable_canvas import st_canvas

# --- CONEXIÓN AUTOMÁTICA ---
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

# --- FUNCIÓN DE CARGA ---
def cargar(tabla):
    try:
        res = supabase.table(tabla).select("*").eq("creado_por", st.session_state.user).execute()
        return res.data if res.data else []
    except: return []

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="CORMAIN CMMS PRO", layout="wide")
if 'auth' not in st.session_state: st.session_state.auth = False

# --- ACCESO ---
if not st.session_state.auth:
    st.title("🔐 Sistema CORMAIN - Acceso")
    u = st.text_input("Usuario")
    p = st.text_input("Contraseña", type="password")
    if st.button("Iniciar Sesión"):
        res = supabase.table("usuarios").select("*").eq("email", u).eq("password", p).execute()
        if res.data:
            st.session_state.auth = True
            st.session_state.user = res.data[0]['email']
            st.rerun()
        else: st.error("Credenciales incorrectas")
else:
    # --- INTERFAZ ---
    st.sidebar.title(f"👤 {st.session_state.user}")
    menu = st.sidebar.radio("Navegación", ["🏠 Inicio", "👥 Personal", "⚙️ Maquinaria", "📑 Órdenes"])
    if st.sidebar.button("Cerrar Sesión"):
        st.session_state.auth = False
        st.rerun()

    # --- 1. INICIO (DASHBOARD COMPLETO) ---
    if menu == "🏠 Inicio":
        st.title("📊 Panel de Control Operativo")
        df = pd.DataFrame(cargar("ordenes"))
        if not df.empty:
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Órdenes", len(df))
            c2.metric("En Proceso", len(df[df['estado'] == 'Proceso']))
            c3.metric("Finalizadas", len(df[df['estado'] == 'Finalizada']))
            if 'costo' in df.columns: c4.metric("Inversión", f"${df['costo'].sum():,.2f}")
            
            import plotly.express as px
            g1, g2, g3 = st.columns(3)
            g1.plotly_chart(px.pie(df, names='estado', title="Por Estado", hole=0.4), use_container_width=True)
            g2.plotly_chart(px.pie(df, names='prioridad', title="Por Prioridad", hole=0.4), use_container_width=True)
            if 'tipo_tarea' in df.columns:
                g3.plotly_chart(px.pie(df, names='tipo_tarea', title="Mantenimiento", hole=0.4), use_container_width=True)
        else: st.info("Sin datos registrados.")

    # --- 2. PERSONAL (9 CAMPOS + FIRMA) ---
    elif menu == "👥 Personal":
        st.header("Gestión de Personal")
        with st.form("f_p"):
            c1, c2, c3 = st.columns(3)
            nom, ape, cod = c1.text_input("Nombre"), c2.text_input("Apellido"), c3.text_input("Código Empleado")
            mai, car, esp = c1.text_input("Email"), c2.text_input("Cargo"), c3.text_input("Especialidad")
            cl1, dir_p = c1.selectbox("Clasificación", ["Interno", "Externo"]), c2.text_input("Dirección")
            st.write("✒️ **Firma Digital**")
            st_canvas(stroke_width=2, stroke_color="black", height=100, width=400, key="p_sign")
            if st.form_submit_button("Guardar"):
                supabase.table("personal").insert({
                    "nombre": nom, "apellido": ape, "codigo_empleado": cod, "email": mai,
                    "cargo": car, "especialidad": esp, "clasificacion1": cl1, "direccion": dir_p,
                    "firma_path": "SI", "creado_por": st.session_state.user
                }).execute()
                st.rerun()
        st.dataframe(pd.DataFrame(cargar("personal")))

    # --- 3. MAQUINARIA (12 CAMPOS RESTAURADOS) ---
    elif menu == "⚙️ Maquinaria":
        st.header("Ficha Técnica de Equipos")
        with st.form("f_m"):
            c1, c2, c3 = st.columns(3)
            nm, cd, ub = c1.text_input("Nombre Máquina"), c2.text_input("Código"), c3.text_input("Ubicación")
            sr, fb, mo = c1.text_input("Serial"), c2.text_input("Fabricante"), c3.text_input("Modelo")
            es, hu = c1.selectbox("Estado", ["Operativa", "Falla"]), c2.number_input("Horas Uso", 0)
            fc = c3.date_input("Fecha Compra")
            a1, a2 = st.text_area("Notas Técnicas"), st.text_area("Observaciones")
            if st.form_submit_button("Registrar Equipo"):
                supabase.table("maquinas").insert({
                    "nombre_maquina": nm, "codigo": cd, "ubicacion": ub, "estado": es,
                    "serial": sr, "fabricante": fb, "modelo": mo, "horas_uso": hu,
                    "fecha_compra": str(fc), "apartado1": a1, "apartado2": a2,
                    "creado_por": st.session_state.user
                }).execute()
                st.rerun()
        st.dataframe(pd.DataFrame(cargar("maquinas")))

    # --- 4. ÓRDENES (COMPLETO) ---
    elif menu == "📑 Órdenes":
        st.header("Gestión de Órdenes de Trabajo")
        with st.expander("➕ Lanzar Nueva OP"):
            with st.form("f_o"):
                desc = st.text_area("Descripción")
                c1, c2 = st.columns(2)
                mq, pr = c1.text_input("Máquina (Código)"), c2.selectbox("Prioridad", ["ALTA", "BAJA"])
                if st.form_submit_button("Lanzar"):
                    supabase.table("ordenes").insert({
                        "descripcion": desc, "id_maquina": mq, "estado": "Proceso",
                        "prioridad": pr, "creado_por": st.session_state.user
                    }).execute()
                    st.rerun()
        
        for r in cargar("ordenes"):
            with st.container(border=True):
                st.write(f"**{r['id_maquina']}** | {r['prioridad']}")
                st.caption(r['descripcion'])
                st.write("✒️ **Validación Jefe**")
                st_canvas(stroke_width=2, stroke_color="black", height=80, width=250, key=f"f_{r['id']}")
                if st.button("Eliminar", key=f"d_{r['id']}"):
                    supabase.table("ordenes").delete().eq("id", r['id']).execute()
                    st.rerun()
