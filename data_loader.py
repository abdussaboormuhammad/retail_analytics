import pandas as pd
import numpy as np
from pathlib import Path

DATA = Path("data")
SUPPLIER = DATA / "supplier"

_CACHE: dict = {}


def _cached(key, fn):
    if key not in _CACHE:
        _CACHE[key] = fn()
    return _CACHE[key]


# ── Dimension helpers ─────────────────────────────────────────────────────────

def _dim_item():
    return pd.read_csv(DATA / "dim_item.csv")[
        ["item_id", "item_name", "category_name", "subcategory", "brand",
         "vendor_id", "is_private_label", "is_perishable", "unit_cost", "unit_retail"]
    ]


def _dim_store():
    return pd.read_csv(DATA / "dim_store.csv")[
        ["store_id", "store_name", "store_type", "city", "state", "region",
         "has_grocery_pickup", "avg_weekly_customers"]
    ]


def _supplier_brands():
    return pd.read_csv(SUPPLIER / "dim_brand.csv")[
        ["brand_id", "brand_name", "segment", "business_unit", "is_category_captain"]
    ]


def _supplier_retailers():
    return pd.read_csv(SUPPLIER / "dim_retailer.csv")[
        ["retailer_id", "retailer_name", "channel", "khc_account_tier"]
    ]


def _supplier_skus():
    return pd.read_csv(SUPPLIER / "dim_sku.csv")[
        ["sku_id", "sku_name", "brand_id", "size", "tier", "list_price",
         "margin_pct", "is_core_item", "velocity_index"]
    ]


# ── Store Sales ───────────────────────────────────────────────────────────────

def get_store_sales():
    def _load():
        df = pd.read_csv(DATA / "fact_store_sales.csv",
                         parse_dates=["week_start_date"])
        df = df.merge(_dim_item(), on="item_id", how="left")
        df = df.merge(_dim_store(), on="store_id", how="left")
        df["month"] = df["week_start_date"].dt.to_period("M").astype(str)
        df["quarter"] = df["week_start_date"].dt.to_period("Q").astype(str)
        df["year"] = df["week_start_date"].dt.year
        return df
    return _cached("store_sales", _load)


def get_sales_weekly_agg():
    """Pre-aggregated weekly totals — fast for trend charts."""
    def _load():
        df = get_store_sales()
        return df.groupby("week_start_date").agg(
            net_sales=("net_sales", "sum"),
            gross_sales=("gross_sales", "sum"),
            gross_margin=("gross_margin", "sum"),
            net_units=("net_units", "sum"),
            num_transactions=("num_transactions", "sum"),
        ).reset_index().assign(
            gross_margin_pct=lambda x: (x["gross_margin"] / x["net_sales"] * 100).round(2)
        )
    return _cached("sales_weekly_agg", _load)


def get_sales_category_agg():
    def _load():
        df = get_store_sales()
        return df.groupby("category_name").agg(
            net_sales=("net_sales", "sum"),
            gross_margin=("gross_margin", "sum"),
            net_units=("net_units", "sum"),
        ).reset_index().assign(
            gross_margin_pct=lambda x: (x["gross_margin"] / x["net_sales"] * 100).round(2)
        ).sort_values("net_sales", ascending=False)
    return _cached("sales_cat_agg", _load)


def get_top_items():
    def _load():
        df = get_store_sales()
        return (df.groupby(["item_id", "item_name", "category_name", "brand"])
                .agg(net_sales=("net_sales", "sum"),
                     net_units=("net_units", "sum"),
                     gross_margin_pct=("gross_margin_pct", "mean"))
                .reset_index()
                .sort_values("net_sales", ascending=False)
                .head(30))
    return _cached("top_items", _load)


def get_store_performance():
    def _load():
        df = get_store_sales()
        return (df.groupby(["store_id", "store_name", "region", "state"])
                .agg(net_sales=("net_sales", "sum"),
                     gross_margin_pct=("gross_margin_pct", "mean"),
                     net_units=("net_units", "sum"))
                .reset_index())
    return _cached("store_perf", _load)


# ── Ecommerce Sales ───────────────────────────────────────────────────────────

