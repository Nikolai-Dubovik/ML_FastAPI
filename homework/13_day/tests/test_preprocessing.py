from models import FeatureVectorChurn
from preprocessing import (
    CATEGORICAL_FEATURES,
    FEATURE_COLUMNS,
    NUMERIC_FEATURES,
    TARGET_COLUMN,
    feature_schema,
    features_to_dataframe,
    split_train_test,
)


def test_split_train_test_sizes_and_classes(sample_df):
    X_train, X_test, y_train, y_test = split_train_test(sample_df, test_size=0.25)

    assert len(X_train) + len(X_test) == len(sample_df)
    assert len(X_test) == len(sample_df) // 4
    assert list(X_train.columns) == FEATURE_COLUMNS
    # стратификация: оба класса должны попасть и в train, и в test
    assert set(y_train.unique()) == {0, 1}
    assert set(y_test.unique()) == {0, 1}


def test_features_to_dataframe_keeps_column_order(features):
    # порядок колонок задан один раз в FEATURE_COLUMNS — обучение и предсказание должны совпадать
    shuffled = {key: features[key] for key in reversed(list(features))}
    df = features_to_dataframe([FeatureVectorChurn(**shuffled)])

    assert list(df.columns) == FEATURE_COLUMNS
    assert len(df) == 1
    assert df.loc[0, "region"] == "europe"


def test_feature_schema_describes_all_features(sample_df):
    schema = feature_schema(sample_df)
    features = schema["features"]

    assert schema["target"] == TARGET_COLUMN
    assert [f["name"] for f in features] == FEATURE_COLUMNS
    assert len(features) == 9
    for item in features:
        expected_role = "numeric" if item["name"] in NUMERIC_FEATURES else "categorical"
        assert item["role"] == expected_role
        # у категориальных признаков схема отдаёт допустимые значения из датасета
        if item["name"] in CATEGORICAL_FEATURES:
            assert item["categories"]
