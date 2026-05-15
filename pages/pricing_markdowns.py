import dash
from dash import dcc, html, Input, Output, callback
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import data_loader as dl

dash.register_page(__name__, path="/pricing-markdowns", name="Pricing & Markdowns", order=4)

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
        dbc.Col(html.H4("Pricing & Markdowns", style={"color": WMT_YELLOW, "fontWeight":"700"}), width=5),
        dbc.Col([
            html.Label("Category", style={"color":"#aaa","fontSize":"0.8rem"}),
            dcc.Dropdown(
                id="pm-category",
                options=[{"label":"All Categories","value":"ALL"}] +
                        [{"label":c,"value":c} for c in dl.CATEGORIES],
                value="ALL", clearable=False,
                style={"background":"#0d1117","color":"#eee","minWidth":"200px"},
            ),
        ], width=3),
        dbc.Col([
            html.Label("Event Type", style={"color":"#aaa","fontSize":"0.8rem"}),
            dcc.Dropdown(
                id="pm-event-type",
                options=[{"label":"All","value":"ALL"}] +
                        [{"label":t,"value":t} for t in sorted(dl.fact_markdown["event_type"].unique())],
                value="ALL", clearable=False,
                style={"background":"#0d1117","color":"#eee","minWidth":"180px"},
            ),
        ], width=3),
        dbc.Col([
            html.Label("Region", style={"color":"#aaa","fontSize":"0.8rem"}),
            dcc.Dropdown(
                id="pm-region",
                options=[{"label":"All Regions","value":"ALL"}] +
                        [{"label":r,"value":r} for r in dl.REGIONS],
                value="ALL", clearable=False,
                style={"background":"#0d1117","color":"#eee","minWidth":"180px"},
            ),
        ], width=1),
    ], className="mb-4 align-items-end g-3"),

    dbc.Row([
        dbc.Col(card("Markdown Depth Distribution", "pm-depth-hist", 290), width=5),
        dbc.Col(card("Markdown Revenue Impact by Category", "pm-revenue-cat", 290), width=7),
    ], className="g-3 mb-4"),

    dbc.Row([
        dbc.Col(card("Price Index vs Competitor Price", "pm-price-scatter", 300), width=7),
        dbc.Col(card("Revenue by Event Type", "pm-event-type-bar", 300), width=5),
    ], className="g-3 mb-4"),

    dbc.Row([
        dbc.Col(card("Markdown Event Timeline (Sample)", "pm-gantt", 280), width=12),
    ], className="g-3"),
], style={"padding":"16px"})


