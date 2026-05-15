"""
Shared data loader — CSVs are read once at import time and pre-aggregated.
All pages import from here; nothing reads CSVs inside callbacks.
"""
import os
import pandas as pd
import numpy as np

DATA = os.path.join(os.path.dirname(__file__), "data")

def _p(name): return os.path.join(DATA, f"{name}.csv")

# ── Dimensions ─────────────────────────────────────────────────────────────
print("Loading dimensions...")
dim_item     = pd.read_csv(_p("dim_item"))
dim_store    = pd.read_csv(_p("dim_store"))
dim_calendar = pd.read_csv(_p("dim_calendar"), parse_dates=["date"])
dim_dc       = pd.read_csv(_p("dim_distribution_fulfillment_center"))

CATEGORIES = sorted(dim_item["category_name"].unique().tolist())
REGIONS    = sorted(dim_store["region"].unique().tolist())
STATES     = sorted(dim_store["state"].unique().tolist())

# ── Heavy fact tables ───────────────────────────────────────────────────────
print("Loading store sales...")
_sales_raw = pd.read_csv(_p("fact_store_sales"), parse_dates=["week_start_date"])
_sales_raw = _sales_raw.merge(dim_item[["item_id","category_name"]], on="item_id", how="left")
_sales_raw = _sales_raw.merge(dim_store[["store_id","state","region","store_type","square_footage"]], on="store_id", how="left")

print("Loading store inventory...")
_inv_raw = pd.read_csv(_p("fact_store_inventory"), parse_dates=["snapshot_date"])
_inv_raw = _inv_raw.merge(dim_item[["item_id","category_name"]], on="item_id", how="left")
_inv_raw = _inv_raw.merge(dim_store[["store_id","state","region"]], on="store_id", how="left")

print("Loading clickstream (pre-aggregating)...")
_click_raw = pd.read_csv(_p("fact_clickstream"), parse_dates=["event_date"])

print("Loading remaining facts...")
fact_ecomm_sales   = pd.read_csv(_p("fact_ecomm_sales"), parse_dates=["week_start_date"])
fact_opd           = pd.read_csv(_p("fact_online_pickup_delivery"), parse_dates=["order_date"])
fact_otif          = pd.read_csv(_p("fact_otif"), parse_dates=["order_date","actual_delivery_date"])
fact_po            = pd.read_csv(_p("fact_purchase_order"), parse_dates=["order_date"])
fact_markdown      = pd.read_csv(_p("fact_store_markup_markdown"), parse_dates=["event_date","end_date"])
fact_tender        = pd.read_csv(_p("fact_tender_analysis"), parse_dates=["date"])
fact_pricing       = pd.read_csv(_p("fact_item_pricing"), parse_dates=["effective_date"])

# ── Pre-aggregations ────────────────────────────────────────────────────────

# Weekly sales by category (for trend charts)
sales_weekly_cat = (
    _sales_raw.groupby(["week_start_date","category_name"], as_index=False)
    .agg(net_sales=("net_sales","sum"), gross_margin=("gross_margin","sum"),
         units_sold=("units_sold","sum"), cogs=("cogs","sum"))
)

# Weekly sales by state (for choropleth)
sales_by_state = (
    _sales_raw.groupby("state", as_index=False)
    .agg(net_sales=("net_sales","sum"), gross_margin=("gross_margin","sum"),
         units_sold=("units_sold","sum"))
)

# Top items by revenue
top_items = (
    _sales_raw.groupby(["item_id","category_name"], as_index=False)
    .agg(net_sales=("net_sales","sum"))
    .merge(dim_item[["item_id","item_name"]], on="item_id")
    .nlargest(20, "net_sales")
)

# Weekly sales by store (for store performance page)
sales_by_store_week = (
    _sales_raw.groupby(["week_start_date","store_id","state","region","store_type","square_footage"], as_index=False)
    .agg(net_sales=("net_sales","sum"), gross_margin=("gross_margin","sum"),
         units_sold=("units_sold","sum"), cogs=("cogs","sum"))
)
sales_by_store_week["gross_margin_pct"] = (
    sales_by_store_week["gross_margin"] / sales_by_store_week["net_sales"].replace(0, np.nan) * 100
)
sales_by_store_week["sales_per_sqft"] = (
    sales_by_store_week["net_sales"] / sales_by_store_week["square_footage"].replace(0, np.nan)
)

# Category × store margin
sales_cat_store = (
    _sales_raw.groupby(["store_id","category_name"], as_index=False)
    .agg(net_sales=("net_sales","sum"), gross_margin=("gross_margin","sum"))
)
sales_cat_store["gm_pct"] = (
    sales_cat_store["gross_margin"] / sales_cat_store["net_sales"].replace(0, np.nan) * 100
)

# Inventory: in-stock rate by category
inv_instock = (
    _inv_raw.groupby("category_name", as_index=False)
    .apply(lambda g: pd.Series({
        "in_stock_rate": (g["on_hand_units"] > 0).mean() * 100,
        "avg_dos": g["days_of_supply"].mean(),
        "avg_on_hand": g["on_hand_units"].mean(),
    }), include_groups=False)
    .reset_index(drop=True)
)

# Inventory DOS distribution (sampled for performance)
inv_dos_sample = _inv_raw[["category_name","days_of_supply"]].sample(n=min(50_000, len(_inv_raw)), random_state=42)

# Inventory turns by category (annual COGS / avg on-hand value)
_inv_cat = _inv_raw.groupby("category_name", as_index=False).agg(
    avg_on_hand=("on_hand_units","mean")
)
_sales_cat_total = _sales_raw.groupby("category_name", as_index=False).agg(cogs=("cogs","sum"))
inv_turns = _inv_cat.merge(_sales_cat_total, on="category_name")
inv_turns["inv_turn_rate"] = (
    inv_turns["cogs"] / (inv_turns["avg_on_hand"] * dim_item.groupby("category_name")["unit_cost"].mean().reindex(inv_turns["category_name"]).values)
).fillna(0)

