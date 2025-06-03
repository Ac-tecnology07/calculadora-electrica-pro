import streamlit as st
import json
import cmath
import math
import pandas as pd

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
if 'results_cables' not in st.session_state:
    st.session_state.results_cables = None

# --- CARGA DE DATOS ---
config = cargar_configuracion()
if config:
    datos_cables_config = config.get("datos_cables_mt", [])
    # Creamos el diccionario aquí para que esté disponible globalmente en el script
    datos_cables = {cable['tipo']: cable for cable in datos_cables_config}

else:
    datos_cables = {}

# --- TÍTULO Y LAYOUT ---
st.header("📏 Análisis de Líneas de Media Tensión")
st.markdown("---")
col1, col2 = st.columns([1, 1.2])

# --- COLUMNA IZQUIERDA: PANEL DE CONTROL ---
with col1:
    st.markdown("<h5>⚙️ Parámetros de Entrada</h5>", unsafe_allow_html=True)
    with st.container(border=True):
        # Los widgets se definen aquí. Sus valores actuales se usarán
        # directamente dentro del bloque del botón.
        tipo_sistema = st.radio(
            "Tipo de Sistema Eléctrico",
            ["Trifásico", "Monofásico"],
            horizontal=True,
            key="tipo_sistema_cables"
        )

        default_voltage = 23.0 if tipo_sistema == 'Trifásico' else 13.2
        tension_kv_input = st.number_input(
            f"Tensión de Línea ({'L-L' if tipo_sistema == 'Trifásico' else 'L-N'}) (kV)",
            min_value=1.0,
            value=default_voltage,
            step=0.1,
            format="%.1f",
            key="tension_kv_cables_input" # Key diferente para el widget
        )

        potencia_kw_input = st.number_input("Potencia Activa (kW)", min_value=1.0, value=475.0, step=25.0)
        factor_potencia_input = st.slider("Factor de Potencia (cos φ)", 0.70, 1.00, 0.95, step=0.01)
        longitud_metros_input = st.slider(
            "Longitud de la Línea (metros)",
            min_value=1,
            max_value=30000,
            value=100,
            step=1,
        )

        if datos_cables:
            tipo_conductor_seleccionado_input = st.selectbox(
                "Seleccione el Conductor",
                options=list(datos_cables.keys())
            )
            cable_info_display = datos_cables[tipo_conductor_seleccionado_input]
            res_ohm_m = cable_info_display['resistencia_ohm_km'] / 1000
            react_ohm_m = cable_info_display['reactancia_ohm_km'] / 1000
            st.info(f"""
            **Conductor:** {tipo_conductor_seleccionado_input}
            - Resistencia: {res_ohm_m:.6f} Ω/m
            - Reactancia: {react_ohm_m:.6f} Ω/m
            """)
        else:
            st.error("Datos de cables no cargados.")
            tipo_conductor_seleccionado_input = None # Asegurarnos que está definido

        # Botón para ejecutar el análisis
        if st.button("▶️ Analizar Línea", use_container_width=True):
            if tipo_conductor_seleccionado_input: # Usamos el valor actual del widget
                # Los cálculos usan los valores actuales de los widgets
                longitud_km = longitud_metros_input / 1000.0
                potencia_kva = potencia_kw_input / (factor_potencia_input + 1e-9)
                tension_linea_V = tension_kv_input * 1000
                cable_info_calc = datos_cables[tipo_conductor_seleccionado_input]


                if tipo_sistema == 'Trifásico':
                    V_calculo_fase = tension_linea_V / (3**0.5)
                    corriente_A = (potencia_kva * 1000) / (tension_linea_V * (3**0.5))
                    factor_perdida_potencia = 3
                    num_conductores_costo = 3 # Costo para 3 conductores de fase
                else: # Monofásico
                    V_calculo_fase = tension_linea_V
                    corriente_A = (potencia_kva * 1000) / tension_linea_V
                    factor_perdida_potencia = 2
                    # --- CAMBIO EN EL COSTEO MONOFÁSICO ---
                    num_conductores_costo = 1 # Costo para 1 conductor de fase principal

                angulo_fp = math.acos(factor_potencia_input)
                I_fasor = cmath.rect(corriente_A, -angulo_fp)

                resistencia_total_conductor_fase = cable_info_calc['resistencia_ohm_km'] * longitud_km
                reactancia_total_conductor_fase = cable_info_calc['reactancia_ohm_km'] * longitud_km
                Z_linea_fase = complex(resistencia_total_conductor_fase, reactancia_total_conductor_fase)

                V_carga_fasor = V_calculo_fase - (I_fasor * Z_linea_fase)
                V_carga_magnitud_fase = abs(V_carga_fasor)

                if tipo_sistema == 'Trifásico':
                    V_fuente_LL = tension_linea_V
                    V_carga_LL = V_carga_magnitud_fase * (3**0.5)
                else:
                    V_fuente_LL = tension_linea_V
                    V_carga_LL = V_carga_magnitud_fase

                caida_tension_V_LL = V_fuente_LL - V_carga_LL
                caida_tension_porc = (caida_tension_V_LL / V_fuente_LL) * 100 if V_fuente_LL != 0 else 0

                perdida_potencia_kw = factor_perdida_potencia * (corriente_A**2) * resistencia_total_conductor_fase / 1000

                costo_total_conductor = cable_info_calc['costo_gs_por_metro'] * longitud_metros_input * num_conductores_costo
                costo_anual_perdidas = perdida_potencia_kw * 8760 * 450

                st.session_state.results_cables = {
                    "potencia_kva": potencia_kva, "corriente_A": corriente_A, "caida_tension_porc": caida_tension_porc,
                    "caida_tension_V_LL": caida_tension_V_LL, "perdida_potencia_kw": perdida_potencia_kw,
                    "costo_total_conductor": costo_total_conductor, "costo_anual_perdidas": costo_anual_perdidas,
                    "V_fuente_LL": V_fuente_LL, "V_carga_LL": V_carga_LL, "tipo_sistema": tipo_sistema
                }
            else:
                st.warning("Por favor, seleccione un tipo de conductor.")


