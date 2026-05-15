# Retail Analytics — Walmart-Style Data Model

Synthetic dataset covering **one full year (2024)**, **1,000 items** across **10 categories**,
**50 stores** (one per US state), **10 fulfillment centers**, and **25 distribution centers**.

---

## Dataset Inventory

| # | File | Type | Rows | Description |
|---|------|------|------|-------------|
| 1 | `dim_calendar.csv` | Dimension | 366 | Day-level calendar with fiscal, holiday, season flags |
| 2 | `dim_item.csv` | Dimension | 1,000 | Item master: category, brand, cost, retail, attributes |
| 3 | `dim_store.csv` | Dimension | 50 | Store master: state, type, sq ft, services |
| 4 | `dim_distribution_fulfillment_center.csv` | Dimension | 35 | 25 DCs + 10 FCs: capacity, region, cold storage |
| 5 | `fact_item_pricing.csv` | Fact | ~7,400 | Price records per item: regular, rollback, clearance |
| 6 | `fact_store_sales.csv` | Fact | ~618,000 | Weekly store × item sales, returns, margin |
| 7 | `fact_ecomm_sales.csv` | Fact | ~15,600 | Weekly ecomm sales by item and fulfillment type |
| 8 | `fact_store_inventory.csv` | Fact | 650,000 | Weekly store × item on-hand, shrink, days of supply |
| 9 | `fact_ecomm_inventory.csv` | Fact | 208,000 | Weekly FC × item available, reserved, in-transit |
| 10 | `fact_online_pickup_delivery.csv` | Fact | 150,000 | Order-level OPD with SLA, rating, fulfillment type |
| 11 | `fact_modular_plan.csv` | Fact | 15,000 | Planogram: store × item shelf placement |
| 12 | `fact_order_forecast.csv` | Fact | 52,000 | Weekly DC order forecast vs actual, MAPE |
| 13 | `fact_purchase_order.csv` | Fact | 15,000 | PO header: vendor, DC, item, cost, status |
| 14 | `fact_otif.csv` | Fact | ~10,500 | OTIF by PO: on-time, in-full, fill-rate |
| 15 | `fact_store_demand_forecast.csv` | Fact | 31,200 | Weekly store × item demand forecast vs actual |
| 16 | `fact_store_markup_markdown.csv` | Fact | 80,000 | Markdown/rollback events: depth, duration, revenue impact |
| 17 | `fact_tender_analysis.csv` | Fact | 128,100 | Daily store × tender type transaction counts and amounts |
| 18 | `fact_clickstream.csv` | Fact | 500,000 | Session-level web/app events: page views, cart, purchase |

---

## Data Model (Star / Snowflake Schema)

```
                          ┌───────────────────────┐
                          │    dim_calendar        │
                          │  PK: date_key / date   │
                          └──────────┬────────────-┘
                                     │ date
         ┌───────────────────────────┼─────────────────────────────────┐
         │                           │                                 │
         ▼                           ▼                                 ▼
┌─────────────────┐      ┌──────────────────────┐        ┌─────────────────────┐
│ fact_store_sales│      │ fact_tender_analysis │        │ fact_clickstream    │
│  store_id  ──────────► dim_store              │        │  item_id ──────────►│
│  item_id   ──────────► dim_item               │        │  (session,user,event)│
│  week_start_date│      │  store_id            │        └─────────────────────┘
│  units_sold     │      │  tender_type         │
│  gross_sales    │      │  transaction_count   │
│  net_sales      │      │  total_amount        │
│  cogs           │      └──────────────────────┘
│  gross_margin   │
└─────────────────┘
         ▲ store_id, item_id
         │
┌────────┴────────────────────────────────────────────────────────┐
│                         dim_item (PK: item_id)                  │
│  category_id · category_name · subcategory · brand · vendor_id  │
│  unit_cost · unit_retail · is_perishable · is_private_label     │
└─────────────────────────────────────────────────────────────────┘
         ▲ item_id referenced by ALL fact tables
         │
┌────────┴────────────────────────────────────────────────────────┐
│                        dim_store (PK: store_id)                 │
│  state · region · district · store_type · square_footage        │
│  has_pharmacy · has_grocery_pickup · avg_weekly_customers        │
└─────────────────────────────────────────────────────────────────┘
         ▲ store_id referenced by store-level facts
         │
┌────────┴───────────────────────────────────────────────────────────┐
│         dim_distribution_fulfillment_center (PK: center_id)        │
│  center_type (DC / FC) · region · capacity_pallets · has_cold      │
└────────────────────────────────────────────────────────────────────┘
         ▲ center_id (as dc_id / fulfillment_center_id) referenced by
         │   purchase order, OTIF, order forecast, ecomm inventory,
         │   online pickup/delivery
```

### Entity Relationship Summary

