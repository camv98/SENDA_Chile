import pandas as pd
from fastapi import FastAPI
from senda.ml_logic import data
from senda.interface.main import pred 
from datetime import datetime
import os
from google.cloud import storage
import pytz
app = FastAPI()

# Allowing all middleware is optional, but good practice for dev purposes
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

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
        df_clima_general = pd.read_csv(pd.compat.StringIO(data_clima.decode("utf-8")))
        print("✅ Datos de clima cargados desde GCS")
    except Exception as e:
        print(f"Error al cargar datos de clima desde GCS: {e}")
        df_clima_general = None

    # Cargar df_historico
    blob_historico = bucket.blob(HISTORICO_CSV_PATH)
    try:
        data_historico = blob_historico.download_as_string()
        df_historico = pd.read_csv(pd.compat.StringIO(data_historico.decode("utf-8")))
        print("✅ Datos históricos cargados desde GCS")
    except Exception as e:
        print(f"Error al cargar datos históricos desde GCS: {e}")
        df_historico = None
        
@app.get("/predict")
def predict(
        hospital: str,  
        date: str,
        SEREMI: str  

    ):      # 1
    global df_clima_general, df_historico # Aseguramos el acceso a las variables globales.

    data = pd.DataFrame({
        "fecha": pd.to_datetime(date),
        "hospital": [hospital],
        "SEREMI": [SEREMI],
    })
    y_pred = pred(data, df_clima_general, df_historico) # Pasamos los dataframes como argumentos.

    return {"bead": float(y_pred)}
    

@app.get("/")
def root():
    return {"greeting": "Hello"}