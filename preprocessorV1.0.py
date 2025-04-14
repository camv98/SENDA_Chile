class ClimaPreprocessor:
    def __init__(self):
        # El constructor __init__ permite definir parámetros de la instancia.
        # es mejor tenerlo para facilitar futuras extensiones.
        pass

    def transform(self, x_new, df_hist):
        """
        x_new: dict con claves: 'Temperatura Máxima', 'Temperatura Mínima', 'Precipitaciones (suma)', 'mes'
        df_hist: DataFrame histórico del hospital (ya transformado con preparar_dataset_climatico_avanzado)
        """

        if df_hist is None or df_hist.empty:
            raise ValueError("❌ El historial del hospital no puede estar vacío")

        # Aseguramos que tenga las columnas necesarias
        required_cols = ['Fecha', 'Dias Cama Disponibles', 'Mes']
        for col in required_cols:
            if col not in df_hist.columns:
                raise ValueError(f"❌ Falta la columna requerida en el historial: {col}")

        # Ordenamos por fecha
        df_hist = df_hist.sort_values('Fecha')

        # Extraemos la última fila válida para calcular referencias
        last_row = df_hist.iloc[-1]

        # Calculamos valores derivados a partir de x_new y df_hist
        temp_max = x_new['Temperatura Máxima']
        temp_min = x_new['Temperatura Mínima']
        precipitacion = x_new['Precipitaciones (suma)']
        mes = x_new['mes']

        diferencia_termica = temp_max - temp_min

        # Mismo mes del año pasado
        same_month_last_year = df_hist[df_hist['Mes'] == mes].iloc[-12:]['Dias Cama Disponibles'].mean()

        # Promedio histórico del mes
        hist_avg_mes = df_hist[df_hist['Mes'] == mes]['Dias Cama Disponibles'].mean()

        X_processed = pd.DataFrame([{
            'Mes': mes,
            'Trimestre': (mes - 1) // 3 + 1,
            'Temperatura Máxima': temp_max,
            'Temperatura Mínima': temp_min,
            'Precipitaciones (suma)': precipitacion,
            'Diferencia Térmica': diferencia_termica,
            'same_month_last_year': same_month_last_year,
            'hist_avg_mes': hist_avg_mes
        }])

        return X_processed

# Como ingresaria masomenos la data obviamente ya agarrando directo de la api del clima
# x_new = {
#     'Temperatura Máxima': 28.5,
#     'Temperatura Mínima': 15.2,
#     'Precipitaciones (suma)': 12.3,
#     'mes': 4
# }

# preproc = ClimaPreprocessor()
# X_final = preproc.transform(x_nuevo, df_hospital)
