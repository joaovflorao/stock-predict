import asyncio

import reflex as rx

from stock_predict.database.session import SessionLocal
from stock_predict.schemas.config import Granularity
from stock_predict.services.prediction import run_full_analysis

from .common import MODEL_LABELS, load_items_sync, parse_item_id
from .nav import nav_bar


def _run_analysis_sync(item_id: int, granularity: Granularity, horizon: int, model_name: str) -> dict:
    db = SessionLocal()
    try:
        return run_full_analysis(db, item_id, granularity, horizon, model_name=model_name)
    finally:
        db.close()


class PredictionState(rx.State):
    item_options: list[str] = []
    selected_item: str = ""
    granularity: str = Granularity.WEEKLY.value
    horizon: int = 4
    model_name: str = "xgboost"

    predictions_list: list[dict] = []
    comparison_list: list[dict] = []
    chart_data_list: list[dict] = []
    predictions_reliable: bool = True

    is_loading_items: bool = False
    is_predicting: bool = False
    error: str = ""

    def set_selected_item(self, value: str):
        self.selected_item = value

    def set_granularity(self, value: str):
        self.granularity = value

    def set_horizon(self, value: str):
        self.horizon = int(value) if value else 0

    def set_model_name(self, value: str):
        self.model_name = value

    @rx.event(background=True)
    async def load_items(self):
        async with self:
            self.is_loading_items = True
            self.error = ""

        try:
            options = await asyncio.to_thread(load_items_sync)
        except Exception as exc:
            async with self:
                self.error = f"Falha ao carregar itens: {exc}"
                self.is_loading_items = False
            return

        async with self:
            self.item_options = options
            self.is_loading_items = False

    @rx.event(background=True)
    async def run_prediction(self):
        if not self.selected_item:
            async with self:
                self.error = "Selecione um item"
            return
        if self.horizon <= 0:
            async with self:
                self.error = "O horizonte precisa ser maior que zero."
            return

        item_id = parse_item_id(self.selected_item)
        granularity = Granularity(self.granularity)
        horizon = self.horizon
        model_name = self.model_name

        async with self:
            self.is_predicting = True
            self.error = ""
            self.predictions_list = []
            self.comparison_list = []
            self.chart_data_list = []

        try:
            result = await asyncio.to_thread(_run_analysis_sync, item_id, granularity, horizon, model_name)
        except ValueError as exc:
            async with self:
                self.error = str(exc)
                self.is_predicting = False
            return
        except Exception as exc:
            async with self:
                self.error = f"Erro ao executar a predição: {exc}"
                self.is_predicting = False
            return

        predictions_data = [p.model_dump(mode="json") for p in result["predictions"]]
        comparison_data = [c.model_dump(mode="json") for c in result["comparison"]]

        chart_points = [
            {
                "period": h["period"],
                "actual": h["demand"],
            }
            for h in result["history"]
        ]
        if chart_points:
            last = chart_points[-1]
            chart_points[-1] = {
                **last,
                "predicted": last["actual"],
                "band_base": last["actual"],
                "band_range": 0.0,
            }
        for p in predictions_data:
            chart_points.append({
                "period": p["period"],
                "predicted": float(p["predicted_quantity"]),
                "band_base": float(p["lower_bound"]),
                "band_range": float(p["upper_bound"]) - float(p["lower_bound"]),
            })

        async with self:
            self.predictions_list = predictions_data
            self.comparison_list = comparison_data
            self.chart_data_list = chart_points
            self.predictions_reliable = predictions_data[0]["reliable"] if predictions_data else True
            self.is_predicting = False


