# FORESIGHT --- Demand & Inventory Intelligence

**Project:** FORESIGHT --- Demand & Inventory Intelligence\
**Client:** NorthBay Living\
**Role:** Data Scientist & Analytics\
**Program:** Zidio Development --- Data Science & Analytics\
**Current completion:** D1, D2, D3

FORESIGHT is a demand forecasting and inventory intelligence project.
The work converts retail transaction, product, calendar, and inventory
data into analysis-ready datasets, demand insights, and weekly SKU-level
forecasts.

> **Scope covered in this README:** D1 Data Pipeline, D2 Data-quality &
> EDA Insight Memo, and D3 Demand Forecast Model.

------------------------------------------------------------------------

## 1. Project Objective

The project is designed to support better inventory decisions by:

1.  Building a reproducible data pipeline from the provided extracts.
2.  Cleaning and validating the data.
3.  Understanding demand trend, seasonality, SKU concentration, and
    low-demand behavior.
4.  Producing weekly SKU-level demand forecasts.
5.  Comparing a machine-learning forecast against a seasonal-naive
    baseline.
6.  Using rolling-origin backtesting to evaluate forecast performance
    without future-data leakage.

The broader FORESIGHT scope includes demand forecasting, inventory risk
scoring, a dashboard, a deployed scoring service, and an executive
readout. D4 and later stages are outside the scope of this D1--D3
README.

------------------------------------------------------------------------

# D1 --- Data Foundation & Reproducible Pipeline

## 2. D1 Requirements

The project specification defines four acceptance criteria for D1:

1.  Ingest all four extracts and produce analysis-ready data.
2.  Code cleaning steps for missing values, duplicates, and data-type
    fixes rather than handling them manually.
3.  Re-run the pipeline end-to-end from raw files with a single command.
4.  Document key cleaning decisions and their rationale.

## 3. Four Source Extracts

The project uses four provided data extracts:

  -----------------------------------------------------------------------
  Dataset                             Purpose
  ----------------------------------- -----------------------------------
  `sales_transactions.csv`            Raw transaction-level sales data

  `sku_master.csv`                    SKU/product attributes

  `calendar.csv`                      Date, week, month, season, holiday
                                      and promotion information

  `inventory_snapshots.csv`           Inventory position, lead time and
                                      reorder-point information
  -----------------------------------------------------------------------

The target analysis-ready tables follow the project specification:

-   `sales_daily` --- SKU/day demand fact table
-   `sku_master` --- one row per SKU
-   `calendar` --- one row per date
-   `inventory_snapshots` --- periodic SKU inventory position

## 4. Pipeline Implementation

The reproducible pipeline is implemented in:

``` text
src/data_pipeline.py
```

Run the pipeline with:

``` bash
python src/data_pipeline.py
```

The pipeline reads the raw extracts and creates/validates the processed
datasets.

### Generated datasets

``` text
data/
├── raw/
└── processed/
    ├── sales_daily.csv
    ├── sku_master.csv
    ├── calendar.csv
    └── inventory_snapshots.csv
```

## 5. D1 Pipeline Results

The completed pipeline produced:

  Dataset                            Rows   Columns   Missing Values
  --------------------------- ----------- --------- ----------------
  `sales_daily.csv`             4,143,430         6                0
  `sku_master.csv`                  5,000         6                0
  `calendar.csv`                    1,461         6                0
  `inventory_snapshots.csv`        24,872         6                0

Validation results:

-   Sales SKUs missing from SKU master: **0**
-   Inventory SKUs missing from SKU master: **0**
-   Master SKUs without inventory: **0**
-   Final inventory SKU coverage: **5,000**

## 6. Important D1 Cleaning Decisions

### 6.1 Sales column standardization

The raw sales transaction extract uses:

``` text
quantity
total_value
promo_id
```

The pipeline maps these to the analysis-ready concepts required by the
downstream workflow, including:

``` text
units_sold
revenue
promo_flag
```

This keeps the raw source unchanged while producing a consistent
analytical schema.

### 6.2 SKU master column standardization

The raw SKU master contains:

``` text
unit_price
cost_price
```

The pipeline standardizes the analytical fields to the required
concepts:

``` text
unit_cost
list_price
```

The SKU master contains 5,000 unique SKUs.

### 6.3 Missing inventory coverage

The original inventory extract did not contain inventory observations
for all master SKUs.

The pipeline identified:

``` text
505 SKUs
```

missing from the original inventory extract.

To preserve complete SKU coverage, zero-inventory records were added for
those SKUs.

