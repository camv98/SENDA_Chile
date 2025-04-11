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

# Función para cargar el modelo XGBoost
def cargar_modelo(hospital_id):
    # Mantener el nombre original del hospital y añadir el sufijo del modelo
    ruta_modelo = os.path.join("/home/bren/code/camv98/SENDA_Chile/models/models/", f"{hospital_id}_modelo_xgb_nativo.ubj")

    if os.path.exists(ruta_modelo):
        try:
            modelo = XGBRegressor()
            modelo.load_model(ruta_modelo)
            return modelo
        except Exception as e:
            st.error(f"Error al cargar el modelo: {str(e)}")
            return None
    else:
        st.error(f"Modelo para hospital {hospital_id} no encontrado en: {ruta_modelo}")
        return None

class ClimaPreprocessor(BaseEstimator, TransformerMixin):
    def __init__(self):
        # El constructor __init__ permite definir parámetros de la instancia.
        # es mejor tenerlo para facilitar futuras extensiones.
        pass
    def fit(self, X, y=None):
        """
        Aquí se puede procesara o almacenara información del dataset histórico.
        En el caso de nuestro proyecto, X seria el DataFrame histórico (df_hospital) preprocesado.
        """
        # Guardamos el DataFrame (placeholder: hospital_df) histórico para su uso en transform.
        self.hospital_df_ = X.copy()
        # Convertimos la columna 'Fecha' a tipo datetime y extraemos el mes, esto entiendo que se hace por seguridad.
        if 'Fecha' in self.hospital_df_.columns:
            self.hospital_df_['Fecha'] = pd.to_datetime(self.hospital_df_['Fecha'])
            self.hospital_df_['Mes'] = self.hospital_df_['Fecha'].dt.month
        else:
            raise ValueError("El DataFrame histórico debe tener una columna 'Fecha'")
        return self

    def transform(self, x_new):
        """
        x_new: diccionario con los siguientes keys:
          - 'Temperatura Máxima'
          - 'Temperatura Mínima'
          - 'Precipitaciones (suma)'
          - 'mes'
        La función utiliza la data histórica (self.hospital_df_) para calcular:
          - 'Diferencia Térmica': diferencia entre la temperatura máxima y mínima.
          - 'same_month_last_year': valor obtenido de hace 12 registros dentro del mismo mes.
          - 'hist_avg_mes': promedio histórico de 'Dias Cama Disponibles' para el mes.
        """
        # Validamos que la data histórica fue fijada en fit.
        if not hasattr(self, "hospital_df_"):
            raise AttributeError("La data histórica no ha sido fijada. Llama a fit(X) primero.")
        # Extraemos valores desde x_new (nota: estos son los datos que deberiamos tener de la API del clima)
        try:
            temp_max = float(x_new['Temperatura Máxima'])
            temp_min = float(x_new['Temperatura Mínima'])
            precipitacion = float(x_new['Precipitaciones (suma)'])
            mes = int(x_new['mes'])
        except KeyError as e:
            raise KeyError(f"Falta la clave requerida en x_new: {e}")
        diferencia_termica = temp_max - temp_min

        # Utilizamos la data histórica para calcular 'hist_avg_mes' tal cual indico Claudio.
        df_hist = self.hospital_df_
        df_mes = df_hist[df_hist['Mes'] == mes]
        if df_mes.empty:
            hist_avg_mes = np.nan
        else:
            hist_avg_mes = df_mes['Dias Cama Disponibles'].mean()

        # Esto no se si este correcto pero para 'same_month_last_year', se puede plantear de distintas formas:
        # la opción que escogí es obtener el valor de "Dias Cama Disponibles" de hace 12 registros
        # para el mismo mes. Si existen al menos 12 registros para ese mes se toma el valor correspondiente
        # no recuerdo muy bien esta parte si es asi en nuestro proyecto.
        if len(df_mes) >= 12:
            same_month_last_year = df_mes['Dias Cama Disponibles'].iloc[-12]
        else:
            same_month_last_year = np.nan
        # El calculo del trimestre a partir del mes.
        trimestre = (mes - 1) // 3 + 1
        # El armado del DataFrame de salida con las columnas requeridas.
        X_processed = pd.DataFrame([{
            'Mes': mes,
            'Trimestre': trimestre,
            'Temperatura Máxima': temp_max,
            'Temperatura Mínima': temp_min,
            'Precipitaciones (suma)': precipitacion,
            'Diferencia Térmica': diferencia_termica,
            'same_month_last_year': same_month_last_year,
            'hist_avg_mes': hist_avg_mes
        }])
        return X_processed


