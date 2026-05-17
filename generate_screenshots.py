"""
Generates static PNG screenshots of every dashboard chart and saves them to
assets/screenshots/. Run once to populate the images used in DASHBOARDS.md.

Usage:
    python generate_screenshots.py
"""
import sys
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import data_loader as dl

OUT = Path("assets/screenshots")
OUT.mkdir(parents=True, exist_ok=True)

W, H = 1100, 480   # standard chart size
W_WIDE, H_WIDE = 1300, 520
W_TALL, H_TALL = 900, 580

P = {
    "blue": "#1565C0", "green": "#2E7D32", "red": "#C62828",
    "amber": "#F57F17", "teal": "#00695C", "purple": "#6A1B9A",
    "navy": "#0D47A1", "orange": "#E65100", "cyan": "#006064",
}
LAYOUT = dict(
    paper_bgcolor="white", plot_bgcolor="white",
    font_family="Inter, Arial, sans-serif", font_size=13,
    xaxis=dict(showgrid=False, zeroline=False),
)
M = dict(l=60, r=40, t=55, b=50)   # default margin, override per chart as needed


def save(fig, name, w=W, h=H):
    path = OUT / f"{name}.png"
    pio.write_image(fig, str(path), width=w, height=h, scale=2)
    print(f"  saved {path.name}")


def title(fig, text):
    fig.update_layout(title=dict(text=text, font=dict(size=15, color="#212529"),
                                  x=0.01, xanchor="left"))


# ─────────────────────────────────────────────────────────────────────────────
# DASHBOARD 1 — SALES ANALYTICS
# ─────────────────────────────────────────────────────────────────────────────
print("\n── Sales Analytics ──")

wk = dl.get_sales_weekly_agg()
fig = go.Figure()
fig.add_trace(go.Scatter(
    x=wk["week_start_date"], y=wk["net_sales"],
    name="Revenue", fill="tozeroy",
    line=dict(color=P["blue"], width=2.5),
    fillcolor="rgba(21,101,192,0.12)",
))
fig.add_trace(go.Scatter(
    x=wk["week_start_date"], y=wk["gross_margin_pct"],
    name="Gross Margin %", yaxis="y2",
    line=dict(color=P["green"], width=2.5, dash="dot"),
))
fig.update_layout(
    **LAYOUT,
    yaxis=dict(title="Revenue ($)", gridcolor="#EEEEEE", zeroline=False,
               tickformat="$,.0f"),
    yaxis2=dict(title="Gross Margin %", overlaying="y", side="right",
                showgrid=False, zeroline=False, ticksuffix="%"),
    legend=dict(orientation="h", y=1.12, x=0),
    hovermode="x unified",
)
title(fig, "Weekly Revenue & Gross Margin % — FY 2024")
save(fig, "sa_trend", W_WIDE, H)

# Revenue by category
cat = dl.get_sales_category_agg().head(12).sort_values("net_sales")
fig = px.bar(cat, x="net_sales", y="category_name", orientation="h",
             color="net_sales", color_continuous_scale="Blues",
             labels={"net_sales": "Revenue ($)", "category_name": ""},
             text=cat["net_sales"].apply(dl.fmt_millions))
fig.update_traces(textposition="outside", textfont_size=12)
fig.update_coloraxes(showscale=False)
fig.update_layout(**LAYOUT, margin=M, xaxis_title=None, yaxis_title=None)
title(fig, "Revenue by Category")
save(fig, "sa_cat_bar", 800, H_TALL)

# Top 15 items
top = dl.get_top_items().head(15).sort_values("net_sales")
short = top["item_name"].str[:38] + "…"
fig = px.bar(top, x="net_sales", y=short, orientation="h",
             color="gross_margin_pct",
             color_continuous_scale=[(0, "#EF9A9A"), (0.5, "#FFF176"), (1, "#A5D6A7")],
             range_color=[20, 45],
             labels={"net_sales": "Revenue ($)", "y": "", "gross_margin_pct": "Margin %"},
             text=top["net_sales"].apply(dl.fmt_millions))
