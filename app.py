import streamlit as st
import streamlit_authenticator as stauth
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="CORMAIN", layout="wide", page_icon="🛠️")

# Conexión a Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# --- 1. CARGAR USUARIOS DESDE EL EXCEL ---
try:
    df_usuarios = conn.read(worksheet="Usuarios")
    # Convertimos el Excel a un formato que el login entienda
    user_dict = {}
    for index, row in df_usuarios.iterrows():
        user_dict[row['username']] = {"name": row['name'], "password": row['password']}
except:
    # Si el Excel está vacío, dejamos a emilio123 por defecto para no quedar fuera
    user_dict = {"emilio123": {"name": "Emilio", "password": "abc123"}}

config = {
    "credentials": {"usernames": user_dict},
    "cookie": {"expiry_days": 30, "key": "cormain_key", "name": "cormain_cookie"}
}

authenticator = stauth.Authenticate(
    config['credentials'], config['cookie']['name'], config['cookie']['key'], config['cookie']['expiry_days']
)

# --- 2. LÓGICA DE REGISTRO (BOTÓN QUE FALTABA) ---
if not st.session_state.get("authentication_status"):
    with st.expander("🆕 ¿No tienes cuenta? Regístrate aquí"):
        with st.form("registro"):
            n_nombre = st.text_input("Nombre Completo")
            n_usuario = st.text_input("Usuario (ID)")
            n_clave = st.text_input("Contraseña", type="password")
            if st.form_submit_button("Crear mi cuenta en CORMAIN"):
                # Crear fila nueva
                nueva_data = pd.DataFrame([[n_nombre, n_usuario, n_clave]], 
                                         columns=['name', 'username', 'password'])
                # Combinar con lo existente y guardar
                df_actual = conn.read(worksheet="Usuarios")
                df_final = pd.concat([df_actual, nueva_data], ignore_index=True)
                conn.update(worksheet="Usuarios", data=df_final)
                st.success("¡Cuenta creada! Ya puedes loguearte arriba.")

# --- 3. LOGIN ---
authenticator.login(location='main')

if st.session_state["authentication_status"]:
    authenticator.logout("Cerrar Sesión", "sidebar")
    st.title("🛠️ CORMAIN")
    
    menu = ["Recursos Humanos", "Órdenes de Trabajo"]
    choice = st.sidebar.selectbox("Módulos", menu)

    if choice == "Recursos Humanos":
        st.header("👤 Registro de Personal")
        with st.form("rrhh_form"):
            nom = st.text_input("Nombre")
            cod = st.text_input("Código")
            em = st.text_input("Email")
            cel = st.text_input("Celular")
            if st.form_submit_button("Guardar en Base de Datos"):
                # Guardar en la pestaña Personal
                nueva_fila = pd.DataFrame([[nom, cod, em, cel, st.session_state['username']]], 
                                         columns=['Nombre', 'Codigo', 'Email', 'Celular', 'Registrado_Por'])
                df_pers = conn.read(worksheet="Personal")
                df_res = pd.concat([df_pers, nueva_fila], ignore_index=True)
                conn.update(worksheet="Personal", data=df_res)
                st.balloons()
                st.success("¡Datos guardados en el Excel!")

elif st.session_state["authentication_status"] is False:
    st.error("Usuario o contraseña incorrectos")