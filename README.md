# LEAF [![PyPI version](https://img.shields.io/pypi/v/leafsim.svg?color=52c72b)](https://pypi.org/project/leafsim/) [![Supported versions](https://img.shields.io/pypi/pyversions/leafsim.svg)](https://pypi.org/project/leafsim/) [![License](https://img.shields.io/pypi/l/leafsim.svg)](https://pypi.org/project/leafsim/)

LEAF is a simulator for **L**arge **E**nergy-**A**ware **F**og computing environments.
It enables then modeling of complex application graphs in distributed, heterogeneous, and resource-constrained infrastructures.
A special emphasis was put on the modeling of energy consumption (and soon carbon emissions).

Please visit the official [documentation](https://leaf.readthedocs.io) for more information and examples on this project.


<p align="center">
  <img src="/docs/_static/infrastructure.png">
</p>

This Python implementation was ported from the [original Java protoype](https://www.github.com/birnbaum/leaf).
All future development will take place in this repository.


## Installation

You can use LEAF either by directly cloning this repository or installing the latest release via [pip](https://pip.pypa.io/en/stable/quickstart/):

```
$ pip install leafsim
```

## What can I do with it?

LEAF enables a high-level modeling of cloud, fog and edge computing environments.
It builds on top of [networkx](https://networkx.org/), a library for creating and manipulating complex networks,
and [SimPy](https://simpy.readthedocs.io/en/latest/), a process-based discrete-event simulation framework.

Besides allowing research on scheduling and placement algorithms on resource-constrained environments,
LEAF puts a special focus on:

- **Dynamic networks**: Simulate mobile nodes which can join or leave the network during the simulation.
- **Power consumption modeling**: Model the power usage of individual compute nodes, network traffic and applications.
- **Energy-aware algorithms**: Implement dynamically adapting task placement strategies, routing policies, and other energy-saving mechanisms.
- **Scalability**: Model the execution of thousands of compute nodes and applications in magnitudes faster than real time.

Please visit the official [documentation](https://leaf.readthedocs.io) for more information and examples on this project.


## Publications

The paper behind LEAF is accepted for publication:
- Philipp Wiesner and Lauritz Thamsen. "[LEAF: Simulating Large Energy-Aware Fog Computing Environments](https://arxiv.org/abs/2103.01170)" To appear in the Proceedings of the *5th IEEE International Conference on Fog and Edge Computing (ICFEC)*. IEEE, 2021.
