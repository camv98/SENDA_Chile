import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin

def preparar_dataset_climatico_avanzado(df_datos):
    if 'Area' in df_datos.columns:
        df_datos = df_datos[df_datos['Area'] == "Datos Establecimiento"].copy()

    df_modelo = df_datos.pivot(index='Fecha', columns='Glosa', values='Valor').reset_index()

    columnas_necesarias = [
        'Dias Cama Disponibles', 'Dias Cama Ocupados',
        'Promedio Cama Disponibles', 'Numero de Egresos', 'Egresos Fallecidos'
    ]
    columnas_faltantes = [col for col in columnas_necesarias if col not in df_modelo.columns]
    if columnas_faltantes:
        print("❌ Faltan columnas en los datos pivotados:", columnas_faltantes)
        return None

    clima = df_datos.drop_duplicates(subset='Fecha')[[
        'Fecha', 'Temperatura Máxima', 'Temperatura Mínima',
        'Precipitaciones (suma)', 'Dirección del Viento'
    ]] if 'Temperatura Máxima' in df_datos.columns else pd.DataFrame()

    if not clima.empty:
        df_modelo = pd.merge(df_modelo, clima, on='Fecha', how='left')
        df_modelo = pd.get_dummies(df_modelo, columns=['Dirección del Viento'], prefix='Viento')

    df_modelo = df_modelo.sort_values('Fecha')
    df_modelo['Mes'] = df_modelo['Fecha'].dt.month
    df_modelo['Trimestre'] = df_modelo['Fecha'].dt.quarter

    df_modelo['lag_1'] = df_modelo['Dias Cama Disponibles'].shift(1)
    df_modelo['lag_2'] = df_modelo['Dias Cama Disponibles'].shift(2)
    df_modelo['lag_3'] = df_modelo['Dias Cama Disponibles'].shift(3)
    df_modelo['media_movil_3'] = df_modelo['Dias Cama Disponibles'].rolling(window=3).mean()
    df_modelo['variacion_disponibles'] = df_modelo['Dias Cama Disponibles'].diff()
    df_modelo['porcentaje_ocupacion'] = df_modelo['Dias Cama Ocupados'] / df_modelo['Dias Cama Disponibles']
    df_modelo['ocupados_media_movil'] = df_modelo['Dias Cama Ocupados'].rolling(window=3).mean()
    df_modelo['promedio_media_movil'] = df_modelo['Promedio Cama Disponibles'].rolling(window=3).mean()
    df_modelo['egresos_media_movil'] = df_modelo['Numero de Egresos'].rolling(window=3).mean()
    df_modelo['egresos_fallecidos_media_movil'] = df_modelo['Egresos Fallecidos'].rolling(window=3).mean()

    if 'Temperatura Máxima' in df_modelo.columns and 'Temperatura Mínima' in df_modelo.columns:
        df_modelo['Diferencia Térmica'] = df_modelo['Temperatura Máxima'] - df_modelo['Temperatura Mínima']
        df_modelo['temp_max_movil'] = df_modelo['Temperatura Máxima'].rolling(window=3).mean()
        df_modelo['precipitacion_movil'] = df_modelo['Precipitaciones (suma)'].rolling(window=3).mean()
        df_modelo['interaccion_ocupacion_temp'] = df_modelo['porcentaje_ocupacion'] * df_modelo['Temperatura Máxima']
        df_modelo['interaccion_precipitacion_disp'] = df_modelo['Precipitaciones (suma)'] * df_modelo['Dias Cama Disponibles']

    df_modelo['same_month_last_year'] = df_modelo['Dias Cama Disponibles'].shift(12)
    df_modelo['hist_avg_mes'] = df_modelo.groupby('Mes')['Dias Cama Disponibles'].transform('mean')

    return df_modelo.dropna().copy()

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


def cargar_datos_clima(fecha_str, hospital, ruta_base):
    """Carga datos climáticos desde archivo basado en hospital y fecha"""
    fecha = pd.to_datetime(fecha_str)
    ruta_clima = os.path.join(ruta_base, f"clima_{hospital}.csv")
    
    try:
        df = pd.read_csv(ruta_clima)
        df['Fecha'] = pd.to_datetime(df['Fecha'])
        df['Mes'] = df['Fecha'].dt.month
        return df[df['Mes'] == fecha.month].iloc[-1]  # Último registro del mes
    except Exception as e:
        raise ValueError(f"Error cargando datos climáticos: {str(e)}")

# 3. Función principal que usa todo (nueva)
def cargar_datos_clima(fecha_str, hospital, ruta_base="nuevo_clima"):
    """Carga datos climáticos desde archivo basado en hospital y fecha"""
    fecha = pd.to_datetime(fecha_str)
    ruta_clima = os.path.join(ruta_base, f"{hospital}.csv")
    
    try:
        df = pd.read_csv(ruta_clima)
        df['Fecha'] = pd.to_datetime(df['Fecha'])
        df['Mes'] = df['Fecha'].dt.month
        return df[df['Mes'] == fecha.month].iloc[-1]  # Último registro del mes
    except Exception as e:
        raise ValueError(f"Error cargando datos climáticos: {str(e)}")

