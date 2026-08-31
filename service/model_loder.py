from pathlib import Path
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parent.parent

REPORTS_DIR = PROJECT_ROOT / "reports"


class ForecastRiskStore:

    def __init__(self):
        forecast_path = REPORTS_DIR / "forecast_weekly.csv"
        risk_path = REPORTS_DIR / "inventory_risk.csv"

        if not forecast_path.exists():
            raise FileNotFoundError(
                f"Forecast file not found: {forecast_path}"
            )

        if not risk_path.exists():
            raise FileNotFoundError(
                f"Risk file not found: {risk_path}"
            )

        self.forecast = pd.read_csv(
            forecast_path,
            parse_dates=["week_start"],
        )

        self.risk = pd.read_csv(
            risk_path
        )

        self.forecast["sku_id"] = (
            self.forecast["sku_id"].astype(str)
        )

        self.risk["sku_id"] = (
            self.risk["sku_id"].astype(str)
        )

        self.forecast_skus = set(
            self.forecast["sku_id"].unique()
        )

        self.risk_skus = set(
            self.risk["sku_id"].unique()
        )

    def get_sku(self, sku_id: str):
        sku_id = str(sku_id).strip()

        if not sku_id:
            raise ValueError(
                "sku_id cannot be empty."
            )

        if sku_id not in self.forecast_skus:
            raise KeyError(
                f"SKU '{sku_id}' not found in forecast data."
            )

        if sku_id not in self.risk_skus:
            raise KeyError(
                f"SKU '{sku_id}' not found in risk data."
            )

        forecast = (
            self.forecast[
                self.forecast["sku_id"] == sku_id
            ]
            .sort_values("week_start")
        )

        risk = (
            self.risk[
                self.risk["sku_id"] == sku_id
            ]
            .iloc[0]
        )

        return forecast, risk