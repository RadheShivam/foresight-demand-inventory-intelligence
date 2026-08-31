from fastapi import FastAPI, HTTPException

from .model_loder import ForecastRiskStore

from .schemas import (
    PredictionRequest,
    BatchPredictionRequest,
    PredictionResponse,
    BatchPredictionResponse,
    ForecastPoint,
)


app = FastAPI(
    title="FORESIGHT Scoring Service",
    description=(
        "Returns weekly demand forecast and inventory risk "
        "for FORESIGHT SKUs."
    ),
    version="1.0.0",
)


# ---------------------------------------------------------
# Root endpoint
# ---------------------------------------------------------
@app.get("/")
def root():
    return {
        "service": "FORESIGHT Scoring Service",
        "status": "ok",
        "docs": "/docs",
        "health": "/healthz",
    }


# ---------------------------------------------------------
# Load forecast and risk data
# ---------------------------------------------------------
try:
    store = ForecastRiskStore()
except Exception as exc:
    store = None
    startup_error = str(exc)
else:
    startup_error = None


# ---------------------------------------------------------
# Health check
# ---------------------------------------------------------
@app.get("/healthz")
def healthz():

    if store is None:
        return {
            "status": "unhealthy",
            "error": startup_error,
        }

    return {
        "status": "ok",
        "forecast_skus": len(store.forecast_skus),
        "risk_skus": len(store.risk_skus),
    }


# ---------------------------------------------------------
# Single SKU prediction
# ---------------------------------------------------------
@app.post(
    "/predict",
    response_model=PredictionResponse,
)
def predict(request: PredictionRequest):

    if store is None:
        raise HTTPException(
            status_code=503,
            detail="Scoring data is unavailable.",
        )

    try:
        forecast, risk = store.get_sku(
            request.sku_id
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    except KeyError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )

    result_forecast = []

    for row in forecast.itertuples():

        result_forecast.append(
            ForecastPoint(
                week_start=row.week_start.strftime("%Y-%m-%d"),
                forecast_units=float(row.forecast_units),
                lower_80=float(row.lower_80),
                upper_80=float(row.upper_80),
            )
        )

    return PredictionResponse(
        sku_id=str(request.sku_id).strip(),
        forecast=result_forecast,
        decision_quadrant=str(
            risk["decision_quadrant"]
        ),
        recommended_action=str(
            risk["recommended_action"]
        ),
        stockout_risk=bool(
            risk["stockout_risk"]
        ),
        overstock_risk=bool(
            risk["overstock_risk"]
        ),
        sales_at_risk_rupees=float(
            risk["sales_at_risk_rupees"]
        ),
        locked_capital_rupees=float(
            risk["locked_capital_rupees"]
        ),
    )


# ---------------------------------------------------------
# Batch prediction
# ---------------------------------------------------------
@app.post(
    "/predict/batch",
    response_model=BatchPredictionResponse,
)
def predict_batch(
    request: BatchPredictionRequest
):

    if store is None:
        raise HTTPException(
            status_code=503,
            detail="Scoring data is unavailable.",
        )

    if not request.sku_ids:
        raise HTTPException(
            status_code=400,
            detail="sku_ids cannot be empty.",
        )

    results = []

    for sku_id in request.sku_ids:

        try:
            forecast, risk = store.get_sku(
                sku_id
            )

        except ValueError as exc:
            raise HTTPException(
                status_code=400,
                detail=str(exc),
            )

        except KeyError as exc:
            raise HTTPException(
                status_code=404,
                detail=str(exc),
            )

        result_forecast = []

        for row in forecast.itertuples():

            result_forecast.append(
                ForecastPoint(
                    week_start=row.week_start.strftime("%Y-%m-%d"),
                    forecast_units=float(row.forecast_units),
                    lower_80=float(row.lower_80),
                    upper_80=float(row.upper_80),
                )
            )

        results.append(
            PredictionResponse(
                sku_id=str(sku_id).strip(),
                forecast=result_forecast,
                decision_quadrant=str(
                    risk["decision_quadrant"]
                ),
                recommended_action=str(
                    risk["recommended_action"]
                ),
                stockout_risk=bool(
                    risk["stockout_risk"]
                ),
                overstock_risk=bool(
                    risk["overstock_risk"]
                ),
                sales_at_risk_rupees=float(
                    risk["sales_at_risk_rupees"]
                ),
                locked_capital_rupees=float(
                    risk["locked_capital_rupees"]
                ),
            )
        )

    return BatchPredictionResponse(
        results=results
    )

