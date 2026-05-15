import dash
from dash import dcc, html, Input, Output, callback
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import plotly.express as px
import khc_loader as kl

dash.register_page(__name__, path="/customer-intelligence", name="Customer Intelligence", order=1)

RED  = "#CC0000"
GOLD = "#F5A623"
CARD = "#232323"
TEXT = "#E8E8E8"
MUTED= "#9A9A9A"
LAYOUT = dict(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
              font=dict(color=TEXT, size=11), margin=dict(l=40,r=20,t=20,b=40),
              legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=10)))

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
            html.H4("Customer Intelligence", style={"color":RED,"fontWeight":"800","margin":"0"}),
            html.P("Retailer-specific selling story · KHC vs. Market", style={"color":MUTED,"margin":"0","fontSize":"0.82rem"}),
        ]),
        html.Div([
            html.Label("Select Customer", style={"color":MUTED,"fontSize":"0.72rem","display":"block"}),
            dcc.Dropdown(id="ci-retailer",
                options=[{"label":r[1],"value":r[0]} for r in kl.RETAILERS_LIST],
                value=kl.RETAILERS_LIST[0][0], clearable=False,
                style={"minWidth":"200px","fontSize":"0.82rem"}),
        ]),
        html.Div([
            html.Label("Business Unit", style={"color":MUTED,"fontSize":"0.72rem","display":"block"}),
            dcc.Dropdown(id="ci-bu",
                options=[{"label":"All","value":"ALL"}]+[{"label":b,"value":b} for b in kl.BUS_LIST],
                value="ALL", clearable=False,
                style={"minWidth":"200px","fontSize":"0.82rem"}),
        ]),
    ], style={"display":"flex","alignItems":"flex-end","gap":"16px","marginBottom":"20px"}),

    # Retailer header banner
    html.Div(id="ci-banner", style={"marginBottom":"16px"}),

    dbc.Row(id="ci-kpis", className="g-2 mb-3"),

    dbc.Row([
        dbc.Col(card("KHC Net Sales at Customer — Brand Breakdown","ci-brand-sales",300), width=6),
        dbc.Col(card("ACV % vs. Target (95%) by Brand","ci-acv-bar",300), width=6),
    ], className="g-3 mb-3"),

    dbc.Row([
        dbc.Col(card("Category Market Share at Customer vs. Total Market","ci-share-compare",290), width=7),
        dbc.Col(card("Promo Compliance % by Event Type","ci-compliance",290), width=5),
    ], className="g-3 mb-3"),

    dbc.Row([
        dbc.Col(card("Velocity ($/TDP) by Brand at This Customer","ci-velocity",270), width=6),
        dbc.Col(card("Consumer Penetration & Purchase Frequency","ci-consumer",270), width=6),
    ], className="g-3"),
], style={"padding":"20px"})


