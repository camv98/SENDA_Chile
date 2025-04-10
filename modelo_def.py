from xgboost import XGBRegressor #
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.model_selection import TimeSeriesSplit, GridSearchCV, train_test_split
#pip install Openpyxl


#def cargar_datos():
#    """
#    Carga los datos de hospitales desde archivos CSV.

#    Returns:
#        tuple: (DataFrame con datos del 2024, lista de hospitales únicos)
#    """
    # Cargar datos principales de hospitales, poner el de toda la data
#    df_2024_csv = pd.read_csv("/code/camv98/SENDA_Chile/raw_data/hospitales_unicos_2023.csv")

    # Cargar lista de hospitales únicos, poner el merge de seremi, hosp, area
#    hospitales_df = pd.read_csv("/code/camv98/SENDA_Chile/raw_data/hospitales_unicos_merge.csv")

    # Extraer la lista de nombres de hospitales válidos
#    hospitales_lista = hospitales_df['Nombre Establecimiento'].unique().tolist()

#    return df_2024_csv, hospitales_df, hospitales_lista
df_2024_csv = pd.read_excel("/home/bren/code/camv98/SENDA_Chile/Consolidado Estadísticas Hospitalarias 2021.xlsx", skiprows=2)
hospitales_df = pd.read_csv("/home/bren/code/camv98/SENDA_Chile/raw_data/hospitales_unicos_merge.csv")
hospitales_lista = hospitales_df['Nombre Establecimiento'].unique().tolist()


#Toma el df merge de seremi, hosp y area
def procesar_seremi_y_predecir(df, seremi, funcion_entrenamiento):
    """
    Procesa un SEREMI específico, obteniendo todos sus hospitales y áreas,
    y realiza predicciones para cada combinación hospital-área.

    Args:
        df (pd.DataFrame): DataFrame con los datos (debe tener columnas SEREMI, hospital, area)
        seremi (str): Nombre del SEREMI a procesar
        funcion_entrenamiento (function): Función de entrenamiento (entrenar_modelo_xgboost_optimo)

    Returns:
        list: Lista de diccionarios con los resultados de cada predicción
    """
    # Filtrar datos por SEREMI
    df_seremi = df[df['SEREMI'] == seremi]

    if df_seremi.empty:
        return f"No se encontraron datos para el SEREMI: {seremi}"

    # Obtener lista única de hospitales en este SEREMI
    hospitales = df_seremi['hospital'].unique()

    resultados = []

    df_modelo_base = preparar_datos_para_modelo(df_2024_csv, hospitales_lista)

    # Para cada hospital en el SEREMI
    for hospital in hospitales:
        # Filtrar datos para este hospital
        df_hospital = df_seremi[df_seremi['hospital'] == hospital]

        # Obtener áreas únicas en este hospital
        areas = df_hospital['area'].unique()

        # Para cada área en el hospital
        for area in areas:
            # Entrenar modelo y obtener predicciones
            try:
                resultado = funcion_entrenamiento(df_modelo_base, hospital, area)
                resultados.append(resultado)
            except Exception as e:
                print(f"Error al procesar hospital {hospital}, área {area}: {str(e)}")
                continue

    return resultados

def preparar_datos_para_modelo(df, hospitales_validos):
    """
    Transforma el dataset original de formato mensual a formato largo diario.
    Incluye solo hospitales que están en la lista de hospitales válidos.

    Devuelve un DataFrame con columnas:
    ['Fecha', 'Nombre Establecimiento', 'Nombre Nivel Cuidado', 'Glosa', 'Valor']
    """
    # 1. Nos quedamos solo con los hospitales válidos especificados
    df = df[df['Nombre Establecimiento'].isin(hospitales_validos)].copy()

    # 2. Creamos un diccionario para traudcir los nombres de columnas de mes a número
    meses_mapeo = {
        'Ene': 1, 'Feb': 2, 'Mar': 3, 'Abr': 4, 'May': 5, 'Jun': 6,
        'Jul': 7, 'Ago': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dic': 12
    }

    # 3. Extraemos solo las columnas de meses en orden
    columnas_meses = list(meses_mapeo.keys())

    # 4. Transformamos el DataFrame de formato ancho a largo (melt)
    df_largo = df.melt(
        id_vars=['Nombre Establecimiento', 'Nombre Nivel Cuidado', 'Glosa'],
        value_vars=columnas_meses,
        var_name='Mes',
        value_name='Valor'
    )

    # 5. Reemplazamos nombres de meses por números y creamos columna de fecha (día 15 por simplicidad)
    df_largo['Mes_Num'] = df_largo['Mes'].map(meses_mapeo)
    df_largo['Fecha'] = pd.to_datetime({'year': 2024, 'month': df_largo['Mes_Num'], 'day': 15})

    # 6. Limiamos y dejamos columnas necesarias
    df_largo = df_largo[['Fecha', 'Nombre Establecimiento', 'Nombre Nivel Cuidado', 'Glosa', 'Valor']]

    # 7. Nos aseguramos que los valores estén en formato numérico
    df_largo['Valor'] = pd.to_numeric(df_largo['Valor'], errors='coerce')

    return df_largo

