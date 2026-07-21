# 📝 День 1 — Базовое приложение FastAPI

Минимальный сервис FastAPI с одним эндпоинтом `GET /`, который возвращает
`{"message": "ml churn service is running"}`.

## ⚙️ Установка

Из корня проекта `ML_FastAPI`:

```bash
python3 -m venv .venv          # создать виртуальное окружение (один раз)
source .venv/bin/activate      # активировать (macOS/Linux)
pip install -r homework/1_day/requirements.txt
```

## ▶️ Запуск

Из папки `homework/1_day/`:

```bash
cd homework/1_day
uvicorn main:app --reload
```

Сервер поднимется на `http://127.0.0.1:8000`.
Если порт занят: `uvicorn main:app --reload --port 8001`.

## 🔍 Проверка

- Браузер: открыть `http://127.0.0.1:8000/`
- Swagger UI: `http://127.0.0.1:8000/docs`
- Консоль:
  ```bash
  curl http://127.0.0.1:8000/
  # {"message":"ml churn service is running"}
  ```