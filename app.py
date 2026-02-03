import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# Configuración de la página
st.set_page_config(page_title="CORMAIN", page_icon="🛠️")
st.title("🛠️ CORMAIN")

# Conectamos con el Robot (usa los Secrets que ya pegaste)
conn = st.connection("gsheets", type=GSheetsConnection)

# Menú lateral
menu = st.sidebar.selectbox("Menú", ["Iniciar Sesión", "Registrarse"])

# Función para leer usuarios
def cargar_usuarios():
    # Forzamos la conexión a usar la URL de los secrets
    conn = st.connection("gsheets", type=GSheetsConnection)
    url = st.secrets["connections"]["gsheets"]["spreadsheet"]
    return conn.read(spreadsheet=url, worksheet="Usuarios", ttl=0)
    
if menu == "Registrarse":
    st.subheader("Crear nueva cuenta")
    with st.form("form_registro"):
        nombre = st.text_input("Nombre Completo")
        usuario = st.text_input("Usuario (Correo)")
        clave = st.text_input("Contraseña", type="password")
        boton = st.form_submit_button("Registrarme en CORMAIN")

    if boton:
        if nombre and usuario and clave:
            df_actual = cargar_usuarios()
            # Creamos la nueva fila
            nuevo_dato = pd.DataFrame([{"name": nombre, "username": usuario, "password": clave}])
            # La unimos a la tabla actual
            df_final = pd.concat([df_actual, nuevo_dato], ignore_index=True)
            # ¡EL ROBOT ESCRIBE EN EL EXCEL!
            conn.update(worksheet="Usuarios", data=df_final)
            st.success(f"✅ ¡Excelente! {nombre}, ya estás en la base de datos.")
            st.balloons()
        else:
            st.warning("Por favor, llena todos los campos.")

elif menu == "Iniciar Sesión":
    st.subheader("Acceso Personal")
    u = st.text_input("Usuario")
    p = st.text_input("Contraseña", type="password")
    
    if st.button("Entrar"):
        df = cargar_usuarios()
        # Buscamos si existe
        check = df[(df['username'] == u) & (df['password'] == p)]
        if not check.empty:
            st.success(f"Bienvenido de nuevo, {check.iloc[0]['name']}")
        else:

            st.error("Usuario o clave no encontrados.")

