"""Creates plots for one or more experiment runs.

The follow plots are created:
- A bar plot comparing all experiments in the specified directory
- A plot comparing experiments Fog 4 and Fog6s
- For every experiment a detailed plot on infrastructure component and application consumption.
  Additionally a plot for both applications that illustrates the static consumption.
"""

import os
import warnings
from typing import Tuple, Dict, List

import numpy as np
import pandas as pd
import plotly.graph_objs as go
from figures import subplot_figure, barplot_figure, timeline_figure, single_experiment_figure
from scipy import signal
from settings import SOURCE_DIR, RESULTS_DIR, EXPERIMENTS, EXPERIMENT_TITLES, COLORS

ExperimentResults = Dict[str, Tuple[pd.DataFrame, pd.DataFrame]]


def load_experiment_results() -> ExperimentResults:
    results = {}
    for experiment in EXPERIMENTS:
        df_i = pd.read_csv(os.path.join(SOURCE_DIR, experiment, "infrastructure.csv"), index_col="time")
        df_a = pd.read_csv(os.path.join(SOURCE_DIR, experiment, "applications.csv"), index_col="time")
        results[experiment] = (df_i, df_a)
    return results


def create_comparison_plot(results: ExperimentResults, name: str = None):
    fig = timeline_figure()
    for result, (df, _) in results.items():
        experiment_name = EXPERIMENT_TITLES[EXPERIMENTS.index(result)]
        series = df.drop(columns="taxis").sum(axis=1)
        fig.add_trace(go.Scatter(x=series.index, y=signal.savgol_filter(series, 3601, 3), name=experiment_name, line=dict(width=1)))
    fig.write_image(os.path.join(RESULTS_DIR, name))


def create_barplot(results: ExperimentResults):
    cloud = []
    fog_static = []
    fog_dynamic = []
    wifi = []
    wan = []
    for _, (df, _) in results.items():
        cloud.append(df["cloud dynamic"].sum() / 3600000)
        fog_static.append(df["fog static"].sum() / 3600000)
        fog_dynamic.append(df["fog dynamic"].sum() / 3600000)
        wifi.append(df["wifi dynamic"].sum() / 3600000)
        wan.append((df["wanUp dynamic"].sum() + df["wanDown dynamic"].sum()) / 3600000)
    total = list(np.array(cloud) + np.array(fog_static) + np.array(fog_dynamic) + np.array(wifi) + np.array(wan))

    fig = barplot_figure()
    fig.add_trace(go.Bar(name='Fog static', x=EXPERIMENT_TITLES, y=fog_static, marker_color=COLORS["fog_static"]))
    fig.add_trace(go.Bar(name='Fog dynamic', x=EXPERIMENT_TITLES, y=fog_dynamic, marker_color=COLORS["fog"]))
    fig.add_trace(go.Bar(name='Cloud', x=EXPERIMENT_TITLES, y=cloud, marker_color=COLORS["cloud"]))
    fig.add_trace(go.Bar(name='Wi-Fi', x=EXPERIMENT_TITLES, y=wifi, marker_color=COLORS["wifi"]))
    fig.add_trace(go.Bar(name='WAN', x=EXPERIMENT_TITLES, y=wan, marker_color=COLORS["wan"],
                         text=total, texttemplate='%{text:.2f}', textposition='outside'))
    fig.write_image(os.path.join(RESULTS_DIR, "barplot.pdf"))


