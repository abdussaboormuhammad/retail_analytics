import dash
import dash_bootstrap_components as dbc
from dash import html, dcc

app = dash.Dash(
    __name__,
    use_pages=True,
    external_stylesheets=[dbc.themes.FLATLY, dbc.icons.BOOTSTRAP],
    suppress_callback_exceptions=True,
    title="Retail Analytics Platform",
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
)
server = app.server

NAV_LINKS = [
    {"href": "/",            "label": "Sales Analytics",  "icon": "bi-bar-chart-fill"},
    {"href": "/supply-chain","label": "Supply Chain",     "icon": "bi-truck"},
    {"href": "/shoppers",    "label": "Shopper Behavior", "icon": "bi-people-fill"},
    {"href": "/category",    "label": "Category Manager", "icon": "bi-grid-fill"},
]

navbar = dbc.Navbar(
    dbc.Container([
        html.A(
            dbc.Row([
                dbc.Col(html.I(className="bi bi-shop-window fs-4 text-white me-2")),
                dbc.Col(dbc.NavbarBrand("Retail Analytics Platform",
                                        className="ms-1 fw-bold fs-5 text-white")),
            ], align="center", className="g-0"),
            href="/", style={"textDecoration": "none"},
        ),
        dbc.NavbarToggler(id="navbar-toggler"),
        dbc.Collapse(
            dbc.Nav([
                dbc.NavItem(
                    dcc.Link(
                        [html.I(className=f"{l['icon']} me-1"), l["label"]],
                        href=l["href"],
                        className="nav-link text-white fw-semibold px-3",
                        style={"fontSize": "0.88rem"},
                    )
                ) for l in NAV_LINKS
            ], className="ms-auto", navbar=True),
            id="navbar-collapse",
            navbar=True,
        ),
    ], fluid=True),
    color="primary",
    dark=True,
    className="shadow-sm",
    style={"padding": "0.5rem 0"},
)

app.layout = html.Div([
    navbar,
    dbc.Container(dash.page_container, fluid=True,
                  style={"padding": "1.5rem 1rem", "backgroundColor": "#F4F6F9",
                         "minHeight": "calc(100vh - 58px)"}),
    html.Footer(
        dbc.Container([
            html.Small("Retail Analytics Platform · Data refreshed weekly · 2024 FY",
                       className="text-muted"),
        ], fluid=True),
        className="border-top py-2 bg-white text-center",
    ),
], style={"backgroundColor": "#F4F6F9"})


@app.callback(
    dash.Output("navbar-collapse", "is_open"),
    [dash.Input("navbar-toggler", "n_clicks")],
    [dash.State("navbar-collapse", "is_open")],
)
def toggle_navbar(n, is_open):
    if n:
        return not is_open
    return is_open


if __name__ == "__main__":
    app.run(debug=True, port=8050)
