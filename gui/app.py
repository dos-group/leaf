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
    "padding": "3px",

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
            'height': "10px"

        }
    }
]

NODEPANEL_STYLE = {
    "position": "absolute",
    "right": "-50%",
    "top": "0",
    "height": "100vh",
    "width": "50%",
    "transition": "all 1000ms",
    "backgroundColor": "#A2C2C2",
    "zIndex": "10000",
    "color": "white",
    "padding": "20px",
    "overflow": "hidden"

}

SELECT_STYLE = {
    "padding": "15px",
    "width": "150px",
    "margin": "10px",
    "backgroundColor": "white",
    "position": "absolute",
    "zIndex": "10",
    "top": "10px",
    "left": "10px",
    "borderRadius": "50px",
    "fontSize": "larger",
    "border": "3px #A2C2C2 solid",
    "color": "#A2C2C2",
}


DESELECT_STYLE = {
    "display":"none",
    "padding": "15px",
    "width": "150px",
    "margin": "10px",
    "backgroundColor": "white",
    "position": "absolute",
    "zIndex": "10",
    "top": "10px",
    "left": "10px",
    "borderRadius": "50px",
    "fontSize": "larger",
    "border": "3px #A2C2C2 solid",
    "color": "#A2C2C2",

}

OVERLAY_STYLE = {
    "position": "fixed",
    "width": "100vw",
    "height": "100vh",
    "display": "none",
    "top": "0",
    "left": "0",
    "right": "0",
    "bottom": "0",
    "backgroundColor": "rgba(0,0,0,0.5)",
    "zIndex": "1"
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

def select_all(list):
    for elem in list:
        NETWORK_STYLESHEET.append({
            "selector": "." + elem,
            "style": {
                "backgroundColor": "#ABE8E8",
                'content': 'data(label)',
                'width': "60px",
                'height': "60px",
            }
        })

def highlight_selectable_nodes():
    for nodeID in get_selectable_nodes():
        NETWORK_STYLESHEET.append({
            "selector": "." + nodeID,
            "style": {
                "backgroundColor": "#ABE8E8",
                'content': 'data(label)',
                'width': "60px",
                'height': "60px",
            }
        })


config, infrastructure, node_measurements, link_measurements = load_data("../examples/smart_city_traffic/vis_results/fog_2")
timeseries_chart = dcc.Graph(
    config={"displayModeBar": True},
    style={
        "borderRadius": "20px",

    },
)

def main():
    # https://dash.plotly.com/cytoscape/reference
    print("test")
    print(get_selectable_nodes())
    print(infrastructure_to_cyto_dict(infrastructure["100"]))
    highlight_selectable_nodes()

    network = cyto.Cytoscape(
        #layout=config["cytoscape_layout"],
        layout={
            'name': 'breadthfirst'
        },
        elements=infrastructure_to_cyto_dict(infrastructure["100"]),
        style=NETWORK_STYLE,
        maxZoom=10,
        minZoom=0.2,
        stylesheet=NETWORK_STYLESHEET,
        id="network"

    )

    app = dash.Dash(external_stylesheets=[dbc.themes.BOOTSTRAP])

    node_info = html.Div([
        html.H5(children=["Node info"], style={"color": "black"}, id="title")

    ], style=NODE_INFO)

    node_panel = html.Div(children=[

         dbc.Row(
             timeseries_chart, className='plotContainer', style=PLOT_CONTAINER, id="test"

         ),
         node_info
    ], style=NODEPANEL_STYLE, id="nodepanelID")

    overlay = html.Div(id="overlay", style=OVERLAY_STYLE)
    app.layout = html.Div([
        overlay,
        node_panel,
        html.Button(children=['Select all'], id="select", className="selectButton", n_clicks=0, style=SELECT_STYLE),
        html.Button(children=['Deselect all'], id="deselect", className="deselectButton",n_clicks=0, style=DESELECT_STYLE),


        dbc.Row([
            dbc.Col(html.Div(network, className='networkContainer')),
        ], className='childrenContainer', id="networkID")
    ],  style={"overflow": "hidden"}, id="applayoutID")

    last_plot: [] = [None]

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
        for nodeID in selected_nodes_backup:
            for elem in NETWORK_STYLESHEET:
                if elem["selector"] == "." + nodeID:
                    elem["style"]["backgroundColor"] = "#ABE8E8"
                    elem["style"]["content"] = 'data(label)'
                    elem["style"]["width"] = '60px'
                    elem["style"]["height"] = '60px'
        for nodeID in selected_nodes_backup:
            selected_nodes_backup.remove(nodeID)

    def set_selected_nodes(selected_node_data):
        for nodeID in selected_node_data:
            selected_nodes_backup.append(nodeID)
            is_first_call = True
            for el in NETWORK_STYLESHEET:
                if el["selector"] == "." + nodeID:
                    is_first_call = False
                    el["style"]["backgroundColor"] = "#A2C2C2"
                    el["style"]["content"] = 'data(label)'
                    el["style"]["width"] = '60px'
                    el["style"]["height"] = '60px'

        if is_first_call:
            NETWORK_STYLESHEET.append({
                "selector": "." + nodeID,
                "style": {
                    "backgroundColor": "#A2C2C2",
                    'content': 'data(label)',
                    'width': "60px",
                    'height': "60px",
                }
            })

    def show_element(style, show):
        show_str = "none"
        if show:
            show_str = "block"
        style["display"] = show_str

    def button_clicked(click_backup, is_select):
        click_backup[0] += 1
        reset_dash_nodes()
        NODEPANEL_STYLE["width"] = "75%"
        if is_select:
            open_node_panel()
            show_element(OVERLAY_STYLE, True)
            set_selected_nodes(get_selectable_nodes())
        else:
            NODEPANEL_STYLE["right"] = "-75%"
            show_element(OVERLAY_STYLE, False)
        last_selected_node_content[0] = ', '.join([el for el in get_selectable_nodes()])
        node_panel_children = [last_selected_node_content[0], dbc.Row(timeseries_chart, style=PLOT_CONTAINER), node_info]
        timeseries_chart_nodes = get_selectable_nodes()
        show_element(SELECT_STYLE, not is_select)
        show_element(DESELECT_STYLE, is_select)
        last_plot[0] = timeseries_chart_nodes
        return node_panel_children, timeseries_chart_nodes
    last_selected_node_content: [] = [None]
    n_clicks_select_backup = [1]
    n_clicks_deselect_backup = [1]

    callback_list: [] = [False, False]

    @app.callback(
        Output(network, "tapNodeData"),
        Input("deselect", "n_clicks")
    )
    def trigger_update_click_again(n_clicks):
        if n_clicks == 0:
            return None
        return {"triggerHelper": True}

    @app.callback(
        Output(node_panel, 'style'),
        Output(node_panel, "children"),
        Output(timeseries_chart, component_property='figure'),
        Output(network, "stylesheet"),
        Output("select", "style"),
        Output("deselect", "style"),
        Output("overlay", "style"),
        Input(network, component_property='selectedNodeData'),
        Input("select", "n_clicks"),
        Input("deselect", "n_clicks"),
        Input(network, "tapNodeData"),
    )
    def update_click(selectedNodeData, n_clicks_select, n_clicks_deselect, tapNodeData):
        NODEPANEL_STYLE["width"] = "50%"
        node_panel_children = ["", dbc.Col(timeseries_chart, style=PLOT_CONTAINER), node_info]
        timeseries_chart_nodes = []
        timeseries_chart_figure = None
        select_button_clicked = False
        deselect_button_clicked = False
        reset_dash_nodes()
        add = True if not selectedNodeData or selectedNodeData is None else False
        # auf select button geklickt
        if n_clicks_select == n_clicks_select_backup[0]:
            select_button_clicked = True

            node_panel_children, timeseries_chart_nodes = button_clicked(n_clicks_select_backup, True)
            timeseries_chart_figure = power_fig(node_measurements, timeseries_chart_nodes)

        # auf deselect button geklickt
        if n_clicks_deselect == n_clicks_deselect_backup[0]:
            deselect_button_clicked = True
            node_panel_children, timeseries_chart_nodes = button_clicked(n_clicks_deselect_backup, False)
            timeseries_chart_figure = power_fig(node_measurements, timeseries_chart_nodes)

        if select_button_clicked or deselect_button_clicked:
            return [NODEPANEL_STYLE, node_panel_children, timeseries_chart_figure, NETWORK_STYLESHEET, SELECT_STYLE,
                    DESELECT_STYLE, OVERLAY_STYLE]
        if selectedNodeData is None:
            if not select_button_clicked:
                close_node_panel()
        else:
            show_element(SELECT_STYLE, True)
            show_element(DESELECT_STYLE, False)
            # liste ist leer
            if not selectedNodeData:
                close_node_panel()
                timeseries_chart_nodes = last_plot[0]
                node_panel_children = [last_selected_node_content[0], dbc.Row(timeseries_chart, style=PLOT_CONTAINER), node_info]

            # selected liste ist nicht leer und node is selectable
            if selectedNodeData and is_node_selectable(selectedNodeData):
                last_selected_node_content[0] = ', '.join([el["id"] for el in selectedNodeData])
                set_selected_nodes([el["id"] for el in selectedNodeData])
                node_panel_children = [last_selected_node_content[0], dbc.Row(timeseries_chart, style=PLOT_CONTAINER), node_info]
                timeseries_chart_nodes = [el["id"] for el in selectedNodeData]
                last_plot[0] = timeseries_chart_nodes
                open_node_panel()
            # geklickter node ist nicht selektierbar
            if selectedNodeData and not is_node_selectable(selectedNodeData):
                last_selected_nodes_id_list = last_plot[0]
                if last_selected_nodes_id_list is not None and is_node_panel_open():
                    set_selected_nodes(last_selected_nodes_id_list)
                    node_panel_children = [last_selected_node_content[0], dbc.Row(timeseries_chart, style=PLOT_CONTAINER), node_info]
                    timeseries_chart_nodes = last_plot[0]
                    open_node_panel()
        timeseries_chart_figure = power_fig(node_measurements, timeseries_chart_nodes)
        return [NODEPANEL_STYLE, node_panel_children, timeseries_chart_figure, NETWORK_STYLESHEET, SELECT_STYLE,
                DESELECT_STYLE, OVERLAY_STYLE]

    app.run_server(debug=True)


if __name__ == "__main__":
    main()