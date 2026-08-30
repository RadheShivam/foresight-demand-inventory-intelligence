# FORESIGHT — Data Quality Report

## 1. Objective

This report documents the data-quality validation performed on
the four core FORESIGHT datasets before exploratory data analysis
and demand forecasting.

The validation covers schema, completeness, duplicates, data
types, value validity, and cross-table consistency.

---

## 2. Datasets Validated

| Dataset | Rows | Columns |
|---|---:|---:|
| sales_daily | 4,143,561 | 6 |
| sku_master | 5,000 | 6 |
| calendar | 1,461 | 6 |
| inventory_snapshots | 24,872 | 6 |

---

## 3. Schema Validation

All required columns specified for the four FORESIGHT datasets
are present.

### sales_daily

- date
- sku_id
- units_sold
- revenue
- unit_price
- promo_flag

### sku_master

- sku_id
- category
- subcategory
- launch_date
- unit_cost
- list_price

### calendar

- date
- week
- month
- season
- is_holiday
- promo_event

### inventory_snapshots

- date
- sku_id
- on_hand_units
- on_order_units
- lead_time_days
- reorder_point

Status: PASS

---

## 4. Missing Value Validation

All four processed datasets contain zero missing values in their
required fields.

The calendar `promo_event` field uses "No Promotion" for dates
where no supplied promotion is active.

Status: PASS

---

## 5. Duplicate Validation

Business-key duplicate checks produced zero duplicates.

| Dataset | Business Key | Duplicates |
|---|---|---:|
| sales_daily | date + sku_id | 0 |
| sku_master | sku_id | 0 |
| calendar | date | 0 |
| inventory_snapshots | date + sku_id | 0 |

Status: PASS

---

## 6. Value Validation

### sales_daily

- Negative units_sold: 0
- Negative revenue: 0
- Negative unit_price: 0
- Invalid promo_flag: 0

### sku_master

- Negative unit_cost: 0
- Negative list_price: 0

### calendar

- Invalid is_holiday: 0
- Invalid month: 0
- Invalid week: 0

### inventory_snapshots

- Negative on_hand_units: 0
- Negative on_order_units: 0
- Negative lead_time_days: 0
- Negative reorder_point: 0

Status: PASS

---

## 7. Cross-Table Validation

The following relationships were validated:

- Sales SKUs exist in sku_master.
- Inventory SKUs exist in sku_master.
- All sku_master SKUs have an inventory record after the documented
  inventory completion assumption.
- Sales dates exist in calendar.

Status: PASS

---

## 8. Data Transformation and Assumptions

### Inventory coverage

The original inventory source contained 4,495 unique SKUs while
the SKU master contains 5,000 SKUs.

For the 505 SKUs absent from the original inventory source,
zero-inventory records were added at the latest inventory
snapshot date.

These values are modelling assumptions and are not observed
source inventory values.

### Lead time

A 7-day planning assumption is used where supplier lead-time
information is not available in the source.

### On-order inventory

on_order_units is treated as a planning proxy because observed
purchase-order quantity is not available in the source.

### Promotion events

promo_event is derived from the supplied promotions data using
promotion start and end dates.

Dates without an active promotion are represented as:

No Promotion

---

## 9. Data Quality Conclusion

The four processed FORESIGHT datasets pass the automated
technical validation checks.

The datasets contain the required schema, have no missing
required values, contain no duplicate business keys, and pass
the defined numeric and cross-table validation rules.

The documented assumptions will be carried forward into the
forecasting and inventory-risk stages.

The datasets are ready for Exploratory Data Analysis (D2).