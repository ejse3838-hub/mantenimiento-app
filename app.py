import streamlit as st
import streamlit_authenticator as stauth

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Software Mantenimiento Pro", layout="wide")

# --- 1. CONFIGURACIÓN DE USUARIOS ---
# En el futuro, estos nombres y claves vendrán de tu base de datos
nombres = ["Emilio Silva", "Admin Principal", "Tecnico Invitado"]
usuarios = ["emilio123", "admin", "user01"]
# NOTA: En una app real usaremos claves encriptadas, por ahora usamos estas para probar:
claves = ["abc123", "admin123", "clave456"] 

# Crear el objeto de autenticación
authenticator = stauth.Authenticate(
    nombres, usuarios, claves, 
    "mantenimiento_cookie", "signature_key", cookie_expiry_days=30
)

# --- 2. PANTALLA DE LOGIN ---
nombre, autenticado, usuario = authenticator.login("Iniciar Sesión", "main")

if autenticado:
    # --- TODO ESTO SOLO SE VE SI EL USUARIO ENTRA CORRECTAMENTE ---
    
    # Botón para salir en la barra lateral
    authenticator.logout("Cerrar Sesión", "sidebar")
    st.sidebar.write(f"👋 Bienvenido, **{nombre}**")
    
    st.title("🛠️ Sistema de Gestión de Mantenimiento")
    st.markdown(f"### Sesión activa: {usuario}")

    # --- NAVEGACIÓN ---
    menu = ["Órdenes de Trabajo (OT)", "Recursos Humanos", "Activos", "Plan de Tareas"]
    choice = st.sidebar.selectbox("Módulos del Sistema", menu)

    # --- MÓDULO 1: OTs ---
    if choice == "Órdenes de Trabajo (OT)":
        st.header("📋 Tablero de Control de OTs")
        col1, col2, col3, col4 = st.columns(4)
        col1.info("#### Pendientes")
        col2.warning("#### En Proceso")
        col3.error("#### En Revisión")
        col4.success("#### Finalizadas")

    # --- MÓDULO 2: RRHH ---
    elif choice == "Recursos Humanos":
        st.header("👤 Gestión de Personal")
        with st.form("form_rrhh"):
            c1, c2 = st.columns(2)
            c1.text_input("Nombre")
            c1.text_input("Apellidos")
            c1.text_input("Código")
            c1.selectbox("Clasificación", ["Técnico", "Mecánico", "Eléctrico"])
            c2.text_input("Email")
            c2.number_input("Valor por hora ($)", min_value=0.0)
            c2.text_input("Dirección")
            c2.text_input("Celular")
            
            if st.form_submit_button("Guardar Datos"):
                st.success(f"Datos de {nombre} procesados (Módulo en desarrollo)")

    # --- MÓDULO 3: ACTIVOS ---
    elif choice == "Activos":
        st.header("⚙️ Inventario de Activos")
        st.info("Aquí aparecerán las máquinas asignadas a tu usuario.")

# --- MENSAJES DE ERROR ---
elif autenticado == False:
    st.error("Usuario o contraseña incorrectos. Por favor, intenta de nuevo.")
elif autenticado == None:
    st.warning("Por favor, ingresa tus credenciales para acceder al software.")