import streamlit as st
from supabase import create_client, Client

# 1. Conexión (Ya la tienes bien)
url = st.secrets["connections"]["supabase"]["SUPABASE_URL"]
key = st.secrets["connections"]["supabase"]["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

def cargar_usuarios():
    response = supabase.table("usuarios").select("*").execute()
    return response.data

# --- LÓGICA DE NAVEGACIÓN ---
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    st.title("CORMAIN - Login")
    email_input = st.text_input("Correo")
    pass_input = st.text_input("Contraseña", type="password")
    
    if st.button("Entrar"):
        usuarios = cargar_usuarios()
        if any(u['email'] == email_input and u['password'] == pass_input for u in usuarios):
            st.session_state.autenticado = True
            st.rerun()
        else:
            st.error("Credenciales incorrectas")

else:
    # --- AQUÍ EMPIEZA LO QUE TE FALTABA: EL MENÚ ---
    st.sidebar.title("Menú Principal")
    opcion = st.sidebar.selectbox(
        "Seleccione una opción",
        ["Inicio", "Recursos Humanos", "Órdenes de Trabajo", "Inventario"]
    )

    if opcion == "Inicio":
        st.title("Bienvenido a CORMAIN")
        st.write("Seleccione una opción en el menú de la izquierda para comenzar.")

    elif opcion == "Recursos Humanos":
        st.title("Gestión de Recursos Humanos")
        # Aquí puedes poner tus st.text_input para nombres, cargos, etc.
        st.write("Formulario de personal aquí...")

    elif opcion == "Órdenes de Trabajo":
        st.title("Órdenes de Trabajo")
        # Aquí puedes poner el formulario para las órdenes
        st.write("Registro de órdenes...")

    if st.sidebar.button("Cerrar Sesión"):
        st.session_state.autenticado = False
        st.rerun()