fig.update_traces(textposition="outside", textfont_size=11)
fig.update_layout(**LAYOUT, margin=M, xaxis_title=None, yaxis_title=None,
                  coloraxis_colorbar=dict(title="Margin %", len=0.5,
                                          thickness=14, x=1.01))
title(fig, "Top 15 Items by Revenue  (color = Gross Margin %)")
save(fig, "sa_top_items", W_WIDE, H_TALL)

# Channel comparison
ch = dl.get_channel_comparison()
fig = px.area(ch, x="week_start_date", y="net_sales", color="channel",
              color_discrete_map={"In-Store": P["blue"], "E-Commerce": P["teal"]},
              labels={"net_sales": "Revenue ($)", "week_start_date": "",
                      "channel": "Channel"})
fig.update_layout(**LAYOUT, margin=M, legend=dict(orientation="h", y=1.12, x=0),
                  hovermode="x unified")
title(fig, "In-Store vs E-Commerce Revenue — Weekly")
save(fig, "sa_channel", W_WIDE, H)

# Store scatter
sp = dl.get_store_performance()
fig = px.scatter(sp, x="net_sales", y="gross_margin_pct",
                 color="region", size="net_units",
                 hover_data={"store_name": True, "state": True},
                 labels={"net_sales": "Revenue ($)", "gross_margin_pct": "Gross Margin %",
                         "region": "Region"},
                 color_discrete_sequence=px.colors.qualitative.Set2)
fig.update_layout(**LAYOUT, margin=M, legend=dict(orientation="h", y=1.12, x=0))
title(fig, "Store Revenue vs Gross Margin % by Region  (size = Units)")
save(fig, "sa_store_scatter", W_WIDE, H)

# Markdown impact
md = dl.get_markdowns()
agg = (md.groupby("event_type")
       .agg(avg_depth=("markdown_depth", "mean"),
            total_units=("units_sold_during_event", "sum"))
       .reset_index())
fig = go.Figure()
fig.add_trace(go.Bar(name="Units Sold", x=agg["event_type"], y=agg["total_units"],
                      marker_color=P["blue"]))
fig.add_trace(go.Scatter(name="Avg Markdown Depth %", x=agg["event_type"],
                          y=agg["avg_depth"], mode="markers+lines",
                          marker=dict(size=12, color=P["amber"]),
                          line=dict(color=P["amber"], width=2.5), yaxis="y2"))
fig.update_layout(**LAYOUT, margin=M,
                  yaxis=dict(title="Units Sold", gridcolor="#EEEEEE", zeroline=False),
                  yaxis2=dict(title="Avg Depth %", overlaying="y", side="right",
                               showgrid=False, zeroline=False),
                  legend=dict(orientation="h", y=1.12, x=0))
title(fig, "Markdown Event Impact: Units Sold vs Avg Discount Depth")
save(fig, "sa_markdown", W, H)


# ─────────────────────────────────────────────────────────────────────────────
# DASHBOARD 2 — SUPPLY CHAIN
# ─────────────────────────────────────────────────────────────────────────────
print("\n── Supply Chain ──")

otif = dl.get_otif()
wk_otif = (otif.groupby("order_week")
           .agg(otif_rate=("otif_flag", lambda x: x.mean() * 100),
                on_time=("on_time_flag", lambda x: x.mean() * 100),
                in_full=("in_full_flag", lambda x: x.mean() * 100))
           .reset_index())
fig = go.Figure()
for col, label, color in [
    ("otif_rate", "OTIF %", P["blue"]),
    ("on_time", "On-Time %", P["green"]),
    ("in_full", "In-Full %", P["teal"]),
]:
    fig.add_trace(go.Scatter(x=wk_otif["order_week"], y=wk_otif[col],
                              name=label, line=dict(color=color, width=2.5)))
fig.add_hline(y=95, line_dash="dash", line_color="red", opacity=0.55,
              annotation_text="95% Target", annotation_position="top right")
fig.update_layout(**LAYOUT, margin=M, yaxis_range=[60, 105], yaxis_title="Rate (%)",
                  legend=dict(orientation="h", y=1.12, x=0), hovermode="x unified")
