from pathlib import Path
import pandas as pd
import numpy as np


# ============================================================
# FORESIGHT — DATA PIPELINE
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

PROCESSED_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# Utility functions
# ============================================================

def print_header(title):
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)


def check_file(path):
    if not path.exists():
        raise FileNotFoundError(
            f"Required file not found:\n{path}"
        )


def save_csv(df, filename):
    output_path = PROCESSED_DIR / filename
    df.to_csv(output_path, index=False)

    print(
        f"Saved: {filename} "
        f"({len(df):,} rows)"
    )

    return output_path


# ============================================================
# 1. SALES DAILY
# ============================================================

def build_sales_daily():

    print_header("BUILDING SALES DAILY")

    source = RAW_DIR / "sales_transactions.csv"
    check_file(source)

    df = pd.read_csv(source)

    print(f"Raw rows: {len(df):,}")

    # --------------------------------------------------------
    # Actual raw source columns
    # --------------------------------------------------------

    required = [
        "date",
        "sku_id",
        "quantity",
        "unit_price",
        "total_value",
        "promo_id"
    ]

    missing = [
        col for col in required
        if col not in df.columns
    ]

    if missing:
        raise ValueError(
            f"sales_transactions.csv is missing columns: {missing}"
        )

    # --------------------------------------------------------
    # Data types
    # --------------------------------------------------------

    df["date"] = pd.to_datetime(
        df["date"],
        errors="coerce"
    )

    df["sku_id"] = df["sku_id"].astype(str)

    df["quantity"] = pd.to_numeric(
        df["quantity"],
        errors="coerce"
    )

    df["unit_price"] = pd.to_numeric(
        df["unit_price"],
        errors="coerce"
    )

    df["total_value"] = pd.to_numeric(
        df["total_value"],
        errors="coerce"
    )

    # --------------------------------------------------------
    # Promotion flag
    #
    # promo_id is NaN when there is no promotion.
    # Therefore:
    #     promo_id present -> 1
    #     promo_id missing -> 0
    # --------------------------------------------------------

    df["promo_flag"] = (
        df["promo_id"]
        .notna()
        .astype(int)
    )

    # --------------------------------------------------------
    # Remove rows with invalid essential values
    # --------------------------------------------------------

    df = df.dropna(
        subset=[
            "date",
            "sku_id",
            "quantity",
            "unit_price",
            "total_value"
        ]
    )

    # --------------------------------------------------------
    # Validate numeric values
    # --------------------------------------------------------

    df = df[
        (df["quantity"] >= 0) &
        (df["unit_price"] >= 0) &
        (df["total_value"] >= 0)
    ]

    # --------------------------------------------------------
    # Aggregate transaction data to:
    #
    # date + sku_id
    #
    # This creates the Zidio sales_daily grain.
    # --------------------------------------------------------

    sales_daily = (
        df.groupby(
            ["date", "sku_id"],
            as_index=False
        )
        .agg(
            units_sold=(
                "quantity",
                "sum"
            ),

            revenue=(
                "total_value",
                "sum"
            ),

            unit_price=(
                "unit_price",
                "mean"
            ),

            promo_flag=(
                "promo_flag",
                "max"
            )
        )
    )

    sales_daily["promo_flag"] = (
        sales_daily["promo_flag"]
        .astype(int)
    )

    # --------------------------------------------------------
    # Final column order
    # --------------------------------------------------------

    sales_daily = sales_daily[
        [
            "date",
            "sku_id",
            "units_sold",
            "revenue",
            "unit_price",
            "promo_flag"
        ]
    ]

    sales_daily = sales_daily.sort_values(
        ["date", "sku_id"]
    )

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    save_csv(
        sales_daily,
        "sales_daily.csv"
    )

    print(
        f"Final sales_daily rows: "
        f"{len(sales_daily):,}"
    )