After this correction:

``` text
Final inventory SKUs: 5,000
Master SKUs without inventory: 0
```

This decision treats an SKU with no observed inventory record as having
zero observed inventory rather than silently dropping the SKU from
inventory analysis.

### 6.4 Missing values and validation

Processed datasets were validated after transformation.

Final validation showed:

``` text
Missing values: 0
```

for the four processed outputs.

### 6.5 Large dataset handling

Large raw and processed CSV files are intentionally excluded from Git
tracking.

The project uses `.gitignore` so that large datasets remain available
locally without exceeding GitHub's file-size limits.

The data can be regenerated locally from the raw inputs using the
pipeline.

------------------------------------------------------------------------

# D2 --- Data-quality & Exploratory Data Analysis

## 7. D2 Requirements

The project specification defines four D2 acceptance criteria:

1.  Report data-quality issues and how they were handled.
2.  Show demand patterns including seasonality, trend, top movers, and
    dead stock.
3.  State at least three business-relevant insights in plain language.
4.  Provide charts that are labelled and readable by a non-technical
    reader.

EDA is implemented in:

``` text
notebooks/02_eda.ipynb
```

## 8. Demand Trend Analysis

### Daily Demand

Daily demand shows a long-term upward movement from 2022 through 2025,
together with recurring seasonal peaks and troughs.

The strongest recurring peaks occur toward the end of calendar years,
followed by substantial declines at the beginning of the following year.

### Monthly Demand

Monthly demand confirms a strong annual seasonal pattern.

Demand generally increases through the year, reaches its highest levels
toward the end of the year, and then drops sharply in January.

This demonstrates why seasonal information is important for the
forecasting stage.

## 9. Day-of-Week Demand

Average demand by weekday is relatively stable across Monday through
Sunday.

The weekday pattern is weaker than the annual/monthly seasonal pattern,
indicating that the forecasting problem is driven more strongly by
longer seasonal cycles than by a single dominant weekday.

## 10. Category Demand

Demand is unevenly distributed across categories.

The highest-demand category in the analysis is:

``` text
Personal Care
```

Other major categories include:

-   Stationery & Office
-   Dairy & Bakery
-   Home Care
-   Frozen Foods
-   Grocery
-   Beverages
-   Home & Kitchen
-   Electronics & Accessories
-   Snacks & Confectionery
-   Health & Wellness
-   Apparel & Footwear

This category concentration is relevant when prioritizing inventory and
forecasting decisions.

## 11. SKU Concentration

Demand is concentrated among a relatively small number of SKUs.

  SKU Group     Share of Total Units
  ----------- ----------------------
  Top 1                        6.34%
  Top 5                       10.06%
  Top 10                      12.57%
  Top 20                      15.99%
  Top 50                      21.23%
  Top 100                     26.74%

The top SKU contributes **6.34%** of total units sold.

The top 100 SKUs contribute **26.74%** of total units.

### Business implication

Forecasting errors on high-volume SKUs can have a larger aggregate
impact, so these SKUs should receive particular attention in downstream
planning.

## 12. Low-Demand / Dead-Stock Analysis

The bottom 10% of SKUs contains:

``` text
501 SKUs
```

These SKUs have substantially lower observed demand than the high-volume
SKU group.

The analysis also calculates selling frequency, average on-hand
inventory, and days of stock to identify SKUs that may create inventory
carrying risk.

## 13. Promotion Analysis

The aggregate promotion comparison produced:

``` text
Promotion average demand:      4.4368
Non-promotion average demand:  4.5342
Promotion lift:               -2.15%
```

In this dataset, promotional periods did not produce a positive
aggregate demand lift.

### Business implication

Promotion should not automatically be treated as a positive demand
driver. Its impact should be evaluated at SKU/category level before
being relied upon for forecasting.

## 14. Inventory-Oriented EDA

The D2 analysis combines demand and inventory indicators including:

-   Average daily demand
-   Average on-hand inventory
-   Days of stock
-   Sales frequency
-   Reorder point

The rule-based exploratory classification produced:

  Risk Category           SKU Count   SKU Share
  --------------------- ----------- -----------
  Normal                      3,492      69.84%
  Potential Stockout            862      17.24%
  Potential Overstock           601      12.02%
  Slow Moving                    45       0.90%

These are exploratory D2 classifications and provide context for the
formal risk-scoring work planned for D4.

## 15. D2 Business Insights

### Insight 1 --- Demand is strongly seasonal

