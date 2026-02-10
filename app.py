# --- 3. MAQUINARIA (FICHA TÉCNICA CORREGIDA) ---
    elif st.session_state.menu == "⚙️ Maquinaria":
        st.header("Gestión de Activos (Ficha Técnica)")
        with st.form("f_maq_full"):
            c1, c2, c3 = st.columns(3)
            n_m = c1.text_input("Nombre Máquina")
            cod_m = c2.text_input("Código de Máquina")
            ubi_m = c3.text_input("Ubicación") # Columna: ubicacion
            
            fab_m = c1.text_input("Fabricante")
            mod_m = c2.text_input("Modelo")
            ser_m = c3.text_input("Número Serial") # Columna: serial
            
            est_m = c1.selectbox("Estado", ["Operativa", "Falla", "Mantenimiento"])
            hrs_uso = c2.number_input("Horas de Uso", min_value=0)
            f_compra = c3.date_input("Fecha de Compra")
            
            ap1 = st.text_area("Apartado 1 (Especif. Técnicas)")
            ap2 = st.text_area("Apartado 2 (Ubicación/Notas)")
            
            if st.form_submit_button("Registrar Máquina"):
                # ESTA ES LA LÍNEA 145 QUE TE DABA ERROR
                # Asegúrate de que los nombres de la izquierda sean EXACTOS a Supabase
                supabase.table("maquinas").insert({
                    "nombre_maquina": n_m,
                    "codigo": cod_m,
                    "ubicacion": ubi_m,
                    "estado": est_m,
                    "serial": ser_m,
                    "fabricante": fab_m,
                    "modelo": mod_m,
                    "horas_uso": hrs_uso,
                    "fecha_compra": str(f_compra),
                    "apartado1": ap1,
                    "apartado2": ap2,
                    "creado_por": st.session_state.user
                }).execute()
                st.success("Máquina registrada con éxito")
                st.rerun()
        
        mlist = cargar("maquinas")
        if mlist:
            st.dataframe(pd.DataFrame(mlist).drop(columns=['id', 'creado_por'], errors='ignore'), use_container_width=True)
