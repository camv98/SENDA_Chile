import pandas as pd
import plotly.express as px #pip install plotly-express
import folium #pip install folium
import streamlit as st #pip install streamlit
from streamlit_folium import st_folium #pip install streamlit-folium
from branca.colormap import linear
import random


st.set_page_config(page_title="SENDA",
                   page_icon="🏥",
                   layout="wide")
st.title("🏥SENDA")
st.subheader("Estadísticas del Sistema Público de Hospitales en Chile")

# Datos completos de SEREMIs con coordenadas aproximadas
seremi_data = {
    'SEREMI': [
        'Aconcagua', 'Aisén', 'Antofagasta', 'Araucanía Norte', 'Araucanía Sur',
        'Arauco', 'Atacama', 'Biobío', 'Chiloé', 'Concepción', 'Coquimbo',
        'Del Libertador B.O Higgins', 'Del Maule', 'Del Reloncaví', 'Iquique',
        'Magallanes', 'Metropolitano Central', 'Metropolitano Norte',
        'Metropolitano Occidente', 'Metropolitano Oriente', 'Metropolitano Sur',
        'Metropolitano Sur Oriente', 'Osorno', 'Talcahuano', 'Valdivia',
        'Valparaíso San Antonio', 'Viña del Mar Quillota', 'Ñuble'
    ],
    'Latitud': [
        -32.8, -45.6, -23.6, -38.5, -39.0, -37.3, -27.4, -36.8, -42.6, -36.8,
        -30.0, -34.4, -35.4, -41.5, -20.2, -53.2, -33.5, -33.4, -33.5, -33.5,
        -33.6, -33.6, -40.6, -36.7, -39.8, -33.0, -32.9, -36.6
    ],
    'Longitud': [
        -70.7, -72.1, -70.4, -72.6, -72.3, -73.3, -70.7, -73.0, -73.9, -73.0,
        -71.3, -71.0, -71.7, -72.9, -69.8, -70.9, -70.7, -70.7, -70.9, -70.6,
        -70.7, -70.6, -73.1, -73.1, -73.2, -71.6, -71.5, -72.1
    ],
    'Region': [
        'Valparaíso', 'Aysén', 'Antofagasta', 'Araucanía', 'Araucanía',
        'Biobío', 'Atacama', 'Biobío', 'Los Lagos', 'Biobío', 'Coquimbo',
        "O'Higgins", 'Maule', 'Los Lagos', 'Tarapacá', 'Magallanes',
        'Metropolitana', 'Metropolitana', 'Metropolitana', 'Metropolitana',
        'Metropolitana', 'Metropolitana', 'Los Lagos', 'Biobío', 'Los Ríos',
        'Valparaíso', 'Valparaíso', 'Ñuble'
    ]
}

df_seremis = pd.DataFrame(seremi_data)

# Función para la página de selección
def selection_page():
    st.subheader("Seleccione una SEREMI y mes para la predicción")

    # Crear mapa
    m = folium.Map(
        location=[-38.0, -72.5],
        zoom_start=5,
        tiles='https://mt1.google.com/vt/lyrs=y,h&x={x}&y={y}&z={z}',
        attr='Google Hybrid',
        control_scale=True
    )

    # Añadir marcadores
    for idx, row in df_seremis.iterrows():
        folium.Marker(
            location=[row['Latitud'], row['Longitud']],
            popup=f"<b>{row['SEREMI']}</b>",
            tooltip="Clic para seleccionar",
            icon=folium.Icon(color='white', icon_color='red', icon='hospital', prefix='fa')
        ).add_to(m)

    # Mostrar mapa y capturar interacción
    map_data = st_folium(m, use_container_width=True, height=500)

    # Obtener SEREMI seleccionada del mapa (si se hizo clic)
    selected_seremi = None
    if map_data.get('last_object_clicked_popup'):
        selected_seremi = map_data['last_object_clicked_popup']

    # Selector de SEREMI en sidebar (alternativo)
    with st.sidebar:

        # Selector de SEREMI (con valor por defecto del mapa o primera opción)
        selected_seremi_sidebar = st.selectbox(
            "Seleccione una SEREMI:",
            options=sorted(df_seremis['SEREMI']),
            index=16 if not selected_seremi else list(sorted(df_seremis['SEREMI'])).index(selected_seremi))

        # Usar la selección del mapa si existe, de lo contrario usar sidebar
        selected_seremi = selected_seremi if selected_seremi else selected_seremi_sidebar

        # Selector de mes
        months = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
                 "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
        selected_month = st.selectbox("Seleccione un mes:", options=months)

        # Botón para continuar
        if st.button("Obtener Predicción", type="primary"):
            st.session_state.selected_seremi = selected_seremi
            st.session_state.selected_month = selected_month
            st.session_state.current_page = "prediction"
            st.rerun()