def build_sku_master():

    print_header("BUILDING SKU MASTER")

    source = RAW_DIR / "sku_master.csv"
    sales_source = RAW_DIR / "sales_transactions.csv"

    check_file(source)
    check_file(sales_source)

    # --------------------------------------------------------
    # Load raw SKU master
    # --------------------------------------------------------

    df = pd.read_csv(source)

    print(f"Raw SKU rows: {len(df):,}")

    # Actual raw columns
    required = [
        "sku_id",
        "category",
        "subcategory",
        "unit_price",
        "cost_price"
    ]

    missing = [
        col for col in required
        if col not in df.columns
    ]

    if missing:
        raise ValueError(
            f"sku_master.csv is missing columns: {missing}"
        )

    # --------------------------------------------------------
    # Clean data types
    # --------------------------------------------------------

    df["sku_id"] = df["sku_id"].astype(str)

    df["category"] = df["category"].astype(str)

    df["subcategory"] = df["subcategory"].astype(str)

    df["unit_price"] = pd.to_numeric(
        df["unit_price"],
        errors="coerce"
    )

    df["cost_price"] = pd.to_numeric(
        df["cost_price"],
        errors="coerce"
    )

    # --------------------------------------------------------
    # Remove invalid records
    # --------------------------------------------------------

    df = df.dropna(
        subset=[
            "sku_id",
            "category",
            "subcategory",
            "unit_price",
            "cost_price"
        ]
    )

    df = df[
        (df["unit_price"] >= 0) &
        (df["cost_price"] >= 0)
    ]

    # --------------------------------------------------------
    # Load sales dates to derive launch_date
    # --------------------------------------------------------

    sales = pd.read_csv(
        sales_source,
        usecols=["date", "sku_id"]
    )

    sales["date"] = pd.to_datetime(
        sales["date"],
        errors="coerce"
    )

    sales["sku_id"] = sales["sku_id"].astype(str)

    # Earliest observed sale = launch_date proxy
    first_sale = (
        sales
        .dropna(subset=["date", "sku_id"])
        .groupby("sku_id", as_index=False)["date"]
        .min()
        .rename(
            columns={
                "date": "launch_date"
            }
        )
    )

    # --------------------------------------------------------
    # Add launch_date
    # --------------------------------------------------------

    df = df.merge(
        first_sale,
        on="sku_id",
        how="left"
    )

    # --------------------------------------------------------
    # Convert raw names to Zidio names
    # --------------------------------------------------------

    df = df.rename(
        columns={
            "cost_price": "unit_cost",
            "unit_price": "list_price"
        }
    )

    # --------------------------------------------------------
    # Final Zidio schema
    # --------------------------------------------------------

    final_columns = [
        "sku_id",
        "category",
        "subcategory",
        "launch_date",
        "unit_cost",
        "list_price"
    ]

    df = df[final_columns]

    # --------------------------------------------------------
    # One row per SKU
    # --------------------------------------------------------

    df = (
        df
        .sort_values("sku_id")
        .drop_duplicates(
            subset=["sku_id"],
            keep="first"
        )
    )

    # --------------------------------------------------------
    # Final validation
    # --------------------------------------------------------

    if df["sku_id"].duplicated().any():
        raise ValueError(
            "Duplicate SKU IDs remain."
        )

    if df["unit_cost"].lt(0).any():
        raise ValueError(
            "Negative unit_cost detected."
        )

    if df["list_price"].lt(0).any():
        raise ValueError(
            "Negative list_price detected."
        )

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    save_csv(
        df,
        "sku_master.csv"
    )

    print(
        f"Final SKU master rows: {len(df):,}"
    )

    print(
        "SKUs without observed launch date:",
        df["launch_date"].isna().sum()
    )


# ============================================================
# 3. CALENDAR
# ============================================================

