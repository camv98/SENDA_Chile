FROM python:3.10-slim

WORKDIR /app

COPY senda/requirements.txt /app/

RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt

COPY . /app

RUN pip list

CMD ["uvicorn", "senda.api:app", "--host", "0.0.0.0", "--port", "8080"]
