from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlalchemy.orm import Session

from stock_predict.database.session import get_connection
from stock_predict.schemas.ingestion import IngestionResult
from stock_predict.schemas.opportunity import ItemOpportunity, OpportunityRequest
from stock_predict.schemas.predict import PredictRequest, SeriesRequest, PredictionResult, EvaluationResult
from stock_predict.schemas.recommendation import PurchaseRecommendation, PurchaseRecommendationRequest
from stock_predict.services.demand import get_demand_series
from stock_predict.services.evaluation import compare_models
from stock_predict.services.ingestion import ingest_movement_from_csv
from stock_predict.services.opportunity import generate_opportunities
from stock_predict.services.prediction import generate_prediction, MODEL_FACTORIES
from stock_predict.services.recommendation import generate_purchase_recommendation


router = APIRouter()


@router.post("/predict", response_model=list[PredictionResult])
def predict(request: PredictRequest, db: Session = Depends(get_connection)):
    try:
        return generate_prediction(db, request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/compare", response_model=list[EvaluationResult])
def compare(request: SeriesRequest, db: Session = Depends(get_connection)):
    try:
        series, frequency = get_demand_series(db, request.item_id, request.granularity)
        return compare_models(series, frequency, request.horizon, request.min_train_size, MODEL_FACTORIES)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/recommend", response_model=PurchaseRecommendation)
def recommend(request: PurchaseRecommendationRequest, db: Session = Depends(get_connection)):
    try:
        return generate_purchase_recommendation(db, request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/opportunities", response_model=list[ItemOpportunity])
def opportunities(request: OpportunityRequest, db: Session = Depends(get_connection)):
    return generate_opportunities(db, request)


@router.post("/ingest", response_model=IngestionResult)
async def ingest(file: UploadFile, db: Session = Depends(get_connection)):
    content = await file.read()
    return ingest_movement_from_csv(content, db)
