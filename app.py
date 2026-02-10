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

    # --- 1. INICIO (DASHBOARD) ---
    if st.session_state.menu == "🏠 Inicio":
        st.title("📊 Panel de Control")
        df = pd.DataFrame(cargar("ordenes"))
        if not df.empty:
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("En Proceso", len(df[df['estado'] == 'Proceso']))
            c2.metric("Realizadas", len(df[df['estado'] == 'Realizada']))
            c3.metric("Finalizadas", len(df[df['estado'] == 'Finalizada']))
            if 'costo' in df.columns:
                c4.metric("Inversión Total", f"${df['costo'].sum():,.2f}")
            
            import plotly.express as px
            fig = px.pie(df, names='estado', hole=0.4, title="Distribución de Estados")
            st.plotly_chart(fig, use_container_width=True)
        else: st.info("Sin datos registrados.")

    # --- 2. PERSONAL ---
    elif st.session_state.menu == "👥 Personal":
        st.header("Gestión de Personal")
        with st.form("f_personal"):
            c1, c2, c3 = st.columns(3)
            nom, ape = c1.text_input("Nombres"), c2.text_input("Apellidos")
            cod_e = c3.text_input("Código Empleado")
            mail, car = c1.text_input("Email"), c2.text_input("Cargo")
            dire = c3.text_input("Dirección")
            cl1 = c1.selectbox("Clasificación 1", ["Interno", "Externo"])
            cl2 = c2.selectbox("Especialidad", ["Mecánico", "Eléctrico", "Operador"])
            
            st.write("✒️ **Firma Digital**")
            st_canvas(stroke_width=2, stroke_color="black", height=100, width=400, key="p_sign")
            
            if st.form_submit_button("Guardar"):
                supabase.table("personal").insert({
                    "nombre": f"{nom} {ape}", "apellido": ape, "codigo_empleado": cod_e,
                    "email": mail, "cargo": car, "especialidad": cl2, "clasificacion1": cl1,
                    "direccion": dire, "firma_path": "REGISTRADA", "creado_por": st.session_state.user
                }).execute()
                st.rerun()
        st.dataframe(pd.DataFrame(cargar("personal")), use_container_width=True)

    # --- 3. MAQUINARIA ---
    elif st.session_state.menu == "⚙️ Maquinaria":
        st.header("Ficha Técnica de Equipos")
        with st.form("f_maq"):
            c1, c2, c3 = st.columns(3)
            nm, cod, ubi = c1.text_input("Nombre Máquina"), c2.text_input("Código"), c3.text_input("Ubicación")
            fab, mod, ser = c1.text_input("Fabricante"), c2.text_input("Modelo"), c3.text_input("Serial")
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

    # --- 4. ÓRDENES (REVISADO CON TUS 15 COLUMNAS) ---
    elif st.session_state.menu == "📑 Órdenes de Trabajo":
        st.header("Gestión de OP")
        m_list = [f"{m['nombre_maquina']} ({m['codigo']})" for m in cargar("maquinas")]
        p_list = [p['nombre'] for p in cargar("personal")]

        with st.expander("➕ Lanzar Nueva OP"):
            with st.form("f_op"):
                desc = st.text_area("Descripción")
                c1, c2, c3 = st.columns(3)
                mq, tc, pr = c1.selectbox("Máquina", maqs if 'maqs' in locals() else m_list), c2.selectbox("Técnico", p_list), c3.selectbox("Prioridad", ["🔴 ALTA", "🟡 MEDIA", "🟢 BAJA"])
                
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

        st.divider()
        df_o = pd.DataFrame(cargar("ordenes"))
        if not df_o.empty:
            pasos = {"Proceso": "Realizada", "Realizada": "Revisada", "Revisada": "Finalizada"}
            for est in ["Proceso", "Realizada", "Revisada", "Finalizada"]:
                st.subheader(f"📍 {est}")
                filas = df_o[df_o['estado'] == est]
                for _, row in filas.iterrows():
                    with st.container(border=True):
                        c1, c2, c3 = st.columns([3, 1, 1])
                        c1.write(f"**{row['id_maquina']}** | {row['prioridad']}")
                        c1.caption(f"🔧 {row['descripcion']}")
                        if est == "Revisada":
                            st.write("✒️ Firma Jefe")
                            st_canvas(stroke_width=2, stroke_color="black", height=80, width=250, key=f"f_{row['id']}")
                            if c2.button("Finalizar", key=f"fbtn_{row['id']}"):
                                supabase.table("ordenes").update({"estado": "Finalizada", "firma_jefe": "OK"}).eq("id", row['id']).execute()
                                st.rerun()
                        elif est in pasos:
                            if c2.button(f"➡️", key=f"av_{row['id']}"):
                                supabase.table("ordenes").update({"estado": pasos[est]}).eq("id", row['id']).execute()
                                st.rerun()
                        if c3.button("🗑️", key=f"del_{row['id']}"):
                            supabase.table("ordenes").delete().eq("id", row['id']).execute()
                            st.rerun()
