import streamlit as st
from supabase import create_client, Client
import pandas as pd
from datetime import datetime

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="COMAIN - CMMS Industrial", layout="wide", page_icon="🛠️")

# --- 2. CONEXIÓN (Usando tu llave sb_secret confirmada) ---
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except Exception as e:
    st.error("Error en Secrets. Revisa la configuración en Streamlit Cloud.")
    st.stop()

# --- 3. MENÚ LATERAL ---
st.sidebar.title("🛠️ COMAIN")
menu = st.sidebar.radio("Navegación", ["Dashboard", "Personal", "Maquinaria", "Órdenes de Trabajo"])

# --- 4. SECCIÓN PERSONAL (9 CAMPOS) ---
if menu == "Personal":
    st.header("👥 Gestión de Personal")
    with st.form("form_p", clear_on_submit=True):
        c1, c2 = st.columns(2)
        nombre = c1.text_input("Nombre Completo")
        # Si da error en 'cedula', cámbialo por el nombre que tengas en Supabase
        ced = c2.text_input("Cédula / Identificación") 
        cargo = c1.text_input("Cargo")
        tel = c2.text_input("Teléfono")
        email = c1.text_input("Correo Electrónico")
        turno = c2.selectbox("Turno", ["Matutino", "Vespertino", "Nocturno"])
        f_ing = c1.date_input("Fecha de Ingreso")
        salario = c2.number_input("Salario Mensual", min_value=0.0)
        obs = st.text_area("Observaciones")
        
        if st.form_submit_button("Guardar Empleado"):
            datos_p = {
                "nombre": nombre, 
                "cedula": ced, # Asegúrate que en Supabase se llame 'cedula'
                "cargo": cargo, 
                "telefono": tel, 
                "email": email, 
                "turno": turno,
                "fecha_ingreso": str(f_ing), 
                "salario": salario, 
                "notas": obs
            }
            try:
                supabase.table("personal").insert(datos_p).execute()
                st.success(f"✅ {nombre} registrado correctamente.")
            except Exception as e:
                st.error(f"Error: {e}")
                st.info("💡 Consejo: Revisa si en tu base de datos la columna se llama 'cedula' o 'identificacion'.")

# --- 5. SECCIÓN MAQUINARIA (10 CAMPOS) ---
elif menu == "Maquinaria":
    st.header("⚙️ Inventario de Activos")
    with st.form("form_m", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        cod = c1.text_input("Código de Máquina")
        nom = c2.text_input("Nombre/Modelo")
        mar = c3.text_input("Marca")
        ubi = c1.text_input("Ubicación")
        est = c2.selectbox("Estado", ["Operativo", "En Mantenimiento", "Falla Crítica"])
        f_adq = c3.date_input("Fecha Adquisición")
        prio = c1.selectbox("Prioridad", ["Alta", "Media", "Baja"])
        prov = c2.text_input("Proveedor")
        v_util = c3.number_input("Vida Útil (Años)", min_value=1)
        espec = st.text_area("Especificaciones Técnicas")

        if st.form_submit_button("Registrar Activo"):
            datos_m = {
                "codigo": cod, "nombre": nom, "marca": mar, "ubicacion": ubi,
                "estado": est, "fecha_adquisicion": str(f_adq), "prioridad": prio,
                "proveedor": prov, "vida_util": v_util, "especificaciones": espec
            }
            try:
                supabase.table("maquinaria").insert(datos_m).execute()
                st.success("✅ Máquina registrada.")
            except Exception as e:
                st.error(f"Error al guardar: {e}")

# --- 6. ÓRDENES DE TRABAJO (CAMPOS REDUCIDOS) ---
elif menu == "Órdenes de Trabajo":
    st.header("📝 Órdenes de Trabajo (OT)")
    with st.expander("➕ Generar Nueva Orden"):
        with st.form("form_ot"):
            m_id = st.text_input("Código o ID de Máquina")
            tipo = st.selectbox("Tipo de Mantenimiento", ["Preventivo", "Correctivo", "Predictivo"])
            tec = st.text_input("Técnico Responsable")
            desc = st.text_area("Descripción de la Tarea")
            
            if st.form_submit_button("Generar Orden"):
                datos_ot = {
                    "id_maquina": m_id, 
                    "tipo": tipo, 
                    "tecnico": tec, 
                    "descripcion": desc,
                    "fecha": str(datetime.now().date()), 
                    "estado": "Abierta"
                }
                try:
                    supabase.table("ordenes_trabajo").insert(datos_ot).execute()
                    st.success("✅ Orden generada con éxito.")
                except Exception as e:
                    st.error(f"Error: {e}")

    st.divider()
    st.subheader("📋 Historial de Órdenes")
    try:
        res = supabase.table("ordenes_trabajo").select("*").execute()
        if res.data:
            df = pd.DataFrame(res.data)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No hay órdenes registradas.")
    except:
        st.warning("No se pudo cargar la tabla de órdenes.")

# --- 7. DASHBOARD ---
elif menu == "Dashboard":
    st.header("📊 Resumen del Sistema")
    col1, col2, col3 = st.columns(3)
    try:
        m_qty = len(supabase.table("maquinaria").select("id").execute().data)
        p_qty = len(supabase.table("personal").select("id").execute().data)
        ot_qty = len(supabase.table("ordenes_trabajo").select("id").execute().data)
        
        col1.metric("Activos Totales", m_qty)
        col2.metric("Personal Activo", p_qty)
        col3.metric("Órdenes Generadas", ot_qty)
    except:
        st.info("Cargando indicadores... (Asegúrate de tener datos en las tablas)")
