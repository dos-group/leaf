import json
import logging
import random

import simpy
import pandas as pd

from leaf.infrastructure import Node, Infrastructure, Link
from leaf.power import PowerModelNode, PowerModelLink

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s\t%(message)s')

{
    "config": {
    },
    "network": {
        0: {
            "nodes": [
                {
                    "id": "car-1",
                    "class": "Car",
                    "x": 123,
                    "y": 20,
                    # other: cu, power_model, ...
                }
            ],
            "link": [
                {
                    "id": "car-1$car-2",
                    "class": "wifi",
                }
            ]
        }
    },
    "node_measurements": {

    },
    "link_measurements": {

    }
}


def Visualizer:

    def __init__(env):
        self.env = env

    def increase_load_process(env, node: Node):
        while node.used_cu < node.cu:
            yield env.timeout(1)
            node.used_cu += 1


def main():
    infrastructure = create_infrastructure()
    node_measurements = []
    link_measurements = []

    env = simpy.Environment()
    env.process(increase_load_process(env, infrastructure.node("cloud")))
    env.process(random_load_process(env, infrastructure.node("fog")))
    env.process(monitoring_process(env, infrastructure, node_measurements, link_measurements))
    env.run(until=10)

    # Write result files
    write_infrastructure_graph("data_generator/example1_data/infrastructure.json", infrastructure)
    pd.DataFrame(node_measurements).to_csv("data_generator/example1_data/node_measurements.csv", index=False)
    pd.DataFrame(link_measurements).to_csv("data_generator/example1_data/link_measurements.csv", index=False)


def create_infrastructure():
    infrastructure = Infrastructure()
    sensor = Node("sensor", cu=1, power_model=PowerModelNode(max_power=1.8, static_power=0.2))
    sensor.used_cu = 1
    fog_node = Node("fog", cu=400, power_model=PowerModelNode(max_power=200, static_power=30))
    cloud = Node("cloud", power_model=PowerModelNode(power_per_cu=0.5))
    wifi_link_up = Link(sensor, fog_node, latency=10, bandwidth=30e6, power_model=PowerModelLink(energy_per_bit=300))
    wan_link_up = Link(fog_node, cloud, latency=5, bandwidth=1e9, power_model=PowerModelLink(energy_per_bit=6000))
    infrastructure.add_link(wifi_link_up)
    infrastructure.add_link(wan_link_up)
    return infrastructure


def increase_load_process(env, node: Node):
    while node.used_cu < node.cu:
        yield env.timeout(1)
        node.used_cu += 1


def random_load_process(env, node: Node):
    while True:
        yield env.timeout(1)
        node.used_cu = random.random() * node.cu


def monitoring_process(env: simpy.Environment, infrastructure: Infrastructure, node_measurements, link_measurements):
    while True:
        for node in infrastructure.nodes():
            power_measurement = node.measure_power()
            node_measurements.append({
                "time": env.now,
                "id": node.name,
                "used_cu": node.used_cu,
                "static_power": power_measurement.static,
                "dynamic_power": power_measurement.dynamic,
            })
        for link in infrastructure.links():
            power_measurement = link.measure_power()
            link_measurements.append({
                "time": env.now,
                "id": link.src.name + "$" + link.dst.name,
                "used_bandwidth": link.used_bandwidth,
                "static_power": power_measurement.static,
                "dynamic_power": power_measurement.dynamic,
            })
        yield env.timeout(1)


def write_infrastructure_graph(outfile: str, infrastructure: Infrastructure):
    nodes = []
    for node in infrastructure.nodes():
        node: Node
        node_dict = {
            "id": node.name,
            "class": node.__class__.__name__,
#            "cu": node.cu,
#            "power_model": {  # TODO this should be refactored into LEAF core
#                "max_power": node.power_model.max_power,
#                "static_power": node.power_model.static_power,
#                "power_per_cu": node.power_model.power_per_cu,
#            },
        }
        if hasattr(node, 'location'):
        nodes.append(node_dict)

    links = []
    for link in infrastructure.links():
        links.append({
            "id": link.src.name + "$" + link.dst.name,
#            "src": link.src.name,
#            "dst": link.dst.name,
            "class": link.__class__.__name__,
#            "bandwidth": link.bandwidth,
#            "latency": link.latency,
#            "power_model": {  # TODO this should be refactored into LEAF core
#                "energy_per_bit": link.power_model.energy_per_bit,
#            },
        })

    graph = {"nodes": nodes, "links": links}
    with open(outfile, "w") as f:
        json.dump(graph, f)


if __name__ == "__main__":
    main()
