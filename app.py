import streamlit as st
from supabase import create_client, Client

# Configuración inicial
st.set_page_config(page_title="CORMAIN CMMS", layout="wide")

# Conexión
url = st.secrets["connections"]["supabase"]["SUPABASE_URL"]
key = st.secrets["connections"]["supabase"]["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

# --- LÓGICA DE SESIÓN ---
if 'auth' not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    st.title("Sistema CORMAIN")
    tab1, tab2 = st.tabs(["Iniciar Sesión", "Registrarse"])
    
    with tab1:
        u = st.text_input("Correo")
        p = st.text_input("Clave", type="password")
        if st.button("Entrar"):
            res = supabase.table("usuarios").select("*").eq("email", u).eq("password", p).execute()
            if res.data:
                st.session_state.auth = True
                st.session_state.user = u
                st.rerun()
            else:
                st.error("Credenciales incorrectas")
                
    with tab2:
        new_u = st.text_input("Nuevo Correo")
        new_p = st.text_input("Nueva Clave", type="password")
        if st.button("Crear Cuenta"):
            supabase.table("usuarios").insert({"email": new_u, "password": new_p}).execute()
            st.success("¡Registrado! Ya puedes iniciar sesión.")

else:
    # --- MENÚ PRINCIPAL ---
    st.sidebar.title(f"Bienvenido")
    st.sidebar.write(st.session_state.user)
    opcion = st.sidebar.selectbox("Menú", ["RRHH", "Máquinas", "Órdenes de Trabajo"])
    
    if st.sidebar.button("Cerrar Sesión"):
        st.session_state.auth = False
        st.rerun()

    # --- SECCIÓN RRHH ---
    if opcion == "RRHH":
        st.header("Gestión de Personal")
        with st.form("form_rrhh"):
            nombre = st.text_input("Nombre Completo")
            cargo = st.text_input("Cargo")
            especialidad = st.text_input("Especialidad")
            if st.form_submit_button("Guardar Empleado"):
                supabase.table("personal").insert({"nombre": nombre, "cargo": cargo, "especialidad": especialidad}).execute()
                st.success("Empleado registrado")

    # --- SECCIÓN MÁQUINAS ---
    elif opcion == "Máquinas":
        st.header("Inventario de Equipos")
        with st.form("form_maquina"):
            nom_m = st.text_input("Nombre de la Máquina")
            cod_m = st.text_input("Código/ID")
            ubi_m = st.text_input("Ubicación")
            if st.form_submit_button("Registrar Máquina"):
                supabase.table("maquinas").insert({"nombre_maquina": nom_m, "codigo": cod_m, "ubicacion": ubi_m, "estado": "Activa"}).execute()
                st.success("Máquina agregada")

    # --- SECCIÓN ÓRDENES (FLUJO DE TRABAJO) ---
    elif opcion == "Órdenes de Trabajo":
        st.header("Flujo de Producción y Mantenimiento")
        
        # 1. Crear Orden
        with st.expander("➕ Crear Nueva Orden"):
            maquinas_res = supabase.table("maquinas").select("nombre_maquina").execute()
            lista_m = [m['nombre_maquina'] for m in maquinas_res.data]
            
            desc = st.text_area("Descripción de la tarea")
            maq_sel = st.selectbox("Asignar a Máquina", lista_m)
            if st.button("Lanzar Orden"):
                supabase.table("ordenes").insert({"descripcion": desc, "estado": "Proceso"}).execute()
                st.rerun()

        # 2. Visualización por estados (Tu flujo)
        cols = st.columns(3)
        estados = ["Proceso", "Revisión Jefe", "Finalizada"]
        
        for i, est in enumerate(estados):
            with cols[i]:
                st.subheader(f"📍 {est}")
                ordenes = supabase.table("ordenes").select("*").eq("estado", est).execute()
                for o in ordenes.data:
                    with st.container(border=True):
                        st.write(f"ID: {o['id']}")
                        st.write(o['descripcion'])
                        if est == "Proceso":
                            if st.button(f"Enviar a Revisión", key=f"btn_{o['id']}"):
                                supabase.table("ordenes").update({"estado": "Revisión Jefe"}).eq("id", o['id']).execute()
                                st.rerun()
                        elif est == "Revisión Jefe":
                            if st.button(f"Finalizar Orden", key=f"btn_{o['id']}"):
                                supabase.table("ordenes").update({"estado": "Finalizada"}).eq("id", o['id']).execute()
                                st.rerun()
