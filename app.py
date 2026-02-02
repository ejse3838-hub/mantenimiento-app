import streamlit as st
import streamlit_authenticator as stauth

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Software Mantenimiento Pro", layout="wide")

# --- 1. CONFIGURACIÓN DE USUARIOS (NUEVO FORMATO) ---
credentials = {
    "usernames": {
        "emilio123": {
            "name": "Emilio Silva",
            "password": "abc123"  # En el futuro esto irá encriptado
        },
        "admin": {
            "name": "Admin Principal",
            "password": "admin123"
        }
    }
}

# Crear el objeto de autenticación
# Usamos 'mantenimiento_db' como nombre de la cookie para que sea única
authenticator = stauth.Authenticate(
    credentials,
    "mantenimiento_cookie",
    "signature_key",
    cookie_expiry_days=30
)

# --- 2. PANTALLA DE LOGIN ---
# El método login ahora devuelve el nombre, el estado y el usuario
# (La nueva versión requiere especificar el nombre del formulario)
nombre, autenticado, usuario = authenticator.login("Login", "main")

if autenticado:
    # --- TODO ESTO SOLO SE VE SI EL LOGIN ES EXITOSO ---
    
    # Botón de cierre de sesión y bienvenida
    authenticator.logout("Cerrar Sesión", "sidebar")
    st.sidebar.success(f"Bienvenido, {nombre}")
    
    st.title("🛠️ Sistema de Gestión de Mantenimiento")

    # --- NAVEGACIÓN ---
    menu = ["Órdenes de Trabajo (OT)", "Recursos Humanos", "Activos"]
    choice = st.sidebar.selectbox("Módulos del Sistema", menu)

    if choice == "Recursos Humanos":
        st.header("👤 Gestión de Personal")
        with st.form("form_rrhh"):
            c1, c2 = st.columns(2)
            nombre_pers = c1.text_input("Nombre")
            apellido_pers = c1.text_input("Apellidos")
            codigo = c1.text_input("Código")
            clase = c1.selectbox("Clasificación", ["Técnico", "Mecánico", "Eléctrico"])
            
            email = c2.text_input("Email")
            pago = c2.number_input("Valor por hora ($)", min_value=0.0)
            direccion = c2.text_input("Dirección")
            celular = c2.text_input("Celular")
            
            if st.form_submit_button("Guardar Datos"):
                # Aquí conectaremos luego Google Sheets
                st.balloons()
                st.success(f"¡Empleado {nombre_pers} registrado con éxito por {nombre}!")

    elif choice == "Órdenes de Trabajo (OT)":
        st.header("📋 Tablero de OTs")
        st.info("Módulo de seguimiento en construcción.")

# --- MENSAJES DE ERROR ---
elif autenticado == False:
    st.error("Usuario o contraseña incorrectos.")
elif autenticado == None:
    st.warning("Por favor, ingresa tus credenciales.")