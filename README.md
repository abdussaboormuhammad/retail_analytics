# Retail Analytics Dashboard

A multi-page interactive analytics application built with Python and Plotly Dash. The project explores real-world retail and consumer goods data across four supplier use cases: sales performance, supply chain operations, shopper behavior, and category management. The dashboards are designed to reflect the kinds of questions a retail buyer, category manager, or supply chain analyst would actually ask.

---

## Table of Contents

- [Overview](#overview)
- [Project Structure](#project-structure)
- [Dashboards](#dashboards)
- [Dataset Reference](#dataset-reference)
- [Setup & Installation](#setup--installation)
- [Running the App](#running-the-app)
- [Dependencies](#dependencies)
- [Notes](#notes)

---

## Overview

This project was built to practice working with large, realistic retail datasets and to get hands-on experience with Plotly Dash for interactive data visualization. The data covers a full fiscal year (2024) of simulated Walmart-style store operations, e-commerce activity, and a branded CPG supplier portfolio (modeled after a condiments/beverages company).

The app has four separate dashboard pages, each focused on a different stakeholder:

| Dashboard | Stakeholder | Core Question |
|---|---|---|
| Sales Analytics | Retail Buyer / Sales Team | How is revenue and margin trending across stores, categories, and channels? |
| Supply Chain | Supply Chain Analyst | Are vendors delivering on time and in full? Where are the inventory gaps? |
| Shopper Behavior | Shopper Insights / E-Commerce | How are customers browsing, converting, and paying? What do they search for? |
| Category Manager | CPG Supplier / Category Captain | How is market share moving? Are promotions working? Is the shelf set correctly? |

---

## Project Structure

```
retail_analytics/
│
├── app.py                   # Main Dash app entry point, navbar, routing
├── data_loader.py           # All data loading and pre-aggregation logic
├── requirements.txt
│
├── pages/
│   ├── sales_analytics.py   # Dashboard 1 — Sales
│   ├── supply_chain.py      # Dashboard 2 — Supply Chain
│   ├── shopper_behavior.py  # Dashboard 3 — Shopper Behavior
│   └── category_manager.py  # Dashboard 4 — Category Manager (Supplier)
│
└── data/
    ├── dim_calendar.csv
    ├── dim_item.csv
    ├── dim_store.csv
    ├── dim_distribution_fulfillment_center.csv
    ├── fact_store_sales.csv
    ├── fact_ecomm_sales.csv
    ├── fact_store_inventory.csv
    ├── fact_ecomm_inventory.csv
    ├── fact_otif.csv
    ├── fact_purchase_order.csv
    ├── fact_order_forecast.csv
    ├── fact_store_demand_forecast.csv
    ├── fact_online_pickup_delivery.csv
    ├── fact_tender_analysis.csv
    ├── fact_clickstream.csv
    ├── fact_item_pricing.csv
    ├── fact_store_markup_markdown.csv
    ├── fact_modular_plan.csv
    │
    └── supplier/            # CPG supplier sub-dataset
        ├── dim_brand.csv
        ├── dim_sku.csv
        ├── dim_retailer.csv
        ├── dim_market.csv
        ├── dim_calendar.csv
        ├── fact_weekly_sales.csv
        ├── fact_market_share.csv
        ├── fact_volume_decomp.csv
        ├── fact_promotional_events.csv
        ├── fact_shelf_compliance.csv
        ├── fact_distribution.csv
        └── fact_consumer_panel.csv
```

---

## Dashboards

### 1. Sales Analytics

**Path:** `/`

Covers store and e-commerce revenue performance for FY2024. The main questions here are around which categories and items are driving revenue, how margin looks across the assortment, and how in-store compares to online.

**Charts:**
- Weekly Revenue & Gross Margin % trend (dual-axis line)
- Revenue by Category (horizontal bar, sorted)
- Top 15 Items by Revenue (bar, color-coded by margin)
- In-Store vs E-Commerce revenue over time (stacked area)
- Store Revenue vs Margin scatter by region
- Markdown Event Impact — units sold and markdown depth by event type (clearance, rollback, competition-driven, etc.)

**Filters:** Category dropdown, Region dropdown. Both filters cascade into all charts on the page.

---

### 2. Supply Chain Intelligence

**Path:** `/supply-chain`

Covers vendor delivery performance, inventory health, demand forecasting, and purchase order tracking. This is the dashboard a DC operations analyst or merchandising planner would check weekly.

**Charts:**
- OTIF (On-Time In-Full) trend by week with 95% target line
- Vendor OTIF Scorecard — bottom 15 vendors, color-coded red/amber/green
- Average Days of Supply by Category with 7-day minimum and 14-day target lines
- Out-of-Stock Rate by Category with 15% alert threshold
- Demand Forecast Accuracy — MAPE % and forecast accuracy % over time
- Purchase Order Status donut — Open, Confirmed, Shipped, Received, Cancelled

**Filters:** Vendor dropdown. Filters the OTIF trend and vendor scorecard; inventory and forecast views show all data.

---

### 3. Shopper Behavior Analytics

**Path:** `/shoppers`

Uses clickstream event data, payment tender records, and online fulfillment data to understand how shoppers are browsing, converting, and choosing how to pick up or receive their orders.

**Charts:**
- Purchase Funnel — Search → Page View → Product View → Add to Cart → Checkout (with drop-off %)
- Sessions by Device Type and Referral Source (stacked bar)
- Top 15 Search Terms
- Category Browse vs Purchase Conversion Rate (grouped bar + bubble)
- Payment Tender Mix by dollar volume (donut — Credit, Debit, Cash, EBT/SNAP, Gift Card, Mobile Pay, Check)
- Fulfillment Type performance — order count, SLA attainment rate, and average customer rating

**Filters:** Device type (Mobile / Desktop / Tablet), Referral source (Google Search, Direct, Social Media, Email, Affiliate).

---

### 4. Category Manager — Supplier Portfolio

**Path:** `/category`

This dashboard is from the perspective of a CPG supplier acting as category captain. It covers the branded portfolio (condiments, sauces, beverages, and other segments) across major retail accounts. This is the kind of view a supplier would bring to a joint business planning meeting with a retail buyer.

**Charts:**
- Market Share Trend by Brand over 52 weeks — supplier brands vs competitors (solid vs dashed lines)
- Volume Decomposition Waterfall — breaks YoY sales change into: Base Volume, Distribution, Velocity/Mix, Price, and Promotion drivers
- Promotion ROI Scatter — store compliance rate vs volume lift factor, bubble size = promo spend
- Shelf Compliance by Retailer/Category — Facing Compliance, Planogram Compliance, and On-Shelf Availability side by side with 90% target
- Consumer Panel — Household Penetration % by brand over 12 months
- Distribution ACV Gap Scatter — current ACV % vs ACV gap (opportunity) sized by TDP

**Filters:** Retailer, Business Unit, Brand. All three cascade across charts.

---

## Dataset Reference

### Core Retail (data/)

| File | Description | Rows |
|---|---|---|
| `dim_item.csv` | Item master — category, brand, cost, retail, attributes | 1,000 |
| `dim_store.csv` | Store master — location, type, region, amenities | 50 |
| `dim_calendar.csv` | Date dimension — fiscal week, season, holidays | 366 |
| `dim_distribution_fulfillment_center.csv` | DC/FC attributes — capacity, location, capabilities | 35 |
| `fact_store_sales.csv` | Weekly store-item sales, margin, transactions | 617,824 |
| `fact_ecomm_sales.csv` | Weekly e-commerce sales by item and fulfillment type | 15,600 |
| `fact_store_inventory.csv` | Weekly store-item inventory snapshots, shrink, days of supply | 650,000 |
| `fact_ecomm_inventory.csv` | FC-level e-comm inventory snapshots | 208,000 |
| `fact_otif.csv` | Vendor purchase order delivery performance | 10,538 |
| `fact_purchase_order.csv` | Purchase orders — vendor, DC, item, status, cost | 15,000 |
| `fact_order_forecast.csv` | DC-level demand forecasts with actuals and MAPE | 52,000 |
| `fact_store_demand_forecast.csv` | Store-level demand forecasts and accuracy | 31,200 |
| `fact_online_pickup_delivery.csv` | Online orders — fulfillment type, SLA, customer rating | 150,000 |
| `fact_tender_analysis.csv` | Daily store payment tender breakdown | 128,100 |
| `fact_clickstream.csv` | Web/app event-level browsing and conversion data | 500,000 |
| `fact_item_pricing.csv` | Item price history — regular, sale, clearance | 7,424 |
| `fact_store_markup_markdown.csv` | Markdown events — type, depth, units sold, margin impact | 80,000 |
| `fact_modular_plan.csv` | Planogram assignments — store, item, aisle, shelf position | 15,000 |

### CPG Supplier (data/supplier/)

| File | Description | Rows |
|---|---|---|
| `dim_brand.csv` | Brand master — segment, BU, market share tier, ACV | 18 |
| `dim_sku.csv` | SKU master — size, price, margin, velocity index | 62 |
| `dim_retailer.csv` | Retailer accounts — channel, tier, promo compliance baseline | 10 |
| `dim_market.csv` | State-level market attributes — size, urbanization, income index | 50 |
| `dim_calendar.csv` | Supplier fiscal calendar with seasonality flags | 52 |
| `fact_weekly_sales.csv` | SKU-retailer weekly sales — units, revenue, margin, YoY | 32,233 |
| `fact_market_share.csv` | Weekly category dollar and unit share by brand and retailer | 28,600 |
| `fact_volume_decomp.csv` | YoY volume change decomposed into business drivers | 9,360 |
| `fact_promotional_events.csv` | Promo events — type, discount, compliance, lift, spend | 4,755 |
| `fact_shelf_compliance.csv` | Monthly shelf audits — facings, planogram, OSA, OOS | 1,080 |
| `fact_distribution.csv` | Weekly ACV distribution and TDP by SKU and retailer | 32,240 |
| `fact_consumer_panel.csv` | Monthly household panel — penetration, loyalty, frequency | 216 |

---

## Setup & Installation

**Requires Python 3.9 or higher.**

### 1. Clone the repository

```bash
git clone https://github.com/<your-username>/retail_analytics.git
cd retail_analytics
```

### 2. Create a virtual environment (recommended)

```bash
python3 -m venv venv
source venv/bin/activate        # macOS / Linux
venv\Scripts\activate           # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

## Running the App

```bash
python app.py
```

Then open your browser and go to:

```
http://localhost:8050
```

The first page load takes a few seconds because the larger CSV files (store sales, inventory, clickstream) are read and aggregated into memory on startup. After that, navigating between dashboards and changing filters is fast because everything is cached.

If port 8050 is already in use, change the port at the bottom of `app.py`:

```python
if __name__ == "__main__":
    app.run(debug=True, port=8051)   # change port here
```

---

## Dependencies

| Package | Version | Purpose |
|---|---|---|
| `dash` | ≥ 4.0.0 | Web framework and page routing |
| `dash-bootstrap-components` | ≥ 2.0.0 | Layout grid, cards, navbar |
| `plotly` | ≥ 6.0.0 | All charts |
| `pandas` | ≥ 2.0.0 | Data loading and aggregation |
| `numpy` | ≥ 1.24.0 | Numeric operations |

Install them all at once with:

```bash
pip install -r requirements.txt
```

---

## Notes

- All data is synthetic/simulated. No real customer, transaction, or business data is included.
- The `data_loader.py` module uses a simple module-level dictionary cache so each CSV is only read once per session. If you want to reload data after modifying a CSV, just restart the server.
- The supplier dataset (`data/supplier/`) is a standalone sub-dataset meant to represent a CPG supplier's view of the market, separate from the retailer's internal data.
- Charts use `displayModeBar: False` to keep the UI clean, but you can remove that config option in any page file if you want the Plotly toolbar back.
- `debug=True` is set in `app.py` by default, which enables hot-reloading and the Dash DevTools panel. Set it to `False` for a cleaner experience once you are done exploring.
