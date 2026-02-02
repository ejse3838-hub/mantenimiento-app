import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# 1. Configuración de la página
st.set_page_config(page_title="CORMAIN", page_icon="🛠️")
st.title("🛠️ CORMAIN")
st.subheader("Registro de Usuarios")

# 2. Conexión con Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# 3. Formulario de Registro
with st.form("registro_cormain"):
    nombre = st.text_input("Nombre Completo")
    usuario = st.text_input("Usuario (ID o Correo)")
    clave = st.text_input("Contraseña", type="password")
    submit = st.form_submit_button("Crear mi cuenta en CORMAIN")

if submit:
    if nombre and usuario and clave:
        try:
            # Leer datos existentes de la pestaña "Usuarios"
            df_existente = conn.read(worksheet="Usuarios", ttl=0)
            
            # Crear el nuevo registro
            nuevo_usuario = pd.DataFrame([{"name": nombre, "username": usuario, "password": clave}])
            
            # Unir datos nuevos con los viejos
            df_final = pd.concat([df_existente, nuevo_usuario], ignore_index=True)
            
            # Guardar todo de vuelta en el Excel
            conn.update(worksheet="Usuarios", data=df_final)
            
            st.success(f"✅ ¡Bienvenido {nombre}! Usuario registrado en el Excel.")
            st.balloons()
        except Exception as e:
            st.error(f"Hubo un problema: {e}")
    else:
        st.warning("Por favor, llena todos los campos.")