import os
import numpy as np

################## VARIABLES ##################

GCP_PROJECT = os.environ.get("GCP_PROJECT")
GCP_PROJECT_WAGON = os.environ.get("GCP_PROJECT_WAGON")
GCP_REGION = os.environ.get("GCP_REGION")
BQ_DATASET = os.environ.get("BQ_DATASET")
BQ_REGION = os.environ.get("BQ_REGION")
BUCKET_NAME = os.environ.get("BUCKET_NAME")
INSTANCE = os.environ.get("INSTANCE")
PREFECT_LOG_LEVEL = os.environ.get("PREFECT_LOG_LEVEL")
EVALUATION_START_DATE = os.environ.get("EVALUATION_START_DATE")
GAR_IMAGE = os.environ.get("GAR_IMAGE")
GAR_MEMORY = os.environ.get("GAR_MEMORY")
BUCKET_DATOS = os.environ.get("BUCKET_DATOS")
BUCKET_MODELOS = os.environ.get("BUCKET_MODELOS")
CLIMA_CSV_PATH = os.environ.get("CLIMA_CSV_PATH")
MODEL_BASE_NAME = os.environ.get("MODEL_BASE_NAME")
MODEL_FOLDER = os.environ.get("MODEL_FOLDER")
HISTORICO_CSV_PATH = os.environ.get("HISTORICO_CSV_PATH")


################## CONSTANTS #####################
LOCAL_DATA_PATH = os.path.join(os.path.expanduser('~'), ".lewagon", "mlops", "data")
LOCAL_REGISTRY_PATH = os.path.join(os.path.expanduser('~'), ".lewagon", "mlops", "training_outputs")
DTYPES_PROCESSED = np.float32

################## VALIDATIONS #################


def validate_env_value(env, valid_options):
    env_value = os.environ[env]
    if env_value not in valid_options:
        raise NameError(f"Invalid value for {env} in `.env` file: {env_value} must be in {valid_options}")

# for env, valid_options in env_valid_options.items():
#     validate_env_value(env, valid_options)