# 3. Función principal que usa todo (nueva)
def cargar_datos_clima(seremi,fecha_str, ruta_base="nuevo_clima/nuevo_clima/"):
    """Carga datos climáticos desde archivo basado en hospital y fecha"""
    fecha = pd.to_datetime(fecha_str)
    ruta_clima = os.path.join(ruta_base, f"{seremi}.csv")
    try:
        df = pd.read_csv(ruta_clima)
        df['Fecha'] = pd.to_datetime(df['Mes'], errors='coerce')
        df['Fecha'] = pd.to_datetime(df['Fecha'])
        df['Mes'] = df['Fecha'].dt.month
        return df[df['Mes'] == fecha.month].iloc[-1]  # Último registro del mes
    except Exception as e:
        raise ValueError(f"Error cargando datos climáticos: {str(e)}")

# 3. Función principal que usa todo (nueva)
def return_xnew_prepoc(seremi,fecha, hospital, ruta_clima="nuevo_clima/nuevo_clima/"):
    """
    Ejemplo de uso completo:
    resultado = predecir_camas(
        fecha="2025-03-01",
        hospital="Hospital Regional",
        ruta_clima="data/climas",
        df_hospital_historico=df_hospital
    )
    """
    # Paso 1: Cargar y preparar datos climáticos
    datos_clima = cargar_datos_clima(seremi,fecha_str=fecha)
    # Paso 2: Crear input para el preprocesador
    input_preprocesador = {
        'Temperatura Máxima': datos_clima['temperature_2m_max'],
        'Temperatura Mínima': datos_clima['temperature_2m_min'],
        'Precipitaciones (suma)': datos_clima['precipitation_sum'],
        'mes': pd.to_datetime(fecha).month
    }
    # Paso 3: Configurar y usar el ClimaPreprocessor
    preprocesador = ClimaPreprocessor()
    df_hospital_historico=pd.read_csv(os.path.join("df_extr/df_extr/", f"{hospital}_df_extr.csv"))

    preprocesador.fit(df_hospital_historico)  # Entrenar con datos históricos
    datos_procesados = preprocesador.transform(input_preprocesador)
    # Paso 4: Retornar resultado (aquí podrías añadir tu modelo predictivo)
    return datos_procesados,df_hospital_historico

