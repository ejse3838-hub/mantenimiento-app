import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# 1. Configuración visual
st.set_page_config(page_title="CORMAIN - Sistema de Mantenimiento", page_icon="🛠️")
st.image("https://cdn-icons-png.flaticon.com/512/1063/1063376.png", width=100) # Icono de ejemplo
st.title("CORMAIN")
st.subheader("Registro de Usuarios")

# 2. Conexión Estable con Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# Función para leer datos de forma segura
def obtener_usuarios():
    try:
        # Lee la pestaña "Usuarios" del Excel
        return conn.read(worksheet="Usuarios", ttl=0)
    except Exception:
        # Si la hoja está vacía, crea un DataFrame con las columnas necesarias
        return pd.DataFrame(columns=["name", "username", "password"])

# 3. Formulario de Registro
with st.form("registro_cormain"):
    nombre = st.text_input("Nombre Completo")
    email = st.text_input("Usuario (ID o Correo)")
    clave = st.text_input("Contraseña", type="password")
    
    submit = st.form_submit_button("Crear mi cuenta en CORMAIN")

if