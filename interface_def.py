import pandas as pd
import plotly.express as px #pip install plotly-express
import folium #pip install folium
import streamlit as st #pip install streamlit
from streamlit_folium import st_folium #pip install streamlit-folium
from branca.colormap import linear
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import random
from datetime import datetime, timedelta
import time
import requests
from urllib.parse import quote



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

#@st.cache_data
#def load_hospital_data():
#    df_hospitales = pd.read_csv('/home/bren/code/camv98/SENDA_Chile/raw_data/lista_hospitales_seremi_versionfinal.csv')
#    return df_hospitales.reset_index(drop=True)

#df_hospitales = load_hospital_data()

#def llamar_api_local(date, seremi, hospital):
#    hospital_codificado = quote(hospital)
#    url = f"http://127.0.0.1:8080/predict?date={date}&SEREMI={seremi}&hospital={hospital_codificado}"
#    try:
#        response = requests.get(url)
#        response.raise_for_status()
#        return response.json(), url  # Devuelve la respuesta y la URL
#    except requests.exceptions.RequestException as e:
#        return {"error": str(e)}, url  # Devuelve el error y la URL

lista_hospitales= ['Hospital de Mejillones',
 'Hospital Provincial del Huasco Monseñor Fernando Ariztía Ruiz (Vallenar)',
 'Hospital San Juan de Dios (La Serena)',
 'Hospital San Pablo (Coquimbo)',
 'Hospital de Salamanca',
 'Hospital San Juan de Dios (Combarbalá)',
 'Hospital San Pedro (Los Vilos)',
 'Hospital Carlos Van Buren (Valparaíso)',
 'Hospital San José (Casablanca)',
 'Hospital de Quilpué',
 'Hospital San Agustín (La Ligua)',
 'Hospital Adriana Cousiño (Quintero)',
 'Hospital Juana Ross de Edwards (Peñablanca, Villa Alemana)',
 'Hospital Centro Geriátrico Paz de la Tarde (Limache)',
 'Hospital San Juan de Dios (Los Andes)',
 'Hospital San Francisco (Llaillay)',
 'Hospital San Antonio (Putaendo)',
 'Complejo Hospitalario San José (Santiago, Independencia)',
 'Hospital San Juan de Dios (Santiago, Santiago)',
 'Hospital Adalberto Steeger (Talagante)',
 'Hospital San José (Melipilla)',
 'Hospital de Curacaví',
 'Instituto Nacional de Enfermedades Respiratorias y Cirugía Torácica',
 'Instituto Nacional de Rehabilitación Infantil Presidente Pedro Aguirre Cerda',
 'Instituto Nacional Geriátrico Presidente Eduardo Frei Montalva',
 'Hospital Hanga Roa (Isla De Pascua)',
 'Hospital Barros Luco Trudeau (Santiago, San Miguel)',
 'Hospital San Luis (Buin)',
 'Hospital Psiquiátrico El Peral (Santiago, Puente Alto)',
 'Hospital El Pino (Santiago, San Bernardo)',
 'Hospital San José de Maipo',
 'Hospital Padre Alberto Hurtado (San Ramón)',
 'Hospital San Vicente de Tagua-Tagua',
 'Hospital de Pichidegua',
 'Hospital de Nancagua',
 'Hospital de Marchigüe',
 'Hospital de Pichilemu',
 'Hospital de Lolol',
 'Hospital de Litueche',
 'Hospital San Juan de Dios (Curicó)',
 'Hospital de Molina',
 'Hospital de Curepto',
 'Hospital de Constitución',
 'Hospital Presidente Carlos Ibáñez del Campo (Linares)',
 'Hospital San José (Parral)',
 'Hospital San Juan de Dios (Cauquenes)',
 'Hospital Clínico Herminda Martín (Chillán)',
 'Hospital Comunitario de Salud Familiar de Bulnes',
 'Hospital Comunitario de Salud Familiar Pedro Morales Campos (Yungay)',
 'Hospital Comunitario de Salud Familiar de Quirihue',
 'Hospital Comunitario de Salud Familiar de El Carmen',
 'Hospital Traumatológico (Concepción)',
 'Hospital San José (Coronel)',
 'Hospital de Lota',
 'Hospital Clorinda Avello (Santa Juana)',
 'Hospital Las Higueras (Talcahuano)',
 'Hospital de Tomé',
 'Hospital de Galvarino',
 'Hospital de Vilcún',
 'Hospital de Carahue',
 'Hospital de Pitrufquén',
 'Hospital de Toltén',
 'Hospital de Gorbea',
 'Hospital de Villarrica',
 'Hospital de Corral',
 'Hospital de Los Lagos',
 'Hospital Juan Morey (La Unión)',
 'Hospital de Río Bueno',
 'Hospital de Río Negro',
 'Hospital de Puerto Octay',
 'Hospital de Puerto Montt',
 'Hospital de Frutillar',
 'Hospital de Fresia',
 'Hospital de Maullín',
 'Hospital de Calbuco',
 'Hospital de Futaleufú',
 'Hospital Lord Cochrane',
 'Hospital de Lebu',
 'Hospital Intercultural Kallvu Llanka (Cañete)',
 'Hospital de Contulmo',
 'Hospital de Purén',
 'Hospital de Collipulli',
 'Hospital de Lonquimay',
 'Hospital de Castro',
 'Hospital de Ancud',
 'Hospital de Quellón']

