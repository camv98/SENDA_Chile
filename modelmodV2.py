# Aproveche a quitar algunos modulos que ya no servian
# para dejar un poco mas limpio el archivo
import numpy as np
import pandas as pd
from xgboost import XGBRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error
from ml_logic.data import extraer_info_hospital_area_todo_el_año
from ml_logic.preprocessor import preparar_dataset_climatico_avanzado

def extraer_y_preparar_datos(hospital, filtrado_limpio, seremi_data):
    """
    Funcion que extrae la información de un hospital específico y prepara nuestro dataset.
    """
    df_base = extraer_info_hospital_area_todo_el_año(hospital, filtrado_limpio, seremi_data)
    if df_base is None or df_base.empty:
        print("❌ No se encontraron datos del hospital especificado.")
        return None
    df_modelo = preparar_dataset_climatico_avanzado(df_base)
    if df_modelo is None or df_modelo.empty:
        print("❌ No se pudo preparar el dataset.")
        return None
    return df_modelo

def obtener_features(df_modelo):
    """
    Funcion que define todas las columnas que se utilizarán como features para el modelo.
    """
    base_features = [
        'Dias Cama Ocupados', 'Promedio Cama Disponibles', 'Numero de Egresos',
        'Mes', 'Trimestre', 'lag_1', 'lag_2', 'lag_3', 'media_movil_3',
        'porcentaje_ocupacion', 'variacion_disponibles',
        'ocupados_media_movil', 'promedio_media_movil', 'egresos_media_movil',
        'Temperatura Máxima', 'Temperatura Mínima', 'Precipitaciones (suma)',
        'Diferencia Térmica', 'temp_max_movil', 'precipitacion_movil',
        'same_month_last_year', 'hist_avg_mes',
        'interaccion_ocupacion_temp', 'interaccion_precipitacion_disp'
    ]
    viento_features = [col for col in df_modelo.columns if col.startswith('Viento_')]
    return base_features + viento_features

def entrenar_modelo(X, y):
    """
    La funcion que entrena al modelo XGBoost con los datos completos.
    """
    model = XGBRegressor(n_jobs=1, random_state=42)
    model.fit(X, y)
    return model

def evaluar_modelo(model, X, y, fechas):
    """
    Evalúa el modelo en los datos de entrenamiento y devuelve un dataframe con métricas y errores.
    """
    y_pred = model.predict(X)
    mae = mean_absolute_error(y, y_pred)
    rmse = mean_squared_error(y, y_pred) ** 0.5
    error_pct = np.mean(np.abs((y.values - y_pred) / y.values)) * 100

    print(f"✅ MAE: {mae:.2f}")
    print(f"✅ RMSE: {rmse:.2f}")
    print(f"📉 Error promedio porcentual: {error_pct:.2f}%")

    return pd.DataFrame({
        'Fecha': fechas,
        'Real': y.values,
        'Predicho': y_pred,
        'Error Absoluto': np.abs(y.values - y_pred),
        'Error Porcentual (%)': np.abs((y.values - y_pred) / y.values) * 100
    })

def preparar_fila_futura(df_modelo, clima_futuro, mes_futuro, hospital, todas_las_features):
    """
    La funcion que crea una nueva fila con datos climáticos futuros y variables derivadas (necesarias para hacer la predicción).
    """
    mes_dt = pd.to_datetime(mes_futuro)
    ultima_fila = df_modelo.iloc[-1].copy()
    fila_nueva = ultima_fila.copy()

    # Actualiza la fila con valores futuros conocidos
    fila_nueva['Fecha'] = mes_dt
    fila_nueva['Mes'] = mes_dt.month
    fila_nueva['Trimestre'] = mes_dt.quarter
    fila_nueva['Temperatura Máxima'] = clima_futuro['Temperatura Máxima'].values[0]
    fila_nueva['Temperatura Mínima'] = clima_futuro['Temperatura Mínima'].values[0]
    fila_nueva['Precipitaciones (suma)'] = clima_futuro['Precipitaciones (suma)'].values[0]
    fila_nueva['Diferencia Térmica'] = fila_nueva['Temperatura Máxima'] - fila_nueva['Temperatura Mínima']

    # Calcula promedios históricos del mismo mes
    historico_mes = df_modelo[df_modelo['Mes'] == fila_nueva['Mes']]['Dias Cama Disponibles']
    fila_nueva['same_month_last_year'] = historico_mes.iloc[-12] if len(historico_mes) >= 12 else historico_mes.mean()
    fila_nueva['hist_avg_mes'] = historico_mes.mean()

    # Rellena valores faltantes
    for col in todas_las_features:
        if col not in fila_nueva:
            fila_nueva[col] = df_modelo[col].mean() if col in df_modelo.columns else 0

    return pd.DataFrame([fila_nueva])

def pipeline_final_mae_reducido(hospital, filtrado_limpio, seremi_data, modo="entrenamiento", mes_futuro=None):
    """
    Pipeline principal que maneja los dos modos discutidos llamando las funciones anteriores:
    - entrenamiento: entrena el modelo con todos los datos históricos y reporta desempeño.
    - futuro: predice camas disponibles para un mes futuro usando datos climáticos del SEREMI.
    """
    print(f"🔍 Procesando hospital: {hospital}")

    # 1. Cargar y preparar el dataset
    df_modelo = extraer_y_preparar_datos(hospital, filtrado_limpio, seremi_data)
    if df_modelo is None:
        return None

    # 2. Definir variables predictoras
    todas_las_features = obtener_features(df_modelo)
    X_full = df_modelo[todas_las_features]
    y_full = df_modelo['Dias Cama Disponibles']

    # 3. Entrenamiento y evaluación
    if modo == "entrenamiento":
        print("🔧 Entrenando modelo con todos los datos disponibles...")
        model = entrenar_modelo(X_full, y_full)
        return evaluar_modelo(model, X_full, y_full, df_modelo['Fecha'])

    # 4. Predicción futura
    elif modo == "futuro" and mes_futuro is not None:
        print(f"🔮 Prediciendo para el mes futuro: {mes_futuro}")
        model = entrenar_modelo(X_full, y_full)

        mes_dt = pd.to_datetime(mes_futuro)
        clima_futuro = seremi_data[
            (seremi_data['Nombre Establecimiento'] == hospital) &
            (seremi_data['Fecha'] == mes_dt)
        ]
        if clima_futuro.empty:
            print(f"⚠️ No se encontraron datos climáticos para {mes_futuro}")
            return None

        df_futuro = preparar_fila_futura(df_modelo, clima_futuro, mes_futuro, hospital, todas_las_features)
        X_futuro = df_futuro[todas_las_features]
        prediccion = model.predict(X_futuro)[0]
        print(f"📈 Predicción para {mes_futuro}: {prediccion:.2f} camas disponibles")
        return prediccion

    else:
        print("⚠️ Modo no reconocido o mes_futuro no especificado.")
        return None
