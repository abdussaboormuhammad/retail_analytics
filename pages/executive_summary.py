import dash
from dash import dcc, html, Input, Output, callback
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import data_loader as dl

dash.register_page(__name__, path="/", name="Executive Summary", order=0)

WMT_BLUE   = "#0071CE"
WMT_YELLOW = "#FFC220"
DARK_BG    = "#1a1a2e"
CARD_BG    = "#16213e"

def kpi_card(title, value, icon="📊", color=WMT_BLUE):
    return dbc.Card(
        dbc.CardBody([
            html.Div(icon, style={"fontSize":"1.8rem"}),
            html.H6(title, className="text-muted mt-1 mb-0", style={"fontSize":"0.75rem","letterSpacing":"0.05em"}),
            html.H3(value, style={"color": color, "fontWeight":"700","margin":"4px 0 0"}),
        ]),
        style={"background": CARD_BG, "border": f"1px solid {color}33",
               "borderRadius":"12px", "textAlign":"center"},
    )

layout = html.Div([
    dbc.Row([
        dbc.Col(html.H4("Executive Summary", style={"color": WMT_YELLOW, "fontWeight":"700"}), width=8),
        dbc.Col(
            dcc.DatePickerRange(
                id="exec-date-range",
                min_date_allowed="2024-01-01",
                max_date_allowed="2024-12-31",
                start_date="2024-01-01",
                end_date="2024-12-31",
                display_format="MMM D, YYYY",
                style={"fontSize":"0.8rem"},
            ), width=4, className="d-flex justify-content-end align-items-center"
        ),
    ], className="mb-3 align-items-center"),

    # KPI row
    dbc.Row([
        dbc.Col(kpi_card("Total Net Sales", f"${dl.TOTAL_NET_SALES/1e9:.2f}B", "💰", WMT_YELLOW), width=True),
        dbc.Col(kpi_card("Gross Margin %",  f"{dl.GROSS_MARGIN_PCT:.1f}%",      "📈", WMT_BLUE), width=True),
        dbc.Col(kpi_card("Top Category",    dl.TOP_CATEGORY,                    "🏆", WMT_YELLOW), width=True),
        dbc.Col(kpi_card("OTIF %",          f"{dl.GLOBAL_OTIF_PCT:.1f}%",       "🚚", WMT_BLUE), width=True),
        dbc.Col(kpi_card("In-Stock Rate",   f"{dl.INSTOCK_RATE:.1f}%",          "📦", WMT_YELLOW), width=True),
    ], className="g-3 mb-4"),

    # Charts row 1
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Weekly Net Sales by Category", style={"color": WMT_YELLOW, "background": CARD_BG, "border":"none"}),
                dbc.CardBody(dcc.Loading(dcc.Graph(id="exec-sales-trend", style={"height":"320px"}))),
            ], style={"background": CARD_BG, "border": f"1px solid {WMT_BLUE}33", "borderRadius":"12px"}),
        ], width=8),
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Category Filter", style={"color": WMT_YELLOW, "background": CARD_BG, "border":"none"}),
                dbc.CardBody(
                    dcc.Checklist(
                        id="exec-cat-filter",
                        options=[{"label": c, "value": c} for c in dl.CATEGORIES],
                        value=dl.CATEGORIES,
                        labelStyle={"display":"block","color":"#ccc","fontSize":"0.85rem","margin":"3px 0"},
                        inputStyle={"marginRight":"6px","accentColor": WMT_BLUE},
                    )
                ),
            ], style={"background": CARD_BG, "border": f"1px solid {WMT_BLUE}33", "borderRadius":"12px", "height":"100%"}),
        ], width=4),
    ], className="g-3 mb-4"),

    # Charts row 2
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Net Sales by State", style={"color": WMT_YELLOW, "background": CARD_BG, "border":"none"}),
                dbc.CardBody(dcc.Loading(dcc.Graph(id="exec-choropleth", style={"height":"320px"}))),
            ], style={"background": CARD_BG, "border": f"1px solid {WMT_BLUE}33", "borderRadius":"12px"}),
        ], width=7),
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Top 10 Items by Revenue", style={"color": WMT_YELLOW, "background": CARD_BG, "border":"none"}),
                dbc.CardBody(dcc.Loading(dcc.Graph(id="exec-top-items", style={"height":"320px"}))),
            ], style={"background": CARD_BG, "border": f"1px solid {WMT_BLUE}33", "borderRadius":"12px"}),
        ], width=5),
    ], className="g-3"),
], style={"padding":"16px"})


