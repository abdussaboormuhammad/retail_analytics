import dash
from dash import dcc, html, callback, Input, Output
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np

from data_loader import (
    get_otif, get_purchase_orders, get_store_inventory_agg,
    get_store_forecast, get_ecomm_inventory, fmt_number,
)

dash.register_page(__name__, path="/supply-chain", name="Supply Chain", order=2)

P = {
    "blue": "#1565C0", "green": "#2E7D32", "red": "#C62828",
    "amber": "#F57F17", "orange": "#E65100", "teal": "#00695C",
}
CHART_LAYOUT = dict(
    paper_bgcolor="white", plot_bgcolor="white",
    font_family="Inter, system-ui, sans-serif", font_size=12,
    margin=dict(l=10, r=10, t=36, b=10),
    xaxis=dict(showgrid=False, zeroline=False),
    yaxis=dict(gridcolor="#EEEEEE", zeroline=False),
)

# ── KPI helper ────────────────────────────────────────────────────────────────
def kpi(title, val, sub, icon, color, alert=False):
    border = "border-danger" if alert else "border-0"
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
                    html.Div(sub, className="small text-muted", style={"fontSize": "0.78rem"}),
                ]),
            ], align="center", className="g-2"),
        ], className="py-3"),
    ], className=f"{border} shadow-sm h-100")


# ── Vendor options ────────────────────────────────────────────────────────────
def _vendor_opts():
    vendors = sorted(get_otif()["vendor_id"].unique())
    return [{"label": "All Vendors", "value": "ALL"}] + [
        {"label": v, "value": v} for v in vendors[:30]
    ]


layout = html.Div([
    dbc.Row([
        dbc.Col([
            html.H4("Supply Chain Intelligence", className="fw-bold mb-0",
                    style={"color": "#212529"}),
            html.Small("OTIF · Inventory Health · Demand Forecast · PO Tracking",
                       className="text-muted"),
        ]),
        dbc.Col(
            dcc.Dropdown(id="sc-vendor-filter", options=_vendor_opts(),
                         value="ALL", clearable=False,
                         style={"fontSize": "0.85rem"}),
            width=3,
        ),
    ], className="mb-3 align-items-center"),

    # KPI row
    dbc.Row(id="sc-kpis", className="g-3 mb-3"),

    # Row 1: OTIF trend + Vendor scorecard
    dbc.Row([
        dbc.Col(dbc.Card([
            dbc.CardHeader(html.Span("OTIF Performance Trend (Weekly)",
                                     className="fw-semibold small")),
            dbc.CardBody(dcc.Graph(id="sc-otif-trend", config={"displayModeBar": False},
                                   style={"height": "280px"})),
        ], className="border-0 shadow-sm"), width=7),

        dbc.Col(dbc.Card([
            dbc.CardHeader(html.Span("Top Vendor OTIF Scorecard",
                                     className="fw-semibold small")),
            dbc.CardBody(dcc.Graph(id="sc-vendor-bar", config={"displayModeBar": False},
                                   style={"height": "280px"})),
        ], className="border-0 shadow-sm"), width=5),
    ], className="g-3 mb-3"),

    # Row 2: Inventory health + OOS trend
    dbc.Row([
        dbc.Col(dbc.Card([
            dbc.CardHeader(html.Span("Avg Days of Supply by Category",
                                     className="fw-semibold small")),
            dbc.CardBody(dcc.Graph(id="sc-inv-dos", config={"displayModeBar": False},
                                   style={"height": "300px"})),
        ], className="border-0 shadow-sm"), width=6),

        dbc.Col(dbc.Card([
            dbc.CardHeader(html.Span("Out-of-Stock Rate by Category (%)",
                                     className="fw-semibold small")),
            dbc.CardBody(dcc.Graph(id="sc-oos-rate", config={"displayModeBar": False},
                                   style={"height": "300px"})),
        ], className="border-0 shadow-sm"), width=6),
    ], className="g-3 mb-3"),

    # Row 3: Forecast accuracy + PO status
    dbc.Row([
        dbc.Col(dbc.Card([
            dbc.CardHeader(html.Span("Demand Forecast Accuracy Trend (MAPE %)",
                                     className="fw-semibold small")),
            dbc.CardBody(dcc.Graph(id="sc-forecast", config={"displayModeBar": False},
                                   style={"height": "280px"})),
        ], className="border-0 shadow-sm"), width=7),

        dbc.Col(dbc.Card([
            dbc.CardHeader(html.Span("Purchase Order Status Distribution",
                                     className="fw-semibold small")),
            dbc.CardBody(dcc.Graph(id="sc-po-status", config={"displayModeBar": False},
                                   style={"height": "280px"})),
        ], className="border-0 shadow-sm"), width=5),
    ], className="g-3"),
])


