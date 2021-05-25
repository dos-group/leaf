import math

from leaf.application import Application, ProcessingTask
from examples.smart_city_traffic.infrastructure import FogNode, Cloud
from examples.smart_city_traffic.settings import FOG_UTILIZATION_THRESHOLD, FOG_DCS, FOG_IDLE_SHUTDOWN
from leaf.infrastructure import Infrastructure, Node
from leaf.orchestrator import Orchestrator


class CityOrchestrator(Orchestrator):

    def __init__(self, infrastructure: Infrastructure, utilization_threshold: float = FOG_UTILIZATION_THRESHOLD):
        super().__init__(infrastructure)
        self.utilization_threshold = utilization_threshold

    def _processing_task_placement(self, processing_task: ProcessingTask, application: Application) -> Node:
        result_node = None

        if FOG_DCS > 0:
            if FOG_IDLE_SHUTDOWN:
                highest_utilization_below_threshold = -1
                for fog_node in self.infrastructure.nodes(type_filter=FogNode):
                    if highest_utilization_below_threshold < fog_node.utilization() < self.utilization_threshold:
                        highest_utilization_below_threshold = fog_node.utilization()
                        result_node = fog_node
            else:
                lowest_utilization = math.inf
                for fog_node in self.infrastructure.nodes(type_filter=FogNode):
                    if fog_node.utilization() < lowest_utilization:
                        lowest_utilization = fog_node.utilization()
                        result_node = fog_node

        if result_node is None or result_node.utilization() > self.utilization_threshold:
            result_node = self.infrastructure.nodes(type_filter=Cloud)[0]

        return result_node
