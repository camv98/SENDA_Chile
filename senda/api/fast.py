import pandas as pd
from fastapi import FastAPI, HTTPException
from senda.ml_logic import data
from senda.interface.main import pred
from datetime import datetime
import os
from google.cloud import storage
import pytz
from senda.params import *
import io
app = FastAPI()

# Allowing all middleware is optional, but good practice for dev purposes
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],  # Allows all origins
#     allow_credentials=True,
#     allow_methods=["*"],  # Allows all methods
#     allow_headers=["*"],  # Allows all headers
# )

df_clima_general = None
df_historico = None

@app.on_event("startup")
async def startup_event():
    """
    Carga los datasets desde GCS al inicio de la aplicación.
    """
    global df_clima_general, df_historico

    client = storage.Client()
    bucket = client.bucket(BUCKET_DATOS)

    # Cargar df_clima_general
    blob_clima = bucket.blob(CLIMA_CSV_PATH)
    try:
        data_clima = blob_clima.download_as_string()
        df_clima_general = pd.read_csv(io.StringIO(data_clima.decode("utf-8")))
        print("✅ Datos de clima cargados desde GCS")
    except Exception as e:
        print(f"Error al cargar datos de clima desde GCS: {e}")
        df_clima_general = None




@app.get("/predict")
def predict(
        hospital: str,
        date: str,
        SEREMI: str

    ):      # 1
    global df_clima_general, df_historico # Aseguramos el acceso a las variables globales.
    # Cargar df_historico
    client = storage.Client()
    bucket = client.bucket(BUCKET_DATOS)
    blob_path = f"{HISTORICO_CSV_PATH}{hospital}_df_extr.csv"
    blob_historico = bucket.blob(blob_path)
    try:
        data_historico = blob_historico.download_as_string()
        df_historico = pd.read_csv(io.StringIO(data_historico.decode("utf-8")))
        print("✅ Datos históricos cargados desde GCS")
    except Exception as e:
        print(f"Error al cargar datos históricos desde GCS: {e}")
        df_historico = None
    try:
        data = pd.DataFrame({ "fecha": pd.to_datetime(date), "hospital": [hospital], "SEREMI": [SEREMI], })
        y_pred = pred(data, df_clima_general, df_historico)
        return {"prediction": float(y_pred[0])}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@app.get("/")
def root():
    return {"greeting": "Hello"}