title(fig, "OTIF Performance Trend — Weekly (On-Time · In-Full · Combined)")
save(fig, "sc_otif_trend", W_WIDE, H)

# Vendor scorecard
vend = (otif.groupby("vendor_id")
        .agg(otif_rate=("otif_flag", lambda x: round(x.mean() * 100, 1)),
             fill_rate=("fill_rate_pct", "mean"),
             pos=("otif_flag", "count"))
        .reset_index()
        .nsmallest(15, "otif_rate")
        .sort_values("otif_rate"))
colors = [P["green"] if r >= 95 else P["amber"] if r >= 85 else P["red"]
          for r in vend["otif_rate"]]
fig = go.Figure(go.Bar(x=vend["otif_rate"], y=vend["vendor_id"], orientation="h",
                        marker_color=colors,
                        text=vend["otif_rate"].apply(lambda v: f"{v:.0f}%"),
                        textposition="outside"))
fig.add_vline(x=95, line_dash="dash", line_color="grey", opacity=0.6,
              annotation_text="95% Target")
fig.update_layout(**LAYOUT, margin=M, xaxis_range=[50, 110],
                  xaxis_title="OTIF Rate (%)", yaxis_title=None)
title(fig, "Vendor OTIF Scorecard — Bottom 15 Vendors")
save(fig, "sc_vendor_bar", W, H_TALL)

# Inventory DOS
inv = dl.get_store_inventory_agg()
latest = inv[inv["snapshot_date"] == inv["snapshot_date"].max()]
cat_dos = (latest.groupby("category_name").agg(avg_dos=("avg_dos", "mean"))
           .reset_index().sort_values("avg_dos"))
colors = [P["red"] if d < 7 else P["amber"] if d < 14 else P["green"]
          for d in cat_dos["avg_dos"]]
fig = go.Figure(go.Bar(x=cat_dos["avg_dos"], y=cat_dos["category_name"],
                        orientation="h", marker_color=colors,
                        text=cat_dos["avg_dos"].apply(lambda v: f"{v:.1f}d"),
                        textposition="outside"))
fig.add_vline(x=7, line_dash="dash", line_color="red", opacity=0.5,
              annotation_text="7d Min")
fig.add_vline(x=14, line_dash="dot", line_color="orange", opacity=0.5,
              annotation_text="14d Target")
fig.update_layout(**LAYOUT, margin=M, xaxis_title="Days of Supply", yaxis_title=None)
title(fig, "Avg Days of Supply by Category  (red < 7d · amber < 14d · green ✓)")
save(fig, "sc_inv_dos", W, H_TALL)

# OOS rate
cat_oos = (inv.groupby("category_name").agg(oos_rate=("oos_rate", "mean"))
           .reset_index().sort_values("oos_rate", ascending=False))
fig = px.bar(cat_oos, x="category_name", y="oos_rate",
             color="oos_rate",
             color_continuous_scale=[(0, "#A5D6A7"), (0.4, "#FFF176"), (1, "#EF9A9A")],
             range_color=[0, 30],
             text=cat_oos["oos_rate"].apply(lambda v: f"{v:.1f}%"),
             labels={"oos_rate": "OOS Rate (%)", "category_name": ""})
fig.update_traces(textposition="outside", textfont_size=11)
fig.update_coloraxes(showscale=False)
fig.add_hline(y=15, line_dash="dash", line_color="red", opacity=0.5,
              annotation_text="15% Alert Threshold")
fig.update_layout(**LAYOUT, margin=M, xaxis_title=None, xaxis_tickangle=-30)
title(fig, "Out-of-Stock Rate by Category (%)")
save(fig, "sc_oos_rate", W_WIDE, H)

# Forecast accuracy
fc = dl.get_store_forecast()
wk_fc = (fc.groupby("forecast_date")
         .agg(avg_mape=("mape", "mean"), avg_acc=("forecast_accuracy_pct", "mean"))
         .reset_index())
