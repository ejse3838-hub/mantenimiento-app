# --- 3. MAQUINARIA (SINCRONIZACIÓN TOTAL) ---
    elif st.session_state.menu == "⚙️ Maquinaria":
        st.header("Ficha Técnica de Equipos")
        with st.form("f_maq"):
            c1, c2, c3 = st.columns(3)
            # Mapeo exacto a tus columnas de Supabase
            nm = c1.text_input("Nombre Máquina")
            cod = c2.text_input("Código")
            ubi = c3.text_input("Ubicación")
            
            fab = c1.text_input("Fabricante")
            mod = c2.text_input("Modelo")
            ser = c3.text_input("Serial")
            
            est = c1.selectbox("Estado", ["Operativa", "Falla", "Mantenimiento"])
            hu = c2.number_input("Horas Uso", min_value=0)
            fc = c3.date_input("Fecha Compra")
            
            a1 = st.text_area("Apartado 1 (Especificaciones)")
            a2 = st.text_area("Apartado 2 (Notas)")
            
            if st.form_submit_button("Registrar Máquina"):
                # ESTA ES LA LÍNEA QUE DABA EL ERROR 140
                # Los nombres de la izquierda DEBEN ser idénticos a los de tu Supabase
                supabase.table("maquinas").insert({
                    "nombre_maquina": nm,
                    "codigo": cod,
                    "ubicacion": ubi,
                    "estado": est,
                    "serial": ser,
                    "fabricante": fab,
                    "modelo": mod,
                    "horas_uso": hu,
                    "fecha_compra": str(fc),
                    "apartado1": a1,
                    "apartado2": a2,
                    "creado_por": st.session_state.user
                }).execute()
                st.success("¡Máquina registrada correctamente!")
                st.rerun()
        
        # Mostrar tabla respetando el diseño
        df_m = pd.DataFrame(cargar("maquinas"))
        if not df_m.empty:
            st.dataframe(df_m.drop(columns=['id', 'creado_por'], errors='ignore'), use_container_width=True)
