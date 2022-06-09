import json
from typing import List
import random
import dash
import dash_bootstrap_components as dbc
import dash_cytoscape as cyto
import pandas as pd
from dash import Input, Output, State, dcc, html
import plotly.graph_objs as go
import plotly.express as px


import plotly.io as pio
from plotly.subplots import make_subplots
import numpy as np

# Colors
bgcolor = "#f3f3f1"  # mapbox light map land color
bar_bgcolor = "#b0bec5"  # material blue-gray 200
bar_unselected_color = "#78909c"  # material blue-gray 400
bar_color = "#546e7a"  # material blue-gray 600
bar_selected_color = "#37474f"  # material blue-gray 800
bar_unselected_opacity = 0.8

#colors = ['rgb(127, 166, 238)', 'rgb(184, 247, 212)', 'rgb(184, 247, 212)', 'rgb(131, 90, 241)', "#DBF227"]

PLOT_CONTAINER = {
}

NODE_INFO = {
    "fontFamiliy":"Avenir",
    "borderRadius": "15px",
    "background": "white",
    "filter": "drop-shadow(5px 5px 5px #879696)",
    "padding": "8px",
    "margin":"5px"

}

NETWORK_STYLE = {
    "width": "100%",
    "height": "100%",
    "backgroundColor": "linear-gradient(rgba(255, 255, 255, 1), rgba(118, 118, 118, 1))",
}

NETWORK_STYLESHEET = [
    {
        'selector': 'node',
        'style': {
            'content': 'data(label)',
            'backgroundColor': "black",
            'width': "10px",
            'height': "10px",
            #"background-image": ["./assets/64324.png"]

        }
    },
    {
        'selector': 'link',
        'style': {
            #'content': 'data(id)',
            'width': "8px",
            'height': "8px",
            #"background-image": ["./assets/64324.png"]

        }
    },
    {
        'selector': '.taxi',
        'style': {
            "background-image": ["./assets/2.png"],
            'background-fit': 'cover',
            "width": "50px",
            "height": "50px"
        }
    },
    {
        'selector': '.traffic',
        'style': {
            "background-image": ["./assets/1.png"],
            'background-fit': 'cover',
            "width": "50px",
            "height": "50px"
        }
    },


]

NODEPANEL_STYLE = {
    "position": "absolute",
    "right": "-50%",
    "top": "-26px",
    "height": "100vh",
    "width": "50%",
    "transition": "all 1000ms",
    "backgroundColor": "#A2C2C2",
    "zIndex": "10000",
    "color": "white",
    "padding": "25px",
    "overflow": "hidden",
    "overflowY": "auto"

}
SELECT_STYLE = {
    "padding": "3px",
    "width": "100px",
    "margin": "5px",
    "backgroundColor": "white",
    "borderRadius": "50px",
    "border": "3px white solid",
    "color": "#A2C2C2",
    "marginLeft": "5px",
    "marginRight": "15px"
}

