import streamlit as st
from supabase import create_client, Client
import pandas as pd
from datetime import datetime

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="COMAIN - CMMS Industrial", layout="wide")

# --- 2. CONEXIÓN (Usando tu llave sb_secret) ---
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except Exception as e:
    st.error("Error en Secrets. Revisa la configuración en Streamlit Cloud.")
    st.stop()

# --- 3. LÓGICA DE NAVEGACIÓN ---
st.sidebar.title("🛠️ COMAIN")
menu = st.sidebar.radio("Navegación", ["Dashboard", "Personal", "Maquinaria", "Órdenes de Trabajo"])

# --- 4. SECCIÓN PERSONAL (9 CAMPOS) ---
if menu == "Personal":
    st.header("👥 Gestión de Talento Humano")
    with st.form("form_p", clear_on_submit=True):
        c1, c2 = st.columns(2)
        nombre = c1.text_input("Nombre Completo")
        # Si sigue saliendo error de columna, cambia 'cedula' por el nombre exacto en tu DB
        ced = c2.text_input("Cédula / ID") 
        cargo = c1.text_input("Cargo")
        tel = c2.text_input("Teléfono")
        email = c1.text_input("Correo Electrónico")
        turno = c2.selectbox("Turno", ["Matutino", "Vespertino", "Nocturno"])
        f_ing = c1.date_input("Fecha de Ingreso")
        salario = c2.number_input("Salario Mensual", min_value=0.0)
        obs = st.text_area("Observaciones")
        
        if st.form_submit_button("Guardar Empleado"):
            datos_p = {
                "nombre": nombre, "cedula": ced, "cargo": cargo, 
                "telefono": tel, "email": email, "turno": turno,
                "fecha_ingreso": str(f_ing), "salario": salario, "notas": obs
            }
            try:
                supabase.table("personal").insert(datos_p).execute()
                st.success(f"✅ {nombre} registrado correctamente.")
            except Exception as e:
                st.error(f"Error: {e}")

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
        v_util = c3.number_input("Vida Útil (Años)")
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

# --- 6. ÓRDENES DE TRABAJO (CAMPOS REDUCIDOS PARA EVITAR ERRORES) ---
elif menu == "Órdenes de Trabajo":
    st.header("📝 Órdenes de Trabajo (OP)")
    with st.expander("Nueva Orden"):
        with st.form("form_op"):
            m_id = st.text_input("Código de Máquina")
            tipo = st.selectbox("Tipo", ["Preventivo", "Correctivo"])
            tec = st.text_input("Técnico Responsable")
            desc = st.text_area("Descripción de la Tarea")
            
            if st.form_submit_button("Generar OP"):
                datos_op = {
                    "id_maquina": m_id, "tipo": tipo, 
                    "tecnico": tec, "descripcion": desc,
                    "fecha": str(datetime.now().date()), "estado": "Abierta"
                }
                try:
                    supabase.table("ordenes_trabajo").insert(datos_op).execute()
                    st.success("✅ Orden generada.")
                except Exception as e:
                    st.error(f"Error: {e}")

    # Ver historial
    st.subheader("Historial de Mantenimiento")
    try:
        res = supabase.table("ordenes_trabajo").select("*").execute()
        if res.data:
            st.dataframe(pd.DataFrame(res.data))
    except:
        st.info("No hay datos para mostrar.")

# --- 7. DASHBOARD ---
elif menu == "Dashboard":
    st.header("📊 Resumen Gerencial")
    col1, col2, col3 = st.columns(3)
    try:
        # Conteos rápidos para indicadores
        m_qty = len(supabase.table("maquinaria").select("id").execute().data)
        p_qty = len(supabase.table("personal").select("id").execute().data)
        op_qty = len(supabase.table("ordenes_trabajo").select("id").execute().data)
        
        col1.metric("Activos", m_qty)
        col2.metric("Personal", p_qty)
        col3.metric("OPs Totales", op_qty)
    except:
        st.warning("Cargando indicadores...")