# ── Callbacks ─────────────────────────────────────────────────────────────────

@callback(Output("sc-kpis", "children"), Input("sc-vendor-filter", "value"))
def update_kpis(vendor):
    otif = get_otif()
    if vendor != "ALL":
        otif = otif[otif["vendor_id"] == vendor]

    otif_pct = otif["otif_flag"].mean() * 100
    fill_rate = otif["fill_rate_pct"].mean()
    avg_days_late = otif[otif["days_early_late"] < 0]["days_early_late"].mean()
    total_pos = len(otif)

    inv = get_store_inventory_agg()
    oos_rate = inv["oos_rate"].mean()

    cards = [
        kpi("OTIF Rate", f"{otif_pct:.1f}%",
            f"{total_pos:,} purchase orders",
            "bi-check-circle-fill", P["green"] if otif_pct >= 90 else P["red"],
            alert=otif_pct < 85),
        kpi("Avg Fill Rate", f"{fill_rate:.1f}%",
            "Units received / ordered",
            "bi-box-seam", P["blue"]),
        kpi("Avg Days Late", f"{abs(avg_days_late):.1f}d",
            "Late deliveries only",
            "bi-clock-history", P["amber"]),
        kpi("Store OOS Rate", f"{oos_rate:.1f}%",
            "Items at reorder threshold",
            "bi-exclamation-triangle-fill", P["red"] if oos_rate > 15 else P["orange"],
            alert=oos_rate > 20),
    ]
    return [dbc.Col(c, md=3) for c in cards]