def get_ecomm_sales():
    def _load():
        df = pd.read_csv(DATA / "fact_ecomm_sales.csv",
                         parse_dates=["week_start_date"])
        df = df.merge(_dim_item()[["item_id", "category_name", "brand"]], on="item_id", how="left")
        return df
    return _cached("ecomm_sales", _load)


def get_channel_comparison():
    """Weekly store vs ecomm sales for channel split chart."""
    def _load():
        store_wk = get_sales_weekly_agg()[["week_start_date", "net_sales"]].copy()
        store_wk["channel"] = "In-Store"

        ecomm = get_ecomm_sales()
        ecomm_wk = (ecomm.groupby("week_start_date")["net_sales"]
                    .sum().reset_index())
        ecomm_wk["channel"] = "E-Commerce"

        return pd.concat([store_wk, ecomm_wk], ignore_index=True)
    return _cached("channel_comp", _load)


# ── Markdowns ─────────────────────────────────────────────────────────────────

def get_markdowns():
    def _load():
        df = pd.read_csv(DATA / "fact_store_markup_markdown.csv",
                         parse_dates=["event_date", "end_date"])
        df = df.merge(_dim_item()[["item_id", "category_name"]], on="item_id", how="left")
        return df
    return _cached("markdowns", _load)


# ── Supply Chain ──────────────────────────────────────────────────────────────

def get_otif():
    def _load():
        df = pd.read_csv(DATA / "fact_otif.csv",
                         parse_dates=["order_date", "expected_delivery_date",
                                      "actual_delivery_date"])
        df["order_week"] = df["order_date"].dt.to_period("W").apply(lambda p: p.start_time)
        return df
    return _cached("otif", _load)


def get_purchase_orders():
    def _load():
        return pd.read_csv(DATA / "fact_purchase_order.csv",
                           parse_dates=["order_date", "expected_delivery_date"])
    return _cached("po", _load)


def get_store_inventory_agg():
    """Category-level inventory aggregation (avoids loading 650K rows into charts)."""
    def _load():
        df = pd.read_csv(DATA / "fact_store_inventory.csv",
                         parse_dates=["snapshot_date"],
                         usecols=["snapshot_id", "snapshot_date", "store_id", "item_id",
                                  "on_hand_units", "days_of_supply", "reorder_needed",
                                  "shrink_value"])
        df = df.merge(_dim_item()[["item_id", "category_name"]], on="item_id", how="left")
        df["reorder_needed"] = df["reorder_needed"].astype(bool)
        return df.groupby(["snapshot_date", "category_name"]).agg(
            avg_dos=("days_of_supply", "mean"),
            oos_items=("reorder_needed", "sum"),
            total_items=("reorder_needed", "count"),
            total_shrink=("shrink_value", "sum"),
            on_hand_units=("on_hand_units", "sum"),
        ).reset_index().assign(
            oos_rate=lambda x: (x["oos_items"] / x["total_items"] * 100).round(2)
        )
    return _cached("inv_agg", _load)


def get_store_forecast():
    def _load():
        return pd.read_csv(DATA / "fact_store_demand_forecast.csv",
                           parse_dates=["forecast_date"])
    return _cached("store_fc", _load)


def get_ecomm_inventory():
    def _load():
        df = pd.read_csv(DATA / "fact_ecomm_inventory.csv",
                         parse_dates=["snapshot_date"],
                         usecols=["snapshot_id", "snapshot_date", "fulfillment_center_id",
                                  "item_id", "on_hand_units", "days_of_supply",
                                  "reorder_needed", "available_units"])
        df = df.merge(_dim_item()[["item_id", "category_name"]], on="item_id", how="left")
        df["reorder_needed"] = df["reorder_needed"].astype(bool)
        return df
    return _cached("ecomm_inv", _load)


# ── Shopper Behavior ──────────────────────────────────────────────────────────

def get_clickstream_agg():
    """Pre-aggregated clickstream — avoids loading 500K rows per chart call."""
    def _load():
        df = pd.read_csv(DATA / "fact_clickstream.csv",
                         parse_dates=["event_date"],
                         usecols=["event_id", "session_id", "user_id", "event_date",
                                  "event_type", "page_category", "device_type",
                                  "referral_source", "search_term",
                                  "add_to_cart_flag", "purchase_flag",
                                  "time_on_page_sec"])
        df["add_to_cart_flag"] = df["add_to_cart_flag"].astype(bool)
        df["purchase_flag"] = df["purchase_flag"].astype(bool)
        return df
    return _cached("clickstream", _load)