# OTIF by vendor (merge with DC dim for region)
otif_vendor = (
    fact_otif.groupby("vendor_id", as_index=False)
    .agg(total_pos=("otif_id","count"), otif_pct=("otif_flag","mean"),
         fill_rate=("fill_rate_pct","mean"), otif_score=("otif_score","mean"))
)
otif_vendor["otif_pct"] = otif_vendor["otif_pct"] * 100

# OTIF by DC+region
otif_dc = (
    fact_otif.merge(dim_dc[["center_id","region","center_name","center_type"]],
                    left_on="dc_id", right_on="center_id", how="left")
    .groupby(["dc_id","region","center_name"], as_index=False)
    .agg(total_pos=("otif_id","count"), otif_pct=("otif_flag","mean"),
         fill_rate=("fill_rate_pct","mean"), avg_score=("otif_score","mean"))
)
otif_dc["otif_pct"] = otif_dc["otif_pct"] * 100

# KPIs (global, used by executive summary)
TOTAL_NET_SALES   = _sales_raw["net_sales"].sum()
TOTAL_GROSS_MARGIN= _sales_raw["gross_margin"].sum()
GROSS_MARGIN_PCT  = TOTAL_GROSS_MARGIN / TOTAL_NET_SALES * 100 if TOTAL_NET_SALES else 0
TOP_CATEGORY      = _sales_raw.groupby("category_name")["net_sales"].sum().idxmax()
GLOBAL_OTIF_PCT   = fact_otif["otif_flag"].mean() * 100 if len(fact_otif) else 0
INSTOCK_RATE      = (_inv_raw["on_hand_units"] > 0).mean() * 100

# ── Clickstream pre-aggregations ────────────────────────────────────────────

# Funnel totals
click_funnel_totals = (
    _click_raw.groupby("event_type", as_index=False)["event_id"].count()
    .rename(columns={"event_id":"count"})
)

# Weekly conversion trend
_click_weekly = _click_raw.copy()
_click_weekly["week"] = _click_weekly["event_date"].dt.to_period("W").dt.start_time
click_weekly_funnel = (
    _click_weekly.groupby(["week","event_type"], as_index=False)["event_id"].count()
    .rename(columns={"event_id":"count"})
)
_pvw = click_weekly_funnel[click_weekly_funnel["event_type"]=="product_view"].set_index("week")["count"]
_pur = click_weekly_funnel[click_weekly_funnel["event_type"]=="purchase"].set_index("week")["count"]
conversion_trend = pd.DataFrame({
    "week": _pvw.index,
    "product_views": _pvw.values,
    "purchases": _pur.reindex(_pvw.index, fill_value=0).values,
}).assign(conversion_rate=lambda d: d["purchases"] / d["product_views"].replace(0, np.nan) * 100)

# Top search terms
click_search_terms = (
    _click_raw[_click_raw["search_term"].str.len() > 0]
    .groupby("search_term", as_index=False)["event_id"].count()
    .rename(columns={"event_id":"count"})
    .nlargest(15, "count")
)

# Device mix
click_device = (
    _click_raw.groupby("device_type", as_index=False)["event_id"].count()
    .rename(columns={"event_id":"count"})
)

# ── OPD pre-aggregations ────────────────────────────────────────────────────
opd_sla = fact_opd["sla_met"].mean() * 100 if len(fact_opd) else 0
opd_by_type = (
    fact_opd.groupby("fulfillment_type", as_index=False)
    .agg(orders=("order_id","count"), avg_order_total=("order_total","mean"),
         sla_met_pct=("sla_met","mean"), avg_rating=("customer_rating","mean"))
)
opd_by_type["sla_met_pct"] *= 100

# ── Tender pre-aggregations ────────────────────────────────────────────────
tender_mix = (
    fact_tender.groupby("tender_type", as_index=False)
    .agg(total_amount=("total_amount","sum"), transaction_count=("transaction_count","sum"))
)

# ── Markdown pre-aggregations ───────────────────────────────────────────────
markdown_df = fact_markdown.merge(dim_item[["item_id","category_name"]], on="item_id", how="left")
markdown_df = markdown_df.merge(dim_store[["store_id","state","region"]], on="store_id", how="left")

md_by_cat = (
    markdown_df.groupby(["category_name","event_type"], as_index=False)
    .agg(revenue=("revenue_during_event","sum"),
         margin_impact=("margin_impact","sum"),
         avg_depth=("markdown_depth","mean"),
         events=("event_id","count"))
)

md_revenue_by_cat = (
    markdown_df.groupby("category_name", as_index=False)
    .agg(revenue=("revenue_during_event","sum"), events=("event_id","count"),
         avg_depth=("markdown_depth","mean"))
)

# Sample for Gantt (too many rows to show all)
md_gantt_sample = (
    markdown_df[markdown_df["event_type"].isin(["Markdown","Clearance"])]
    .sample(n=min(200, len(markdown_df)), random_state=42)
    [["event_date","end_date","event_type","category_name","store_id","markdown_depth"]]
)

# Pricing: price index vs competitor
pricing_scatter = (
    fact_pricing[fact_pricing["competitor_price"].notna()]
    .merge(dim_item[["item_id","category_name"]], on="item_id", how="left")
    .sample(n=min(3000, len(fact_pricing)), random_state=42)
    [["item_id","category_name","regular_price","competitor_price","price_index","price_type"]]
)

print("Data loader ready.")