# 3. Función principal que usa todo (nueva)
def return_xnew_prepoc(fecha, hospital, ruta_clima="nuevo_clima"):
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
    datos_clima = cargar_datos_clima(fecha, hospital, ruta_clima)
    
    # Paso 2: Crear input para el preprocesador
    input_preprocesador = {
        'Temperatura Máxima': datos_clima['Temperatura Máxima'],
        'Temperatura Mínima': datos_clima['Temperatura Mínima'],
        'Precipitaciones (suma)': datos_clima['Precipitaciones (suma)'],
        'mes': pd.to_datetime(fecha).month
    }
    
    # Paso 3: Configurar y usar el ClimaPreprocessor
    preprocesador = ClimaPreprocessor()
    df_hospital_historico=pd.read_csv(os.path.join("df_extr", f"{hospital}_df_extr.csv"))
    preprocesador.fit(df_hospital_historico)  # Entrenar con datos históricos
    datos_procesados = preprocesador.transform(input_preprocesador)
    
    # Paso 4: Retornar resultado (aquí podrías añadir tu modelo predictivo)
    return datos_procesados
def preparar_y_preprocesar_x_futuro(X_pred, df_clima_general, df_hospital_historico):
    """
    Combina la preparación de X_futuro y el preprocesamiento de datos climáticos,
    utilizando un dataset general de clima y el dataframe histórico de hospitales.
    xpred= deberia tener 
        "fecha": pd.to_datetime(date),
        "hospital": [hospital],
        "SEREMI": [SEREMI],
    """
    hospital=X_pred['hospital']
    fecha=X_pred['fecha']
    seremi = X_pred['SEREMI']
    fecha_dt = pd.to_datetime(fecha)
    datos_clima = df_clima_general[
        (df_clima_general['seremi'] == seremi) &
        (pd.to_datetime(df_clima_general['Mes']).dt.year == fecha_dt.year) &
        (pd.to_datetime(df_clima_general['Mes']).dt.month == fecha_dt.month)
    ]

    # Verificar si el DataFrame está vacío
    if datos_clima.empty:
        print(f"Advertencia: No se encontraron datos climáticos para {hospital}, {fecha}.")
        return None  # O algún otro valor predeterminado

    datos_clima = datos_clima.iloc[0]
    # 2. Crear input para el preprocesador
    input_preprocesador = {
        'Temperatura Máxima': datos_clima['temperature_2m_max'],
        'Temperatura Mínima': datos_clima['temperature_2m_min'],
        'Precipitaciones (suma)': datos_clima['precipitation_sum'],
        'mes': fecha_dt.month
    }

    # 3. Configurar y usar el ClimaPreprocessor
    preprocesador = ClimaPreprocessor()
    preprocesador.fit(df_hospital_historico)  # Entrenar con datos históricos
    datos_procesados = preprocesador.transform(input_preprocesador)

    # 4. Definir features requeridas (lista predefinida)
    features_requeridas = [
        'Dias Cama Ocupados', 'Promedio Cama Disponibles', 'Numero de Egresos',
        'Mes', 'Trimestre', 'lag_1', 'lag_2', 'lag_3', 'media_movil_3',
        'porcentaje_ocupacion', 'variacion_disponibles',
        'ocupados_media_movil', 'promedio_media_movil', 'egresos_media_movil',
        'Temperatura Máxima', 'Temperatura Mínima', 'Precipitaciones (suma)',
        'Diferencia Térmica', 'temp_max_movil', 'precipitacion_movil',
        'same_month_last_year', 'hist_avg_mes',
        'interaccion_ocupacion_temp', 'interaccion_precipitacion_disp',
        'Viento_SW', 'Viento_W'
    ]

    # 5. Crear DataFrame base desde datos_procesados
    X_futuro = datos_procesados.copy()

    # 6. Añadir variables obligatorias del histórico
    ultima = df_hospital_historico.iloc[-1]
    obligatorias = {
        'Dias Cama Ocupados': ultima['Dias Cama Ocupados'],
        'Promedio Cama Disponibles': ultima['Promedio Cama Disponibles'],
        'Numero de Egresos': ultima['Numero de Egresos'],
        'lag_1': ultima['Dias Cama Disponibles'],
        'lag_2': df_hospital_historico['Dias Cama Disponibles'].iloc[-2] if len(df_hospital_historico) > 1 else ultima['Dias Cama Disponibles'],
        'lag_3': df_hospital_historico['Dias Cama Disponibles'].iloc[-3] if len(df_hospital_historico) > 2 else ultima['Dias Cama Disponibles'],
        'media_movil_3': df_hospital_historico['Dias Cama Disponibles'].rolling(3).mean().iloc[-1],
        'porcentaje_ocupacion': (ultima['Dias Cama Ocupados'] / ultima['Promedio Cama Disponibles']) * 100
    }
    X_futuro = X_futuro.assign(**obligatorias)

    # 7. Calcular variables derivadas de clima
    if 'Temperatura Máxima' in X_futuro:
        X_futuro['Diferencia Térmica'] = X_futuro['Temperatura Máxima'] - X_futuro['Temperatura Mínima']
        X_futuro['interaccion_ocupacion_temp'] = X_futuro['porcentaje_ocupacion'] * X_futuro['Temperatura Máxima']
        X_futuro['interaccion_precipitacion_disp'] = X_futuro['Precipitaciones (suma)'] * X_futuro['Promedio Cama Disponibles']

    # 8. Inicializar columnas de viento faltantes con 0
    vientos_requeridos = ['Viento_E', 'Viento_NE', 'Viento_S', 'Viento_SE', 'Viento_SW', 'Viento_W']
    for viento in vientos_requeridos:
        if viento not in X_futuro:
            X_futuro[viento] = 0.0

    # 9. Asegurar todas las columnas requeridas
    for col in features_requeridas:
        if col not in X_futuro:
            X_futuro[col] = df_hospital_historico[col].mean() if col in df_hospital_historico.columns else 0.0

    # 10. Ordenar columnas EXACTAMENTE como el modelo las espera
    X_futuro = X_futuro[features_requeridas]

    # 11. Asegurar que todos los datos sean numéricos
    X_futuro = X_futuro.astype(float)

    return X_futuro