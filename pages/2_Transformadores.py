import streamlit as st
import json
import math

# --- FUNCIÓN DE CONFIGURACIÓN (sin cambios) ---
def cargar_configuracion():
    ruta_config = 'config.json'
    try:
        with open(ruta_config, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        st.error(f"Error: Archivo '{ruta_config}' no encontrado.")
        return None

# --- INICIALIZAR EL ESTADO DE LA SESIÓN ---
if 'results_transformador' not in st.session_state:
    st.session_state.results_transformador = None

default_mano_obra = 3000000
default_poste_montaje = 8000000
default_materiales_menores = 2000000
default_gestoria = 1500000

config = cargar_configuracion()
if config:
    costos_transformadores_config_full = config.get("costos_transformadores", {}) # Ahora es un dict con "monofasico" y "trifasico"
    tarifas_ande_config = config.get("tarifas_ande", {})
    costos_instalacion_config = config.get("costos_instalacion_transformador", {})
    costos_generales_config = config.get("costos_materiales_generales", {})

    default_mano_obra = costos_instalacion_config.get("mano_obra_base_gs", default_mano_obra)
    default_poste_montaje = costos_generales_config.get("puesto_distribucion_completo", default_poste_montaje)
    default_materiales_menores = costos_instalacion_config.get("materiales_menores_bt_gs", default_materiales_menores)
    default_gestoria = costos_generales_config.get("gestoria_y_permisos", default_gestoria)
else:
    costos_transformadores_config_full = {}
    tarifas_ande_config = {}

# Inicializar session_state para los inputs
if "tr_tipo_transformador" not in st.session_state:
    st.session_state.tr_tipo_transformador = "Trifásico" # Default
if "tr_potencia_kva_input" not in st.session_state:
    st.session_state.tr_potencia_kva_input = 60.0
if "tr_fp_trafo" not in st.session_state:
    st.session_state.tr_fp_trafo = 0.92
if "tr_mano_obra" not in st.session_state:
    st.session_state.tr_mano_obra = default_mano_obra
if "tr_poste_montaje" not in st.session_state:
    st.session_state.tr_poste_montaje = default_poste_montaje
if "tr_materiales_menores" not in st.session_state:
    st.session_state.tr_materiales_menores = default_materiales_menores
if "tr_gestoria" not in st.session_state:
    st.session_state.tr_gestoria = default_gestoria

# --- TÍTULO Y LAYOUT ---
st.header("💡 Dimensionamiento y Estimación de Costos de Transformadores")
st.markdown("---")
col1, col2 = st.columns([1, 1.2])

# --- COLUMNA IZQUIERDA: PANEL DE CONTROL ---
with col1:
    st.markdown("<h5>⚙️ Parámetros de Carga y Costos de Instalación</h5>", unsafe_allow_html=True)

    with st.container(border=True):
        st.subheader("1. Datos de la Carga y Tipo de Transformador")
        # --- CAMBIO CLAVE N°1: SELECTOR DE TIPO DE TRANSFORMADOR ---
        st.radio(
            "Tipo de Transformador Requerido",
            ["Trifásico", "Monofásico"],
            horizontal=True,
            key="tr_tipo_transformador"
        )
        st.number_input("Potencia Aparente de Carga (kVA)", min_value=1.0, step=1.0, key="tr_potencia_kva_input")
        st.slider("Factor de Potencia de la Carga (cos φ)", 0.70, 1.00, step=0.01, key="tr_fp_trafo")

    with st.container(border=True):
        st.subheader("2. Costos Adicionales de Instalación (Gs.)")
        st.number_input("Mano de Obra", min_value=0, step=100000, format="%d", key="tr_mano_obra")
        st.number_input("Poste y Montaje", min_value=0, step=100000, format="%d", key="tr_poste_montaje")
        st.number_input("Materiales Menores BT", min_value=0, step=100000, format="%d", key="tr_materiales_menores")
        st.number_input("Gestoría y Permisos", min_value=0, step=100000, format="%d", key="tr_gestoria")

    if st.button("Calcular Estimación del Transformador", use_container_width=True):
        # --- CAMBIO CLAVE N°2: LEER VALORES DE SESSION_STATE ---
        tipo_trafo_seleccionado = st.session_state.tr_tipo_transformador.lower() # "monofasico" o "trifasico"
        kVA_requerido_input = st.session_state.tr_potencia_kva_input
        fp_carga_input = st.session_state.tr_fp_trafo

        # Obtener la lista correcta de costos de transformadores
        costos_transformadores_especificos = costos_transformadores_config_full.get(tipo_trafo_seleccionado, {})

        if not costos_transformadores_especificos:
            st.error(f"No se encontraron costos para transformadores de tipo '{tipo_trafo_seleccionado}' en `config.json`.")
            st.session_state.results_transformador = None # Limpiar resultados previos
        else:
            potencia_kw_calculada = kVA_requerido_input * fp_carga_input
            capacidades_comerciales_kVA = sorted([float(k) for k in costos_transformadores_especificos.keys()])
            kVA_sugerido = None
            for cap in capacidades_comerciales_kVA:
                if cap >= kVA_requerido_input:
                    kVA_sugerido = cap
                    break
            if kVA_sugerido is None and capacidades_comerciales_kVA:
                kVA_sugerido = capacidades_comerciales_kVA[-1]

            costo_transformador_sugerido = 0
            if kVA_sugerido is not None:
                 costo_transformador_sugerido = costos_transformadores_especificos.get(str(kVA_sugerido).replace('.0', ''), 0) # Quitar .0 si es float

            derecho_conexion_ande = 0
            if kVA_sugerido is not None and tarifas_ande_config:
                # La lógica actual de ANDE no distingue monofasico/trifasico directamente, solo por kVA.
                # Esto se podría refinar si las tarifas de ANDE tienen una distinción explícita.
                if kVA_sugerido <= 100:
                    derecho_conexion_ande = tarifas_ande_config.get("derecho_conexion_bt_fijo", 0)
                else:
                    derecho_conexion_ande = tarifas_ande_config.get("derecho_conexion_bt_variable_por_kva", 0) * kVA_sugerido

            costo_total_estimado = (
                costo_transformador_sugerido +
                derecho_conexion_ande +
                st.session_state.tr_mano_obra +
                st.session_state.tr_poste_montaje +
                st.session_state.tr_materiales_menores +
                st.session_state.tr_gestoria
            )

            st.session_state.results_transformador = {
                "tipo_trafo_seleccionado": st.session_state.tr_tipo_transformador, # Guardar tipo
                "kVA_requerido_input": kVA_requerido_input,
                "potencia_kw_calculada": potencia_kw_calculada,
                "kVA_sugerido": kVA_sugerido,
                "costo_transformador_sugerido": costo_transformador_sugerido,
                "derecho_conexion_ande": derecho_conexion_ande,
                "costo_mano_obra": st.session_state.tr_mano_obra,
                "costo_poste_montaje": st.session_state.tr_poste_montaje,
                "costo_materiales_menores": st.session_state.tr_materiales_menores,
                "costo_gestoria": st.session_state.tr_gestoria,
                "costo_total_estimado": costo_total_estimado
            }

# --- COLUMNA DERECHA: MONITOR DE RESULTADOS ---
with col2:
    st.markdown("<h5>📊 Estimación del Proyecto de Transformación</h5>", unsafe_allow_html=True)

    if st.session_state.results_transformador:
        res = st.session_state.results_transformador

        with st.container(border=True):
            st.subheader(f"Resumen del Transformador ({res['tipo_trafo_seleccionado']})") # Mostrar tipo
            st.metric("Potencia Aparente de Carga (Ingresada)", f"{res['kVA_requerido_input']:.2f} kVA")
            st.metric("Potencia Activa de Carga (Calculada)", f"{res['potencia_kw_calculada']:.2f} kW")

            if res['kVA_sugerido'] is not None:
                st.success(f"Se sugiere un transformador **{res['tipo_trafo_seleccionado']}** de: **{res['kVA_sugerido']} kVA**")
                st.metric("Costo del Transformador (Solo Equipo)", f"Gs. {int(res['costo_transformador_sugerido']):,}")
            else:
                st.error(f"No se encontró un transformador {res['tipo_trafo_seleccionado']} estándar para la carga especificada.")

        st.markdown("---")

        with st.container(border=True):
            st.subheader("Desglose de Costos Estimados (Gs.)")
            cost_items = [
                ("Transformador (Equipo)", res['costo_transformador_sugerido']),
                ("Derecho de Conexión ANDE", res['derecho_conexion_ande']),
                ("Mano de Obra", res['costo_mano_obra']),
                ("Poste y Montaje", res['costo_poste_montaje']),
                ("Materiales Menores BT", res['costo_materiales_menores']),
                ("Gestoría y Permisos", res['costo_gestoria'])
            ]
            for item, costo in cost_items:
                st.write(f"**{item}:** {int(costo):,}")
            st.markdown("---")
            st.metric("**COSTO TOTAL ESTIMADO DEL PROYECTO**", f"Gs. {int(res['costo_total_estimado']):,}", label_visibility="visible")
            st.caption("Nota: Todos los costos son estimaciones y deben ser verificados.")
    else:
        st.info("Configure los parámetros de carga y costos, luego presione 'Calcular Estimación'.")
