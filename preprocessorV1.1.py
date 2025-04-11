from sklearn.base import BaseEstimator, TransformerMixin
import numpy as np
import pandas as pd

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
