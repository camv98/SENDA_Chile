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

# Inicializar variables de sesión
if 'selected_seremi' not in st.session_state:
    st.session_state.selected_seremi = None
if 'selected_month' not in st.session_state:
    st.session_state.selected_month = None
if 'current_page' not in st.session_state:
    st.session_state.current_page = "mapa"

# Crear mapa con estilo Google Maps
m = folium.Map(
    location=[-38.0, -72.5],
    zoom_start=5,
    tiles='https://mt1.google.com/vt/lyrs=y,h&x={x}&y={y}&z={z}',  # Capa híbrida
    attr='Google Hybrid',
    control_scale=True,
    width='100%',
    height=600
)

# Añadir marcadores en blanco y negro
for idx, row in df_seremis.iterrows():
    folium.Marker(
        location=[row['Latitud'], row['Longitud']],
        popup=f"<b>{row['SEREMI']}</b>",
        tooltip="Clic para detalles",
        icon=folium.Icon(
            color='white',
            icon_color='red',
            icon='hospital',
            prefix='fa',
            shadow=True
        )
    ).add_to(m)

# Añadir capa de relieve
folium.TileLayer(
    tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}',
    attr='Google Satellite',
    name='Relieve',
    overlay=False,
    control=True
).add_to(m)

# Control de capas
folium.LayerControl().add_to(m)

# Mostrar mapa
st_folium(m, use_container_width=True, height=600)

# Selectores en sidebar
with st.sidebar:
    st.header("🎚️ Controles")

    # Selector de SEREMI
    selected_seremi = st.selectbox(
        "Selecciona una SEREMI:",
        options=sorted(df_seremis['SEREMI']),
        index=16
    )

# Estilo CSS personalizado
st.markdown("""
<style>
    .st-emotion-cache-1v0mbdj img {
        border-radius: 10px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    .sidebar .sidebar-content {
        background-color: #f8f9fa;
    }
</style>
""", unsafe_allow_html=True)
