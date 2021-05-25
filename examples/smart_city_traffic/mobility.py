import math
from typing import List, Optional

import networkx as nx
import simpy

from examples.smart_city_traffic.infrastructure import TrafficLight, Taxi
from examples.smart_city_traffic.settings import UPDATE_MOBILITY_INTERVAL, MAX_CARS_PER_MINUTE, RNG, \
    TAXI_COUNT_DISTRIBUTION, TAXI_SPEED_DISTRIBUTION


class Location:
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y

    def distance(self, location: "Location") -> float:
        return math.sqrt((location.y - self.y) * (location.y - self.y) + (location.x - self.x) * (location.x - self.x))

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y

    def __hash__(self):
        return hash((self.x, self.y))


class MobilityManager:

    def __init__(self, env: simpy.Environment, city: "City"):
        self.env = env
        self.city = city
        self.add_taxis_process = env.process(self._add_taxis_process())

    def _add_taxis_process(self):
        while True:
            for taxi in self._create_taxis():
                self.city.add_taxi_and_start_v2i_app(taxi)
                self.env.process(self._remove_taxi_process(taxi))
            yield self.env.timeout(UPDATE_MOBILITY_INTERVAL)

    def _remove_taxi_process(self, taxi: "Taxi"):
        yield self.env.timeout(taxi.mobility_model.life_time)
        self.city.remove_taxi_and_stop_v2i_app(taxi)

    def _create_taxis(self) -> List["Taxi"]:
        avg_taxi_speed = _avg_taxi_speed(self.env.now)
        avg_taxi_count = _avg_taxi_count(self.env.now)
        taxi_count = RNG.poisson(avg_taxi_count)
        return [self._create_taxi(speed=avg_taxi_speed) for _ in range(taxi_count)]

    def _create_taxi(self, speed: float) -> "Taxi":
        start = self._random_gate_location()
        dst = self._random_gate_location()
        while not start.distance(dst) > 0.5:
            dst = self._random_gate_location()
        path = nx.shortest_path(self.city.street_graph, source=start, target=dst)
        mobility_model = TaxiMobilityModel(path, speed=speed, start_time=self.env.now)
        return Taxi(self.env, mobility_model, application_sinks=self._traffic_lights_on_taxi_path(path))

    def _random_gate_location(self) -> Location:
        return RNG.choice(self.city.entry_point_locations)

    def _traffic_lights_on_taxi_path(self, path: List) -> List[TrafficLight]:
        return [tl for tl in self.city.infrastructure.nodes(type_filter=TrafficLight) if tl.location in path]

    # /**
    #      * Calculates which traffic light systems are in the path of the taxi.
    #      */
    #     private static List<TrafficLightSystem> getTrafficLightSystemsOnPath(Taxi taxi) {
    #         List<Location> locations = taxi.getMobilityModel().getPath().getVertexList();
    #         locations.remove(locations.size() - 1);
    #         locations.remove(0);
    #         Set<Location> locationSet = new HashSet<>(locations);
    #
    #         InfrastructureGraphCity topologyExp = (InfrastructureGraphCity) taxi.getSimulation().getNetworkTopology();
    #         return topologyExp.getTraficLightSystems().stream()
    #             .filter(tls -> locationSet.contains(tls.getLocation()))
    #             .collect(Collectors.toList());
    #     }


class TaxiMobilityModel:
    def __init__(self, path: List[Location], speed: float, start_time: float):
        self.start_time = start_time
        self._location_dict, self.life_time = self._create_location_dict(path, speed, interval=UPDATE_MOBILITY_INTERVAL)

    def location(self, time: float) -> Optional[Location]:
        try:
            return self._location_dict[self._time_to_map_key(time - self.start_time)]
        except KeyError:
            print(f"Error: {time}")
            return self._location_dict[max(self._location_dict.keys())]

    def _create_location_dict(self, path: List[Location], speed: float, interval: float):
        """Computes the random path of the taxi and precomputes its location at specific time steps."""
        distance_per_interval = speed * UPDATE_MOBILITY_INTERVAL

        last_location: Location = None
        remaining_meters_from_last_path = 0
        time = 0

        time_location_dict = {}
        for next_location in path:
            if last_location is not None:
                distance = next_location.distance(last_location)
                for fraction in self._get_fractions(distance, remaining_meters_from_last_path, distance_per_interval):
                    new_x = last_location.x + fraction * (next_location.x - last_location.x)
                    new_y = last_location.y + fraction * (next_location.y - last_location.y)
                    time_location_dict[self._time_to_map_key(time)] = Location(new_x, new_y)
                    time += interval
                remaining_meters_from_last_path = distance % distance_per_interval
            last_location = next_location
        return time_location_dict, time - interval  # TODO Check if this is correct

    @staticmethod
    def _get_fractions(path_distance: float, remaining_last_path_distance: float, distance_per_step: float):
        total_distance = path_distance + remaining_last_path_distance
        n_steps = int(total_distance / distance_per_step)
        fractions = []
        for i in range(n_steps):
            distance_on_path = i * distance_per_step - remaining_last_path_distance
            fractions.append(distance_on_path / path_distance)
        return fractions

    @staticmethod
    def _time_to_map_key(time: float) -> int:
        return int(round(time * 100) / 100)


def _avg_taxi_count(time: float):
    """Returns the average number of taxis that should be generated at this time step.
    The result will be passed to a Poisson distribution to determine the actual number.
    """
    # TODO Check int
    steps_per_minute = 60 / UPDATE_MOBILITY_INTERVAL
    minute = (time / steps_per_minute) % len(TAXI_COUNT_DISTRIBUTION)
    return TAXI_COUNT_DISTRIBUTION[int(minute)] / steps_per_minute * MAX_CARS_PER_MINUTE


def _avg_taxi_speed(time: float):
    """Returns the average speed of taxis at the time of the day."""
    # TODO Check int
    steps_per_minute = 60 / UPDATE_MOBILITY_INTERVAL
    minute = (time / steps_per_minute) % len(TAXI_SPEED_DISTRIBUTION)
    return TAXI_SPEED_DISTRIBUTION[int(minute)]