lista_seremis=['Antofagasta',
 'Atacama',
 'Coquimbo',
 'Coquimbo',
 'Coquimbo',
 'Coquimbo',
 'Coquimbo',
 'Valparaíso San Antonio',
 'Valparaíso San Antonio',
 'Viña del Mar Quillota',
 'Viña del Mar Quillota',
 'Viña del Mar Quillota',
 'Viña del Mar Quillota',
 'Viña del Mar Quillota',
 'Aconcagua',
 'Aconcagua',
 'Aconcagua',
 'Metropolitano Norte',
 'Metropolitano Occidente',
 'Metropolitano Occidente',
 'Metropolitano Occidente',
 'Metropolitano Occidente',
 'Metropolitano Oriente',
 'Metropolitano Oriente',
 'Metropolitano Oriente',
 'Metropolitano Oriente',
 'Metropolitano Sur',
 'Metropolitano Sur',
 'Metropolitano Sur',
 'Metropolitano Sur',
 'Metropolitano Sur Oriente',
 'Metropolitano Sur Oriente',
 'Del Libertador B.O Higgins',
 'Del Libertador B.O Higgins',
 'Del Libertador B.O Higgins',
 'Del Libertador B.O Higgins',
 'Del Libertador B.O Higgins',
 'Del Libertador B.O Higgins',
 'Del Libertador B.O Higgins',
 'Del Maule',
 'Del Maule',
 'Del Maule',
 'Del Maule',
 'Del Maule',
 'Del Maule',
 'Del Maule',
 'Ñuble',
 'Ñuble',
 'Ñuble',
 'Ñuble',
 'Ñuble',
 'Concepción',
 'Concepción',
 'Concepción',
 'Concepción',
 'Talcahuano',
 'Talcahuano',
 'Araucanía Sur',
 'Araucanía Sur',
 'Araucanía Sur',
 'Araucanía Sur',
 'Araucanía Sur',
 'Araucanía Sur',
 'Araucanía Sur',
 'Valdivia',
 'Valdivia',
 'Valdivia',
 'Valdivia',
 'Osorno',
 'Osorno',
 'Del Reloncaví',
 'Del Reloncaví',
 'Del Reloncaví',
 'Del Reloncaví',
 'Del Reloncaví',
 'Del Reloncaví',
 'Aisén',
 'Arauco',
 'Arauco',
 'Arauco',
 'Araucanía Norte',
 'Araucanía Norte',
 'Araucanía Norte',
 'Chiloé',
 'Chiloé',
 'Chiloé']

@st.cache_data
def load_hospital_data():
    return pd.DataFrame({
        'Nombre Establecimiento': lista_hospitales,
        'Nombre SS/SEREMI': lista_seremis
    })

df_hospitales_seremis = load_hospital_data()

def llamar_api_nube(date, seremi, hospital):
    hospital_codificado = quote(hospital)
    url = f"https://sendaapp-933848607376.southamerica-west1.run.app/predict?date={date}&SEREMI={seremi}&hospital={hospital_codificado}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json(), url  # Devuelve la respuesta y la URL
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}, url  # Devuelve el error y la URL


