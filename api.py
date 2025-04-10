from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import pandas as pd
import numpy as np
from typing import Dict


from modelo_def import procesar_seremi_y_predecir,preparar_datos_para_modelo

df_2024_csv = pd.read_excel("/home/bren/code/camv98/SENDA_Chile/Consolidado Estadísticas Hospitalarias 2021.xlsx", skiprows=2)

class PredictionRequest(BaseModel):
    seremi: str
    mes: str

class PredictionResponse(BaseModel):
    seremi: str
    mes: str
    prediccion: float
    confianza: float
    factores: Dict[str, float]
    timestamp: str

app = FastAPI(title="API de Predicción Hospitalaria",
              description="API para predecir ocupación hospitalaria")

# Allowing all middleware is optional, but good practice for dev purposes
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

#app.state.model

#@app.post("/predict")
@app.post("/predict", response_model=PredictionResponse)
async def predict(request: PredictionRequest):
    """
    Endpoint principal para obtener predicciones de ocupación hospitalaria

    Args:
        request: PredictionRequest con seremi y mes
    Returns:
        PredictionResponse con los resultados de la predicción
    """
    #X_pred = pd.DataFrame(locals(), index=[0])
    #model = app.state.model
    #assert model is not None

    #y_pred = model.predict(X_pred)
    #return dict(fare=float(y_pred))

    resultados = procesar_seremi_y_predecir(df_2024_csv, request.seremi, preparar_datos_para_modelo)
    return resultados

@app.get('/')
def index():
    return {'message': 'API de Predicción Hospitalaria operativa'}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
