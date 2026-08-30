from pathlib import Path
import pandas as pd


# ============================================================
# FORESIGHT - DATA QUALITY CHECK
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data" / "processed"


# ------------------------------------------------------------
# Required schemas from Zidio FORESIGHT
# ------------------------------------------------------------

REQUIRED_COLUMNS = {
    "sales_daily.csv": [
        "date",
        "sku_id",
        "units_sold",
        "revenue",
        "unit_price",
        "promo_flag",
    ],

    "sku_master.csv": [
        "sku_id",
        "category",
        "subcategory",
        "launch_date",
        "unit_cost",
        "list_price",
    ],

    "calendar.csv": [
        "date",
        "week",
        "month",
        "season",
        "is_holiday",
        "promo_event",
    ],

    "inventory_snapshots.csv": [
        "date",
        "sku_id",
        "on_hand_units",
        "on_order_units",
        "lead_time_days",
        "reorder_point",
    ],
}


# ------------------------------------------------------------
# Utility functions
# ------------------------------------------------------------

def print_header(title):
    """Print a formatted section header."""
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)


def check_columns(df, filename):
    """Check required and extra columns."""

    required = REQUIRED_COLUMNS[filename]

    missing_columns = [
        column for column in required
        if column not in df.columns
    ]

    extra_columns = [
        column for column in df.columns
        if column not in required
    ]

    print("\nRequired columns:")
    for column in required:
        status = "OK" if column in df.columns else "MISSING"
        print(f"  [{status}] {column}")

    if extra_columns:
        print("\nExtra columns:")
        for column in extra_columns:
            print(f"  [INFO] {column}")

    return missing_columns


def check_missing_values(df):
    """Check missing values."""

    missing = df.isna().sum()

    print("\nMissing values:")

    total_missing = 0

    for column, count in missing.items():
        print(f"  {column}: {count:,}")
        total_missing += count

    return total_missing


def check_duplicates(df, filename):
    """Check duplicate records using the appropriate business key."""

    if filename == "sales_daily.csv":
        duplicate_count = df.duplicated(
            subset=["date", "sku_id"]
        ).sum()

    elif filename == "sku_master.csv":
        duplicate_count = df.duplicated(
            subset=["sku_id"]
        ).sum()

    elif filename == "calendar.csv":
        duplicate_count = df.duplicated(
            subset=["date"]
        ).sum()

    elif filename == "inventory_snapshots.csv":
        duplicate_count = df.duplicated(
            subset=["date", "sku_id"]
        ).sum()

    else:
        duplicate_count = df.duplicated().sum()

    print(f"\nDuplicate business-key records: {duplicate_count:,}")

    return duplicate_count


def check_data_types(df):
    """Display data types."""

    print("\nData types:")

    for column, dtype in df.dtypes.items():
        print(f"  {column}: {dtype}")


# ------------------------------------------------------------
# Value validation
# ------------------------------------------------------------

def check_sales_daily(df):
    """Validate sales_daily values."""

    problems = 0

    if "units_sold" in df.columns:
        negative_units = (df["units_sold"] < 0).sum()
        print(f"\nNegative units_sold: {negative_units:,}")
        problems += negative_units

    if "revenue" in df.columns:
        negative_revenue = (df["revenue"] < 0).sum()
        print(f"Negative revenue: {negative_revenue:,}")
        problems += negative_revenue

    if "unit_price" in df.columns:
        negative_price = (df["unit_price"] < 0).sum()
        print(f"Negative unit_price: {negative_price:,}")
        problems += negative_price

    if "promo_flag" in df.columns:
        invalid_promo = ~df["promo_flag"].isin([0, 1])
        invalid_count = invalid_promo.sum()

        print(f"Invalid promo_flag values: {invalid_count:,}")

        problems += invalid_count

    return problems


def check_sku_master(df):
    """Validate sku_master values."""

    problems = 0

    if "unit_cost" in df.columns:
        negative_cost = (df["unit_cost"] < 0).sum()

        print(f"\nNegative unit_cost: {negative_cost:,}")

        problems += negative_cost

    if "list_price" in df.columns:
        negative_price = (df["list_price"] < 0).sum()

        print(f"Negative list_price: {negative_price:,}")

        problems += negative_price

    return problems


def check_calendar(df):
    """Validate calendar values."""

    problems = 0

    if "is_holiday" in df.columns:
        invalid_holiday = ~df["is_holiday"].isin([0, 1])
        invalid_count = invalid_holiday.sum()

        print(f"\nInvalid is_holiday values: {invalid_count:,}")

        problems += invalid_count

    if "month" in df.columns:
        invalid_month = ~df["month"].between(1, 12)
        invalid_count = invalid_month.sum()

        print(f"Invalid month values: {invalid_count:,}")

        problems += invalid_count

    if "week" in df.columns:
        invalid_week = ~df["week"].between(1, 53)
        invalid_count = invalid_week.sum()

        print(f"Invalid week values: {invalid_count:,}")

        problems += invalid_count

    return problems


