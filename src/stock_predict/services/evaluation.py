import numpy as np
import pandas as pd

from typing import Callable

from stock_predict.schemas.predict import EvaluationResult
from stock_predict.ml.base import ForecastModel


def wape(y_true: pd.Series, y_pred: pd.Series) -> float:
    denominator = np.sum(np.abs(y_true))
    if denominator == 0:
        return 0.0

    return float(np.sum(np.abs(y_true - y_pred)) / denominator)


def walk_forward_validation(
        series: pd.DataFrame,
        model_factory,
        horizon: int,
        min_train_size: int,
        frequency: str,
) -> dict:
    """
    Validação walk-forward

    Treina o modelo utilizando os dados disponíveis até determinado
    período, prevê os próximos `horizon` períodos e avança a janela

    Retorna métricas agregadas (WAPE, MAE, RMSE)
    """
    if len(series) < min_train_size + horizon:
        raise ValueError(
            f"Série tem {len(series)} períodos, mas min_train_size ({min_train_size}) "
            f"+ horizon ({horizon}) exige pelo menos {min_train_size + horizon} períodos."
        )

    y_true_list = []
    y_pred_list = []
    predictions_list = []

    for end in range(min_train_size, len(series) - horizon + 1):
        train = series.iloc[:end].copy()
        test = series.iloc[end:end + horizon].copy()

        model = model_factory()
        model.fit(train, frequency)

        forecast = model.predict(horizon)

        predictions = pd.DataFrame({
            "period": test["period"].reset_index(drop=True),
            "actual": test["demand"].reset_index(drop=True),
            "predicted": forecast["predicted_quantity"].reset_index(drop=True),
        })
        predictions_list.append(predictions)

        y_true = test["demand"].reset_index(drop=True)
        y_pred = forecast["predicted_quantity"].reset_index(drop=True)

        y_true_list.extend(y_true.tolist())
        y_pred_list.extend(y_pred.tolist())

    y_true_all = pd.Series(y_true_list)
    y_pred_all = pd.Series(y_pred_list)

    errors = y_true_all - y_pred_all

    mae = float(np.mean(np.abs(errors)))
    rmse = float(np.sqrt(np.mean(errors ** 2)))

    predictions_list = pd.concat(
        predictions_list,
        ignore_index=True,
    )
    return {
        "metrics": {
            "wape": wape(y_true_all, y_pred_all),
            "mae": mae,
            "rmse": rmse,
        },
        "predictions": predictions_list,
    }


def compare_models(
        series: pd.DataFrame,
        frequency: str,
        horizon: int,
        min_train_size: int,
        model_factories: dict[str, Callable[[], ForecastModel]]
) -> list[EvaluationResult]:
    """ Compara o desempenho dos modelos """
    results_list = []
    for model_name, factory in model_factories.items():
        validation = walk_forward_validation(series, factory, horizon, min_train_size, frequency)
        results_list.append(
            EvaluationResult(
                model_name=model_name,
                wape=validation["metrics"]["wape"],
                mae=validation["metrics"]["mae"],
                rmse=validation["metrics"]["rmse"],
            )
        )
    return results_list