# Función para la página de predicción
def prediction_page():
    # Botón para volver
    if st.button("← Volver al mapa", type="secondary"):
        st.session_state.current_page = "mapa"
        st.rerun()

    st.title(f"{st.session_state.selected_seremi}")
    st.subheader(f"Mes seleccionado: {st.session_state.selected_month}")


    # Mostrar información de la SEREMI seleccionada
    seremi_info = df_seremis[df_seremis['SEREMI'] == st.session_state.selected_seremi].iloc[0]

    col1, col2 = st.columns(2)

    with col1:

        # Mapa pequeño de la ubicación
        m = folium.Map(
            location=[seremi_info['Latitud'], seremi_info['Longitud']],
            zoom_start=12,
            tiles='https://mt1.google.com/vt/lyrs=y,h&x={x}&y={y}&z={z}',
            attr='Google Hybrid',
            width='100%',
            height=200
        )
        folium.Marker(
            location=[seremi_info['Latitud'], seremi_info['Longitud']],
            popup=f"<b>{seremi_info['SEREMI']}</b>",
            icon=folium.Icon(color='red', icon='hospital', prefix='fa')
        ).add_to(m)
        st_folium(m, use_container_width=True, height=300)

    with col2:
        # Aquí iría la llamada a tu API para obtener la predicción
        st.info("Conectando con la API de predicción...")

        # Simulación de llamada a API (reemplazar con tu código real)
        try:
            # Ejemplo de llamada a API (ajusta según tu implementación)
            # response = requests.get(f"TU_API_URL?seremi={st.session_state.selected_seremi}&month={st.session_state.selected_month}")
            # prediction_data = response.json()

            # Datos simulados para el ejemplo
            prediction_data = {
                "prediction": random.uniform(50, 95),
                "confidence": random.uniform(0.7, 0.95),
                "factors": ["Tasa de ocupación", "Estacionalidad", "Indicadores económicos"]
            }

            st.success("Predicción obtenida exitosamente!")

            # Mostrar resultados
            st.metric(
                label="**Tasa de ocupación predicha**",
                value=f"{prediction_data['prediction']:.1f}%",
                delta=f"Confianza: {prediction_data['confidence']*100:.1f}%"
            )

            st.write("**Factores considerados:**")
            for factor in prediction_data["factors"]:
                st.write(f"- {factor}")

        except Exception as e:
            st.error(f"Error al obtener predicción: {str(e)}")


# Navegación entre páginas
if "current_page" not in st.session_state:
    st.session_state.current_page = "mapa"

if st.session_state.current_page == "mapa":
    selection_page()
elif st.session_state.current_page == "prediction":
    prediction_page()

# Estilos CSS
st.markdown("""
<style>
    .st-emotion-cache-1v0mbdj img {
        border-radius: 10px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    .sidebar .sidebar-content {
        background-color: #f8f9fa;
    }
    [data-testid="stMetric"] {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 10px;
    }
    [data-testid="stMetricLabel"] {
        font-size: 1.1rem !important;
    }
    [data-testid="stMetricValue"] {
        font-size: 2.5rem !important;
    }
</style>
""", unsafe_allow_html=True)