fig = go.Figure()
fig.add_trace(go.Scatter(x=wk_fc["forecast_date"], y=wk_fc["avg_mape"],
                          name="MAPE %", fill="tozeroy",
                          line=dict(color=P["orange"], width=2.5),
                          fillcolor="rgba(230,81,0,0.1)"))
fig.add_trace(go.Scatter(x=wk_fc["forecast_date"], y=wk_fc["avg_acc"],
                          name="Accuracy %", yaxis="y2",
                          line=dict(color=P["blue"], width=2.5, dash="dot")))
fig.update_layout(**LAYOUT, margin=M,
                  yaxis=dict(title="MAPE %", gridcolor="#EEEEEE", zeroline=False),
                  yaxis2=dict(title="Accuracy %", overlaying="y", side="right",
                               showgrid=False, range=[50, 105]),
                  legend=dict(orientation="h", y=1.12, x=0), hovermode="x unified")
title(fig, "Demand Forecast Accuracy — MAPE % vs Accuracy %")
save(fig, "sc_forecast", W_WIDE, H)

# PO status donut
po = dl.get_purchase_orders()
status_totals = po["po_status"].value_counts().reset_index()
status_totals.columns = ["po_status", "count"]
colors_map = {"Open": P["blue"], "Confirmed": P["teal"], "Shipped": P["amber"],
               "Received": P["green"], "Cancelled": P["red"]}
fig = go.Figure(go.Pie(
    labels=status_totals["po_status"], values=status_totals["count"], hole=0.55,
    marker_colors=[colors_map.get(s, "#999") for s in status_totals["po_status"]],
    textinfo="label+percent", textfont_size=13,
))
fig.add_annotation(text=f"<b>{len(po):,}</b><br>POs", x=0.5, y=0.5,
                   showarrow=False, font_size=15)
fig.update_layout(**LAYOUT, margin=M, showlegend=True,
                  legend=dict(orientation="h", y=-0.08))
title(fig, "Purchase Order Status Distribution")
save(fig, "sc_po_status", 700, 480)


# ─────────────────────────────────────────────────────────────────────────────
# DASHBOARD 3 — SHOPPER BEHAVIOR
# ─────────────────────────────────────────────────────────────────────────────
print("\n── Shopper Behavior ──")

funnel_df = dl.get_funnel_data()
fig = go.Figure(go.Funnel(
    y=funnel_df["stage"], x=funnel_df["count"],
    textinfo="value+percent initial",
    marker=dict(color=[P["blue"], "#1976D2", "#1E88E5", P["teal"], P["green"]]),
    connector=dict(line=dict(color="white", width=2)),
    textfont=dict(size=13),
))
fig.update_layout(**LAYOUT, margin=dict(l=60, r=60, t=55, b=40))
title(fig, "Shopper Purchase Funnel — Search to Checkout")
save(fig, "sh_funnel", 750, H_TALL)

# Device + source stacked bar
cs = dl.get_clickstream_agg()
agg_dev = (cs.groupby(["referral_source", "device_type"]).size()
           .reset_index(name="sessions"))
fig = px.bar(agg_dev, x="referral_source", y="sessions", color="device_type",
             color_discrete_map={"Mobile": P["blue"], "Desktop": P["teal"],
                                  "Tablet": P["amber"]},
             barmode="stack",
             labels={"sessions": "Sessions", "referral_source": "",
                     "device_type": "Device"})
fig.update_layout(**LAYOUT, margin=M, xaxis_title=None,
                  legend=dict(orientation="h", y=1.12, x=0))
title(fig, "Sessions by Referral Source & Device Type")
save(fig, "sh_device_bar", W, H)

# Top search terms
searches = (cs[cs["event_type"] == "search"]["search_term"]
            .dropna().value_counts().head(15).reset_index())
searches.columns = ["term", "count"]
searches = searches.sort_values("count")
fig = px.bar(searches, x="count", y="term", orientation="h",
             color="count", color_continuous_scale="Blues",
             labels={"count": "Search Count", "term": ""},
             text="count")
