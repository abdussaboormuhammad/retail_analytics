import dash
from dash import dcc, html, callback, Input, Output
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np

from data_loader import (
    get_supplier_sales, get_supplier_market_share, get_supplier_volume_decomp,
    get_supplier_promotions, get_supplier_shelf, get_supplier_consumer,
    get_supplier_distribution, fmt_millions, fmt_number,
)

dash.register_page(__name__, path="/category", name="Category Manager", order=4)

P = {
    "blue": "#1565C0", "green": "#2E7D32", "red": "#C62828",
    "amber": "#F57F17", "teal": "#00695C", "purple": "#6A1B9A",
    "navy": "#0D47A1", "lime": "#558B2F",
}
CHART_LAYOUT = dict(
    paper_bgcolor="white", plot_bgcolor="white",
    font_family="Inter, system-ui, sans-serif", font_size=12,
    margin=dict(l=10, r=10, t=36, b=10),
    xaxis=dict(showgrid=False, zeroline=False),
    yaxis=dict(gridcolor="#EEEEEE", zeroline=False),
)

# ── Dropdown options ──────────────────────────────────────────────────────────
def _retailer_opts():
    retailers = sorted(get_supplier_market_share()["retailer_name"].dropna().unique())
    return [{"label": "All Retailers", "value": "ALL"}] + [
        {"label": r, "value": r} for r in retailers
    ]


def _bu_opts():
    bus = sorted(get_supplier_sales()["business_unit"].dropna().unique())
    return [{"label": "All Categories", "value": "ALL"}] + [
        {"label": b, "value": b} for b in bus
    ]


def _brand_opts():
    brands = sorted(get_supplier_market_share()["brand_name"].dropna().unique())
    return [{"label": "All Brands", "value": "ALL"}] + [
        {"label": b, "value": b} for b in brands[:12]
    ]


def kpi(title, val, sub, icon, color, delta=None):
    delta_el = html.Div()
    if delta is not None:
        cls = "text-success" if delta >= 0 else "text-danger"
        arrow = "▲" if delta >= 0 else "▼"
        delta_el = html.Div(f"{arrow} {abs(delta):.2f} pts vs prior yr",
                            className=f"small {cls}", style={"fontSize": "0.78rem"})
    return dbc.Card([
        dbc.CardBody([
            dbc.Row([
                dbc.Col(html.I(className=f"bi {icon} fs-2",
                                style={"color": color, "opacity": 0.85}), width="auto"),
                dbc.Col([
                    html.Div(title, className="text-muted small text-uppercase fw-semibold",
                             style={"letterSpacing": "0.05em", "fontSize": "0.72rem"}),
                    html.Div(val, className="fw-bold",
                             style={"fontSize": "1.45rem", "color": "#212529"}),
                    html.Div(sub, className="small text-muted",
                             style={"fontSize": "0.78rem"}),
                    delta_el,
                ]),
            ], align="center", className="g-2"),
        ], className="py-3"),
    ], className="border-0 shadow-sm h-100")


