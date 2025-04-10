import pandas as pd
import plotly.express as px #pip install plotly-express
import folium #pip install folium
import streamlit as st #pip install streamlit
from streamlit_folium import st_folium #pip install streamlit-folium
from branca.colormap import linear
import random


# Page configuration (keep this at the top)
st.set_page_config(page_title="SENDA", page_icon="🏥", layout="wide")

# Only show the main title/subtitle if we're not on the prediction page
if "current_page" not in st.session_state or st.session_state.current_page != "prediction":
    st.title("🏥SENDA")
    st.subheader("Estadísticas del Sistema Público de Hospitales en Chile")

# Inicialización del estado de sesión
if 'current_page' not in st.session_state:
    st.session_state.current_page = "mapa"
if 'selected_seremi' not in st.session_state:
    st.session_state.selected_seremi = None
if 'selected_month' not in st.session_state:
    st.session_state.selected_month = None
if 'selected_hospital' not in st.session_state:
    st.session_state.selected_hospital = None
if 'areas_hospital' not in st.session_state:
    st.session_state.areas_hospital = []

@st.cache_data
def load_hospital_data():
    df_hospitales = pd.read_csv('/home/bren/code/camv98/SENDA_Chile/raw_data/lista_hospitales_final.csv')
    return df_hospitales

df_hospitales = load_hospital_data()

# Datos completos de SEREMIs con coordenadas aproximadas
seremi_data = {

    'SEREMI': [
        'Aconcagua', 'Aisén', 'Antofagasta', 'Araucanía Norte', 'Araucanía Sur',
        'Arauco','Arica', 'Atacama', 'Biobío', 'Chiloé', 'Concepción', 'Coquimbo',
        'Del Libertador B.O Higgins', 'Del Maule', 'Del Reloncaví', 'Iquique',
        'Magallanes', 'Metropolitano Central', 'Metropolitano Norte',
        'Metropolitano Occidente', 'Metropolitano Oriente', 'Metropolitano Sur',
        'Metropolitano Sur Oriente', 'Osorno', 'Talcahuano', 'Valdivia',
        'Valparaíso San Antonio', 'Viña del Mar Quillota', 'Ñuble'
    ],
    'Latitud': [
        -32.8, -45.6, -23.6, -38.5, -39.0, -37.3, -18.5,-27.4, -36.8, -42.6, -36.8,
        -30.0, -34.4, -35.4, -41.5, -20.2, -53.2, -33.5, -33.4, -33.5, -33.5,
        -33.6, -33.6, -40.6, -36.7, -39.8, -33.0, -32.9, -36.6
    ],
    'Longitud': [
        -70.7, -72.1, -70.4, -72.6, -72.3, -73.3,-70.3, -70.7, -73.0, -73.9, -73.0,
        -71.3, -71.0, -71.7, -72.9, -69.8, -70.9, -70.7, -70.7, -70.9, -70.6,
        -70.7, -70.6, -73.1, -73.1, -73.2, -71.6, -71.5, -72.1
    ],
    'Region': [
        'Valparaíso', 'Aysén', 'Antofagasta', 'Araucanía', 'Araucanía',
        'Biobío', 'Arica y Parinacota','Atacama', 'Biobío', 'Los Lagos', 'Biobío', 'Coquimbo',
        "O'Higgins", 'Maule', 'Los Lagos', 'Tarapacá', 'Magallanes',
        'Metropolitana', 'Metropolitana', 'Metropolitana', 'Metropolitana',
        'Metropolitana', 'Metropolitana', 'Los Lagos', 'Biobío', 'Los Ríos',
        'Valparaíso', 'Valparaíso', 'Ñuble'
    ]
}

df_seremis = pd.DataFrame(seremi_data)

# Function to generate random bed data for visualization, cambiar por api
def generate_bed_data(area_name, month):
    """Generate sample bed occupancy data for visualization"""
    total_beds = random.randint(20, 50)  # Total de camas para el área
    occupied = random.randint(5, total_beds-5)  # Camas ocupadas
    available = total_beds - occupied  # Camas disponibles

    return {
        'total_beds': total_beds,
        'occupied': occupied,
        'available': available,
        'occupancy_rate': round((occupied/total_beds)*100, 1),
        'availability_rate': round((available/total_beds)*100, 1)
    }

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
            st.session_state.current_page = "hospital_selection"
            st.rerun()

