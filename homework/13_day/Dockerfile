# Собирать из корня проекта (там лежит data/):
#   docker build -f homework/13_day/Dockerfile -t churn-service .
FROM python:3.11-slim

WORKDIR /app

# зависимости отдельным слоем — он кешируется, пока requirements.txt не менялся
COPY homework/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# код сервиса и данные
COPY homework/13_day/ /app/
COPY data/churn_dataset.csv /app/data/churn_dataset.csv
ENV CHURN_DATA_PATH=/app/data/churn_dataset.csv

EXPOSE 8000
# --host 0.0.0.0: иначе сервер слушает только внутри контейнера и снаружи недоступен
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
