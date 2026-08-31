from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "processed"
REPORTS_DIR = PROJECT_ROOT / "reports"

def _require(path: Path) -> Path:
    if not path.exists():
        raise FileNotFoundError(f"Required file not found: {path}")
    return path

def load_forecast() -> pd.DataFrame:
    return pd.read_csv(_require(REPORTS_DIR / "forecast_weekly.csv"),
                        parse_dates=["week_start"])

def load_risk() -> pd.DataFrame:
    return pd.read_csv(_require(REPORTS_DIR / "inventory_risk.csv"))

def load_sales() -> pd.DataFrame:
    return pd.read_csv(_require(DATA_DIR / "sales_daily.csv"),
                        parse_dates=["date"])
