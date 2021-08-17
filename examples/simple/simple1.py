import logging
import simpy

from leaf.application import SourceTask
from leaf.infrastructure import Node
from leaf.power import PowerModelNode

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s\t%(message)s')


def main():
    sensor = Node("sensor", mips=1000, power_model=PowerModelNode(max_power=1.8, static_power=0.2))
    task = SourceTask(mips=100, bound_node=sensor)
    env = simpy.Environment()

    env.process(place_task(env, sensor, task))
    env.process(remove_task(env, sensor, task))
    env.run(until=10)


def place_task(env, sensor, task):
    yield env.timeout(3)
    sensor.add_task(task)
    print(f'task has been added at {env.now}')


def remove_task(env, sensor, task):
    yield env.timeout(5)
    sensor.remove_task(task)
    print(f'task has been added at {env.now}')


if __name__ == '__main__':
    main()
