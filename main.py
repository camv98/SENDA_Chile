import pandas as pd
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from senda.ml_logic import data
from senda.interface.main import pred
from datetime import datetime
import pytz


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/predict")
def predict(hospital: str, date: str):
    """
    Realiza una predicción para un hospital y una fecha.
    Se asume que 'date' está en formato "%Y-%m-%d %H:%M:%S" y que está en la zona horaria "US/Eastern".
    """
    date_obj = pd.to_datetime(date)

    data = pd.DataFrame({
        "date": [date_obj],
        "hospital": [str(hospital)],
    })

    y_pred = pred(data)

    return {"prediction": float(y_pred)}

@app.get("/")
def root():
    return {"greeting": "Hello"}
