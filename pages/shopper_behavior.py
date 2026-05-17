import dash
from dash import dcc, html, callback, Input, Output
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np

from data_loader import (
    get_clickstream_agg, get_funnel_data, get_tender, get_fulfillment,
    fmt_number,
)

dash.register_page(__name__, path="/shoppers", name="Shopper Behavior", order=3)

P = {
    "blue": "#1565C0", "green": "#2E7D32", "red": "#C62828",
    "amber": "#F57F17", "teal": "#00695C", "purple": "#6A1B9A",
    "indigo": "#283593", "cyan": "#006064",
}
CHART_LAYOUT = dict(
    paper_bgcolor="white", plot_bgcolor="white",
    font_family="Inter, system-ui, sans-serif", font_size=12,
    margin=dict(l=10, r=10, t=36, b=10),
    xaxis=dict(showgrid=False, zeroline=False),
    yaxis=dict(gridcolor="#EEEEEE", zeroline=False),
)


def kpi(title, val, sub, icon, color):
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
    ], className="border-0 shadow-sm h-100")


def _device_opts():
    return [{"label": "All Devices", "value": "ALL"},
            {"label": "Mobile", "value": "Mobile"},
            {"label": "Desktop", "value": "Desktop"},
            {"label": "Tablet", "value": "Tablet"}]


def _channel_opts():
    return [{"label": "All Sources", "value": "ALL"},
            {"label": "Google Search", "value": "Google Search"},
            {"label": "Direct", "value": "Direct"},
            {"label": "Social Media", "value": "Social Media"},
            {"label": "Email", "value": "Email"},
            {"label": "Affiliate", "value": "Affiliate"}]


layout = html.Div([
    dbc.Row([
        dbc.Col([
            html.H4("Shopper Behavior Analytics", className="fw-bold mb-0",
                    style={"color": "#212529"}),
            html.Small("Clickstream · Conversion · Payment · Fulfillment Preferences",
                       className="text-muted"),
        ]),
        dbc.Col([
            dbc.Row([
                dbc.Col(dcc.Dropdown(id="sh-device", options=_device_opts(),
                                     value="ALL", clearable=False,
                                     style={"fontSize": "0.85rem"}), width=6),
                dbc.Col(dcc.Dropdown(id="sh-source", options=_channel_opts(),
                                     value="ALL", clearable=False,
                                     style={"fontSize": "0.85rem"}), width=6),
            ]),
        ], width=5),
    ], className="mb-3 align-items-center"),

    # KPIs
    dbc.Row(id="sh-kpis", className="g-3 mb-3"),

    # Row 1: Funnel + Device split
    dbc.Row([
        dbc.Col(dbc.Card([
            dbc.CardHeader(html.Span("Shopper Purchase Funnel",
                                     className="fw-semibold small")),
            dbc.CardBody(dcc.Graph(id="sh-funnel", config={"displayModeBar": False},
                                   style={"height": "300px"})),
        ], className="border-0 shadow-sm"), width=5),

        dbc.Col(dbc.Card([
            dbc.CardHeader(html.Span("Sessions by Device & Referral Source",
                                     className="fw-semibold small")),
            dbc.CardBody(dcc.Graph(id="sh-device-bar", config={"displayModeBar": False},
                                   style={"height": "300px"})),
        ], className="border-0 shadow-sm"), width=7),
    ], className="g-3 mb-3"),

    # Row 2: Top search terms + Page category engagement
    dbc.Row([
        dbc.Col(dbc.Card([
            dbc.CardHeader(html.Span("Top 15 Search Terms",
                                     className="fw-semibold small")),
            dbc.CardBody(dcc.Graph(id="sh-search", config={"displayModeBar": False},
                                   style={"height": "320px"})),
        ], className="border-0 shadow-sm"), width=5),

        dbc.Col(dbc.Card([
            dbc.CardHeader(html.Span("Category Browse vs Purchase Conversion",
                                     className="fw-semibold small")),
            dbc.CardBody(dcc.Graph(id="sh-cat-conv", config={"displayModeBar": False},
                                   style={"height": "320px"})),
        ], className="border-0 shadow-sm"), width=7),
    ], className="g-3 mb-3"),

    # Row 3: Tender mix + Fulfillment performance
    dbc.Row([
        dbc.Col(dbc.Card([
            dbc.CardHeader(html.Span("Payment Tender Mix ($ Volume)",
                                     className="fw-semibold small")),
            dbc.CardBody(dcc.Graph(id="sh-tender", config={"displayModeBar": False},
                                   style={"height": "280px"})),
        ], className="border-0 shadow-sm"), width=4),

        dbc.Col(dbc.Card([
            dbc.CardHeader(html.Span("Fulfillment Type: SLA Attainment & Customer Rating",
                                     className="fw-semibold small")),
            dbc.CardBody(dcc.Graph(id="sh-fulfillment", config={"displayModeBar": False},
                                   style={"height": "280px"})),
        ], className="border-0 shadow-sm"), width=8),
    ], className="g-3"),
])