# Función para selección de hospital
def hospital_selection_page():
    # Botón para volver
    if st.button("← Volver al mapa", type="secondary"):
        st.session_state.current_page = "mapa"
        st.rerun()

    st.title(f"SEREMI: {st.session_state.selected_seremi}")
    st.subheader(f"Mes seleccionado: {st.session_state.selected_month}")

    # Filtrar hospitales por SEREMI seleccionada (excluyendo "Datos Servicio Salud")
    hospitales_seremi = df_hospitales[
        df_hospitales['Nombre SS/SEREMI'] == st.session_state.selected_seremi
    ]

    if hospitales_seremi.empty:
        st.warning(f"No se encontraron hospitales para la SEREMI {st.session_state.selected_seremi}")
        return

    # Obtener lista de establecimientos únicos (excluyendo "Datos Servicio Salud")
    establecimientos = [
        est for est in hospitales_seremi['Nombre Establecimiento'].unique()
        if est != "Datos Servicio Salud"
    ]

    # Verificar si solo existe "Datos Servicio Salud" para esta SEREMI
    if len(establecimientos) == 0:
        # Mostrar solo la opción de Datos Generales Seremi
        st.info("Esta SEREMI solo cuenta con datos generales para la zona")

        if st.button("Ver estadísticas generales", type="primary"):
            st.session_state.selected_hospital = "Datos Servicio Salud"
            # Obtener todas las áreas únicas de la SEREMI
            st.session_state.areas_hospital = ["Datos Servicio Salud"]
            st.session_state.current_page = "prediction"
            st.rerun()
    else:
        # Opción para ver datos generales o seleccionar hospital
        option = st.radio(
            "Seleccione una opción:",
            options=["Datos Generales Seremi", "Seleccionar hospital específico"],
            horizontal=True
        )

        if option == "Datos Generales Seremi":
            if st.button("Ver estadísticas generales", type="primary"):
                st.session_state.selected_hospital = "Datos Servicio Salud"
                # Obtener todas las áreas únicas de la SEREMI
                st.session_state.areas_hospital = ["Datos Servicio Salud"]
                st.session_state.current_page = "prediction"
                st.rerun()
        else:
            # Seleccionar hospital (excluyendo "Datos Servicio Salud")
            selected_hospital = st.selectbox(
                "Seleccione un hospital:",
                options=sorted(establecimientos))

            if st.button("Ver estadísticas del hospital", type="primary"):
                st.session_state.selected_hospital = selected_hospital
                st.session_state.areas_hospital = ["Datos Servicio Salud"]
                st.session_state.current_page = "prediction"
                st.rerun()


# Función para la página de predicción por seremi
def prediction_page():

    # Reemplazamos los títulos originales con nuestra versión pequeña
    st.markdown("""
    <style>
        .inline-header {
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 1rem;
        }
        .inline-header h1 {
            font-size: 1.5rem !important;
            margin: 0 !important;
        }
        .inline-header h2 {
            font-size: 1rem !important;
            margin: 0 !important;
            color: gray;
            font-weight: normal;
        }
    </style>
    <div class="inline-header">
        <h1>🏥SENDA</h1>
        <h2>Estadísticas del Sistema Público de Hospitales en Chile</h2>
    </div>
    """, unsafe_allow_html=True)

     # Botón para volver
    if st.button("← Volver a selección de hospital", type="secondary"):
        st.session_state.current_page = "hospital_selection"
        st.rerun()


    if not st.session_state.selected_hospital:
        st.warning("No se ha seleccionado ningún hospital")
        st.session_state.current_page = "hospital_selection"
        st.rerun()
        return

        # Mostrar información principal sin los títulos repetidos
    st.write("")  # Espacio en blanco para separación

    # Encabezado con la información de selección
    col1, col2, col3 = st.columns(3)
    with col1:
        st.subheader(f"**SEREMI:** {st.session_state.selected_seremi}")
    with col2:
        st.subheader(f"**{'Servicio Salud' if st.session_state.selected_hospital == 'Datos Generales Seremi' else 'Hospital'}:** {st.session_state.selected_hospital}")
    with col3:
        st.subheader(f"**Mes:** {st.session_state.selected_month}")

    st.markdown("---")

    if st.session_state.selected_hospital == "Datos Servicio Salud":
        st.subheader("Estadísticas generales del Servicio Salud")
    else:
        st.subheader(f"Estadísticas del hospital {st.session_state.selected_hospital}")

    # Solo mostramos "Datos Servicio Salud" como área única
    area = "Datos Servicio Salud"
    st.markdown(f"### {area}")

    # Obtener datos de camas
    bed_data = generate_bed_data(area, st.session_state.selected_month)

    # Crear columnas para las gráficas
    col1, col2 = st.columns(2)

    with col1:
        # Gráfica circular de ocupación
        fig_occupied = px.pie(
            names=['Ocupadas', 'Disponibles'],
            values=[bed_data['occupied'], bed_data['available']],
            title=f"Ocupación: {bed_data['occupancy_rate']}%",
            color=['Ocupadas', 'Disponibles'],
            color_discrete_map={'Ocupadas':'#EF553B', 'Disponibles':'#00CC96'}
        )
        st.plotly_chart(fig_occupied, use_container_width=True)

    with col2:
        # Gráfica circular de disponibilidad
        fig_available = px.pie(
            names=['Disponibles', 'Ocupadas'],
            values=[bed_data['available'], bed_data['occupied']],
            title=f"Disponibilidad: {bed_data['availability_rate']}%",
            color=['Disponibles', 'Ocupadas'],
            color_discrete_map={'Disponibles':'#00CC96', 'Ocupadas':'#EF553B'}
        )
        st.plotly_chart(fig_available, use_container_width=True)

    # Mostrar métricas
    st.metric(label="Total de camas", value=bed_data['total_beds'])

    col_metric1, col_metric2 = st.columns(2)
    with col_metric1:
        st.metric(label="Camas ocupadas",
                value=f"{bed_data['occupied']} ({bed_data['occupancy_rate']}%)")
    with col_metric2:
        st.metric(label="Camas disponibles",
                value=f"{bed_data['available']} ({bed_data['availability_rate']}%)")

# Main navigation
if st.session_state.current_page == "mapa":
    selection_page()
elif st.session_state.current_page == "hospital_selection":
    hospital_selection_page()
elif st.session_state.current_page == "prediction":
    prediction_page()

# CSS styles
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
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 8px 16px;
        border-radius: 4px 4px 0 0;
    }
</style>
""", unsafe_allow_html=True)
