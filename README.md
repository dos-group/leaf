# LEAF 🌱

A simulator for **L**arge **E**nergy-**A**ware **F**og computing environments.
LEAF enables energy consumption modeling of distributed, heterogeneous, and resource-constrained infrastructure that executes complex application graphs.

Features include:

- **Power modeling**: Model the power usage of individual compute nodes, network traffic and applications
- **Energy-aware algorithms**: Implement dynamically adapting task placement strategies, routing policies, and other energy-saving mechanisms
- **Dynamic networks**: Nodes can be mobile and can join or leave the network during the simulation
- **Scalability**: Simulate thousands of devices and applications in magnitudes faster than real time
- **Exporting**: Export power usage characteristics and other results as CSV files for further analysis

<p align="center">
  <img src="/images/infrastructure.png">
</p>


## Under Development

This Python implementation was ported from the [original Java protoype](https://www.github.com/birnbaum/leaf).
All future development will take place in this repository.
However, the code is currently under early development and only comes with a minimal working example you can find under `examples/simple`.

Further examples, including the smart city traffic scenario implemented in the Java prototype will follow soon.


## Publications

The paper behind LEAF is currently under review:
- Philipp Wiesner and Lauritz Thamsen. "LEAF: Simulating Large Energy-Aware Fog Computing Environments" [under review]
