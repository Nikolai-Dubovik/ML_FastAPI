CUSTOMER = {
    "monthly_fee": 9.99,
    "usage_hours": 30.0,
    "support_requests": 0,
    "account_age_months": 36,
    "failed_payments": 0,
    "region": "europe",
    "device_type": "desktop",
    "payment_method": "card",
    "autopay_enabled": 1,
}


def test_predict_without_model(client):
    """Предсказание до обучения — 409 model_not_trained."""
    response = client.post("/predict", json=CUSTOMER)
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "model_not_trained"


def test_train_status_predict_cycle(client):
    """Полный сценарий: датасет → обучение → статус → предсказание."""
    assert client.get("/dataset/info").json()["n_rows"] == 2000

    metrics = client.post("/model/train", json={"model_type": "logreg"}).json()["metrics"]
    assert 0.0 <= metrics["roc_auc"] <= 1.0

    assert client.get("/model/status").json()["is_trained"] is True

    prediction = client.post("/predict", json=CUSTOMER).json()
    assert prediction["prediction"] in (0, 1)
    assert round(sum(prediction["probabilities"].values()), 4) == 1.0


def test_validation_error(client):
    response = client.post("/predict", json={**CUSTOMER, "monthly_fee": "дорого"})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


def test_metrics_history(client):
    client.post("/model/train", json={"model_type": "logreg"})
    client.post("/model/train", json={"model_type": "random_forest"})
    assert len(client.get("/model/metrics").json()["history"]) == 2
    assert len(client.get("/model/metrics", params={"model_type": "logreg"}).json()["history"]) == 1
