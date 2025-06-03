import streamlit as st
from PIL import Image
from datetime import datetime
import pytz # Librería para manejar zonas horarias

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(
    page_title="Calculadora Eléctrica Pro",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- INYECCIÓN DE CSS PERSONALIZADO ---
st.markdown("""
<style>
    /* Importar fuente desde Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600&display=swap');

    /* Fuente principal para toda la app */
    html, body, [class*="st-"], [class*="css-"] {
        font-family: 'Poppins', sans-serif;
    }

    /* Colores del tema oscuro */
    [data-testid="stAppViewContainer"] {
        background-color: #0d1117;
        color: #c9d1d9;
    }
    
    /* Color de la barra lateral */
    [data-testid="stSidebar"] {
        background-color: #161b22;
        border-right: 1px solid #30363d;
    }

    /* Estilo de los títulos */
    h1, h2, h3 {
        color: #58a6ff; /* Azul de acento */
        font-weight: 600;
    }

    /* Estilo para las tarjetas (cards) */
    .card {
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 4px 8px 0 rgba(0,0,0,0.2);
        transition: 0.3s;
    }
    .card:hover {
        box-shadow: 0 8px 16px 0 rgba(0,0,0,0.2);
        border-color: #58a6ff;
    }

    /* Estilo para los botones */
    .stButton > button {
        border-color: #58a6ff;
        color: #58a6ff;
        border-radius: 8px;
    }
    .stButton > button:hover {
        border-color: #c9d1d9;
        color: #c9d1d9;
        background-color: #58a6ff;
    }
    
</style>
""", unsafe_allow_html=True)


# --- LÓGICA PARA OBTENER HORA DE PARAGUAY ---
# Esto solo se ejecuta una vez por sesión del usuario
if 'current_time' not in st.session_state:
    py_tz = pytz.timezone('America/Asuncion')
    st.session_state.current_time = datetime.now(py_tz)


# --- BARRA LATERAL (SIDEBAR) ---
with st.sidebar:
    st.title("🔌 Calculadora Eléctrica Pro")
    
    try:
        logo = Image.open("/home/anu/Downloads/robot_mejorado_hd.png")
        st.image(logo)
    except FileNotFoundError:
        st.write("*(Tu Logo Aquí)*")
    
    st.markdown("---")
    st.markdown("Navega a la sección que necesites:")
    st.page_link("pages/1_Potencia_Cables_TM.py", label="Potencia y Cables", icon="📏")
    st.page_link("pages/2_Transformadores.py", label="Transformadores", icon="💡")
    
    st.markdown("---")
    st.info("© 2025 - Creado por Anu. Todos los derechos reservados.")


# --- PÁGINA PRINCIPAL ---
st.title("Bienvenido al Dashboard de Cálculo Eléctrico")
st.caption(f"Fecha y Hora Actual en Paraguay: {st.session_state.current_time.strftime('%d/%m/%Y, %H:%M:%S')}")

st.markdown("---")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    <div class="card">
        <h3>📏 Potencia y Cables MT</h3>
        <p>
        Esta sección está diseñada para realizar cálculos de caída de tensión,
        selección de conductores y otras verificaciones esenciales para líneas de Media Tensión.
        </p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="card">
        <h3>💡 Transformadores</h3>
        <p>
        Calcula la capacidad necesaria de un transformador, estima los costos asociados
        a su instalación y verifica los requisitos según las normativas de la ANDE.
        </p>
    </div>
    """, unsafe_allow_html=True)

st.success("Selecciona una herramienta del menú de la izquierda para comenzar.")
