import reflex as rx
from fastapi import FastAPI

from stock_predict.api.routes import router as prediction_router

from frontend.pages.ingestion import ingestion_page
from frontend.pages.opportunities import opportunities_page
from frontend.pages.prediction import prediction_page
from frontend.pages.recommendation import recommendation_page

fastapi_app = FastAPI()
fastapi_app.include_router(prediction_router, prefix="/api")

app = rx.App(api_transformer=fastapi_app)
app.add_page(prediction_page, route="/")
app.add_page(ingestion_page, route="/ingestion")
app.add_page(recommendation_page, route="/recommendation")
app.add_page(opportunities_page, route="/opportunities")
