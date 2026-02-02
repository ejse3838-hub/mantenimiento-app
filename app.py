import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# 1. Configuración de la interfaz
st.set_page_config(page_title="CORMAIN", page_icon="🛠️")
st.title("🛠️ CORMAIN")

# 2. Conexión con Google Sheets (Lectura y Escritura)
conn = st.connection("gsheets", type=GSheetsConnection)

def cargar_datos():
    try:
        # Forzamos lectura fresca de la pestaña "Usuarios"
        return conn.read(worksheet="Usuarios", ttl=0)
    except:
        return pd.DataFrame(columns=["name", "username", "password"])

# 3. Menú de navegación lateral
menu = st.sidebar.selectbox("Seleccione una opción", ["Iniciar Sesión", "Registrarse"])

if menu == "Iniciar Sesión":
    st.subheader("Acceso al Panel de Control")
    user_input = st.text_input("Usuario (Correo)")
    pass_input = st.text_input("Contraseña", type="password")
    
    if st.button("Entrar"):
        df = cargar_datos()
        # Verificamos si coinciden usuario y clave en el Excel
        user_db = df[(df['username'] == user_input) & (df['password'] == pass_input)]
        
        if not user_db.empty:
            nombre = user_db.iloc[0]['name']
            st.success(f"✅ ¡Bienvenido, {nombre}!")
            st.balloons()
            st.info("Próximamente: Aquí verás tus reportes de mantenimiento.")
        else:
            st.error("❌ Credenciales incorrectas o usuario no registrado.")

elif menu == "Registrarse":
    st.subheader("Crear nueva cuenta")
    with st.form("registro_form"):
        nuevo_nombre = st.text_input("Nombre Completo")
        nuevo_user = st.text_input("Usuario (Correo)")
        nueva_pass = st.text_input("Contraseña", type="password")
        submit = st.form_submit_button("Crear mi cuenta en CORMAIN")

    if submit:
        if nuevo_nombre and nuevo_user and nueva_pass:
            df_actual = cargar_datos()
            if nuevo_user in df_actual['username'].values:
                st.warning("⚠️ Este correo ya está registrado.")
            else:
                # Preparamos la nueva fila
                nuevo_usuario = pd.DataFrame([{"name": nuevo_nombre, "username": nuevo_user, "password": nueva_pass}])
                # Concatenamos y actualizamos
                df_final = pd.concat([df_actual, nuevo_usuario], ignore_index=True)
                
                try:
                    conn.update(worksheet="Usuarios", data=df_final)
                    st.success("✅ ¡Registro exitoso! Ya puedes iniciar sesión en el menú de la izquierda.")
                except Exception as e:
                    st.error(f"Error al guardar: Asegúrate de que el Excel esté compartido como EDITOR.")
        else:
            st.warning("Por favor, completa todos los campos.")