# ── Layout ────────────────────────────────────────────────────────────────────
layout = html.Div([
    dbc.Row([
        dbc.Col([
            html.H4("Category Manager · Supplier Portfolio",
                    className="fw-bold mb-0", style={"color": "#212529"}),
            html.Small("Market Share · Volume Decomposition · Shelf · Promotions · Consumer Panel",
                       className="text-muted"),
        ]),
        dbc.Col([
            dbc.Row([
                dbc.Col(dcc.Dropdown(id="cm-retailer", options=_retailer_opts(),
                                     value="ALL", clearable=False,
                                     style={"fontSize": "0.85rem"}), width=4),
                dbc.Col(dcc.Dropdown(id="cm-bu", options=_bu_opts(),
                                     value="ALL", clearable=False,
                                     style={"fontSize": "0.85rem"}), width=4),
                dbc.Col(dcc.Dropdown(id="cm-brand", options=_brand_opts(),
                                     value="ALL", clearable=False,
                                     style={"fontSize": "0.85rem"}), width=4),
            ]),
        ], width=6),
    ], className="mb-3 align-items-center"),

    # KPI row
    dbc.Row(id="cm-kpis", className="g-3 mb-3"),

    # Row 1: Market share trend + Volume decomposition
    dbc.Row([
        dbc.Col(dbc.Card([
            dbc.CardHeader(html.Span("Market Share Trend by Brand (%)",
                                     className="fw-semibold small")),
            dbc.CardBody(dcc.Graph(id="cm-ms-trend", config={"displayModeBar": False},
                                   style={"height": "290px"})),
        ], className="border-0 shadow-sm"), width=7),

        dbc.Col(dbc.Card([
            dbc.CardHeader(html.Span("Volume Decomposition Waterfall",
                                     className="fw-semibold small")),
            dbc.CardBody(dcc.Graph(id="cm-waterfall", config={"displayModeBar": False},
                                   style={"height": "290px"})),
        ], className="border-0 shadow-sm"), width=5),
    ], className="g-3 mb-3"),

    # Row 2: Promo ROI scatter + Shelf compliance
    dbc.Row([
        dbc.Col(dbc.Card([
            dbc.CardHeader(html.Span("Promotion ROI: Compliance vs Volume Lift",
                                     className="fw-semibold small")),
            dbc.CardBody(dcc.Graph(id="cm-promo-roi", config={"displayModeBar": False},
                                   style={"height": "300px"})),
        ], className="border-0 shadow-sm"), width=6),

        dbc.Col(dbc.Card([
            dbc.CardHeader(html.Span("Shelf Compliance by Retailer & Category",
                                     className="fw-semibold small")),
            dbc.CardBody(dcc.Graph(id="cm-shelf", config={"displayModeBar": False},
                                   style={"height": "300px"})),
        ], className="border-0 shadow-sm"), width=6),
    ], className="g-3 mb-3"),

    # Row 3: Consumer panel + Distribution ACV
    dbc.Row([
        dbc.Col(dbc.Card([
            dbc.CardHeader(html.Span("Consumer Panel: Penetration & Loyalty",
                                     className="fw-semibold small")),
            dbc.CardBody(dcc.Graph(id="cm-consumer", config={"displayModeBar": False},
                                   style={"height": "280px"})),
        ], className="border-0 shadow-sm"), width=6),

        dbc.Col(dbc.Card([
            dbc.CardHeader(html.Span("Distribution ACV % by SKU & Retailer",
                                     className="fw-semibold small")),
            dbc.CardBody(dcc.Graph(id="cm-dist", config={"displayModeBar": False},
                                   style={"height": "280px"})),
        ], className="border-0 shadow-sm"), width=6),
    ], className="g-3"),
])


# ── Callbacks ─────────────────────────────────────────────────────────────────

def _filter_ms(retailer, brand):
    df = get_supplier_market_share()
    if retailer != "ALL":
        df = df[df["retailer_name"] == retailer]
    if brand != "ALL":
        df = df[df["brand_name"] == brand]
    return df


@callback(Output("cm-kpis", "children"),
          Input("cm-retailer", "value"),
          Input("cm-bu", "value"),
          Input("cm-brand", "value"))
def update_kpis(retailer, bu, brand):
    ms = _filter_ms(retailer, brand)
    avg_share = ms["dollar_share_pct"].mean()
    yoy_chg = ms["yoy_share_chg"].mean()

    promos = get_supplier_promotions()
    if retailer != "ALL":
        promos = promos[promos["retailer_name"] == retailer]
    promo_compliance = promos["compliance_pct"].mean()

    dist = get_supplier_distribution()
    if retailer != "ALL":
        dist = dist[dist["retailer_name"] == retailer]
    avg_acv = dist["acv_pct"].mean()

    shelf = get_supplier_shelf()
    if retailer != "ALL":
        shelf = shelf[shelf["retailer_name"] == retailer]
    avg_osa = shelf["osa_pct"].mean()

    cards = [
        kpi("Avg Dollar Share", f"{avg_share:.1f}%",
            "Category market share",
            "bi-pie-chart-fill", P["blue"], delta=yoy_chg),
        kpi("Distribution ACV", f"{avg_acv:.1f}%",
            "% of ACV with distribution",
            "bi-diagram-3-fill", P["teal"]),
        kpi("Promo Compliance", f"{promo_compliance:.1f}%",
            "Stores executing promo",
            "bi-megaphone-fill", P["amber"]),
        kpi("On-Shelf Availability", f"{avg_osa:.1f}%",
            "OSA across shelf audits",
            "bi-shop", P["green"]),
    ]
    return [dbc.Col(c, md=3) for c in cards]


@callback(Output("cm-ms-trend", "figure"),
          Input("cm-retailer", "value"),
          Input("cm-bu", "value"),
          Input("cm-brand", "value"))
def update_ms_trend(retailer, bu, brand):
    df = _filter_ms(retailer, brand)

    trend = (df.groupby(["week_start_date", "brand_name"])
             .agg(share=("dollar_share_pct", "mean"))
             .reset_index())

    top_brands = (trend.groupby("brand_name")["share"].mean()
                  .nlargest(8).index.tolist())
    trend = trend[trend["brand_name"].isin(top_brands)]

    ms_all = get_supplier_market_share()
    supplier_brands = ms_all[ms_all["entity_type"] != "Competitor"]["brand_name"].unique()

    fig = px.line(trend, x="week_start_date", y="share", color="brand_name",
                  line_dash=trend["brand_name"].map(
                      lambda b: "solid" if b in supplier_brands else "dot"),
                  labels={"share": "$ Share %", "week_start_date": "",
                          "brand_name": "Brand"},
                  color_discrete_sequence=px.colors.qualitative.Bold)
    fig.update_layout(**CHART_LAYOUT,
                      legend=dict(orientation="h", y=1.12, x=0, font_size=10),
                      hovermode="x unified",
                      yaxis_title="Dollar Share %")
    return fig


