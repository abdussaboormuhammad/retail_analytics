import dash
from dash import dcc, html, Input, Output, callback
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import data_loader as dl

dash.register_page(__name__, path="/ecommerce-fulfillment", name="eCommerce & Fulfillment", order=3)

WMT_BLUE   = "#0071CE"
WMT_YELLOW = "#FFC220"
CARD_BG    = "#16213e"

PLOT_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#ccc", size=11),
    margin=dict(l=40, r=20, t=10, b=40),
    legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=10)),
)

FUNNEL_ORDER = ["page_view","product_view","add_to_cart","begin_checkout","purchase"]
FUNNEL_LABELS = {
    "page_view":      "Page Views",
    "product_view":   "Product Views",
    "add_to_cart":    "Add to Cart",
    "begin_checkout": "Begin Checkout",
    "purchase":       "Purchases",
}

def kpi_card(title, value, color=WMT_BLUE):
    return dbc.Card(
        dbc.CardBody([
            html.H6(title, className="text-muted mb-1", style={"fontSize":"0.75rem","letterSpacing":"0.05em"}),
            html.H3(value, style={"color": color, "fontWeight":"700","margin":"0"}),
        ]),
        style={"background": CARD_BG, "border": f"1px solid {color}33", "borderRadius":"12px", "textAlign":"center"},
    )

def card(header, graph_id, height=300):
    return dbc.Card([
        dbc.CardHeader(header, style={"color": WMT_YELLOW, "background": CARD_BG, "border":"none"}),
        dbc.CardBody(dcc.Loading(dcc.Graph(id=graph_id, style={"height":f"{height}px"}))),
    ], style={"background": CARD_BG, "border": f"1px solid {WMT_BLUE}33", "borderRadius":"12px"})


layout = html.Div([
    dbc.Row([
        dbc.Col(html.H4("eCommerce & Fulfillment", style={"color": WMT_YELLOW, "fontWeight":"700"}), width=6),
        dbc.Col([
            html.Label("Fulfillment Type", style={"color":"#aaa","fontSize":"0.8rem"}),
            dcc.Dropdown(
                id="ec-ftype",
                options=[{"label":"All","value":"ALL"}] +
                        [{"label":t,"value":t} for t in sorted(dl.fact_opd["fulfillment_type"].unique())],
                value="ALL", clearable=False,
                style={"background":"#0d1117","color":"#eee","minWidth":"220px"},
            ),
        ], width=3),
        dbc.Col([
            html.Label("Device Type", style={"color":"#aaa","fontSize":"0.8rem"}),
            dcc.Dropdown(
                id="ec-device",
                options=[{"label":"All","value":"ALL"}] +
                        [{"label":d,"value":d} for d in sorted(dl._click_raw["device_type"].unique())],
                value="ALL", clearable=False,
                style={"background":"#0d1117","color":"#eee","minWidth":"180px"},
            ),
        ], width=3),
    ], className="mb-3 align-items-end g-3"),

    # KPI row
    dbc.Row(id="ec-kpi-row", className="g-3 mb-4"),

    dbc.Row([
        dbc.Col(card("Conversion Funnel", "ec-funnel", 310), width=5),
        dbc.Col(card("Weekly Conversion Rate Trend", "ec-conversion-trend", 310), width=7),
    ], className="g-3 mb-4"),

    dbc.Row([
        dbc.Col(card("Avg Order Value by Fulfillment Type", "ec-aov-bar", 280), width=5),
        dbc.Col(card("Top Search Terms", "ec-search-terms", 280), width=4),
        dbc.Col(card("Device Mix", "ec-device-pie", 280), width=3),
    ], className="g-3"),
], style={"padding":"16px"})