fig.update_traces(textposition="outside", textfont_size=11)
fig.update_coloraxes(showscale=False)
fig.update_layout(**LAYOUT, margin=M, xaxis_title=None, yaxis_title=None)
title(fig, "Top 15 Search Terms")
save(fig, "sh_search", W, H_TALL)

# Category conversion
cat_agg = (cs.groupby("page_category")
           .agg(views=("event_id", "count"),
                purchases=("purchase_flag", "sum"),
                add_to_cart=("add_to_cart_flag", "sum"))
           .reset_index())
cat_agg["conv_rate"] = (cat_agg["purchases"] / cat_agg["views"] * 100).round(2)
cat_agg["cart_rate"] = (cat_agg["add_to_cart"] / cat_agg["views"] * 100).round(2)
cat_agg = cat_agg.sort_values("conv_rate", ascending=False)
fig = go.Figure()
fig.add_trace(go.Bar(name="Conversion Rate %", x=cat_agg["page_category"],
                      y=cat_agg["conv_rate"], marker_color=P["blue"]))
fig.add_trace(go.Bar(name="Add-to-Cart Rate %", x=cat_agg["page_category"],
                      y=cat_agg["cart_rate"], marker_color=P["teal"]))
fig.update_layout(**LAYOUT, margin=M, barmode="group", xaxis_title=None,
                  yaxis_title="Rate (%)", xaxis_tickangle=-30,
                  legend=dict(orientation="h", y=1.12, x=0))
title(fig, "Category Browse-to-Purchase & Add-to-Cart Conversion Rates")
save(fig, "sh_cat_conv", W_WIDE, H)

# Tender mix donut
tend = dl.get_tender()
tender_agg = (tend.groupby("tender_type").agg(total=("total_amount", "sum"))
              .reset_index().sort_values("total", ascending=False))
colors_tend = [P["blue"], P["teal"], P["green"], P["amber"], P["purple"],
               P["cyan"], P["red"]]
fig = go.Figure(go.Pie(
    labels=tender_agg["tender_type"], values=tender_agg["total"], hole=0.52,
    marker_colors=colors_tend[:len(tender_agg)],
    textinfo="label+percent", textfont_size=12,
))
fig.add_annotation(text="Payment<br>Mix", x=0.5, y=0.5,
                   showarrow=False, font_size=14, font_color="#555")
fig.update_layout(**LAYOUT, margin=dict(l=40, r=40, t=55, b=40), showlegend=False)
title(fig, "Payment Tender Mix — Total Dollar Volume")
save(fig, "sh_tender", 700, 480)

# Fulfillment SLA + rating
ful = dl.get_fulfillment()
ful_agg = (ful.groupby("fulfillment_type")
           .agg(orders=("order_id", "count"),
                sla_rate=("sla_met", lambda x: x.mean() * 100),
                avg_rating=("customer_rating", "mean"))
           .reset_index().sort_values("orders", ascending=False))
fig = go.Figure()
fig.add_trace(go.Bar(name="Order Count", x=ful_agg["fulfillment_type"],
                      y=ful_agg["orders"], marker_color=P["blue"],
                      text=ful_agg["orders"].apply(lambda v: f"{v:,}"),
                      textposition="outside"))
fig.add_trace(go.Scatter(name="SLA Met %", x=ful_agg["fulfillment_type"],
                          y=ful_agg["sla_rate"], mode="markers+lines",
                          marker=dict(size=14, color=P["green"], symbol="diamond"),
                          line=dict(color=P["green"], width=2.5), yaxis="y2"))
fig.add_trace(go.Scatter(name="Avg Rating ★", x=ful_agg["fulfillment_type"],
                          y=ful_agg["avg_rating"], mode="markers+lines",
                          marker=dict(size=12, color=P["amber"]),
                          line=dict(color=P["amber"], width=2.5, dash="dot"),
                          yaxis="y2"))
fig.update_layout(**LAYOUT, margin=M,
                  yaxis=dict(title="Order Count", gridcolor="#EEEEEE", zeroline=False),
                  yaxis2=dict(title="Rate / Rating", overlaying="y", side="right",
                               showgrid=False, range=[0, 110]),
                  legend=dict(orientation="h", y=1.12, x=0), xaxis_title=None)
