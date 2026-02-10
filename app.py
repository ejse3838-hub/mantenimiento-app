import streamlit as st
from supabase import create_client, Client
import pandas as pd
from datetime import datetime

# --- CONFIGURACIÓN INICIAL ---
st.set_page_config(page_title="COMAIN - Sistema de Mantenimiento", layout="wide")

# Conexión con la llave sb_secret que funcionó
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except Exception as e:
    st.error("Error al conectar. Verifica tus Secrets.")
    st.stop()

# --- MENÚ ---
st.sidebar.title("COMAIN")
opcion = st.sidebar.radio("Ir a:", ["Dashboard", "Personal", "Maquinaria", "Órdenes de Trabajo"])

# --- 1. SECCIÓN PERSONAL (9 CAMPOS) ---
if opcion == "Personal":
    st.header("Gestión de Personal")
    with st.form("form_personal", clear_on_submit=True):
        c1, c2 = st.columns(2)
        nombre = c1.text_input("Nombre Completo")
        cedula = c2.text_input("Cédula/ID")
        cargo = c1.text_input("Cargo")
        telefono = c2.text_input("Teléfono")
        email = c1.text_input("Correo Electrónico")
        turno = c2.selectbox("Turno", ["Matutino", "Vespertino", "Nocturno"])
        f_ingreso = c1.date_input("Fecha de Ingreso")
        salario = c2.number_input("Salario Mensual", min_value=0.0)
        observaciones = st.text_area("Observaciones del empleado")
        
        if st.form_submit_button("Guardar Personal"):
            data = {
                "nombre": nombre, "cedula": cedula, "cargo": cargo,
                "telefono": telefono, "email": email, "turno": turno,
                "fecha_ingreso": str(f_ingreso), "salario": salario, "notas": observaciones
            }
            try:
                supabase.table("personal").insert(data).execute()
                st.success(f"Empleado {nombre} registrado con éxito.")
            except Exception as e:
                st.error(f"Error al guardar: {e}")

# --- 2. SECCIÓN MAQUINARIA (10 CAMPOS) ---
elif opcion == "Maquinaria":
    st.header("Inventario de Maquinaria")
    with st.form("form_maquina", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        codigo = c1.text_input("Código de Máquina")
        nombre_m = c2.text_input("Nombre/Modelo")
        marca = c3.text_input("Marca")
        ubicacion = c1.text_input("Ubicación en Planta")
        estado = c2.selectbox("Estado Actual", ["Operativo", "En Mantenimiento", "Crítico"])
        f_adquisicion = c3.date_input("Fecha de Adquisición")
        prioridad = c1.selectbox("Prioridad", ["Alta", "Media", "Baja"])
        proveedor = c2.text_input("Proveedor")
        vida_util = c3.number_input("Vida Útil (Años)", min_value=1)
        notas_tecnicas = st.text_area("Especificaciones Técnicas")

        if st.form_submit_button("Registrar Máquina"):
            data_m = {
                "codigo": codigo, "nombre": nombre_m, "marca": marca,
                "ubicacion": ubicacion, "estado": estado, "fecha_adquisicion": str(f_adquisicion),
                "prioridad": prioridad, "proveedor": proveedor, "vida_util": vida_util, "especificaciones": notas_tecnicas
            }
            try:
                supabase.table("maquinaria").insert(data_m).execute()
                st.success("Máquina registrada correctamente.")
            except Exception as e:
                st.error(f"Error al guardar maquinaria: {e}")

# --- 3. ÓRDENES DE TRABAJO (CAMPOS REDUCIDOS PARA EVITAR ERRORES) ---
elif opcion == "Órdenes de Trabajo":
    st.header("Órdenes de Trabajo (OT)")
    
    # Formulario simplificado para asegurar que se guarde
    with st.expander("Crear Nueva Orden de Trabajo"):
        with st.form("form_ot"):
            tipo = st.selectbox("Tipo de Mantenimiento", ["Preventivo", "Correctivo", "Predictivo"])
            maquina_id = st.text_input("Código de la Máquina")
            tecnico = st.text_input("Técnico Asignado")
            descripcion = st.text_area("Descripción del Trabajo")
            
            if st.form_submit_button("Generar Orden"):
                data_ot = {
                    "tipo": tipo,
                    "id_maquina": maquina_id,
                    "tecnico": tecnico,
                    "descripcion": descripcion,
                    "fecha_creacion": str(datetime.now().date()),
                    "estado": "Abierta"
                }
                try:
                    supabase.table("ordenes_trabajo").insert(data_ot).execute()
                    st.success("Orden de trabajo generada con éxito.")
                except Exception as e:
                    st.error(f"Error al generar OT: {e}. Revisa si los nombres de las columnas coinciden en Supabase.")

    # Visualización de órdenes actuales
    st.subheader("Historial de Órdenes")
    try:
        res = supabase.table("ordenes_trabajo").select("*").execute()
        if res.data:
            st.dataframe(pd.DataFrame(res.data))
        else:
            st.info("No hay órdenes registradas todavía.")
    except:
        st.warning("No se pudo cargar la tabla. Asegúrate de que la tabla 'ordenes_trabajo' existe en Supabase.")

# --- 4. DASHBOARD (RESUMEN) ---
elif opcion == "Dashboard":
    st.header("Resumen del Sistema COMAIN")
    try:
        m_data = supabase.table("maquinaria").select("id", count="exact").execute()
        p_data = supabase.table("personal").select("id", count="exact").execute()
        ot_data = supabase.table("ordenes_trabajo").select("id", count="exact").execute()
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Máquinas Totales", m_data.count if m_data.count else 0)
        col2.metric("Personal Activo", p_data.count if p_data.count else 0)
        col3.metric("Órdenes Pendientes", ot_data.count if ot_data.count else 0)
    except:
        st.info("Agregue datos en las otras secciones para ver las métricas aquí.")
