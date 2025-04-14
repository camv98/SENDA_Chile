import pandas as pd
from fastapi import FastAPI
from senda.ml_logic import data
from senda.interface.main import pred 
from datetime import datetime
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
    Carga los datasets al inicio de la aplicación.
    """
    global df_clima_general, df_historico
    df_clima_general = pd.read_csv("predicciones_seremis_con_marzo.csv") # Asegúrate de que la ruta sea correcta
    df_historico = pd.read_csv("historico_camas_hospitales.csv") # Asegúrate de que la ruta sea correcta

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