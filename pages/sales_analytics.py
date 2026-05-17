import dash
from dash import dcc, html, callback, Input, Output
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

from data_loader import (
    get_store_sales, get_sales_weekly_agg, get_sales_category_agg,
    get_top_items, get_store_performance, get_ecomm_sales,
    get_channel_comparison, get_markdowns, fmt_millions, fmt_number,
)

dash.register_page(__name__, path="/", name="Sales Analytics", order=1)

# ── Palette ────────────────────────────────────────────────────────────────────
P = {
    "blue": "#1565C0", "green": "#2E7D32", "red": "#C62828",
    "amber": "#F57F17", "teal": "#00695C", "purple": "#6A1B9A",
    "bg": "#F4F6F9", "card": "#FFFFFF",
}
CHART_LAYOUT = dict(
    paper_bgcolor="white", plot_bgcolor="white",
    font_family="Inter, system-ui, sans-serif", font_size=12,
    margin=dict(l=10, r=10, t=36, b=10),
    xaxis=dict(showgrid=False, zeroline=False),
    yaxis=dict(gridcolor="#EEEEEE", zeroline=False),
)

# ── Shared filter options ──────────────────────────────────────────────────────
def _category_options():
    cats = sorted(get_sales_category_agg()["category_name"].tolist())
    return [{"label": "All Categories", "value": "ALL"}] + [
        {"label": c, "value": c} for c in cats
    ]


def _region_options():
    regions = sorted(get_store_performance()["region"].dropna().unique())
    return [{"label": "All Regions", "value": "ALL"}] + [
        {"label": r, "value": r} for r in regions
    ]


# ── KPI card ──────────────────────────────────────────────────────────────────
def kpi(title, val, sub, icon, color):
    return dbc.Card([
        dbc.CardBody([
            dbc.Row([
                dbc.Col(html.Div(html.I(className=f"bi {icon} fs-2"),
                                  style={"color": color, "opacity": 0.85}), width="auto"),
                dbc.Col([
                    html.Div(title, className="text-muted small text-uppercase fw-semibold",
                             style={"letterSpacing": "0.05em", "fontSize": "0.72rem"}),
                    html.Div(val, className="fw-bold", style={"fontSize": "1.45rem",
                                                               "color": "#212529"}),
                    html.Div(sub, className="small text-muted", style={"fontSize": "0.78rem"}),
                ]),
            ], align="center", className="g-2"),
        ], className="py-3"),
    ], className="border-0 shadow-sm h-100")


# ── Layout ────────────────────────────────────────────────────────────────────
layout = html.Div([
    # Header
    dbc.Row([
        dbc.Col([
            html.H4("Sales Analytics", className="fw-bold mb-0", style={"color": "#212529"}),
            html.Small("Store & e-commerce performance · FY 2024", className="text-muted"),
        ]),
        dbc.Col([
            dbc.Row([
                dbc.Col(dcc.Dropdown(id="sa-cat-filter", options=_category_options(),
                                     value="ALL", clearable=False,
                                     style={"fontSize": "0.85rem"}), width=6),
                dbc.Col(dcc.Dropdown(id="sa-region-filter", options=_region_options(),
                                     value="ALL", clearable=False,
                                     style={"fontSize": "0.85rem"}), width=6),
            ]),
        ], width=5),
    ], className="mb-3 align-items-center"),

    # KPI cards
    dbc.Row(id="sa-kpis", className="g-3 mb-3"),

    # Row 1: Weekly trend + Category bar
    dbc.Row([
        dbc.Col(dbc.Card([
            dbc.CardHeader(html.Span("Weekly Revenue & Margin Trend",
                                     className="fw-semibold small")),
            dbc.CardBody(dcc.Graph(id="sa-trend", config={"displayModeBar": False},
                                   style={"height": "300px"})),
        ], className="border-0 shadow-sm"), width=8),

        dbc.Col(dbc.Card([
            dbc.CardHeader(html.Span("Revenue by Category",
                                     className="fw-semibold small")),
            dbc.CardBody(dcc.Graph(id="sa-cat-bar", config={"displayModeBar": False},
                                   style={"height": "300px"})),
        ], className="border-0 shadow-sm"), width=4),
    ], className="g-3 mb-3"),

    # Row 2: Top Items + Channel split
    dbc.Row([
        dbc.Col(dbc.Card([
            dbc.CardHeader(html.Span("Top 15 Items by Revenue",
                                     className="fw-semibold small")),
            dbc.CardBody(dcc.Graph(id="sa-top-items", config={"displayModeBar": False},
                                   style={"height": "360px"})),
        ], className="border-0 shadow-sm"), width=6),

        dbc.Col(dbc.Card([
            dbc.CardHeader(html.Span("In-Store vs E-Commerce Revenue",
                                     className="fw-semibold small")),
            dbc.CardBody(dcc.Graph(id="sa-channel", config={"displayModeBar": False},
                                   style={"height": "360px"})),
        ], className="border-0 shadow-sm"), width=6),
    ], className="g-3 mb-3"),

    # Row 3: Store performance scatter + Markdown impact
    dbc.Row([
        dbc.Col(dbc.Card([
            dbc.CardHeader(html.Span("Store Revenue vs Gross Margin % (by Region)",
                                     className="fw-semibold small")),
            dbc.CardBody(dcc.Graph(id="sa-store-scatter", config={"displayModeBar": False},
                                   style={"height": "300px"})),
        ], className="border-0 shadow-sm"), width=7),

        dbc.Col(dbc.Card([
            dbc.CardHeader(html.Span("Markdown Event Impact by Type",
                                     className="fw-semibold small")),
            dbc.CardBody(dcc.Graph(id="sa-markdown", config={"displayModeBar": False},
                                   style={"height": "300px"})),
        ], className="border-0 shadow-sm"), width=5),
    ], className="g-3"),
])