def build_calendar():

    print_header("BUILDING CALENDAR")

    source = RAW_DIR / "promotions.csv"
    check_file(source)

    promotions = pd.read_csv(source)

    required_promo = [
        "promo_id",
        "promo_name",
        "start_date",
        "end_date",
        "discount_pct",
        "promo_type",
        "target_type",
        "target_value"
    ]

    missing = [
        col
        for col in required_promo
        if col not in promotions.columns
    ]

    if missing:
        raise ValueError(
            f"promotions.csv is missing columns: {missing}"
        )

    promotions["start_date"] = pd.to_datetime(
        promotions["start_date"],
        errors="coerce"
    )

    promotions["end_date"] = pd.to_datetime(
        promotions["end_date"],
        errors="coerce"
    )

    promotions = promotions.dropna(
        subset=[
            "promo_name",
            "start_date",
            "end_date"
        ]
    )

    # --------------------------------------------------------
    # Determine calendar date range
    # --------------------------------------------------------

    sales_source = RAW_DIR / "sales_transactions.csv"
    check_file(sales_source)

    sales_dates = pd.read_csv(
        sales_source,
        usecols=["date"]
    )

    sales_dates["date"] = pd.to_datetime(
        sales_dates["date"],
        errors="coerce"
    )

    start_date = sales_dates["date"].min()
    end_date = sales_dates["date"].max()

    if pd.isna(start_date) or pd.isna(end_date):
        raise ValueError(
            "Could not determine sales date range."
        )

    dates = pd.date_range(
        start=start_date,
        end=end_date,
        freq="D"
    )

    calendar = pd.DataFrame({
        "date": dates
    })

    # --------------------------------------------------------
    # Calendar fields
    # --------------------------------------------------------

    iso_calendar = calendar["date"].dt.isocalendar()

    calendar["week"] = (
        iso_calendar.week
        .astype(int)
    )

    calendar["month"] = (
        calendar["date"]
        .dt.month
        .astype(int)
    )

    calendar["season"] = (
        "Q" +
        calendar["date"]
        .dt.quarter
        .astype(str)
    )

    # --------------------------------------------------------
    # Holiday
    #
    # Preserve existing calendar if available.
    # Otherwise use 0 because promotions.csv does not
    # contain holiday information.
    # --------------------------------------------------------

    existing_calendar = (
        PROCESSED_DIR / "calendar.csv"
    )

    if existing_calendar.exists():

        old_calendar = pd.read_csv(
            existing_calendar
        )

        if {
            "date",
            "is_holiday"
        }.issubset(old_calendar.columns):

            old_calendar["date"] = pd.to_datetime(
                old_calendar["date"],
                errors="coerce"
            )

            holiday_map = (
                old_calendar[
                    ["date", "is_holiday"]
                ]
                .drop_duplicates("date")
            )

            calendar = calendar.merge(
                holiday_map,
                on="date",
                how="left"
            )

            calendar["is_holiday"] = (
                pd.to_numeric(
                    calendar["is_holiday"],
                    errors="coerce"
                )
                .fillna(0)
                .astype(int)
            )

        else:
            calendar["is_holiday"] = 0

    else:
        calendar["is_holiday"] = 0

    # --------------------------------------------------------
    # Promotion events
    # --------------------------------------------------------

    def get_promotion_names(day):

        active = promotions[
            (promotions["start_date"] <= day) &
            (promotions["end_date"] >= day)
        ]

        names = (
            active["promo_name"]
            .drop_duplicates()
            .astype(str)
            .tolist()
        )

        if not names:
            return "No Promotion"

        return "; ".join(names)

    calendar["promo_event"] = (
        calendar["date"]
        .apply(get_promotion_names)
    )

    calendar = calendar[
        [
            "date",
            "week",
            "month",
            "season",
            "is_holiday",
            "promo_event"
        ]
    ]

    save_csv(
        calendar,
        "calendar.csv"
    )


# ============================================================
# 4. INVENTORY SNAPSHOTS
# ============================================================

