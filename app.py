import streamlit as st

st.set_page_config(page_title="Software Mantenimiento", layout="wide")

# --- NAVEGACIÓN ---
menu = ["Órdenes de Trabajo (OT)", "Recursos Humanos", "Activos (Herramientas)", "Plan de Tareas"]
choice = st.sidebar.selectbox("Módulos del Sistema", menu)

# --- MÓDULO 1: OTs ---
if choice == "Órdenes de Trabajo (OT)":
    st.header("📋 Tablero de Control de OTs")
    col1, col2, col3, col4 = st.columns(4)
    with col1: st.info("#### Pendientes")
    with col2: st.warning("#### En Proceso")
    with col3: st.error("#### En Revisión")
    with col4: st.success("#### Finalizadas")

# --- MÓDULO 2: RRHH ---
elif choice == "Recursos Humanos":
    st.header("👤 Gestión de Personal")
    with st.form("form_rrhh"):
        c1, c2 = st.columns(2)
        c1.text_input("Nombre")
        c1.text_input("Apellidos")
        c1.text_input("Código")
        c1.selectbox("Clasificación 1", ["Técnico", "Mecánico", "Eléctrico"])
        c2.text_input("Email")
        c2.number_input("Valor por hora ($)", min_value=0.0)
        c2.text_input("Dirección")
        c2.text_input("Celular")
        st.form_submit_button("Guardar Datos")

# --- MÓDULO 3: ACTIVOS ---
elif choice == "Activos (Herramientas)":
    st.header("⚙️ Inventario de Activos")
    with st.form("form_activos"):
        c1, c2 = st.columns(2)
        c1.text_input("Nombre Máquina")
        c1.text_input("Fabricante")
        c1.text_input("Modelo")
        c2.text_input("Número Serial")
        c2.date_input("Fecha de Compra")
        c2.number_input("Horas de uso", min_value=0)
        st.selectbox("Anclar a Plan de Tarea", ["Plan Preventivo Semanal", "Revisión Mensual"])
        st.form_submit_button("Registrar Activo")

# --- MÓDULO 4: PLAN DE TAREAS ---
elif choice == "Plan de Tareas":
    st.header("📅 Planificación de Tareas")
    with st.form("form_tareas"):
        st.text_area("Descripción de la tarea")
        c1, c2 = st.columns(2)
        c1.text_input("Clasificación 1")
        c1.selectbox("Prioridad", ["Baja", "Media", "Alta", "Urgente"])
        c2.number_input("Duración estimada (h)", min_value=0.5)
        c2.checkbox("¿Requiere paro de máquina?")
        st.write("---")
        st.subheader("Frecuencia y Repetición")
        st.text_input("Cada cuánto (Ej: 100 horas o 30 días)")
        st.checkbox("Repetir por siempre", value=True)
        st.form_submit_button("Crear Plan de Tarea")
