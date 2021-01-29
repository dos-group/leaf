from typing import List, Tuple, Iterator

import networkx as nx
import numpy as np
import simpy

from examples.smart_city_traffic.infrastructure import Cloud, FogNode, TrafficLight, LinkWanUp, LinkEthernet, \
    LinkWifiBetweenTrafficLights, LinkWanDown, LinkWifiTaxiToTrafficLight, Taxi
from examples.smart_city_traffic.mobility import Location
from examples.smart_city_traffic.orchestrator import CityOrchestrator
from examples.smart_city_traffic.settings import *
from src.infrastructure import Infrastructure


class City:
    def __init__(self, env: simpy.Environment):
        self.env = env
        self.street_graph, self.entry_point_locations, self.traffic_light_locations = _create_street_graph()
        self.infrastructure = Infrastructure()
        self.orchestrator = CityOrchestrator(self.infrastructure, utilization_threshold=FOG_UTILIZATION_THRESHOLD)

        # Create infrastructure
        self.infrastructure.add_node(Cloud())
        for location in self.traffic_light_locations:
            self._add_traffic_light(location)
        for location in RNG.choice(self.traffic_light_locations, FOG_DCS):
            self._add_fog_node(location)

        # Start update wifi connections process
        self.update_wifi_connections_process = self.env.process(self._update_wifi_connections())

        # Place CCTV applications
        for traffic_light in self.infrastructure.nodes(type_filter=TrafficLight):
            self.orchestrator.place(traffic_light.application)

    def add_taxi_and_start_v2i_app(self, taxi: Taxi):
        """Cars are connected to all traffic light systems in range via WiFi.

        Note: This initial allocation may change during simulation since taxis are mobile.
        """
        for traffic_light in self._traffic_lights_in_range(taxi):
            self.infrastructure.add_link(LinkWifiTaxiToTrafficLight(taxi, traffic_light))
        self.orchestrator.place(taxi.application)

    def remove_taxi_and_stop_v2i_app(self, taxi: Taxi):
        taxi.application.deallocate()
        self.infrastructure.remove_node(taxi)

    def _add_traffic_light(self, location: Location):
        """Traffic lights are connected to the cloud via WAN and to other traffic lights in range via WiFi."""
        cloud: Cloud = self.infrastructure.nodes(type_filter=Cloud)[0]
        traffic_light = TrafficLight(location, application_sink=cloud)
        self.infrastructure.add_link(LinkWanUp(traffic_light, cloud))
        self.infrastructure.add_link(LinkWanDown(cloud, traffic_light))
        for traffic_light_ in self._traffic_lights_in_range(traffic_light):
            self.infrastructure.add_link(LinkWifiBetweenTrafficLights(traffic_light, traffic_light_))
            self.infrastructure.add_link(LinkWifiBetweenTrafficLights(traffic_light_, traffic_light))

    def _add_fog_node(self, location: Location):
        """Fog nodes are connected to a traffic lights via Ethernet (no power usage)"""
        fog_node = FogNode(location)
        for traffic_light in self.infrastructure.nodes(type_filter=TrafficLight):
            if traffic_light.location == location:
                self.infrastructure.add_link(LinkEthernet(traffic_light, fog_node))
                self.infrastructure.add_link(LinkEthernet(fog_node, traffic_light))

    def _update_wifi_connections(self):
        """Recalculates the traffic lights in range for all taxis."""
        g = self.infrastructure.graph
        while True:
            yield self.env.timeout(UPDATE_WIFI_CONNECTIONS_INTERVAL)
            for taxi in self.infrastructure.nodes(type_filter=Taxi):
                traffic_lights_connected = set(nx.neighbors(g, taxi.name))
                traffic_lights_in_range = set(tl.name for tl in self._traffic_lights_in_range(taxi))
                traffic_lights_to_remove = traffic_lights_connected - traffic_lights_in_range
                traffic_lights_to_add = traffic_lights_in_range - traffic_lights_connected
                for traffic_light_name in traffic_lights_to_remove:
                    g.remove_edge(taxi.name, traffic_light_name)
                for traffic_light_name in traffic_lights_to_add:
                    self.infrastructure.add_link(LinkWifiTaxiToTrafficLight(taxi, self.infrastructure.node(traffic_light_name)))

    def _traffic_lights_in_range(self, node) -> Iterator[TrafficLight]:
        for traffic_light_ in self.infrastructure.nodes(type_filter=TrafficLight):
            if node.location.distance(traffic_light_.location) <= WIFI_RANGE:
                yield traffic_light_


def _create_street_graph() -> Tuple[nx.Graph, List[Location], List[Location]]:
    graph = nx.Graph()
    n_points = STREETS_PER_AXIS + 2  # crossings + entry points
    step_size_x = CITY_WIDTH / (n_points - 1)
    step_size_y = CITY_HEIGHT / (n_points - 1)

    entry_point_locations = []
    traffic_light_locations = []
    locations = [[None for _ in range(n_points)] for _ in range(n_points)]
    for x in range(n_points):
        for y in range(n_points):
            location = Location(x * step_size_x, y * step_size_y)
            if x == 0 or x == n_points - 1 or y == 0 or y == n_points - 1:
                entry_point_locations.append(location)
            else:
                traffic_light_locations.append(location)
            locations[x][y] = location
            graph.add_node(location)
            if x > 0 and y > 0:
                if y < n_points - 1:
                    graph.add_edge(location, locations[x - 1][y])
                if x < n_points - 1:
                    graph.add_edge(location, locations[x][y - 1])

    for corner_location in [locations[0][0],
                            locations[n_points - 1][0],
                            locations[0][n_points - 1],
                            locations[n_points - 1][n_points - 1]]:
        graph.remove_node(corner_location)
        entry_point_locations.remove(corner_location)

    return graph, entry_point_locations, traffic_light_locations
