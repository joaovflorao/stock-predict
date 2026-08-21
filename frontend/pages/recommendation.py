import asyncio

import reflex as rx

from stock_predict.database.session import SessionLocal
from stock_predict.schemas.config import Granularity
from stock_predict.schemas.recommendation import PurchaseRecommendationRequest
from stock_predict.services.recommendation import generate_purchase_recommendation

from .common import MODEL_LABELS, load_items_sync, parse_item_id
from .nav import nav_bar


def _run_recommendation_sync(
        item_id: int,
        granularity: Granularity,
        horizon: int,
        lead_time_periods: int,
        model_name: str,
) -> dict:
    db = SessionLocal()
    try:
        request = PurchaseRecommendationRequest(
            item_id=item_id,
            granularity=granularity,
            horizon=horizon,
            lead_time_periods=lead_time_periods,
            model_name=model_name,
        )
        recommendation = generate_purchase_recommendation(db, request)
        return recommendation.model_dump(mode="json")
    finally:
        db.close()


class RecommendationState(rx.State):
    item_options: list[str] = []
    selected_item: str = ""
    granularity: str = Granularity.WEEKLY.value
    horizon: int = 4
    lead_time_periods: int = 2
    model_name: str = "xgboost"

    has_result: bool = False
    result_reliable: bool = True
    result_current_stock: str = ""
    result_reorder_point: str = ""
    result_should_reorder_label: str = ""
    result_recommended_order_quantity: str = ""
    result_periods_until_stockout: str = ""
    result_next_reorder_date: str = ""

    is_loading_items: bool = False
    is_computing: bool = False
    error: str = ""

    def set_selected_item(self, value: str):
        self.selected_item = value

    def set_granularity(self, value: str):
        self.granularity = value

    def set_horizon(self, value: str):
        self.horizon = int(value) if value else 0

    def set_lead_time_periods(self, value: str):
        self.lead_time_periods = int(value) if value else 0

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
    async def compute_recommendation(self):
        if not self.selected_item:
            async with self:
                self.error = "Selecione um item"
            return
        if self.horizon <= 0 or self.lead_time_periods <= 0:
            async with self:
                self.error = "Horizonte e tempo de reposição precisam ser maiores que zero."
            return

        item_id = parse_item_id(self.selected_item)
        granularity = Granularity(self.granularity)
        horizon = self.horizon
        lead_time_periods = self.lead_time_periods
        model_name = self.model_name

        async with self:
            self.is_computing = True
            self.error = ""
            self.has_result = False

        try:
            result = await asyncio.to_thread(
                _run_recommendation_sync, item_id, granularity, horizon, lead_time_periods, model_name
            )
        except ValueError as exc:
            async with self:
                self.error = str(exc)
                self.is_computing = False
            return
        except Exception as exc:
            async with self:
                self.error = f"Erro ao calcular a recomendação: {exc}"
                self.is_computing = False
            return

        async with self:
            self.has_result = True
            self.result_reliable = result["reliable"]
            self.result_current_stock = str(result["current_stock"])
            self.result_reorder_point = f'{result["reorder_point"]:.2f}'
            self.result_should_reorder_label = "Sim" if result["should_reorder_now"] else "Não"
            self.result_recommended_order_quantity = f'{result["recommended_order_quantity"]:.2f}'
            self.result_periods_until_stockout = (
                str(result["periods_until_stockout"])
                if result["periods_until_stockout"] is not None
                else "-"
            )
            self.result_next_reorder_date = result["next_reorder_date"] or "-"
            self.is_computing = False


def recommendation_page() -> rx.Component:
    return rx.center(
        rx.vstack(
            nav_bar(),
            rx.heading("Recomendação de Compra"),
            rx.hstack(
                rx.button(
                    "Carregar Itens",
                    on_click=RecommendationState.load_items,
                    loading=RecommendationState.is_loading_items,
                ),
                rx.select(
                    RecommendationState.item_options,
                    placeholder="Selecione um item",
                    value=RecommendationState.selected_item,
                    on_change=RecommendationState.set_selected_item,
                ),
                rx.select(
                    [g.value for g in Granularity],
                    value=RecommendationState.granularity,
                    on_change=RecommendationState.set_granularity,
                ),
                rx.input(
                    type="number",
                    value=RecommendationState.horizon,
                    on_change=RecommendationState.set_horizon,
                    width="6em",
                ),
                rx.input(
                    type="number",
                    value=RecommendationState.lead_time_periods,
                    on_change=RecommendationState.set_lead_time_periods,
                    width="6em",
                ),
                rx.select(
                    list(MODEL_LABELS.keys()),
                    value=RecommendationState.model_name,
                    on_change=RecommendationState.set_model_name,
                ),
                rx.button(
                    "Calcular",
                    on_click=RecommendationState.compute_recommendation,
                    loading=RecommendationState.is_computing,
                ),
                spacing="3",
                wrap="wrap",
            ),
            rx.cond(
                RecommendationState.error != "",
                rx.callout(RecommendationState.error, color_scheme="red"),
            ),
            rx.cond(
                RecommendationState.has_result,
                rx.vstack(
                    rx.cond(
                        ~RecommendationState.result_reliable,
                        rx.callout(
                            "Histórico curto: recomendação estimada pela demanda média histórica.",
                            color_scheme="amber",
                        ),
                    ),
                    rx.table.root(
                        rx.table.body(
                            rx.table.row(
                                rx.table.cell("Estoque atual"),
                                rx.table.cell(RecommendationState.result_current_stock),
                            ),
                            rx.table.row(
                                rx.table.cell("Ponto de reposição"),
                                rx.table.cell(RecommendationState.result_reorder_point),
                            ),
                            rx.table.row(
                                rx.table.cell("Comprar agora?"),
                                rx.table.cell(RecommendationState.result_should_reorder_label),
                            ),
                            rx.table.row(
                                rx.table.cell("Quantidade sugerida"),
                                rx.table.cell(RecommendationState.result_recommended_order_quantity),
                            ),
                            rx.table.row(
                                rx.table.cell("Períodos até esgotar o estoque"),
                                rx.table.cell(RecommendationState.result_periods_until_stockout),
                            ),
                            rx.table.row(
                                rx.table.cell("Próxima reposição estimada"),
                                rx.table.cell(RecommendationState.result_next_reorder_date),
                            ),
                        )
                    ),
                    spacing="3",
                ),
            ),
            spacing="4",
            width="100%",
            max_width="900px",
        ),
    )