def prediction_page() -> rx.Component:
    return rx.center(
        nav_bar(),
        rx.vstack(
        rx.heading("Stock Predict"),
        rx.hstack(
            rx.button(
                "Carregar Itens",
                on_click=PredictionState.load_items,
                loading=PredictionState.is_loading_items,
            ),
            rx.select(
                PredictionState.item_options,
                placeholder="Selecione um item",
                value=PredictionState.selected_item,
                on_change=PredictionState.set_selected_item,
            ),
            rx.select(
                [g.value for g in Granularity],
                value=PredictionState.granularity,
                on_change=PredictionState.set_granularity,
            ),
            rx.input(
                type="number",
                value=PredictionState.horizon,
                on_change=PredictionState.set_horizon,
                width="6em",
            ),
            rx.select(
                list(MODEL_LABELS.keys()),
                value=PredictionState.model_name,
                on_change=PredictionState.set_model_name,
            ),
            rx.button(
                "Consultar",
                on_click=PredictionState.run_prediction,
                loading=PredictionState.is_predicting,
            ),
            spacing="3",
        ),
        rx.cond(
            PredictionState.error != "",
            rx.callout(PredictionState.error, color_scheme="red"),
        ),
        rx.cond(
            (PredictionState.predictions_list.length() > 0) & (~PredictionState.predictions_reliable),
            rx.callout(
                "Histórico curto: previsão estimada pela demanda média histórica.",
                color_scheme="amber",
            ),
        ),
        rx.cond(
            (~PredictionState.is_loading_items) & (PredictionState.item_options.length() == 0),
            rx.text('Clique em "Carregar Itens" para começar', color_scheme="gray"),
        ),
        rx.cond(
            PredictionState.chart_data_list.length() > 0,
            rx.recharts.responsive_container(
                rx.recharts.composed_chart(
                    rx.recharts.cartesian_grid(stroke_dasharray="3 3"),
                    rx.recharts.x_axis(data_key="period"),
                    rx.recharts.y_axis(),
                    rx.recharts.tooltip(),
                    rx.recharts.legend(),
                    rx.recharts.area(
                        data_key="band_base",
                        stack_id="band",
                        stroke="transparent",
                        fill="transparent",
                        name="",
                        legend_type="none",
                    ),
                    rx.recharts.area(
                        data_key="band_range",
                        stack_id="band",
                        stroke="transparent",
                        fill="#8884d8",
                        fill_opacity=0.2,
                        name="Intervalo de confiança",
                    ),
                    rx.recharts.line(
                        data_key="actual",
                        stroke="#2b8a3e",
                        name="Demanda real",
                        dot=False,
                    ),
                    rx.recharts.line(
                        data_key="predicted",
                        stroke="#1c7ed6",
                        name="Previsão",
                        dot=False,
                    ),
                    data=PredictionState.chart_data_list,
                ),
                width="100%",
                height=350,
            ),
        ),
        rx.cond(
            PredictionState.comparison_list.length() > 0,
            rx.vstack(
                rx.heading("Comparação de modelos", size="4"),
                rx.table.root(
                    rx.table.header(
                        rx.table.row(
                            rx.table.column_header_cell("Modelo"),
                            rx.table.column_header_cell("WAPE"),
                            rx.table.column_header_cell("MAE"),
                            rx.table.column_header_cell("RMSE"),
                        )
                    ),
                    rx.table.body(
                        rx.foreach(
                            PredictionState.comparison_list,
                            lambda c: rx.table.row(
                                rx.table.cell(c["model_name"]),
                                rx.table.cell(c["wape"]),
                                rx.table.cell(c["mae"]),
                                rx.table.cell(c["rmse"]),
                            ),
                        )
                    )
                ),
            ),
        ),
        rx.cond(
            PredictionState.predictions_list.length() > 0,
            rx.vstack(
                rx.heading("Previsão", size="4"),
                rx.table.root(
                    rx.table.header(
                        rx.table.row(
                            rx.table.column_header_cell("Período"),
                            rx.table.column_header_cell("Previsto"),
                            rx.table.column_header_cell("Mínimo"),
                            rx.table.column_header_cell("Máximo"),
                        )
                    ),
                    rx.table.body(
                        rx.foreach(
                            PredictionState.predictions_list,
                            lambda p: rx.table.row(
                                rx.table.cell(p["period"]),
                                rx.table.cell(p["predicted_quantity"]),
                                rx.table.cell(p["lower_bound"]),
                                rx.table.cell(p["upper_bound"]),
                            )
                        )
                    )
                ),
            ),
        ),
            spacing="4",
            width="100%",
            max_width="900px",
        ),
    )
