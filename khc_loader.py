"""
KHC Data Loader — reads all KHC CSVs once and pre-aggregates for dashboard callbacks.
"""
import pandas as pd
import numpy as np
import os

KHC = os.path.join(os.path.dirname(__file__), "data", "khc")
def _p(n): return os.path.join(KHC, f"{n}.csv")

print("Loading KHC dimensions...")
dim_brand    = pd.read_csv(_p("dim_brand"))
dim_sku      = pd.read_csv(_p("dim_sku"))
dim_retailer = pd.read_csv(_p("dim_retailer"))
dim_calendar = pd.read_csv(_p("dim_calendar"), parse_dates=["week_start_date"])
dim_market   = pd.read_csv(_p("dim_market"))

print("Loading KHC facts...")
sales     = pd.read_csv(_p("fact_weekly_sales"),      parse_dates=["week_start_date"])
dist      = pd.read_csv(_p("fact_distribution"),      parse_dates=["week_start_date"])
mshare    = pd.read_csv(_p("fact_market_share"),      parse_dates=["week_start_date"])
promo     = pd.read_csv(_p("fact_promotional_events"),parse_dates=["week_start_date"])
shelf     = pd.read_csv(_p("fact_shelf_compliance"))
panel     = pd.read_csv(_p("fact_consumer_panel"))
vol_decomp= pd.read_csv(_p("fact_volume_decomp"))

# ── Enrich tables ───────────────────────────────────────────────────────────
sales = (sales
    .merge(dim_brand[["brand_id","brand_name","segment","business_unit"]], on="brand_id", how="left")
    .merge(dim_sku[["sku_id","sku_name","tier","list_price","is_innovation"]], on="sku_id", how="left")
    .merge(dim_retailer[["retailer_id","retailer_name","channel","khc_account_tier"]], on="retailer_id", how="left")
    .merge(dim_calendar[["fiscal_week","fiscal_quarter","is_holiday_week","holiday_occasion","is_grilling_season"]], on="fiscal_week", how="left")
)

dist = (dist
    .merge(dim_brand[["brand_id","brand_name","business_unit"]], on="brand_id", how="left")
    .merge(dim_sku[["sku_id","sku_name","tier"]], on="sku_id", how="left")
    .merge(dim_retailer[["retailer_id","retailer_name","channel"]], on="retailer_id", how="left")
)

promo = (promo
    .merge(dim_brand[["brand_id","brand_name","business_unit"]], on="brand_id", how="left")
    .merge(dim_sku[["sku_id","sku_name","tier"]], on="sku_id", how="left")
    .merge(dim_retailer[["retailer_id","retailer_name","channel","khc_account_tier"]], on="retailer_id", how="left")
    .merge(dim_calendar[["fiscal_week","is_holiday_week","holiday_occasion"]], on="fiscal_week", how="left")
)

vol_decomp = (vol_decomp
    .merge(dim_brand[["brand_id","brand_name","business_unit"]], on="brand_id", how="left")
    .merge(dim_retailer[["retailer_id","retailer_name"]], on="retailer_id", how="left")
)

mshare = mshare.merge(dim_retailer[["retailer_id","retailer_name"]], on="retailer_id", how="left")

# ── Reference lists ─────────────────────────────────────────────────────────
RETAILERS_LIST  = dim_retailer[["retailer_id","retailer_name"]].values.tolist()
BRANDS_LIST     = dim_brand[["brand_id","brand_name"]].values.tolist()
BUS_LIST        = sorted(dim_brand["business_unit"].unique().tolist())
CATEGORIES_LIST = BUS_LIST
SEGMENTS_LIST   = sorted(dim_brand["segment"].unique().tolist())

# ── Global KPIs ──────────────────────────────────────────────────────────────
TOTAL_NET_SALES    = sales["net_sales"].sum()
TOTAL_PRIOR_SALES  = sales["prior_yr_net_sales"].sum()
YOY_GROWTH_PCT     = (TOTAL_NET_SALES - TOTAL_PRIOR_SALES) / TOTAL_PRIOR_SALES * 100

