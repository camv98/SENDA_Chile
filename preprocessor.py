import numpy as np
import pandas as pd

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

input
x_new
'Temperatura Máxima'
"mes"
'Temperatura Mínima'
'Precipitaciones (suma)'
,df_del hospital

output prepoc
'Mes', 'Trimestre', 'Temperatura Máxima', 'Temperatura Mínima',
        'Precipitaciones (suma)', 'Diferencia Térmica',
        'same_month_last_year', 'hist_avg_mes'

class ClimaPreprocessor:
    def __init__(self):
        # El constructor __init__ permite definir parámetros de la instancia.
        # es mejor tenerlo para facilitar futuras extensiones.
        pass

    def transform(self, x_new, df_hist):
        """
        x_new: dict con claves: 'Temperatura Máxima', 'Temperatura Mínima', 'Precipitaciones (suma)', 'mes'
        df_hist: DataFrame histórico del hospital (ya transformado con preparar_dataset_climatico_avanzado)
        """

        if df_hist is None or df_hist.empty:
            raise ValueError("❌ El historial del hospital no puede estar vacío")

        # Aseguramos que tenga las columnas necesarias
        required_cols = ['Fecha', 'Dias Cama Disponibles', 'Mes']
        for col in required_cols:
            if col not in df_hist.columns:
                raise ValueError(f"❌ Falta la columna requerida en el historial: {col}")

        # Ordenamos por fecha
        df_hist = df_hist.sort_values('Fecha')

        # Extraemos la última fila válida para calcular referencias
        last_row = df_hist.iloc[-1]

        # Calculamos valores derivados a partir de x_new y df_hist
        temp_max = x_new['Temperatura Máxima']
        temp_min = x_new['Temperatura Mínima']
        precipitacion = x_new['Precipitaciones (suma)']
        mes = x_new['mes']

        diferencia_termica = temp_max - temp_min

        # Mismo mes del año pasado
        same_month_last_year = df_hist[df_hist['Mes'] == mes].iloc[-12:]['Dias Cama Disponibles'].mean()

        # Promedio histórico del mes
        hist_avg_mes = df_hist[df_hist['Mes'] == mes]['Dias Cama Disponibles'].mean()

        X_processed = pd.DataFrame([{
            'Mes': mes,
            'Trimestre': (mes - 1) // 3 + 1,
            'Temperatura Máxima': temp_max,
            'Temperatura Mínima': temp_min,
            'Precipitaciones (suma)': precipitacion,
            'Diferencia Térmica': diferencia_termica,
            'same_month_last_year': same_month_last_year,
            'hist_avg_mes': hist_avg_mes
        }])

        return X_processed

x_new = {
    'Temperatura Máxima': 28.5,
    'Temperatura Mínima': 15.2,
    'Precipitaciones (suma)': 12.3,
    'mes': 4
}

preproc = ClimaPreprocessor()
X_final = preproc.transform(x_nuevo, df_hospital)

from sklearn.base import BaseEstimator, TransformerMixin

class ClimaPreprocessor(BaseEstimator, TransformerMixin):
    def __init__(self):
        pass

    def fit(self, X, y=None):
        """
        Este método se invoca cuando se "entrena" el pipeline.
        Aquí se puede procesar o almacenar información del dataset histórico.
        En el caso de nuestro proyecto, X seria el DataFrame histórico (df_hospital) preprocesado.
        """
        # Guardamos el DataFrame histórico para su uso en transform.
        self.hospital_df_ = X.copy()
        # Convertimos la columna 'Fecha' a tipo datetime y extraemos el mes, esto segun lei se hace por seguridad.
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
        # para el mismo mes. Aquí, si existen al menos 12 registros para ese mes se toma el valor correspondiente
        # que es como lo entendi.
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

    x_new = {
    'Temperatura Máxima': 28.5,
    'Temperatura Mínima': 15.2,
    'Precipitaciones (suma)': 12.3,
    'mes': 4
}

preproc = ClimaPreprocessor()
X_final = preproc.transform(x_nuevo, df_hospital)
