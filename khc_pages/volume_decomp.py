import dash
from dash import dcc, html, Input, Output, callback
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import khc_loader as kl

dash.register_page(__name__, path="/volume-decomp", name="Volume Decomposition", order=4)

RED  = "#CC0000"
GOLD = "#F5A623"
CARD = "#232323"
TEXT = "#E8E8E8"
MUTED= "#9A9A9A"
LAYOUT = dict(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
              font=dict(color=TEXT, size=11), margin=dict(l=40,r=20,t=20,b=40),
              legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=10)))

DRIVER_COLORS = {
    "Distribution": "#00b4d8",
    "Velocity":     GOLD,
    "Price/Mix":    "#9b59b6",
    "Promotions":   "#2ecc71",
}

def card(title, gid, h=310):
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
            html.H4("Volume Decomposition", style={"color":RED,"fontWeight":"800","margin":"0"}),
            html.P("Identify what is driving growth or decline: Distribution · Velocity · Price/Mix · Promotions", style={"color":MUTED,"margin":"0","fontSize":"0.82rem"}),
        ]),
        html.Div([
            html.Label("Business Unit", style={"color":MUTED,"fontSize":"0.72rem","display":"block"}),
            dcc.Dropdown(id="vd-bu",
                options=[{"label":"All","value":"ALL"}]+[{"label":b,"value":b} for b in kl.BUS_LIST],
                value="ALL", clearable=False, style={"minWidth":"220px","fontSize":"0.82rem"}),
        ]),
        html.Div([
            html.Label("Retailer", style={"color":MUTED,"fontSize":"0.72rem","display":"block"}),
            dcc.Dropdown(id="vd-retailer",
                options=[{"label":"All Retailers","value":"ALL"}]+[{"label":r[1],"value":r[0]} for r in kl.RETAILERS_LIST],
                value="ALL", clearable=False, style={"minWidth":"200px","fontSize":"0.82rem"}),
        ]),
    ], style={"display":"flex","alignItems":"flex-end","gap":"16px","marginBottom":"20px"}),

    dbc.Row(id="vd-kpis", className="g-2 mb-3"),

    # Full-width waterfall
    dbc.Row([
        dbc.Col(card("Total KHC Volume Change Waterfall — Current vs. Prior Year","vd-waterfall-total",320), width=12),
    ], className="g-3 mb-3"),

    dbc.Row([
        dbc.Col(card("Volume Drivers by Brand","vd-drivers-brand",330), width=7),
        dbc.Col(card("Base vs. Incremental Volume Mix","vd-base-incr",330), width=5),
    ], className="g-3 mb-3"),

    dbc.Row([
        dbc.Col(card("YoY Growth % by Retailer","vd-ret-growth",280), width=5),
        dbc.Col(card("Driver Contribution % by Business Unit","vd-driver-pct",280), width=7),
    ], className="g-3"),
], style={"padding":"20px"})


