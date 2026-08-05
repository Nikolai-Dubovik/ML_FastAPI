FROM python:3.11-slim

WORKDIR /app
COPY homework/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY data/churn_dataset.csv data/churn_dataset.csv
COPY homework/14_day/app homework/14_day/app

WORKDIR /app/homework/14_day
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
