import dash
from dash import dcc, html, Input, Output, callback
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import khc_loader as kl

dash.register_page(__name__, path="/trade-promotion", name="Trade Promotion", order=3)

RED  = "#CC0000"
GOLD = "#F5A623"
CARD = "#232323"
TEXT = "#E8E8E8"
MUTED= "#9A9A9A"
LAYOUT = dict(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
              font=dict(color=TEXT, size=11), margin=dict(l=40,r=20,t=20,b=40),
              legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=10)))

PROMO_COLORS = {"TPR":RED,"Feature":GOLD,"Display":"#00b4d8",
                "Feature + Display":"#2ecc71","TPR + Feature":"#9b59b6"}

def card(title, gid, h=290):
    return dbc.Card([
        dbc.CardHeader(title, style={"color":GOLD,"background":CARD,"border":"none","fontWeight":"600","fontSize":"0.85rem"}),
        dbc.CardBody(dcc.Loading(dcc.Graph(id=gid, style={"height":f"{h}px"}),color=RED)),
    ], style={"background":CARD,"border":f"1px solid {RED}22","borderRadius":"10px"})

def kpi(label, val, sub=None, color=GOLD):
    return dbc.Card(dbc.CardBody([
        html.P(label, style={"color":MUTED,"fontSize":"0.7rem","margin":"0","textTransform":"uppercase","letterSpacing":"0.05em"}),
        html.H3(val, style={"color":color,"fontWeight":"800","margin":"4px 0 0"}),
        html.P(sub, style={"color":MUTED,"fontSize":"0.72rem","margin":"0"}) if sub else None,
    ]), style={"background":CARD,"border":f"1px solid {color}33","borderRadius":"10px"})


layout = html.Div([
    html.Div([
        html.Div([
            html.H4("Trade Promotion Analysis", style={"color":RED,"fontWeight":"800","margin":"0"}),
            html.P("Execution compliance · Volume lift · Spend efficiency · ROI by event type", style={"color":MUTED,"margin":"0","fontSize":"0.82rem"}),
        ]),
        html.Div([
            html.Label("Retailer", style={"color":MUTED,"fontSize":"0.72rem","display":"block"}),
            dcc.Dropdown(id="tp-retailer",
                options=[{"label":"All Retailers","value":"ALL"}]+[{"label":r[1],"value":r[0]} for r in kl.RETAILERS_LIST],
                value="ALL", clearable=False, style={"minWidth":"200px","fontSize":"0.82rem"}),
        ]),
        html.Div([
            html.Label("Brand", style={"color":MUTED,"fontSize":"0.72rem","display":"block"}),
            dcc.Dropdown(id="tp-brand",
                options=[{"label":"All Brands","value":"ALL"}]+[{"label":b[1],"value":b[0]} for b in kl.BRANDS_LIST],
                value="ALL", clearable=False, style={"minWidth":"200px","fontSize":"0.82rem"}),
        ]),
        html.Div([
            html.Label("Promo Type", style={"color":MUTED,"fontSize":"0.72rem","display":"block"}),
            dcc.Dropdown(id="tp-ptype",
                options=[{"label":"All Types","value":"ALL"}] + [{"label":t,"value":t} for t in sorted(kl.promo["promo_type"].unique())],
                value="ALL", clearable=False, style={"minWidth":"200px","fontSize":"0.82rem"}),
        ]),
    ], style={"display":"flex","alignItems":"flex-end","gap":"16px","marginBottom":"20px"}),

    dbc.Row(id="tp-kpis", className="g-2 mb-3"),

    dbc.Row([
        dbc.Col(card("Weekly Promo Events & Compliance Trend","tp-weekly-trend",300), width=8),
        dbc.Col(card("Event Count by Type","tp-type-pie",300), width=4),
    ], className="g-3 mb-3"),

    dbc.Row([
        dbc.Col(card("Compliance % vs. Volume Lift — by Retailer","tp-scatter-ret",290), width=6),
        dbc.Col(card("Avg Compliance & Lift by Promo Type","tp-type-bar",290), width=6),
    ], className="g-3 mb-3"),

    dbc.Row([
        dbc.Col(card("Promo Spend & Incremental Units by Brand","tp-brand-spend",280), width=7),
        dbc.Col(card("Holiday vs. Non-Holiday Lift Factor","tp-holiday",280), width=5),
    ], className="g-3"),
], style={"padding":"20px"})


