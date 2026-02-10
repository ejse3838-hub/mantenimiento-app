import streamlit as st
import pandas as pd
from supabase import create_client, Client
from streamlit_drawable_canvas import st_canvas # Mantener diseño de firmas
import urllib.parse

# --- PROTECCIÓN PARA LOS GRÁFICOS (MANTENER DISEÑO) ---
try:
    import plotly.express as px
    GRAFICOS_LISTOS = True
except ImportError:
    GRAFICOS_LISTOS = False

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

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="CORMAIN CMMS PRO", layout="wide")

if 'auth' not in st.session_state: st.session_state.auth = False

# --- LOGIN (SIN CAMBIOS) ---
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
            supabase.table("usuarios").insert({"email": nu, "password": np}).execute()
            st.success("¡Cuenta creada!")

else:
    # --- MENÚ LATERAL (BOTONES LARGOS) ---
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
        o_data = cargar("ordenes")
        df = pd.DataFrame(o_data)
        if not df.empty:
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("En Proceso", len(df[df['estado'] == 'Proceso']))
            c2.metric("Realizadas", len(df[df['estado'] == 'Realizada']))
            c3.metric("Revisadas", len(df[df['estado'] == 'Revisada']))
            c4.metric("Finalizadas", len(df[df['estado'] == 'Finalizada']))
            if 'costo' in df.columns:
                st.metric("Inversión Total", f"${df['costo'].sum():,.2f}")
            if GRAFICOS_LISTOS:
                st.divider()
                colg1, colg2 = st.columns(2)
                fig1 = px.pie(df, names='estado', hole=0.4, title="Estado Global")
                colg1.plotly_chart(fig1, use_container_width=True)
                fig2 = px.pie(df, names='prioridad', title="Prioridad de Tareas")
                colg2.plotly_chart(fig2, use_container_width=True)
        else: st.info("No hay datos para mostrar.")

    # --- 2. PERSONAL (RESPETANDO TUS COLUMNAS) ---
    elif st.session_state.menu == "👥 Personal":
        st.header("Gestión de Personal")
        with st.form("f_pers"):
            c1, c2, c3 = st.columns(3)
            nom, ape = c1.text_input("Nombres"), c2.text_input("Apellidos")
            cod_e = c3.text_input("Código de Empleado")
            mail, car = c1.text_input("Email Corporativo"), c2.text_input("Cargo")
            direc = c3.text_input("Dirección")
            cl1 = c1.selectbox("Clasificación 1", ["Interno", "Externo"])
            cl2 = c2.selectbox("Clasificación 2", ["Mecánico", "Eléctrico", "Operador", "Instrumentista", "Civil"])
            
            st.write("✒️ **Firma Digital Maestra**")
            st_canvas(stroke_width=2, stroke_color="black", background_color="#ffffff", height=100, width=400, key="p_sign")
            
            if st.form_submit_button("Guardar Personal"):
                supabase.table("personal").insert({
                    "nombre": f"{nom} {ape}", "apellido": ape, "codigo_empleado": cod_e,
                    "email": mail, "cargo": car, "especialidad": cl2, 
                    "clasificacion1": cl1, "direccion": direc, "firma_path": "REGISTRADA",
                    "creado_por": st.session_state.user
                }).execute()
                st.rerun()
        
        plist = cargar("personal")
        if plist: st.dataframe(pd.DataFrame(plist).drop(columns=['id', 'creado_por'], errors='ignore'), use_container_width=True)

    # --- 3. MAQUINARIA (FICHA TÉCNICA) ---
    elif st.session_state.menu == "⚙️ Maquinaria":
        st.header("Gestión de Activos (Ficha Técnica)")
        with st.form("f_maq"):
            c1, c2, c3 = st.columns(3)
            n_m, cod_m, fab_m = c1.text_input("Máquina"), c2.text_input("Código"), c3.text_input("Fabricante")
            mod_m, ser_m = c1.text_input("Modelo"), c2.text_input("Serial")
            est_m = c3.selectbox("Estado", ["Operativa", "Falla", "Mantenimiento"])
            f_compra, hrs_uso = c1.date_input("Fecha Compra"), c2.number_input("Horas Uso", min_value=0)
            ap1, ap2 = st.text_area("Apartado 1"), st.text_area("Apartado 2")
            if st.form_submit_button("Registrar Máquina"):
                supabase.table("maquinas").insert({
                    "nombre_maquina": n_m, "codigo": cod_m, "fabricante": fab_m, "modelo": mod_m,
                    "serial": ser_m, "estado": est_m, "fecha_compra": str(f_compra), "horas_uso": hrs_uso,
                    "apartado1": ap1, "apartado2": ap2, "creado_por": st.session_state.user
                }).execute()
                st.rerun()
        mlist = cargar("maquinas")
        if mlist: st.dataframe(pd.DataFrame(mlist).drop(columns=['id', 'creado_por'], errors='ignore'), use_container_width=True)

    # --- 4. ÓRDENES (USANDO TUS 15 COLUMNAS EXACTAS) ---
    elif st.session_state.menu == "📑 Órdenes de Trabajo":
        st.header("Gestión de Mantenimiento")
        
        with st.expander("➕ Crear Nueva Orden"):
            maqs = [f"{m['nombre_maquina']} ({m['codigo']})" for m in cargar("maquinas")]
            pers = [p['nombre'] for p in cargar("personal")]
            
            with st.form("f_orden_completa"):
                desc = st.text_area("Descripción de la Falla/Tarea")
                c1, c2, c3 = st.columns(3)
                maq, tec, prio = c1.selectbox("Máquina", maqs), c2.selectbox("Técnico", pers), c3.selectbox("Prioridad", ["🔴 ALTA", "🟡 MEDIA", "🟢 BAJA"])
                
                c4, c5, c6 = st.columns(3)
                tipo_t = c4.selectbox("Tipo de Tarea", ["Lubricación", "Ajuste", "Inspección", "Reparación"])
                duracion = c5.text_input("Duración Estimada", value="1h")
                paro = c6.selectbox("¿Requiere Paro?", ["No", "Sí"])
                
                c7, c8, c9 = st.columns(3)
                frec = c7.selectbox("Frecuencia", ["Única", "Diaria", "Semanal", "Mensual"])
                costo = c8.number_input("Costo Estimado ($)", min_value=0.0)
                herr = c9.text_input("Herramientas")
                
                insu = st.text_input("Insumos/Repuestos")
                
                if st.form_submit_button("Lanzar Orden"):
                    # EMPALME DE TERMINALES HACIA TUS 15 COLUMNAS
                    supabase.table("ordenes").insert({
                        "descripcion": desc, "id_maquina": maq, "id_tecnico": tec,
                        "tipo_tarea": tipo_t, "frecuencia": frec, "duracion_estimada": duracion,
                        "requiere_paro": paro, "herramientas": herr, "prioridad": prio,
                        "insumos": insu, "costo": costo, "estado": "Proceso",
                        "creado_por": st.session_state.user
                    }).execute()
                    st.rerun()

        st.divider()
        df_o = pd.DataFrame(cargar("ordenes"))
        if not df_o.empty:
            pasos = {"Proceso": "Realizada", "Realizada": "Revisada", "Revisada": "Finalizada"}
            for est in ["Proceso", "Realizada", "Revisada", "Finalizada"]:
                st.subheader(f"📍 {est}")
                items = df_o[df_o['estado'] == est]
                for _, row in items.iterrows():
                    with st.container(border=True):
                        col_a, col_b, col_c = st.columns([3, 1, 1])
                        col_a.write(f"### {row['prioridad']} | {row['id_maquina']}")
                        col_a.write(f"**Tarea:** {row['descripcion']}")
                        col_a.caption(f"🛠️ {row.get('tipo_tarea','-')} | ⏱️ {row.get('duracion_estimada','-')} | 💰 ${row.get('costo',0)}")
                        
                        if est == "Revisada":
                            st.write("✒️ **Firma de Aprobación del Jefe**")
                            st_canvas(stroke_width=2, stroke_color="black", background_color="#eee", height=80, width=250, key=f"f_{row['id']}")
                            if col_b.button("✅ Firmar y Cerrar", key=f"btn_f_{row['id']}"):
                                supabase.table("ordenes").update({"estado": "Finalizada", "firma_jefe": "APROBADO"}).eq("id", row['id']).execute()
                                st.rerun()
                        elif est in pasos:
                            if col_b.button(f"➡️ {pasos[est]}", key=f"av_{row['id']}"):
                                supabase.table("ordenes").update({"estado": pasos[est]}).eq("id", row['id']).execute()
                                st.rerun()
                        
                        if col_c.button("🗑️ Eliminar", key=f"del_{row['id']}"):
                            supabase.table("ordenes").delete().eq("id", row['id']).execute()
                            st.rerun()