# Gross margin
TOTAL_GM           = sales["gross_margin"].sum()
GM_PCT             = TOTAL_GM / TOTAL_NET_SALES * 100

# Average ACV across all brands
AVG_ACV            = dist["acv_pct"].mean()

# Promo compliance avg
AVG_COMPLIANCE     = promo["compliance_pct"].mean()

# Top brand by revenue
TOP_BRAND          = sales.groupby("brand_name")["net_sales"].sum().idxmax()

# Volume on promo %
PROMO_VOL_PCT      = sales[sales["is_on_promo"]]["net_sales"].sum() / TOTAL_NET_SALES * 100

# ── Pre-aggregations: Selling Story page ─────────────────────────────────────
# Weekly brand sales trend
sales_weekly_brand = (
    sales.groupby(["fiscal_week","week_start_date","brand_name","business_unit"], as_index=False)
    .agg(net_sales=("net_sales","sum"), prior_yr=("prior_yr_net_sales","sum"),
         units=("units_sold","sum"), gm=("gross_margin","sum"))
)
sales_weekly_brand["yoy_chg_pct"] = (
    (sales_weekly_brand["net_sales"] - sales_weekly_brand["prior_yr"]) / sales_weekly_brand["prior_yr"] * 100
).round(1)

# Brand scorecard (full year)
brand_scorecard = (
    sales.groupby(["brand_id","brand_name","business_unit"], as_index=False)
    .agg(net_sales=("net_sales","sum"), prior_yr=("prior_yr_net_sales","sum"),
         gross_margin=("gross_margin","sum"), units=("units_sold","sum"))
    .merge(dist.groupby("brand_id")[["acv_pct","tdp","velocity_per_tdp"]].mean().round(1).reset_index(), on="brand_id", how="left")
    .merge(dim_brand[["brand_id","yoy_trend","category_market_share_pct"]], on="brand_id", how="left")
)
brand_scorecard["yoy_pct"] = ((brand_scorecard["net_sales"] - brand_scorecard["prior_yr"]) / brand_scorecard["prior_yr"] * 100).round(1)
brand_scorecard["gm_pct"]  = (brand_scorecard["gross_margin"] / brand_scorecard["net_sales"] * 100).round(1)

# Volume decomp waterfall (total, all brands, all retailers)
vol_waterfall = vol_decomp.agg(
    current_net_sales=("current_net_sales","sum"),
    prior_yr_net_sales=("prior_yr_net_sales","sum"),
    distribution_driver=("distribution_driver","sum"),
    velocity_driver=("velocity_driver","sum"),
    price_mix_driver=("price_mix_driver","sum"),
    promo_driver=("promo_driver","sum"),
)

# ── Pre-aggregations: Customer Intelligence page ──────────────────────────────
# Sales by retailer × brand
sales_by_ret_brand = (
    sales.groupby(["retailer_id","retailer_name","brand_id","brand_name","business_unit"], as_index=False)
    .agg(net_sales=("net_sales","sum"), prior_yr=("prior_yr_net_sales","sum"),
         units=("units_sold","sum"), gm=("gross_margin","sum"))
)
sales_by_ret_brand["yoy_pct"] = (
    (sales_by_ret_brand["net_sales"] - sales_by_ret_brand["prior_yr"]) / sales_by_ret_brand["prior_yr"] * 100
).round(1)

# ACV/TDP by retailer × brand
dist_by_ret_brand = (
    dist.groupby(["retailer_id","brand_id","brand_name"], as_index=False)
    .agg(acv_pct=("acv_pct","mean"), tdp=("tdp","mean"),
         velocity=("velocity_per_tdp","mean"), acv_gap=("acv_gap_pct","mean"))
    .round(2)
)

# Promo compliance by retailer
promo_by_ret = (
    promo.groupby(["retailer_id","retailer_name"], as_index=False)
    .agg(avg_compliance=("compliance_pct","mean"),
         avg_lift=("volume_lift_factor","mean"),
         total_events=("promo_id","count"),
         promo_spend=("promo_spend_dollars","sum"))
    .round(2)
)

