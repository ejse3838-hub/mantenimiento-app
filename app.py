import streamlit as st
import pandas as pd
from supabase import create_client, Client
import urllib.parse

# --- PROTECCIÓN PARA LOS GRÁFICOS ---
try:
    import plotly.express as px
    GRAFICOS_LISTOS = True
except ImportError:
    GRAFICOS_LISTOS = False

# --- CONEXIÓN ---
url = st.secrets["connections"]["supabase"]["SUPABASE_URL"]
key = st.secrets["connections"]["supabase"]["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

# --- FUNCIÓN DE CARGA FILTRADA POR USUARIO ---
def cargar(tabla):
    try:
        res = supabase.table(tabla).select("*").eq("creado_por", st.session_state.user).execute()
        return res.data if res.data else []
    except: return []

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
        new_u = st.text_input("Nuevo Email")
        new_p = st.text_input("Nueva Clave", type="password")
        if st.button("Crear Cuenta"):
            try:
                supabase.table("usuarios").insert({"email": new_u, "password": new_p}).execute()
                st.success("¡Cuenta creada!")
            except: st.error("Error al crear cuenta.")

else:
    # --- MENÚ LATERAL (BOTONES) ---
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
            
            # KPI de Costos
            if 'costo' in df.columns:
                gasto_total = df['costo'].sum()
                st.metric("Gasto Total en Mantenimiento", f"${gasto_total:,.2f}")
            
            if GRAFICOS_LISTOS:
                st.divider()
                colg1, colg2 = st.columns(2)
                fig1 = px.pie(df, names='estado', hole=0.4, title="Distribución por Estado")
                colg1.plotly_chart(fig1, use_container_width=True)
                fig2 = px.bar(df, x='id_tecnico', color='prioridad', title="Carga de Trabajo por Técnico")
                colg2.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("No hay datos para mostrar.")

    # --- 2. PERSONAL ---
    elif st.session_state.menu == "👥 Personal":
        st.header("Gestión de Personal")
        with st.form("f_pers"):
            c1, c2 = st.columns(2)
            nom = c1.text_input("Nombres")
            ape = c2.text_input("Apellidos")
            car = c1.text_input("Cargo")
            pue = c2.text_input("Puesto (Especialidad)")
            if st.form_submit_button("Guardar Empleado"):
                supabase.table("personal").insert({
                    "nombre": f"{nom} {ape}", 
                    "cargo": car, 
                    "especialidad": pue, 
                    "creado_por": st.session_state.user
                }).execute()
                st.rerun()
        
        per_list = cargar("personal")
        if per_list:
            st.subheader("Personal Registrado")
            st.table(pd.DataFrame(per_list)[["nombre", "cargo", "especialidad"]])

    # --- 3. MAQUINARIA (FORMULARIO EXTENDIDO) ---
    elif st.session_state.menu == "⚙️ Maquinaria":
        st.header("Inventario Técnico de Maquinaria")
        with st.form("f_maq_pro"):
            col1, col2, col3 = st.columns(3)
            n_m = col1.text_input("Nombre de la Máquina")
            cod_m = col2.text_input("Código Interno")
            serial_m = col3.text_input("Número de Serial")
            
            fab_m = col1.text_input("Fabricante")
            mod_m = col2.text_input("Modelo")
            est_m = col3.selectbox("Estado Operativo", ["Operativa", "Falla", "En Mantenimiento"])
            
            f_compra = col1.date_input("Fecha de Compra")
            hrs_uso = col2.number_input("Horas de Uso Acumuladas", min_value=0, value=0)
            
            ap1 = col1.text_area("Apartado 1 (Especificaciones)")
            ap2 = col2.text_area("Apartado 2 (Ubicación/Notas)")
            
            if st.form_submit_button("Registrar Activo en Sistema"):
                supabase.table("maquinas").insert({
                    "nombre_maquina": n_m, "codigo": cod_m, "serial": serial_m,
                    "fabricante": fab_m, "modelo": mod_m, "estado": est_m,
                    "fecha_compra": str(f_compra), "horas_uso": hrs_uso,
                    "apartado1": ap1, "apartado2": ap2,
                    "creado_por": st.session_state.user
                }).execute()
                st.rerun()
        
        maq_list = cargar("maquinas")
        if maq_list:
            st.subheader("Listado de Activos")
            df_maq = pd.DataFrame(maq_list)
            # Mostramos un dataframe interactivo con todos los datos
            st.dataframe(df_maq.drop(columns=['id', 'creado_por'], errors='ignore'), use_container_width=True)

    # --- 4. ÓRDENES DE TRABAJO (SISTEMA DE PRIORIDADES Y COSTOS) ---
    elif st.session_state.menu == "📑 Órdenes de Trabajo":
        st.header("Gestión de Órdenes de Trabajo")
        
        with st.expander("➕ Generar Nueva Orden de Trabajo"):
            maqs_data = cargar("maquinas")
            maqs_opts = [f"{m['nombre_maquina']} ({m['codigo']})" for m in maqs_data]
            pers_data = cargar("personal")
            pers_opts = [p['nombre'] for p in pers_data]
            
            with st.form("f_orden_completa"):
                desc = st.text_area("Descripción detallada del problema o tarea")
                
                c1, c2, c3 = st.columns(3)
                maq = c1.selectbox("Máquina afectada", maqs_opts)
                tec = c2.selectbox("Técnico asignado", pers_opts)
                prio = c3.selectbox("Prioridad", ["🔴 ALTA", "🟡 MEDIA", "🟢 BAJA"])
                
                c4, c5, c6 = st.columns(3)
                frec = c4.selectbox("Periodicidad", ["Correctiva", "Diaria", "Semanal", "Mensual", "Anual"])
                costo_est = c5.number_input("Costo Estimado ($)", min_value=0.0)
                insumos = c6.text_input("Repuestos / Insumos necesarios")
                
                if st.form_submit_button("Lanzar Orden al Sistema"):
                    supabase.table("ordenes").insert({
                        "descripcion": desc, "id_maquina": maq, "id_tecnico": tec,
                        "prioridad": prio, "frecuencia": frec, "costo": costo_est,
                        "insumos": insumos, "estado": "Proceso", 
                        "creado_por": st.session_state.user
                    }).execute()
                    st.rerun()

        st.divider()
        df_o = pd.DataFrame(cargar("ordenes"))
        if not df_o.empty:
            pasos = {"Proceso": "Realizada", "Realizada": "Revisada", "Revisada": "Finalizada"}
            
            # Vista por columnas de estados
            for est in ["Proceso", "Realizada", "Revisada", "Finalizada"]:
                st.subheader(f"📍 Estado: {est}")
                items = df_o[df_o['estado'] == est]
                
                for _, row in items.iterrows():
                    with st.container(border=True):
                        col_info, col_btn1, col_btn2 = st.columns([3, 1, 1])
                        
                        with col_info:
                            st.write(f"### {row['id_maquina']}")
                            st.write(f"**Tarea:** {row['descripcion']}")
                            st.caption(f"🔧 **Técnico:** {row['id_tecnico']} | 🚨 **Prioridad:** {row['prioridad']}")
                            st.caption(f"⏱️ **Frecuencia:** {row.get('frecuencia','N/A')} | 💰 **Costo:** ${row.get('costo', 0)}")
                            if row.get('insumos'):
                                st.info(f"📦
