import streamlit as st
import pandas as pd
from supabase import create_client, Client

# 1. CONFIGURACIÓN
st.set_page_config(page_title="CORMAIN CMMS v3.0", layout="wide")

url = st.secrets["connections"]["supabase"]["SUPABASE_URL"]
key = st.secrets["connections"]["supabase"]["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

# --- FUNCIÓN DE CARGA ---
def obtener_datos(tabla):
    res = supabase.table(tabla).select("*").execute()
    return res.data

# --- LÓGICA DE ACCESO ---
if 'auth' not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    st.title("🛡️ Sistema CORMAIN")
    u = st.text_input("Usuario (Email)")
    p = st.text_input("Clave", type="password")
    if st.button("Ingresar"):
        res = supabase.table("usuarios").select("*").eq("email", u).eq("password", p).execute()
        if res.data:
            st.session_state.auth = True
            st.rerun()
        else:
            st.error("Acceso denegado")
else:
    st.sidebar.title("Navegación")
    opcion = st.sidebar.selectbox("Seleccione Área", ["Recursos Humanos", "Maquinaria", "Órdenes de Trabajo"])

    # --- RECURSOS HUMANOS ---
    if opcion == "Recursos Humanos":
        st.header("👥 Personal")
        with st.expander("➕ Nuevo Operador"):
            with st.form("rrhh"):
                nombre = st.text_input("Nombre Completo")
                cargo = st.text_input("Cargo")
                if st.form_submit_button("Guardar"):
                    supabase.table("personal").insert({"nombre": nombre, "cargo": cargo}).execute()
                    st.rerun()
        
        datos_p = obtener_datos("personal")
        if datos_p:
            df_p = pd.DataFrame(datos_p)
            # Solo mostramos columnas de texto para editar y ocultamos el ID interno
            cols_p = [c for c in ["nombre", "cargo", "especialidad"] if c in df_p.columns]
            st.data_editor(df_p[cols_p], use_container_width=True, key="edit_rrhh")

    # --- MAQUINARIA ---
    elif opcion == "Maquinaria":
        st.header("⚙️ Activos")
        with st.expander("➕ Nueva Máquina"):
            with st.form("maq"):
                nom_m = st.text_input("Nombre de Máquina")
                cod_m = st.text_input("Código de Inventario")
                if st.form_submit_button("Registrar"):
                    supabase.table("maquinas").insert({"nombre_maquina": nom_m, "codigo": cod_m}).execute()
                    st.rerun()

        datos_m = obtener_datos("maquinas")
        if datos_m:
            df_m = pd.DataFrame(datos_m)
            cols_m = [c for c in ["nombre_maquina", "codigo", "ubicacion"] if c in df_m.columns]
            st.data_editor(df_m[cols_m], use_container_width=True, key="edit_maq")

    # --- ÓRDENES DE TRABAJO (CORRECCIÓN DE ID) ---
    elif opcion == "Órdenes de Trabajo":
        st.header("📑 Órdenes de Producción")
        
        # Obtenemos datos para mapear nombres a IDs ocultos
        maqs = obtener_datos("maquinas")
        tecs = obtener_datos("personal")
        
        # Mapeo seguro usando .get() para evitar KeyError
        dict_maqs = {m.get('nombre_maquina', 'Desconocido'): m.get('id') for m in maqs} if maqs else {}
        dict_tecs = {t.get('nombre', 'Sin nombre'): t.get('id') for t in tecs} if tecs else {}

        with st.expander("🆕 Crear Orden"):
            with st.form("ot"):
                descripcion = st.text_area("Descripción de la falla/tarea")
                m_sel = st.selectbox("Máquina", list(dict_maqs.keys()) if dict_maqs else ["No hay máquinas"])
                t_sel = st.selectbox("Técnico Asignado", list(dict_tecs.keys()) if dict_tecs else ["No hay técnicos"])
                
                if st.form_submit_button("Iniciar"):
                    if dict_maqs and dict_tecs:
                        # Estructura que envía los IDs necesarios para evitar el APIError
                        ins_data = {
                            "descripcion": descripcion,
                            "id_maquina": dict_maqs[m_sel],
                            "id_tecnico": dict_tecs[t_sel],
                            "estado": "Proceso"
                        }
                        supabase.table("ordenes").insert(ins_data).execute()
                        st.success("Orden creada con éxito")
                        st.rerun()

        # Tablero de control
        st.divider()
        ots = obtener_datos("ordenes")
        if ots:
            st.subheader("Estado Actual")
            df_ots = pd.DataFrame(ots)
            # Mostramos solo información relevante para el usuario
            cols_ot = [c for c in ["id", "descripcion", "estado"] if c in df_ots.columns]
            st.dataframe(df_ots[cols_ot], use_container_width=True)

    if st.sidebar.button("Salir"):
        st.session_state.auth = False
        st.rerun()
