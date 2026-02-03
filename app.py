# --- SECCIÓN RRHH (CORREGIDA) ---
    if opcion == "Recursos Humanos":
        st.header("👥 Gestión de Recursos Humanos")
        
        with st.expander("➕ Registrar Nuevo Personal", expanded=False):
            with st.form("rrhh_form"):
                col1, col2 = st.columns(2)
                nombre = col1.text_input("Nombre Completo")
                cargo = col2.text_input("Cargo")
                especialidad = st.text_input("Especialidad")
                if st.form_submit_button("Guardar en Base de Datos"):
                    if nombre and cargo: # Verificamos que no esté vacío
                        supabase.table("personal").insert({
                            "nombre": nombre, "cargo": cargo, "especialidad": especialidad
                        }).execute()
                        st.success("✅ Personal guardado con éxito")
                        st.rerun()
                    else:
                        st.error("Por favor llena los campos obligatorios")

        st.subheader("📋 Listado de Personal")
        datos_p = obtener_datos("personal")
        if datos_p:
            df_p = pd.DataFrame(datos_p)
            
            # CORRECCIÓN: Quitamos "id" de la lista porque no existe en tu tabla
            columnas_visibles = ["nombre", "cargo", "especialidad"]
            
            # Mostramos el editor solo con las columnas que sí existen
            edit_df_p = st.data_editor(
                df_p[columnas_visibles], 
                key="ed_p", 
                hide_index=True, 
                use_container_width=True
            )
            
            if st.button("💾 Guardar cambios en el listado"):
                st.info("Función de actualización masiva en desarrollo")
        else:
            st.warning("Aún no hay personal registrado en la base de datos")