@callback(
    Output("pm-depth-hist",    "figure"),
    Output("pm-revenue-cat",   "figure"),
    Output("pm-price-scatter", "figure"),
    Output("pm-event-type-bar","figure"),
    Output("pm-gantt",         "figure"),
    Input("pm-category",       "value"),
    Input("pm-event-type",     "value"),
    Input("pm-region",         "value"),
)
def update_pm(category, etype, region):
    md = dl.markdown_df.copy()
    if category != "ALL": md = md[md["category_name"] == category]
    if etype    != "ALL": md = md[md["event_type"]    == etype]
    if region   != "ALL": md = md[md["region"]        == region]

    # Markdown depth histogram
    fig_hist = px.histogram(
        md[md["markdown_depth"] > 0],
        x="markdown_depth", color="event_type", nbins=40,
        barmode="overlay", opacity=0.75,
        color_discrete_sequence=[WMT_YELLOW, WMT_BLUE, "#00b4d8", "#ff9f1c"],
        labels={"markdown_depth":"Markdown Depth (%)","count":"Count"},
    )
    fig_hist.update_layout(**PLOT_LAYOUT, xaxis_ticksuffix="%", bargap=0.02)
    fig_hist.update_traces(marker_line_width=0)

    # Revenue by category (horizontal bar)
    rev_cat = (
        md.groupby("category_name", as_index=False)
        .agg(revenue=("revenue_during_event","sum"), events=("event_id","count"))
        .sort_values("revenue")
    )
    fig_rev = px.bar(
        rev_cat, x="revenue", y="category_name", orientation="h",
        color="events",
        color_continuous_scale=[[0, WMT_BLUE],[1, WMT_YELLOW]],
        labels={"revenue":"Revenue ($)","category_name":"","events":"# Events"},
        text="revenue",
    )
    fig_rev.update_traces(texttemplate="$%{text:,.0f}", textposition="outside", marker_line_width=0)
    fig_rev.update_layout(**PLOT_LAYOUT, xaxis_tickformat="$,.0f")

    # Price scatter — filtered by category
    scatter_df = dl.pricing_scatter.copy()
    if category != "ALL":
        scatter_df = scatter_df[scatter_df["category_name"] == category]
    fig_scatter = px.scatter(
        scatter_df, x="competitor_price", y="regular_price",
        color="category_name", symbol="price_type",
        opacity=0.6, size_max=8,
        color_discrete_sequence=px.colors.qualitative.Bold,
        labels={"competitor_price":"Competitor Price ($)","regular_price":"Our Price ($)"},
        hover_data={"price_index":True,"price_type":True},
    )
    # 1:1 line
    max_p = max(scatter_df["competitor_price"].max(), scatter_df["regular_price"].max()) if len(scatter_df) else 200
    fig_scatter.add_shape(type="line", x0=0,y0=0,x1=max_p,y1=max_p,
                          line=dict(color="#555",dash="dot",width=1))
    fig_scatter.update_layout(**PLOT_LAYOUT, xaxis_tickformat="$,.0f", yaxis_tickformat="$,.0f")

    # Revenue by event type
    evt_rev = (
        md.groupby("event_type", as_index=False)
        .agg(revenue=("revenue_during_event","sum"), events=("event_id","count"),
             avg_depth=("markdown_depth","mean"))
        .sort_values("revenue", ascending=True)
    )
    fig_evt = px.bar(
        evt_rev, x="revenue", y="event_type", orientation="h",
        color="avg_depth",
        color_continuous_scale=[[0,WMT_BLUE],[1,WMT_YELLOW]],
        labels={"revenue":"Revenue ($)","event_type":"","avg_depth":"Avg Depth %"},
        text="revenue",
    )
    fig_evt.update_traces(texttemplate="$%{text:,.0f}", textposition="outside", marker_line_width=0)
    fig_evt.update_layout(**PLOT_LAYOUT, xaxis_tickformat="$,.0f",
                           coloraxis_colorbar=dict(title="Avg Depth %", ticksuffix="%"))

    # Gantt — sample of markdown events
    gantt_df = dl.md_gantt_sample.copy()
    if category != "ALL":
        gantt_df = gantt_df[gantt_df["category_name"] == category]
    gantt_df = gantt_df.sort_values("event_date").head(80)

    fig_gantt = go.Figure()
    colors = {
        "Markdown":  WMT_BLUE,
        "Clearance": "#e74c3c",
        "Rollback":  WMT_YELLOW,
        "Markup":    "#2ecc71",
    }
    for _, row in gantt_df.iterrows():
        fig_gantt.add_trace(go.Scatter(
            x=[row["event_date"], row["end_date"]],
            y=[row["category_name"], row["category_name"]],
            mode="lines",
            line=dict(color=colors.get(row["event_type"], WMT_BLUE), width=6),
            name=row["event_type"],
            showlegend=False,
            hovertemplate=(
                f"<b>{row['event_type']}</b><br>"
                f"Depth: {row['markdown_depth']:.1f}%<br>"
                f"{row['event_date']} → {row['end_date']}<extra></extra>"
            ),
        ))
    # Legend
    for etype, color in colors.items():
        fig_gantt.add_trace(go.Scatter(
            x=[None], y=[None], mode="lines",
            line=dict(color=color, width=4), name=etype,
        ))
    fig_gantt.update_layout(**PLOT_LAYOUT, xaxis_title="Date", yaxis_title="",
                             margin=dict(l=120,r=20,t=10,b=40))

    return fig_hist, fig_rev, fig_scatter, fig_evt, fig_gantt