# ── Callbacks ─────────────────────────────────────────────────────────────────

@callback(
    Output("sa-kpis", "children"),
    Input("sa-cat-filter", "value"),
    Input("sa-region-filter", "value"),
)
def update_kpis(cat, region):
    df = get_store_sales()
    if cat != "ALL":
        df = df[df["category_name"] == cat]
    if region != "ALL":
        df = df[df["region"] == region]

    total_rev = df["net_sales"].sum()
    total_units = df["net_units"].sum()
    avg_margin = df["gross_margin_pct"].mean()
    transactions = df["num_transactions"].sum()

    ecomm = get_ecomm_sales()
    if cat != "ALL":
        ecomm = ecomm[ecomm["category_name"] == cat]
    ecomm_rev = ecomm["net_sales"].sum()

    cards = [
        kpi("Total Revenue", fmt_millions(total_rev),
            f"E-Comm: {fmt_millions(ecomm_rev)}",
            "bi-currency-dollar", P["blue"]),
        kpi("Net Units Sold", fmt_number(total_units),
            "All channels combined",
            "bi-box-seam-fill", P["teal"]),
        kpi("Avg Gross Margin", f"{avg_margin:.1f}%",
            "Store sales margin",
            "bi-graph-up-arrow", P["green"]),
        kpi("Total Transactions", fmt_number(transactions),
            "In-store checkout count",
            "bi-receipt", P["purple"]),
    ]
    return [dbc.Col(c, md=3) for c in cards]


@callback(
    Output("sa-trend", "figure"),
    Input("sa-cat-filter", "value"),
    Input("sa-region-filter", "value"),
)
def update_trend(cat, region):
    if cat == "ALL" and region == "ALL":
        wk = get_sales_weekly_agg().copy()
    else:
        df = get_store_sales()
        if cat != "ALL":
            df = df[df["category_name"] == cat]
        if region != "ALL":
            df = df[df["region"] == region]
        wk = df.groupby("week_start_date").agg(
            net_sales=("net_sales", "sum"),
            gross_margin=("gross_margin", "sum"),
        ).reset_index()
        wk["gross_margin_pct"] = (wk["gross_margin"] / wk["net_sales"] * 100).round(2)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=wk["week_start_date"], y=wk["net_sales"],
        name="Revenue", fill="tozeroy",
        line=dict(color=P["blue"], width=2),
        fillcolor="rgba(21,101,192,0.1)",
    ))
    fig.add_trace(go.Scatter(
        x=wk["week_start_date"], y=wk["gross_margin_pct"],
        name="Margin %", yaxis="y2",
        line=dict(color=P["green"], width=2, dash="dot"),
    ))
    fig.update_layout(
        **CHART_LAYOUT,
        yaxis=dict(title="Revenue ($)", gridcolor="#EEEEEE", zeroline=False),
        yaxis2=dict(title="Margin %", overlaying="y", side="right",
                    showgrid=False, zeroline=False),
        legend=dict(orientation="h", y=1.08, x=0),
        hovermode="x unified",
    )
    return fig


@callback(
    Output("sa-cat-bar", "figure"),
    Input("sa-region-filter", "value"),
)
def update_cat_bar(region):
    if region == "ALL":
        cat = get_sales_category_agg().head(12)
    else:
        df = get_store_sales()
        df = df[df["region"] == region]
        cat = (df.groupby("category_name")["net_sales"].sum()
               .reset_index().sort_values("net_sales", ascending=False).head(12))
        cat["gross_margin_pct"] = (df.groupby("category_name")["gross_margin_pct"]
                                   .mean().reindex(cat["category_name"]).values)

    cat = cat.sort_values("net_sales")
    fig = px.bar(cat, x="net_sales", y="category_name", orientation="h",
                 color="net_sales", color_continuous_scale="Blues",
                 labels={"net_sales": "Revenue ($)", "category_name": ""},
                 text=cat["net_sales"].apply(fmt_millions))
    fig.update_traces(textposition="outside", textfont_size=10)
    fig.update_coloraxes(showscale=False)
    fig.update_layout(**CHART_LAYOUT,
                      xaxis_title=None, yaxis_title=None)
    return fig