def hacer_prediccion(seremi, hospital, mes_seleccionado):
    """
    Obtiene datos de predicción desde la API

    Args:
        seremi (str): Nombre de la SEREMI seleccionada
        hospital (str): Nombre del hospital seleccionado
        mes_seleccionado (str): Mes en formato "Mes Año" (ej. "Septiembre 2025")

    Returns:
        list: Lista con 4 elementos:
            0. Diccionario con últimos 12 meses + predicción
            1. Diccionario con mismo mes en 5 años diferentes
            2. Tupla con (temp_min, temp_max)
            3. Porcentaje de confiabilidad (float)
            4. Mensaje de predicción (str)
            5. URL de la API (str)
    """
    # Diccionario de meses en español
    meses_espanol = {
        1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
        5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
        9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
    }
    # Parsear el mes seleccionado
    mes = mes_seleccionado
    año_actual = 2025

    # Encontrar el número del mes
    mes_numero = next((num for num, nombre in meses_espanol.items() if nombre.lower() == mes.lower()), 1)

    # Llamar a la API
    fecha_str = datetime(año_actual, mes_numero, 1).strftime("%Y-%m-%d")
    api_response, api_url = llamar_api_nube(fecha_str, seremi, hospital)

    # Procesar respuesta de la API
    if not isinstance(api_response, list) or len(api_response) < 4:
        error_msg = f"Respuesta inesperada de la API: {api_response}"
        return [
            {},  # historico_12_meses
            {},  # mismo_mes_5_años
            (0, 0),  # temp_min, temp_max
            0,  # confiabilidad
            f"Error: {error_msg}",
            api_url
        ]

    # 1. Procesar histórico de 12 meses + predicción
    historico_12_meses = {}
    if api_response[0]:
        for fecha_str, valor in api_response[0].items():
            fecha = datetime.strptime(fecha_str, "%Y-%m-%d")
            nombre_mes = f"{meses_espanol[fecha.month]} {fecha.year}"
            historico_12_meses[nombre_mes] = round(valor)  # Redondeamos a entero

    # 2. Procesar temperaturas
    temp_data = api_response[1] if len(api_response) > 1 else {}
    temp_min = int(round(temp_data.get("temp_min", 0)))  # Convertir directamente a entero
    temp_max = int(round(temp_data.get("temp_max", 0)))  # Convertir directamente a entero

    # 3. Procesar comparación anual
    mismo_mes_5_años = {}
    if len(api_response) > 2 and api_response[2]:
        for fecha_str, valor in api_response[2].items():
            fecha = datetime.strptime(fecha_str, "%Y-%m-%d")
            nombre_mes = f"{meses_espanol[fecha.month]} {fecha.year}"
            mismo_mes_5_años[nombre_mes] = round(valor)  # Redondeamos a entero

    # 4. Procesar confiabilidad
    confiabilidad_data = api_response[3] if len(api_response) > 3 else {}
    confiabilidad = round(confiabilidad_data.get("confiable", 0) * 100, 1)

    # Crear mensaje de predicción
    prediccion = round(list(historico_12_meses.values())[-1]) if historico_12_meses else 0
    mensaje_prediccion = f"Para el mes de {mes_seleccionado}, se predice que:\n{prediccion}\nserá el número de camas disponibles"

    return [
        historico_12_meses,
        mismo_mes_5_años,
        (temp_min, temp_max),
        confiabilidad,
        mensaje_prediccion,
        api_url
    ]


