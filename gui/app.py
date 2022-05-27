import json
from typing import List
import random
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

#colors = ['rgb(127, 166, 238)', 'rgb(184, 247, 212)', 'rgb(184, 247, 212)', 'rgb(131, 90, 241)', "#DBF227"]


PLOT_CONTAINER = {
     "borderRadius": "10px",
     "background": "white",
     "padding": "3px"

 }

NODE_INFO = {
    "borderRadius": "10px",
    "background": "white",
    "marginTop": "10px",
    "padding": "10px"

}

NETWORK_STYLE = {
    "width": "100%",
    "height": "100%",
    "backgroundColor": "rgba(239, 239, 239, 1)",
}

NETWORK_STYLESHEET = [
    {
        'selector': 'node',
        'style': {
            'content': 'data(label)',
            'backgroundColor': "black",
            'width': "10px",
            'height': "10px",
        }
    }
]

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


template = {"layout": {"paper_bgcolor": bgcolor, "plot_bgcolor": bgcolor}}

#def randomizeColor():
    #return random.choice(colors)



def load_data(basedir):
    """This can be replaced by real-time simulation code at some point"""
    with open(f"{basedir}/config.json", "r") as f:
        config = json.load(f)
    with open(f"{basedir}/infrastructure.json", "r") as f:
        infrastructure = json.load(f)
    node_measurements = pd.read_csv(f"{basedir}/node_measurements.csv")
    print("node_measurements")
    print(node_measurements)
    link_measurements = pd.read_csv(f"{basedir}/link_measurements.csv")
    return config, infrastructure, node_measurements, link_measurements


def infrastructure_to_cyto_dict(infrastructure):
    elements = []
    for node in infrastructure["nodes"]:
        if "x" in node and "y" in node:
            position = {'x': node["x"] * 1.25, 'y': (node["y"]*2) * 1.3}
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


# def blank_fig(height):
#     """
#     Build blank figure with the requested height
#     """
#     return {
#         "data": [],
#         "layout": {
#             "height": height,
#             "template": template,
#             "xaxis": {"visible": False},
#             "yaxis": {"visible": False},
#         },
#     }


def power_fig(node_measurements, node_ids: List[str]):
    df = node_measurements.pivot(index='time', columns='id', values=["static_power", "dynamic_power"])
    df.columns = df.columns.swaplevel()

    fig = go.Figure()
    for node_id in node_ids:
        node_df = df[node_id]
        fig.add_trace(go.Scatter(x=node_df.index, y=node_df["static_power"], name=node_id + " Static power", stackgroup='one'))
        fig.add_trace(go.Scatter(x=node_df.index, y=node_df["dynamic_power"],  name=node_id + " Dynamic power", stackgroup='one'))
    fig.update_layout(
        title=f"Power usage: {', '.join(node_ids)}",
        xaxis_title="Time",
        yaxis_title="Power usage (Watt)",
        legend=dict(
            x=0,
            y=1,
            traceorder="normal",
        ),
        plot_bgcolor='white',
        #paper_bgcolor="white"

    )
    fig.update_xaxes(showline=True, linewidth=1, linecolor='lightgray', gridcolor='lightgray')
    fig.update_yaxes(showline=True, linewidth=1, linecolor='lightgray', gridcolor='lightgray')


    return fig


def get_selectable_nodes():
    helper_list = []
    for elem in node_measurements["id"]:
        helper_list.append(elem)
    return list(dict.fromkeys(helper_list))


def highlight_selectable_nodes():
    for nodeID in get_selectable_nodes():
        NETWORK_STYLESHEET.append({
            "selector": "." + nodeID,
            "style": {
                "backgroundColor": "#ABE8E8",
                'content': 'data(label)',
                'width': "50px",
                'height': "50px"
            }
        })


config, infrastructure, node_measurements, link_measurements = load_data("../examples/smart_city_traffic/vis_results/fog_2")