def create_infrastructure_subplot(results: ExperimentResults):
    fig = subplot_figure()
    for i, (_, (df, _)) in enumerate(results.items(), 1):
        fig.add_trace(go.Scatter(x=df.index, y=df["wanUp dynamic"]+df["wanDown dynamic"], name="WAN", line=dict(width=1, color=COLORS["wan"]), showlegend=(i == 1)), row=1, col=i)
        fig.add_trace(go.Scatter(x=df.index, y=df["wifi dynamic"], name="Wi-Fi", line=dict(width=1, color=COLORS["wifi"]), showlegend=(i == 1)), row=1, col=i)
        fig.add_trace(go.Scatter(x=df.index, y=df["cloud dynamic"], name="Cloud", line=dict(width=1, color=COLORS["cloud"]), showlegend=(i == 1)), row=1, col=i)
        fig.add_trace(go.Scatter(x=df.index, y=df["fog static"] + df["fog dynamic"], name="Fog", line=dict(width=1, color=COLORS["fog"]), showlegend=(i == 1)), row=1, col=i)
        fig.add_trace(go.Scatter(x=df.index, y=df["fog static"], name="Fog static", line=dict(width=1, dash="1px,2px", color=COLORS["fog"]), showlegend=(i == 1)), row=1, col=i)
    fig.write_image(os.path.join(RESULTS_DIR, "infrastructure.pdf"))


def create_applications_subplot(results: ExperimentResults):
    fig = subplot_figure()
    for i, (_, (_, df)) in enumerate(results.items(), 1):
        fig.add_trace(go.Scatter(x=df.index, y=df["cctv static"] + df["cctv dynamic"], name="CCTV", line=dict(width=1, color=COLORS["cctv"]), showlegend=(i == 1)), row=1, col=i)
        fig.add_trace(go.Scatter(x=df.index, y=df["v2i static"] + df["v2i dynamic"], name="V2I", line=dict(width=1, color=COLORS["v2i"]), showlegend=(i == 1)), row=1, col=i)
    fig.write_image(os.path.join(RESULTS_DIR, "applications.pdf"))


def create_taxi_count_plot(df: pd.DataFrame):
    fig = timeline_figure(yaxes_title="Number of cars")
    fig.add_trace(go.Scatter(x=df.index, y=df["taxis"], name="Taxis", line=dict(width=1, color=COLORS["wan"])))
    return fig


def infrastructure_figure(df: pd.DataFrame):
    fig = single_experiment_figure()
    fig.add_trace(go.Scatter(x=df.index, y=df["wanUp dynamic"] + df["wanDown dynamic"], name="WAN", line=dict(width=1, color=COLORS["wan"])))
    fig.add_trace(go.Scatter(x=df.index, y=df["wifi dynamic"], name="Wi-Fi", line=dict(width=1, color=COLORS["wifi"])))
    fig.add_trace(go.Scatter(x=df.index, y=df["cloud dynamic"], name="Cloud", line=dict(width=1, color=COLORS["cloud"])))
    if (df["fog static"] + df["fog dynamic"]).sum() > 0:
        fig.add_trace(go.Scatter(x=df.index, y=df["fog static"] + df["fog dynamic"], name="Fog", line=dict(width=1, color=COLORS["fog"])))
        fig.add_trace(go.Scatter(x=df.index, y=df["fog static"], name="Fog static", line=dict(width=1, dash="dot", color=COLORS["fog"])))
    return fig


def applications_figure(df: pd.DataFrame):
    fig = single_experiment_figure()
    fig.add_trace(go.Scatter(x=df.index, y=df["cctv static"] + df["cctv dynamic"], name="CCTV", line=dict(width=1, color=COLORS["cctv"])))
    fig.add_trace(go.Scatter(x=df.index, y=df["v2i static"] + df["v2i dynamic"], name="V2I", line=dict(width=1, color=COLORS["v2i"])))
    return fig


def _filter_results(results: ExperimentResults, experiment_names: List[str]) -> ExperimentResults:
    return {k: v for k, v in results.items() if k in experiment_names}


if __name__ == '__main__':
    warnings.filterwarnings("ignore")
    results = load_experiment_results()

    for key, (df_i, df_a) in results.items():
        fig_i = infrastructure_figure(df_i)
        fig_a = applications_figure(df_a)
        os.makedirs(os.path.join(RESULTS_DIR, key), exist_ok=True)
        fig_i.write_image(os.path.join(RESULTS_DIR, key, "infrastructure.pdf"))
        fig_a.write_image(os.path.join(RESULTS_DIR, key, "applications.pdf"))

    create_barplot(results)