title(fig, "Fulfillment Type: Order Volume, SLA Attainment & Customer Rating")
save(fig, "sh_fulfillment", W_WIDE, H)


# ─────────────────────────────────────────────────────────────────────────────
# DASHBOARD 4 — CATEGORY MANAGER
# ─────────────────────────────────────────────────────────────────────────────
print("\n── Category Manager ──")

# Market share trend
ms = dl.get_supplier_market_share()
trend = (ms.groupby(["week_start_date", "brand_name"])
         .agg(share=("dollar_share_pct", "mean"))
         .reset_index())
top_brands = (trend.groupby("brand_name")["share"].mean().nlargest(8).index.tolist())
trend = trend[trend["brand_name"].isin(top_brands)]
supplier_brands = ms[ms["entity_type"] != "Competitor"]["brand_name"].unique()
fig = px.line(trend, x="week_start_date", y="share", color="brand_name",
              line_dash=trend["brand_name"].map(
                  lambda b: "solid" if b in supplier_brands else "dot"),
              labels={"share": "Dollar Share %", "week_start_date": "",
                      "brand_name": "Brand"},
              color_discrete_sequence=px.colors.qualitative.Bold)
fig.update_layout(**LAYOUT, margin=M, legend=dict(orientation="h", y=1.16, x=0, font_size=11),
                  hovermode="x unified", yaxis_title="Dollar Share %")
title(fig, "Market Share Trend by Brand — Supplier (solid) vs Competitor (dashed)")
save(fig, "cm_ms_trend", W_WIDE, H)

# Volume decomp waterfall
vd = dl.get_supplier_volume_decomp()
totals = vd[["distribution_driver", "velocity_driver",
              "price_mix_driver", "promo_driver"]].sum()
base = vd["base_volume"].sum()
current = vd["current_net_sales"].sum()
drivers = {
    "Base Volume": base,
    "Distribution": totals["distribution_driver"],
    "Velocity / Mix": totals["velocity_driver"],
    "Price": totals["price_mix_driver"],
    "Promotion": totals["promo_driver"],
}
labels = list(drivers.keys()) + ["Total Net Sales"]
measures = ["absolute"] + ["relative"] * (len(drivers) - 1) + ["total"]
values = list(drivers.values()) + [current]
fig = go.Figure(go.Waterfall(
    orientation="v", measure=measures, x=labels, y=values,
    text=[f"${v:,.0f}" if abs(v) > 50 else "" for v in values],
    textposition="outside", textfont_size=11,
    connector=dict(line=dict(color="#BDBDBD", width=1)),
    increasing=dict(marker_color=P["green"]),
    decreasing=dict(marker_color=P["red"]),
    totals=dict(marker_color=P["navy"]),
))
fig.update_layout(**LAYOUT, margin=dict(l=60, r=40, t=55, b=60),
                  yaxis_title="Net Sales ($)", showlegend=False)
title(fig, "Volume Decomposition Waterfall — YoY Sales Change by Driver")
save(fig, "cm_waterfall", W, H)

# Promo ROI scatter
promos = dl.get_supplier_promotions()
promo_agg = (promos.groupby(["brand_name", "promo_type"])
             .agg(avg_compliance=("compliance_pct", "mean"),
                  avg_lift=("volume_lift_factor", "mean"),
                  total_spend=("promo_spend_dollars", "sum"))
             .reset_index())
fig = px.scatter(promo_agg, x="avg_compliance", y="avg_lift",
                 size="total_spend", color="promo_type",
                 hover_name="brand_name",
                 labels={"avg_compliance": "Compliance Rate (%)",
                          "avg_lift": "Volume Lift Factor",
                          "promo_type": "Promo Type"},
                 size_max=45,
                 color_discrete_sequence=px.colors.qualitative.Set2)
fig.add_hline(y=1.0, line_dash="dash", line_color="grey", opacity=0.5,
              annotation_text="No-Lift Baseline")
fig.add_vline(x=80, line_dash="dash", line_color="grey", opacity=0.5,
              annotation_text="80% Compliance Target")