Demand repeatedly peaks toward the end of the year and falls sharply at
the beginning of the next year.

**Implication:** Forecasting should explicitly account for seasonal
demand patterns.

### Insight 2 --- A relatively small SKU group drives a large share of demand

The top 100 SKUs account for **26.74%** of total units.

**Implication:** High-volume SKUs should receive priority when
evaluating forecast accuracy and inventory decisions.

### Insight 3 --- Inventory risk is material

The exploratory classification identifies **862 potential stockout
SKUs** and **601 potential overstock SKUs**.

**Implication:** Inventory planning should combine demand forecasts with
inventory position rather than using demand forecasts alone.

### Insight 4 --- Promotion does not guarantee demand lift

Aggregate promotional demand is **2.15% lower** than non-promotional
demand.

**Implication:** Promotion effects should be validated at a more
granular level before being used as a strong forecasting assumption.

------------------------------------------------------------------------

# D3 --- Demand Forecast Model

## 16. D3 Requirements

The project specification defines four D3 acceptance criteria:

1.  Produce a weekly SKU-level forecast over the defined horizon.
2.  Include a seasonal-naive baseline.
3.  Backtest with rolling-origin cross-validation and report WAPE
    against the baseline.
4.  Ensure no data leakage: future information must never enter a
    feature.

## 17. Forecasting Granularity

The forecasting workflow operates at:

``` text
SKU × Week
```

The baseline forecasting dataset contains:

``` text
Baseline rows: 985,000
SKUs: 5,000
```

Date range:

``` text
2022-03-28 to 2025-12-29
```

## 18. Train/Test Split

The final evaluation uses a time-based split:

``` text
Training weeks: 184
Testing weeks: 13

Test start: 2025-10-06
Test end:   2025-12-29
```

The test period is kept after the training period to preserve the
chronological structure of forecasting.

## 19. Feature Engineering

The forecasting workflow uses historical demand features, including lag
variables.

Important lag features include:

``` text
lag_1
lag_4
lag_13
```

The final feature matrix contains:

``` text
X_train: (920000, 13)
X_test:  (65000, 13)
```

The workflow avoids one-hot encoding all 5,000 SKU identifiers because
that approach attempted to create a very large matrix and caused a
memory allocation failure.

The final model uses a compact 13-feature representation instead.

## 20. Seasonal-Naive Baseline

The seasonal-naive model is the required benchmark.

Final test-period results:

``` text
Seasonal-naive WAPE: 0.4115
Seasonal-naive Bias: -7.72%
```

The seasonal-naive forecast provides the reference point that the
machine-learning model must improve upon.

## 21. LightGBM Model

The machine-learning forecasting model uses LightGBM regression.

Final test-period results:

  Metric     Seasonal Naive   LightGBM
  -------- ---------------- ----------
  WAPE               0.4115     0.3126
  Bias               -7.72%      3.85%

### WAPE improvement

``` text
24.03%
```

The LightGBM model therefore reduces WAPE by **24.03%** relative to the
seasonal-naive benchmark on the final test period.

## 22. Rolling-Origin Cross-Validation

Rolling-origin backtesting was performed across four folds.

    Fold Train End    Test Start   Test End         WAPE      Bias
  ------ ------------ ------------ ------------ -------- ---------
       1 2024-12-30   2025-01-06   2025-03-31     0.5092    30.17%
       2 2025-03-31   2025-04-07   2025-06-30     0.3623   -10.01%
       3 2025-06-30   2025-07-07   2025-09-29     0.3512    -2.90%
       4 2025-09-29   2025-10-06   2025-12-29     0.4115    -7.72%

Mean rolling-origin baseline performance:

``` text
Mean WAPE: 0.4086
Mean Bias: 2.39%
```

## 23. Rolling-Origin LightGBM Performance

The LightGBM model achieved:

``` text
Mean rolling-origin WAPE: 0.2768
Mean rolling-origin Bias: -0.71%
```

Comparison:

  Metric                Baseline   LightGBM
  ------------------- ---------- ----------
  Mean Rolling WAPE       0.4086     0.2768
  Mean Rolling Bias        2.39%     -0.71%
  WAPE Improvement           ---     32.25%

### Interpretation

The rolling-origin evaluation shows that LightGBM provides a substantial
improvement over the seasonal-naive benchmark across multiple historical
evaluation windows.

The mean rolling bias of **-0.71%** is also close to zero, indicating
limited systematic over- or under-forecasting on average across the
rolling folds.

## 24. Leakage Control

