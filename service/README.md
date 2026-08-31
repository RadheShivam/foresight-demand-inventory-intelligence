# FORESIGHT Scoring Service

FastAPI service that returns the D3 weekly demand forecast and D4 inventory-risk decision for a SKU.

## Endpoints

### GET `/`
Service information.

### GET `/healthz`
Health and loaded-SKU status.

### POST `/predict`
Returns the 13-week forecast and inventory risk for one SKU.

Request:

```json
{
  "sku_id": "SKU00001"
}