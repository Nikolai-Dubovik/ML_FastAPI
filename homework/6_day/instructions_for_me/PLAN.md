# 📝 День 6 — Сохранение и загрузка churn-модели (план решения)

## 🎯 Цель
Сделать модель персистентной: после обучения сохранять pipeline на диск
(joblib), при старте приложения загружать его обратно, а текущее состояние
показывать через новый эндпоинт `GET /model/status`. Обученная модель
больше не теряется при перезапуске сервиса.

Продолжаем приложение дней 1–5 (все прежние эндпоинты остаются).

---

## 📂 Структура `homework/6_day/`

```
homework/6_day/
├── main.py                  # FastAPI + GET /model/status, загрузка при старте
├── models.py                # Pydantic-модели (без изменений)
├── dataset.py               # ChurnDataset (без изменений)
├── preprocessing.py         # типы признаков, split (без изменений)
├── model.py                 # pipeline и обучение (без изменений)
├── storage.py               # НОВЫЙ модуль: save/load модели через joblib
├── models/                  # каталог артефактов (создаётся при сохранении)
│   └── churn_model.joblib   # сохранённая модель (в .gitignore!)
└── instructions_for_me/
    ├── PLAN.md
    ├── README.md
    └── TECHNOLOGIES.md
```

**Новая зависимость — joblib**, но ставить отдельно не нужно: он уже
установлен как зависимость scikit-learn. Для честности стоит дописать
`joblib` в `homework/requirements.txt`.

---

## ⚙️ Как будет работать решение

### Модуль `storage.py`

Путь к файлу модели:
```python
MODEL_PATH = Path(__file__).resolve().parent / "models" / "churn_model.joblib"
```

Сохраняем не голый pipeline, а **bundle-словарь** — чтобы вместе с моделью
на диске жили время обучения и метрики (они нужны для `/model/status`):

```python
bundle = {
    "pipeline": pipeline,
    "trained_at": datetime.now(timezone.utc).isoformat(),
    "metrics": metrics,          # accuracy, f1 с тестовой выборки
}
```

Функции:
- `save_churn_model(pipeline, metrics, path=MODEL_PATH)` — создаёт каталог
  (`path.parent.mkdir(parents=True, exist_ok=True)`), собирает bundle,
  `joblib.dump(bundle, path)`, возвращает bundle;
- `load_churn_model(path=MODEL_PATH)` — если файла нет → `None`, иначе
  `joblib.load(path)` → bundle.

### Изменения в `main.py`
- **При старте приложения** (на уровне модуля, как `dataset = ChurnDataset()`):
  ```python
  model_state: dict | None = load_churn_model()
  ```
  Файла нет → сервис спокойно стартует без модели (`model_state is None`).
- **`POST /model/train`** — после успешного обучения вызывает
  `save_churn_model(...)` и кладёт свежий bundle в `model_state`
  (не забыть `global model_state` внутри функции).
- **`GET /model/status`** — новый эндпоинт:
  ```json
  {"is_trained": true, "trained_at": "2026-07-09T...", "metrics": {...}}
  ```
  Если модели нет: `{"is_trained": false, "trained_at": null, "metrics": null}`.

---

## 🪜 Пошаговый план реализации

1. Скопировать файлы дня 5 в `homework/6_day/`.
2. Создать `storage.py`: `MODEL_PATH`, `save_churn_model`, `load_churn_model`.
3. В `main.py`: загрузка bundle при старте, сохранение в `/model/train`,
   эндпоинт `GET /model/status`.
4. Добавить `homework/6_day/models/` (или `*.joblib`) в `.gitignore`,
   дописать `joblib` в `requirements.txt`.
5. Проверить цикл персистентности: train → status → рестарт → status.

---

## ✅ Критерии готовности (Definition of Done)

- [ ] `save_churn_model` / `load_churn_model` работают через joblib;
- [ ] после успешного `POST /model/train` появляется файл
      `models/churn_model.joblib`;
- [ ] при старте приложение подхватывает модель из файла (если он есть);
- [ ] `GET /model/status` показывает: обучена ли модель, когда обучена
      (`trained_at`), метрики на тестовой выборке;
- [ ] до первого обучения статус честно отдаёт `is_trained: false`
      (и сервис не падает);
- [ ] **после перезапуска uvicorn** `/model/status` показывает обученную
      модель без повторного обучения;
- [ ] эндпоинты прошлых дней работают.

---

## 🧪 Чем проверять
Ключевой сценарий — цикл персистентности:
1. удалить `models/churn_model.joblib` (если есть) → запустить сервер →
   `GET /model/status` → `is_trained: false`;
2. `POST /model/train` → метрики (accuracy ≈ 0.7875, f1 ≈ 0.045), файл
   появился на диске;
3. `GET /model/status` → `is_trained: true`, время, метрики;
4. **остановить сервер (Ctrl+C) и запустить снова** →
   `GET /model/status` → модель на месте, `trained_at` — прежний.

---

## ⚠️ Возможные подводные камни

- **`models/` рядом с `models.py`** — не путать: `models.py` — модуль с
  Pydantic-классами, `models/` — каталог артефактов на диске. Питоновским
  импортам каталог не мешает (импортируется файл `models.py`), но читать
  код стоит внимательно.
- **Каталога может не быть** → перед `joblib.dump` обязательно
  `mkdir(parents=True, exist_ok=True)`, иначе `FileNotFoundError`.
- **`global model_state`** — присваивание глобальной переменной внутри
  функции эндпоинта без `global` создаст локальную переменную, и статус
  «не увидит» свежеобученную модель до рестарта.
- **Файл модели — не для git**: бинарный артефакт, генерируется заново;
  добавить в `.gitignore`.
- **Совместимость версий**: joblib/pickle не гарантируют загрузку модели,
  сохранённой другой версией scikit-learn, — модель и сервис должны жить
  в одном окружении (наш общий `.venv` это обеспечивает).
- **`--reload` и обучение**: uvicorn в режиме reload перезапускает процесс
  при изменении файлов кода — удобно для проверки пункта «модель
  переживает рестарт», но не редактируйте код между train и проверкой,
  чтобы не запутаться, какой рестарт что вызвал.

---

## 🔮 Что дальше (день 7)
Модель обучена и переживает перезапуски — пора ей пользоваться: в дне 7
`POST /predict` начнёт возвращать настоящие предсказания класса и
вероятности через `predict_proba`, появится модель ответа
`PredictionResponseChurn`.