@callback(
    Output("sa-top-items", "figure"),
    Input("sa-cat-filter", "value"),
)
def update_top_items(cat):
    df = get_top_items()
    if cat != "ALL":
        df = get_store_sales()
        df = df[df["category_name"] == cat]
        df = (df.groupby(["item_id", "item_name", "category_name"])
              .agg(net_sales=("net_sales", "sum"),
                   gross_margin_pct=("gross_margin_pct", "mean"))
              .reset_index()
              .sort_values("net_sales", ascending=False).head(15))
    else:
        df = df.head(15)

    df = df.sort_values("net_sales")
    short_names = df["item_name"].str[:35] + "…"
    fig = px.bar(df, x="net_sales", y=short_names, orientation="h",
                 color="gross_margin_pct",
                 color_continuous_scale=[(0, "#EF9A9A"), (0.5, "#FFF176"), (1, "#A5D6A7")],
                 range_color=[20, 45],
                 labels={"net_sales": "Revenue ($)", "y": "",
                         "gross_margin_pct": "Margin %"},
                 text=df["net_sales"].apply(fmt_millions))
    fig.update_traces(textposition="outside", textfont_size=10)
    fig.update_layout(**CHART_LAYOUT,
                      xaxis_title=None, yaxis_title=None,
                      coloraxis_colorbar=dict(title="Margin %",
                                              len=0.6, thickness=12, x=1.01))
    return fig


@callback(
    Output("sa-channel", "figure"),
    Input("sa-cat-filter", "value"),
)
def update_channel(cat):
    df = get_channel_comparison()
    if cat != "ALL":
        store = get_store_sales()
        store = store[store["category_name"] == cat]
        s_wk = (store.groupby("week_start_date")["net_sales"]
                .sum().reset_index().assign(channel="In-Store"))
        e_wk = (get_ecomm_sales()[get_ecomm_sales()["category_name"] == cat]
                .groupby("week_start_date")["net_sales"]
                .sum().reset_index().assign(channel="E-Commerce"))
        df = pd.concat([s_wk, e_wk])

    fig = px.area(df, x="week_start_date", y="net_sales", color="channel",
                  color_discrete_map={"In-Store": P["blue"], "E-Commerce": P["teal"]},
                  labels={"net_sales": "Revenue ($)", "week_start_date": "",
                          "channel": "Channel"},
                  line_group="channel")
    fig.update_layout(**CHART_LAYOUT,
                      legend=dict(orientation="h", y=1.08, x=0),
                      hovermode="x unified")
    return fig


@callback(
    Output("sa-store-scatter", "figure"),
    Input("sa-region-filter", "value"),
)
def update_store_scatter(region):
    df = get_store_performance()
    if region != "ALL":
        df = df[df["region"] == region]

    fig = px.scatter(df, x="net_sales", y="gross_margin_pct",
                     color="region", size="net_units",
                     hover_data={"store_name": True, "state": True,
                                 "net_sales": ":,.0f",
                                 "gross_margin_pct": ":.1f",
                                 "net_units": False},
                     labels={"net_sales": "Revenue ($)",
                              "gross_margin_pct": "Gross Margin %",
                              "region": "Region"},
                     color_discrete_sequence=px.colors.qualitative.Set2)
    fig.update_layout(**CHART_LAYOUT,
                      legend=dict(orientation="h", y=1.08, x=0))
    return fig


@callback(
    Output("sa-markdown", "figure"),
    Input("sa-cat-filter", "value"),
)
def update_markdown(cat):
    df = get_markdowns()
    if cat != "ALL":
        df = df[df["category_name"] == cat]

    agg = (df.groupby("event_type")
           .agg(avg_depth=("markdown_depth", "mean"),
                total_units=("units_sold_during_event", "sum"),
                total_revenue=("revenue_during_event", "sum"),
                margin_impact=("margin_impact", "sum"),
                event_count=("event_id", "count"))
           .reset_index())

    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="Units Sold",
        x=agg["event_type"],
        y=agg["total_units"],
        marker_color=P["blue"],
        yaxis="y",
    ))
    fig.add_trace(go.Scatter(
        name="Avg Markdown Depth %",
        x=agg["event_type"],
        y=agg["avg_depth"],
        mode="markers+lines",
        marker=dict(size=10, color=P["amber"]),
        line=dict(color=P["amber"], width=2),
        yaxis="y2",
    ))
    fig.update_layout(
        **CHART_LAYOUT,
        yaxis=dict(title="Units Sold", gridcolor="#EEEEEE", zeroline=False),
        yaxis2=dict(title="Avg Depth %", overlaying="y", side="right",
                    showgrid=False, zeroline=False),
        legend=dict(orientation="h", y=1.12, x=0),
        barmode="group",
    )
    return fig
