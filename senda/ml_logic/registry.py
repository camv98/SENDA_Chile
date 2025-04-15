import glob
import os
import time
import pickle
from colorama import Fore, Style
# from tensorflow import keras
from google.cloud import storage
from xgboost import XGBRegressor
from senda.params import *

# from mlflow.tracking import MlflowClient

def save_results(params: dict, metrics: dict) -> None:


    print("✅ Results saved locally")


def save_model(model) -> None:
    """
"""
    return None


def load_model(hospital:str):
    """
    Load the latest saved model from GCS.
    """
    if BUCKET_MODELOS is None:
        print("Warning: BUCKET_MODELOS environment variable not set. Loading model from local file.")
        try:
            with open(hospital, "rb") as file:
                model = pickle.load(file)
            return model
        except FileNotFoundError:
            print("Error: Model file not found locally.")
            return None

    client = storage.Client()
    bucket = client.bucket(BUCKET_MODELOS)

    model_name = f"{hospital}_modelo_xgb_nativo.ubj"
    # model_name = "Hospital San Juan de Dios (La Serena)_modelo_xgb_nativo.ubj"

    if MODEL_FOLDER:
        blob_path = f"{MODEL_FOLDER}{model_name}"
    else:
        blob_path = model_name
    blob = bucket.blob(blob_path)

    try:
        blob.download_to_filename("Hospital San Juan de Dios (La Serena)_modelo_xgb_nativo.ubj")
        model = XGBRegressor()
        model.load_model(model_name)
        # model = pickle.loads("Hospital San Juan de Dios (La Serena)_modelo_xgb_nativo.ubj")
        print("✅ Model loaded from GCS")
        return model
    except Exception as e:
        print(f"Error loading model from GCS: {e}")
        return None

def descargar_modelo(hospital):
    """Descarga el modelo correspondiente al hospital desde GCS."""
    client = storage.Client()
    bucket = client.bucket(BUCKET_MODELOS)

    # Construir el nombre del modelo
    model_name = f"{hospital}.ubj"

    # Construir la ruta del modelo
    if MODEL_FOLDER:
        blob_path = f"{MODEL_FOLDER}/{model_name}"
    else:
        blob_path = model_name

    blob = bucket.blob(blob_path)
    blob.download_to_filename(model_name)
    return model_name
