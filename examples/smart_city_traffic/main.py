import logging
from os import makedirs

import simpy
from tqdm import tqdm

from examples.smart_city_traffic.city import City
from examples.smart_city_traffic.infrastructure import Cloud, FogNode, Taxi, LinkWanDown, LinkWanUp, \
    LinkWifiTaxiToTrafficLight, LinkWifiBetweenTrafficLights, TrafficLight
from examples.smart_city_traffic.mobility import MobilityManager
from examples.smart_city_traffic.settings import SIMULATION_TIME, FOG_DCS, POWER_MEASUREMENT_INTERVAL, \
    FOG_IDLE_SHUTDOWN
from leaf.infrastructure import Infrastructure
from leaf.power import PowerMeter

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.WARN, format='%(levelname)s: %(message)s')


def main(count_taxis: bool, measure_infrastructure: bool, measure_applications: bool):
    # ----------------- Set up experiment -----------------
    env = simpy.Environment()
    city = City(env)
    mobility_manager = MobilityManager(city)
    env.process(mobility_manager.run(env))

    # ----------------- Initialize meters -----------------
    if count_taxis:
        # Measures the amount of taxis on the map
        taxi_counter = TaxiCounter(env, city.infrastructure)
    if measure_infrastructure:
        # Measures the power usage of cloud and fog nodes as well as WAN and WiFi links
        pm_cloud = PowerMeter(entities=city.infrastructure.nodes(type_filter=Cloud), name="cloud", measurement_interval=POWER_MEASUREMENT_INTERVAL)
        pm_fog = PowerMeter(entities=city.infrastructure.nodes(type_filter=FogNode), name="fog", measurement_interval=POWER_MEASUREMENT_INTERVAL)
        pm_wan_up = PowerMeter(entities=city.infrastructure.links(type_filter=LinkWanUp), name="wan_up", measurement_interval=POWER_MEASUREMENT_INTERVAL)
        pm_wan_down = PowerMeter(entities=city.infrastructure.links(type_filter=LinkWanDown), name="wan_down", measurement_interval=POWER_MEASUREMENT_INTERVAL)
        pm_wifi = PowerMeter(entities=lambda: city.infrastructure.links(type_filter=(LinkWifiBetweenTrafficLights, LinkWifiTaxiToTrafficLight)), name="wifi", measurement_interval=POWER_MEASUREMENT_INTERVAL)

        env.process(pm_cloud.run(env))
        env.process(pm_fog.run(env))
        env.process(pm_wan_up.run(env))
        env.process(pm_wan_down.run(env))
        env.process(pm_wifi.run(env))
    if measure_applications:
        # Measures the power usage of the V2I and CCTV applications
        pm_v2i = PowerMeter(entities=lambda: [taxi.application for taxi in city.infrastructure.nodes(type_filter=Taxi)], name="v2i", measurement_interval=POWER_MEASUREMENT_INTERVAL)
        pm_cctv = PowerMeter(entities=lambda: [tl.application for tl in city.infrastructure.nodes(type_filter=TrafficLight)], name="cctv", measurement_interval=POWER_MEASUREMENT_INTERVAL)
        env.process(pm_v2i.run(env))
        env.process(pm_cctv.run(env))

    # ------------------ Run experiment -------------------
    for until in tqdm(range(1, SIMULATION_TIME)):
        env.run(until=until)

    # ------------------ Write results --------------------
    result_dir = f"results/fog_{FOG_DCS}"
    if FOG_IDLE_SHUTDOWN:
        result_dir += "_shutdown"
    makedirs(result_dir, exist_ok=True)
    if count_taxis:
        csv_content = "time,taxis\n"
        for i, taxis in enumerate(taxi_counter.measurements):
            csv_content += f"{i},{taxis}\n"
        with open(f"{result_dir}/taxis.csv", 'w') as csvfile:
            csvfile.write(csv_content)
    if measure_infrastructure:
        csv_content = "time,cloud static,cloud dynamic,fog static,fog dynamic,wifi static,wifi dynamic,wanUp static," \
                      "wanUp dynamic,wanDown static,wanDown dynamic\n"
        for i, (cloud, fog, wifi, wan_up, wan_down) in enumerate(zip(pm_cloud.measurements, pm_fog.measurements, pm_wifi.measurements, pm_wan_up.measurements, pm_wan_down.measurements)):
            csv_content += f"{i},{cloud.static},{cloud.dynamic},{fog.static},{fog.dynamic},{wifi.static},{wifi.dynamic},{wan_up.static},{wan_up.dynamic},{wan_down.static},{wan_down.dynamic}\n"
        with open(f"{result_dir}/infrastructure.csv", 'w') as csvfile:
            csvfile.write(csv_content)
    if measure_applications:
        csv_content = "time,v2i static,v2i dynamic,cctv static,cctv dynamic\n"
        for i, (v2i, cctv) in enumerate(zip(pm_v2i.measurements, pm_cctv.measurements)):
            csv_content += f"{i},{v2i.static},{v2i.dynamic},{cctv.static},{cctv.dynamic}\n"
        with open(f"{result_dir}/applications.csv", 'w') as csvfile:
            csvfile.write(csv_content)


class TaxiCounter:
    def __init__(self, env: simpy.Environment, infrastructure: Infrastructure):
        self.env = env
        self.measurements = []
        self.process = env.process(self._run(infrastructure))

    def _run(self, infrastructure: Infrastructure):
        yield self.env.timeout(0.01)
        while True:
            self.measurements.append(len(infrastructure.nodes(type_filter=Taxi)))
            yield self.env.timeout(1)


if __name__ == '__main__':
    main(count_taxis=True, measure_infrastructure=True, measure_applications=False)
