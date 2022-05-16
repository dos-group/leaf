import logging
import simpy

from leaf.application import Task
from leaf.infrastructure import Node
from leaf.power import PowerModelNode, PowerMeasurement, PowerMeter

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s\t%(message)s')


def main():
    """Simple example that adds and removes a task from a single node

    Log Output:
        DEBUG	0: PowerMeter1: PowerMeasurement(dynamic=0.00W, static=10.00W)
        DEBUG	1: PowerMeter1: PowerMeasurement(dynamic=0.00W, static=10.00W)
        DEBUG	2: PowerMeter1: PowerMeasurement(dynamic=0.00W, static=10.00W)
        INFO	task has been added at 3
        DEBUG	3: PowerMeter1: PowerMeasurement(dynamic=20.00W, static=10.00W)
        DEBUG	4: PowerMeter1: PowerMeasurement(dynamic=20.00W, static=10.00W)
        DEBUG	5: PowerMeter1: PowerMeasurement(dynamic=20.00W, static=10.00W)
        DEBUG	6: PowerMeter1: PowerMeasurement(dynamic=20.00W, static=10.00W)
        DEBUG	7: PowerMeter1: PowerMeasurement(dynamic=20.00W, static=10.00W)
        INFO	task has been removed at 8
        DEBUG	8: PowerMeter1: PowerMeasurement(dynamic=0.00W, static=10.00W)
        DEBUG	9: PowerMeter1: PowerMeasurement(dynamic=0.00W, static=10.00W)
        INFO	Total power usage: 200.0 Ws
    """
    # Initializing infrastructure and workload
    node = Node("node1", cu=100, power_model=PowerModelNode(max_power=30, static_power=10))
    task = Task(cu=100)

    power_meter = PowerMeter(node, name="PowerMeter1")

    env = simpy.Environment()  # creating SimPy simulation environment
    env.process(placement(env, node, task))  # registering workload placement process
    env.process(power_meter.run(env))  # registering power metering process

    env.run(until=10)  # run simulation for 10 seconds

    logger.info(f"Total power usage: {float(PowerMeasurement.sum(power_meter.measurements))} Ws")


def placement(env, node, task):
    """Places the task after 3 seconds and removes it after 8 seconds."""
    yield env.timeout(3)
    task.allocate(node)
    logger.info(f'task has been added at {env.now}')
    yield env.timeout(5)
    task.deallocate()
    logger.info(f'task has been removed at {env.now}')


if __name__ == '__main__':
    main()
