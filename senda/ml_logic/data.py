import pandas as pd
from datetime import datetime
from google.cloud import bigquery
from colorama import Fore, Style
from pathlib import Path
from senda.params import *

def procesar_datasets_climaticos(seremi_data_dict: dict):
    def grados_a_cardinal(grados):
        if pd.isna(grados):
            return None
        direcciones = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']
        index = int((grados + 22.5) % 360 // 45)
        return direcciones[index]

    for año, df in seremi_data_dict.items():
        # Eliminar columna innecesaria
        if "Unnamed: 0" in df.columns:
            df = df.drop(columns=["Unnamed: 0"])

        # Crear columna cardinal
        if "winddirection_10m_dominant" in df.columns:
            df["wind_direction_cardinal"] = df["winddirection_10m_dominant"].apply(grados_a_cardinal)

        # Renombrar columnas
        df = df.rename(columns={
            "temperature_2m_max": "Temperatura Máxima",
            "temperature_2m_min": "Temperatura Mínima",
            "precipitation_sum": "Precipitaciones (suma)",
            "winddirection_10m_dominant": "Dirección Viento"
        })

        # Limpiar columna de grados si existe y renombrar cardinal
        if "Dirección Viento" in df.columns:
            df = df.drop(columns=["Dirección Viento"])
        if "wind_direction_cardinal" in df.columns:
            df = df.rename(columns={"wind_direction_cardinal": "Dirección del Viento"})

        # Guardar el dataframe procesado
        seremi_data_dict[año] = df

    return seremi_data_dict

def procesar_datasets_hospitales(hospitales_dic: dict):

    filtrado_limpio = {}
    # Abreviaturas de los meses
    meses_abreviados = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun',
                        'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']

    # Columnas que se eliminarán si existen
    columnas_a_eliminar = ["Cód. SS/SEREMI", "Cód. Estab.", "Cód. Nivel Cuidado", "Acum", "Año"]
    for año, archivo in hospitales_dic.items():
    # Cargar CSV
        df = pd.read_csv(archivo)
        # Eliminar filas irrelevantes
        df = df[~df["Nombre Nivel Cuidado"].isin([
        "330 - Area Pensionado",
        "330 - Área Pensionado",
        "401 - Área Médica Adulto Cuidados Básicos",
        "402 - Área Médica Adulto Cuidados Medios",
        "403 - Área Médico-Quirúrgico Cuidados Básicos",
        "404 - Área Médico-Quirúrgico Cuidados Medios",
        "405 - Área Cuidados Intensivos Adultos",
        "406 - Área Cuidados Intermedios Adultos",
        "407 - Área Médica Pediátrica Cuidados Básicos",
        "408 - Área Médica Pediátrica Cuidados Medios",
        "409 - Área Médico-Quirúrgico Pediátrica Cuidados Básicos",
        "410 - Área Médico-Quirúrgico Pediátrica Cuidados Medios",
        "411 - Área Cuidados Intensivos Pediátricos",
        "412 - Área Cuidados Intermedios Pediátricos",
        "413 - Área Neonatología Cuidados Básicos",
        "414 - Área Neonatología Cuidados Intensivos",
        "415 - Área Neonatología Cuidados Intermedios",
        "416 - Área Obstetricia",
        "418 - Área Psiquiatría Adulto Corta estadía",
        "419 - Área Psiquiatría Adulto Mediana estadía",
        "420 - Área Psiquiatría Adulto Larga estadía",
        "421 - Área Psiquiatría Infanto-adolescente corta estadía",
        "427 - Área Sociosanitaria Adulto",
        "428 - Área de Hospitalización de Cuidados Intensivos en Psiquiatría Adulto",
        "429 - Área de Hospitalización de Cuidados Intensivos en Psiquiatría Infanto Adolescente",
        "Área Cuidados Intensivos Adultos",
        "Área Cuidados Intensivos Pediátricos",
        "Área Cuidados Intermedios Adultos",
        "Área Cuidados Intermedios Pediátricos",
        "Área Médica Adulto Cuidados Básicos",
        "Área Médica Adulto Cuidados Medios",
        "Área Médica Pediátrica Cuidados Básicos",
        "Área Médica Pediátrica Cuidados Medios",
        "Área Médico-Quirúrgico Cuidados Básicos",
        "Área Médico-Quirúrgico Cuidados Medios",
        "Área Médico-Quirúrgico Pediátrica Cuidados Básicos",
        "Área Médico-Quirúrgico Pediátrica Cuidados Medios",
        "Área Neonatología Cuidados Básicos",
        "Área Neonatología Cuidados Intensivos",
        "Área Neonatología Cuidados Intermedios",
        "Área Obstetricia",
        "Área Pensionado",
        "Área Psiquiatría Adulto Corta estadía",
        "Área Psiquiatría Adulto Larga estadía",
        "Área Psiquiatría Adulto Mediana estadía",
        "Área Psiquiatría Infanto-adolescente corta estadía"
        ]
        )].copy()

        # Eliminar columnas innecesarias
        df = df.drop(columns=columnas_a_eliminar, errors='ignore')

        # Renombrar columnas clave
        df = df.rename(columns={
            "Nombre SS/SEREMI": "SEREMI",
            "Nombre Nivel Cuidado": "Area"
        })

        # Renombrar columnas de meses abreviados por fecha
        nuevo_nombre_columnas = {}
        año_int = int(año)

        for i, mes_abrev in enumerate(meses_abreviados, start=1):
            if mes_abrev in df.columns:
                fecha = datetime(año_int, i, 1).strftime('%Y-%m-%d')
                nuevo_nombre_columnas[mes_abrev] = fecha

        df = df.rename(columns=nuevo_nombre_columnas)

        # Guardar DataFrame limpio
        filtrado_limpio[año] = df

    return filtrado_limpio