def get_funnel_data():
    def _load():
        df = get_clickstream_agg()
        events = df["event_type"].value_counts()
        steps = ["search", "page_view", "product_view", "add_to_cart", "begin_checkout"]
        labels = ["Search", "Page View", "Product View", "Add to Cart", "Checkout"]
        counts = [events.get(s, 0) for s in steps]
        return pd.DataFrame({"stage": labels, "count": counts})
    return _cached("funnel", _load)


def get_tender():
    def _load():
        return pd.read_csv(DATA / "fact_tender_analysis.csv", parse_dates=["date"])
    return _cached("tender", _load)


def get_fulfillment():
    def _load():
        df = pd.read_csv(DATA / "fact_online_pickup_delivery.csv",
                         parse_dates=["order_date", "fulfillment_date"])
        df["sla_met"] = df["sla_met"].astype(bool)
        return df
    return _cached("fulfillment", _load)


# ── Supplier / Category Manager ───────────────────────────────────────────────

def get_supplier_sales():
    def _load():
        df = pd.read_csv(SUPPLIER / "fact_weekly_sales.csv", parse_dates=["week_start_date"])
        df = (df.merge(_supplier_brands(), on="brand_id", how="left")
                .merge(_supplier_skus(), on="sku_id", how="left", suffixes=("", "_sku"))
                .merge(_supplier_retailers(), on="retailer_id", how="left"))
        return df
    return _cached("supplier_sales", _load)


def get_supplier_market_share():
    def _load():
        df = pd.read_csv(SUPPLIER / "fact_market_share.csv", parse_dates=["week_start_date"])
        df = df.merge(_supplier_retailers(), on="retailer_id", how="left")
        return df
    return _cached("supplier_ms", _load)


def get_supplier_volume_decomp():
    def _load():
        df = pd.read_csv(SUPPLIER / "fact_volume_decomp.csv")
        df = (df.merge(_supplier_brands(), on="brand_id", how="left")
                .merge(_supplier_retailers(), on="retailer_id", how="left"))
        return df
    return _cached("supplier_vd", _load)


def get_supplier_promotions():
    def _load():
        df = pd.read_csv(SUPPLIER / "fact_promotional_events.csv",
                         parse_dates=["week_start_date"])
        df = (df.merge(_supplier_brands(), on="brand_id", how="left")
                .merge(_supplier_retailers(), on="retailer_id", how="left")
                .merge(_supplier_skus()[["sku_id", "sku_name", "size"]], on="sku_id", how="left"))
        return df
    return _cached("supplier_promos", _load)


def get_supplier_shelf():
    def _load():
        df = pd.read_csv(SUPPLIER / "fact_shelf_compliance.csv")
        df = df.merge(_supplier_retailers(), on="retailer_id", how="left")
        return df
    return _cached("supplier_shelf", _load)


def get_supplier_consumer():
    def _load():
        df = pd.read_csv(SUPPLIER / "fact_consumer_panel.csv")
        df = df.merge(_supplier_brands(), on="brand_id", how="left")
        return df
    return _cached("supplier_consumer", _load)


def get_supplier_distribution():
    def _load():
        df = pd.read_csv(SUPPLIER / "fact_distribution.csv", parse_dates=["week_start_date"])
        df = (df.merge(_supplier_brands(), on="brand_id", how="left")
                .merge(_supplier_retailers(), on="retailer_id", how="left")
                .merge(_supplier_skus()[["sku_id", "sku_name", "size"]], on="sku_id", how="left"))
        return df
    return _cached("supplier_dist", _load)


# ── Shared helpers ────────────────────────────────────────────────────────────

def fmt_millions(v):
    if v >= 1_000_000_000:
        return f"${v/1_000_000_000:.1f}B"
    if v >= 1_000_000:
        return f"${v/1_000_000:.1f}M"
    if v >= 1_000:
        return f"${v/1_000:.1f}K"
    return f"${v:.0f}"


def fmt_number(v):
    if v >= 1_000_000:
        return f"{v/1_000_000:.1f}M"
    if v >= 1_000:
        return f"{v/1_000:.1f}K"
    return f"{v:.0f}"
