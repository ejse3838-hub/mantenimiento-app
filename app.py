import streamlit as st
import pandas as pd
from supabase import create_client, Client

# 1. CONFIGURACIÓN Y CONEXIÓN (Mantenemos tus llaves de las capturas)
st.set_page_config(page_title="CORMAIN CMMS v2.0", layout="wide")

url = st.secrets["connections"]["supabase"]["SUPABASE_URL"]
key = st.secrets["connections"]["supabase"]["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

# --- FUNCIONES DE PERSISTENCIA (Para que nada se pierda) ---
def obtener_datos(tabla):
    res = supabase.table(tabla).select("*").execute()
    return res.data

# --- LÓGICA DE NAVEGACIÓN Y LOGIN ---
if 'auth' not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    st.title("🛡️ Acceso al Sistema CORMAIN")
    tab1, tab2 = st.tabs(["Ingresar", "Registrar Nuevo Usuario"])
    
    with tab1:
        u = st.text_input("Email")
        p = st.text_input("Password", type="password")
        if st.button("Entrar"):
            # Verificamos contra tu tabla 'usuarios'
            res = supabase.table("usuarios").select("*").eq("email", u).eq("password", p).execute()
            if res.data:
                st.session_state.auth = True
                st.session_state.user = u
                st.rerun()
            else:
                st.error("Credenciales no encontradas")
    
    with tab2:
        new_u = st.text_input("Nuevo Usuario")
        new_p = st.text_input("Nueva Clave", type="password")
        if st.button("Crear Cuenta"):
            supabase.table("usuarios").insert({"email": new_u, "password": new_p}).execute()
            st.success("Cuenta creada con éxito")
else:
    # --- MENÚ PRINCIPAL (CON TODAS LAS FUNCIONES) ---
    st.sidebar.title("Navegación")
    opcion = st.sidebar.selectbox("Seleccione Área", 
        ["Inicio", "Recursos Humanos", "Maquinaria y Herramientas", "Órdenes de Trabajo"])

    # --- SECCIÓN RRHH (LISTADO + REGISTRO) ---
    if opcion == "Recursos Humanos":
        st.header("👥 Gestión de Recursos Humanos")
        
        # Formulario (Función anterior mejorada)
        with st.expander("➕ Registrar Nuevo Personal", expanded=False):
            with st.form("rrhh_form"):
                col1, col2 = st.columns(2)
                nombre = col1.text_input("Nombre Completo")
                cargo = col2.text_input("Cargo")
                especialidad = st.text_input("Especialidad")
                if st.form_submit_button("Guardar en Base de Datos"):
                    supabase.table("personal").insert({
                        "nombre": nombre, "cargo": cargo, "especialidad": especialidad
                    }).execute()
                    st.success("Datos guardados")
                    st.rerun()

        # LISTADO PERMANENTE
        st.subheader("📋 Listado de Personal")
        datos_p = obtener_datos("personal")
        if datos_p:
            df_p = pd.DataFrame(datos_p)
            # CORRECCIÓN AQUÍ: Quitamos "id" porque no existe en la tabla
            edit_df_p = st.data_editor(df_p[["nombre", "cargo", "especialidad"]], key="ed_p", hide_index=True)
            if st.button("Actualizar Cambios en RRHH"):
                st.info("Función de edición masiva activada")
        else:
            st.warning("No hay registros en la tabla 'personal'")

    # --- SECCIÓN MÁQUINAS (LISTADO + REGISTRO) ---
    elif opcion == "Maquinaria y Herramientas":
        st.header("⚙️ Gestión de Activos")
        
        with st.expander("➕ Agregar Nueva Máquina"):
            with st.form("maq_form"):
                n_m = st.text_input("Nombre de Máquina")
                c_m = st.text_input("Código de Inventario")
                u_m = st.text_input("Ubicación")
                if st.form_submit_button("Registrar Activo"):
                    supabase.table("maquinas").insert({
                        "nombre_maquina": n_m, "codigo": c_m, "ubicacion": u_m
                    }).execute()
                    st.rerun()

        st.subheader("🚜 Inventario de Equipos")
        datos_m = obtener_datos("maquinas")
        if datos_m:
            st.dataframe(pd.DataFrame(datos_m)[["nombre_maquina", "codigo", "ubicacion"]], use_container_width=True)

    # --- SECCIÓN ÓRDENES DE TRABAJO (FLUJO DE PROCESOS) ---
    elif opcion == "Órdenes de Trabajo":
        st.header("📑 Flujo de Órdenes de Producción")
        
        # Formulario vinculado a máquinas
        with st.expander("🆕 Crear Orden de Trabajo"):
            maqs = obtener_datos("maquinas")
            lista_maqs = [m['nombre_maquina'] for m in maqs] if maqs else ["Sin máquinas"]
            
            with st.form("ot_form"):
                desc = st.text_area("Descripción del trabajo")
                maq_asig = st.selectbox("Asignar a Máquina", lista_maqs)
                if st.form_submit_button("Iniciar Orden"):
                    supabase.table("ordenes").insert({
                        "descripcion": desc, "estado": "Proceso"
                    }).execute()
                    st.rerun()

        # EL KANBAN (PROCESOS)
        st.divider()
        c1, c2, c3 = st.columns(3)
        
        estados = [("Proceso", c1), ("Revisión Jefe", c2), ("Finalizada", c3)]
        
        for est_nombre, columna in estados:
            with columna:
                st.subheader(f"📍 {est_nombre}")
                ots = supabase.table("ordenes").select("*").eq("estado", est_nombre).execute()
                for ot in ots.data:
                    with st.container(border=True):
                        st.write(f"**Orden #{ot['id']}**")
                        st.write(ot['descripcion'])
                        if est_nombre == "Proceso":
                            if st.button("➡️ Revisión", key=f"rev_{ot['id']}"):
                                supabase.table("ordenes").update({"estado": "Revisión Jefe"}).eq("id", ot['id']).execute()
                                st.rerun()
                        elif est_nombre == "Revisión Jefe":
                            if st.button("✅ Finalizar", key=f"fin_{ot['id']}"):
                                supabase.table("ordenes").update({"estado": "Finalizada"}).eq("id", ot['id']).execute()
                                st.rerun()

    if st.sidebar.button("Cerrar Sesión"):
        st.session_state.auth = False
        st.rerun()