DESELECT_STYLE = {
    "display": "none",
    "padding": "3px",
    "width": "100px",
    "margin": "5px",
    "backgroundColor": "white",
    "marginLeft": "5px",
    "marginRight": "15px",
    "position": "relative",
    "zIndex": "2",
    "borderRadius": "50px",
    "border": "3px white solid",
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

NODE_NAMES_STYLE = {
    "fontFamiliy" : "Avenir",
    "filter": "drop-shadow(5px 5px 5px #808080)",
    "margin": "5px",
    "color": "white",
    "fontSize": "larger",
    "padding": "8px",
    "borderBottom": "1.5px white solid",
    "marginBottom": "15px",
    "justifyContent": "center"
}

CHART_STYLE = {
    "borderRadius": "10px",
    "background": "white",
    "padding": "6px",
    "margin":"5px",
    "fontFamiliy":"Avenir",
    "filter": "drop-shadow(5px 5px 5px #879696)",
}

SUM_CHART_STYLE = {
    "display": "none",
    "borderRadius": "10px",
    "background": "white",
    "padding": "6px",
    "margin":"5px",
    "fontFamiliy":"Avenir",
    "filter": "drop-shadow(5px 5px 5px #879696)",
}

SUM_PLOT_CONTAINER = {
    "display": "none",
    "borderRadius": "10px",
    "background": "white",
    "padding": "5px",
    "margin":"5px",
    "fontFamiliy":"Avenir",
    "filter": "drop-shadow(5px 5px 5px #879696)",
}


template = {"layout": {"paper_bgcolor": bgcolor, "plot_bgcolor": bgcolor}}


def set_type_of_node(nodeid):
    node_type = nodeid
    if nodeid.startswith("taxi"):
        node_type = "taxi"
    elif nodeid.startswith("traffic"):
        node_type = "traffic"

    return node_type


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
    elements= []
    for node in infrastructure["nodes"]:
        if "x" in node and "y" in node:
            position = {'x': node["x"], 'y': node["y"]}
        else:
            position = {'x': 0, 'y': 0}

        elements.append({
            'data': {'id': node["id"], 'label': node["id"]},
            'position': position,
            'classes': set_type_of_node(node['id']),
            'selectable': node["id"] in get_selectable_nodes()
        }
        )
    for link in infrastructure["links"]:
        src, dst = link["id"].split("$")
        elements.append({
            'data': {'source': src, 'target': dst, "id": link["id"]},
            'position': position,
            'classes': link['id']
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

def power_fig(measurements, node_ids: List[str]):
    df = measurements.pivot(index='time', columns='id', values=["static_power", "dynamic_power"])
    df.columns = df.columns.swaplevel()

    fig = go.Figure()
    for node_id in node_ids:
        node_df = df[node_id]
        fig.add_trace(go.Scatter(x=node_df.index, y=node_df["static_power"], name=node_id + " Static power", line_width=1 ))
        fig.add_trace(go.Scatter(x=node_df.index, y=node_df["dynamic_power"],  name=node_id + " Dynamic power",  line_width=1))


    fig.update_layout(
        title=f"Power usage: {', '.join(node_ids)}",
        xaxis_title="Time in sec",
        yaxis_title="Power usage (Watt)",
        font_family="Avenir",
        font_color="black",

        legend=dict(
            x=1,
            y=1,
            traceorder="normal",

        ),
        plot_bgcolor='#e5ecf6',
        #paper_bgcolor="white"

    )
    fig.update_xaxes(showline=True, linewidth=1, linecolor='white', gridcolor='white')
    fig.update_yaxes(showline=True, linewidth=1, linecolor='white', gridcolor='white')

    return fig

def sum_power_fig(measurements, node_ids: List[str]):
    df = pd.DataFrame(measurements, columns=["time", "id", "static_power", "dynamic_power"])
    df = df[df["id"].isin(node_ids)].groupby("time").sum()
    fig = go.Figure()

    fig.add_trace(go.Scatter(x=df.index, y=df["static_power"], name="Sum Static power", line_width=1 ))
    fig.add_trace(go.Scatter(x=df.index, y=df["dynamic_power"],  name="Sum Dynamic power", line_width=1))

    fig.update_layout(
        title=f"Summed power usage: {', '.join(node_ids)}",
        xaxis_title="Time in sec",
        yaxis_title="Summed power usage (Watt)",
        font_family="Avenir",
        font_color="black",
        legend=dict(
            x=1,
            y=1,
            traceorder="normal",
        ),
        plot_bgcolor='#e5ecf6',
        #paper_bgcolor="white"

    )
    fig.update_xaxes(showline=True, linewidth=1, linecolor='white', gridcolor='white')
    fig.update_yaxes(showline=True, linewidth=1, linecolor='white', gridcolor='white')

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
                'width': "100px",
                'height': "100px",
            }
        })

