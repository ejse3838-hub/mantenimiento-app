import streamlit as st
import pandas as pd
from supabase import create_client, Client
import urllib.parse

# --- 1. CONEXIÓN (Sin cambios) ---
url = st.secrets["connections"]["supabase"]["SUPABASE_URL"]
key = st.secrets["connections"]["supabase"]["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

# --- 2. FUNCIÓN DE CARGA (Nueva lógica sin .execute() extra) ---
def cargar_datos(tabla):
    try:
        # Simplificamos la consulta al máximo
        query = supabase.table(tabla).select("*").eq("creado_por", st.session_state.user).execute()
        return query.data if query.data else []
    except Exception as e:
        st.error(f"Error en {tabla}: {e}")
        return []

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="CORMAIN CMMS PRO", layout="wide")
if 'auth' not in st.session_state: st.session_state.auth = False

# --- LOGIN ---
if not st.session_state.auth:
    tab1, tab2 = st.tabs(["🔑 Login", "📝 Registro"])
    with tab1:
        u = st.text_input("Usuario")
        p = st.text_input("Clave", type="password")
        if st.button("Entrar"):
            res = supabase.table("usuarios").select("*").eq("email", u).eq("password", p).execute()
            if res.data:
                st.session_state.auth = True
                st.session_state.user = res.data[0]['email']
                st.rerun()
            else: st.error("Fallo de acceso")
    with tab2:
        nu = st.text_input("Nuevo Email")
        np = st.text_input("Nueva Clave", type="password")
        if st.button("Crear"):
            supabase.table("usuarios").insert({"email": nu, "password": np, "creado_por": nu}).execute()
            st.success("Creado")

else:
    # --- MENÚ LATERAL ---
    st.sidebar.title(f"👤 {st.session_state.user}")
    opcion = st.sidebar.radio("Ir a:", ["Inicio", "Personal", "Maquinas", "Ordenes"])
    
    if st.sidebar.button("Cerrar Sesión"):
        st.session_state.auth = False
        st.rerun()

    # --- PÁGINA: INICIO ---
    if opcion == "Inicio":
        st.title("📊 Dashboard")
        ordenes = cargar_datos("ordenes")
        if ordenes:
            df = pd.DataFrame(ordenes)
            st.write("Resumen de actividad:")
            st.dataframe(df[['descripcion', 'estado', 'id_tecnico']])
        else:
            st.info("No hay datos")

    # --- PÁGINA: PERSONAL ---
    elif opcion == "Personal":
        st.header("👥 Personal")
        with st.form("per"):
            n = st.text_input("Nombre")
            t = st.text_input("WhatsApp")
            if st.form_submit_button("Guardar"):
                supabase.table("personal").insert({"nombre": n, "telefono": t, "creado_por": st.session_state.user}).execute()
                st.rerun()
        datos_p = cargar_datos("personal")
        if datos_p: st.table(pd.DataFrame(datos_p)[['nombre', 'telefono']])

    # --- PÁGINA: MAQUINAS ---
    elif opcion == "Maquinas":
        st.header("⚙️ Maquinas")
        with st.form("maq"):
            m = st.text_input("Nombre Máquina")
            if st.form_submit_button("Guardar"):
                supabase.table("maquinas").insert({"nombre_maquina": m, "creado_por": st.session_state.user}).execute()
                st.rerun()
        datos_m = cargar_datos("maquinas")
        if datos_m: st.table(pd.DataFrame(datos_m)[['nombre_maquina']])

    # --- PÁGINA: ORDENES ---
    elif opcion == "Ordenes":
        st.header("📑 Gestión de Órdenes")
        
        # Cargamos los datos para los selectbox
        m_list = cargar_datos("maquinas")
        p_list = cargar_datos("personal")
        
        # Transformamos a listas simples (Aquí estaba el error de las líneas anteriores)
        lista_m = [item['nombre_maquina'] for item in m_list] if m_list else ["Vacio"]
        lista_p = [item['nombre'] for item in p_list] if p_list else ["Vacio"]

        with st.expander("Crear OP"):
            with st.form("op"):
                desc = st.text_area("Tarea")
                sel_m = st.selectbox("Máquina", lista_m)
                sel_p = st.selectbox("Técnico", lista_p)
                if st.form_submit_button("Lanzar"):
                    supabase.table("ordenes").insert({
                        "descripcion": desc, "id_maquina": sel_m, 
                        "id_tecnico": sel_p, "estado": "Proceso", 
                        "creado_por": st.session_state.user
                    }).execute()
                    st.rerun()

        # Visualización de órdenes
        o_list = cargar_datos("ordenes")
        if o_list:
            df_o = pd.DataFrame(o_list)
            for est in ["Proceso", "Realizada", "Finalizada"]:
                st.subheader(f"Estado: {est}")
                filtro = df_o[df_o['estado'] == est]
                for _, fila in filtro.iterrows():
                    with st.container(border=True):
                        col1, col2 = st.columns([4,1])
                        col1.write(f"{fila['descripcion']} | {fila['id_tecnico']}")
                        if col2.button("🗑️", key=f"del_{fila['id']}"):
                            supabase.table("ordenes").delete().eq("id", fila['id']).execute()
                            st.rerun()
