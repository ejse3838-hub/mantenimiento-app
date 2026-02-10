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

    # --- PÁGINAS ---
    if st.session_state.menu == "🏠 Inicio":
        st.title("📊 Panel de Control")
        df = pd.DataFrame(cargar("ordenes"))
        if not df.empty:
            c1, c2, c3 = st.columns(3)
            c1.metric("Total Órdenes", len(df))
            c2.metric("En Proceso", len(df[df['estado'] == 'Proceso']))
            if 'costo' in df.columns:
                c3.metric("Inversión Total", f"${df['costo'].sum():,.2f}")
            
            st.divider()
            import plotly.express as px
            g1, g2, g3 = st.columns(3)
            
            # Gráficos circulares restaurados
            g1.plotly_chart(px.pie(df, names='estado', hole=0.4, title="Estado de Órdenes"), use_container_width=True)
            g2.plotly_chart(px.pie(df, names='prioridad', hole=0.4, title="Carga por Prioridad"), use_container_width=True)
            if 'tipo_tarea' in df.columns:
                g3.plotly_chart(px.pie(df, names='tipo_tarea', hole=0.4, title="Tipo de Tarea"), use_container_width=True)
        else: st.info("Sin datos registrados.")

    elif st.session_state.menu == "👥 Personal":
        st.header("Gestión de Personal")
        with st.form("f_p"):
            c1, c2, c3 = st.columns(3)
            n, a = c1.text_input("Nombre"), c2.text_input("Apellido")
            cod_e = c3.text_input("Código Empleado")
            car, esp = c1.text_input("Cargo"), c2.text_input("Especialidad")
            mail = c3.text_input("Email")
            cl1 = c1.selectbox("Clasificación", ["Interno", "Externo"])
            dir_p = c2.text_input("Dirección")
            
            st.write("✒️ **Firma del Técnico**")
            st_canvas(stroke_width=2, stroke_color="black", height=100, width=400, key="p_sign")
            
            if st.form_submit_button("Guardar"):
                supabase.table("personal").insert({
                    "nombre": n, "apellido": a, "cargo": car, "especialidad": esp,
                    "codigo_empleado": cod_e, "email": mail, "clasificacion1": cl1,
                    "direccion": dir_p, "firma_path": "SI",
                    "creado_por": st.session_state.user
                }).execute()
                st.rerun()
        st.dataframe(pd.DataFrame(cargar("personal")), use_container_width=True)

    elif st.session_state.menu == "⚙️ Maquinaria":
        st.header("Ficha Técnica")
        with st.form("f_m"):
            c1, c2, c3 = st.columns(3)
            nm, cod = c1.text_input("Máquina"), c2.text_input("Código")
            ubi = c3.text_input("Ubicación")
            ser, fab = c1.text_input("Serial"), c2.text_input("Fabricante")
            mod = c3.text_input("Modelo")
            est = c1.selectbox("Estado", ["Operativa", "Mantenimiento", "Falla"])
            hu = c2.number_input("Horas Uso", 0)
            fc = c3.date_input("Fecha Compra")
            
            if st.form_submit_button("Registrar"):
                supabase.table("maquinas").insert({
                    "nombre_maquina": nm, "codigo": cod, "ubicacion": ubi, 
                    "estado": est, "serial": ser, "fabricante": fab, "modelo": mod,
                    "horas_uso": hu, "fecha_compra": str(fc),
                    "creado_por": st.session_state.user
                }).execute()
                st.rerun()
        st.dataframe(pd.DataFrame(cargar("maquinas")), use_container_width=True)

    elif st.session_state.menu == "📑 Órdenes de Trabajo":
        st.header("Gestión de OP")
        m_list = [f"{m['nombre_maquina']} ({m['codigo']})" for m in cargar("maquinas")]
        p_list = [p['nombre'] for p in cargar("personal")]
        
        with st.expander("➕ Lanzar Nueva OP"):
            with st.form("f_op"):
                desc = st.text_area("Descripción")
                c1, c2, c3 = st.columns(3)
                mq, tc, pr = c1.selectbox("Máquina", m_list), c2.selectbox("Técnico", p_list), c3.selectbox("Prioridad", ["ALTA", "BAJA"])
                tt = st.selectbox("Tipo", ["Correctiva", "Preventiva"])
                cos = st.number_input("Costo ($)", 0.0)
                
                if st.form_submit_button("Lanzar"):
                    try:
                        supabase.table("ordenes").insert({
                            "descripcion": desc, "id_maquina": mq, "id_tecnico": tc, 
                            "prioridad": pr, "costo": cos, "tipo_tarea": tt,
                            "estado": "Proceso", "creado_por": st.session_state.user
                        }).execute()
                        st.success("✅ ¡Orden enviada!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")

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
                            st.write("✒️ **Firma Jefe de Planta**")
                            st_canvas(stroke_width=2, stroke_color="black", height=80, width=250, key=f"f_{row['id']}")
                            if c2.button("Finalizar", key=f"fbtn_{row['id']}"):
                                supabase.table("ordenes").update({"estado": "Finalizada", "firma_jefe": "OK"}).eq("id", row['id']).execute()
                                st.rerun()
                        elif est_actual in pasos:
                            if c2.button(f"➡️", key=f"av_{row['id']}"):
                                supabase.table("ordenes").update({"estado": pasos[est_actual]}).eq("id", row['id']).execute()
                                st.rerun()
                        
                        if c3.button("🗑️", key=f"del_{row['id']}"):
                            supabase.table("ordenes").delete().eq("id", row['id']).execute()
                            st.rerun()
