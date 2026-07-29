def test_train_status_predict_cycle(client, features):
    """Полный сценарий: обучили на churn_dataset.csv → проверили статус → предсказали."""
    train = client.post("/model/train", json={"model_type": "logreg"})
    assert train.status_code == 200
    metrics = train.json()["metrics"]
    assert {"accuracy", "f1", "roc_auc"} <= set(metrics)

    status = client.get("/model/status")
    assert status.status_code == 200
    assert status.json()["is_trained"] is True
    assert status.json()["model_type"] == "logreg"

    # история пополнилась записью об этом обучении
    assert client.get("/model/metrics").json()["last"]["model_type"] == "logreg"

    predict = client.post("/predict", json=features)
    assert predict.status_code == 200
    body = predict.json()
    assert body["prediction"] in (0, 1)
    assert set(body["probabilities"]) == {"0", "1"}


def test_predict_without_model(client, features):
    response = client.post("/predict", json=features)

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "model_not_trained"


def test_predict_with_invalid_type(client, features):
    response = client.post("/predict", json={**features, "monthly_fee": "abc"})

    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == "validation_error"
    assert error["details"]["errors"][0]["field"] == "monthly_fee"
