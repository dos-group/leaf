import logging

import simpy
from tqdm import tqdm

from examples.smart_city_traffic.city import City
from examples.smart_city_traffic.infrastructure import Cloud, FogNode, Taxi, LinkWanDown, LinkWanUp, \
    LinkWifiTaxiToTrafficLight, LinkWifiBetweenTrafficLights, TrafficLight
from examples.smart_city_traffic.mobility import MobilityManager
from examples.smart_city_traffic.settings import SIMULATION_TIME, FOG_DCS, POWER_MEASUREMENT_INTERVAL
from src.infrastructure import Infrastructure
from src.power import PowerMeter

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')


def main():
    env = simpy.Environment()

    city = City(env)
    mm = MobilityManager(env, city)

    taxi_counter = TaxiCounter(env, city.infrastructure)
    pm_cloud = _PowerMeter(env, entities=city.infrastructure.nodes(type_filter=Cloud), name="cloud")
    pm_fog = _PowerMeter(env, entities=city.infrastructure.nodes(type_filter=FogNode), name="fog")
    pm_wan_up = _PowerMeter(env, entities=city.infrastructure.links(type_filter=LinkWanUp), name="wan_up")
    pm_wan_down = _PowerMeter(env, entities=city.infrastructure.links(type_filter=LinkWanDown), name="wan_down")
    pm_wifi = _PowerMeter(env, entities=lambda: city.infrastructure.links(
        type_filter=(LinkWifiBetweenTrafficLights, LinkWifiTaxiToTrafficLight)), name="wifi")

    pm_v2i = _PowerMeter(env, entities=lambda: [taxi.application for taxi in city.infrastructure.nodes(type_filter=Taxi)], name="v2i")
    pm_cctv = _PowerMeter(env, entities=lambda: [tl.application for tl in city.infrastructure.nodes(type_filter=TrafficLight)], name="cctv")

    PROGRESS_UPDATE_INTERVAL = 300
    for until in tqdm(range(PROGRESS_UPDATE_INTERVAL, SIMULATION_TIME, PROGRESS_UPDATE_INTERVAL), total=SIMULATION_TIME/PROGRESS_UPDATE_INTERVAL):
        env.run(until=until)


    filename = "fog_" + FOG_DCS

    csv_content = "time,taxis\n"
    for i, taxis in enumerate(taxi_counter.measurements):
        csv_content += f"{i},{taxis}\n"
    with open(f"results/{filename}/taxis.csv", 'w') as csvfile:
        csvfile.write(csv_content)

    csv_content = "time,cloud static,cloud dynamic,fog static,fog dynamic,wifi static,wifi dynamic,wanUp static,wanUp dynamic,wanDown static,wanDown dynamic\n"
    for i, (cloud, fog, wifi, wan_up, wan_down) in enumerate(zip(pm_cloud.measurements, pm_fog.measurements, pm_wifi.measurements, pm_wan_up.measurements, pm_wan_down.measurements)):
        csv_content += f"{i},{cloud.static},{cloud.dynamic},{fog.static},{fog.dynamic},{wifi.static},{wifi.dynamic},{wan_up.static},{wan_up.dynamic},{wan_down.static},{wan_down.dynamic}\n"
    with open(f"results/{filename}//infrastructure.csv", 'w') as csvfile:
        csvfile.write(csv_content)

    csv_content = "time,v2i static,v2i dynamic,cctv static,cctv dynamic\n"
    for i, (v2i, cctv) in enumerate(zip(pm_v2i.measurements, pm_cctv.measurements)):
        csv_content += f"{i},{v2i.static},{v2i.dynamic},{cctv.static},{cctv.dynamic}\n"
    with open(f"results/{filename}//applications.csv", 'w') as csvfile:
        csvfile.write(csv_content)


class _PowerMeter(PowerMeter):
    def __init__(self, env, entities, **kwargs):
        super().__init__(env, entities, measurement_interval=POWER_MEASUREMENT_INTERVAL, **kwargs)


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
    main()
