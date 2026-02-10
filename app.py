import streamlit as st
import pandas as pd
from supabase import create_client, Client
import urllib.parse

# --- 1. CONEXIÓN ---
url = st.secrets["connections"]["supabase"]["SUPABASE_URL"]
key = st.secrets["connections"]["supabase"]["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

# --- 2. FUNCIÓN DE CARGA SEGURA ---
def cargar_datos(tabla):
    try:
        # Consulta simple: traemos los datos y los guardamos en 'res'
        res = supabase.table(tabla).select("*").eq("creado_por", st.session_state.user).execute()
        # Retornamos solo la lista de datos (.data)
        return res.data if res.data else []
    except Exception as e:
        st.error(f"Error cargando {tabla}: {e}")
        return []

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
            res = supabase.table("usuarios").select("*").eq("email", u).eq("password", p).execute()
            if res.data:
                st.session_state.auth = True
                st.session_state.user = res.data[0]['email']
                st.rerun()
            else: st.error("Datos incorrectos")
    with tab2:
        nu = st.text_input("Nuevo Email")
        np = st.text_input("Nueva Clave", type="password")
        if st.button("Crear Cuenta"):
            supabase.table("usuarios").insert({"email": nu, "password": np, "creado_por": nu}).execute()
            st.success("Usuario creado")

else:
    # --- MENÚ LATERAL (ESTILO RADIO PARA EVITAR ERRORES) ---
    st.sidebar.title(f"👤 {st.session_state.user}")
    opcion = st.sidebar.radio("Navegación:", ["Dashboard", "Personal", "Maquinaria", "Órdenes de Trabajo"])
    
    if st.sidebar.button("🚪 Cerrar Sesión"):
        st.session_state.auth = False
        st.rerun()

    # --- PÁGINA: DASHBOARD ---
    if opcion == "Dashboard":
        st.title("📊 Resumen General")
        ordenes = cargar_datos("ordenes")
        if ordenes:
            df = pd.DataFrame(ordenes)
            col1, col2, col3 = st.columns(3)
            col1.metric("En Proceso", len(df[df['estado'] == 'Proceso']))
            col2.metric("Realizadas", len(df[df['estado'] == 'Realizada']))
            col3.metric("Finalizadas", len(df[df['estado'] == 'Finalizada']))
        else:
            st.info("No hay datos registrados")

    # --- PÁGINA: PERSONAL ---
    elif opcion == "Personal":
        st.header("👥 Gestión de Técnicos")
        with st.form("form_per"):
            nombre = st.text_input("Nombre Completo")
            wpp = st.text_input("WhatsApp (ej: 593987654321)")
            if st.form_submit_button("Guardar"):
                supabase.table("personal").insert({
                    "nombre": nombre, "telefono": wpp, "creado_por": st.session_state.user
                }).execute()
                st.rerun()
        
        datos_p = cargar_datos("personal")
        if datos_p:
            st.table(pd.DataFrame(datos_p)[["nombre", "telefono"]])

    # --- PÁGINA: MAQUINARIA ---
    elif opcion == "Maquinaria":
        st.header("⚙️ Gestión de Equipos")
        with st.form("form_maq"):
            maquina = st.text_input("Nombre de Equipo")
            if st.form_submit_button("Registrar Equipo"):
                supabase.table("maquinas").insert({
                    "nombre_maquina": maquina, "creado_por": st.session_state.user
                }).execute()
                st.rerun()
        
        datos_m = cargar_datos("maquinas")
        if datos_m:
            st.table(pd.DataFrame(datos_m)[["nombre_maquina"]])

    # --- PÁGINA: ÓRDENES ---
    elif opcion == "Órdenes de Trabajo":
        st.header("📑 Órdenes de Producción")
        
        # 1. Cargamos datos brutos
        m_raw = cargar_datos("maquinas")
        p_raw = cargar_datos("personal")
        
        # 2. Procesamos nombres (AQUÍ ESTABA EL ERROR, AHORA ESTÁ SEPARADO)
        nombres_maquinas = [x['nombre_maquina'] for x in m_raw] if m_raw else ["Vacio"]
        nombres_tecnicos = [x['nombre'] for x in p_raw] if p_raw else ["Vacio"]

        with st.expander("➕ Nueva Orden"):
            with st.form("form_op"):
                tarea = st.text_area("Descripción de tarea")
                sel_m = st.selectbox("Máquina", nombres_maquinas)
                sel_t = st.selectbox("Técnico", nombres_tecnicos)
                if st.form_submit_button("Crear"):
                    if sel_m == "Vacio" or sel_t == "Vacio":
                        st.error("Registra maquinaria y personal primero")
                    else:
                        supabase.table("ordenes").insert({
                            "descripcion": tarea, "id_maquina": sel_m, 
                            "id_tecnico": sel_t, "estado": "Proceso", 
                            "creado_por": st.session_state.user
                        }).execute()
                        st.rerun()

        # Listado de órdenes
        o_raw = cargar_datos("ordenes")
        if o_raw:
            df_o = pd.DataFrame(o_raw)
            for e in ["Proceso", "Realizada", "Finalizada"]:
                st.subheader(f"📍 {e}")
                items = df_o[df_o['estado'] == e]
                for _, fila in items.iterrows():
                    with st.container(border=True):
                        c1, c2 = st.columns([4, 1])
                        c1.write(f"**{fila['id_maquina']}**: {fila['descripcion']} - {fila['id_tecnico']}")
                        if c2.button("🗑️", key=f"del_{fila['id']}"):
                            supabase.table("ordenes").delete().eq("id", fila['id']).execute()
                            st.rerun()
