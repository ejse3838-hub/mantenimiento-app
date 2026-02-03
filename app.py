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

# --- LÓGICA DE LOGIN ---
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
            st.success("Cuenta creada")
else:
    # --- MENÚ PRINCIPAL ---
    st.sidebar.title("Navegación")
    opcion = st.sidebar.selectbox("Seleccione Área", 
        ["Inicio", "Recursos Humanos", "Maquinaria y Herramientas", "Órdenes de Trabajo"])

    # --- SECCIÓN RRHH (EDITABLE) ---
    if opcion == "Recursos Humanos":
        st.header("👥 Gestión de Recursos Humanos")
        with st.expander("➕ Registrar Nuevo Personal"):
            with st.form("rrhh_form"):
                nombre = st.text_input("Nombre Completo")
                cargo = st.text_input("Cargo")
                esp = st.text_input("Especialidad")
                if st.form_submit_button("Guardar"):
                    supabase.table("personal").insert({"nombre": nombre, "cargo": cargo, "especialidad": esp}).execute()
                    st.rerun()

        st.subheader("📋 Listado de Personal (Edición habilitada)")
        datos_p = obtener_datos("personal")
        if datos_p:
            df_p = pd.DataFrame(datos_p)
            # Solo mostramos lo que existe para evitar KeyError
            cols = [c for c in ["nombre", "cargo", "especialidad"] if c in df_p.columns]
            st.data_editor(df_p[cols], use_container_width=True, key="edit_p")
            st.info("💡 Haz doble clic en una celda para corregir un nombre o cargo.")

    # --- SECCIÓN MÁQUINAS (EDITABLE) ---
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

        st.subheader("🚜 Inventario (Edición habilitada)")
        datos_m = obtener_datos("maquinas")
        if datos_m:
            df_m = pd.DataFrame(datos_m)
            cols_m = [c for c in ["nombre_maquina", "codigo", "ubicacion"] if c in df_m.columns]
            st.data_editor(df_m[cols_m], use_container_width=True, key="edit_m")

    # --- SECCIÓN ÓRDENES DE TRABAJO (CORRECCIÓN APIERROR) ---
    elif opcion == "Órdenes de Trabajo":
        st.header("📑 Flujo de Órdenes de Producción")
        
        # 1. Cargamos máquinas y mapeamos sus IDs para el insert
        maqs_db = obtener_datos("maquinas")
        # Diccionario seguro que evita el KeyError de las imágenes anteriores
        dict_maquinas = {m['nombre_maquina']: m.get('id', m.get('id_maquina')) for m in maqs_db} if maqs_db else {}
        lista_nombres = list(dict_maquinas.keys()) if dict_maquinas else ["Sin máquinas"]

        with st.expander("🆕 Crear Orden de Trabajo"):
            with st.form("ot_form"):
                desc = st.text_area("Descripción del trabajo")
                maq_sel = st.selectbox("Asignar a Máquina", lista_nombres)
                if st.form_submit_button("Iniciar Orden"):
                    if desc and maq_sel != "Sin máquinas":
                        # Enviamos el ID real de la máquina para evitar el APIError
                        id_final = dict_maquinas[maq_sel]
                        supabase.table("ordenes").insert({
                            "descripcion": desc, 
                            "estado": "Proceso",
                            "id_maquina": id_final
                        }).execute()
                        st.success("✅ Orden lanzada correctamente")
                        st.rerun()

        # TABLERO KANBAN
        st.divider()
        c1, c2, c3 = st.columns(3)
        for est, col in [("Proceso", c1), ("Revisión Jefe", c2), ("Finalizada", c3)]:
            with col:
                st.subheader(f"📍 {est}")
                ots = supabase.table("ordenes").select("*").eq("estado", est).execute()
                for ot in ots.data:
                    with st.container(border=True):
                        st.write(f"**Orden #{ot.get('id', 'N/A')}**")
                        st.write(ot['descripcion'])
                        # Botones de flujo
                        if est == "Proceso":
                            if st.button("➡️ Revisión", key=f"r_{ot['id']}"):
                                supabase.table("ordenes").update({"estado": "Revisión Jefe"}).eq("id", ot['id']).execute()
                                st.rerun()
                        elif est == "Revisión Jefe":
                            if st.button("✅ Finalizar", key=f"f_{ot['id']}"):
                                supabase.table("ordenes").update({"estado": "Finalizada"}).eq("id", ot['id']).execute()
                                st.rerun()

    if st.sidebar.button("Cerrar Sesión"):
        st.session_state.auth = False
        st.rerun()