def highlight_selectable_nodes():
    for nodeID in get_selectable_nodes():
        NETWORK_STYLESHEET.append({
            "selector": "." + nodeID,
            "style": {
                "backgroundColor": "#ABE8E8",
                'content': 'data(label)',
                'width': "100px",
                'height': "100px",
            }
        })

config, infrastructure, node_measurements, link_measurements = load_data("../examples/smart_city_traffic/vis_results/fog_2")
timeseries_chart = dcc.Graph(
    config={"displayModeBar": True},
    style= CHART_STYLE,
    figure={}
)
sum_chart = dcc.Graph(
    config={"displayModeBar": True},
    style= SUM_CHART_STYLE,
    figure={}
)

def main():
    # https://dash.plotly.com/cytoscape/reference
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
        html.Div(children=["Node info"], style={"border": "2px solid white",
                                                "borderRadius": "15px",
                                                "padding": "8px",
                                                "color": "black",
                                                "fontFamily": "Avenir",
                                                "fontSize": "large"})
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

        html.Div([
            html.Div(
                dbc.Row([
                        dcc.Input(
                             id="input",
                             type="text",
                             value="",
                             placeholder="search for node types...",
                             style={
                                 "width": "300px",
                                 "zIndex": "10",
                                 "height": "38px",
                                 "borderRadius": "50px",
                                 "padding": "3px",
                                 "margin": "5px",
                                 "marginLeft": "20px",
                                 "borderStyle": "none"
                             }
                         ),
                        html.Button('Search', id='submit-val', n_clicks=0,
                                    style={"width": "100px",
                                           "height": "38px",
                                           "zIndex": "10",
                                           "position": "absolute",
                                           "top": "5px",
                                           "left": "220px",
                                           "borderStyle": "none",
                                           "backgroundColor": "transparent",
                                           "borderRadius": "50px",
                                           "color": "#a2c2c2"

                                           }),
                        html.Button(children=['Select all'], id="select", className="selectButton", n_clicks=0, style=SELECT_STYLE),
                        html.Button(children=['Deselect all'], id="deselect", className="deselectButton", n_clicks=0, style=DESELECT_STYLE),
                        html.Div(id='container-button-basic', children='')
                        ], style={"alignItems": "baseline"}
                        ), style={"display": "table-caption"}
                    )

        ], id="header", style={"backgroundColor": "#A2C2C2", "display": "flex", "position":"sticky", "zIndex":"10"}
        ),

        dbc.Row([
            dbc.Col(html.Div(network, className='networkContainer')),
        ], className='childrenContainer', id="networkID"),
        sum_chart,

    ],  style={"overflow": "hidden"}, id="applayoutID")

    last_plot: [] = [None]

    def are_nodes_selectable(selectednodedata):
        all_selectable = True
        legal_nodes_list = []
        for node in selectednodedata:
            #node ist nicht legal
            if not node["id"] in get_selectable_nodes():
                #die legale liste bleibt leer
                all_selectable = False
            #node ist legal
            else:
                #liste wird mit dem legalen node gefüllt
                legal_nodes_list.append(node)

        return all_selectable, legal_nodes_list

    def generate_selected_edge_data(tap_edge):
        if not tap_edge in selected_edge_data and tap_edge is not None:
            selected_edge_data.append(tap_edge)
        else:
            return selected_edge_data
        return selected_edge_data

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
                        elem["style"]["width"] = '100px'
                        elem["style"]["height"] = '100px'
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
                        el["style"]["width"] = '100px'
                        el["style"]["height"] = '100px'

        if selected_node_data and is_first_call:
                NETWORK_STYLESHEET.append({
                    "selector": "." + nodeID,
                    "style": {
                        "backgroundColor": "#A2C2C2",
                        'content': 'data(label)',
                        'width': "100px",
                        'height': "100px",
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
        node_panel_children = [dbc.Row(last_selected_node_content[0], style=NODE_NAMES_STYLE),sum_chart, timeseries_chart, node_info]
        timeseries_chart_nodes = get_selectable_nodes()
        show_element(SELECT_STYLE, not is_select)
        show_element(DESELECT_STYLE, is_select)
        last_plot[0] = timeseries_chart_nodes
        return node_panel_children, timeseries_chart_nodes
    last_selected_node_content: [] = [None]
    n_clicks_select_backup = [1]
    n_clicks_deselect_backup = [1]
    n_clicks_input_backup = [1]

    def input_button_clicked(values):
        legal_values = []

        i = 0
        while i < len(values):
            for elem in infrastructure_to_cyto_dict(infrastructure["100"]):
                #the infrastructure contains the value written to the input
                elem_id = elem["data"]["id"]
                if not is_edge(elem_id) and values[i].strip() in elem_id:
                    if elem_id not in legal_values:
                        legal_values += [elem_id]
                        SUM_CHART_STYLE["display"] = "block"
                    if not is_node_panel_open():
                        open_node_panel()
                    content_string = "The following nodes were found: "
                    content = html.Div(content_string + " ".join(legal_values), style={"width": "50%", "position": "absolute"})

            if not legal_values:
                close_node_panel()
                content = html.Div("Nothing found", style={"width": "50%", "position": "absolute"})
            i += 1
        set_selected_nodes(get_selectable_nodes())
        converted_legal_values = list(map(lambda x: {'id': x}, legal_values))
        all_selectable, selectable_legal_values = are_nodes_selectable(converted_legal_values)
        converted_selectable_legal_values = list(map(lambda x: x['id'], selectable_legal_values))
        return converted_selectable_legal_values, content

    def is_edge(elem_id):
        if "$" in elem_id:
            return True
        else:
            return False

    selected_edge_data = []
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
        Output(sum_chart, component_property="figure"),
        Output('container-button-basic', 'children'),
        Input(network, component_property='selectedNodeData'),
        Input("select", "n_clicks"),
        Input("deselect", "n_clicks"),
        Input(network, "tapNodeData"),
        Input(network, "tapEdgeData"),
        Input('submit-val', 'n_clicks'),
        State('input', 'value')

    )
    def update_click(selectedNodeData, n_clicks_select, n_clicks_deselect, tapNodeData, tap_edge, n_clicks, value):
        NODEPANEL_STYLE["width"] = "50%"
        SUM_CHART_STYLE["display"] = "none"
        node_panel_children = ["", sum_chart, timeseries_chart, node_info]
        timeseries_chart_nodes = []
        timeseries_chart_figure = None
        select_button_clicked = False
        deselect_button_clicked = False
        reset_dash_nodes()

        # #Auf Kante geklickt
        # if tap_edge is not None:
        #     print("tap_edge")
        #     print(tap_edge)
            #timeseries_chart_links = [tap_edge["id"]]
            #timeseries_chart_figure = power_fig(link_measurements, timeseries_chart_links)

        sum_chart_figure = sum_power_fig(node_measurements, timeseries_chart_nodes)
        # auf submit button geklickt
        if n_clicks == n_clicks_input_backup[0]:
            n_clicks_input_backup[0] += 1

            #check if value is in network
            legal_values, content = input_button_clicked(value.split(","))

            node_panel_children = [dbc.Row(legal_values, style=NODE_NAMES_STYLE),sum_chart, timeseries_chart, node_info]
            timeseries_chart_figure = power_fig(node_measurements, legal_values)
            sum_chart_figure = sum_power_fig(node_measurements, legal_values)

            return [NODEPANEL_STYLE, node_panel_children, timeseries_chart_figure, NETWORK_STYLESHEET, SELECT_STYLE,
                DESELECT_STYLE, OVERLAY_STYLE, sum_chart_figure, content]

        # auf select button geklickt
        if n_clicks_select == n_clicks_select_backup[0]:
            select_button_clicked = True
            node_panel_children, timeseries_chart_nodes = button_clicked(n_clicks_select_backup, True)
            timeseries_chart_figure = power_fig(node_measurements, timeseries_chart_nodes)
            SUM_CHART_STYLE["display"] = "block"
            sum_chart_figure = sum_power_fig(node_measurements, timeseries_chart_nodes)
            node_panel_children = [dbc.Row(last_selected_node_content[0], style=NODE_NAMES_STYLE),
                                   sum_chart,
                                   timeseries_chart, node_info]

        # auf deselect button geklickt
        if n_clicks_deselect == n_clicks_deselect_backup[0]:
            deselect_button_clicked = True
            node_panel_children, timeseries_chart_nodes = button_clicked(n_clicks_deselect_backup, False)
            timeseries_chart_figure = power_fig(node_measurements, timeseries_chart_nodes)

        if select_button_clicked or deselect_button_clicked:
            return [NODEPANEL_STYLE, node_panel_children, timeseries_chart_figure, NETWORK_STYLESHEET, SELECT_STYLE,
                    DESELECT_STYLE, OVERLAY_STYLE, sum_chart_figure, ""]
        show_element(SELECT_STYLE, True)
        show_element(DESELECT_STYLE, False)
        show_element(OVERLAY_STYLE, False)
        if selectedNodeData is None:
            if not select_button_clicked:
                close_node_panel()
        else:
            # liste ist leer
            all_selectable, legal_nodes_list = are_nodes_selectable(selectedNodeData)
            if not selectedNodeData:
                close_node_panel()
                timeseries_chart_nodes = last_plot[0]
                node_panel_children = [dbc.Row(last_selected_node_content[0], style=NODE_NAMES_STYLE), sum_chart, timeseries_chart, node_info]
            else:
                #selected liste ist nicht leer und node is selectable
                #if are_nodes_selectable returns selectedNodeData

                if (all_selectable or legal_nodes_list) and tapNodeData["id"] in get_selectable_nodes():
                    last_selected_node_content[0] = ', '.join([el["id"] for el in legal_nodes_list])
                    set_selected_nodes([el["id"] for el in legal_nodes_list])
                    node_panel_children = [dbc.Row(last_selected_node_content[0], style=NODE_NAMES_STYLE),
                                           sum_chart,
                                           timeseries_chart, node_info]
                    timeseries_chart_nodes = [el["id"] for el in legal_nodes_list]
                    last_plot[0] = timeseries_chart_nodes
                    open_node_panel()
                    if len(legal_nodes_list) > 1:
                        SUM_CHART_STYLE["display"] = "block"
                        sum_chart_figure = sum_power_fig(node_measurements, timeseries_chart_nodes)
                        node_panel_children = [dbc.Row(last_selected_node_content[0], style=NODE_NAMES_STYLE),
                                               sum_chart,
                                               timeseries_chart, node_info]

                # geklickter node ist nicht selektierbar
                #if are_nodes_selectable returns empty list
                else:
                    last_selected_nodes_id_list = last_plot[0]
                    if last_selected_nodes_id_list is not None and is_node_panel_open():
                        set_selected_nodes(last_selected_nodes_id_list)
                        node_panel_children = [dbc.Row(last_selected_node_content[0], style=NODE_NAMES_STYLE),dbc.Row(sum_chart, style=SUM_PLOT_CONTAINER), timeseries_chart, node_info]
                        timeseries_chart_nodes = last_plot[0]
                        open_node_panel()
        timeseries_chart_figure = power_fig(node_measurements, timeseries_chart_nodes)
        return [NODEPANEL_STYLE, node_panel_children, timeseries_chart_figure, NETWORK_STYLESHEET, SELECT_STYLE,
                DESELECT_STYLE, OVERLAY_STYLE, sum_chart_figure, ""]

    app.run_server(debug=True)


if __name__ == "__main__":
    main()