def main():
    # https://dash.plotly.com/cytoscape/reference
    print(get_selectable_nodes())

    highlight_selectable_nodes()

    network = cyto.Cytoscape(
        layout=config["cytoscape_layout"],
        elements=infrastructure_to_cyto_dict(infrastructure["100"]),
        style=NETWORK_STYLE,
        maxZoom=10,
        minZoom=0.5,
        stylesheet=NETWORK_STYLESHEET,

    )

    timeseries_chart = dcc.Graph(
        #figure=blank_fig(500),
        config={"displayModeBar": True},
        style={
            "borderRadius": "20px",

        }
    )

    app = dash.Dash(external_stylesheets=[dbc.themes.BOOTSTRAP])

    node_info = html.Div([
        html.H5(children=["Node info"], style={"color": "black"}, id="title")

    ], style=NODE_INFO)

    node_panel = html.Div([

         dbc.Row(
             timeseries_chart, className='plotContainer', style=PLOT_CONTAINER

            ), node_info
         ], style=NODEPANEL_STYLE)

    app.layout = html.Div([
        node_panel,
        dbc.Row([
            dbc.Col(html.H5(children=["LEAF GUI v0.1"], className='header')),
        ], style={"backgroundColor": "rgba(239, 239, 239, 1)"}),
        html.Button('Select all', className="selectButton"),


        dbc.Row([
            dbc.Col(html.Div(network, className='networkContainer')),
        ], className='childrenContainer')
    ], style={"overflow": "hidden"})

    last_plot: [] = [None]
    @app.callback(
        Output(timeseries_chart, component_property='figure'),
        Input(network, component_property='selectedNodeData')  # tapNodeData
    )
    def update_plot(input_value):
        print(input_value)
        if input_value is None:
            print("nothing selected")
            return {}
        else:
            print("graf")
            if not input_value:
                print("dont update")
                return power_fig(node_measurements, last_plot[0])
            else:
                last_plot[0] = [el["id"] for el in input_value]
                return power_fig(node_measurements, last_plot[0])

    def is_node_selectable(selectednodedata):
        if selectednodedata[0]["id"] in get_selectable_nodes():
            return True
        else:
            return False

    def close_node_panel():
        NODEPANEL_STYLE["right"] = "-50%"


    def open_node_panel():
        NODEPANEL_STYLE["right"] = "0"

    def is_node_panel_open():
        right = NODEPANEL_STYLE["right"]
        if right == "-50%":
            return False
        elif right == "0":
            return True

    selected_nodes_backup: [] = []

    def reset_dash_nodes():
        for node in selected_nodes_backup:
            for elem in NETWORK_STYLESHEET:
                if elem["selector"] == "." + node["id"]:
                    elem["style"]["backgroundColor"] = "#ABE8E8"
                    elem["style"]["content"] = 'data(label)'
                    elem["style"]["width"] = '50px'
                    elem["style"]["height"] = '50px'
        for node in selected_nodes_backup:
            selected_nodes_backup.remove(node)

    def set_selected_nodes(selected_node_data):
        for node in selected_node_data:
            selected_nodes_backup.append(node)
            is_first_call = True
            for el in NETWORK_STYLESHEET:
                if el["selector"] == "." + node["id"]:
                    is_first_call = False
                    el["style"]["backgroundColor"] = "#A2C2C2"
                    el["style"]["content"] = 'data(label)'
                    el["style"]["width"] = '50px'
                    el["style"]["height"] = '50px'
            if is_first_call:
                NETWORK_STYLESHEET.append({
                    "selector": "." + node["id"],
                    "style": {
                        "backgroundColor": "#A2C2C2",
                        'content': 'data(label)',
                        'width': "50px",
                        'height': "50px"
                    }
                })

    last_selected_node_content: [] = [None]
    @app.callback(
        Output(node_panel, 'style'),
        Output(node_panel, "children"),
        Output(network, "stylesheet"),
        Input(network, component_property='selectedNodeData'),  # tapNodeData
    )
    def update_nodePanel(selectedNodeData):
        reset_dash_nodes()
        if selectedNodeData is None:
            #selected is None
            close_node_panel()
            return NODEPANEL_STYLE, "", NETWORK_STYLESHEET
        else:
            # if nothing selected or node is selectable
            if not selectedNodeData or is_node_selectable(selectedNodeData):
                # if nodePanel is open and nothing selected
                if is_node_panel_open() and not selectedNodeData:
                    close_node_panel()
                    print(selectedNodeData)

                    #wenn man zu macht verschwindet der graf
                    return NODEPANEL_STYLE, [last_selected_node_content[0], dbc.Col(timeseries_chart, style=PLOT_CONTAINER),  node_info], NETWORK_STYLESHEET

                # nodePanel is closed and needs to be open
                else:
                    last_selected_node_content[0] = ', '.join([el["id"] for el in selectedNodeData])

                    set_selected_nodes(selectedNodeData)
                    open_node_panel()
                    return NODEPANEL_STYLE, [ last_selected_node_content[0], dbc.Col(timeseries_chart, style=PLOT_CONTAINER) , node_info], NETWORK_STYLESHEET
            else:
                # node is not selectable
                print("node is not selectable")
                close_node_panel()
                return NODEPANEL_STYLE, "", NETWORK_STYLESHEET

    app.run_server(debug=True)


if __name__ == "__main__":
    main()