@callback(
    Output("tp-kpis",          "children"),
    Output("tp-weekly-trend",  "figure"),
    Output("tp-type-pie",      "figure"),
    Output("tp-scatter-ret",   "figure"),
    Output("tp-type-bar",      "figure"),
    Output("tp-brand-spend",   "figure"),
    Output("tp-holiday",       "figure"),
    Input("tp-retailer",       "value"),
    Input("tp-brand",          "value"),
    Input("tp-ptype",          "value"),
)
def update_tp(rid, bid, ptype):
    p = kl.promo.copy()
    if rid   != "ALL": p = p[p["retailer_id"] == rid]
    if bid   != "ALL": p = p[p["brand_id"]    == bid]
    if ptype != "ALL": p = p[p["promo_type"]  == ptype]

    avg_comp  = p["compliance_pct"].mean() if len(p) else 0
    avg_lift  = p["volume_lift_factor"].mean() if len(p) else 0
    tot_spend = p["promo_spend_dollars"].sum() if len(p) else 0
    tot_incr  = p["incremental_units"].sum() if len(p) else 0
    cost_per_unit = tot_spend / max(tot_incr, 1)
    n_events = len(p)

    kpis = [
        dbc.Col(kpi("Total Events", f"{n_events:,}", color=GOLD), width=True),
        dbc.Col(kpi("Avg Compliance", f"{avg_comp:.1f}%",
                    "Industry avg: ~60%", RED if avg_comp<60 else GOLD), width=True),
        dbc.Col(kpi("Avg Volume Lift", f"{avg_lift:.2f}x", "vs. baseline", GOLD), width=True),
        dbc.Col(kpi("Promo Spend", f"${tot_spend/1e3:.1f}K", color=RED), width=True),
        dbc.Col(kpi("Cost/Incr. Unit", f"${cost_per_unit:.2f}", color=GOLD), width=True),
    ]

    # Weekly trend
    wk = p.groupby(["fiscal_week","week_start_date"], as_index=False).agg(
        events=("promo_id","count"),
        avg_compliance=("compliance_pct","mean"),
        avg_lift=("volume_lift_factor","mean"),
        spend=("promo_spend_dollars","sum"))
    wk["week_start_date"] = pd.to_datetime(wk["week_start_date"])

    fig_wk = go.Figure()
    fig_wk.add_trace(go.Bar(x=wk["week_start_date"], y=wk["events"],
        name="Events", marker_color=RED, marker_line_width=0,
        yaxis="y", opacity=0.6))
    fig_wk.add_trace(go.Scatter(x=wk["week_start_date"], y=wk["avg_compliance"],
        name="Compliance %", line=dict(color=GOLD,width=2), yaxis="y2"))
    fig_wk.update_layout(**LAYOUT,
        yaxis=dict(title="# Events",color=RED,showgrid=False),
        yaxis2=dict(title="Compliance %", overlaying="y", side="right",
                    color=GOLD, range=[0,105], ticksuffix="%"),
        xaxis_title="")
    # Mark holiday weeks
    for _, row in kl.dim_calendar[kl.dim_calendar["is_holiday_week"]].iterrows():
        fig_wk.add_vline(x=str(row["week_start_date"])[:10], line=dict(color="#555",dash="dot",width=1))

    # Event type pie
    type_cnt = p.groupby("promo_type", as_index=False).size().rename(columns={"size":"count"})
    fig_pie = go.Figure(go.Pie(
        labels=type_cnt["promo_type"], values=type_cnt["count"],
        marker_colors=[PROMO_COLORS.get(t, "#888") for t in type_cnt["promo_type"]],
        hole=0.5, textinfo="percent+label", textfont=dict(size=9)))
    fig_pie.update_layout(**LAYOUT, showlegend=False)

    # Scatter: compliance vs lift by retailer
    ret_sc = p.groupby(["retailer_id","retailer_name"], as_index=False).agg(
        compliance=("compliance_pct","mean"),
        lift=("volume_lift_factor","mean"),
        events=("promo_id","count"),
        spend=("promo_spend_dollars","sum"))
    fig_sc = px.scatter(ret_sc, x="compliance", y="lift", size="events",
        text="retailer_name", color="spend",
        color_continuous_scale=[[0,"#c0392b"],[0.5,RED],[1,GOLD]],
        size_max=35,
        labels={"compliance":"Avg Compliance %","lift":"Avg Lift Factor","spend":"Total Spend $"})
    fig_sc.update_traces(textposition="top center", textfont=dict(size=8,color=TEXT),
                         marker_line_width=0)
    fig_sc.add_hline(y=avg_lift, line=dict(color="#555",dash="dot",width=1))
    fig_sc.add_vline(x=avg_comp, line=dict(color="#555",dash="dot",width=1))
    fig_sc.update_layout(**LAYOUT, xaxis_ticksuffix="%",
        coloraxis_colorbar=dict(title="Spend $",len=0.6))

    # Promo type performance bar
    type_perf = p.groupby("promo_type", as_index=False).agg(
        compliance=("compliance_pct","mean"),
        lift=("volume_lift_factor","mean"),
        disc=("actual_discount_pct","mean"))
    fig_type = go.Figure()
    fig_type.add_trace(go.Bar(name="Compliance %", x=type_perf["promo_type"],
        y=type_perf["compliance"],
        marker_color=[PROMO_COLORS.get(t,RED) for t in type_perf["promo_type"]],
        marker_line_width=0, text=type_perf["compliance"].round(1),
        texttemplate="%{text:.1f}%", textposition="outside", yaxis="y"))
    fig_type.add_trace(go.Scatter(name="Lift Factor", x=type_perf["promo_type"],
        y=type_perf["lift"], mode="markers+lines",
        marker=dict(color=GOLD, size=10, symbol="diamond"), line=dict(color=GOLD,width=2),
        yaxis="y2"))
    fig_type.update_layout(**LAYOUT, barmode="group",
        yaxis=dict(title="Compliance %",ticksuffix="%",showgrid=False),
        yaxis2=dict(title="Lift Factor", overlaying="y", side="right", color=GOLD))

    # Brand spend vs incremental
    brand_sp = p.groupby("brand_name", as_index=False).agg(
        spend=("promo_spend_dollars","sum"),
        incr=("incremental_units","sum"),
        lift=("volume_lift_factor","mean"))
    brand_sp["roi"] = (brand_sp["incr"] / brand_sp["spend"].replace(0,1)).round(3)
    brand_sp = brand_sp.sort_values("spend", ascending=True)
    fig_brand = go.Figure()
    fig_brand.add_trace(go.Bar(y=brand_sp["brand_name"], x=brand_sp["spend"],
        orientation="h", name="Promo Spend $", marker_color=RED, marker_line_width=0,
        text=brand_sp["spend"].apply(lambda x: f"${x/1e3:.1f}K"), textposition="outside"))
    fig_brand.add_trace(go.Scatter(y=brand_sp["brand_name"], x=brand_sp["roi"]*5000,
        mode="markers", name="ROI (scaled)", marker=dict(color=GOLD, size=8, symbol="diamond"),
        xaxis="x2"))
    fig_brand.update_layout(**LAYOUT, barmode="group",
        xaxis=dict(title="Promo Spend ($)", tickformat="$,.0f"),
        xaxis2=dict(overlaying="x", side="top", title="ROI (units/$ scaled)"))

    # Holiday vs non-holiday
    p["holiday_flag"] = p["is_holiday_promo"].map({True:"Holiday Week",False:"Non-Holiday"})
    hol = p.groupby(["holiday_flag","promo_type"], as_index=False).agg(
        avg_lift=("volume_lift_factor","mean"),
        avg_comp=("compliance_pct","mean"),
        count=("promo_id","count"))
    fig_hol = px.bar(hol, x="promo_type", y="avg_lift", color="holiday_flag",
        barmode="group", text="avg_lift",
        color_discrete_map={"Holiday Week":GOLD,"Non-Holiday":RED},
        labels={"avg_lift":"Avg Lift Factor","promo_type":"","holiday_flag":""})
    fig_hol.update_traces(texttemplate="%{text:.2f}x", textposition="outside", marker_line_width=0)
    fig_hol.update_layout(**LAYOUT)

    return kpis, fig_wk, fig_pie, fig_sc, fig_type, fig_brand, fig_hol