@callback(Output("sc-otif-trend", "figure"), Input("sc-vendor-filter", "value"))
def update_otif_trend(vendor):
    otif = get_otif()
    if vendor != "ALL":
        otif = otif[otif["vendor_id"] == vendor]

    wk = (otif.groupby("order_week")
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
        fig.add_trace(go.Scatter(
            x=wk["order_week"], y=wk[col], name=label,
            line=dict(color=color, width=2),
            mode="lines",
        ))

    # Target line at 95%
    fig.add_hline(y=95, line_dash="dash", line_color="red", opacity=0.5,
                  annotation_text="95% Target", annotation_position="top right")
    fig.update_layout(
        **CHART_LAYOUT,
        yaxis_range=[60, 105],
        yaxis_title="Rate (%)",
        legend=dict(orientation="h", y=1.1, x=0),
        hovermode="x unified",
    )
    return fig


@callback(Output("sc-vendor-bar", "figure"), Input("sc-vendor-filter", "value"))
def update_vendor_bar(vendor):
    otif = get_otif()
    vend = (otif.groupby("vendor_id")
            .agg(otif_rate=("otif_flag", lambda x: round(x.mean() * 100, 1)),
                 fill_rate=("fill_rate_pct", "mean"),
                 pos=("otif_flag", "count"))
            .reset_index()
            .sort_values("otif_rate"))

    # Show bottom 20 worst + top 5 best
    worst = vend.nsmallest(15, "otif_rate")
    worst = worst.sort_values("otif_rate")

    colors = [P["green"] if r >= 95 else P["amber"] if r >= 85 else P["red"]
              for r in worst["otif_rate"]]

    fig = go.Figure(go.Bar(
        x=worst["otif_rate"],
        y=worst["vendor_id"],
        orientation="h",
        marker_color=colors,
        text=worst["otif_rate"].apply(lambda v: f"{v:.0f}%"),
        textposition="outside",
        customdata=worst[["fill_rate", "pos"]].values,
        hovertemplate="<b>%{y}</b><br>OTIF: %{x:.1f}%<br>Fill Rate: %{customdata[0]:.1f}%<br>POs: %{customdata[1]}<extra></extra>",
    ))
    fig.add_vline(x=95, line_dash="dash", line_color="grey", opacity=0.6,
                  annotation_text="95% Target")
    fig.update_layout(**CHART_LAYOUT, xaxis_range=[50, 110],
                      xaxis_title="OTIF Rate (%)", yaxis_title=None)
    return fig


@callback(Output("sc-inv-dos", "figure"), Input("sc-vendor-filter", "value"))
def update_inv_dos(_):
    inv = get_store_inventory_agg()
    latest = inv[inv["snapshot_date"] == inv["snapshot_date"].max()]
    cat_dos = (latest.groupby("category_name")
               .agg(avg_dos=("avg_dos", "mean"))
               .reset_index()
               .sort_values("avg_dos"))

    colors = [P["red"] if d < 7 else P["amber"] if d < 14 else P["green"]
              for d in cat_dos["avg_dos"]]

    fig = go.Figure(go.Bar(
        x=cat_dos["avg_dos"],
        y=cat_dos["category_name"],
        orientation="h",
        marker_color=colors,
        text=cat_dos["avg_dos"].apply(lambda v: f"{v:.1f}d"),
        textposition="outside",
    ))
    fig.add_vline(x=7, line_dash="dash", line_color="red", opacity=0.5,
                  annotation_text="7d Min")
    fig.add_vline(x=14, line_dash="dot", line_color="orange", opacity=0.5,
                  annotation_text="14d Target")
    fig.update_layout(**CHART_LAYOUT, xaxis_title="Days of Supply",
                      yaxis_title=None)
    return fig


@callback(Output("sc-oos-rate", "figure"), Input("sc-vendor-filter", "value"))
def update_oos_rate(_):
    inv = get_store_inventory_agg()
    cat_oos = (inv.groupby("category_name")
               .agg(oos_rate=("oos_rate", "mean"),
                    total_shrink=("total_shrink", "sum"))
               .reset_index()
               .sort_values("oos_rate", ascending=False))

    fig = px.bar(cat_oos, x="category_name", y="oos_rate",
                 color="oos_rate",
                 color_continuous_scale=[(0, "#A5D6A7"), (0.4, "#FFF176"), (1, "#EF9A9A")],
                 range_color=[0, 30],
                 text=cat_oos["oos_rate"].apply(lambda v: f"{v:.1f}%"),
                 labels={"oos_rate": "OOS Rate (%)", "category_name": ""},
                 hover_data={"total_shrink": ":,.0f"})
    fig.update_traces(textposition="outside", textfont_size=10)
    fig.update_coloraxes(showscale=False)
    fig.add_hline(y=15, line_dash="dash", line_color="red", opacity=0.5,
                  annotation_text="15% Alert Threshold")
    fig.update_layout(**CHART_LAYOUT, xaxis_title=None,
                      xaxis_tickangle=-30)
    return fig


@callback(Output("sc-forecast", "figure"), Input("sc-vendor-filter", "value"))
def update_forecast(_):
    fc = get_store_forecast()
    wk = (fc.groupby("forecast_date")
          .agg(avg_mape=("mape", "mean"),
               avg_acc=("forecast_accuracy_pct", "mean"),
               bias=("forecast_bias", "mean"))
          .reset_index())

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=wk["forecast_date"], y=wk["avg_mape"],
        name="MAPE %", fill="tozeroy",
        line=dict(color=P["orange"], width=2),
        fillcolor="rgba(230,81,0,0.1)",
    ))
    fig.add_trace(go.Scatter(
        x=wk["forecast_date"], y=wk["avg_acc"],
        name="Accuracy %", yaxis="y2",
        line=dict(color=P["blue"], width=2, dash="dot"),
    ))
    fig.update_layout(
        **CHART_LAYOUT,
        yaxis=dict(title="MAPE %", gridcolor="#EEEEEE", zeroline=False),
        yaxis2=dict(title="Accuracy %", overlaying="y", side="right",
                    showgrid=False, range=[50, 105]),
        legend=dict(orientation="h", y=1.1, x=0),
        hovermode="x unified",
    )
    return fig


@callback(Output("sc-po-status", "figure"), Input("sc-vendor-filter", "value"))
def update_po_status(vendor):
    po = get_purchase_orders()
    if vendor != "ALL":
        po = po[po["vendor_id"] == vendor]

    status_counts = po.groupby(["po_status", "po_type"])["total_cost"].sum().reset_index()
    status_totals = po["po_status"].value_counts().reset_index()
    status_totals.columns = ["po_status", "count"]

    colors = {
        "Open": P["blue"], "Confirmed": P["teal"],
        "Shipped": P["amber"], "Received": P["green"], "Cancelled": P["red"],
    }
    fig = go.Figure(go.Pie(
        labels=status_totals["po_status"],
        values=status_totals["count"],
        hole=0.55,
        marker_colors=[colors.get(s, "#999") for s in status_totals["po_status"]],
        textinfo="label+percent",
        textfont_size=11,
        hovertemplate="<b>%{label}</b><br>Count: %{value:,}<br>Share: %{percent}<extra></extra>",
    ))
    fig.add_annotation(text=f"<b>{len(po):,}</b><br>POs",
                       x=0.5, y=0.5, showarrow=False, font_size=14)
    fig.update_layout(**CHART_LAYOUT,
                      showlegend=False,
                      margin=dict(l=10, r=10, t=10, b=10))
    return fig
