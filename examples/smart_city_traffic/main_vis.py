import json
import logging
from os import makedirs
from typing import Optional, Callable, Dict

import pandas as pd
import simpy
from tqdm import tqdm

from examples.smart_city_traffic.city import City
from examples.smart_city_traffic.mobility import MobilityManager
from examples.smart_city_traffic.settings import SIMULATION_TIME, FOG_DCS, FOG_IDLE_SHUTDOWN
from leaf.infrastructure import Infrastructure, Node, Link
from mobility import Location
from power import PowerMeasurement

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.WARN, format='%(levelname)s: %(message)s')


class Visualizer:
    def __init__(self, infrastructure: Infrastructure, measurement_interval: Optional[float] = 1,
                 cytoscape_layout: Dict = None, default_location: Callable[[Node], Location] = None):
        """Periodically stores the infrastructure state and power consumption.

        Args:
            infrastructure: Infrastructure object to monitor
            measurement_interval: Time interval between two measurements
            cytoscape_layout: The Cytoscape layout, see https://dash.plotly.com/cytoscape/layout and
                https://js.cytoscape.org/#layouts
            default_location: If layout["name"] is "preset", this function will map nodes without location to its
                location on the visualization. Otherwise, this argument is ignored.
        """
        self.infrastructure = infrastructure
        self.measurement_interval = measurement_interval
        if cytoscape_layout is None:
            self.cytoscape_layout = {"name": "preset"}  # Default layout
        else:
            self.cytoscape_layout = cytoscape_layout
        self.default_location = default_location
        self.network_measurements = {}
        self.node_measurements = []
        self.link_measurements = []

    def run(self, env: simpy.Environment):
        while True:
            self.network_measurements[env.now] = self._infrastructure_network()
            for node in self.infrastructure.nodes():
                try:
                    measurement: PowerMeasurement = node.measure_power()
                except RuntimeError:
                    continue
                else:
                    self.node_measurements.append({"time": env.now, "id": node.name,
                                                   "static_power": measurement.static,
                                                   "dynamic_power": measurement.dynamic})
            for link in self.infrastructure.links():
                try:
                    measurement: PowerMeasurement = link.measure_power()
                except RuntimeError:
                    continue
                else:
                    self.link_measurements.append({"time": env.now, "id": self._link_to_id(link),
                                                   "static_power": measurement.static,
                                                   "dynamic_power": measurement.dynamic})
            yield env.timeout(self.measurement_interval)

    def save(self, outpath):
        makedirs(outpath, exist_ok=True)
        with open(f"{outpath}/config.json", "w") as f:
            json.dump({
                "measurement_interval": self.measurement_interval,
                "cytoscape_layout": self.cytoscape_layout,
            }, f)
        with open(f"{outpath}/infrastructure.json", "w") as f:
            json.dump(self.network_measurements, f, separators=(',', ':'))
        pd.DataFrame(self.node_measurements).to_csv(f"{outpath}/node_measurements.csv", index=False)
        pd.DataFrame(self.link_measurements).to_csv(f"{outpath}/link_measurements.csv", index=False)

    def _infrastructure_network(self):
        nodes = []
        for node in self.infrastructure.nodes():
            node: Node
            node_dict = {
                "id": node.name,
                "class": node.__class__.__name__,
            }

            if self.cytoscape_layout["name"] == "preset":
                if hasattr(node, "location") and node.location is not None:
                    location = node.location
                else:
                    location = self.default_location(node)
                node_dict["x"] = location.x
                node_dict["y"] = location.y

            nodes.append(node_dict)
        links = []
        for link in self.infrastructure.links():
            links.append({
                "id": self._link_to_id(link),
                "class": link.__class__.__name__,
            })
        return {"nodes": nodes, "links": links}

    def _link_to_id(self, link: Link) -> str:
        return link.src.name + "$" + link.dst.name


def main():
    # ----------------- Set up experiment -----------------
    env = simpy.Environment()
    city = City(env)
    mobility_manager = MobilityManager(city)
    env.process(mobility_manager.run(env))

    visualizer = Visualizer(city.infrastructure, measurement_interval=100, default_location=lambda _: Location(0, 0))
    env.process(visualizer.run(env))

    # ------------------ Run experiment -------------------
    for until in tqdm(range(1, SIMULATION_TIME)):
        env.run(until=until)

    # ------------------ Write results --------------------
    result_dir = f"vis_results/fog_{FOG_DCS}"
    if FOG_IDLE_SHUTDOWN:
        result_dir += "_shutdown"
    visualizer.save(result_dir)


if __name__ == '__main__':
    main()
