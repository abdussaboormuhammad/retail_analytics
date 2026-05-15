import dash
from dash import html, dcc
import dash_bootstrap_components as dbc

RED    = "#CC0000"
GOLD   = "#F5A623"
DARK   = "#0F0F0F"
NAV_BG = "#1A1A1A"

app = dash.Dash(
    __name__,
    use_pages=True,
    pages_folder="khc_pages",
    external_stylesheets=[dbc.themes.DARKLY],
    suppress_callback_exceptions=True,
    title="Kraft Heinz · Retail Analytics",
    meta_tags=[{"name":"viewport","content":"width=device-width, initial-scale=1"}],
)
server = app.server

nav_links = [
    dbc.NavItem(dbc.NavLink(
        page["name"], href=page["path"], active="exact",
        style={"color":"#ccc","fontSize":"0.84rem","padding":"8px 14px","fontWeight":"500"}
    ))
    for page in sorted(dash.page_registry.values(), key=lambda p: p.get("order", 99))
]

navbar = dbc.Navbar(
    dbc.Container([
        html.Div([
            html.Div([
                html.Span("K", style={"color":RED,"fontWeight":"900","fontSize":"1.1rem"}),
                html.Span("H", style={"color":GOLD,"fontWeight":"900","fontSize":"1.1rem"}),
                html.Span("C", style={"color":"#fff","fontWeight":"900","fontSize":"1.1rem"}),
            ], style={"background":"#111","border":f"2px solid {RED}","borderRadius":"4px",
                      "padding":"2px 7px","marginRight":"12px"}),
            html.Div([
                html.Span("Kraft Heinz", style={"color":"#fff","fontWeight":"700","fontSize":"0.95rem"}),
                html.Span(" Retail Analytics", style={"color":GOLD,"fontWeight":"400","fontSize":"0.95rem"}),
            ]),
        ], className="d-flex align-items-center me-4"),

        dbc.Nav(nav_links, navbar=True, className="me-auto"),

        html.Div([
            html.Span("FY 2024", style={"color":GOLD,"fontSize":"0.75rem","fontWeight":"700"}),
            html.Span(" · 18 KHC Brands · 10 Retailers · 62 SKUs",
                      style={"color":"#666","fontSize":"0.72rem","marginLeft":"6px"}),
        ]),
    ], fluid=True),
    color=NAV_BG,
    dark=True,
    style={"borderBottom":f"2px solid {RED}","boxShadow":"0 2px 8px rgba(0,0,0,0.5)"},
)

app.layout = html.Div(
    [navbar, dash.page_container],
    style={
        "background": DARK,
        "minHeight": "100vh",
        "fontFamily": "'Segoe UI', 'Helvetica Neue', Arial, sans-serif",
    }
)

if __name__ == "__main__":
    app.run(debug=False, host="127.0.0.1", port=8050)
