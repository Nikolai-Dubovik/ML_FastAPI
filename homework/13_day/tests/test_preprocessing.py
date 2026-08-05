from models import FeatureVectorChurn
from preprocessing import FEATURE_COLUMNS, feature_schema, features_to_dataframe, split_train_test


def test_split_train_test_shapes(synthetic_df):
    X_train, X_test, _, _ = split_train_test(synthetic_df)
    assert len(X_train) == 160
    assert len(X_test) == 40
    assert len(X_train) + len(X_test) == len(synthetic_df)


def test_split_preserves_class_ratio(synthetic_df):
    """Стратификация: доля оттока в частях совпадает с исходной."""
    _, _, y_train, y_test = split_train_test(synthetic_df)
    ratio = synthetic_df["churn"].mean()
    assert abs(y_train.mean() - ratio) < 0.05
    assert abs(y_test.mean() - ratio) < 0.05


def test_features_to_dataframe_column_order(synthetic_df):
    rows = synthetic_df.drop(columns=["churn"]).head(1).to_dict(orient="records")
    X = features_to_dataframe([FeatureVectorChurn(**row) for row in rows])
    assert list(X.columns) == FEATURE_COLUMNS


def test_feature_schema(synthetic_df):
    schema = feature_schema(synthetic_df)
    roles = {f["name"]: f["role"] for f in schema["features"]}
    assert len(roles) == 9
    assert roles["monthly_fee"] == "numeric"
    assert roles["region"] == "categorical"
    assert schema["target"] == "churn"
