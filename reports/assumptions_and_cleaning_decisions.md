1. launch_date
   Derived as the earliest observed sales date for each SKU because
   the raw SKU extract did not contain launch_date.

2. unit_cost
   Mapped from raw cost_price.

3. list_price
   Mapped from raw unit_price.

4. Missing inventory SKUs
   505 SKUs absent from the source inventory extract were represented
   with zero on-hand and zero on-order inventory.

5. lead_time_days
   7-day assumption for generated zero-inventory records.

6. Potential overstock
   >180 days of inventory coverage used as a D2 screening threshold.

7. Potential stockout
   Inventory coverage below lead time used as a D2 screening rule.

8. Promotion impact
   Reported as observational association, not causal impact.