import numpy as np
import time
import pandas as pd
from colorama import Fore, Style
from typing import Tuple
from xgboost import XGBRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.model_selection import TimeSeriesSplit, GridSearchCV, train_test_split
from ml_logic.data import extraer_info_hospital_area_todo_el_año
from ml_logic.preprocessor import preparar_dataset_climatico_avanzado
from typing import Tuple, Dict, Union
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split, TimeSeriesSplit, GridSearchCV
from xgboost import XGBRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error

def pipeline_final_mae_reducido(hospital, filtrado_limpio, seremi_data, modo= "entrenamiento", mes_futuro= None):
    """
    Pipeline para predecir camas disponibles:
    - Modo 'entrenamiento': entrena con todo el historial disponible (sin split)
    - Modo 'futuro': predice camas disponibles para un mes futuro usando datos climáticos
    """
    print(f"🔍 Procesando hospital: {hospital}")

    # 1. Extracción de datos
    df_base = extraer_info_hospital_area_todo_el_año(hospital, filtrado_limpio, seremi_data)
    if df_base is None or df_base.empty:
        print("❌ No se encontraron datos del hospital especificado.")
        return None

    # 2. Preparación del dataset
    df_modelo = preparar_dataset_climatico_avanzado(df_base)
    if df_modelo is None or df_modelo.empty:
        print("❌ No se pudo preparar el dataset.")
        return None

    # 3. Definición de features
    todas_las_features = [
        'Dias Cama Ocupados', 'Promedio Cama Disponibles', 'Numero de Egresos',
        'Mes', 'Trimestre', 'lag_1', 'lag_2', 'lag_3', 'media_movil_3',
        'porcentaje_ocupacion', 'variacion_disponibles',
        'ocupados_media_movil', 'promedio_media_movil', 'egresos_media_movil',
        'Temperatura Máxima', 'Temperatura Mínima', 'Precipitaciones (suma)',
        'Diferencia Térmica', 'temp_max_movil', 'precipitacion_movil',
        'same_month_last_year', 'hist_avg_mes',
        'interaccion_ocupacion_temp', 'interaccion_precipitacion_disp'
    ] + [col for col in df_modelo.columns if col.startswith('Viento_')]

    # 4. Modo entrenamiento
    if modo == "entrenamiento":
        print("🔧 Entrenando modelo con todos los datos disponibles...")
        X_full = df_modelo[todas_las_features]
        y_full = df_modelo['Dias Cama Disponibles']

        model = XGBRegressor(n_jobs=1, random_state=42)
        model.fit(X_full, y_full)

        y_pred = model.predict(X_full)
        mae = mean_absolute_error(y_full, y_pred)
        rmse = mean_squared_error(y_full, y_pred) ** 0.5
        error_pct = np.mean(np.abs((y_full.values - y_pred) / y_full.values)) * 100

        print(f"✅ MAE: {mae:.2f}")
        print(f"✅ RMSE: {rmse:.2f}")
        print(f"📉 Error promedio porcentual: {error_pct:.2f}%")

        resultados = pd.DataFrame({
            'Fecha': df_modelo['Fecha'].values,
            'Real': y_full.values,
            'Predicho': y_pred,
            'Error Absoluto': np.abs(y_full.values - y_pred),
            'Error Porcentual (%)': np.abs((y_full.values - y_pred) / y_full.values) * 100
        })

        return resultados
    # 5. Modo prediccion
    elif modo == "futuro" and mes_futuro is not None:
        print(f"🔮 Prediciendo para el mes futuro: {mes_futuro}")

        X_full = df_modelo[todas_las_features]
        y_full = df_modelo['Dias Cama Disponibles']
        model = XGBRegressor(n_jobs=1, random_state=42)
        model.fit(X_full, y_full)

        mes_dt = pd.to_datetime(mes_futuro)
        clima_futuro = seremi_data[(seremi_data['Nombre Establecimiento'] == hospital) & (seremi_data['Fecha'] == mes_dt)]

        if clima_futuro.empty:
            print(f"⚠️ No se encontraron datos climáticos para {mes_futuro}")
            return None

        ultima_fila = df_modelo.iloc[-1].copy()
        fila_nueva = ultima_fila.copy()

        fila_nueva['Fecha'] = mes_dt
        fila_nueva['Mes'] = mes_dt.month
        fila_nueva['Trimestre'] = mes_dt.quarter
        fila_nueva['Temperatura Máxima'] = clima_futuro['Temperatura Máxima'].values[0]
        fila_nueva['Temperatura Mínima'] = clima_futuro['Temperatura Mínima'].values[0]
        fila_nueva['Precipitaciones (suma)'] = clima_futuro['Precipitaciones (suma)'].values[0]
        fila_nueva['Diferencia Térmica'] = fila_nueva['Temperatura Máxima'] - fila_nueva['Temperatura Mínima']

        historico_mes = df_modelo[df_modelo['Mes'] == fila_nueva['Mes']]['Dias Cama Disponibles']
        fila_nueva['same_month_last_year'] = historico_mes.iloc[-12] if len(historico_mes) >= 12 else historico_mes.mean()
        fila_nueva['hist_avg_mes'] = historico_mes.mean()

        for col in todas_las_features:
            if col not in fila_nueva:
                fila_nueva[col] = df_modelo[col].mean() if col in df_modelo.columns else 0

        df_futuro = pd.DataFrame([fila_nueva])
        X_futuro = df_futuro[todas_las_features]
        prediccion = model.predict(X_futuro)[0]

        print(f"📈 Predicción para {mes_futuro}: {prediccion:.2f} camas disponibles")
        return prediccion

    else:
        print("⚠️ Modo no reconocido o mes_futuro no especificado.")
        return None
