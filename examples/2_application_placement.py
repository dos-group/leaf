import logging
import random
import simpy

from leaf.application import Application, SourceTask, ProcessingTask, SinkTask
from leaf.infrastructure import Node, Link, Infrastructure
from leaf.orchestrator import Orchestrator
from leaf.power import PowerModelNode, PowerModelNodeShared, PowerModelLink, power_meter

RANDOM_SEED = 1

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s\t%(message)s')


def main():
    """Simple example that places an application in the beginning an performs power measurements on different entities.

    Read the explanations of :func:`create_infrastructure`, :func:`create_application` and :class:`SimpleOrchestrator`
    for details on the scenario setup.

    The power meters can be configured to periodically measure the power consumption of one or more PowerAware entities
    such as applications, tasks, data flows, compute nodes, network links or the entire infrastructure.

    The scenario is running for 5 time steps.

    Log Output:
        INFO	Placing Application(tasks=3):
        INFO	- SourceTask(id=0, mips=100) on Node('sensor', mips=0/1000).
        INFO	- ProcessingTask(id=1, mips=5000) on Node('fog', mips=0/400000).
        INFO	- SinkTask(id=2, mips=100) on Node('cloud', mips=0/inf).
        INFO	- DataFlow(bit_rate=1000) on [Link('sensor' -> 'fog', bandwidth=0/30000000.0, latency=10)].
        INFO	- DataFlow(bit_rate=200) on [Link('fog' -> 'cloud', bandwidth=0/1000000000.0, latency=5)].
        DEBUG	0: cloud_and_fog_meter: PowerMeasurement(dynamic=70002.125W, static=30W)
        DEBUG	0: infrastructure_meter: PowerMeasurement(dynamic=1570002.2850000001W, static=30.2W)
        DEBUG	0.5: application_meter: PowerMeasurement(dynamic=1570002.2850000001W, static=30.2W)
        DEBUG	1: cloud_and_fog_meter: PowerMeasurement(dynamic=70002.125W, static=30W)
        DEBUG	1.5: application_meter: PowerMeasurement(dynamic=1570002.2850000001W, static=30.2W)
        DEBUG	2: infrastructure_meter: PowerMeasurement(dynamic=1570002.2850000001W, static=30.2W)
        DEBUG	2: cloud_and_fog_meter: PowerMeasurement(dynamic=70002.125W, static=30W)
        DEBUG	2.5: application_meter: PowerMeasurement(dynamic=1570002.2850000001W, static=30.2W)
        DEBUG	3: cloud_and_fog_meter: PowerMeasurement(dynamic=70002.125W, static=30W)
        DEBUG	3.5: application_meter: PowerMeasurement(dynamic=1570002.2850000001W, static=30.2W)
        DEBUG	4: infrastructure_meter: PowerMeasurement(dynamic=1570002.2850000001W, static=30.2W)
        DEBUG	4: cloud_and_fog_meter: PowerMeasurement(dynamic=70002.125W, static=30W)
        DEBUG	4.5: application_meter: PowerMeasurement(dynamic=1570002.2850000001W, static=30.2W)
    """
    infrastructure = create_infrastructure()
    application = create_application(source_node=infrastructure.node("sensor"), sink_node=infrastructure.node("cloud"))
    orchestrator = SimpleOrchestrator(infrastructure)
    orchestrator.place(application)

    application_measurements = []
    cloud_and_fog_measurements = []
    infrastructure_measurements = []

    env = simpy.Environment()
    env.process(power_meter(env, application, name="application_meter", delay=0.5,
                            callback=lambda m: application_measurements.append(m)))
    env.process(power_meter(env, [infrastructure.node("cloud"), infrastructure.node("fog")], name="cloud_and_fog_meter",
                            callback=lambda m: cloud_and_fog_measurements.append(m)))
    env.process(power_meter(env, infrastructure, name="infrastructure_meter", measurement_interval=2,
                            callback=lambda m: infrastructure_measurements.append(m)))
    env.run(until=5)


def create_infrastructure():
    """Create the scenario's infrastructure graph.

    It consists of three nodes:
    - A sensor that can compute up to 1000 million instructions per second (MIPS).
        It has a maximum power usage of 1.8 Watt and a power usage of 0.2 Watt when being idle.
    - A fog node which can compute up to 400000 MIPS; 200 Watt max and 30 Watt static power usage
    - A node representing a cloud data center with unlimited processing power that consumes 700 W/MIPS

    And two network links that connect the nodes:
    - A WiFi connection between the sensor and fog node that consumes 300 J/bit
    - A wide are network (WAN) connection between the fog node and cloud that consumes 6000 J/bit
    """
    infrastructure = Infrastructure()
    sensor = Node("sensor", mips=1000, power_model=PowerModelNode(max_power=1.8, static_power=0.2))
    fog_node = Node("fog", mips=400000, power_model=PowerModelNode(max_power=200, static_power=30))
    cloud = Node("cloud", power_model=PowerModelNodeShared(power_per_mips=700))
    wifi_link_up = Link(sensor, fog_node, latency=10, bandwidth=30e6, power_model=PowerModelLink(300))
    wan_link_up = Link(fog_node, cloud, latency=5, bandwidth=1e9, power_model=PowerModelLink(6000))

    infrastructure.add_link(wifi_link_up)
    infrastructure.add_link(wan_link_up)
    return infrastructure


def create_application(source_node: Node, sink_node: Node):
    """Create the application running in the scenario.

    It consists of three tasks and two data flows between these tasks:
    - A source task that is bound to the sensor node and requires 100 MIPS (for measuring data)
    - A processing task that receives 1000 bit/s from the source task, requires 5000 MIPS (for aggregating the data)
        and returns 200 bit/s to the sink task
    - A sink task that is bound to the cloud node and requires 500 MIPS (for storing the data)
    """
    application = Application()

    source_task = SourceTask(mips=100, bound_node=source_node)
    processing_task = ProcessingTask(mips=5000)
    sink_task = SinkTask(mips=100, bound_node=sink_node)

    application.add_task(source_task)
    application.add_task(processing_task, incoming_data_flows=[(source_task, 1000)])
    application.add_task(sink_task, incoming_data_flows=[(processing_task, 200)])

    return application


class SimpleOrchestrator(Orchestrator):
    """Very simple orchestrator that places the processing task on the fog node.

    You can try out other placements here and see how the placement may consume more energy ("cloud")
    or fail because there are not enough resources available ("sensor").
    """

    def _processing_task_placement(self, processing_task: ProcessingTask, application: Application) -> Node:
        return self.infrastructure.node("fog")


if __name__ == '__main__':
    random.seed(RANDOM_SEED)
    main()