The forecasting workflow is time-ordered.

Feature construction uses historical observations and lagged demand
rather than future-period actual demand.

The test period is held out chronologically, and rolling-origin
validation repeatedly trains on earlier periods before evaluating the
following period.

This is consistent with the requirement that future information must not
enter forecasting features.

------------------------------------------------------------------------

# 25. D1--D3 Final Status

  Deliverable                               Requirement Status
  ----------------------------------------- --------------------
  D1 --- Four source extracts ingested      ✅
  D1 --- Coded cleaning and validation      ✅
  D1 --- Single-command pipeline            ✅
  D1 --- Cleaning decisions documented      ✅
  D2 --- Data-quality handling documented   ✅
  D2 --- Trend analysis                     ✅
  D2 --- Seasonality analysis               ✅
  D2 --- Top movers / SKU concentration     ✅
  D2 --- Low-demand / dead-stock analysis   ✅
  D2 --- At least 3 business insights       ✅
  D2 --- Labelled EDA charts                ✅
  D3 --- Weekly SKU-level forecast          ✅
  D3 --- Seasonal-naive baseline            ✅
  D3 --- Rolling-origin CV                  ✅
  D3 --- WAPE comparison                    ✅
  D3 --- Leakage control                    ✅

------------------------------------------------------------------------

# 26. Repository Structure

``` text
foresight-demand-inventory-intelligence/
│
├── app/
│
├── data/
│   ├── raw/
│   └── processed/
│
├── notebooks/
│   └── 02_eda.ipynb
│
├── reports/
│
├── service/
│
├── src/
│   └── data_pipeline.py
│
├── tests/
│
├── .gitignore
├── LICENSE
├── requirements.txt
└── README.md
```

Large datasets are excluded from Git tracking and remain local.

------------------------------------------------------------------------

# 27. Reproducibility

Create the virtual environment:

``` bash
python -m venv .venv
```

Activate it on Windows:

``` powershell
.venv\Scripts\activate
```

Install dependencies:

``` bash
pip install -r requirements.txt
```

Run the data pipeline:

``` bash
python src/data_pipeline.py
```

The pipeline regenerates the processed datasets from the available raw
data.

Run the EDA notebook:

``` text
notebooks/02_eda.ipynb
```

The forecasting workflow should be executed using the project's D3
notebook/model workflow after the processed datasets have been
generated.

------------------------------------------------------------------------

# 28. Evaluation Metrics

## WAPE

Weighted Absolute Percentage Error is the primary forecasting accuracy
metric.

It is preferred for this project because it is more robust than MAPE
when SKU demand can be very low or close to zero.

## Bias

Bias measures signed forecast error and indicates whether the model
systematically over-forecasts or under-forecasts.

## Seasonal-Naive Baseline

The seasonal-naive model predicts demand using the corresponding
seasonal historical period and provides the required benchmark.

## Rolling-Origin Cross-Validation

Rolling-origin validation repeatedly trains on the past and evaluates
the next period, more closely representing how the model would operate
in production.

------------------------------------------------------------------------

# 29. Technologies

-   Python
-   pandas
-   NumPy
-   scikit-learn
-   LightGBM
-   Matplotlib
-   Jupyter Notebook
-   Git
-   GitHub

------------------------------------------------------------------------

# 30. Project Progress

``` text
D1 — Data Foundation & Pipeline
✅ Complete

D2 — Data-quality & EDA Insight Memo
✅ Complete

D3 — Demand Forecast Model
✅ Complete

D4 — Risk Scoring
⏳ Next

D5 — Planning Dashboard
⏳ Pending
```

------------------------------------------------------------------------

# 31. Next Stage

The next stage is **D4 --- Risk Scoring & Decisioning**.

D4 will extend the forecasting output into actionable inventory
decisions by scoring stockout and overstock risk for every SKU,
attaching recommended actions and rupee value at stake, and reconciling
the results with the project's decisioning framework.

------------------------------------------------------------------------

## Project Completion Through D3

**D1 + D2 + D3 completed.**

The current D3 model demonstrates:

``` text
Final test WAPE improvement: 24.03%
Rolling CV WAPE improvement: 32.25%
Mean rolling LightGBM bias: -0.71%
```

The project is ready to proceed to D4.




# D4 — Inventory Risk Scoring

D4 combines the 13-week LightGBM forecast with the latest available
inventory position for every SKU.

## Risk Logic

### Stockout Risk
Forecast demand during lead time is compared with:

```text
on_hand_units + on_order_units