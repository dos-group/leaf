# LEAF [![PyPI version](https://img.shields.io/pypi/v/leafsim.svg?color=52c72b)](https://pypi.org/project/leafsim/) [![Supported versions](https://img.shields.io/pypi/pyversions/leafsim.svg)](https://pypi.org/project/leafsim/) [![License](https://img.shields.io/pypi/l/leafsim.svg)](https://pypi.org/project/leafsim/)

<img align="right" width="300" height="230" src="https://leaf.readthedocs.io/en/latest/_static/logo.svg">

LEAF is a simulator for **L**arge **E**nergy-**A**ware **F**og computing environments.
It enables the modeling of simple tasks and complex application graphs in distributed, heterogeneous, and resource-constrained infrastructures.
A special emphasis was put on the modeling of energy consumption (and soon carbon emissions).

Please have a look at out [examples](https://github.com/dos-group/leaf/tree/main/examples) and visit the official [documentation](https://leaf.readthedocs.io) for more information on this project.

This Python implementation was ported from the [original Java protoype](https://www.github.com/birnbaum/leaf).
All future development will take place in this repository.


## Installation

You can use LEAF by installing the [latest release](https://pypi.org/project/leafsim/) via [pip](https://pip.pypa.io/en/stable/quickstart/):

```
$ pip install leafsim
```

For the latest changes and development we recommend cloning the repository and setting up your environment via:

```
$ pip install -e .
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

<p align="center">
  <img src="/docs/_static/infrastructure.png">
</p>


## Publications

Philipp Wiesner and Lauritz Thamsen. "[LEAF: Simulating Large Energy-Aware Fog Computing Environments](https://ieeexplore.ieee.org/document/9458907)" In the Proceedings of the 2021 *5th IEEE International Conference on Fog and Edge Computing (ICFEC)*, IEEE, 2021. [[arXiv preprint]](https://arxiv.org/pdf/2103.01170.pdf) [[video]](https://youtu.be/G70hudAhd5M)

Cite as:
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

Projects using LEAF:

- Philipp Wiesner, Ilja Behnke, Dominik Scheinert,  Kordian Gontarska, and Lauritz Thamsen. "[Let's Wait Awhile: How Temporal Workload Shifting Can Reduce Carbon Emissions in the Cloud](https://arxiv.org/pdf/2110.13234.pdf)" In the Proceedings of the *22nd International Middleware Conference*, ACM, 2021. [[code](https://github.com/dos-group/lets-wait-awhile)]

