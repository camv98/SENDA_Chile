import numpy as np
import pandas as pd

from pathlib import Path
from colorama import Fore, Style
from dateutil.parser import parse

from senda.params import *
from senda.ml_logic.data import procesar_datasets_climaticos,procesar_datasets_hospitales,extraer_info_hospital_area_todo_el_año,descargar_de_bigquery
from senda.ml_logic.preprocessor import preparar_y_preprocesar_x_futuro
from senda.ml_logic.registry import load_model, save_results
# from senda.ml_logic.registry import mlflow_run, mlflow_transition_model

def preprocess() -> None:
    """
    - Query the raw dataset from Le Wagon's BigQuery dataset
    - Cache query result as a local CSV if it doesn't exist locally
    - Process query data
    - Store processed data on your personal BQ (truncate existing table if it exists)
    - No need to cache processed data as CSV (it will be cached when queried back from BQ during training)
    """



    """cargar datos de clima  y limpiar
    cargar datos de hospital y limpiar
    preproc de ambos y obtener
    """
    ruta_data = os.path.abspath(os.path.join(os.getcwd(), "..", "demo_day"))
    seremi_data_dict = {
    str(year): pd.read_csv(os.path.join(ruta_data, f"seremi_{year}.csv"))
    for year in range(2014, 2026)  # 2026 no está incluido
}

    ###datos del clima limpios
    seremi_data=procesar_datasets_climaticos(seremi_data_dict)
    seremi_data.to_csv(os.path.join(ruta_data, "seremi_data.csv"))
    print("✅ data de clima limpia guardada\n")
    hospitales_dic = {
    str(year): pd.read_csv(os.path.join(ruta_data, f"{year}_filtrado.csv"))
    for year in range(2014, 2026)  # 2026 no está incluido
}
    ###datos del camas y hospitales limpios
    filtrado_limpio=procesar_datasets_hospitales(hospitales_dic)
    filtrado_limpio.to_csv(os.path.join(ruta_data, "filtrado_limpio.csv"))
    print("✅ data de hospitales limpia guardada\n")



# def train(modo="entrenamiento", mes_futuro=None,hospital,
#     how="each") -> float:

#     """
#     - entrena el modelo segun sea entrenamiento (split data) o prediccion (total data)
#     -  guarda el modelo dependiendo si es general o para cada hospital
#     -
#     Return val_mae as a float
#     """


#     return

def evaluate(

    ) -> float:
    """
    Evaluate the performance of the latest production model on processed data
    Return MAE as a float
    """
    print(Fore.MAGENTA + "\n⭐️ Use case: evaluate" + Style.RESET_ALL)

    model = load_model(stage=stage)
    assert model is not None

    min_date = parse(min_date).strftime('%Y-%m-%d') # e.g '2009-01-01'
    max_date = parse(max_date).strftime('%Y-%m-%d') # e.g '2009-01-01'

    # Query your BigQuery processed table and get data_processed using `get_data_with_cache`
    query = f"""
        SELECT * EXCEPT(_0)
        FROM `{GCP_PROJECT}`.{BQ_DATASET}.processed_{DATA_SIZE}
        WHERE _0 BETWEEN '{min_date}' AND '{max_date}'
    """

    data_processed_cache_path = Path(f"{LOCAL_DATA_PATH}/processed/processed_{min_date}_{max_date}_{DATA_SIZE}.csv")
    data_processed = get_data_with_cache(
        gcp_project=GCP_PROJECT,
        query=query,
        cache_path=data_processed_cache_path,
        data_has_header=False
    )

    if data_processed.shape[0] == 0:
        print("❌ No data to evaluate on")
        return None

    data_processed = data_processed.to_numpy()

    X_new = data_processed[:, :-1]
    y_new = data_processed[:, -1]

    metrics_dict = evaluate_model(model=model, X=X_new, y=y_new)
    mae = metrics_dict["mae"]

    params = dict(
        context="evaluate", # Package behavior
        training_set_size=DATA_SIZE,
        row_count=len(X_new)
    )

    save_results(params=params, metrics=metrics_dict)

    print("✅ evaluate() done \n")

    return mae


def pred(X_pred: pd.DataFrame ,df_clima_general: pd.DataFrame, df_historico: pd.DataFrame) -> np.ndarray:
    """
    Make a prediction using the latest trained model
    """

    print("\n⭐️ Use case: predict")

    """   if X_pred is None:

    ))
    """
    hospital = X_pred['hospital'].iloc[0]
    model = load_model(hospital)
    assert model is not None

    X_processed =preparar_y_preprocesar_x_futuro(X_pred, df_clima_general=df_clima_general, df_hospital_historico=df_historico)
    # data = {
    # "Dias Cama Ocupados": [150.0],
    # "Promedio Cama Disponibles": [9.0],
    # "Numero de Egresos": [17.0],
    # "Mes": [3.0],
    # "Trimestre": [1.0],
    # "lag_1": [252.0],
    # "lag_2": [279.0],
    # "lag_3": [279.0],
    # "media_movil_3": [270.0],
    # "porcentaje_ocupacion": [1666.666667],
    # "variacion_disponibles": [-0.47541],
    # "ocupados_media_movil": [98.672131],
    # "promedio_media_movil": [9.490246],
    # "egresos_media_movil": [13.745902],
    # "Temperatura Máxima": [22.858299],
    # "Temperatura Mínima": [17.603545],
    # "Precipitaciones (suma)": [0.258],
    # "Diferencia Térmica": [5.254754],
    # "temp_max_movil": [20.655452],
    # "precipitacion_movil": [1.473497],
    # "same_month_last_year": [0],
    # "hist_avg_mes": [294.5],
    # "interaccion_ocupacion_temp": [38097.164875],
    # "interaccion_precipitacion_disp": [2.322],
    # "Viento_SW": [0.254098],
    # "Viento_W": [0.745902],
    # "Viento_SE": [0.0],
    # "Viento_S": [0.0],
    # "Viento_NW": [0.0]
    # }
    # df = pd.DataFrame(data)
    expected_cols = ['Dias Cama Ocupados', 'Promedio Cama Disponibles', 'Numero de Egresos', 'Mes', 'Trimestre', 'lag_1', 'lag_2', 'lag_3', 'media_movil_3', 'porcentaje_ocupacion', 'variacion_disponibles', 'ocupados_media_movil', 'promedio_media_movil', 'egresos_media_movil', 'Temperatura Máxima', 'Temperatura Mínima', 'Precipitaciones (suma)', 'Diferencia Térmica', 'temp_max_movil', 'precipitacion_movil', 'same_month_last_year', 'hist_avg_mes', 'interaccion_ocupacion_temp', 'interaccion_precipitacion_disp', 'Viento_NW', 'Viento_S', 'Viento_SE', 'Viento_SW', 'Viento_W']
    X_processed = X_processed[expected_cols]
    y_pred = model.predict(X_processed)

    print("\n✅ prediction done: ", y_pred, y_pred.shape, "\n")
    return y_pred


if __name__ == '__main__':
    # preprocess(min_date='2009-01-01', max_date='2015-01-01')
    # train(min_date='2009-01-01', max_date='2015-01-01')
    # evaluate(min_date='2009-01-01', max_date='2015-01-01')
    pred()
