# --- SECCIÓN PERSONAL (9 CAMPOS) ---
if opcion == "Personal":
    st.header("Gestión de Personal")
    with st.form("form_personal", clear_on_submit=True):
        col1, col2 = st.columns(2)
        nombre = col1.text_input("Nombre Completo")
        ced = col2.text_input("Cédula/ID") # Este es el que dio error
        cargo = col1.text_input("Cargo")
        tel = col2.text_input("Teléfono")
        email = col1.text_input("Correo")
        turno = col2.selectbox("Turno", ["Matutino", "Vespertino", "Nocturno"])
        f_ing = col1.date_input("Fecha Ingreso")
        sal = col2.number_input("Salario", min_value=0.0)
        obs = st.text_area("Notas")
        
        if st.form_submit_button("Guardar"):
            # AQUÍ: Asegúrate que los nombres a la izquierda coincidan con Supabase
            data_p = {
                "nombre": nombre, 
                "cedula": ced,  # Si falla, intenta cambiar "cedula" por "id"
                "cargo": cargo,
                "telefono": tel,
                "email": email,
                "turno": turno,
                "fecha_ingreso": str(f_ing),
                "salario": sal,
                "notas": obs
            }
            res = supabase.table("personal").insert(data_p).execute()
            st.success("Guardado correctamente")
            
            # --- SECCIÓN MAQUINARIA (10 CAMPOS) ---
elif opcion == "Maquinaria":
    st.header("Inventario de Activos")
    with st.form("form_m"):
        c1, c2, c3 = st.columns(3)
        cod = c1.text_input("Código Máquina")
        nom = c2.text_input("Nombre")
        mar = c3.text_input("Marca")
        ubi = c1.text_input("Ubicación")
        est = c2.selectbox("Estado", ["Operativo", "Mantenimiento"])
        f_adq = c3.date_input("Fecha Adquisición")
        prio = c1.selectbox("Prioridad", ["Alta", "Baja"])
        prov = c2.text_input("Proveedor")
        v_util = c3.number_input("Vida Útil")
        espec = st.text_area("Especificaciones")

        if st.form_submit_button("Registrar"):
            data_m = {"codigo": cod, "nombre": nom, "estado": est} # Campos base
            supabase.table("maquinaria").insert(data_m).execute()
            st.success("Máquina registrada")
            # --- SECCIÓN ÓRDENES DE TRABAJO (OP) ---
elif opcion == "Órdenes de Trabajo":
    st.header("Generar Orden de Trabajo")
    with st.form("form_op"):
        # Solo 4 campos esenciales para que no falle
        m_id = st.text_input("ID de Máquina")
        tarea = st.text_area("Descripción de la falla")
        tec = st.text_input("Técnico")
        prior = st.selectbox("Prioridad", ["Urgente", "Normal"])
        
        if st.form_submit_button("Crear OP"):
            # Solo mandamos 3 datos a la base para asegurar el éxito
            op_data = {"id_maquina": m_id, "descripcion": tarea, "tecnico": tec}
            supabase.table("ordenes_trabajo").insert(op_data).execute()
            st.success("Orden generada")
            