@callback(Output("cm-waterfall", "figure"),
          Input("cm-retailer", "value"),
          Input("cm-bu", "value"),
          Input("cm-brand", "value"))
def update_waterfall(retailer, bu, brand):
    vd = get_supplier_volume_decomp()
    if retailer != "ALL":
        vd = vd[vd["retailer_name"] == retailer]
    if brand != "ALL":
        vd = vd[vd["brand_name"] == brand]

    totals = vd[["distribution_driver", "velocity_driver",
                 "price_mix_driver", "promo_driver"]].sum()

    base = vd["base_volume"].sum()
    drivers = {
        "Base Volume": base,
        "Distribution": totals["distribution_driver"],
        "Velocity/Mix": totals["velocity_driver"],
        "Price": totals["price_mix_driver"],
        "Promotion": totals["promo_driver"],
    }
    current = vd["current_net_sales"].sum()

    labels = list(drivers.keys()) + ["Total"]
    measures = ["absolute"] + ["relative"] * (len(drivers) - 1) + ["total"]
    values = list(drivers.values()) + [current]

    colors = []
    for i, (k, v) in enumerate(drivers.items()):
        if k == "Base Volume":
            colors.append(P["blue"])
        elif v >= 0:
            colors.append(P["green"])
        else:
            colors.append(P["red"])
    colors.append(P["navy"])

    fig = go.Figure(go.Waterfall(
        orientation="v",
        measure=measures,
        x=labels,
        y=values,
        text=[f"${v:,.0f}" if abs(v) > 50 else "" for v in values],
        textposition="outside",
        textfont_size=10,
        connector=dict(line=dict(color="rgb(63,63,63)", width=1)),
        increasing=dict(marker_color=P["green"]),
        decreasing=dict(marker_color=P["red"]),
        totals=dict(marker_color=P["navy"]),
    ))
    fig.update_layout(**CHART_LAYOUT,
                      yaxis_title="Net Sales ($)",
                      showlegend=False)
    return fig


@callback(Output("cm-promo-roi", "figure"),
          Input("cm-retailer", "value"),
          Input("cm-bu", "value"),
          Input("cm-brand", "value"))
def update_promo_roi(retailer, bu, brand):
    promos = get_supplier_promotions()
    if retailer != "ALL":
        promos = promos[promos["retailer_name"] == retailer]
    if brand != "ALL":
        promos = promos[promos["brand_name"] == brand]

    agg = (promos.groupby(["brand_name", "promo_type"])
           .agg(avg_compliance=("compliance_pct", "mean"),
                avg_lift=("volume_lift_factor", "mean"),
                total_spend=("promo_spend_dollars", "sum"),
                total_incremental=("incremental_units", "sum"),
                events=("promo_id", "count"))
           .reset_index())

    roi = agg["total_incremental"] / agg["total_spend"].replace(0, np.nan) * 1000
    agg["roi_per_k"] = roi.fillna(0).round(2)

    fig = px.scatter(agg, x="avg_compliance", y="avg_lift",
                     size="total_spend", color="promo_type",
                     hover_name="brand_name",
                     hover_data={"avg_compliance": ":.1f",
                                 "avg_lift": ":.2f",
                                 "total_spend": ":,.0f",
                                 "roi_per_k": ":.2f"},
                     labels={"avg_compliance": "Compliance Rate (%)",
                              "avg_lift": "Volume Lift Factor",
                              "promo_type": "Promo Type"},
                     size_max=40,
                     color_discrete_sequence=px.colors.qualitative.Set2)
    fig.add_hline(y=1.0, line_dash="dash", line_color="grey", opacity=0.5,
                  annotation_text="No Lift")
    fig.add_vline(x=80, line_dash="dash", line_color="grey", opacity=0.5,
                  annotation_text="80% Target")
    fig.update_layout(**CHART_LAYOUT,
                      legend=dict(orientation="h", y=1.1, x=0))
    return fig


@callback(Output("cm-shelf", "figure"),
          Input("cm-retailer", "value"),
          Input("cm-bu", "value"),
          Input("cm-brand", "value"))
