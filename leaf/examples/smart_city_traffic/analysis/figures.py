"""Utility class for figure styles."""

import plotly.graph_objs as go
from plotly.subplots import make_subplots


def base_figure(fig: go.Figure = None) -> go.Figure:
    if not fig:
        fig = go.Figure()
    fig.update_layout(template="plotly_white",
                      legend_orientation="h",
                      legend=dict(x=0, y=1.1),
                      xaxis=dict(mirror=True, linewidth=1, linecolor='black', ticks = '', showline=True),
                      yaxis=dict(mirror=True, linewidth=1, linecolor='black', ticks = '', showline=True))
    return fig


def timeline_figure(fig: go.Figure = None, yaxes_title: str = "Power Usage (Watt)") -> go.Figure:
    fig = base_figure(fig)
    fig.update_xaxes(
        title=dict(text="Time", standoff=0),
        ticktext=[" ", "04:00", "08:00", "12:00", "16:00", "20:00", "24:00"],
        tickvals=[h * 120 * 60 * 2 for h in range(13)],
    )
    fig.update_yaxes(
        title=dict(text=yaxes_title, standoff=0),
        rangemode="nonnegative",
    )
    fig.update_layout(
        height=370,
        width=500,
        font=dict(size=9),
        legend=dict(x=0, y=1.16),
    )
    return fig


def single_experiment_figure():
    fig = timeline_figure()
    fig.update_layout(
        height=450,
        width=600,
        legend=dict(x=0, y=1.12),
    )
    return fig


def barplot_figure(fig: go.Figure = None) -> go.Figure:
    fig = base_figure(fig)
    fig.update_layout(barmode='stack')
    fig.update_yaxes(title=dict(text="kWh consumed in 24h", standoff=0))
    fig.update_layout(
        height=420,
        width=565,
        font=dict(size=10),
        legend=dict(yanchor="bottom", y=1.01, x=-0.02),
    )
    # Fine tuning: Make chart a little higher than plotly suggests so the labels aren't cut off
    fig.update_yaxes(range=[0, 70])
    return fig


def subplot_figure():
    fig = make_subplots(rows=1, cols=3, shared_yaxes=True, horizontal_spacing=0.01)
    fig = timeline_figure(fig)
    fig.update_layout(
        height=320,
        width=1000,
        font=dict(size=9),
        legend=dict(x=0, y=1.215),
    )
    fig.update_yaxes(title_text=None)
    fig.update_yaxes(title=dict(text="Power Usage (Watt)", standoff=0), row=1, col=1)

    fig.update_xaxes(showline=True, linewidth=1, linecolor='black', mirror=True)
    fig.update_yaxes(showline=True, linewidth=1, linecolor='black', mirror=True)
    return fig


def taxi_figure() -> go.Figure:
    # Create figure with secondary y-axis
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig = timeline_figure(fig=fig)

    fig.update_yaxes(title_text="Taxis generated per minute", secondary_y=False)
    fig.update_yaxes(title_text="Driving speed (km/h)", secondary_y=True)
    # fig.update_xaxes(range=[0, 86400])
    return fig
