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
    "backgroundColor": "#eee",
    "margin": "10px 0",
    "padding": "20px 20px",
    "border": "medium solid lightgray",
    #"borderRadius": "5px"
    "backgroundColor": "rgba(239, 239, 239, 1)",
}
CONTAINER_CHILDREN_STYLE = {
    "height": "100vh",
    "backgroundColor": "rgba(239, 239, 239, 1)",

}
PLOT_CONTAINER = {
    "borderRadius": "10px",
    "background": "white",
    "padding": "5px"

}
NETWORK_CONTAINER_STYLE = {
    "height": "100%",
    "width": "100%",
    "backgroundColor": "rgba(239, 239, 239, 1)",

}
NETWORK_STYLE = {
    "width": "100%",
    "height": "100%",
    "backgroundColor": "rgba(239, 239, 239, 1)",
    #"overflow": "hidden"

}

HEADER_STYLE = {
    "padding": "10px",
    "margin": "10px",
    "backgroundColor": "rgba(239, 239, 239, 1)",
    "position": "absolute",
    "zIndex": "10",

}
template = {"layout": {"paper_bgcolor": bgcolor, "plot_bgcolor": bgcolor}}


def load_data(basedir):
    """This can be replaced by real-time simulation code at some point"""
    with open(f"{basedir}/config.json", "r") as f:
        config = json.load(f)
    with open(f"{basedir}/infrastructure.json", "r") as f:
        infrastructure = json.load(f)
    node_measurements = pd.read_csv(f"{basedir}/node_measurements.csv")
    link_measurements = pd.read_csv(f"{basedir}/link_measurements.csv")
    return config, infrastructure, node_measurements, link_measurements


