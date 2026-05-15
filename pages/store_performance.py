import dash
from dash import dcc, html, Input, Output, callback
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import data_loader as dl

dash.register_page(__name__, path="/store-performance", name="Store Performance", order=1)

WMT_BLUE   = "#0071CE"
WMT_YELLOW = "#FFC220"
CARD_BG    = "#16213e"

PLOT_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#ccc", size=11),
    margin=dict(l=40, r=20, t=10, b=40),
    legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=10)),
)

def card(header, graph_id, height=300):
    return dbc.Card([
        dbc.CardHeader(header, style={"color": WMT_YELLOW, "background": CARD_BG, "border":"none"}),
        dbc.CardBody(dcc.Loading(dcc.Graph(id=graph_id, style={"height":f"{height}px"}))),
    ], style={"background": CARD_BG, "border": f"1px solid {WMT_BLUE}33", "borderRadius":"12px"})


layout = html.Div([
    dbc.Row([
        dbc.Col(html.H4("Store Performance", style={"color": WMT_YELLOW, "fontWeight":"700"}), width=6),
        dbc.Col(
            dcc.DatePickerRange(
                id="sp-date-range",
                min_date_allowed="2024-01-01", max_date_allowed="2024-12-31",
                start_date="2024-01-01", end_date="2024-12-31",
                display_format="MMM D, YYYY", style={"fontSize":"0.8rem"},
            ), width=6, className="d-flex justify-content-end align-items-center"
        ),
    ], className="mb-3 align-items-center"),

    dbc.Row([
        dbc.Col([
            html.Label("Region", style={"color":"#aaa","fontSize":"0.8rem"}),
            dcc.Dropdown(
                id="sp-region",
                options=[{"label":"All Regions","value":"ALL"}] +
                        [{"label":r,"value":r} for r in dl.REGIONS],
                value="ALL", clearable=False,
                style={"background":"#0d1117","color":"#eee"},
            ),
        ], width=3),
        dbc.Col([
            html.Label("State", style={"color":"#aaa","fontSize":"0.8rem"}),
            dcc.Dropdown(
                id="sp-state",
                options=[{"label":"All States","value":"ALL"}] +
                        [{"label":s,"value":s} for s in dl.STATES],
                value="ALL", clearable=False,
                style={"background":"#0d1117","color":"#eee"},
            ),
        ], width=3),
        dbc.Col([
            html.Label("Store Type", style={"color":"#aaa","fontSize":"0.8rem"}),
            dcc.Dropdown(
                id="sp-store-type",
                options=[{"label":"All Types","value":"ALL"}] +
                        [{"label":t,"value":t} for t in sorted(dl.dim_store["store_type"].unique())],
                value="ALL", clearable=False,
                style={"background":"#0d1117","color":"#eee"},
            ),
        ], width=3),
    ], className="mb-4 g-3"),

    dbc.Row([
        dbc.Col(card("Weekly Net Sales by Store (Top 10)", "sp-weekly-sales", 300), width=8),
        dbc.Col(card("Tender Mix", "sp-tender-pie", 300), width=4),
    ], className="g-3 mb-4"),

    dbc.Row([
        dbc.Col(card("Gross Margin % by Category", "sp-margin-bar", 300), width=5),
        dbc.Col(card("Sales per Sq Ft by Store Type", "sp-sales-sqft", 300), width=7),
    ], className="g-3"),
], style={"padding":"16px"})


@callback(
    Output("sp-weekly-sales", "figure"),
    Output("sp-tender-pie",   "figure"),
    Output("sp-margin-bar",   "figure"),
    Output("sp-sales-sqft",   "figure"),
    Input("sp-date-range",    "start_date"),
    Input("sp-date-range",    "end_date"),
    Input("sp-region",        "value"),
    Input("sp-state",         "value"),
    Input("sp-store-type",    "value"),
)
def update_store(start, end, region, state, stype):
    sw = dl.sales_by_store_week.copy()
    sw = sw[(sw["week_start_date"] >= start) & (sw["week_start_date"] <= end)]
    if region != "ALL": sw = sw[sw["region"] == region]
    if state  != "ALL": sw = sw[sw["state"]  == state]
    if stype  != "ALL": sw = sw[sw["store_type"] == stype]

    # Weekly sales — top 10 stores by total
    top_stores = sw.groupby("store_id")["net_sales"].sum().nlargest(10).index
    sw_top = sw[sw["store_id"].isin(top_stores)].copy()
    sw_top["store_label"] = "Store " + sw_top["store_id"].astype(str)
    fig_weekly = px.line(
        sw_top, x="week_start_date", y="net_sales", color="store_label",
        color_discrete_sequence=px.colors.qualitative.Pastel,
    )
    fig_weekly.update_traces(line=dict(width=1.5))
    fig_weekly.update_layout(**PLOT_LAYOUT, xaxis_title="", yaxis_title="Net Sales ($)",
                              yaxis_tickformat="$,.0f")

    # Tender mix — filter by store_ids in sw
    store_ids = sw["store_id"].unique()
    tender_df = dl.fact_tender[
        (dl.fact_tender["date"] >= start) &
        (dl.fact_tender["date"] <= end) &
        (dl.fact_tender["store_id"].isin(store_ids))
    ].groupby("tender_type", as_index=False)["total_amount"].sum()
    fig_tender = px.pie(
        tender_df, names="tender_type", values="total_amount",
        color_discrete_sequence=px.colors.qualitative.Bold,
        hole=0.45,
    )
    fig_tender.update_traces(textposition="inside", textinfo="percent+label",
                              textfont=dict(size=10))
    fig_tender.update_layout(**PLOT_LAYOUT, showlegend=False)

    # Margin by category
    sc = dl.sales_cat_store[dl.sales_cat_store["store_id"].isin(store_ids)]
    margin_cat = sc.groupby("category_name", as_index=False).agg(
        net_sales=("net_sales","sum"), gross_margin=("gross_margin","sum")
    )
    margin_cat["gm_pct"] = margin_cat["gross_margin"] / margin_cat["net_sales"].replace(0, pd.NA) * 100
    margin_cat = margin_cat.dropna().sort_values("gm_pct")
    fig_margin = px.bar(
        margin_cat, x="gm_pct", y="category_name", orientation="h",
        color="gm_pct", color_continuous_scale=[[0,WMT_BLUE],[1,WMT_YELLOW]],
        labels={"gm_pct":"GM %","category_name":""},
    )
    fig_margin.update_layout(**PLOT_LAYOUT, xaxis_ticksuffix="%", showlegend=False,
                              coloraxis_showscale=False)
    fig_margin.update_traces(marker_line_width=0)

    # Sales per sqft scatter
    sqft_df = sw.groupby(["store_id","store_type","square_footage"], as_index=False).agg(
        net_sales=("net_sales","sum")
    )
    sqft_df["sales_per_sqft"] = sqft_df["net_sales"] / sqft_df["square_footage"].replace(0, pd.NA)
    sqft_df = sqft_df.dropna()
    fig_sqft = px.scatter(
        sqft_df, x="square_footage", y="sales_per_sqft", color="store_type",
        size="net_sales", size_max=20,
        color_discrete_sequence=[WMT_BLUE, WMT_YELLOW, "#00b4d8", "#90e0ef"],
        labels={"square_footage":"Sq Ft","sales_per_sqft":"Sales / Sq Ft","store_type":"Type"},
        hover_data={"store_id":True,"net_sales":True},
    )
    fig_sqft.update_layout(**PLOT_LAYOUT, yaxis_tickformat="$,.2f")

    return fig_weekly, fig_tender, fig_margin, fig_sqft