# Market share by retailer × BU
share_by_ret_bu = (
    mshare[mshare["entity_type"] == "KHC Brand"]
    .groupby(["retailer_id","retailer_name","business_unit"], as_index=False)
    .agg(avg_share=("dollar_share_pct","mean"), yoy_share_chg=("yoy_share_chg","mean"))
    .round(2)
)

# ── Pre-aggregations: Category Review page ───────────────────────────────────
# Market share trend by brand (KHC) and competitor
share_trend = (
    mshare.groupby(["fiscal_week","week_start_date","business_unit","brand_name","entity_type"], as_index=False)
    .agg(dollar_share=("dollar_share_pct","mean"), yoy_chg=("yoy_share_chg","mean"))
)

# Distribution (ACV) by BU × retailer
dist_by_bu_ret = (
    dist.groupby(["business_unit","retailer_id"], as_index=False)
    .agg(avg_acv=("acv_pct","mean"), avg_tdp=("tdp","mean"), avg_velocity=("velocity_per_tdp","mean"))
    .merge(dim_retailer[["retailer_id","retailer_name"]], on="retailer_id")
    .round(2)
)

# Shelf compliance by BU × retailer
shelf_enriched = shelf.merge(dim_retailer[["retailer_id","retailer_name","channel"]], on="retailer_id", how="left")

# ── Pre-aggregations: Trade Promotion page ───────────────────────────────────
promo_by_type_ret = (
    promo.groupby(["retailer_name","promo_type"], as_index=False)
    .agg(events=("promo_id","count"),
         avg_compliance=("compliance_pct","mean"),
         avg_lift=("volume_lift_factor","mean"),
         avg_disc=("actual_discount_pct","mean"),
         total_spend=("promo_spend_dollars","sum"),
         total_incremental=("incremental_units","sum"))
    .round(2)
)

promo_by_brand = (
    promo.groupby(["brand_name","promo_type"], as_index=False)
    .agg(events=("promo_id","count"),
         avg_compliance=("compliance_pct","mean"),
         avg_lift=("volume_lift_factor","mean"),
         total_spend=("promo_spend_dollars","sum"),
         total_incremental=("incremental_units","sum"))
    .round(2)
)

promo_weekly = (
    promo.groupby(["fiscal_week","week_start_date"], as_index=False)
    .agg(events=("promo_id","count"),
         avg_compliance=("compliance_pct","mean"),
         avg_lift=("volume_lift_factor","mean"),
         spend=("promo_spend_dollars","sum"))
    .round(2)
)

# ── Pre-aggregations: Volume Decomp page ────────────────────────────────────
vd_by_brand = (
    vol_decomp.groupby(["brand_id","brand_name","business_unit"], as_index=False)
    .agg(current=("current_net_sales","sum"), prior=("prior_yr_net_sales","sum"),
         dist_driver=("distribution_driver","sum"),
         vel_driver=("velocity_driver","sum"),
         price_driver=("price_mix_driver","sum"),
         promo_driver=("promo_driver","sum"),
         base_vol=("base_volume","sum"),
         incr_vol=("incremental_volume","sum"))
)
vd_by_brand["yoy_pct"] = ((vd_by_brand["current"] - vd_by_brand["prior"]) / vd_by_brand["prior"] * 100).round(1)
vd_by_brand["total_chg"] = (vd_by_brand["current"] - vd_by_brand["prior"]).round(0)

vd_by_retailer = (
    vol_decomp.groupby(["retailer_id","retailer_name"], as_index=False)
    .agg(current=("current_net_sales","sum"), prior=("prior_yr_net_sales","sum"),
         dist_driver=("distribution_driver","sum"),
         vel_driver=("velocity_driver","sum"),
         price_driver=("price_mix_driver","sum"),
         promo_driver=("promo_driver","sum"))
)
vd_by_retailer["yoy_pct"] = ((vd_by_retailer["current"] - vd_by_retailer["prior"]) / vd_by_retailer["prior"] * 100).round(1)

print("KHC data loader ready.")