def infrastructure_to_cyto_dict(infrastructure):
    elements = []
    for node in infrastructure["nodes"]:
        if "x" in node and "y" in node:
            position = {'x': node["x"], 'y': node["y"]}
        else:
            position = {'x': 0, 'y': 0}
        elements.append({
            'data': {'id': node["id"], 'label': node["id"]},
            'position': position,
            'classes': node['id']

        })
    for link in infrastructure["links"]:
        src, dst = link["id"].split("$")
        elements.append({
            'data': {'source': src, 'target': dst}
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


def power_fig(node_measurements, node_ids: List[str]):
    df = node_measurements.pivot(index='time', columns='id', values=["static_power", "dynamic_power"])
    df.columns = df.columns.swaplevel()

    fig = go.Figure()
    for node_id in node_ids:
        node_df = df[node_id]
        fig.add_trace(go.Scatter(x=node_df.index, y=node_df["static_power"], name="Static", stackgroup='one'))
        fig.add_trace(go.Scatter(x=node_df.index, y=node_df["dynamic_power"], name="Dynamic", stackgroup='one'))
    fig.update_layout(
        title=f"Power usage: {', '.join(node_ids)}",
        xaxis_title="Time",
        yaxis_title="Power usage (Watt)",
    )
    return fig

NETWORK_STYLESHEET = [
    {
        'selector': 'node',
        'style': {
            'content': 'data(label)',
            'backgroundColor': "gray",
        }
    }
]


def main():
    config, infrastructure, node_measurements, link_measurements = load_data("../examples/smart_city_traffic/vis_results/fog_2")

    # https://dash.plotly.com/cytoscape/reference
    network = cyto.Cytoscape(
        layout=config["cytoscape_layout"],
        elements=infrastructure_to_cyto_dict(infrastructure["100"]),
        style=NETWORK_STYLE,
        maxZoom=12,
        minZoom=1,
        stylesheet=NETWORK_STYLESHEET,
        # responsive=True,
        # zoom
        # minZoom
        # maxZoom
    )

    timeseries_chart = dcc.Graph(
        figure=blank_fig(500),
        config={"displayModeBar": False},
        style={
            "borderRadius": "20px",

        }
    )

    app = dash.Dash(external_stylesheets=[dbc.themes.BOOTSTRAP])

    NODEPANEL_STYLE = {
        "position": "absolute",
        "right": "-50%",
        "top": "0",
        "height": "100vh",
        "width": "50%",
        "transition": "right 1000ms",
        "backgroundColor": "#A2C2C2",
        "zIndex": "10000",
        "color": "white",
        "padding": "20px",
        "overflow": "hidden"

    }
    node_panel = html.Div(children=["asdf", dbc.Row(timeseries_chart, style=PLOT_CONTAINER)], style=NODEPANEL_STYLE)
    app.layout = html.Div([
        node_panel,
        dbc.Row([
            dbc.Col(html.H5(children=["LEAF GUI v0.1"], style=HEADER_STYLE)),
        ], style={"backgroundColor": "rgba(239, 239, 239, 1)"}),
        dbc.Row([
            dbc.Col(html.Div(network, style=NETWORK_CONTAINER_STYLE)),
        ], style=CONTAINER_CHILDREN_STYLE)
    ], style={"overflow": "hidden"})

    @app.callback(
        Output(timeseries_chart, component_property='figure'),
        Input(network, component_property='selectedNodeData')  # tapNodeData
    )
    def update_plot(input_value):
        if input_value is None:
            return {}
        else:
            return power_fig(node_measurements, [el["id"] for el in input_value])

    selectedNodesBackup: [] = []
    @app.callback(
        Output(node_panel, 'style'),
        Output(node_panel, "children"),
        Output(network, "stylesheet"),
        Input(network, component_property='selectedNodeData'),  # tapNodeData
    )

    def update_nodePanel(selectedNodeData):
        print("")
        print("update nodepanel:")
        print("clicked: ")
        print(selectedNodeData)
        is_node_panel_open = False
        if selectedNodeData is None:
            print("nothing clicked")
            NODEPANEL_STYLE["right"] = "-50%"
            return NODEPANEL_STYLE, "", NETWORK_STYLESHEET
        else:
            right = NODEPANEL_STYLE["right"]
            if right == "-50%":
                is_node_panel_open = False
            elif right == "0":
                is_node_panel_open = True
            print("isNodePanelOpen: ")
            print(is_node_panel_open)
            if is_node_panel_open and not selectedNodeData:
                # close it now
                print("close it now")
                print("selectedNodeData is empty")
                print("stylesheet:")
                print(NETWORK_STYLESHEET)
                NODEPANEL_STYLE["right"] = "-50%"

                #wenn man zu macht verschwindet der graf
                for node in selectedNodesBackup:
                    print("laaa")
                    print(node)
                    for elem in NETWORK_STYLESHEET:
                        print(elem)
                        if elem["selector"] == "." + node["id"]:
                            print("update")
                            print("x")
                            elem["style"]["backgroundColor"] = "gray"
                            print(elem["style"]["backgroundColor"])
                            elem["style"]["content"] = 'data(label)'
                            print(elem["style"]["content"])
                            print(NETWORK_STYLESHEET)
                for node in selectedNodesBackup:
                    selectedNodesBackup.remove(node)
                return NODEPANEL_STYLE, ["", dbc.Col(timeseries_chart, style=PLOT_CONTAINER)], NETWORK_STYLESHEET
            else:
                # open it now
                print("open it now ")
                print("selectedNodeData is not empty")
                for node in selectedNodeData:
                    selectedNodesBackup.append(node)
                    print(node)
                    is_first_call = True
                    for el in NETWORK_STYLESHEET:
                        if el["selector"] == "." + node["id"]:
                            is_first_call = False
                            el["style"]["backgroundColor"] = "lightgray"
                            el["style"]["content"] = 'data(label)'
                    if is_first_call:
                        NETWORK_STYLESHEET.append({
                            "selector": "." + node["id"],
                            "style": {
                                "backgroundColor": "lightgray",
                                'content': 'data(label)'
                            }
                        })

            print(NETWORK_STYLESHEET)
            NODEPANEL_STYLE["right"] = "0"

            return NODEPANEL_STYLE, [selectedNodeData[0]["label"], dbc.Col(timeseries_chart, style=PLOT_CONTAINER)], NETWORK_STYLESHEET


    app.run_server(debug=True)


if __name__ == "__main__":
    main()