PLOT_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#ccc", size=11),
    margin=dict(l=40, r=20, t=10, b=40),
    legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=10)),
)


@callback(
    Output("exec-sales-trend", "figure"),
    Output("exec-choropleth",  "figure"),
    Output("exec-top-items",   "figure"),
    Input("exec-date-range",   "start_date"),
    Input("exec-date-range",   "end_date"),
    Input("exec-cat-filter",   "value"),
)
def update_exec(start, end, cats):
    cats = cats or dl.CATEGORIES

    # Sales trend
    df = dl.sales_weekly_cat[
        (dl.sales_weekly_cat["week_start_date"] >= start) &
        (dl.sales_weekly_cat["week_start_date"] <= end) &
        (dl.sales_weekly_cat["category_name"].isin(cats))
    ]
    fig_trend = px.line(
        df, x="week_start_date", y="net_sales", color="category_name",
        color_discrete_sequence=px.colors.qualitative.Bold,
    )
    fig_trend.update_traces(line=dict(width=1.5))
    fig_trend.update_layout(**PLOT_LAYOUT, xaxis_title="", yaxis_title="Net Sales ($)",
                            yaxis_tickformat="$,.0f")

    # Choropleth — state sales, filtered by selected categories
    state_df = (
        dl._sales_raw[
            (dl._sales_raw["week_start_date"] >= start) &
            (dl._sales_raw["week_start_date"] <= end) &
            (dl._sales_raw["category_name"].isin(cats))
        ]
        .groupby("state", as_index=False)["net_sales"].sum()
    )
    fig_map = px.choropleth(
        state_df, locations="state", locationmode="USA-states",
        color="net_sales", scope="usa",
        color_continuous_scale=[[0, "#16213e"], [0.5, WMT_BLUE], [1, WMT_YELLOW]],
        labels={"net_sales": "Net Sales"},
    )
    fig_map.update_layout(**PLOT_LAYOUT, coloraxis_colorbar=dict(tickformat="$,.0f", len=0.6))
    fig_map.update_geos(bgcolor="rgba(0,0,0,0)", lakecolor="rgba(0,0,0,0)",
                        landcolor="#1a1a2e", coastlinecolor="#444", showcoastlines=True)

    # Top items
    items_df = (
        dl._sales_raw[
            (dl._sales_raw["week_start_date"] >= start) &
            (dl._sales_raw["week_start_date"] <= end) &
            (dl._sales_raw["category_name"].isin(cats))
        ]
        .groupby(["item_id","category_name"], as_index=False)["net_sales"].sum()
        .merge(dl.dim_item[["item_id","item_name"]], on="item_id")
        .nlargest(10, "net_sales")
        .sort_values("net_sales")
    )
    items_df["label"] = items_df["item_name"].str[:25] + "…"
    fig_items = px.bar(
        items_df, x="net_sales", y="label", orientation="h",
        color="category_name", color_discrete_sequence=px.colors.qualitative.Bold,
        labels={"net_sales":"Net Sales","label":""},
    )
    fig_items.update_layout(**PLOT_LAYOUT, xaxis_tickformat="$,.0f", showlegend=False)
    fig_items.update_traces(marker_line_width=0)

    return fig_trend, fig_map, fig_items
