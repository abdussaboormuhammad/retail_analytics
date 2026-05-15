import dash
from dash import dcc, html, Input, Output, callback
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import plotly.express as px
import khc_loader as kl

dash.register_page(__name__, path="/category-review", name="Category Review", order=2)

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


layout = html.Div([
    html.Div([
        html.Div([
            html.H4("Category Business Review", style={"color":RED,"fontWeight":"800","margin":"0"}),
            html.P("Competitive landscape · Distribution · Shelf execution · Growth initiatives", style={"color":MUTED,"margin":"0","fontSize":"0.82rem"}),
        ]),
        html.Div([
            html.Label("Category", style={"color":MUTED,"fontSize":"0.72rem","display":"block"}),
            dcc.Dropdown(id="cr-bu",
                options=[{"label":b,"value":b} for b in kl.BUS_LIST],
                value=kl.BUS_LIST[0], clearable=False,
                style={"minWidth":"220px","fontSize":"0.82rem"}),
        ]),
        html.Div([
            html.Label("Retailer", style={"color":MUTED,"fontSize":"0.72rem","display":"block"}),
            dcc.Dropdown(id="cr-retailer",
                options=[{"label":"All Retailers","value":"ALL"}]+[{"label":r[1],"value":r[0]} for r in kl.RETAILERS_LIST],
                value="ALL", clearable=False,
                style={"minWidth":"200px","fontSize":"0.82rem"}),
        ]),
    ], style={"display":"flex","alignItems":"flex-end","gap":"16px","marginBottom":"20px"}),

    dbc.Row([
        dbc.Col(card("Dollar Share Trend — KHC vs. Competitors","cr-share-trend",310), width=8),
        dbc.Col(card("KHC vs. Competitor Share Mix","cr-share-pie",310), width=4),
    ], className="g-3 mb-3"),

    dbc.Row([
        dbc.Col(card("ACV Distribution by Retailer (Category)","cr-acv-heatmap",280), width=6),
        dbc.Col(card("Shelf Compliance & Share of Shelf by Retailer","cr-shelf",280), width=6),
    ], className="g-3 mb-3"),

    dbc.Row([
        dbc.Col(card("On-Shelf Availability % by Retailer","cr-osa",260), width=5),
        dbc.Col(card("Consumer Loyalty — Brand Health Indicators","cr-health",260), width=7),
    ], className="g-3"),
], style={"padding":"20px"})