@callback(
    Output("ec-kpi-row",          "children"),
    Output("ec-funnel",           "figure"),
    Output("ec-conversion-trend", "figure"),
    Output("ec-aov-bar",          "figure"),
    Output("ec-search-terms",     "figure"),
    Output("ec-device-pie",       "figure"),
    Input("ec-ftype",             "value"),
    Input("ec-device",            "value"),
)
def update_ec(ftype, device):
    # OPD filtered
    opd = dl.fact_opd.copy()
    if ftype != "ALL":
        opd = opd[opd["fulfillment_type"] == ftype]

    sla_pct  = opd["sla_met"].mean() * 100 if len(opd) else 0
    avg_rating = opd["customer_rating"].mean() if len(opd) else 0
    total_orders = len(opd)
    avg_aov = opd["order_total"].mean() if len(opd) else 0

    click = dl.click_funnel_totals.copy()
    trend = dl.conversion_trend.copy()

    # Clickstream device filter on pre-agg (device filter approximated via device mix)
    device_df = dl.click_device.copy()
    if device != "ALL":
        device_df = device_df[device_df["device_type"] == device]

    # KPI cards
    kpi_row = [
        dbc.Col(kpi_card("Total Orders", f"{total_orders:,}", WMT_YELLOW), width=True),
        dbc.Col(kpi_card("Avg Order Value", f"${avg_aov:.2f}", WMT_BLUE), width=True),
        dbc.Col(kpi_card("SLA Achievement", f"{sla_pct:.1f}%", WMT_YELLOW), width=True),
        dbc.Col(kpi_card("Avg Customer Rating", f"{avg_rating:.2f} ⭐", WMT_BLUE), width=True),
    ]

    # Funnel
    funnel_data = []
    for et in FUNNEL_ORDER:
        row = click[click["event_type"] == et]
        funnel_data.append({
            "stage": FUNNEL_LABELS.get(et, et),
            "count": int(row["count"].iloc[0]) if len(row) else 0,
        })
    funnel_df = pd.DataFrame(funnel_data)
    fig_funnel = go.Figure(go.Funnel(
        y=funnel_df["stage"], x=funnel_df["count"],
        textinfo="value+percent initial",
        marker=dict(color=[WMT_YELLOW, WMT_BLUE, "#00b4d8", "#90e0ef", "#48cae4"]),
        connector=dict(line=dict(color="#444", width=1)),
    ))
    fig_funnel.update_layout(**PLOT_LAYOUT)

    # Conversion trend
    fig_trend = go.Figure()
    fig_trend.add_trace(go.Scatter(
        x=trend["week"], y=trend["conversion_rate"],
        mode="lines+markers", name="Conv Rate %",
        line=dict(color=WMT_YELLOW, width=2),
        fill="tozeroy", fillcolor=f"{WMT_YELLOW}22",
    ))
    fig_trend.update_layout(**PLOT_LAYOUT, yaxis_title="Conversion Rate (%)",
                             yaxis_ticksuffix="%", xaxis_title="")

    # AOV by fulfillment type
    opd_aov = opd.groupby("fulfillment_type", as_index=False).agg(
        avg_order_total=("order_total","mean"),
        sla_met_pct=("sla_met","mean"),
        orders=("order_id","count"),
    )
    opd_aov["sla_met_pct"] *= 100
    opd_aov = opd_aov.sort_values("avg_order_total", ascending=True)
    fig_aov = px.bar(
        opd_aov, x="avg_order_total", y="fulfillment_type", orientation="h",
        color="sla_met_pct",
        color_continuous_scale=[[0,"#c0392b"],[0.5,WMT_BLUE],[1,WMT_YELLOW]],
        labels={"avg_order_total":"Avg Order ($)","fulfillment_type":"","sla_met_pct":"SLA %"},
        text="avg_order_total",
    )
    fig_aov.update_traces(texttemplate="$%{text:.2f}", textposition="outside", marker_line_width=0)
    fig_aov.update_layout(**PLOT_LAYOUT, xaxis_tickformat="$,.0f",
                           coloraxis_colorbar=dict(title="SLA %", ticksuffix="%"))

    # Top search terms
    fig_search = px.bar(
        dl.click_search_terms.sort_values("count"), x="count", y="search_term",
        orientation="h",
        color="count", color_continuous_scale=[[0, WMT_BLUE],[1, WMT_YELLOW]],
        labels={"count":"Searches","search_term":""},
    )
    fig_search.update_layout(**PLOT_LAYOUT, coloraxis_showscale=False)
    fig_search.update_traces(marker_line_width=0)

    # Device mix pie
    fig_device = px.pie(
        device_df, names="device_type", values="count",
        color_discrete_sequence=[WMT_BLUE, WMT_YELLOW, "#00b4d8"],
        hole=0.45,
    )
    fig_device.update_traces(textposition="inside", textinfo="percent+label",
                              textfont=dict(size=11))
    fig_device.update_layout(**PLOT_LAYOUT, showlegend=False)

    return kpi_row, fig_funnel, fig_trend, fig_aov, fig_search, fig_device
