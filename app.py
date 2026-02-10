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
        u = st.text_input("Usuario")
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
    menu = st.sidebar.radio("Navegación", ["🏠 Inicio", "👥 Personal", "⚙️ Maquinaria", "📑 Órdenes de Trabajo"])
    if st.sidebar.button("🚪 Cerrar Sesión"):
        st.session_state.auth = False
        st.rerun()

    # --- 1. INICIO (DASHBOARD COMPLETO) ---
    if menu == "🏠 Inicio":
        st.title("📊 Panel de Control Operativo")
        df = pd.DataFrame(cargar("ordenes"))
        if not df.empty:
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Total Órdenes", len(df))
            c2.metric("En Proceso", len(df[df['estado'] == 'Proceso']))
            c3.metric("Finalizadas", len(df[df['estado'] == 'Finalizada']))
            if 'costo' in df.columns: c4.metric("Inversión Total", f"${df['costo'].sum():,.2f}")
            
            import plotly.express as px
            col_a, col_b = st.columns(2)
            fig1 = px.pie(df, names='estado', title="Distribución por Estado", hole=0.4)
            col_a.plotly_chart(fig1, use_container_width=True)
            fig2 = px.bar(df, x='prioridad', title="Órdenes por Prioridad")
            col_b.plotly_chart(fig2, use_container_width=True)
        else: st.info("Sin datos registrados.")

    # --- 2. PERSONAL (9 CAMPOS + FIRMA) ---
    elif menu == "👥 Personal":
        st.header("Gestión de Personal")
        with st.form("f_p"):
            c1, c2, c3 = st.columns(3)
            nom, ape = c1.text_input("Nombre"), c2.text_input("Apellido")
            cod_e, car = c3.text_input("Código"), c1.text_input("Cargo")
            esp, cl1 = c2.text_input("Especialidad"), c3.selectbox("Clasificación", ["Interno", "Externo"])
            mail, dir_p = c1.text_input("Email"), c2.text_input("Dirección")
            st.write("✒️ **Firma Maestra**")
            st_canvas(stroke_width=2, stroke_color="black", height=100, width=400, key="p_sign")
            if st.form_submit_button("Guardar"):
                supabase.table("personal").insert({
                    "nombre": nom, "apellido": ape, "codigo_empleado": cod_e, "email": mail,
                    "cargo": car, "especialidad": esp, "clasificacion1": cl1, "direccion": dir_p,
                    "firma_path": "REGISTRADA", "creado_por": st.session_state.user
                }).execute()
                st.rerun()
        st.dataframe(pd.DataFrame(cargar("personal")), use_container_width=True)

    # --- 3. MAQUINARIA (12 CAMPOS) ---
    elif menu == "⚙️ Maquinaria":
        st.header("Ficha Técnica")
        with st.form("f_m"):
            c1, c2, c3 = st.columns(3)
            nm, cod, ubi = c1.text_input("Máquina"), c2.text_input("Código"), c3.text_input("Ubicación")
            ser, fab, mod = c1.text_input("Serial"), c2.text_input("Fabricante"), c3.text_input("Modelo")
            est = c1.selectbox("Estado", ["Operativa", "Falla", "Mantenimiento"])
            hu = c2.number_input("Horas Uso", min_value=0)
            fc = c3.date_input("Fecha Compra")
            a1, a2 = st.text_area("Apartado 1"), st.text_area("Apartado 2")
            if st.form_submit_button("Registrar"):
                supabase.table("maquinas").insert({
                    "nombre_maquina": nm, "codigo": cod, "ubicacion": ubi, "estado": est,
                    "serial": ser, "fabricante": fab, "modelo": mod, "horas_uso": hu,
                    "fecha_compra": str(fc), "apartado1": a1, "apartado2": a2,
                    "creado_por": st.session_state.user
                }).execute()
                st.rerun()
        st.dataframe(pd.DataFrame(cargar("maquinas")), use_container_width=True)

    # --- 4. ÓRDENES (15 CAMPOS) ---
    elif menu == "📑 Órdenes de Trabajo":
        st.header("Gestión de OP")
        m_list = [f"{m['nombre_maquina']} ({m['codigo']})" for m in cargar("maquinas")]
        p_list = [p['nombre'] for p in cargar("personal")]
        with st.expander("➕ Lanzar Nueva OP"):
            with st.form("f_op"):
                desc = st.text_area("Descripción")
                c1, c2, c3 = st.columns(3)
                mq, tc, pr = c1.selectbox("Máquina", m_list), c2.selectbox("Técnico", p_list), c3.selectbox("Prioridad", ["🔴 ALTA", "🟡 MEDIA", "🟢 BAJA"])
                c4, c5, c6 = st.columns(3)
                tt, fr, dur = c4.selectbox("Tipo", ["Correctiva", "Preventiva"]), c5.selectbox("Frecuencia", ["Mensual", "Semanal"]), c6.text_input("Duración", "1h")
                c7, c8, c9 = st.columns(3)
                paro, her, cos = c7.selectbox("Paro", ["No", "Sí"]), c8.text_input("Herramientas"), c9.number_input("Costo", 0.0)
                ins = st.text_input("Insumos")
                if st.form_submit_button("Lanzar"):
                    supabase.table("ordenes").insert({
                        "descripcion": desc, "id_maquina": mq, "id_tecnico": tc, "estado": "Proceso",
                        "tipo_tarea": tt, "frecuencia": fr, "duracion_estimada": dur, "requiere_paro": paro,
                        "herramientas": her, "prioridad": pr, "insumos": ins, "costo": cos,
                        "creado_por": st.session_state.user
                    }).execute()
                    st.rerun()
        
        df_o = pd.DataFrame(cargar("ordenes"))
        if not df_o.empty:
            for _, row in df_o.iterrows():
                with st.container(border=True):
                    st.write(f"**{row['id_maquina']}** | {row['prioridad']}")
                    st.caption(f"🔧 {row['descripcion']}")
                    st.write("✒️ **Firma Jefe**")
                    st_canvas(stroke_width=2, stroke_color="black", height=80, width=250, key=f"f_{row['id']}")
                    if st.button("🗑️ Eliminar", key=f"del_{row['id']}"):
                        supabase.table("ordenes").delete().eq("id", row['id']).execute()
                        st.rerun()
