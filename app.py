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
    except: return []

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="CORMAIN CMMS PRO", layout="wide")
if 'auth' not in st.session_state: st.session_state.auth = False

# --- LOGIN ---
if not st.session_state.auth:
    tab1, tab2 = st.tabs(["🔑 Login", "📝 Registro"])
    with tab1:
        u = st.text_input("Usuario (Email)")
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
    if st.sidebar.button("🚪 Salir", use_container_width=True):
        st.session_state.auth = False
        st.rerun()

    # --- 1. INICIO (DASHBOARD) ---
    if st.session_state.menu == "🏠 Inicio":
        st.title("📊 Panel de Control")
        df = pd.DataFrame(cargar("ordenes"))
        if not df.empty:
            c1, c2, c3 = st.columns(3)
            c1.metric("Órdenes Totales", len(df))
            if 'costo' in df.columns: c2.metric("Inversión Total", f"${df['costo'].sum():,.2f}")
            import plotly.express as px
            fig = px.pie(df, names='estado', hole=0.4, title="Estado Global")
            st.plotly_chart(fig, use_container_width=True)
        else: st.info("Sin datos")

    # --- 2. PERSONAL ---
    elif st.session_state.menu == "👥 Personal":
        st.header("Gestión de Personal")
        with st.form("f_personal"):
            c1, c2, c3 = st.columns(3)
            nombre = c1.text_input("Nombre")
            apellido = c2.text_input("Apellido")
            codigo_empleado = c3.text_input("Código Empleado")
            email = c1.text_input("Email")
            cargo = c2.text_input("Cargo")
            especialidad = c3.text_input("Especialidad")
            clasificacion1 = c1.selectbox("Clasificación 1", ["Interno", "Externo"])
            direccion = c2.text_input("Dirección")
            
            st.write("✒️ **Firma Digital Maestra**")
            st_canvas(stroke_width=2, stroke_color="black", height=100, width=400, key="p_sign")
            
            if st.form_submit_button("Guardar"):
                supabase.table("personal").insert({
                    "nombre": nombre, "apellido": apellido, "codigo_empleado": codigo_empleado,
                    "email": email, "cargo": cargo, "especialidad": especialidad,
                    "clasificacion1": clasificacion1, "direccion": direccion, 
                    "firma_path": "REGISTRADA", "creado_por": st.session_state.user
                }).execute()
                st.rerun()
        plist = cargar("personal")
        if plist: st.dataframe(pd.DataFrame(plist).drop(columns=['id', 'creado_por'], errors='ignore'))

    # --- 3. MAQUINARIA ---
    elif st.session_state.menu == "⚙️ Maquinaria":
        st.header("Ficha Técnica")
        with st.form("f_maq"):
            c1, c2, c3 = st.columns(3)
            nombre_maquina = c1.text_input("Nombre Máquina")
            codigo = c2.text_input("Código")
            ubicacion = c3.text_input("Ubicación")
            serial = c1.text_input("Serial")
            fabricante = c2.text_input("Fabricante")
            modelo = c3.text_input("Modelo")
            estado = c1.selectbox("Estado", ["Operativa", "Falla", "Mantenimiento"])
            horas_uso = c2.number_input("Horas Uso", min_value=0)
            fecha_compra = c3.date_input("Fecha Compra")
            apartado1 = st.text_area("Apartado 1")
            apartado2 = st.text_area("Apartado 2")
            
            if st.form_submit_button("Registrar"):
                supabase.table("maquinas").insert({
                    "nombre_maquina": nombre_maquina, "codigo": codigo, "ubicacion": ubicacion,
                    "estado": estado, "serial": serial, "fabricante": fabricante, "modelo": modelo,
                    "horas_uso": horas_uso, "fecha_compra": str(fecha_compra),
                    "apartado1": apartado1, "apartado2": apartado2, "creado_por": st.session_state.user
                }).execute()
                st.rerun()
        mlist = cargar("maquinas")
        if mlist: st.dataframe(pd.DataFrame(mlist).drop(columns=['id', 'creado_por'], errors='ignore'))

    # --- 4. ÓRDENES (REVISADO CON FIRMA DE JEFE) ---
    elif st.session_state.menu == "📑 Órdenes de Trabajo":
        st.header("Gestión de OP")
        
        with st.expander("➕ Lanzar Nueva OP"):
            m_opts = [f"{m['nombre_maquina']} ({m['codigo']})" for m in cargar("maquinas")]
            p_opts = [f"{p['nombre']} {p['apellido']}" for p in cargar("personal")]
            with st.form("f_op"):
                desc = st.text_area("Descripción")
                c1, c2, c3 = st.columns(3)
                maq = c1.selectbox("Máquina", m_opts)
                tec = c2.selectbox("Técnico", p_opts)
                prio = c3.selectbox("Prioridad", ["ALTA", "MEDIA", "BAJA"])
                
                c4, c5, c6 = st.columns(3)
                tipo = c4.selectbox("Tipo", ["Correctiva", "Preventiva"])
                frec = c5.selectbox("Frecuencia", ["Única", "Semanal", "Mensual"])
                dur = c6.text_input("Duración", "1h")
                
                c7, c8, c9 = st.columns(3)
                paro = c7.selectbox("Paro", ["No", "Sí"])
                herr = c8.text_input("Herramientas")
                cost = c9.number_input("Costo", 0.0)
                insu = st.text_input("Insumos")
                
                if st.form_submit_button("Lanzar"):
                    supabase.table("ordenes").insert({
                        "descripcion": desc, "id_maquina": maq, "id_tecnico": tec,
                        "estado": "Proceso", "tipo_tarea": tipo, "frecuencia": frec,
                        "duracion_estimada": dur, "requiere_paro": paro,
                        "herramientas": herr, "prioridad": prio, "insumos": insu,
                        "costo": cost, "creado_por": st.session_state.user
                    }) st.rerun()

        st.divider()
        df_o = pd.DataFrame(cargar("ordenes"))
        if not df_o.empty:
            pasos = {"Proceso": "Realizada", "Realizada": "Revisada", "Revisada": "Finalizada"}
            for est in ["Proceso", "Realizada", "Revisada", "Finalizada"]:
                st.subheader(f"📍 {est}")
                items = df_o[df_o['estado'] == est]
                for _, row in items.iterrows():
                    with st.container(border=True):
                        c1, c2, c3 = st.columns([3, 1, 1])
                        c1.write(f"### {row['prioridad']} | {row['id_maquina']}")
                        c1.write(f"**Tarea:** {row['descripcion']}")
                        c1.caption(f"👤 Técnico: {row['id_tecnico']} | ⏱️ {row.get('duracion_estimada','-')} | 💰 ${row.get('costo',0)}")
                        
                        if est == "Revisada":
                            st.write("✒️ **Firma de Aprobación del Jefe**")
                            # Canvas de firma específico para esta orden
                            st_canvas(stroke_width=2, stroke_color="black", background_color="#f0f0f0", height=80, width=250, key=f"f_{row['id']}")
                            if c2.button("✅ Firmar y Finalizar", key=f"btn_f_{row['id']}"):
                                supabase.table("ordenes").update({
                                    "estado": "Finalizada", 
                                    "firma_jefe": "APROBADO"
                                }).eq("id", row['id']).execute()
                                st.rerun()
                        elif est in pasos:
                            if c2.button(f"➡️ {pasos[est]}", key=f"av_{row['id']}"):
                                supabase.table("ordenes").update({"estado": pasos[est]}).eq("id", row['id']).execute()
                                st.rerun()
                        
                        if c3.button("🗑️", key=f"del_{row['id']}"):
                            supabase.table("ordenes").delete().eq("id", row['id']).execute()
                            st.rerun()

