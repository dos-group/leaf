import json
from typing import List

import dash
import dash_bootstrap_components as dbc
import dash_cytoscape as cyto
import pandas as pd
from dash import Input, Output, dcc, html
import plotly.graph_objs as go
from plotly.subplots import make_subplots

# Colors
bgcolor = "#f3f3f1"  # mapbox light map land color
bar_bgcolor = "#b0bec5"  # material blue-gray 200
bar_unselected_color = "#78909c"  # material blue-gray 400
bar_color = "#546e7a"  # material blue-gray 600
bar_selected_color = "#37474f"  # material blue-gray 800
bar_unselected_opacity = 0.8

CONTAINER_STYLE = {
    "background-color": "#eee",
    "margin": "10px 0",
    "padding": "20px 20px",
    #"borderRadius": "5px"
    "width": "1200px",
}

NETWORK_CONTAINER_STYLE = {
    "height": "100%",
    "border": "2px solid #ccc",
#    "padding-left": 0,
#    "padding-right": 0,
}
NETWORK_STYLE = {
    "width": "100%",
    "height": "100%",
}

template = {"layout": {"paper_bgcolor": bgcolor, "plot_bgcolor": bgcolor}}


def load_data(basedir):
    """This can be replaced by real-time simulation code at some point"""
    with open(f"{basedir}/infrastructure.json", "r") as f:
        infrastructure = json.load(f)
    node_measurements = pd.read_csv(f"{basedir}/node_measurements.csv", index_col="time")
    link_measurements = pd.read_csv(f"{basedir}/link_measurements.csv", index_col="time")
    return infrastructure, node_measurements, link_measurements


def infrastructure_to_cyto_dict(infrastructure):
    elements = []
    for node in infrastructure["nodes"]:
        elements.append({
            'data': {'id': node["id"], 'label': node["id"]},
            # 'position': {'x': 75, 'y': 75},
        })
    for link in infrastructure["links"]:
        elements.append({
            'data': {'source': link["src"], 'target': link["dst"]}
        })
    return elements


def blank_fig(height):
    """
    Build blank figure with the requested height
    """
    return {
        "data": [],
        "layout": {
            "height": height,
            "template": template,
            "xaxis": {"visible": False},
            "yaxis": {"visible": False},
        },
    }


def figure_cpu(node_measurements, node_ids: List[str]):
    df = node_measurements[["id", "used_cu"]]
    df = df.reset_index()
    df = df.pivot(index='time', columns='id', values='used_cu')

    fig = go.Figure()
    for node_id in node_ids:
        cu_series = df[node_id]
        fig.add_trace(go.Scatter(x=cu_series.index, y=cu_series, name="CPU"))
    fig.update_layout(
        title="CPU usage",
        xaxis_title="Time",
        yaxis_title="CPU usage",
    )
    # fig.update_yaxes(range=[0, 3])
    return fig


def figure_power(node_measurements, node_ids: List[str]):
    df = node_measurements[["id", "static_power", "dynamic_power"]]
    df = df.reset_index()
    df = df.pivot(index='time', columns='id', values=["static_power", "dynamic_power"])
    df.columns = df.columns.swaplevel()

    fig = go.Figure()
    for node_id in node_ids:
        node_df = df[node_id]
        fig.add_trace(go.Scatter(x=node_df.index, y=node_df["static_power"], name="Static", stackgroup='one'))
        fig.add_trace(go.Scatter(x=node_df.index, y=node_df["dynamic_power"], name="Dynamic", stackgroup='one'))
    fig.update_layout(
        title="Power usage",
        xaxis_title="Time",
        yaxis_title="Power usage (Watt)",
    )
    return fig


def main():
    infrastructure, node_measurements, link_measurements = load_data("gui/data_generator/example1_data")

    # https://dash.plotly.com/cytoscape/reference
    network = cyto.Cytoscape(
        id='cytoscape-two-nodes',
        layout={'name': 'cose'},  # if coordinates are used, use 'preset'
        elements=infrastructure_to_cyto_dict(infrastructure),
        style=NETWORK_STYLE
        # responsive=True,
        # zoom
        # minZoom
        # maxZoom
    )

    timeseries_chart = dcc.Graph(
        figure=blank_fig(500),
        config={"displayModeBar": False},
    )

    app = dash.Dash(external_stylesheets=[dbc.themes.BOOTSTRAP])
    app.layout = dbc.Container(html.Div([
        dbc.Row([
            dbc.Col(html.H2("LEAF GUI v0.1")),
        ]),
        dbc.Row([
            dbc.Col(timeseries_chart),
            dbc.Col(html.Div(network, style=NETWORK_CONTAINER_STYLE)),
        ])
    ], style=CONTAINER_STYLE))

    @app.callback(
        Output(timeseries_chart, component_property='figure'),
        Input(network, component_property='selectedNodeData')  # tapNodeData
    )
    def update_plot(input_value):
        if input_value is None:
            return {}
        else:
            return figure_cpu(node_measurements, [el["id"] for el in input_value])

    app.run_server(debug=True)


if __name__ == "__main__":
    main()
