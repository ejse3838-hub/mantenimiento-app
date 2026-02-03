import streamlit as st
import pandas as pd
from supabase import create_client, Client

# 1. CONFIGURACIÓN Y CONEXIÓN
st.set_page_config(page_title="CORMAIN CMMS v2.0", layout="wide")

url = st.secrets["connections"]["supabase"]["SUPABASE_URL"]
key = st.secrets["connections"]["supabase"]["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

# --- FUNCIONES DE PERSISTENCIA ---
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
    # --- MENÚ PRINCIPAL ---
    st.sidebar.title("Navegación")
    opcion = st.sidebar.selectbox("Seleccione Área", 
        ["Inicio", "Recursos Humanos", "Maquinaria y Herramientas", "Órdenes de Trabajo"])

    # --- SECCIÓN RRHH (CON EDICIÓN DIRECTA) ---
    if opcion == "Recursos Humanos":
        st.header("👥 Gestión de Recursos Humanos")
        with st.expander("➕ Registrar Nuevo Personal"):
            with st.form("rrhh_form"):
                nombre = st.text_input("Nombre Completo")
                cargo = st.text_input("Cargo")
                especialidad = st.text_input("Especialidad")
                if st.form_submit_button("Guardar"):
                    supabase.table("personal").insert({"nombre": nombre, "cargo": cargo, "especialidad": especialidad}).execute()
                    st.rerun()

        st.subheader("📋 Listado de Personal (Editable)")
        datos_p = obtener_datos("personal")
        if datos_p:
            df_p = pd.DataFrame(datos_p)
            # Filtramos columnas existentes para evitar KeyError
            cols_visibles = [c for c in ["nombre", "cargo", "especialidad"] if c in df_p.columns]
            st.data_editor(df_p[cols_visibles], key="edit_rrhh", use_container_width=True)
            st.info("💡 Haz doble clic en cualquier celda para corregir nombres o cargos.")

    # --- SECCIÓN MÁQUINAS (CON EDICIÓN DIRECTA) ---
    elif opcion == "Maquinaria y Herramientas":
        st.header("⚙️ Gestión de Activos")
        with st.expander("➕ Agregar Nueva Máquina"):
            with st.form("maq_form"):
                n_m = st.text_input("Nombre de Máquina")
                c_m = st.text_input("Código")
                u_m = st.text_input("Ubicación")
                if st.form_submit_button("Registrar"):
                    supabase.table("maquinas").insert({"nombre_maquina": n_m, "codigo": c_m, "ubicacion": u_m}).execute()
                    st.rerun()

        st.subheader("🚜 Inventario de Equipos (Editable)")
        datos_m = obtener_datos("maquinas")
        if datos_m:
            df_m = pd.DataFrame(datos_m)
            cols_m = [c for c in ["nombre_maquina", "codigo", "ubicacion"] if c in df_m.columns]
            st.data_editor(df_m[cols_m], key="edit_maq", use_container_width=True)

    # --- SECCIÓN ÓRDENES DE TRABAJO (CORRECCIÓN FINAL) ---
    elif opcion == "Órdenes de Trabajo":
        st.header("📑 Flujo de Producción")
        
        # 1. Obtenemos máquinas y sus IDs correctamente
        maqs_db = obtener_datos("maquinas")
        dict_maquinas = {m['nombre_maquina']: m.get('id') for m in maqs_db} if maqs_db else {}
        lista_nombres = list(dict_maquinas.keys()) if dict_maquinas else ["Sin máquinas"]

        with st.expander("🆕 Crear Orden"):
            with st.form("ot_form"):
                desc = st.text_area("Descripción")
                maq_asig = st.selectbox("Asignar a Máquina", lista_nombres)
                if st.form_submit_button("Iniciar"):
                    if desc and maq_asig != "Sin máquinas":
                        id_m = dict_maquinas[maq_asig]
                        # Aseguramos que id_maquina se envíe para evitar el APIError
                        supabase.table("ordenes").insert({
                            "descripcion": desc, 
                            "estado": "Proceso",
                            "id_maquina": id_m
                        }).execute()
                        st.success("✅ Orden lanzada")
                        st.rerun()

        # KANBAN
        st.divider()
        c1, c2, c3 = st.columns(3)
        for est, col in [("Proceso", c1), ("Revisión Jefe", c2), ("Finalizada", c3)]:
            with col:
                st.subheader(f"📍 {est}")
                ots = supabase.table("ordenes").select("*").eq("estado", est).execute()
                for ot in ots.data:
                    with st.container(border=True):
                        st.write(f"**OT #{ot.get('id', 'N/A')}**")
                        st.write(ot['descripcion'])
                        # Movimiento de estados
                        if est == "Proceso":
                            if st.button("➡️ Revisión", key=f"r{ot['id']}"):
                                supabase.table("ordenes").update({"estado": "Revisión Jefe"}).eq("id", ot['id']).execute()
                                st.rerun()
                        elif est == "Revisión Jefe":
                            if st.button("✅ Finalizar", key=f"f{ot['id']}"):
                                supabase.table("ordenes").update({"estado": "Finalizada"}).eq("id", ot['id']).execute()
                                st.rerun()

    if st.sidebar.button("Cerrar Sesión"):
        st.session_state.auth = False
        st.rerun()
