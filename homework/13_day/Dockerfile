FROM python:3.11-slim

WORKDIR /app
COPY homework/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY data/churn_dataset.csv data/churn_dataset.csv
COPY homework/13_day/*.py homework/13_day/

WORKDIR /app/homework/13_day
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