def check_inventory(df):
    """Validate inventory values."""

    problems = 0

    numeric_columns = [
        "on_hand_units",
        "on_order_units",
        "lead_time_days",
        "reorder_point",
    ]

    for column in numeric_columns:

        if column in df.columns:

            negative_values = (df[column] < 0).sum()

            print(
                f"Negative {column}: "
                f"{negative_values:,}"
            )

            problems += negative_values

    return problems


# ------------------------------------------------------------
# Cross-table validation
# ------------------------------------------------------------

def cross_table_checks(data):
    """Check relationships between the four FORESIGHT tables."""

    print_header("CROSS-TABLE VALIDATION")

    sales = data["sales_daily.csv"]
    sku = data["sku_master.csv"]
    calendar = data["calendar.csv"]
    inventory = data["inventory_snapshots.csv"]

    # --------------------------------------------------------
    # SKU consistency
    # --------------------------------------------------------

    sales_skus = set(
        sales["sku_id"].dropna().astype(str)
    )

    master_skus = set(
        sku["sku_id"].dropna().astype(str)
    )

    inventory_skus = set(
        inventory["sku_id"].dropna().astype(str)
    )

    sales_missing_master = sales_skus - master_skus
    master_missing_sales = master_skus - sales_skus
    inventory_missing_master = inventory_skus - master_skus
    master_missing_inventory = master_skus - inventory_skus

    print(
        "\nSales SKUs missing from sku_master:",
        len(sales_missing_master)
    )

    print(
        "sku_master SKUs missing from sales:",
        len(master_missing_sales)
    )

    print(
        "Inventory SKUs missing from sku_master:",
        len(inventory_missing_master)
    )

    print(
        "sku_master SKUs missing from inventory:",
        len(master_missing_inventory)
    )

    # --------------------------------------------------------
    # Date consistency
    # --------------------------------------------------------

    sales_dates = set(
        pd.to_datetime(
            sales["date"],
            errors="coerce"
        ).dropna()
    )

    calendar_dates = set(
        pd.to_datetime(
            calendar["date"],
            errors="coerce"
        ).dropna()
    )

    missing_calendar_dates = sales_dates - calendar_dates

    print(
        "\nSales dates missing from calendar:",
        len(missing_calendar_dates)
    )


# ------------------------------------------------------------
# Main quality check
# ------------------------------------------------------------

def run_quality_check():

    print_header("FORESIGHT DATA QUALITY REPORT")

    print(f"Project root: {PROJECT_ROOT}")
    print(f"Processed data: {DATA_DIR}")

    data = {}

    overall_problems = 0

    # --------------------------------------------------------
    # Process each dataset
    # --------------------------------------------------------

    for filename in REQUIRED_COLUMNS:

        print_header(filename)

        filepath = DATA_DIR / filename

        if not filepath.exists():

            print(f"ERROR: File not found: {filepath}")

            overall_problems += 1

            continue

        try:
            df = pd.read_csv(filepath)

        except Exception as error:

            print(f"ERROR reading file: {error}")

            overall_problems += 1

            continue

        data[filename] = df

        print(f"\nRows: {len(df):,}")
        print(f"Columns: {len(df.columns)}")

        # Columns
        missing_columns = check_columns(
            df,
            filename
        )

        overall_problems += len(missing_columns)

        # Missing values
        missing_values = check_missing_values(df)

        # Duplicates
        duplicate_count = check_duplicates(
            df,
            filename
        )

        overall_problems += duplicate_count

        # Data types
        check_data_types(df)

        # Dataset-specific checks
        if filename == "sales_daily.csv":
            overall_problems += check_sales_daily(df)

        elif filename == "sku_master.csv":
            overall_problems += check_sku_master(df)

        elif filename == "calendar.csv":
            overall_problems += check_calendar(df)

        elif filename == "inventory_snapshots.csv":
            overall_problems += check_inventory(df)

    # --------------------------------------------------------
    # Cross-table checks
    # --------------------------------------------------------

    if len(data) == 4:
        cross_table_checks(data)

    # --------------------------------------------------------
    # Final result
    # --------------------------------------------------------

    print_header("FINAL RESULT")

    if overall_problems == 0:

        print("STATUS: PASS")
        print("No technical data-quality errors detected.")

    else:

        print("STATUS: REVIEW")
        print(
            f"Potential data-quality issues detected: "
            f"{overall_problems:,}"
        )

    print("\nData quality check completed.")


# ------------------------------------------------------------
# Entry point
# ------------------------------------------------------------

if __name__ == "__main__":
    run_quality_check()