import dash
from dash import dcc, html, Input, Output, callback
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import khc_loader as kl

dash.register_page(__name__, path="/", name="Selling Story", order=0)

RED    = "#CC0000"
GOLD   = "#F5A623"
DARK   = "#1A1A1A"
CARD   = "#232323"
TEXT   = "#E8E8E8"
MUTED  = "#9A9A9A"

LAYOUT = dict(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
              font=dict(color=TEXT, size=11), margin=dict(l=40,r=20,t=20,b=40),
              legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=10)))

def kpi(label, val, delta=None, color=GOLD):
    delta_el = html.Span(delta, style={"color": "#2ecc71" if "+" in str(delta) else "#e74c3c",
                                        "fontSize":"0.78rem","marginLeft":"6px"}) if delta else None
    return dbc.Card(dbc.CardBody([
        html.P(label, style={"color":MUTED,"fontSize":"0.7rem","letterSpacing":"0.06em","margin":"0","textTransform":"uppercase"}),
        html.Div([html.H3(val, style={"color":color,"fontWeight":"800","margin":"4px 0 0","display":"inline"}), delta_el]),
    ]), style={"background":CARD,"border":f"1px solid {color}33","borderRadius":"10px","padding":"4px"})

def card(title, gid, h=300):
    return dbc.Card([
        dbc.CardHeader(title, style={"color":GOLD,"background":CARD,"border":"none","fontWeight":"600","fontSize":"0.85rem"}),
        dbc.CardBody(dcc.Loading(dcc.Graph(id=gid, style={"height":f"{h}px"}),color=RED)),
    ], style={"background":CARD,"border":f"1px solid {RED}22","borderRadius":"10px"})


layout = html.Div([
    # Header
    html.Div([
        html.Div([
            html.H3("Kraft Heinz Company", style={"color":RED,"fontWeight":"900","margin":"0","letterSpacing":"-0.02em"}),
            html.P("Annual Retail Selling Story  ·  FY 2024", style={"color":MUTED,"margin":"0","fontSize":"0.82rem"}),
        ]),
        html.Div([
            html.Label("Business Unit", style={"color":MUTED,"fontSize":"0.72rem","display":"block"}),
            dcc.Dropdown(id="ss-bu",
                options=[{"label":"All Business Units","value":"ALL"}]+[{"label":b,"value":b} for b in kl.BUS_LIST],
                value="ALL", clearable=False, style={"minWidth":"220px","fontSize":"0.82rem"}),
        ]),
        html.Div([
            html.Label("Quarter", style={"color":MUTED,"fontSize":"0.72rem","display":"block"}),
            dcc.Dropdown(id="ss-quarter",
                options=[{"label":"Full Year","value":"ALL"}]+[{"label":f"Q{q}","value":f"Q{q}"} for q in range(1,5)],
                value="ALL", clearable=False, style={"minWidth":"130px","fontSize":"0.82rem"}),
        ]),
    ], style={"display":"flex","alignItems":"flex-end","gap":"16px","marginBottom":"20px"}),

    # KPI Row
    dbc.Row(id="ss-kpis", className="g-2 mb-3"),

    # Row 1
    dbc.Row([
        dbc.Col(card("Weekly Net Sales Trend — KHC vs. Prior Year","ss-trend",300), width=8),
        dbc.Col(card("Volume on Promotion vs. Base","ss-promo-donut",300), width=4),
    ], className="g-3 mb-3"),

    # Row 2
    dbc.Row([
        dbc.Col(card("Brand Performance Scorecard (YoY %)","ss-scorecard",350), width=6),
        dbc.Col(card("Volume Driver Waterfall (YoY $ Change)","ss-waterfall",350), width=6),
    ], className="g-3 mb-3"),

    # Row 3
    dbc.Row([
        dbc.Col(card("Market Share by Category","ss-share-bar",280), width=5),
        dbc.Col(card("Gross Margin % by Brand","ss-margin",280), width=7),
    ], className="g-3"),
], style={"padding":"20px"})


