from pathlib import Path

import pandas as pd

from models import DatasetRowChurn

DATA_PATH = Path(__file__).resolve().parents[2] / "data" / "churn_dataset.csv"


class ChurnDataset:
    """Загружает churn-датасет и даёт удобный доступ к нему."""

    def __init__(self, csv_path: Path = DATA_PATH):
        self.csv_path = Path(csv_path)
        # храним данные в pandas DataFrame
        self.df: pd.DataFrame = pd.read_csv(self.csv_path)

    def to_rows(self) -> list[DatasetRowChurn]:
        """Преобразует все строки датасета в объекты DatasetRowChurn."""
        records = self.df.to_dict(orient="records")
        return [DatasetRowChurn(**row) for row in records]

    def preview(self, n: int = 5) -> list[DatasetRowChurn]:
        """Первые n строк датасета как валидированные объекты DatasetRowChurn."""
        records = self.df.head(n).to_dict(orient="records")
        return [DatasetRowChurn(**row) for row in records]

    def info(self) -> dict:
        """Сводка по датасету: размеры, признаки, распределение churn."""
        churn_counts = self.df["churn"].value_counts().sort_index()
        return {
            "n_rows": int(self.df.shape[0]),
            "n_columns": int(self.df.shape[1]),
            "feature_names": list(self.df.columns),
            "churn_distribution": {int(cls): int(cnt) for cls, cnt in churn_counts.items()},
        }