# Datos completos de SEREMIs con coordenadas aproximadas
seremi_data = {
    'SEREMI': [
        'Aconcagua', 'Aisén', 'Antofagasta', 'Araucanía Norte', 'Araucanía Sur',
        'Arauco', 'Atacama', 'Chiloé', 'Concepción', 'Coquimbo',
        'Del Libertador B.O Higgins', 'Del Maule', 'Del Reloncaví',
        'Metropolitano Norte', 'Metropolitano Occidente', 'Metropolitano Oriente',
        'Metropolitano Sur', 'Metropolitano Sur Oriente', 'Osorno', 'Talcahuano',
        'Valdivia', 'Valparaíso San Antonio', 'Viña del Mar Quillota', 'Ñuble'
    ],
    'Latitud': [
        -32.8, -45.6, -23.6, -38.5, -39.0, -37.3, -27.4, -42.6, -36.8, -30.0,
        -34.4, -35.4, -41.5, -33.4, -33.5, -33.5, -33.6, -33.6, -40.6, -36.7,
        -39.8, -33.0, -32.9, -36.6
    ],
    'Longitud': [
        -70.7, -72.1, -70.4, -72.6, -72.3, -73.3, -70.7, -73.9, -73.0, -71.3,
        -71.0, -71.7, -72.9, -70.7, -70.9, -70.6, -70.7, -70.6, -73.1, -73.1,
        -73.2, -71.6, -71.5, -72.1
    ],
    'Region': [
        'Valparaíso', 'Aysén', 'Antofagasta', 'Araucanía', 'Araucanía',
        'Biobío', 'Atacama', 'Los Lagos', 'Biobío', 'Coquimbo',
        "O'Higgins", 'Maule', 'Los Lagos', 'Metropolitana', 'Metropolitana',
        'Metropolitana', 'Metropolitana', 'Metropolitana', 'Los Lagos', 'Biobío',
        'Los Ríos', 'Valparaíso', 'Valparaíso', 'Ñuble'
    ]
}


df_seremis = pd.DataFrame(seremi_data)


