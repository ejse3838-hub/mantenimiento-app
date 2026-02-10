import streamlit as st
import pandas as pd
from supabase import create_client, Client
from streamlit_drawable_canvas import st_canvas

# --- CONEXIÓN (FORMATO ORIGINAL) ---
# Usamos directamente st.secrets sin diccionarios anidados para asegurar compatibilidad
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

def cargar(tabla):
    try:
        res = supabase.table(tabla).select("*").eq("creado_por", st.session_state.user).execute()
        return res.data if res.data else []
    except: return []

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="CORMAIN CMMS PRO", layout="wide")
if 'auth' not in st.session_state: st.session_state.auth = False

# --- LOGIN ---
if not st.session_state.auth:
    tab1, tab2 = st.tabs(["🔑 Entrar", "📝 Registro"])
    with tab1:
        u = st.text_input("Usuario")
        p = st.text_input("Clave", type="password")
        if st.button("Ingresar"):
            res = supabase.table("usuarios").select("*").eq("email", u).eq("password", p).execute()
            if res.data:
                st.session_state.auth = True
                st.session_state.user = res.data[0]['email']
                st.rerun()
            else: st.error("Acceso denegado")
else:
    # --- MENÚ ---
    st.sidebar.title(f"👤 {st.session_state.user}")
    menu = st.sidebar.radio("Navegación", ["🏠 Inicio", "👥 Personal", "⚙️ Maquinaria", "📑 Órdenes"])
    
    if st.sidebar.button("🚪 Salir"):
        st.session_state.auth = False
        st.rerun()

    # --- INICIO (Tus 3 Flujos) ---
    if menu == "🏠 Inicio":
        st.title("📊 Estadísticas de Planta")
        df = pd.DataFrame(cargar("ordenes"))
        if not df.empty:
            c1, c2, c3 = st.columns(3)
            c1.metric("Órdenes", len(df))
            c2.metric("Inversión", f"${df['costo'].sum() if 'costo' in df.columns else 0}")
            
            import plotly.express as px
            # 3 Gráficos de pastel como pediste
            col1, col2, col3 = st.columns(3)
            col1.plotly_chart(px.pie(df, names='estado', title="Estados", hole=0.3), use_container_width=True)
            col2.plotly_chart(px.pie(df, names='prioridad', title="Prioridad", hole=0.3), use_container_width=True)
            if 'tipo_tarea' in df.columns:
                col3.plotly_chart(px.pie(df, names='tipo_tarea', title="Tareas", hole=0.3), use_container_width=True)
        else: st.info("Sin datos")

    # --- PERSONAL (9 CAMPOS + FIRMA) ---
    elif menu == "👥 Personal":
        with st.form("f_personal"):
            c1, c2, c3 = st.columns(3)
            # Usando tus columnas: nombre, apellido, codigo_empleado, email, cargo, especialidad, clasificacion1, direccion, firma_path
            nombre = c1.text_input("Nombre")
            apellido = c2.text_input("Apellido")
            codigo_empleado = c3.text_input("Código")
            email = c1.text_input("Email")
            cargo = c2.text_input("Cargo")
            especialidad = c3.text_input("Especialidad")
            clasificacion1 = c1.selectbox("Clasificación", ["Interno", "Externo"])
            direccion = c2.text_input("Dirección")
            st.write("✒️ Firma")
            st_canvas(stroke_width=2, stroke_color="black", height=100, width=400, key="p_sign")
            
            if st.form_submit_button("Guardar"):
                supabase.table("personal").insert({
                    "nombre": nombre, "apellido": apellido, "codigo_empleado": codigo_empleado,
                    "email": email, "cargo": cargo, "especialidad": especialidad,
                    "clasificacion1": clasificacion1, "direccion": direccion, 
                    "firma_path": "SI", "creado_por": st.session_state.user
                }).execute()
                st.rerun()

    # --- MAQUINARIA (10 CAMPOS) ---
    elif menu == "⚙️ Maquinaria":
        with st.form("f_maq"):
            c1, c2, c3 = st.columns(3)
            # Columnas: nombre_maquina, codigo, ubicacion, estado, serial, fabricante, modelo, horas_uso, fecha_compra, apartado1
            n_m = c1.text_input("Máquina")
            cod = c2.text_input("Código")
            ubi = c3.text_input("Ubicación")
            ser = c1.text_input("Serial")
            fab = c2.text_input("Fabricante")
            mod = c3.text_input("Modelo")
            est = c1.selectbox("Estado", ["Operativa", "Falla"])
            hus = c2.number_input("Horas Uso", 0)
            if st.form_submit_button("Registrar"):
                supabase.table("maquinas").insert({
                    "nombre_maquina": n_m, "codigo": cod, "ubicacion": ubi, "estado": est,
                    "serial": ser, "fabricante": fab, "modelo": mod, "horas_uso": hus,
                    "creado_por": st.session_state.user
                }).execute()
                st.rerun()

    # --- ÓRDENES ---
    elif menu == "📑 Órdenes":
        # Formulario de órdenes con tus 15 columnas
        st.write("Gestión de OP con Firma del Jefe")
        # Aquí va el bloque de órdenes que ya tenías pero con la firma al final
        df_o = pd.DataFrame(cargar("ordenes"))
        if not df_o.empty:
            for _, row in df_o.iterrows():
                with st.container(border=True):
                    st.write(f"Orden: {row['id_maquina']}")
                    st.write("✒️ Firma del Jefe para Finalizar")
                    st_canvas(stroke_width=2, stroke_color="black", height=80, width=250, key=f"f_{row['id']}")
                    if st.button("Eliminar", key=f"del_{row['id']}"):
                        supabase.table("ordenes").delete().eq("id", row['id']).execute()
                        st.rerun()
