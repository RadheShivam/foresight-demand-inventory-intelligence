from typing import List

from pydantic import BaseModel, Field


class PredictionRequest(BaseModel):
    sku_id: str = Field(
        ...,
        min_length=1,
        description="SKU identifier, for example SKU00001",
    )


class BatchPredictionRequest(BaseModel):
    sku_ids: List[str] = Field(
        ...,
        min_length=1,
        description="List of SKU identifiers",
    )


class ForecastPoint(BaseModel):
    week_start: str
    forecast_units: float
    lower_80: float
    upper_80: float


class PredictionResponse(BaseModel):
    sku_id: str
    forecast: List[ForecastPoint]

    decision_quadrant: str
    recommended_action: str

    stockout_risk: bool
    overstock_risk: bool

    sales_at_risk_rupees: float
    locked_capital_rupees: float


class BatchPredictionResponse(BaseModel):
    results: List[PredictionResponse]