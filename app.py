import streamlit as st
import pandas as pd

# Configuración
st.set_page_config(page_title="CORMAIN", page_icon="🛠️")
st.title("🛠️ CORMAIN")

# Link del Excel (el mismo de tus secrets)
URL = "https://docs.google.com/spreadsheets/d/1j9BYnypEdWlsIIoXgTCkLwb_Mq9YoTrlZRNc6KPZzsk/export?format=csv&gid=0"

def cargar_datos():
    try:
        # Leemos el Excel como un CSV público
        df = pd.read_csv(URL)
        # Limpiamos nombres de columnas y datos (quita espacios y pone en minúsculas)
        df.columns = df.columns.str.strip().str.lower()
        df['username'] = df['username'].astype(str).str.strip()
        df['password'] = df['password'].astype(str).str.strip()
        return df
    except Exception as e:
        st.error(f"Error al leer la base de datos: {e}")
        return None

menu = st.sidebar.selectbox("Menú", ["Iniciar Sesión", "Registrarse"])

if menu == "Iniciar Sesión":
    st.subheader("Acceso de Usuario")
    u = st.text_input("Usuario (Correo)").strip()
    p = st.text_input("Contraseña", type="password").strip()
    
    if st.button("Entrar"):
        df = cargar_datos()
        if df is not None:
            # Buscamos coincidencia exacta
            match = df[(df['username'] == u) & (df['password'] == p)]
            
            if not match.empty:
                st.success(f"✅ ¡Bienvenido {match.iloc[0]['name']}!")
                st.balloons()
            else:
                st.error("❌ No te encontré. Revisa que el usuario y clave sean iguales al Excel.")
                # Muestra lo que la app está viendo (solo para pruebas)
                st.write("Usuarios en la base de datos:", df[['name', 'username']])

elif menu == "Registrarse":
    st.info("Para registrarte, por ahora escríbelo en el Excel mientras arreglamos el permiso de escritura.")