# Ejecutamos la función con los datos cargados
df_modelo_base = preparar_datos_para_modelo(df_2024_csv, hospitales_lista)

def entrenar_modelo_xgboost_optimo(df, hospital, area):
    """
    Entrena un modelo XGBoost más liviano y optimizado en tiempo de ejecución.
    """

    from xgboost import XGBRegressor

    # 1. Filtrar por hospital y área
    df_filtro = df[
        (df['Nombre Establecimiento'] == hospital) &
        (df['Nombre Nivel Cuidado'] == area)
    ].copy()

    # 2. Pivotear glosas a columnas
    df_pivot = df_filtro.pivot(index='Fecha', columns='Glosa', values='Valor').reset_index()

    # 3. Validar columnas necesarias
    columnas_necesarias = ['Dias Cama Disponibles', 'Dias Cama Ocupados',
                           'Promedio Cama Disponibles', 'Numero de Egresos']
    if not all(col in df_pivot.columns for col in columnas_necesarias):
        return f"Datos insuficientes en {hospital} - {area}"

    # 4. Ordenar por fecha
    df_pivot = df_pivot.sort_values('Fecha')

    # 5. Variables temporales
    df_pivot['Mes'] = df_pivot['Fecha'].dt.month
    df_pivot['Trimestre'] = df_pivot['Fecha'].dt.quarter

    # 6. Features históricas
    df_pivot['lag_1'] = df_pivot['Dias Cama Disponibles'].shift(1)
    df_pivot['lag_2'] = df_pivot['Dias Cama Disponibles'].shift(2)
    df_pivot['porcentaje_ocupacion'] = df_pivot['Dias Cama Ocupados'] / df_pivot['Dias Cama Disponibles']
    df_pivot['variacion_disponibles'] = df_pivot['Dias Cama Disponibles'].diff()
    df_pivot['ocupados_media_movil'] = df_pivot['Dias Cama Ocupados'].rolling(window=3).mean()
    df_pivot['promedio_media_movil'] = df_pivot['Promedio Cama Disponibles'].rolling(window=3).mean()
    df_pivot['egresos_media_movil'] = df_pivot['Numero de Egresos'].rolling(window=3).mean()

    # 7. Limpiar datos nulos
    df_modelo = df_pivot.dropna().copy()

    # 8. Features y target
    features = [
        'Dias Cama Ocupados',
        'Promedio Cama Disponibles',
        'Numero de Egresos',
        'Mes', 'Trimestre',
        'lag_1', 'lag_2',
        'porcentaje_ocupacion',
        'variacion_disponibles',
        'ocupados_media_movil',
        'promedio_media_movil',
        'egresos_media_movil'
    ]
    X = df_modelo[features]
    y = df_modelo['Dias Cama Disponibles']

    # 9. Train/test
    X_train, X_test, y_train, y_test = train_test_split(X, y, shuffle=False, test_size=0.2)

    # 10. Entrenar XGBoost más liviano
    modelo = XGBRegressor(
        n_estimators=50,
        max_depth=3,
        learning_rate=0.1,
        random_state=42,
        n_jobs=1
    )
    modelo.fit(X_train, y_train)

    # 11. Predicción y evaluación
    y_pred = modelo.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    rmse = mean_squared_error(y_test, y_pred) ** 0.5

    # 12. Resultados
    resultados = pd.DataFrame({
        'Fecha': df_modelo['Fecha'].iloc[-len(y_test):],
        'Real': y_test.values,
        'Predicho': y_pred
    })

    return {
        'modelo': 'XGBoost (optimizado)',
        'hospital': hospital,
        'area': area,
        'mae': mae,
        'rmse': rmse,
        'predicciones': resultados
    }

# Ejecutamos la versión optimizada
resultado_xgb_optimo = entrenar_modelo_xgboost_optimo(
    df_modelo_base,
    "Hospital Dr. Ernesto Torres Galdames (Iquique)",
    "401 - Área Médica Adulto Cuidados Básicos"
)

resultado_xgb_optimo if isinstance(resultado_xgb_optimo, dict) else print(resultado_xgb_optimo)
