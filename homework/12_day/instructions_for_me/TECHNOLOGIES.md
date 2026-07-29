# 🧰 Новые технологии дня 12 — pytest и TestClient

День 12 не добавляет функциональность — он добавляет **уверенность**. Новые
инструменты: `pytest` (фреймворк тестирования), `TestClient` (запросы к
FastAPI без реального сервера) и приёмы изоляции тестов.

---

## 🧪 pytest — как он находит и запускает тесты

`pytest` автоматически собирает тесты по соглашению об именах:
- файлы `test_*.py`, функции `test_*`;
- проверка — обычный `assert`, без специальных методов:
```python
def test_split_sizes(sample_df):
    X_train, X_test, y_train, y_test = split_train_test(sample_df)
    assert len(X_train) + len(X_test) == len(sample_df)
```
Если `assert` падает, pytest сам покажет, какие значения не совпали. Запуск —
команда `pytest` из папки дня; `-q` короче, `-v` подробнее, `-k "подстрока"`
фильтрует по имени.

**`pytest.ini`** настраивает проект. Нам важны две строки:
```ini
[pytest]
pythonpath = .      # добавить корень дня в путь → import main работает
testpaths = tests   # где искать тесты
```
Без `pythonpath` тесты не найдут плоские модули (`main`, `model`) — типичная
первая ошибка.

---

## 🧩 Фикстуры и conftest.py

**Фикстура** — переиспользуемая заготовка данных/объектов для тестов. Объявляем
через `@pytest.fixture`, а тест просто просит её по имени в аргументе:
```python
@pytest.fixture
def client():
    return TestClient(app)

def test_root(client):        # client придёт из фикстуры
    assert client.get("/").status_code == 200
```
Файл **`conftest.py`** — общие фикстуры для всех тестов рядом; его не надо
импортировать, pytest подхватывает сам.

---

## 🌐 TestClient — API без запуска сервера

`TestClient` шлёт запросы к приложению **в том же процессе**, без uvicorn и
сети — быстро и удобно для тестов:
```python
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)
r = client.post("/model/train", json={"model_type": "logreg"})
assert r.status_code == 200
assert "roc_auc" in r.json()["metrics"]
```
Под капотом он использует **httpx** (поэтому это новая зависимость). Интерфейс
как у обычного HTTP-клиента: `client.get/post(...)`, `r.status_code`,
`r.json()`. Так один тест проходит весь цикл: train → status → predict.

---

## 🔒 Изоляция: tmp_path и monkeypatch

Тесты должны быть **независимыми** и не портить реальные данные. Две встроенные
фикстуры pytest:
- **`tmp_path`** — уникальная временная папка на каждый тест;
- **`monkeypatch`** — временно подменить атрибут/переменную, автоматически
  вернуть назад после теста.

```python
@pytest.fixture(autouse=True)
def isolate(tmp_path, monkeypatch):
    import storage, history, main
    monkeypatch.setattr(storage, "MODEL_PATH", tmp_path / "model.joblib")
    monkeypatch.setattr(history, "HISTORY_PATH", tmp_path / "history.json")
    monkeypatch.setattr(main, "model_state", None)   # старт «модель не обучена»
```
`autouse=True` — фикстура применяется к каждому тесту сама. Зачем это нужно:
`main` грузит модель при импорте, а `/model/train` пишет файлы. Без
перенаправления в `tmp_path` тесты затирали бы настоящие
`churn_model.joblib`/`training_history.json` и зависели бы от порядка запуска.
Сброс `model_state = None` даёт честный тест «predict без обучения → 409».

---

## 🎲 Воспроизводимость: синтетические данные

Тест не должен зависеть от большого CSV и «плавающих» чисел. Делаем маленький
**синтетический** DataFrame с обоими классами:
```python
@pytest.fixture
def sample_df():
    n = 40
    return pd.DataFrame({
        "monthly_fee": [9.99, 19.99] * (n // 2),
        ...,
        "region": ["europe", "asia"] * (n // 2),
        "churn": [0, 0, 0, 1] * (n // 4),   # оба класса, ~25% единиц
    })
```
Он быстрый и одинаковый при каждом прогоне. Важно: классов должно быть по
≥2 примера, иначе `train_test_split(stratify=y)` не сможет разложить их в обе
выборки. Сами метрики проверяем **диапазоном** `0 ≤ m ≤ 1`, а не точным
значением — оно зависит от данных фикстуры.

---

## 🧭 Юнит vs интеграция

Два уровня тестов дополняют друг друга:

| Уровень | Что проверяет | Скорость | Пример |
|---|---|---|---|
| **юнит** | одна функция в изоляции | очень быстро | `split_train_test`, `train_churn_model` |
| **интеграция** | эндпоинты вместе через API | быстро | цикл train→status→predict, 409/422 |

Юнит ловит ошибку близко к причине; интеграция проверяет, что части
собираются в рабочий сервис. Обработку ошибок дня 10 (`409 model_not_trained`,
`422 validation_error`) удобнее всего проверять именно интеграционно — через
реальный ответ API.

---

## 📦 Итог: что нового по сравнению с днём 11

| Технология / приём | Зачем |
|--------------------|-------|
| **pytest** | автозапуск тестов по соглашению, `assert` |
| **pytest.ini (`pythonpath`)** | тесты видят модули приложения |
| **фикстуры / conftest.py** | переиспользуемые данные и объекты |
| **TestClient (+httpx)** | запросы к API без запуска сервера |
| **tmp_path / monkeypatch** | изоляция: не портить реальные артефакты |
| **синтетические данные + seed** | воспроизводимые, быстрые тесты |
| **юнит + интеграция** | ошибка ловится и точечно, и на уровне API |