fig.update_layout(**LAYOUT, margin=M, legend=dict(orientation="h", y=1.12, x=0))
title(fig, "Promo ROI: Store Compliance vs Volume Lift  (bubble = Spend $)")
save(fig, "cm_promo_roi", W_WIDE, H)

# Shelf compliance
shelf = dl.get_supplier_shelf()
shelf_agg = (shelf.groupby(["retailer_name", "business_unit"])
             .agg(facing=("facing_compliance", "mean"),
                  planogram=("planogram_compliance_pct", "mean"),
                  osa=("osa_pct", "mean"))
             .reset_index()
             .sort_values("planogram", ascending=False))
shelf_agg["label"] = shelf_agg["retailer_name"].str[:7] + " / " + shelf_agg["business_unit"].str[:12]
fig = go.Figure()
for col, name, color in [
    ("facing", "Facing Compliance %", P["blue"]),
    ("planogram", "Planogram Compliance %", P["teal"]),
    ("osa", "On-Shelf Availability %", P["green"]),
]:
    fig.add_trace(go.Bar(name=name, x=shelf_agg["label"], y=shelf_agg[col],
                          marker_color=color))
fig.add_hline(y=90, line_dash="dash", line_color="grey", opacity=0.55,
              annotation_text="90% Target")
fig.update_layout(**LAYOUT, margin=M, barmode="group", xaxis_title=None,
                  yaxis_title="Compliance (%)", yaxis_range=[0, 118],
                  xaxis_tickangle=-30,
                  legend=dict(orientation="h", y=1.12, x=0, font_size=11))
title(fig, "Shelf Compliance by Retailer & Category")
save(fig, "cm_shelf", W_WIDE, H_TALL)

# Consumer panel
cons = dl.get_supplier_consumer()
cons = cons.rename(columns={"brand_name_y": "brand_name"})
monthly = (cons.groupby(["month", "brand_name"])
           .agg(penetration=("hh_penetration_pct", "mean"),
                loyalty=("buyer_loyalty_pct", "mean"))
           .reset_index())
top_b = (monthly.groupby("brand_name")["penetration"].mean().nlargest(6).index.tolist())
monthly = monthly[monthly["brand_name"].isin(top_b)]
fig = px.line(monthly.sort_values("month"), x="month", y="penetration",
              color="brand_name",
              labels={"penetration": "HH Penetration %", "month": "Month",
                      "brand_name": "Brand"},
              color_discrete_sequence=px.colors.qualitative.Bold,
              markers=True)
fig.update_layout(**LAYOUT, margin=M,
                  legend=dict(orientation="h", y=1.12, x=0, font_size=10),
                  hovermode="x unified", yaxis_title="HH Penetration %")
title(fig, "Consumer Panel — Household Penetration % by Brand (Monthly)")
save(fig, "cm_consumer", W_WIDE, H)

# Distribution ACV gap
dist = dl.get_supplier_distribution()
latest_dist = dist[dist["week_start_date"] == dist["week_start_date"].max()]
dist_agg = (latest_dist.groupby(["sku_name", "retailer_name"])
            .agg(acv=("acv_pct", "mean"), tdp=("tdp", "sum"), gap=("acv_gap_pct", "mean"))
            .reset_index().sort_values("acv", ascending=False).head(30))
fig = px.scatter(dist_agg, x="acv", y="gap", size="tdp", color="retailer_name",
                 hover_name="sku_name",
                 labels={"acv": "ACV Distribution %",
                          "gap": "ACV Gap % (Opportunity)",
                          "retailer_name": "Retailer"},
                 size_max=30,
                 color_discrete_sequence=px.colors.qualitative.Set2)
fig.update_layout(**LAYOUT, margin=M, legend=dict(orientation="h", y=1.12, x=0, font_size=10))
title(fig, "Distribution ACV Gap — Current Coverage vs Opportunity  (size = TDP)")
save(fig, "cm_dist_gap", W_WIDE, H)


print(f"\n✓ All screenshots saved to {OUT}/")
print(f"  Total files: {len(list(OUT.glob('*.png')))}")
