from typing import List

import simpy

from leaf.application import Application, SourceTask, ProcessingTask, SinkTask
from examples.smart_city_traffic.settings import *
from leaf.infrastructure import Link, Node
from leaf.power import PowerModelLink, PowerModelNode, PowerModelNodeShared, PowerMeasurement

"""Counter for incrementally naming nodes"""
_fog_nodes_created = 0
_traffic_lights_created = 0
_taxis_created = 0


class Cloud(Node):
    def __init__(self):
        super().__init__("cloud", mips=CLOUD_MIPS, power_model=PowerModelNodeShared(CLOUD_WATT_PER_MIPS))


class FogNode(Node):
    def __init__(self, location: "Location"):
        # TODO Shutdown!
        global _fog_nodes_created
        super().__init__(f"fog_{_fog_nodes_created}", mips=FOG_MIPS,
                         power_model=PowerModelNode(max_power=FOG_MAX_POWER, static_power=FOG_STATIC_POWER))
        _fog_nodes_created += 1
        self.location = location
        self.shutdown = FOG_IDLE_SHUTDOWN

    def measure_power(self) -> PowerMeasurement:
        if self.shutdown:
            return PowerMeasurement(0, 0)
        else:
            return super().measure_power()

    def add_task(self, task: "Task"):
        if self.shutdown:
            self.shutdown = False
        super().add_task(task)

    def remove_task(self, task: "Task"):
        super().remove_task(task)
        if FOG_IDLE_SHUTDOWN and self.used_mips == 0:
            self.shutdown = True





class TrafficLight(Node):
    def __init__(self, location: "Location", application_sink: Node):
        global _traffic_lights_created
        super().__init__(f"traffic_light_{_traffic_lights_created}", mips=0, power_model=PowerModelNode(0, 0))
        _traffic_lights_created += 1
        self.location = location
        self.application = self._create_cctv_application(application_sink)

    def _create_cctv_application(self, application_sink: Node):
        application = Application()
        source_task = SourceTask(mips=0, bound_node=self)
        application.add_task(source_task)
        processing_task = ProcessingTask(mips=CCTV_PROCESSOR_MIPS)
        application.add_task(processing_task, incoming_data_flows=[(source_task, CCTV_SOURCE_TO_PROCESSOR_BIT_RATE)])
        sink_task = SinkTask(mips=0, bound_node=application_sink)
        application.add_task(sink_task, incoming_data_flows=[(processing_task, CCTV_PROCESSOR_TO_SINK_BIT_RATE)])
        return application


class Taxi(Node):
    def __init__(self, env: simpy.Environment, mobility_model: "TaxiMobilityModel", application_sinks: List[Node]):
        global _taxis_created
        super().__init__(f"taxi_{_taxis_created}", mips=0, power_model=PowerModelNode(0, 0))
        _taxis_created += 1
        self.env = env
        self.application = self._create_v2i_application(application_sinks)
        self.mobility_model = mobility_model

    @property
    def location(self) -> "Location":
        return self.mobility_model.location(self.env.now)

    def _create_v2i_application(self, application_sinks: List[Node]) -> Application:
        application = Application()
        source_task = SourceTask(mips=0, bound_node=self)
        application.add_task(source_task)
        processing_task = ProcessingTask(mips=V2I_PROCESSOR_MIPS)
        application.add_task(processing_task, incoming_data_flows=[(source_task, V2I_SOURCE_TO_PROCESSOR_BIT_RATE)])
        for application_sink in application_sinks:
            sink_task = SinkTask(mips=0, bound_node=application_sink)
            application.add_task(sink_task, incoming_data_flows=[(processing_task, V2I_PROCESSOR_TO_SINK_BIT_RATE)])
        return application


class LinkEthernet(Link):
    def __init__(self, src: Node, dst: Node):
        super().__init__(src, dst,
                         bandwidth=ETHERNET_BANDWIDTH,
                         latency=ETHERNET_LATENCY,
                         power_model=PowerModelLink(ETHERNET_WATT_PER_BIT))


class LinkWanUp(Link):
    def __init__(self, src: Node, dst: Node):
        super().__init__(src, dst,
                         bandwidth=WAN_BANDWIDTH,
                         latency=WAN_LATENCY,
                         power_model=PowerModelLink(WAN_WATT_PER_BIT_UP))


class LinkWanDown(Link):
    def __init__(self, src: Node, dst: Node):
        super().__init__(src, dst,
                         bandwidth=WAN_BANDWIDTH,
                         latency=WAN_LATENCY,
                         power_model=PowerModelLink(WAN_WATT_PER_BIT_DOWN))


class LinkWifiBetweenTrafficLights(Link):
    def __init__(self, src: Node, dst: Node):
        super().__init__(src, dst,
                         bandwidth=WIFI_BANDWIDTH,
                         latency=WIFI_LATENCY,
                         power_model=PowerModelLink(WIFI_TL_TO_TL_WATT_PER_BIT))


class LinkWifiTaxiToTrafficLight(Link):
    def __init__(self, src: Node, dst: Node):
        super().__init__(src, dst,
                         bandwidth=WIFI_BANDWIDTH,
                         latency=WIFI_LATENCY,
                         power_model=PowerModelLink(WIFI_TAXI_TO_TL_WATT_PER_BIT))
