import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# 1. Configuración de la página
st.set_page_config(page_title="CORMAIN", page_icon="🛠️")
st.title("🛠️ CORMAIN")

# 2. Conexión con Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# Función para cargar usuarios
def cargar_usuarios():
    try:
        return conn.read(worksheet="Usuarios", ttl=0)
    except:
        return pd.DataFrame(columns=["name", "username", "password"])

# 3. Menú Lateral para navegar
menu = st.sidebar.selectbox("Selecciona una opción", ["Iniciar Sesión", "Registrarse"])

if menu == "Iniciar Sesión":
    st.subheader("Acceso al Sistema")
    user_input = st.text_input("Usuario (Correo)")
    pass_input = st.text_input("Contraseña", type="password")
    
    if st.button("Entrar"):
        df = cargar_usuarios()
        # Verificar si el usuario y contraseña coinciden
        validar = df[(df['username'] == user_input) & (df['password'] == pass_input)]
        
        if not validar.empty:
            nombre_usuario = validar.iloc[0]['name']
            st.success(f"✅ ¡Bienvenido de nuevo, {nombre_usuario}!")
            st.balloons()
            # Aquí podrías poner el resto de tu app de mantenimiento
            st.info("Próximamente: Panel de Gestión de Mantenimiento.")
        else:
            st.error("❌ Usuario o contraseña incorrectos.")

elif menu == "Registrarse":
    st.subheader("Crea tu nueva cuenta")
    with st.form("registro_form"):
        nombre = st.text_input("Nombre Completo")
        nuevo_usuario = st.text_input("Usuario (Correo)")
        nueva_clave = st.text_input("Contraseña", type="password")
        submit = st.form_submit_button("Crear mi cuenta en CORMAIN")

    if submit:
        if nombre and nuevo_usuario and nueva_clave:
            df_existente = cargar_usuarios()
            if nuevo_usuario in df_existente['username'].values:
                st.warning("⚠️ Este usuario ya existe.")
            else:
                nuevo_df = pd.concat([df_existente, pd.DataFrame([{"name": nombre, "username": nuevo_usuario, "password": nueva_clave}])], ignore_index=True)
                conn.update(worksheet="Usuarios", data=nuevo_df)
                st.success("✅ Registro exitoso. Ahora puedes Iniciar Sesión en el menú lateral.")
        else:
            st.warning("Por favor, llena todos los campos.")