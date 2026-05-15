import dash
from dash import dcc, html, Input, Output, callback
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import data_loader as dl

dash.register_page(__name__, path="/inventory-supply-chain", name="Inventory & Supply Chain", order=2)

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
        dbc.Col(html.H4("Inventory & Supply Chain", style={"color": WMT_YELLOW, "fontWeight":"700"}), width=6),
        dbc.Col([
            html.Label("Region", style={"color":"#aaa","fontSize":"0.8rem"}),
            dcc.Dropdown(
                id="inv-region",
                options=[{"label":"All Regions","value":"ALL"}] +
                        [{"label":r,"value":r} for r in dl.REGIONS],
                value="ALL", clearable=False,
                style={"background":"#0d1117","color":"#eee","minWidth":"200px"},
            ),
        ], width=3),
        dbc.Col([
            html.Label("Category", style={"color":"#aaa","fontSize":"0.8rem"}),
            dcc.Dropdown(
                id="inv-category",
                options=[{"label":"All Categories","value":"ALL"}] +
                        [{"label":c,"value":c} for c in dl.CATEGORIES],
                value="ALL", clearable=False,
                style={"background":"#0d1117","color":"#eee","minWidth":"200px"},
            ),
        ], width=3),
    ], className="mb-4 align-items-end g-3"),

    dbc.Row([
        dbc.Col(card("Days-of-Supply Distribution", "inv-dos-hist", 290), width=6),
        dbc.Col(card("In-Stock Rate by Category", "inv-instock-bar", 290), width=6),
    ], className="g-3 mb-4"),

    dbc.Row([
        dbc.Col(card("Inventory Turns by Category", "inv-turns-bar", 290), width=5),
        dbc.Col(card("OTIF % by Vendor (Top 20)", "inv-otif-treemap", 290), width=7),
    ], className="g-3 mb-4"),

    dbc.Row([
        dbc.Col(card("Fill Rate % by DC / FC", "inv-fillrate-bar", 290), width=12),
    ], className="g-3"),
], style={"padding":"16px"})


@callback(
    Output("inv-dos-hist",       "figure"),
    Output("inv-instock-bar",    "figure"),
    Output("inv-turns-bar",      "figure"),
    Output("inv-otif-treemap",   "figure"),
    Output("inv-fillrate-bar",   "figure"),
    Input("inv-region",          "value"),
    Input("inv-category",        "value"),
)
def update_inv(region, category):
    dos_df = dl.inv_dos_sample.copy()
    ins_df = dl.inv_instock.copy()
    trn_df = dl.inv_turns.copy()

    if category != "ALL":
        dos_df = dos_df[dos_df["category_name"] == category]
        ins_df = ins_df[ins_df["category_name"] == category]
        trn_df = trn_df[trn_df["category_name"] == category]

    # DOS histogram
    fig_dos = px.histogram(
        dos_df, x="days_of_supply", color="category_name",
        nbins=50, barmode="overlay", opacity=0.7,
        color_discrete_sequence=px.colors.qualitative.Bold,
        labels={"days_of_supply":"Days of Supply","count":"Count"},
    )
    fig_dos.update_layout(**PLOT_LAYOUT, bargap=0.02)
    fig_dos.update_traces(marker_line_width=0)

    # In-stock bar
    ins_sorted = ins_df.sort_values("in_stock_rate")
    fig_ins = px.bar(
        ins_sorted, x="in_stock_rate", y="category_name", orientation="h",
        color="in_stock_rate",
        color_continuous_scale=[[0,"#c0392b"],[0.5, WMT_BLUE],[1, WMT_YELLOW]],
        labels={"in_stock_rate":"In-Stock %","category_name":""},
        text="in_stock_rate",
    )
    fig_ins.update_traces(texttemplate="%{text:.1f}%", textposition="outside", marker_line_width=0)
    fig_ins.update_layout(**PLOT_LAYOUT, xaxis_range=[0,105], xaxis_ticksuffix="%",
                          coloraxis_showscale=False)

    # Inventory turns
    trn_sorted = trn_df.sort_values("inv_turn_rate")
    fig_turns = px.bar(
        trn_sorted, x="category_name", y="inv_turn_rate",
        color="inv_turn_rate",
        color_continuous_scale=[[0, WMT_BLUE],[1, WMT_YELLOW]],
        labels={"inv_turn_rate":"Turns","category_name":""},
        text="inv_turn_rate",
    )
    fig_turns.update_traces(texttemplate="%{text:.1f}x", textposition="outside", marker_line_width=0)
    fig_turns.update_layout(**PLOT_LAYOUT, coloraxis_showscale=False,
                             xaxis_tickangle=-30)

    # OTIF treemap — top 20 vendors
    otif_v = dl.otif_vendor.nlargest(20, "total_pos").copy()
    otif_v["label"] = otif_v["vendor_id"] + "<br>" + otif_v["otif_pct"].round(1).astype(str) + "%"
    fig_otif = px.treemap(
        otif_v, path=["vendor_id"], values="total_pos",
        color="otif_pct",
        color_continuous_scale=[[0,"#c0392b"],[0.5, WMT_BLUE],[1, WMT_YELLOW]],
        labels={"otif_pct":"OTIF %","total_pos":"POs"},
    )
    fig_otif.update_layout(**PLOT_LAYOUT, margin=dict(l=10,r=10,t=10,b=10))
    fig_otif.update_traces(textinfo="label+value", textfont=dict(size=11))

    # Fill rate by DC
    fill_df = dl.otif_dc.copy()
    if region != "ALL":
        fill_df = fill_df[fill_df["region"] == region]
    fill_df = fill_df.sort_values("fill_rate")
    fig_fill = px.bar(
        fill_df, x="center_name", y="fill_rate",
        color="region",
        color_discrete_sequence=[WMT_BLUE, WMT_YELLOW, "#00b4d8", "#90e0ef", "#ff9f1c"],
        labels={"fill_rate":"Fill Rate %","center_name":"Center"},
        text="fill_rate",
    )
    fig_fill.update_traces(texttemplate="%{text:.1f}%", textposition="outside", marker_line_width=0)
    fig_fill.update_layout(**PLOT_LAYOUT, xaxis_tickangle=-30, yaxis_range=[0,110],
                            yaxis_ticksuffix="%")

    return fig_dos, fig_ins, fig_turns, fig_otif, fig_fill
