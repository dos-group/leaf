# LEAF [![PyPI version](https://img.shields.io/pypi/v/leafsim.svg?color=52c72b)](https://pypi.org/project/leafsim/) [![Supported versions](https://img.shields.io/pypi/pyversions/leafsim.svg)](https://pypi.org/project/leafsim/) [![License](https://img.shields.io/pypi/l/leafsim.svg)](https://pypi.org/project/leafsim/)

<img align="right" width="300" height="230" src="https://leaf.readthedocs.io/en/latest/_static/logo.svg">

LEAF is a simulator for analytical modeling of energy consumption in cloud, fog, or edge computing environments.
It enables the modeling of simple tasks running on a single node as well as complex application graphs in distributed, heterogeneous, and resource-constrained infrastructures.
LEAF is based on [SimPy](https://simpy.readthedocs.io/en/latest/) for discrete-event simulation and [NetworkX](https://networkx.org/) for modeling infrastructure or application graphs.

Please have a look at out [examples](https://github.com/dos-group/leaf/tree/main/examples) and visit the official [documentation](https://leaf.readthedocs.io) for more information on this project.

This Python implementation was ported from the [original Java protoype](https://www.github.com/birnbaum/leaf).
All future development will take place in this repository.


## ⚙️ Installation

You can install the [latest release](https://pypi.org/project/leafsim/) of LEAF via [pip](https://pip.pypa.io/en/stable/quickstart/):

```
$ pip install leafsim
```

Alternatively, you can also clone the repository (including all examples) and set up your environment via:

```
$ pip install -e .
```


## 🚀 Getting started

LEAF uses [SimPy](https://simpy.readthedocs.io/en/latest/) for process-based discrete-event simulation and adheres to their API.
To understand how to develop scenarios in LEAF, it makes sense to familiarize yourself with SimPy first.

```python
import simpy
from leaf.application import Task
from leaf.infrastructure import Node
from leaf.power import PowerModelNode, PowerMeter

# Processes modify the model during the simulation
def place_task_after_2_seconds(env, node, task):
    """Waits for 2 seconds and places a task on a node."""
    yield env.timeout(2)
    task.allocate(node)

node = Node("node1", cu=100, power_model=PowerModelNode(max_power=30, static_power=10))
task = Task(cu=100)
power_meter = PowerMeter(node, callback=lambda m: print(f"{env.now}: Node consumes {int(m)}W"))

env = simpy.Environment()  
# register our task placement process
env.process(place_task_after_2_seconds(env, node, task))
# register power metering process (provided by LEAF)
env.process(power_meter.run(env))
env.run(until=5)
```

Which will result in the output:

```
0: Node consumes 10W
1: Node consumes 10W
2: Node consumes 30W
3: Node consumes 30W
4: Node consumes 30W
```

For other examples, please refer to the [examples folder](https://github.com/dos-group/leaf/blob/main/examples).


## 🍃 What can I do with LEAF?

LEAF enables high-level simulation of computing scenarios, where experiments are easy to create and easy to analyze.
Besides allowing research on scheduling and placement algorithms on resource-constrained environments, LEAF puts a special focus on:

- **Dynamic networks**: Simulate mobile nodes which can join or leave the network during the simulation.
- **Power consumption modeling**: Model the power usage of individual compute nodes, network traffic, and applications.
- **Energy-aware algorithms**: Implement dynamically adapting task placement strategies, routing policies, and other energy-saving mechanisms.
- **Scalability**: Model the execution of thousands of compute nodes and applications in magnitudes faster than real time.

Please visit the official [documentation](https://leaf.readthedocs.io) for more information and examples on this project.

<p align="center">
  <img src="/docs/_static/infrastructure.png">
</p>


## 📖 Publications

If you use LEAF in your research, please cite our paper:

Philipp Wiesner and Lauritz Thamsen. "[LEAF: Simulating Large Energy-Aware Fog Computing Environments](https://ieeexplore.ieee.org/document/9458907)" In the Proceedings of the 2021 *5th IEEE International Conference on Fog and Edge Computing (ICFEC)*. IEEE. 2021 [[arXiv preprint]](https://arxiv.org/pdf/2103.01170.pdf) [[video]](https://youtu.be/G70hudAhd5M)

Bibtex:
```
@inproceedings{WiesnerThamsen_LEAF_2021,
  author={Wiesner, Philipp and Thamsen, Lauritz},
  booktitle={2021 IEEE 5th International Conference on Fog and Edge Computing (ICFEC)}, 
  title={{LEAF}: Simulating Large Energy-Aware Fog Computing Environments}, 
  year={2021},
  pages={29-36},
  doi={10.1109/ICFEC51620.2021.00012}
}
```

## 💚 Projects using LEAF

- Philipp Wiesner, Ilja Behnke, Dominik Scheinert,  Kordian Gontarska, and Lauritz Thamsen. "[Let's Wait Awhile: How Temporal Workload Shifting Can Reduce Carbon Emissions in the Cloud](https://arxiv.org/pdf/2110.13234.pdf)" In the Proceedings of the *22nd International Middleware Conference*. ACM. 2021 [[code](https://github.com/dos-group/lets-wait-awhile)]
- Liam Brugger. "An Evaluation of Carbon-Aware Load Shifting Techniques" *Bachelor Thesis*. 2021 [[code](https://gitlab.com/lbrugger72/Bachelor)]