def build_inventory_snapshots():

    print_header("BUILDING INVENTORY SNAPSHOTS")

    source = RAW_DIR / "inventory_snapshot.csv"
    sku_master_source = RAW_DIR / "sku_master.csv"

    check_file(source)
    check_file(sku_master_source)

    df = pd.read_csv(source)

    print(f"Raw rows: {len(df):,}")

    required = [
        "store_id",
        "sku_id",
        "stock_on_hand",
        "reorder_point",
        "safety_stock",
        "last_restock_date"
    ]

    missing = [
        col for col in required
        if col not in df.columns
    ]

    if missing:
        raise ValueError(
            f"inventory_snapshot.csv is missing columns: {missing}"
        )

    # --------------------------------------------------------
    # Clean source data
    # --------------------------------------------------------

    df["sku_id"] = df["sku_id"].astype(str)

    df["last_restock_date"] = pd.to_datetime(
        df["last_restock_date"],
        errors="coerce"
    )

    for column in [
        "stock_on_hand",
        "reorder_point",
        "safety_stock"
    ]:
        df[column] = pd.to_numeric(
            df[column],
            errors="coerce"
        )

    df = df.dropna(
        subset=[
            "sku_id",
            "last_restock_date",
            "stock_on_hand",
            "reorder_point",
            "safety_stock"
        ]
    )

    df = df[
        (df["stock_on_hand"] >= 0) &
        (df["reorder_point"] >= 0) &
        (df["safety_stock"] >= 0)
    ]

    # --------------------------------------------------------
    # Aggregate inventory to date + SKU
    # --------------------------------------------------------

    inventory = (
        df.groupby(
            ["last_restock_date", "sku_id"],
            as_index=False
        )
        .agg(
            on_hand_units=("stock_on_hand", "sum"),
            reorder_point=("reorder_point", "sum"),
            safety_stock=("safety_stock", "sum")
        )
        .rename(
            columns={
                "last_restock_date": "date"
            }
        )
    )

    # --------------------------------------------------------
    # Planning assumptions
    # --------------------------------------------------------

    inventory["lead_time_days"] = 7

    inventory["on_order_units"] = (
        inventory["reorder_point"] -
        inventory["on_hand_units"]
    ).clip(lower=0)

    # --------------------------------------------------------
    # Load all SKUs from SKU master
    # --------------------------------------------------------

    sku_master = pd.read_csv(
        sku_master_source,
        usecols=["sku_id"]
    )

    sku_master["sku_id"] = (
        sku_master["sku_id"].astype(str)
    )

    all_skus = set(
        sku_master["sku_id"]
    )

    inventory_skus = set(
        inventory["sku_id"]
    )

    # --------------------------------------------------------
    # Find SKUs absent from original inventory
    # --------------------------------------------------------

    missing_skus = sorted(
        all_skus - inventory_skus
    )

    print(
        f"SKUs missing from original inventory: "
        f"{len(missing_skus):,}"
    )

    # --------------------------------------------------------
    # Add zero-inventory records
    # --------------------------------------------------------

    if missing_skus:

        latest_date = inventory["date"].max()

        zero_inventory = pd.DataFrame({
            "date": latest_date,
            "sku_id": missing_skus,
            "on_hand_units": 0,
            "on_order_units": 0,
            "lead_time_days": 7,
            "reorder_point": 0
        })

        inventory = pd.concat(
            [
                inventory[
                    [
                        "date",
                        "sku_id",
                        "on_hand_units",
                        "on_order_units",
                        "lead_time_days",
                        "reorder_point"
                    ]
                ],
                zero_inventory
            ],
            ignore_index=True
        )

        print(
            f"Added {len(missing_skus):,} "
            "zero-inventory SKUs."
        )

    # --------------------------------------------------------
    # Final column order
    # --------------------------------------------------------

    inventory = inventory[
        [
            "date",
            "sku_id",
            "on_hand_units",
            "on_order_units",
            "lead_time_days",
            "reorder_point"
        ]
    ]

    inventory = inventory.sort_values(
        ["date", "sku_id"]
    )

    # --------------------------------------------------------
    # Final validation
    # --------------------------------------------------------

    if inventory.isna().sum().sum() != 0:
        raise ValueError(
            "Missing values remain in inventory_snapshots."
        )

    if inventory.duplicated(
        ["date", "sku_id"]
    ).any():
        raise ValueError(
            "Duplicate date + SKU records detected."
        )

    remaining_missing = (
        all_skus -
        set(inventory["sku_id"])
    )

    if remaining_missing:
        raise ValueError(
            f"{len(remaining_missing)} SKU master SKUs "
            "are still missing from inventory."
        )

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    save_csv(
        inventory,
        "inventory_snapshots.csv"
    )

    print(
        f"Final inventory rows: "
        f"{len(inventory):,}"
    )

    print(
        f"Final inventory SKUs: "
        f"{inventory['sku_id'].nunique():,}"
    )


# ============================================================
# 5. FINAL VALIDATION
# ============================================================

def validate_processed_data():

    print_header("FINAL PIPELINE VALIDATION")

    files = [
        "sales_daily.csv",
        "sku_master.csv",
        "calendar.csv",
        "inventory_snapshots.csv"
    ]

    for filename in files:

        path = PROCESSED_DIR / filename

        check_file(path)

        df = pd.read_csv(path)

        print(
            f"{filename}: "
            f"{len(df):,} rows, "
            f"{len(df.columns)} columns"
        )

        if df.isna().sum().sum() > 0:

            print(
                f"WARNING: {filename} "
                "contains missing values."
            )

        else:

            print("Missing values: 0")

    # --------------------------------------------------------
    # Cross-table SKU validation
    # --------------------------------------------------------

    sales = pd.read_csv(
        PROCESSED_DIR / "sales_daily.csv"
    )

    sku = pd.read_csv(
        PROCESSED_DIR / "sku_master.csv"
    )

    inventory = pd.read_csv(
        PROCESSED_DIR / "inventory_snapshots.csv"
    )

    sales_skus = set(
        sales["sku_id"].astype(str)
    )

    master_skus = set(
        sku["sku_id"].astype(str)
    )

    inventory_skus = set(
        inventory["sku_id"].astype(str)
    )

    print(
        "\nSales SKUs missing from master:",
        len(sales_skus - master_skus)
    )

    print(
        "Inventory SKUs missing from master:",
        len(inventory_skus - master_skus)
    )

    print(
        "Master SKUs without inventory:",
        len(master_skus - inventory_skus)
    )

    print_header("PIPELINE COMPLETED")


# ============================================================
# MAIN
# ============================================================

def main():

    print_header(
        "FORESIGHT DATA PIPELINE"
    )

    print(
        f"Raw data directory:\n{RAW_DIR}"
    )

    print(
        f"\nProcessed data directory:\n{PROCESSED_DIR}"
    )

    build_sales_daily()

    build_sku_master()

    build_calendar()

    build_inventory_snapshots()

    validate_processed_data()


if __name__ == "__main__":
    main()