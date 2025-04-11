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

def pipeline_final_mae_reducido(hospital: str, filtrado_limpio: pd.DataFrame, seremi_data: pd.DataFrame) -> Union[pd.DataFrame, None]:
    """
    Pipeline completo para predecir camas disponibles con XGBoost
    
    Args:
        hospital: Nombre del hospital a procesar
        
    Returns:
        DataFrame con resultados de predicción o None si hay error
    """
    # 1. Extracción de datos
    df_base = extraer_datos_hospital(hospital, filtrado_limpio,seremi_data)
    if df_base is None or df_base.empty:
        print("❌ Error en extracción de datos")
        return None

    # 2. Preparación de datos
    df_modelo = preparar_datos(df_base)
    if df_modelo is None or df_modelo.empty:
        print("❌ Error en preparación de datos")
        return None

    # 3. Selección de features
    features = seleccionar_features(df_modelo)

    # 4. División de datos
    X_train, X_test, y_train, y_test = dividir_datos(df_modelo, features)

    # 5. Entrenamiento del modelo
    mejor_modelo = entrenar_modelo_xgboost(X_train, y_train)

    # 6. Evaluación del modelo
    resultados = evaluar_modelo(mejor_modelo, X_test, y_test, df_modelo)
    
    return resultados

# Funciones auxiliares (manteniendo la secuencia original)

def extraer_datos_hospital(hospital: str,filtrado_limpio: pd.DataFrame, seremi_data: pd.DataFrame) -> Union[pd.DataFrame, None]:
    """Paso 1: Extrae datos del hospital especificado"""
    print(f"🔍 Extrayendo datos para: {hospital}")
    return extraer_info_hospital_area_todo_el_año(hospital,filtrado_limpio,seremi_data)

def preparar_datos(df: pd.DataFrame) -> Union[pd.DataFrame, None]:
    """Paso 2: Prepara el dataset con variables climáticas y derivadas"""
    print("🧪 Preparando dataset...")
    return preparar_dataset_climatico_avanzado(df)

def seleccionar_features(df: pd.DataFrame) -> list:
    """Paso 3: Selecciona las features para el modelo"""
    features_base = [
        'Dias Cama Ocupados', 'Promedio Cama Disponibles', 'Numero de Egresos',
        'Mes', 'Trimestre', 'lag_1', 'lag_2', 'lag_3', 'media_movil_3',
        'porcentaje_ocupacion', 'variacion_disponibles',
        'ocupados_media_movil', 'promedio_media_movil', 'egresos_media_movil',
        'Temperatura Máxima', 'Temperatura Mínima', 'Precipitaciones (suma)',
        'Diferencia Térmica', 'temp_max_movil', 'precipitacion_movil',
        'same_month_last_year', 'hist_avg_mes',
        'interaccion_ocupacion_temp', 'interaccion_precipitacion_disp'
    ]
    features_viento = [col for col in df.columns if col.startswith('Viento_')]
    return features_base + features_viento

def dividir_datos(df: pd.DataFrame, features: list) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    """Paso 4: Divide los datos en train y test temporal"""
    X = df[features]
    y = df['Dias Cama Disponibles']
    return train_test_split(X, y, shuffle=False, test_size=0.2)

def entrenar_modelo_xgboost(X_train: pd.DataFrame, y_train: pd.Series) -> XGBRegressor:
    """Paso 5: Entrena modelo XGBoost con GridSearch"""
    print("🔧 Ajustando modelo con GridSearchCV...")
    
    param_grid = {
        'n_estimators': [50, 100],
        'max_depth': [2, 3],
        'learning_rate': [0.05, 0.1]
    }
    
    model = XGBRegressor(n_jobs=1, random_state=42)
    grid_search = GridSearchCV(
        estimator=model,
        param_grid=param_grid,
        scoring='neg_mean_absolute_error',
        cv=TimeSeriesSplit(n_splits=3),
        verbose=1
    )
    grid_search.fit(X_train, y_train)
    print("📌 Mejores parámetros encontrados:", grid_search.best_params_)
    return grid_search.best_estimator_

def evaluar_modelo(model: XGBRegressor, X_test: pd.DataFrame, 
                  y_test: pd.Series, df_original: pd.DataFrame) -> pd.DataFrame:
    """Paso 6: Evalúa el modelo y genera resultados"""
    print("📊 Evaluando sobre el 20% final de los datos...")
    y_pred = model.predict(X_test)
    
    # Cálculo de métricas
    mae = mean_absolute_error(y_test, y_pred)
    rmse = mean_squared_error(y_test, y_pred) ** 0.5
    error_pct = np.mean(np.abs((y_test.values - y_pred) / y_test.values)) * 100
    
    print(f"✅ MAE (camas): {mae:.2f}")
    print(f"✅ RMSE (camas): {rmse:.2f}")
    print(f"📉 Error promedio porcentual: {error_pct:.2f}%")
    
    # Resultados detallados
    return pd.DataFrame({
        'Fecha': df_original['Fecha'].iloc[-len(y_test):].values,
        'Real': y_test.values,
        'Predicho': y_pred,
        'Error Absoluto': np.abs(y_test.values - y_pred),
        'Error Porcentual (%)': np.abs((y_test.values - y_pred) / y_test.values) * 100
    })