@callback(
    Output("cr-share-trend", "figure"),
    Output("cr-share-pie",   "figure"),
    Output("cr-acv-heatmap", "figure"),
    Output("cr-shelf",       "figure"),
    Output("cr-osa",         "figure"),
    Output("cr-health",      "figure"),
    Input("cr-bu",           "value"),
    Input("cr-retailer",     "value"),
)
def update_cr(bu, rid):
    # Market share trend
    sh = kl.share_trend[kl.share_trend["business_unit"] == bu].copy()
    if rid != "ALL":
        sh_raw = kl.mshare[(kl.mshare["business_unit"]==bu) & (kl.mshare["retailer_id"]==rid)]
        sh = sh_raw.groupby(["fiscal_week","week_start_date","brand_name","entity_type"], as_index=False).agg(
            dollar_share=("dollar_share_pct","mean"))

    # Separate KHC from competitors
    khc_sh = sh[sh["entity_type"]=="KHC Brand"].groupby(
        ["fiscal_week","week_start_date"], as_index=False).agg(share=("dollar_share","sum"))
    comp_sh = sh[sh["entity_type"]=="Competitor"].groupby(
        ["fiscal_week","week_start_date","brand_name"], as_index=False).agg(share=("dollar_share","mean"))
    # Top 3 competitors by avg share
    top_comp = comp_sh.groupby("brand_name")["share"].mean().nlargest(3).index.tolist()

    fig_trend = go.Figure()
    fig_trend.add_trace(go.Scatter(x=khc_sh["week_start_date"], y=khc_sh["share"],
        name="KHC (Total)", line=dict(color=RED, width=3),
        fill="tozeroy", fillcolor=f"{RED}15"))
    colors_comp = [GOLD, "#00b4d8", "#2ecc71"]
    for i, comp in enumerate(top_comp):
        c_data = comp_sh[comp_sh["brand_name"]==comp]
        fig_trend.add_trace(go.Scatter(x=c_data["week_start_date"], y=c_data["share"],
            name=comp, line=dict(color=colors_comp[i%3], width=1.5, dash="dot")))
    fig_trend.update_layout(**LAYOUT, yaxis_title="Dollar Share %", yaxis_ticksuffix="%", xaxis_title="")

    # Share pie (latest 4 weeks avg)
    sh_latest = sh[sh["entity_type"]=="KHC Brand"].groupby("brand_name", as_index=False).agg(share=("dollar_share","mean"))
    comp_latest = sh[sh["entity_type"]=="Competitor"].groupby("brand_name", as_index=False).agg(share=("dollar_share","mean"))
    comp_latest = comp_latest.nlargest(4,"share")
    all_pie = pd.concat([
        sh_latest.assign(group="KHC"),
        comp_latest.assign(group="Competitor")
    ])
    pie_colors = [RED if g=="KHC" else GOLD if i<2 else "#00b4d8"
                  for i,g in enumerate(all_pie["group"])]
    fig_pie = go.Figure(go.Pie(
        labels=all_pie["brand_name"], values=all_pie["share"].round(1),
        marker=dict(colors=pie_colors), hole=0.45,
        textinfo="percent+label", textfont=dict(size=9),
        pull=[0.05 if g=="KHC" else 0 for g in all_pie["group"]]))
    fig_pie.update_layout(**LAYOUT, showlegend=False,
        annotations=[dict(text=f"Mkt<br>Share", x=0.5,y=0.5,font=dict(size=10,color=TEXT),showarrow=False)])

    # ACV by retailer heatmap
    d = kl.dist_by_bu_ret[kl.dist_by_bu_ret["business_unit"]==bu].copy() if "business_unit" in kl.dist_by_bu_ret.columns else kl.dist_by_bu_ret.copy()
    if len(d) == 0:
        d = kl.dist[kl.dist["business_unit"]==bu].groupby(["retailer_id"], as_index=False).agg(
            avg_acv=("acv_pct","mean")).merge(kl.dim_retailer[["retailer_id","retailer_name"]], on="retailer_id")
    d = d.sort_values("avg_acv", ascending=False)
    fig_acv = go.Figure(go.Bar(
        x=d["retailer_name"], y=d["avg_acv"],
        marker=dict(
            color=d["avg_acv"],
            colorscale=[[0,"#c0392b"],[0.5,RED],[1,GOLD]],
            line=dict(width=0)),
        text=d["avg_acv"].round(1).astype(str)+"%",
        textposition="outside"))
    fig_acv.add_hline(y=95, line=dict(color="#fff",dash="dot",width=1.2),
        annotation_text="95% ACV Target", annotation_font=dict(color="#fff",size=9))
    fig_acv.update_layout(**LAYOUT, yaxis_range=[0,105], yaxis_ticksuffix="%",
        xaxis_tickangle=-30, xaxis_title="")

    # Shelf compliance by retailer
    sh_data = kl.shelf_enriched[kl.shelf_enriched["business_unit"]==bu].copy() if "business_unit" in kl.shelf_enriched.columns else kl.shelf_enriched.copy()
    if rid != "ALL":
        sh_data = sh_data[sh_data["retailer_id"]==rid]
    sh_ret = sh_data.groupby("retailer_name", as_index=False).agg(
        pog_compliance=("planogram_compliance_pct","mean"),
        sos=("actual_sos_pct","mean"),
        osa=("osa_pct","mean"))
    sh_ret = sh_ret.sort_values("pog_compliance", ascending=True)
    fig_shelf = go.Figure()
    fig_shelf.add_trace(go.Bar(y=sh_ret["retailer_name"], x=sh_ret["pog_compliance"],
        orientation="h", name="POG Compliance %", marker_color=RED, marker_line_width=0,
        text=sh_ret["pog_compliance"].round(1).astype(str)+"%", textposition="outside"))
    fig_shelf.add_trace(go.Bar(y=sh_ret["retailer_name"], x=sh_ret["sos"],
        orientation="h", name="Share of Shelf %", marker_color=GOLD, marker_line_width=0,
        text=sh_ret["sos"].round(1).astype(str)+"%", textposition="outside"))
    fig_shelf.update_layout(**LAYOUT, barmode="group", xaxis_range=[0,110], xaxis_ticksuffix="%")

    # OSA by retailer
    osa_data = sh_data.groupby("retailer_name", as_index=False).agg(osa=("osa_pct","mean"), oos=("oos_incidents","sum"))
    osa_data = osa_data.sort_values("osa")
    fig_osa = px.bar(osa_data, x="osa", y="retailer_name", orientation="h",
        color="osa", color_continuous_scale=[[0,"#c0392b"],[0.7,RED],[1,GOLD]],
        text="osa", labels={"osa":"OSA %","retailer_name":""})
    fig_osa.add_vline(x=95, line=dict(color="#fff",dash="dot",width=1.2),
        annotation_text="95% OSA target", annotation_font=dict(color="#fff",size=9))
    fig_osa.update_traces(texttemplate="%{text:.1f}%", textposition="outside", marker_line_width=0)
    fig_osa.update_layout(**LAYOUT, xaxis_range=[0,105], xaxis_ticksuffix="%", coloraxis_showscale=False)

    # Brand health radar
    bu_brands = kl.dim_brand[kl.dim_brand["business_unit"]==bu]["brand_id"].tolist()
    panel_f = kl.panel[kl.panel["brand_id"].isin(bu_brands)].groupby("brand_name", as_index=False).agg(
        hh_pen=("hh_penetration_pct","mean"),
        freq=("purchase_freq_annual","mean"),
        loyalty=("buyer_loyalty_pct","mean"),
        repeat=("repeat_rate_pct","mean"),
        new_buyer=("new_buyer_pct","mean"))
    panel_f = panel_f.head(5)
    colors_h = [RED, GOLD, "#00b4d8", "#2ecc71", "#9b59b6"]
    fig_health = go.Figure()
    cats_radar = ["HH Penetration","Purchase Freq","Loyalty","Repeat Rate","New Buyer %"]
    for i, (_, row) in enumerate(panel_f.iterrows()):
        vals = [row["hh_pen"], row["freq"]*5, row["loyalty"], row["repeat"], row["new_buyer"]*3]
        vals_norm = [min(v/75*100, 100) for v in vals]
        vals_norm.append(vals_norm[0])
        fig_health.add_trace(go.Scatterpolar(
            r=vals_norm, theta=cats_radar+[cats_radar[0]],
            name=row["brand_name"], fill="toself", opacity=0.5,
            line=dict(color=colors_h[i%5], width=1.5)))
    fig_health.update_layout(**LAYOUT,
        polar=dict(bgcolor="rgba(0,0,0,0)",
                   radialaxis=dict(visible=True,range=[0,100],color="#555",tickfont=dict(size=8)),
                   angularaxis=dict(color=TEXT)))

    return fig_trend, fig_pie, fig_acv, fig_shelf, fig_osa, fig_health


import pandas as pd