def preparar_x_futuro(x_new, df_historico, model):
    """
    Prepara X_futuro con TODAS las features exactamente como el modelo las espera
    Args:
        x_new: DataFrame con las columnas básicas
        df_historico: DataFrame histórico completo
        model: Modelo XGBoost ya entrenado (para obtener feature_names)
    Returns:
        DataFrame compatible al 100% con lo que el modelo espera
    """
    # 1. Obtener las features exactas que el modelo espera (en orden correcto)
    features_requeridas = model.get_booster().feature_names
    # 2. Crear DataFrame base desde x_new
    X_futuro = x_new.copy()
    # 3. Añadir variables obligatorias del histórico
    ultima = df_historico.iloc[-1]
    obligatorias = {
        'Dias Cama Ocupados': ultima['Dias Cama Ocupados'],
        'Promedio Cama Disponibles': ultima['Promedio Cama Disponibles'],
        'Numero de Egresos': ultima['Numero de Egresos'],
        'lag_1': ultima['Dias Cama Disponibles'],
        'lag_2': df_historico['Dias Cama Disponibles'].iloc[-2] if len(df_historico) > 1 else ultima['Dias Cama Disponibles'],
        'lag_3': df_historico['Dias Cama Disponibles'].iloc[-3] if len(df_historico) > 2 else ultima['Dias Cama Disponibles'],
        'media_movil_3': df_historico['Dias Cama Disponibles'].rolling(3).mean().iloc[-1],
        'porcentaje_ocupacion': (ultima['Dias Cama Ocupados'] / ultima['Promedio Cama Disponibles']) * 100
    }
    X_futuro = X_futuro.assign(**obligatorias)
    # 4. Calcular variables derivadas de clima
    if 'Temperatura Máxima' in X_futuro:
        X_futuro['Diferencia Térmica'] = X_futuro['Temperatura Máxima'] - X_futuro['Temperatura Mínima']
        X_futuro['interaccion_ocupacion_temp'] = X_futuro['porcentaje_ocupacion'] * X_futuro['Temperatura Máxima']
        X_futuro['interaccion_precipitacion_disp'] = X_futuro['Precipitaciones (suma)'] * X_futuro['Promedio Cama Disponibles']
    # 5. Inicializar columnas de viento faltantes con 0
    vientos_requeridos = ['Viento_E', 'Viento_NE', 'Viento_S', 'Viento_SE', 'Viento_SW', 'Viento_W']
    for viento in vientos_requeridos:
        if viento not in X_futuro:
            X_futuro[viento] = 0.0
    # 6. Asegurar todas las columnas requeridas
    for col in features_requeridas:
        if col not in X_futuro:
            X_futuro[col] = df_historico[col].mean() if col in df_historico.columns else 0.0
    # 7. Ordenar columnas EXACTAMENTE como el modelo las espera
    X_futuro = X_futuro[features_requeridas]
    # 8. Asegurar que todos los datos sean numéricos
    X_futuro = X_futuro.astype(float)
    return X_futuro

def hacer_prediccion(seremi,hospital_id, mes_seleccionado):
    """Realiza la predicción de camas disponibles"""
    model = cargar_modelo(hospital_id)
    if model is None:
        return None

    meses_a_numeros = {
        "Enero": 1, "Febrero": 2, "Marzo": 3, "Abril": 4,
        "Mayo": 5, "Junio": 6, "Julio": 7, "Agosto": 8,
        "Septiembre": 9, "Octubre": 10, "Noviembre": 11, "Diciembre": 12
    }

    # Obtener el número del mes
    mes_numero = meses_a_numeros.get(mes_seleccionado)
    if mes_numero is None:
        st.error(f"Mes no reconocido: {mes_seleccionado}")
        return None

    # Crear datetime para el primer día del mes
    año_actual = 2025
    fecha_dt = pd.to_datetime(f"{año_actual}-{mes_numero:02d}-01")

    x_new,df = return_xnew_prepoc(seremi,fecha_dt, hospital_id)
    x_futuro = preparar_x_futuro(x_new,df_historico=df,model=model)

    #st.write(x_futuro)

    try:
        y_pred = model.predict(x_futuro)
        return int(round(y_pred[0], 0))
    except Exception as e:
        st.error(f"Error al hacer la predicción: {str(e)}")
        return None

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

    ######################################################################3
    #             Aquí va la parte de la predicción                      #
    #######################################################################

    camas_predichas = hacer_prediccion(st.session_state.selected_seremi, st.session_state.selected_hospital, st.session_state.selected_month)

    if camas_predichas is not None:
        st.markdown(f"""
        <div style="text-align: center; margin: 50px 0;">
            <h2 style="font-size: 1.8rem;">Para el mes de <strong>{st.session_state.selected_month}</strong>, se predice que:</h2>
            <h1 style="font-size: 4rem; color: #00CC96; margin: 20px 0;">{camas_predichas}</h1>
            <h2 style="font-size: 1.8rem;">será el número de camas disponibles</h2>
        </div>
        """, unsafe_allow_html=True)

        with st.expander("Detalles de la predicción"):
                st.write(f"**Hospital:** {st.session_state.selected_hospital}")
                st.write(f"**Modelo utilizado:** XGBoost")
                st.write(f"**Mes predicho:** {st.session_state.selected_month}")
                st.write("**Características utilizadas:** Mes, Trimestre, Datos meteorológicos, Históricos")
    else:
        st.warning("No se pudo obtener la predicción")

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