def extraer_info_hospital_area_todo_el_año(hospital_nombre, filtrado_limpio, seremi_data):
    registros = []

    for año, df in filtrado_limpio.items():
        df_seremi = seremi_data[año].copy()

        df_seremi['Mes'] = pd.to_datetime(df_seremi['Mes'], errors='coerce')
        df_seremi.dropna(subset=['Mes'], inplace=True)
        df_seremi['Mes'] = df_seremi['Mes'].dt.to_period("M").dt.to_timestamp()

        columnas_mes = [col for col in df.columns if col.startswith("20")]
        for col in columnas_mes:
            df_tmp = df[
                (df["Nombre Establecimiento"] == hospital_nombre) &
                (df["Area"] == "Datos Establecimiento")
            ][["SEREMI", "Nombre Establecimiento", "Area", "Glosa", col]].copy()

            if df_tmp.empty:
                continue

            df_tmp = df_tmp.rename(columns={col: "Valor"})
            df_tmp["Fecha"] = pd.to_datetime(col)

            clima_mes = df_seremi[df_seremi["Mes"] == df_tmp["Fecha"].iloc[0]].copy()
            df_merge = df_tmp.merge(clima_mes, on=["SEREMI"], how="left")

            registros.append(df_merge)

    if registros:
        return pd.concat(registros, ignore_index=True).sort_values("Fecha")
    else:
        print("⚠️ No se encontraron datos para ese hospital y área.")
        return pd.DataFrame()


def descargar_de_bigquery(query, destino_pandas=True):
    """
    Ejecuta una consulta y devuelve los resultados
    Args:
        query (str): Consulta SQL válida
        destino_pandas (bool): Si True retorna DataFrame, si False guarda en CSV
    """
    job = client.query(query)

    if destino_pandas:
        return job.to_dataframe()  # Para datasets pequeños/medianos
    else:
        # Para datasets grandes (exporta a GCS primero)
        destination_uri = "gs://tu-bucket/temp_data.csv"
        extract_job = client.extract_table(
            job.destination,
            destination_uri,
            location="US",
            job_config=bigquery.job.ExtractJobConfig(
                field_delimiter=",",
                print_header=True
            )
        )
        extract_job.result()
        return pd.read_csv(destination_uri)
