import logging
import simpy

from leaf.application import SourceTask
from leaf.infrastructure import Node
from leaf.power import PowerModelNode

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s\t%(message)s')



def task(env):
    sensor = Node("sensor", mips=1000, power_model=PowerModelNode(max_power=1.8, static_power=0.2))
    source_task = SourceTask(mips=100, bound_node=sensor)
    while True:
        yield env.timeout(3)
        sensor.add_task(source_task)
        print('task has been added at %d'% env.now)
        yield env.timeout(8)
        sensor.remove_task(source_task)
        print('task has been removed at %d' %env.now)

env = simpy.Environment()
env.process(task(env))
env.run(until=12)

if __name__ == '__main__':
    task(env)
