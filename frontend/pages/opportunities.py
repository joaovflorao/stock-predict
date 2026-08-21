import asyncio

import reflex as rx

from stock_predict.database.session import SessionLocal
from stock_predict.schemas.config import Granularity
from stock_predict.schemas.opportunity import OpportunityRequest
from stock_predict.services.opportunity import generate_opportunities

from .common import MODEL_LABELS
from .nav import nav_bar


def _run_opportunities_sync(
        granularity: Granularity,
        horizon: int,
        model_name: str,
        trend_threshold_pct: float,
) -> list[dict]:
    db = SessionLocal()
    try:
        request = OpportunityRequest(
            granularity=granularity,
            horizon=horizon,
            model_name=model_name,
            trend_threshold_pct=trend_threshold_pct,
        )
        opportunities = generate_opportunities(db, request)
        return [
            {
                **opportunity.model_dump(mode="json"),
                "reliable_label": "Sim" if opportunity.reliable else "Não",
            }
            for opportunity in opportunities
        ]
    finally:
        db.close()


class OpportunityState(rx.State):
    granularity: str = Granularity.WEEKLY.value
    horizon: int = 4
    model_name: str = "xgboost"
    trend_threshold_pct: float = 5.0

    opportunities_list: list[dict] = []

    is_computing: bool = False
    error: str = ""

    def set_granularity(self, value: str):
        self.granularity = value

    def set_horizon(self, value: str):
        self.horizon = int(value) if value else 0

    def set_model_name(self, value: str):
        self.model_name = value

    def set_trend_threshold_pct(self, value: str):
        self.trend_threshold_pct = float(value) if value else 0.0

    @rx.event(background=True)
    async def compute_opportunities(self):
        if self.horizon <= 0:
            async with self:
                self.error = "O horizonte precisa ser maior que zero."
            return

        granularity = Granularity(self.granularity)
        horizon = self.horizon
        model_name = self.model_name
        trend_threshold_pct = self.trend_threshold_pct

        async with self:
            self.is_computing = True
            self.error = ""
            self.opportunities_list = []

        try:
            result = await asyncio.to_thread(
                _run_opportunities_sync, granularity, horizon, model_name, trend_threshold_pct
            )
        except Exception as exc:
            async with self:
                self.error = f"Erro ao calcular oportunidades: {exc}"
                self.is_computing = False
            return

        async with self:
            self.opportunities_list = result
            self.is_computing = False


def opportunities_page() -> rx.Component:
    return rx.center(
        rx.vstack(
            nav_bar(),
            rx.heading("Oportunidades de Venda"),
            rx.hstack(
                rx.select(
                    [g.value for g in Granularity],
                    value=OpportunityState.granularity,
                    on_change=OpportunityState.set_granularity,
                ),
                rx.input(
                    type="number",
                    value=OpportunityState.horizon,
                    on_change=OpportunityState.set_horizon,
                    width="6em",
                ),
                rx.select(
                    list(MODEL_LABELS.keys()),
                    value=OpportunityState.model_name,
                    on_change=OpportunityState.set_model_name,
                ),
                rx.input(
                    type="number",
                    value=OpportunityState.trend_threshold_pct,
                    on_change=OpportunityState.set_trend_threshold_pct,
                    width="6em",
                ),
                rx.button(
                    "Calcular",
                    on_click=OpportunityState.compute_opportunities,
                    loading=OpportunityState.is_computing,
                ),
                spacing="3",
                wrap="wrap",
            ),
            rx.cond(
                OpportunityState.error != "",
                rx.callout(OpportunityState.error, color_scheme="red"),
            ),
            rx.cond(
                OpportunityState.opportunities_list.length() > 0,
                rx.table.root(
                    rx.table.header(
                        rx.table.row(
                            rx.table.column_header_cell("Item"),
                            rx.table.column_header_cell("Tendência"),
                            rx.table.column_header_cell("Var. %"),
                            rx.table.column_header_cell("Média Histórica"),
                            rx.table.column_header_cell("Média Prevista"),
                            rx.table.column_header_cell("Total Previsto"),
                            rx.table.column_header_cell("Confiável"),
                        )
                    ),
                    rx.table.body(
                        rx.foreach(
                            OpportunityState.opportunities_list,
                            lambda o: rx.table.row(
                                rx.table.cell(o["item_description"]),
                                rx.table.cell(o["trend"]),
                                rx.table.cell(o["trend_pct"]),
                                rx.table.cell(o["historical_average_demand"]),
                                rx.table.cell(o["forecasted_average_demand"]),
                                rx.table.cell(o["total_forecasted_demand"]),
                                rx.table.cell(o["reliable_label"]),
                            ),
                        )
                    ),
                ),
            ),
            spacing="4",
            width="100%",
            max_width="1100px",
        ),
    )