def update_shelf(retailer, bu, brand):
    shelf = get_supplier_shelf()
    if retailer != "ALL":
        shelf = shelf[shelf["retailer_name"] == retailer]
    if bu != "ALL":
        shelf = shelf[shelf["business_unit"] == bu]

    agg = (shelf.groupby(["retailer_name", "business_unit"])
           .agg(facing_comp=("facing_compliance", "mean"),
                planogram_comp=("planogram_compliance_pct", "mean"),
                osa=("osa_pct", "mean"),
                oos=("oos_incidents", "sum"))
           .reset_index()
           .sort_values("planogram_comp", ascending=False))

    agg["label"] = agg["retailer_name"].str[:6] + "/" + agg["business_unit"].str[:10]

    fig = go.Figure()
    for col, name, color in [
        ("facing_comp", "Facing Compliance %", P["blue"]),
        ("planogram_comp", "Planogram Compliance %", P["teal"]),
        ("osa", "On-Shelf Availability %", P["green"]),
    ]:
        fig.add_trace(go.Bar(name=name, x=agg["label"], y=agg[col],
                              marker_color=color))

    fig.add_hline(y=90, line_dash="dash", line_color="grey", opacity=0.5,
                  annotation_text="90% Target")
    fig.update_layout(**CHART_LAYOUT,
                      barmode="group",
                      xaxis_title=None,
                      yaxis_title="Compliance (%)",
                      yaxis_range=[0, 115],
                      xaxis_tickangle=-30,
                      legend=dict(orientation="h", y=1.1, x=0, font_size=10))
    return fig


@callback(Output("cm-consumer", "figure"),
          Input("cm-retailer", "value"),
          Input("cm-bu", "value"),
          Input("cm-brand", "value"))
def update_consumer(retailer, bu, brand):
    cons = get_supplier_consumer()
    if brand != "ALL":
        cons = cons[cons["brand_name"] == brand]
    if bu != "ALL":
        cons = cons[cons["business_unit"] == bu]

    monthly = (cons.groupby(["month", "brand_name"])
               .agg(penetration=("hh_penetration_pct", "mean"),
                    loyalty=("buyer_loyalty_pct", "mean"),
                    freq=("purchase_freq_annual", "mean"),
                    new_buyers=("new_buyer_pct", "mean"),
                    lapsed=("lapsed_buyer_pct", "mean"))
               .reset_index())

    top_brands = (monthly.groupby("brand_name")["penetration"].mean()
                  .nlargest(6).index.tolist())
    monthly = monthly[monthly["brand_name"].isin(top_brands)]

    fig = go.Figure()
    for brand_name in monthly["brand_name"].unique():
        bdf = monthly[monthly["brand_name"] == brand_name].sort_values("month")
        fig.add_trace(go.Scatter(
            x=bdf["month"], y=bdf["penetration"],
            name=f"{brand_name[:15]} (Pen.)",
            mode="lines+markers",
            line=dict(width=2),
        ))

    fig.update_layout(**CHART_LAYOUT,
                      yaxis_title="HH Penetration %",
                      xaxis_title="Month",
                      legend=dict(orientation="h", y=1.12, x=0, font_size=9),
                      hovermode="x unified")
    return fig


@callback(Output("cm-dist", "figure"),
          Input("cm-retailer", "value"),
          Input("cm-bu", "value"),
          Input("cm-brand", "value"))
def update_dist(retailer, bu, brand):
    dist = get_supplier_distribution()
    if retailer != "ALL":
        dist = dist[dist["retailer_name"] == retailer]
    if bu != "ALL":
        dist = dist[dist["business_unit"] == bu]
    if brand != "ALL":
        dist = dist[dist["brand_name"] == brand]

    # Latest week only for clarity
    latest = dist[dist["week_start_date"] == dist["week_start_date"].max()]
    agg = (latest.groupby(["sku_name", "retailer_name"])
           .agg(acv=("acv_pct", "mean"),
                tdp=("tdp", "sum"),
                gap=("acv_gap_pct", "mean"))
           .reset_index()
           .sort_values("acv", ascending=False)
           .head(30))

    agg["sku_short"] = agg["sku_name"].str[:20] + "…"

    fig = px.scatter(agg, x="acv", y="gap",
                     size="tdp", color="retailer_name",
                     hover_name="sku_name",
                     hover_data={"acv": ":.1f", "gap": ":.1f",
                                 "tdp": ":.0f", "retailer_name": False},
                     labels={"acv": "ACV Distribution %",
                              "gap": "ACV Gap % (Opportunity)",
                              "tdp": "TDP", "retailer_name": "Retailer"},
                     size_max=30,
                     color_discrete_sequence=px.colors.qualitative.Set2)
    fig.update_layout(**CHART_LAYOUT,
                      legend=dict(orientation="h", y=1.08, x=0, font_size=10))
    return fig