@callback(
    Output("ss-kpis",      "children"),
    Output("ss-trend",     "figure"),
    Output("ss-promo-donut","figure"),
    Output("ss-scorecard", "figure"),
    Output("ss-waterfall", "figure"),
    Output("ss-share-bar", "figure"),
    Output("ss-margin",    "figure"),
    Input("ss-bu",         "value"),
    Input("ss-quarter",    "value"),
)
def update_ss(bu, quarter):
    s = kl.sales.copy()
    sc = kl.brand_scorecard.copy()
    vd = kl.vol_decomp.copy()
    wk = kl.sales_weekly_brand.copy()
    sh = kl.mshare[kl.mshare["entity_type"]=="KHC Brand"].copy()

    if bu != "ALL":
        s  = s[s["business_unit"]  == bu]
        sc = sc[sc["business_unit"] == bu]
        vd = vd[vd["business_unit"] == bu]
        wk = wk[wk["business_unit"] == bu]
        sh = sh[sh["business_unit"] == bu]

    if quarter != "ALL":
        s  = s[s["fiscal_quarter"]  == quarter]
        wk = wk[wk["fiscal_week"].between(
            {"Q1":1,"Q2":14,"Q3":27,"Q4":40}[quarter],
            {"Q1":13,"Q2":26,"Q3":39,"Q4":52}[quarter])]

    tot   = s["net_sales"].sum()
    prior = s["prior_yr_net_sales"].sum()
    yoy   = (tot-prior)/prior*100 if prior else 0
    gm    = s["gross_margin"].sum() / tot * 100 if tot else 0
    promo_pct = s[s["is_on_promo"]]["net_sales"].sum() / tot * 100 if tot else 0
    avg_disc = s[s["is_on_promo"]]["discount_pct"].mean() if s["is_on_promo"].any() else 0

    kpis = [
        dbc.Col(kpi("Net Sales", f"${tot/1e6:.1f}M", f"{'+'if yoy>=0 else ''}{yoy:.1f}% YoY", GOLD), width=True),
        dbc.Col(kpi("Gross Margin %", f"{gm:.1f}%", color=RED), width=True),
        dbc.Col(kpi("Promo Volume %", f"{promo_pct:.1f}%", color=GOLD), width=True),
        dbc.Col(kpi("Avg Promo Discount", f"{avg_disc:.1f}%", color=RED), width=True),
        dbc.Col(kpi("KHC Brands Tracked", str(s["brand_name"].nunique()), color=GOLD), width=True),
    ]

    # Trend
    wk_agg = wk.groupby(["fiscal_week","week_start_date"], as_index=False).agg(
        net_sales=("net_sales","sum"), prior_yr=("prior_yr","sum"))
    fig_trend = go.Figure()
    fig_trend.add_trace(go.Scatter(x=wk_agg["week_start_date"], y=wk_agg["net_sales"],
        name="FY2024", line=dict(color=RED, width=2.5), fill="tozeroy", fillcolor=f"{RED}18"))
    fig_trend.add_trace(go.Scatter(x=wk_agg["week_start_date"], y=wk_agg["prior_yr"],
        name="Prior Year", line=dict(color=GOLD, width=1.5, dash="dot")))
    fig_trend.update_layout(**LAYOUT, yaxis_tickformat="$,.0f", xaxis_title="")

    # Promo donut
    base_vol  = s[~s["is_on_promo"]]["net_sales"].sum()
    promo_vol = s[s["is_on_promo"]]["net_sales"].sum()
    fig_donut = go.Figure(go.Pie(
        labels=["Base Volume","Promotional Volume"],
        values=[base_vol, promo_vol],
        marker_colors=[RED, GOLD],
        hole=0.55, textinfo="percent+label", textfont=dict(size=10)))
    fig_donut.update_layout(**LAYOUT, showlegend=False,
        annotations=[dict(text="Volume\nMix", x=0.5,y=0.5,font=dict(size=11,color=TEXT),showarrow=False)])

    # Scorecard bubble
    sc_f = sc[sc["brand_name"].isin(s["brand_name"].unique())].copy()
    fig_sc = px.scatter(sc_f.dropna(subset=["acv_pct","yoy_pct"]),
        x="acv_pct", y="yoy_pct", size="net_sales", color="business_unit",
        text="brand_name", size_max=40,
        color_discrete_sequence=[RED, GOLD, "#00b4d8", "#2ecc71", "#9b59b6","#e67e22","#1abc9c","#e74c3c"],
        labels={"acv_pct":"ACV %","yoy_pct":"YoY Growth %","business_unit":"Business Unit"})
    fig_sc.add_hline(y=0, line=dict(color="#555",dash="dot",width=1))
    fig_sc.update_traces(textposition="top center", textfont=dict(size=8,color=TEXT))
    fig_sc.update_layout(**LAYOUT, yaxis_ticksuffix="%", xaxis_ticksuffix="%")

    # Waterfall
    vd_agg = vd.agg(dist=("distribution_driver","sum"), vel=("velocity_driver","sum"),
                    price=("price_mix_driver","sum"), promo=("promo_driver","sum"),
                    cur=("current_net_sales","sum"), prior=("prior_yr_net_sales","sum"))
    total_chg = vd_agg["cur"] - vd_agg["prior"]
    cats = ["Prior Year","Distribution","Velocity","Price/Mix","Promotions","Current Year"]
    vals = [vd_agg["prior"], vd_agg["dist"], vd_agg["vel"], vd_agg["price"], vd_agg["promo"], vd_agg["cur"]]
    measures = ["absolute","relative","relative","relative","relative","total"]
    colors_wf = [GOLD if v >= 0 else "#e74c3c" for v in vals]
    colors_wf[0] = RED; colors_wf[-1] = RED
    fig_wf = go.Figure(go.Waterfall(
        x=cats, y=vals, measure=measures,
        connector=dict(line=dict(color="#444",width=1)),
        increasing_marker_color=GOLD, decreasing_marker_color="#e74c3c",
        totals_marker_color=RED,
        text=[f"${v/1000:.0f}K" for v in vals], textposition="outside",
        textfont=dict(color=TEXT, size=9)))
    fig_wf.update_layout(**LAYOUT, yaxis_tickformat="$,.0f", showlegend=False)

    # Share bar by BU
    sh_agg = sh.groupby("business_unit", as_index=False).agg(share=("dollar_share_pct","mean")).sort_values("share")
    fig_share = px.bar(sh_agg, x="share", y="business_unit", orientation="h",
        color="share", color_continuous_scale=[[0,CARD],[0.4,RED],[1,GOLD]],
        text="share", labels={"share":"Mkt Share %","business_unit":""})
    fig_share.update_traces(texttemplate="%{text:.1f}%", textposition="outside", marker_line_width=0)
    fig_share.update_layout(**LAYOUT, xaxis_ticksuffix="%", coloraxis_showscale=False)

    # Margin by brand
    sc_mg = sc_f.sort_values("gm_pct").dropna(subset=["gm_pct"])
    fig_mg = px.bar(sc_mg, x="brand_name", y="gm_pct",
        color="gm_pct", color_continuous_scale=[[0,"#c0392b"],[0.5,RED],[1,GOLD]],
        text="gm_pct", labels={"gm_pct":"GM %","brand_name":""})
    fig_mg.update_traces(texttemplate="%{text:.1f}%", textposition="outside", marker_line_width=0)
    fig_mg.update_layout(**LAYOUT, yaxis_ticksuffix="%", coloraxis_showscale=False, xaxis_tickangle=-30)

    return kpis, fig_trend, fig_donut, fig_sc, fig_wf, fig_share, fig_mg