@callback(
    Output("vd-kpis",            "children"),
    Output("vd-waterfall-total", "figure"),
    Output("vd-drivers-brand",   "figure"),
    Output("vd-base-incr",       "figure"),
    Output("vd-ret-growth",      "figure"),
    Output("vd-driver-pct",      "figure"),
    Input("vd-bu",               "value"),
    Input("vd-retailer",         "value"),
)
def update_vd(bu, rid):
    vd = kl.vol_decomp.copy()
    if bu  != "ALL": vd = vd[vd["business_unit"] == bu]
    if rid != "ALL": vd = vd[vd["retailer_id"]   == rid]

    tot_cur  = vd["current_net_sales"].sum()
    tot_py   = vd["prior_yr_net_sales"].sum()
    tot_chg  = tot_cur - tot_py
    yoy_pct  = (tot_chg / tot_py * 100) if tot_py else 0
    dist_drv = vd["distribution_driver"].sum()
    vel_drv  = vd["velocity_driver"].sum()
    pri_drv  = vd["price_mix_driver"].sum()
    prm_drv  = vd["promo_driver"].sum()
    base_vol = vd["base_volume"].sum()
    incr_vol = vd["incremental_volume"].sum()

    kpis = [
        dbc.Col(kpi("Net Sales (Current)", f"${tot_cur/1e3:.1f}K",
                    f"{'+'if yoy_pct>=0 else ''}{yoy_pct:.1f}% vs PY",
                    GOLD if yoy_pct>=0 else RED), width=True),
        dbc.Col(kpi("$ Change YoY", f"{'+'if tot_chg>=0 else ''}${abs(tot_chg)/1e3:.1f}K",
                    color=GOLD if tot_chg>=0 else RED), width=True),
        dbc.Col(kpi("Distribution Driver", f"{'+'if dist_drv>=0 else ''}${abs(dist_drv)/1e3:.0f}K",
                    "ACV & TDP change", "#00b4d8"), width=True),
        dbc.Col(kpi("Velocity Driver", f"{'+'if vel_drv>=0 else ''}${abs(vel_drv)/1e3:.0f}K",
                    "Units/store/wk", GOLD), width=True),
        dbc.Col(kpi("Promo Driver", f"{'+'if prm_drv>=0 else ''}${abs(prm_drv)/1e3:.0f}K",
                    "Incremental lift", "#2ecc71"), width=True),
    ]

    # Waterfall total
    cats     = ["Prior Year","Distribution","Velocity","Price/Mix","Promotions","Current Year"]
    vals     = [tot_py,       dist_drv,     vel_drv,  pri_drv,   prm_drv,    tot_cur]
    measures = ["absolute","relative","relative","relative","relative","total"]
    fmt      = [f"${v/1e3:.1f}K" for v in vals]
    fig_wf = go.Figure(go.Waterfall(
        x=cats, y=vals, measure=measures,
        text=fmt, textposition="outside", textfont=dict(color=TEXT, size=9),
        connector=dict(line=dict(color="#555",width=1,dash="dot")),
        increasing=dict(marker=dict(color=GOLD,line=dict(width=0))),
        decreasing=dict(marker=dict(color=RED, line=dict(width=0))),
        totals=dict(marker=dict(color="#333",line=dict(color=RED,width=2)))))
    fig_wf.update_layout(**LAYOUT, yaxis_tickformat="$,.0f", showlegend=False)

    # Drivers by brand
    by_brand = kl.vd_by_brand.copy()
    if bu  != "ALL": by_brand = by_brand[by_brand["business_unit"] == bu]
    if len(by_brand) == 0:
        by_brand = kl.vd_by_brand.copy()
    by_brand = by_brand.sort_values("total_chg")
    fig_db = go.Figure()
    for driver, col, color in [
        ("dist_driver","Distribution",DRIVER_COLORS["Distribution"]),
        ("vel_driver", "Velocity",    DRIVER_COLORS["Velocity"]),
        ("price_driver","Price/Mix",  DRIVER_COLORS["Price/Mix"]),
        ("promo_driver","Promotions", DRIVER_COLORS["Promotions"]),
    ]:
        fig_db.add_trace(go.Bar(
            y=by_brand["brand_name"], x=by_brand[driver],
            name=col, orientation="h",
            marker=dict(color=color, line=dict(width=0)),
            text=by_brand[driver].apply(lambda x: f"${x/1e3:.0f}K" if abs(x)>100 else ""),
            textposition="inside", textfont=dict(size=8)))
    fig_db.add_trace(go.Scatter(
        y=by_brand["brand_name"], x=by_brand["yoy_pct"],
        mode="markers+text", name="YoY %",
        marker=dict(color="#fff",size=7,symbol="diamond"),
        text=by_brand["yoy_pct"].apply(lambda x: f"{x:+.1f}%"),
        textposition="middle right", textfont=dict(size=8,color="#fff"),
        xaxis="x2"))
    fig_db.update_layout(**LAYOUT, barmode="relative",
        xaxis=dict(title="$ Change (Drivers)", tickformat="$,.0f"),
        xaxis2=dict(overlaying="x", side="top", title="YoY %", ticksuffix="%"))

    # Base vs incremental donut
    fig_bi = go.Figure()
    fig_bi.add_trace(go.Pie(
        labels=["Base Volume","Incremental Volume"],
        values=[base_vol, incr_vol],
        marker_colors=[RED, GOLD], hole=0.55,
        textinfo="percent+label", textfont=dict(size=10)))
    pct_incr = incr_vol/(base_vol+incr_vol)*100 if (base_vol+incr_vol)>0 else 0
    fig_bi.update_layout(**LAYOUT, showlegend=False,
        annotations=[dict(text=f"{pct_incr:.0f}%<br>Promo", x=0.5,y=0.5,
                          font=dict(size=11,color=TEXT),showarrow=False)])

    # YoY growth by retailer
    ret_vd = kl.vd_by_retailer.copy()
    if rid != "ALL": ret_vd = ret_vd[ret_vd["retailer_id"]==rid]
    ret_vd = ret_vd.sort_values("yoy_pct")
    fig_ret = px.bar(ret_vd, x="yoy_pct", y="retailer_name", orientation="h",
        color="yoy_pct", color_continuous_scale=[[0,"#c0392b"],[0.5,"#888"],[1,GOLD]],
        text="yoy_pct", labels={"yoy_pct":"YoY Growth %","retailer_name":""},
        color_continuous_midpoint=0)
    fig_ret.update_traces(texttemplate="%{text:+.1f}%", textposition="outside", marker_line_width=0)
    fig_ret.add_vline(x=0, line=dict(color="#fff",width=1))
    fig_ret.update_layout(**LAYOUT, xaxis_ticksuffix="%", coloraxis_showscale=False)

    # Driver pct by BU stacked 100%
    vd_bu = vd.groupby("business_unit", as_index=False).agg(
        dist=("distribution_driver","sum"), vel=("velocity_driver","sum"),
        price=("price_mix_driver","sum"), promo=("promo_driver","sum"))
    # Normalize to % of absolute total
    for col in ["dist","vel","price","promo"]:
        vd_bu[col] = vd_bu[col].abs()
    vd_bu["total"] = vd_bu[["dist","vel","price","promo"]].sum(axis=1).replace(0,1)
    for col in ["dist","vel","price","promo"]:
        vd_bu[f"{col}_pct"] = (vd_bu[col]/vd_bu["total"]*100).round(1)
    vd_bu = vd_bu.sort_values("dist_pct")

    fig_dpct = go.Figure()
    for col, name, color in [
        ("dist_pct","Distribution",DRIVER_COLORS["Distribution"]),
        ("vel_pct","Velocity",DRIVER_COLORS["Velocity"]),
        ("price_pct","Price/Mix",DRIVER_COLORS["Price/Mix"]),
        ("promo_pct","Promotions",DRIVER_COLORS["Promotions"]),
    ]:
        fig_dpct.add_trace(go.Bar(
            y=vd_bu["business_unit"], x=vd_bu[col], name=name,
            orientation="h", marker=dict(color=color,line=dict(width=0)),
            text=vd_bu[col].apply(lambda x: f"{x:.0f}%" if x > 5 else ""),
            textposition="inside", textfont=dict(size=8,color="#fff")))
    fig_dpct.update_layout(**LAYOUT, barmode="stack",
        xaxis_ticksuffix="%", xaxis_range=[0,105])

    return kpis, fig_wf, fig_db, fig_bi, fig_ret, fig_dpct
