import logging
import simpy

from leaf.application import SourceTask
from leaf.infrastructure import Node
from leaf.power import PowerModelNode, PowerMeter, PowerMeasurement

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s\t%(message)s')


def main():
    """Simple example that adds and removes a task from a single node

    Log Output:
        DEBUG	0: PowerMeter: PowerMeasurement(dynamic=0.0W, static=1W)
        DEBUG	1: PowerMeter: PowerMeasurement(dynamic=0.0W, static=1W)
        DEBUG	2: PowerMeter: PowerMeasurement(dynamic=0.0W, static=1W)
        INFO	task has been added at 3
        DEBUG	3: PowerMeter: PowerMeasurement(dynamic=2.0W, static=1W)
        DEBUG	4: PowerMeter: PowerMeasurement(dynamic=2.0W, static=1W)
        DEBUG	5: PowerMeter: PowerMeasurement(dynamic=2.0W, static=1W)
        DEBUG	6: PowerMeter: PowerMeasurement(dynamic=2.0W, static=1W)
        DEBUG	7: PowerMeter: PowerMeasurement(dynamic=2.0W, static=1W)
        INFO	task has been removed at 8
        DEBUG	8: PowerMeter: PowerMeasurement(dynamic=0.0W, static=1W)
        DEBUG	9: PowerMeter: PowerMeasurement(dynamic=0.0W, static=1W)
        INFO	Total power usage: 20.0 Ws
    """
    # Initializing infrastructure and workload
    node = Node("node1", mips=1000, power_model=PowerModelNode(max_power=3, static_power=1))
    task = SourceTask(mips=1000, bound_node=node)

    env = simpy.Environment()  # creating SimPy simulation environment
    env.process(placement(env, node, task))  # registering workload placement process
    power_meter = PowerMeter(env, node, name="PowerMeter1")  # registering power metering process

    env.run(until=10)  # run simulation for 10 seconds

    logger.info(f"Total power usage: {float(PowerMeasurement.sum(power_meter.measurements))} Ws")


def placement(env, node, task):
    """Places the task after 3 seconds and removes it after 8 seconds."""
    yield env.timeout(3)
    node.add_task(task)
    logger.info(f'task has been added at {env.now}')
    yield env.timeout(5)
    node.remove_task(task)
    logger.info(f'task has been removed at {env.now}')


if __name__ == '__main__':
    main()