# Función para la página de selección
def selection_page():
    # Aplicar CSS para reducir el margen del subheader
    st.markdown("""
        <style>
            .stSubheader {
                padding-top: 0.5rem !important;
                margin-bottom: 0.5rem !important;
            }
        </style>
    """, unsafe_allow_html=True)

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
    map_data = st_folium(m, use_container_width=True, height=400)

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
        months = ["Mayo", "Junio",
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
    global df_hospitales_seremis
    # Botón para volver
    if st.button("← Volver al mapa", type="secondary"):
        st.session_state.current_page = "mapa"
        st.rerun()

    st.title(f"SEREMI: {st.session_state.selected_seremi}")
    st.subheader(f"Mes seleccionado: {st.session_state.selected_month}")

    # Filtrar hospitales por SEREMI seleccionada (excluyendo "Datos Servicio Salud")
    hospitales_seremi = df_hospitales_seremis[
        df_hospitales_seremis['Nombre SS/SEREMI'] == st.session_state.selected_seremi
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

    if st.session_state.selected_hospital == "Datos Servicio Salud":
        st.subheader("Estadísticas generales del Servicio Salud")
    else:
        st.markdown(f"""
        <div style="
            background-color: #f8f9fa;
            padding: 1rem;
            border-radius: 12px;
            border: 1px solid #e0e0e0;
            margin-bottom: 1.5rem;
        ">
            <div>
                <h2 style="color: #666; margin: 0 0 0.2rem 0; font-size: 1rem; font-weight: 500;">ESTADÍSTICAS HOSPITALARIAS</h2>
                <h1 style="color: #222; margin: 0; font-size: 1.5rem; font-weight: 700;">{st.session_state.selected_hospital}</h1>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Solo mostramos "Datos Servicio Salud" como área única
    area = "Datos Servicio Salud"
    #st.markdown(f"### {area}")

    ######################################################################3
    #             Aquí va la parte de la predicción                      #
    #######################################################################

    camas_predichas = hacer_prediccion(st.session_state.selected_seremi, st.session_state.selected_hospital, st.session_state.selected_month)

    if camas_predichas is None:
        st.warning("No se pudo obtener la predicción")
        return

    # Extraer los componentes de la predicción
    historico_12_meses = camas_predichas[0]
    mismo_mes_5_años = camas_predichas[1]
    temp_min, temp_max = camas_predichas[2]
    confiabilidad = camas_predichas[3]
    mensaje_prediccion = camas_predichas[4]
    api_url = camas_predichas[5]

    # Crear dos columnas (60% | 40%)
    col_pred, col_conf = st.columns([3, 2])

    with col_pred:
        # Tarjeta de predicción (texto modificado)
        mensaje_lineas = mensaje_prediccion.splitlines()

        if len(mensaje_lineas) >= 3:
            st.markdown(f"""
            <div style="text-align: center; margin: 10px 0; padding: 15px; border-radius: 10px; background-color: rgba(248, 249, 250, 0.5);">
                <h2 style="font-size: 1.8rem;">{mensaje_lineas[0]}</h2>
                <h1 style="font-size: 4rem; color: #00CC96; margin: 20px 0;">{mensaje_lineas[1]}</h1>
                <h2 style="font-size: 1.8rem;">{mensaje_lineas[2]}</h2>
                #<p style="font-size: 0.8rem; margin-top: 10px;">URL de la API: {api_url}</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style="text-align: center; margin: 10px 0; padding: 15px; border-radius: 10px; background-color: rgba(248, 249, 250, 0.5);">
                <h2 style="font-size: 1.8rem;">{mensaje_lineas[0]}</h2>
                <p style="font-size: 0.8rem; margin-top: 10px;">URL de la API: {api_url}</p>
            </div>
            """, unsafe_allow_html=True)

    with col_conf:
        # Determinar categoría de confiabilidad
        if confiabilidad < 65:
            categoria = "Baja"
            color_texto = "#ff4b4b"  # Rojo
        elif 50 <= confiabilidad < 80:
            categoria = "Media"
            color_texto = "#f9cb28"  # Amarillo
        else:
            categoria = "Alta"
            color_texto = "#00cc96"  # Verde

        # Medidor de confiabilidad con categoría explícita
        st.markdown(f"""
        <div style="margin: 25px 0; padding: 15px; border-radius: 10px; background-color: rgba(248, 249, 250, 0.5);">
            <h3 style="font-size: 1.5rem; text-align: center; margin-bottom: 15px;">Confiabilidad de la predicción</h3>
            <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                <span style="font-size: 0.9rem;">Baja</span>
                <span style="font-size: 0.9rem;">Media</span>
                <span style="font-size: 0.9rem;">Alta</span>
            </div>
            <div style="height: 20px; background: linear-gradient(90deg, #ff4b4b 0%, #f9cb28 50%, #00cc96 100%); border-radius: 10px; position: relative;">
                <div style="position: absolute; left: 50%; top: 50%; transform: translate(-50%, -50%); color: white; font-weight: bold; text-shadow: 1px 1px 2px rgba(0,0,0,0.5);">{confiabilidad}%</div>
            </div>
            <div style="height: 20px; width: {confiabilidad}%; background-color: rgba(0,204,150,0.3); margin-top: -20px; border-radius: 10px;"></div>
            <p style="text-align: center; margin-top: 10px; font-weight: bold; color: {color_texto}">
                Categoría: {categoria}
            </p>
        </div>
        """, unsafe_allow_html=True)

        # Información de selección
        st.markdown(f"""
        <div style="margin-top: 20px; padding: 15px; border-radius: 10px; background-color: rgba(248, 249, 250, 0.5);">
            <p style="font-size: 1rem; margin: 5px 0;"><strong>SEREMI:</strong> {st.session_state.selected_seremi}</p>
            <p style="font-size: 1rem; margin: 5px 0;"><strong>{"Servicio Salud" if st.session_state.selected_hospital == "Datos Generales Seremi" else "Hospital"}:</strong> {st.session_state.selected_hospital}</p>
            <p style="font-size: 1rem; margin: 5px 0;"><strong>Mes:</strong> {st.session_state.selected_month}</p>
        </div>
        """, unsafe_allow_html=True)

    # Gráfico 1: Tendencia últimos 12 meses + predicción
    st.markdown("### Tendencia de camas disponibles (últimos 12 meses + predicción)")
    fig1 = px.line(
        x=list(historico_12_meses.keys()),
        y=list(historico_12_meses.values()),
        labels={'x': 'Mes', 'y': 'Camas disponibles'},
        markers=True,
        line_shape='linear',
        color_discrete_sequence=['#1f77b4']  # Azul
    )

    # Destacar predicción en gráfico 1
    fig1.add_scatter(
        x=[list(historico_12_meses.keys())[-1]],
        y=[list(historico_12_meses.values())[-1]],
        mode='markers',
        marker=dict(size=20, color='red'),  # Cambié de size=12 a size=20
        name='Predicción'
    )

    # Personalización Gráfico 1
    fig1.update_traces(
        line=dict(width=3),
        marker=dict(size=8),
        hovertemplate="<b>%{x}</b><br>Camas: %{y}"
    )

    # Aplicar layout y mostrar primer gráfico
    fig1.update_layout(
        hovermode="x unified",
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(showgrid=True),
        yaxis=dict(showgrid=True),
        showlegend=False,
        margin=dict(l=20, r=20, t=40, b=20),
        xaxis_title="Mes",
        yaxis_title="Camas disponibles"
    )

    st.plotly_chart(fig1, use_container_width=True)

    st.markdown("---")

    # Gráfico 2: Comparación anual + predicción
    st.markdown(f"### Tendencia de camas disponibles de los últimos años para {st.session_state.selected_month.split()[0]}")

    mismo_mes_ordenado = dict(sorted(mismo_mes_5_años.items(), key=lambda x: int(x[0].split()[1])))

    fig2 = px.line(
        x=list(mismo_mes_ordenado.keys()),
        y=list(mismo_mes_ordenado.values()),
        labels={'x': 'Año', 'y': 'Camas disponibles'},
        markers=True,
        line_shape='linear',
        color_discrete_sequence=['#ff7f0e']  # Naranja
    )

    # Destacar predicción (punto más grande)
    fig2.add_scatter(
        x=[list(mismo_mes_ordenado.keys())[-1]],  # Último elemento (más reciente)
        y=[list(mismo_mes_ordenado.values())[-1]],
        mode='markers',
        marker=dict(size=24, color='red', symbol='star'),
        name='Predicción'
    )

    # Personalización Gráfico 2
    fig2.update_traces(
        line=dict(width=3, dash='dot'),  # Línea punteada
        marker=dict(size=10, symbol='diamond'),  # Marcadores diferentes
        hovertemplate="<b>%{x}</b><br>Camas: %{y}"
    )

    # Aplicar layout y mostrar segundo gráfico
    fig2.update_layout(
        hovermode="x unified",
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(showgrid=True),
        yaxis=dict(showgrid=True),
        showlegend=False,
        margin=dict(l=20, r=20, t=40, b=20),
        xaxis_title="Año",
        yaxis_title="Camas disponibles"
    )

    st.plotly_chart(fig2, use_container_width=True)

    # Gráfico 3: Temperaturas para el mes predicho con animación controlada por botón
    st.markdown("### Condiciones meteorológicas esperadas")

    # Crear columnas para los gráficos (se llenarán después del botón)
    col1, col2 = st.columns(2)

    # Contenedores vacíos para los gráficos
    temp_min_placeholder = col1.empty()
    temp_max_placeholder = col2.empty()

    # Botón para iniciar la animación
    if st.button("▶️ Mostrar temperatura del mes", type="primary"):

        # Mostrar spinner mientras se carga la animación
        with st.spinner("Generando animación..."):

            # Gráfico de temperatura mínima
            fig_temp_min = go.Figure(go.Indicator(
                mode="gauge+number",
                value=0,
                title={'text': "Temperatura Mínima (°C)"},
                gauge={
                    'axis': {'range': [None, 30]},
                    'bar': {'color': "lightskyblue"},
                    'steps': [
                        {'range': [0, 10], 'color': "blue"},
                        {'range': [10, 20], 'color': "deepskyblue"},
                        {'range': [20, 30], 'color': "orange"}]
                }
            ))

            # Gráfico de temperatura máxima
            fig_temp_max = go.Figure(go.Indicator(
                mode="gauge+number",
                value=0,
                title={'text': "Temperatura Máxima (°C)"},
                gauge={
                    'axis': {'range': [None, 40]},
                    'bar': {'color': "orange"},
                    'steps': [
                        {'range': [0, 15], 'color': "wheat"},
                        {'range': [15, 30], 'color': "yellow"},
                        {'range': [30, 40], 'color': "red"}]
                }
            ))

            # Animación lenta para temperatura mínima (0.3 segundos entre pasos)
            for i in range(0, temp_min + 1):
                fig_temp_min.update_traces(value=i)
                temp_min_placeholder.plotly_chart(fig_temp_min, use_container_width=True, key=f"temp_min_{i}")
                time.sleep(0.2)

            # Animación lenta para temperatura máxima (0.3 segundos entre pasos)
            for i in range(0, temp_max + 1):
                fig_temp_max.update_traces(value=i)
                temp_max_placeholder.plotly_chart(fig_temp_max, use_container_width=True, key=f"temp_max_{i}")
                time.sleep(0.2)


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
