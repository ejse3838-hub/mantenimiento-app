import streamlit as st
import pandas as pd
from supabase import create_client, Client
from streamlit_drawable_canvas import st_canvas

# --- CONEXIÓN DIRECTA ---
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except Exception as e:
    st.error("Error de configuración en Secrets. Verifica SUPABASE_URL y SUPABASE_KEY.")
    st.stop()

# --- FUNCIÓN DE CARGA ---
def cargar(tabla):
    try:
        res = supabase.table(tabla).select("*").eq("creado_por", st.session_state.user).execute()
        return res.data if res.data else []
    except Exception: return []

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="CORMAIN CMMS PRO", layout="wide")
if 'auth' not in st.session_state: st.session_state.auth = False

# --- LOGIN ---
if not st.session_state.auth:
    tab1, tab2 = st.tabs(["🔑 Iniciar Sesión", "📝 Registro"])
    with tab1:
        u = st.text_input("Usuario")
        p = st.text_input("Clave", type="password")
        if st.button("Entrar"):
            try:
                res = supabase.table("usuarios").select("*").eq("email", u).eq("password", p).execute()
                if res.data:
                    st.session_state.auth = True
                    st.session_state.user = res.data[0]['email']
                    st.rerun()
                else: st.error("Credenciales incorrectas")
            except Exception as e: st.error(f"Error de conexión: {e}")
else:
    # --- MENÚ ---
    st.sidebar.title(f"👤 {st.session_state.user}")
    menu = st.sidebar.radio("Navegación", ["🏠 Inicio", "👥 Personal", "⚙️ Maquinaria", "📑 Órdenes"])
    if st.sidebar.button("🚪 Cerrar Sesión"):
        st.session_state.auth = False
        st.rerun()

    # --- 1. INICIO (DASHBOARD) ---
    if menu == "🏠 Inicio":
        st.title("📊 Panel de Control CORMAIN")
        df = pd.DataFrame(cargar("ordenes"))
        if not df.empty:
            c1, c2, c3 = st.columns(3)
            c1.metric("Órdenes", len(df))
            c2.metric("En Proceso", len(df[df['estado'] == 'Proceso']))
            if 'costo' in df.columns: c3.metric("Inversión Total", f"${df['costo'].sum():,.2f}")
            
            import plotly.express as px
            col_a, col_b = st.columns(2)
            col_a.plotly_chart(px.pie(df, names='estado', hole=0.4, title="Estado de Órdenes"), use_container_width=True)
            col_b.plotly_chart(px.bar(df, x='prioridad', title="Carga por Prioridad"), use_container_width=True)
        else: st.info("Sin datos registrados.")

    # --- 2. PERSONAL (9 CAMPOS) ---
    elif menu == "👥 Personal":
        st.header("Gestión de Personal Técnico")
        with st.form("f_p"):
            c1, c2, c3 = st.columns(3)
            nom, ape, cod = c1.text_input("Nombre"), c2.text_input("Apellido"), c3.text_input("Código Empleado")
            mail, car, esp = c1.text_input("Email"), c2.text_input("Cargo"), c3.text_input("Especialidad")
            cl1, dir_p = c1.selectbox("Clasificación", ["Interno", "Externo"]), c2.text_input("Dirección")
            st.write("✒️ **Firma Digital**")
            st_canvas(stroke_width=2, stroke_color="black", height=100, width=400, key="p_sign")
            if st.form_submit_button("Guardar"):
                supabase.table("personal").insert({
                    "nombre": nom, "apellido": ape, "codigo_empleado": cod, "email": mail,
                    "cargo": car, "especialidad": esp, "clasificacion1": cl1, "direccion": dir_p,
                    "firma_path": "REGISTRADA", "creado_por": st.session_state.user
                }).execute()
                st.rerun()
        st.dataframe(pd.DataFrame(cargar("personal")), use_container_width=True)

    # --- 3. MAQUINARIA (12 CAMPOS) ---
    elif menu == "⚙️ Maquinaria":
        st.header("Ficha Técnica de Equipos")
        with st.form("f_m"):
            c1, c2, c3 = st.columns(3)
            nm, cod, ubi = c1.text_input("Nombre Máquina"), c2.text_input("Código"), c3.text_input("Ubicación")
            ser, fab, mod = c1.text_input("Serial"), c2.text_input("Fabricante"), c3.text_input("Modelo")
            est, hu = c1.selectbox("Estado", ["Operativa", "Falla"]), c2.number_input("Horas Uso", 0)
            fc = c3.date_input("Fecha Compra")
            a1, a2 = st.text_area("Apartado 1"), st.text_area("Apartado 2")
            if st.form_submit_button("Registrar Equipo"):
                supabase.table("maquinas").insert({
                    "nombre_maquina": nm, "codigo": cod, "ubicacion": ubi, "estado": est,
                    "serial": ser, "fabricante": fab, "modelo": mod, "horas_uso": hu,
                    "fecha_compra": str(fc), "apartado1": a1, "apartado2": a2,
                    "creado_por": st.session_state.user
                }).execute()
                st.rerun()
        st.dataframe(pd.DataFrame(cargar("maquinas")), use_container_width=True)

    # --- 4. ÓRDENES (15 CAMPOS) ---
    elif menu == "📑 Órdenes":
        st.header("Órdenes de Trabajo")
        with st.expander("➕ Lanzar Nueva OP"):
            with st.form("f_op"):
                desc = st.text_area("Descripción")
                c1, c2, c3 = st.columns(3)
                mq, pr = c1.text_input("Máquina"), c2.selectbox("Prioridad", ["ALTA", "BAJA"])
                if st.form_submit_button("Lanzar"):
                    supabase.table("ordenes").insert({
                        "descripcion": desc, "id_maquina": mq, "estado": "Proceso",
                        "prioridad": pr, "creado_por": st.session_state.user
                    }).execute()
                    st.rerun()
        
        for row in cargar("ordenes"):
            with st.container(border=True):
                st.write(f"**{row['id_maquina']}** | {row['prioridad']}")
                st.write(row['descripcion'])
                st_canvas(stroke_width=2, stroke_color="black", height=80, width=250, key=f"f_{row['id']}")
                if st.button("🗑️ Eliminar", key=f"del_{row['id']}"):
                    supabase.table("ordenes").delete().eq("id", row['id']).execute()
                    st.rerun()