# ── Callbacks ─────────────────────────────────────────────────────────────────

def _filter_cs(device, source):
    df = get_clickstream_agg()
    if device != "ALL":
        df = df[df["device_type"] == device]
    if source != "ALL":
        df = df[df["referral_source"] == source]
    return df


@callback(Output("sh-kpis", "children"),
          Input("sh-device", "value"), Input("sh-source", "value"))
def update_kpis(device, source):
    df = _filter_cs(device, source)

    total_sessions = df["session_id"].nunique()
    conversion_rate = df["purchase_flag"].mean() * 100
    cart_rate = df["add_to_cart_flag"].mean() * 100
    avg_time = df["time_on_page_sec"].mean()

    # Abandonment = sessions that added to cart but did NOT purchase
    sess = df.groupby("session_id").agg(
        carted=("add_to_cart_flag", "any"),
        purchased=("purchase_flag", "any"),
    )
    cart_abandon = sess[(sess["carted"]) & (~sess["purchased"])].shape[0]
    abandon_rate = cart_abandon / max(sess["carted"].sum(), 1) * 100

    cards = [
        kpi("Total Sessions", fmt_number(total_sessions),
            "Unique browsing sessions",
            "bi-person-circle", P["blue"]),
        kpi("Purchase Conversion", f"{conversion_rate:.1f}%",
            "Events ending in purchase",
            "bi-cart-check-fill", P["green"]),
        kpi("Add-to-Cart Rate", f"{cart_rate:.1f}%",
            "Events that added item",
            "bi-cart-plus-fill", P["teal"]),
        kpi("Cart Abandonment", f"{abandon_rate:.1f}%",
            "Carted but not purchased",
            "bi-cart-x-fill", P["red"]),
    ]
    return [dbc.Col(c, md=3) for c in cards]


@callback(Output("sh-funnel", "figure"),
          Input("sh-device", "value"), Input("sh-source", "value"))
def update_funnel(device, source):
    df = _filter_cs(device, source)
    events = df["event_type"].value_counts()
    steps = ["search", "page_view", "product_view", "add_to_cart", "begin_checkout"]
    labels = ["Search", "Page View", "Product View", "Add to Cart", "Checkout"]
    counts = [int(events.get(s, 0)) for s in steps]

    fig = go.Figure(go.Funnel(
        y=labels,
        x=counts,
        textinfo="value+percent initial",
        marker=dict(color=[P["blue"], "#1976D2", "#1E88E5", P["teal"], P["green"]]),
        connector=dict(line=dict(color="white", width=2)),
        textfont=dict(size=12),
    ))
    fig.update_layout(**CHART_LAYOUT,
                      margin=dict(l=10, r=10, t=20, b=10))
    return fig


@callback(Output("sh-device-bar", "figure"),
          Input("sh-device", "value"), Input("sh-source", "value"))
def update_device_bar(device, source):
    df = _filter_cs(device, source)
    agg = (df.groupby(["referral_source", "device_type"])
           .size().reset_index(name="sessions"))

    fig = px.bar(agg, x="referral_source", y="sessions", color="device_type",
                 color_discrete_map={"Mobile": P["blue"], "Desktop": P["teal"],
                                     "Tablet": P["amber"]},
                 barmode="stack",
                 labels={"sessions": "Sessions", "referral_source": "",
                         "device_type": "Device"},
                 text_auto=False)
    fig.update_layout(**CHART_LAYOUT,
                      xaxis_title=None,
                      legend=dict(orientation="h", y=1.08, x=0))
    return fig


@callback(Output("sh-search", "figure"),
          Input("sh-device", "value"), Input("sh-source", "value"))
def update_search(device, source):
    df = _filter_cs(device, source)
    searches = (df[df["event_type"] == "search"]["search_term"]
                .dropna().value_counts().head(15).reset_index())
    searches.columns = ["term", "count"]
    searches = searches.sort_values("count")

    fig = px.bar(searches, x="count", y="term", orientation="h",
                 color="count", color_continuous_scale="Blues",
                 labels={"count": "Searches", "term": ""},
                 text="count")
    fig.update_traces(textposition="outside", textfont_size=10)
    fig.update_coloraxes(showscale=False)
    fig.update_layout(**CHART_LAYOUT, xaxis_title=None, yaxis_title=None)
    return fig


@callback(Output("sh-cat-conv", "figure"),
          Input("sh-device", "value"), Input("sh-source", "value"))
