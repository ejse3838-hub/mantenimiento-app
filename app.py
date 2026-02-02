import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# Configuración de la página
st.set_page_config(page_title="CORMAIN - Gestión de Mantenimiento", layout="centered")

# Título de la app
st.title("🛠️ CORMAIN")
st.subheader("Registro de Usuarios")

# Crear la conexión con Google Sheets
# Asegúrate de que en Secrets el link termine en /edit#gid=0
conn = st.connection("gsheets", type=GSheetsConnection)

# --- FUNCIÓN PARA LEER DATOS ---
def cargar_datos():
    try:
        # Forzamos la lectura de la pestaña "Usuarios"
        return conn.read(worksheet="Usuarios", ttl=0)
    except Exception as e:
        st.error(f"Error al conectar con la pestaña 'Usuarios': {e}")
        return None

# --- FORMULARIO DE REGISTRO ---
with st.form("registro_form"):
    nombre = st.text_input("Nombre Completo")
    usuario = st.text_input("Usuario (ID o Correo)")
    password = st.text_input("Contraseña", type="password")
    
    boton_registro = st.form_submit_state = st.form_submit_button("Crear mi cuenta en CORMAIN")

if boton_registro:
    if nombre and usuario and password:
        df_actual = cargar_datos()
        
        if df_actual is not None:
            # Crear el nuevo registro
            nuevo_usuario = pd.DataFrame([{
                "name": nombre,
                "username": usuario,
                "password": password
            }])
            
            # Combinar datos antiguos con el nuevo
            df_actualizado = pd.concat([df_actual, nuevo_usuario], ignore_index=True)
            
            # Guardar en Google Sheets
            try:
                conn.update(worksheet="Usuarios", data=df_actualizado)
                st.success(f"✅ ¡Bienvenido {nombre}! Cuenta creada con éxito.")
                st.balloons()
            except Exception as e:
                st.error(f"Error al guardar en el Excel: {e}")
    else:
        st.warning("Por favor, rellena todos los campos.")