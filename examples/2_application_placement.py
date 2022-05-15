import logging
import random
import simpy

from leaf.application import Application, SourceTask, ProcessingTask, SinkTask
from leaf.infrastructure import Node, Link, Infrastructure
from leaf.orchestrator import Orchestrator
from leaf.power import PowerModelNode, PowerModelLink, PowerMeter

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
        INFO	- SourceTask(id=0, cu=0.1) on Node('sensor', cu=0/1).
        INFO	- ProcessingTask(id=1, cu=5) on Node('fog', cu=0/400).
        INFO	- SinkTask(id=2, cu=0.5) on Node('cloud', cu=0/inf).
        INFO	- DataFlow(bit_rate=1000) on [Link('sensor' -> 'fog', bandwidth=0/30000000.0, latency=10)].
        INFO	- DataFlow(bit_rate=200) on [Link('fog' -> 'cloud', bandwidth=0/1000000000.0, latency=5)].
        DEBUG	0: cloud_and_fog_meter: PowerMeasurement(dynamic=2.38W, static=30.00W)
        DEBUG	0: infrastructure_meter: PowerMeasurement(dynamic=2.54W, static=30.20W)
        DEBUG	0.5: application_meter: PowerMeasurement(dynamic=2.54W, static=30.20W)
        DEBUG	1: cloud_and_fog_meter: PowerMeasurement(dynamic=2.38W, static=30.00W)
        DEBUG	1.5: application_meter: PowerMeasurement(dynamic=2.54W, static=30.20W)
        DEBUG	2: infrastructure_meter: PowerMeasurement(dynamic=2.54W, static=30.20W)
        DEBUG	2: cloud_and_fog_meter: PowerMeasurement(dynamic=2.38W, static=30.00W)
        DEBUG	2.5: application_meter: PowerMeasurement(dynamic=2.54W, static=30.20W)
        DEBUG	3: cloud_and_fog_meter: PowerMeasurement(dynamic=2.38W, static=30.00W)
        DEBUG	3.5: application_meter: PowerMeasurement(dynamic=2.54W, static=30.20W)
        DEBUG	4: infrastructure_meter: PowerMeasurement(dynamic=2.54W, static=30.20W)
        DEBUG	4: cloud_and_fog_meter: PowerMeasurement(dynamic=2.38W, static=30.00W)
        DEBUG	4.5: application_meter: PowerMeasurement(dynamic=2.54W, static=30.20W)
    """
    infrastructure = create_infrastructure()
    application = create_application(source_node=infrastructure.node("sensor"), sink_node=infrastructure.node("cloud"))
    orchestrator = SimpleOrchestrator(infrastructure)
    orchestrator.place(application)

    application_pm = PowerMeter(application, name="application_meter")
    cloud_and_fog_pm = PowerMeter([infrastructure.node("cloud"), infrastructure.node("fog")], name="cloud_and_fog_meter")
    infrastructure_pm = PowerMeter(infrastructure, name="infrastructure_meter", measurement_interval=2)

    env = simpy.Environment()
    env.process(application_pm.run(env, delay=0.5))
    env.process(cloud_and_fog_pm.run(env))
    env.process(infrastructure_pm.run(env))
    env.run(until=5)


def create_infrastructure():
    """Create the scenario's infrastructure graph.

    It consists of three nodes:
    - A sensor with a computational capacity of one compute unit (CU).
        It has a maximum power usage of 1.8 Watt and a power usage of 0.2 Watt when being idle.
    - A fog node which can compute up to 400 CU; 200 Watt max and 30 Watt static power usage
    - A node representing a cloud data center with unlimited processing power that consumes 0.5 W/CU

    And two network links that connect the nodes:
    - A WiFi connection between the sensor and fog node that consumes 300 J/bit
    - A wide are network (WAN) connection between the fog node and cloud that consumes 6000 J/bit
    """
    infrastructure = Infrastructure()
    sensor = Node("sensor", cu=1, power_model=PowerModelNode(max_power=1.8, static_power=0.2))
    fog_node = Node("fog", cu=400, power_model=PowerModelNode(max_power=200, static_power=30))
    cloud = Node("cloud", power_model=PowerModelNode(power_per_cu=0.5))
    wifi_link_up = Link(sensor, fog_node, latency=10, bandwidth=30e6, power_model=PowerModelLink(300e-9))
    wan_link_up = Link(fog_node, cloud, latency=5, bandwidth=1e9, power_model=PowerModelLink(6000e-9))

    infrastructure.add_link(wifi_link_up)
    infrastructure.add_link(wan_link_up)
    return infrastructure


def create_application(source_node: Node, sink_node: Node):
    """Create the application running in the scenario.

    It consists of three tasks and two data flows between these tasks:
    - A source task that is bound to the sensor node and requires 0.1 CU (for measuring data)
    - A processing task that receives 1000 bit/s from the source task, requires 5 CU (for aggregating the data)
        and returns 200 bit/s to the sink task
    - A sink task that is bound to the cloud node and requires 0.5 CU (for storing the data)
    """
    application = Application()

    source_task = SourceTask(cu=0.1, bound_node=source_node)
    processing_task = ProcessingTask(cu=5)
    sink_task = SinkTask(cu=0.5, bound_node=sink_node)

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
