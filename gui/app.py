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
    "transition": "right 1000ms",
    "backgroundColor": "#A2C2C2",
    "zIndex": "10000",
    "color": "white",
    "padding": "20px",
    "overflow": "hidden"

}

SELECT_BUTTON = {
    "padding": "15px",
    "width": "150px",
    "margin": "10px",
    "backgroundColor": "white",
    "position": "absolute",
    "zIndex": "10",
    "top": "40px",
    "left": "10px",
    "borderRadius": "50px",
    "fontSize": "larger",
    "border": "3px #A2C2C2 solid",
    "color": "#A2C2C2",
}

GRAY_BUTTON = {
    "padding": "15px",
    "width": "150px",
    "margin": "10px",
    "backgroundColor": "gray",
    "position": "absolute",
    "zIndex": "10",
    "top": "40px",
    "left": "10px",
    "borderRadius": "50px",
    "fontSize": "larger",
    "border": "3px #A2C2C2 solid",
    "color": "#A2C2C2",

}
DESELECT_BUTTON = {
    "display":"none",
    "padding": "15px",
    "width": "150px",
    "margin": "10px",
    "backgroundColor": "white",
    "position": "absolute",
    "zIndex": "10",
    "top": "40px",
    "left": "170px",
    "borderRadius": "50px",
    "fontSize": "larger",
    "border": "3px #A2C2C2 solid",
    "color": "#A2C2C2",

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

    )

    app = dash.Dash(external_stylesheets=[dbc.themes.BOOTSTRAP])

    node_info = html.Div([
        html.H5(children=["Node info"], style={"color": "black"}, id="title")

    ], style=NODE_INFO)

    node_panel = html.Div([

         dbc.Row(
             timeseries_chart, className='plotContainer', style=PLOT_CONTAINER, id="test"
        
         ),
         node_info
    ], style=NODEPANEL_STYLE, id="nodepanelID")

    app.layout = html.Div([
        node_panel,
        dbc.Row([
            dbc.Col(html.H5(children=[""], className='header')),
        ], style={"backgroundColor": "rgba(239, 239, 239, 1)"}, id="headerID"),
        html.Button(children=['Select all'], id="select", className="selectButton", n_clicks=0, style=SELECT_BUTTON),
        html.Button(children=['Deselect all'], id="deselect", n_clicks=0, style=DESELECT_BUTTON),


        dbc.Row([
            dbc.Col(html.Div(network, className='networkContainer')),
        ], className='childrenContainer', id="networkID")
    ],  style={"overflow": "hidden"}, id="applayoutID")

    last_plot: [] = [None]
    @app.callback(
        Output(timeseries_chart, component_property='figure'),
        Output('select', 'style'),
        Output('deselect', 'style'),
        Input(network, component_property='selectedNodeData'),  # tapNodeData
        Input('select', 'n_clicks'),
        #wenn auf deselect geklickt wird
    )
    def update_plot(input_value, n_clicks_select):
        print("update plot")
        print(input_value)
        SELECT_BUTTON["backgroundColor"] = "white"
        if (input_value is None or not input_value) and n_clicks_select is not None:
            if n_clicks_select > 0:
                print("return A")
                SELECT_BUTTON["backgroundColor"] = "gray"
                DESELECT_BUTTON["display"] = "block"
                return power_fig(node_measurements, get_selectable_nodes()), SELECT_BUTTON, DESELECT_BUTTON
        DESELECT_BUTTON["display"] = "none"

        if input_value is None:
            print("nothing selected")
            return power_fig(node_measurements, []), SELECT_BUTTON, DESELECT_BUTTON
        else:
            print("graf")
            if not input_value:
                print("dont update")
                return power_fig(node_measurements, last_plot[0]), SELECT_BUTTON, DESELECT_BUTTON
            else:
                if input_value[0]["id"] in get_selectable_nodes():
                    last_plot[0] = [el["id"] for el in input_value]
                    return power_fig(node_measurements, last_plot[0]), SELECT_BUTTON, DESELECT_BUTTON
                else:
                    return power_fig(node_measurements, []), SELECT_BUTTON, DESELECT_BUTTON

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

    last_selected_node_content: [] = [None]
    n_clicks_backup = [0]
    @app.callback(
        Output(node_panel, 'style'),
        Output(node_panel, "children"),
        Output(network, "stylesheet"),
        Input(network, component_property='selectedNodeData'),  # tapNodeData
        Input('select', 'n_clicks'),
    )
    def update_nodePanel(selectedNodeData, n_clicks):
        print("akjsdaklsdjaslkdjaskljd")
        print(n_clicks)
        print(n_clicks_backup[0])

        #nichts wurde selektiert aber der button wurde geklickt
        if (selectedNodeData is None or not selectedNodeData) and n_clicks is not None:

            close_node_panel()
            print("n_clicks update nodepanel")
            print(selectedNodeData)
            #wenn der button geklickt wurde
            if n_clicks > 0:
                print("button clicked")
                #passe den style aller selektierbaren nodes an
                set_selected_nodes(get_selectable_nodes())
                #speichere deren ids im chart
                x = ', '.join([el for el in get_selectable_nodes()])

                print(last_selected_node_content)
                #öffne den panel
                open_node_panel()
                #
                return NODEPANEL_STYLE, [x, dbc.Col(timeseries_chart, style=PLOT_CONTAINER), node_info], NETWORK_STYLESHEET
            else:
                return NODEPANEL_STYLE, [last_selected_node_content[0], dbc.Col(timeseries_chart, style=PLOT_CONTAINER),  node_info], NETWORK_STYLESHEET

        #button wurde nicht geklickt
        else:
            if is_node_panel_open() and not selectedNodeData and n_clicks is None:
                close_node_panel()
                print("button not clicked")

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

                        set_selected_nodes([el["id"] for el in selectedNodeData])
                        open_node_panel()
                        return NODEPANEL_STYLE, [ last_selected_node_content[0], dbc.Col(timeseries_chart, style=PLOT_CONTAINER) , node_info], NETWORK_STYLESHEET
                else:
                    # node is not selectable
                    print("node is not selectable")
                    return NODEPANEL_STYLE, [ last_selected_node_content[0], dbc.Col(timeseries_chart, style=PLOT_CONTAINER) , node_info], NETWORK_STYLESHEET

    app.run_server(debug=True)


if __name__ == "__main__":
    main()