# --- COLUMNA DERECHA: MONITOR DE RESULTADOS ---
with col2:
    st.markdown("<h5>📊 Resultados del Análisis</h5>", unsafe_allow_html=True)

    if st.session_state.results_cables:
        res = st.session_state.results_cables

        # Asegurarnos que la información del cable se muestra correctamente si los resultados existen
        # Esto es para el caso en que se haya presionado el botón antes y la página se recargue
        # y el selectbox tenga un valor inicial.
        if datos_cables and tipo_conductor_seleccionado_input not in st.session_state.get('previous_conductor_for_display', ''):
            st.session_state.previous_conductor_for_display = tipo_conductor_seleccionado_input

        tab1, tab2, tab3 = st.tabs(["Resultados Clave", "Análisis Económico", "Detalles y Gráfico"])
        with tab1:
            st.metric("Potencia Aparente Calculada", f"{res['potencia_kva']:.2f} kVA")
            st.metric("Corriente de Línea", f"{res['corriente_A']:.2f} A")
            st.metric("Caída de Tensión", f"{res['caida_tension_porc']:.2f} %", delta=f"{-res['caida_tension_V_LL']:.2f} V ({'L-L' if res['tipo_sistema'] == 'Trifásico' else 'L-N'})", delta_color="inverse")
            if res['caida_tension_porc'] <= 5.0: st.success("✅ Validación: Aceptable (≤ 5%).")
            else: st.error("❌ Validación: Excesiva (> 5%).")

        with tab2:
            st.metric("Costo Total del Conductor (Principal)", f"Gs. {int(res['costo_total_conductor']):,}")
            st.metric("Costo Anual de Energía Perdida", f"Gs. {int(res['costo_anual_perdidas']):,}", help="Estimado con Gs. 450/kWh y operación 24/7.")

        with tab3:
            st.markdown(f"<h6>Visualización de Tensión ({'L-L' if res['tipo_sistema'] == 'Trifásico' else 'L-N'})</h6>", unsafe_allow_html=True)
            chart_data = pd.DataFrame({'Etapa': ['En Fuente', 'En Carga'], f"Tensión ({'L-L' if res['tipo_sistema'] == 'Trifásico' else 'L-N'}) (V)": [res['V_fuente_LL'], res['V_carga_LL']]})
            st.bar_chart(chart_data.set_index('Etapa'))
    else:
        st.info("Configure los parámetros a la izquierda y presione 'Analizar Línea' para ver los resultados.")