def update_cat_conv(device, source):
    df = _filter_cs(device, source)
    cat_agg = (df.groupby("page_category")
               .agg(views=("event_id", "count"),
                    purchases=("purchase_flag", "sum"),
                    add_to_cart=("add_to_cart_flag", "sum"))
               .reset_index())
    cat_agg["conv_rate"] = (cat_agg["purchases"] / cat_agg["views"] * 100).round(2)
    cat_agg["cart_rate"] = (cat_agg["add_to_cart"] / cat_agg["views"] * 100).round(2)
    cat_agg = cat_agg.sort_values("conv_rate", ascending=False)

    fig = go.Figure()
    fig.add_trace(go.Bar(name="Conversion Rate %", x=cat_agg["page_category"],
                          y=cat_agg["conv_rate"], marker_color=P["blue"], yaxis="y"))
    fig.add_trace(go.Bar(name="Cart Rate %", x=cat_agg["page_category"],
                          y=cat_agg["cart_rate"], marker_color=P["teal"], yaxis="y"))
    fig.add_trace(go.Scatter(name="Views (scaled)", x=cat_agg["page_category"],
                              y=cat_agg["views"] / cat_agg["views"].max() * 30,
                              mode="markers",
                              marker=dict(size=cat_agg["views"] / cat_agg["views"].max() * 20 + 5,
                                          color=P["amber"], opacity=0.7),
                              yaxis="y"))
    fig.update_layout(**CHART_LAYOUT,
                      barmode="group",
                      xaxis_title=None, yaxis_title="Rate (%)",
                      xaxis_tickangle=-30,
                      legend=dict(orientation="h", y=1.1, x=0))
    return fig


@callback(Output("sh-tender", "figure"),
          Input("sh-device", "value"), Input("sh-source", "value"))
def update_tender(_d, _s):
    tend = get_tender()
    tender_agg = (tend.groupby("tender_type")
                  .agg(total_amount=("total_amount", "sum"),
                       transactions=("transaction_count", "sum"))
                  .reset_index()
                  .sort_values("total_amount", ascending=False))

    colors = [P["blue"], P["teal"], P["green"], P["amber"], P["purple"],
              P["cyan"], P["red"]]
    fig = go.Figure(go.Pie(
        labels=tender_agg["tender_type"],
        values=tender_agg["total_amount"],
        hole=0.52,
        marker_colors=colors[:len(tender_agg)],
        textinfo="label+percent",
        textfont_size=10,
        hovertemplate="<b>%{label}</b><br>$%{value:,.0f}<br>%{percent}<extra></extra>",
    ))
    fig.add_annotation(text="Payment<br>Mix", x=0.5, y=0.5,
                       showarrow=False, font_size=12, font_color="#555")
    fig.update_layout(**CHART_LAYOUT, showlegend=False,
                      margin=dict(l=10, r=10, t=10, b=10))
    return fig


@callback(Output("sh-fulfillment", "figure"),
          Input("sh-device", "value"), Input("sh-source", "value"))
def update_fulfillment(_d, _s):
    ful = get_fulfillment()
    agg = (ful.groupby("fulfillment_type")
           .agg(orders=("order_id", "count"),
                sla_rate=("sla_met", lambda x: x.mean() * 100),
                avg_rating=("customer_rating", "mean"),
                avg_hours=("actual_hours", "mean"))
           .reset_index()
           .sort_values("orders", ascending=False))

    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="Order Count",
        x=agg["fulfillment_type"],
        y=agg["orders"],
        marker_color=P["blue"],
        yaxis="y",
        text=agg["orders"].apply(lambda v: f"{v:,}"),
        textposition="outside",
    ))
    fig.add_trace(go.Scatter(
        name="SLA Met %",
        x=agg["fulfillment_type"],
        y=agg["sla_rate"],
        mode="markers+lines",
        marker=dict(size=12, color=P["green"], symbol="diamond"),
        line=dict(color=P["green"], width=2),
        yaxis="y2",
    ))
    fig.add_trace(go.Scatter(
        name="Avg Rating (★)",
        x=agg["fulfillment_type"],
        y=agg["avg_rating"],
        mode="markers+lines",
        marker=dict(size=10, color=P["amber"]),
        line=dict(color=P["amber"], width=2, dash="dot"),
        yaxis="y2",
    ))
    fig.update_layout(
        **CHART_LAYOUT,
        yaxis=dict(title="Order Count", gridcolor="#EEEEEE", zeroline=False),
        yaxis2=dict(title="Rate / Rating", overlaying="y", side="right",
                    showgrid=False, range=[0, 110]),
        legend=dict(orientation="h", y=1.1, x=0),
        xaxis_title=None,
    )
    return fig