```
dim_item ──────────────────────────────────────────────────────────────┐
  │ item_id                                                             │
  ├──► fact_store_sales          (store_id, item_id, week_start_date)  │
  ├──► fact_ecomm_sales          (item_id, week_start_date)            │
  ├──► fact_store_inventory      (store_id, item_id, snapshot_date)    │
  ├──► fact_ecomm_inventory      (fc_id, item_id, snapshot_date)       │
  ├──► fact_item_pricing         (item_id, effective_date)             │
  ├──► fact_modular_plan         (store_id, item_id, effective_date)   │
  ├──► fact_order_forecast       (store_id, item_id, dc_id, week)      │
  ├──► fact_purchase_order       (vendor_id, dc_id, item_id)           │
  ├──► fact_store_demand_forecast(store_id, item_id, week)             │
  ├──► fact_store_markup_markdown(store_id, item_id, event_date)       │
  ├──► fact_online_pickup_delivery(store_id/fc_id, item_id)            │
  └──► fact_clickstream          (item_id, session_id, event_type)     │

dim_store ─────────────────────────────────────────────────────────────┤
  │ store_id                                                            │
  ├──► fact_store_sales                                                 │
  ├──► fact_store_inventory                                             │
  ├──► fact_modular_plan                                                │
  ├──► fact_order_forecast                                              │
  ├──► fact_store_demand_forecast                                       │
  ├──► fact_store_markup_markdown                                       │
  ├──► fact_online_pickup_delivery                                      │
  └──► fact_tender_analysis                                             │

dim_distribution_fulfillment_center ───────────────────────────────────┤
  │ center_id                                                           │
  ├──► fact_ecomm_inventory      (as fulfillment_center_id)            │
  ├──► fact_ecomm_sales          (as fulfillment_center_id)            │
  ├──► fact_online_pickup_delivery(as fulfillment_center_id)           │
  ├──► fact_purchase_order       (as dc_id)                            │
  ├──► fact_otif                 (as dc_id)                            │
  └──► fact_order_forecast       (as dc_id)                            │

dim_calendar ──────────────────────────────────────────────────────────┘
  │ date / date_key
  └──► joins to any date column in any fact table
       (week_start_date, snapshot_date, order_date, event_date, etc.)

fact_purchase_order ──► fact_otif   (via po_number)
```

---

## Key Metrics & KPIs by Domain

### Store Sales
- **Gross Sales** = `units_sold × unit_retail`
- **Net Sales** = `gross_sales − (units_returned × unit_retail)`
- **Gross Margin %** = `(net_sales − cogs) / net_sales × 100`
- **Comp Store Sales Growth** = YoY net sales change per store
- **Sales per Sq Ft** = `net_sales / square_footage`

### Inventory
- **Days of Supply (DOS)** = `on_hand_units / avg_daily_sales`
- **In-Stock Rate** = `% of store × item combos with on_hand > 0`
- **Shrink Rate** = `shrink_value / (on_hand_units × unit_retail)`
- **Inventory Turns** = `annual COGS / avg_on_hand_value`

### Supply Chain
- **OTIF %** = `orders where on_time_flag AND in_full_flag / total orders`
- **Fill Rate %** = `received_units / expected_units × 100`
- **Forecast Accuracy** = `100 − MAPE`
- **Lead Time Adherence** = `% POs delivered within lead_time_days`

### eCommerce
- **Conversion Rate** = `purchase events / product_view events` (clickstream)
- **Cart Abandonment Rate** = `add_to_cart − purchase / add_to_cart`
- **Average Order Value (AOV)** = `gross_sales / num_orders`
- **SLA Achievement %** = `orders where sla_met = true / total orders`

### Pricing & Markdowns
- **Price Index** = `our_price / competitor_price`
- **Markdown Depth %** = `abs(change_pct)`
- **Markdown ROI** = `revenue_during_event / (markdown_depth × original_price × units)`
- **Rollback Lift** = `units sold during rollback vs baseline`

### Tender
- **Tender Mix %** per type vs total store revenue
- **Avg Transaction Value** by tender type
- **EBT Penetration %** as proxy for customer demographics

---

## How to Join Tables (Examples)

```sql
-- Weekly store sales enriched with item and store attributes
SELECT
    s.week_start_date,
    st.state,
    st.store_type,
    i.category_name,
    i.brand,
    SUM(s.net_sales)     AS net_sales,
    SUM(s.gross_margin)  AS gross_margin,
    SUM(s.units_sold)    AS units_sold
FROM fact_store_sales s
JOIN dim_store  st ON st.store_id = s.store_id
JOIN dim_item    i ON i.item_id   = s.item_id
JOIN dim_calendar c ON c.date     = s.week_start_date
GROUP BY 1,2,3,4,5;

-- OTIF performance by vendor and DC
SELECT
    o.vendor_id,
    d.center_name,
    d.region,
    COUNT(*)                        AS total_pos,
    AVG(o.otif_score)               AS avg_otif_score,
    SUM(o.short_units)              AS total_short_units,
    AVG(o.fill_rate_pct)            AS avg_fill_rate
FROM fact_otif o
JOIN fact_purchase_order po ON po.po_number = o.po_number
JOIN dim_distribution_fulfillment_center d ON d.center_id = o.dc_id
GROUP BY 1,2,3;

-- eComm funnel from clickstream
SELECT
    event_date,
    SUM(CASE WHEN event_type='product_view'  THEN 1 END) AS pdp_views,
    SUM(CASE WHEN event_type='add_to_cart'   THEN 1 END) AS atc,
    SUM(CASE WHEN event_type='purchase'      THEN 1 END) AS purchases,
    ROUND(SUM(CASE WHEN event_type='purchase' THEN 1 END)
          / NULLIF(SUM(CASE WHEN event_type='product_view' THEN 1 END),0)*100,2)
        AS conversion_rate_pct
FROM fact_clickstream
GROUP BY 1
ORDER BY 1;
```
