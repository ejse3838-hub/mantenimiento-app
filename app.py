import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# 1. Configuración de la página
st.set_page_config(page_title="CORMAIN", page_icon="🛠️")
st.title("🛠️ CORMAIN")

# 2. Conexión con Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# Función para leer los usuarios del Excel
def cargar_usuarios():
    try:
        # Lee la pestaña "Usuarios"
        return conn.read(worksheet="Usuarios", ttl=0)
    except:
        # Si hay error o está vacía, devuelve una estructura básica
        return pd.DataFrame(columns=["name", "username", "password"])

# 3. Menú de navegación en la barra lateral
menu = st.sidebar.selectbox("Menú", ["Iniciar Sesión", "Registrarse"])

if menu == "Iniciar Sesión":
    st.subheader("Acceso para Personal Registrado")
    user_login = st.text_input("Usuario (Correo)")
    pass_login = st.text_input("Contraseña", type="password")
    
    if st.button("Entrar"):
        df = cargar_usuarios()
        # Buscamos si el usuario y clave existen en el Excel
        usuario_valido = df[(df['username'] == user_login) & (df['password'] == pass_login)]
        
        if not usuario_valido.empty:
            nombre_real = usuario_valido.iloc[0]['name']
            st.success(f"✅ ¡Bienvenido, {nombre_real}!")
            st.balloons()
            # Aquí irá tu futuro panel de control
            st.info("Ya estás dentro del sistema. Pronto activaremos el panel de reportes.")
        else:
            st.error("❌ Usuario o contraseña no encontrados. Por favor, regístrate si no tienes cuenta.")

elif menu == "Registrarse":
    st.subheader("Crea tu cuenta nueva")
    with st.form("form_registro"):
        nuevo_nombre = st.text_input("Nombre Completo")
        nuevo_user = st.text_input("Usuario (Correo)")
        nueva_clave = st.text_input("Contraseña", type="password")
        boton_registro = st.form_submit_button("Crear mi cuenta en CORMAIN")
        
    if boton_registro:
        if nuevo_nombre and nuevo_user and nueva_clave:
            df_actual = cargar_usuarios()
            
            # Evitar que se registren correos repetidos
            if nuevo_user in df_actual['username'].values:
                st.warning("⚠️ Este correo ya está registrado. Intenta iniciar sesión.")
            else:
                # Agregar el nuevo usuario
                nuevo_dato = pd.DataFrame([{"name": nuevo_nombre, "username": nuevo_user, "password": nueva_clave}])
                df_final = pd.concat([df_actual, nuevo_dato], ignore_index=True)
                
                # Guardar en el Excel
                conn.update(worksheet="Usuarios", data=df_final)
                st.success("✅ ¡Cuenta creada con éxito! Ahora cambia a 'Iniciar Sesión' en el menú de la izquierda.")
        else:
            st.warning("Por favor, llena todos los campos.")