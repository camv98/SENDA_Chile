import pandas as pd
import plotly.express as px #pip install plotly-express
import folium #pip install folium
import streamlit as st #pip install streamlit
from streamlit_folium import st_folium #pip install streamlit-folium
from branca.colormap import linear
import os
from xgboost import XGBRegressor
import numpy as np
from sklearn.base import BaseEstimator, TransformerMixin
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

@st.cache_data
def load_hospital_data():
    df_hospitales = pd.read_csv('/home/elias/code/camv98/SENDA_Chile/stream/lista_hospitales_final.csv')
    return df_hospitales

df_hospitales = load_hospital_data()

def llamar_api_local(date, seremi, hospital):
    hospital_codificado = quote(hospital)
    url = f"http://127.0.0.1:8080/predict?date={date}&SEREMI={seremi}&hospital={hospital_codificado}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json(), url  # Devuelve la respuesta y la URL
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}, url  # Devuelve el error y la URL


def hacer_prediccion(seremi, hospital, mes_seleccionado):
    """
    Genera datos de predicción aleatorios pero realistas para propósitos de prueba

    Args:
        seremi (str): Nombre de la SEREMI seleccionada
        hospital (str): Nombre del hospital seleccionado
        mes_seleccionado (str): Mes en formato "Mes Año" (ej. "Marzo 2024")

    Returns:
        list: Lista con 4 elementos:
            0. Diccionario con últimos 12 meses + predicción
            1. Diccionario con mismo mes en 5 años diferentes
            2. Tupla con (temp_min, temp_max)
            3. Porcentaje de confiabilidad (float)
    """
    # Diccionario de meses en español
    meses_espanol = {
        1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
        5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
        9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
    }
    # Parsear el mes seleccionado
    mes = mes_seleccionado
    año_actual = 2024

    # Encontrar el número del mes
    mes_numero = next((num for num, nombre in meses_espanol.items() if nombre.lower() == mes.lower()), 1)

    # 1. Generar datos para últimos 12 meses + mes predicho
    meses = []
    valores = []
    fecha_actual = datetime(año_actual, mes_numero, 1)

    for i in range(12, -1, -1):
        fecha = fecha_actual - timedelta(days=30*i)
        nombre_mes = f"{meses_espanol[fecha.month]} {fecha.year}"
        meses.append(nombre_mes)

        # Generar valores con tendencia y estacionalidad
        base = random.randint(50, 150)
        estacionalidad = 10 * np.sin(i * np.pi / 6)  # Patrón estacional
        ruido = random.randint(-5, 5)
        valor = base + estacionalidad + ruido
        valores.append(max(10, int(valor)))  # Asegurar mínimo 10 camas

    year = 2025
    first_day = datetime(year, mes_numero, 1)
    fecha_str = first_day.strftime("%Y-%m-%d")
    api_response, api_url = llamar_api_local(fecha_str, seremi, hospital)

    if "prediction" in api_response:
        prediccion = api_response["prediction"]
        valores[-1] = prediccion
        mensaje_prediccion = f"Para el mes de {mes_seleccionado}, se predice que:\n{prediccion}\nserá el número de camas disponibles"
    else:
        valores[-1] = 0
        mensaje_prediccion = f"Error en la predicción: {api_response.get('error', 'Error desconocido')}"

    historico_12_meses = dict(zip(meses, valores))


    # 2. Generar datos para el mismo mes en 5 años anteriores
    mismos_meses = {}
    for i in range(5):
        año_comparar = año_actual - i
        valor = random.randint(50, 150)
        # Añadir tendencia decreciente leve
        valor = max(30, valor - i*5)
        mismos_meses[f"{mes} {año_comparar}"] = valor

    # Incluir la predicción actual en el diccionario
    mismos_meses[f"{mes} {año_actual}"] = valores[-1]

    # 3. Generar temperaturas (dependiendo del mes)
    meses_calidos = ["diciembre", "enero", "febrero", "marzo"]
    meses_frios = ["junio", "julio", "agosto"]

    if nombre_mes.lower() in meses_calidos:
        temp_min = random.randint(12, 18)
        temp_max = random.randint(28, 35)
    elif nombre_mes.lower() in meses_frios:
        temp_min = random.randint(0, 8)
        temp_max = random.randint(9, 15)
    else:
        temp_min = random.randint(8, 12)
        temp_max = random.randint(16, 27)

    # 4. Generar confiabilidad (más alta para hospitales grandes)
    if "regional" in hospital.lower() or "clínico" in hospital.lower():
        confiabilidad = random.randint(75, 92)
    else:
        confiabilidad = random.randint(65, 85)

    return [
        historico_12_meses,
        mismos_meses,
        (temp_min, temp_max),
        confiabilidad,
        mensaje_prediccion,
        api_url
    ]


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
                <p style="font-size: 0.8rem; margin-top: 10px;">URL de la API: {api_url}</p>
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
        # Medidor de confiabilidad (estilo original)
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
        </div>
        """, unsafe_allow_html=True)

        # Añadir información de selección debajo del medidor
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