@callback(
    Output("ci-banner",       "children"),
    Output("ci-kpis",         "children"),
    Output("ci-brand-sales",  "figure"),
    Output("ci-acv-bar",      "figure"),
    Output("ci-share-compare","figure"),
    Output("ci-compliance",   "figure"),
    Output("ci-velocity",     "figure"),
    Output("ci-consumer",     "figure"),
    Input("ci-retailer",      "value"),
    Input("ci-bu",            "value"),
)
def update_ci(rid, bu):
    ret_name = kl.dim_retailer.loc[kl.dim_retailer["retailer_id"]==rid,"retailer_name"].iloc[0]
    ret_tier = kl.dim_retailer.loc[kl.dim_retailer["retailer_id"]==rid,"khc_account_tier"].iloc[0]
    ret_wt   = kl.dim_retailer.loc[kl.dim_retailer["retailer_id"]==rid,"market_weight_pct"].iloc[0]

    # Banner
    banner = html.Div([
        html.Span(f"📊 {ret_name}", style={"color":RED,"fontWeight":"700","fontSize":"1.1rem"}),
        html.Span(f" · {ret_tier} Account · {ret_wt:.1f}% of KHC Revenue",
                  style={"color":MUTED,"fontSize":"0.82rem","marginLeft":"12px"}),
    ], style={"background":f"{RED}15","borderLeft":f"4px solid {RED}","padding":"10px 16px","borderRadius":"4px"})

    # Filter data
    s = kl.sales[kl.sales["retailer_id"]==rid].copy()
    d = kl.dist_by_ret_brand[kl.dist_by_ret_brand["retailer_id"]==rid].copy()
    pc = kl.promo[kl.promo["retailer_id"]==rid].copy()
    sh_ret = kl.mshare[(kl.mshare["retailer_id"]==rid)].copy()
    sh_all = kl.mshare.copy()

    if bu != "ALL":
        s  = s[s["business_unit"]==bu]
        d  = d[d["brand_id"].isin(kl.dim_brand[kl.dim_brand["business_unit"]==bu]["brand_id"])]
        pc = pc[pc["business_unit"]==bu]
        sh_ret = sh_ret[sh_ret["business_unit"]==bu]
        sh_all = sh_all[sh_all["business_unit"]==bu]

    tot_sales = s["net_sales"].sum()
    tot_prior = s["prior_yr_net_sales"].sum()
    yoy = (tot_sales-tot_prior)/tot_prior*100 if tot_prior else 0
    avg_acv = d["acv_pct"].mean() if len(d) else 0
    avg_comp = pc["compliance_pct"].mean() if len(pc) else 0
    avg_lift = pc["volume_lift_factor"].mean() if len(pc) else 0

    kpis = [
        dbc.Col(kpi("KHC Net Sales", f"${tot_sales/1e3:.1f}K",
                    f"{'+'if yoy>=0 else ''}{yoy:.1f}% vs. PY", GOLD), width=True),
        dbc.Col(kpi("Avg ACV %", f"{avg_acv:.1f}%",
                    f"{'↑' if avg_acv>=80 else '↓'} vs. 95% target", RED if avg_acv<80 else GOLD), width=True),
        dbc.Col(kpi("Promo Compliance", f"{avg_comp:.1f}%",
                    "Avg across events", RED if avg_comp<65 else GOLD), width=True),
        dbc.Col(kpi("Avg Volume Lift", f"{avg_lift:.2f}x",
                    "During promo events", GOLD), width=True),
    ]

    # Brand sales waterfall-style bar
    brand_s = s.groupby("brand_name", as_index=False).agg(
        net_sales=("net_sales","sum"), prior=("prior_yr_net_sales","sum"))
    brand_s["yoy"] = (brand_s["net_sales"]-brand_s["prior"])/brand_s["prior"]*100
    brand_s = brand_s.sort_values("net_sales", ascending=True)
    fig_brands = px.bar(brand_s, x="net_sales", y="brand_name", orientation="h",
        color="yoy", color_continuous_scale=[[0,"#c0392b"],[0.5,RED],[1,GOLD]],
        text="net_sales", labels={"net_sales":"Net Sales ($)","brand_name":"","yoy":"YoY %"},
        color_continuous_midpoint=0)
    fig_brands.update_traces(texttemplate="$%{text:,.0f}", textposition="outside", marker_line_width=0)
    fig_brands.update_layout(**LAYOUT, xaxis_tickformat="$,.0f",
        coloraxis_colorbar=dict(title="YoY %",ticksuffix="%",len=0.6))

    # ACV bar with target line
    d_m = d.merge(kl.dim_brand[["brand_id","brand_name"]], on="brand_id", how="left").dropna(subset=["brand_name"])
    d_m = d_m.sort_values("acv_pct", ascending=True)
    fig_acv = go.Figure()
    fig_acv.add_trace(go.Bar(x=d_m["acv_pct"], y=d_m["brand_name"],
        orientation="h", marker_color=[RED if v < 80 else GOLD for v in d_m["acv_pct"]],
        text=d_m["acv_pct"].round(1).astype(str)+"%",
        textposition="outside", marker_line_width=0, name="ACV %"))
    fig_acv.add_vline(x=95, line=dict(color="#fff",dash="dot",width=1.5),
        annotation_text="95% target", annotation_font=dict(color="#fff",size=9))
    fig_acv.update_layout(**LAYOUT, xaxis_range=[0,105], xaxis_ticksuffix="%", showlegend=False)

    # Share comparison: retailer vs total market
    sh_ret_khc = sh_ret[sh_ret["entity_type"]=="KHC Brand"].groupby("business_unit", as_index=False).agg(share_ret=("dollar_share_pct","mean"))
    sh_all_khc = sh_all[sh_all["entity_type"]=="KHC Brand"].groupby("business_unit", as_index=False).agg(share_all=("dollar_share_pct","mean"))
    share_cmp = sh_ret_khc.merge(sh_all_khc, on="business_unit", how="outer").fillna(0)
    share_cmp = share_cmp.sort_values("share_ret", ascending=True)
    fig_share = go.Figure()
    fig_share.add_trace(go.Bar(y=share_cmp["business_unit"], x=share_cmp["share_ret"],
        orientation="h", name=ret_name, marker_color=RED, marker_line_width=0))
    fig_share.add_trace(go.Bar(y=share_cmp["business_unit"], x=share_cmp["share_all"],
        orientation="h", name="Total Market", marker_color=GOLD, marker_line_width=0,
        marker_pattern_shape="/"))
    fig_share.update_layout(**LAYOUT, barmode="group", xaxis_ticksuffix="%",
        xaxis_title="Dollar Share %")

    # Compliance by promo type
    pc_type = pc.groupby("promo_type", as_index=False).agg(
        compliance=("compliance_pct","mean"), lift=("volume_lift_factor","mean"), events=("promo_id","count"))
    pc_type = pc_type.sort_values("compliance", ascending=True)
    fig_comp = px.bar(pc_type, x="compliance", y="promo_type", orientation="h",
        color="lift", color_continuous_scale=[[0,"#c0392b"],[0.5,RED],[1,GOLD]],
        text="compliance", labels={"compliance":"Compliance %","promo_type":"","lift":"Lift Factor"})
    fig_comp.update_traces(texttemplate="%{text:.1f}%", textposition="outside", marker_line_width=0)
    fig_comp.add_vline(x=65, line=dict(color="#fff",dash="dot",width=1),
        annotation_text="Avg", annotation_font=dict(color="#fff",size=9))
    fig_comp.update_layout(**LAYOUT, xaxis_range=[0,105], xaxis_ticksuffix="%",
        coloraxis_colorbar=dict(title="Lift",len=0.6))

    # Velocity by brand
    d_vel = d.merge(kl.dim_brand[["brand_id","brand_name"]], on="brand_id", how="left").dropna(subset=["brand_name"])
    d_vel = d_vel.sort_values("velocity", ascending=True)
    fig_vel = px.bar(d_vel, x="velocity", y="brand_name", orientation="h",
        color="acv_pct", color_continuous_scale=[[0,"#c0392b"],[0.5,RED],[1,GOLD]],
        text="velocity", labels={"velocity":"$/TDP","brand_name":"","acv_pct":"ACV %"})
    fig_vel.update_traces(texttemplate="$%{text:.2f}", textposition="outside", marker_line_width=0)
    fig_vel.update_layout(**LAYOUT, coloraxis_colorbar=dict(title="ACV %",ticksuffix="%",len=0.6))

    # Consumer panel
    panel_f = kl.panel.copy()
    if bu != "ALL":
        bu_brands = kl.dim_brand[kl.dim_brand["business_unit"]==bu]["brand_id"].tolist()
        panel_f = panel_f[panel_f["brand_id"].isin(bu_brands)]
    panel_brand = panel_f.groupby("brand_name", as_index=False).agg(
        hh_pen=("hh_penetration_pct","mean"), freq=("purchase_freq_annual","mean"),
        loyalty=("buyer_loyalty_pct","mean"))
    fig_cons = px.scatter(panel_brand, x="freq", y="hh_pen", size="loyalty",
        text="brand_name", color="loyalty",
        color_continuous_scale=[[0,"#c0392b"],[0.5,RED],[1,GOLD]], size_max=35,
        labels={"freq":"Purchase Frequency (trips/yr)","hh_pen":"HH Penetration %","loyalty":"Loyalty %"})
    fig_cons.update_traces(textposition="top center", textfont=dict(size=8, color=TEXT))
    fig_cons.update_layout(**LAYOUT, coloraxis_colorbar=dict(title="Loyalty %",ticksuffix="%",len=0.6))

    return banner, kpis, fig_brands, fig_acv, fig_share, fig_comp, fig_vel, fig_cons
