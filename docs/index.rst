Welcome to LEAF
===============

What is LEAF?
-------------

LEAF is a simulator for **L**\ arge **E**\ nergy-**A**\ ware **F**\ og computing environments.
It enables modeling of distributed, heterogeneous, and resource-constrained infrastructures that execute complex application graphs.

A special emphasis was put on the modeling of energy consumption (and soon carbon emissions).

.. image:: ../_static/infrastructure.png
    :alt: Alternative text

What can I do with it?
----------------------

LEAF enables a high-level modeling of cloud, fog and edge computing environments.
It builds on top of `networkx <https://networkx.org/>`_, a library for creating and manipulating complex networks,
and `SimPy <https://simpy.readthedocs.io/en/latest/>`_, a process-based discrete-event simulation framework.

Besides allowing research on scheduling and placement algorithms on resource-constrained environments,
LEAF puts a special focus on:

    - **Dynamic networks**: Simulate mobile nodes which can join or leave the network during the simulation.
    - **Power consumption modeling**: Model the power usage of individual compute nodes, network traffic and applications.
    - **Energy-aware algorithms**: Implement dynamically adapting task placement strategies, routing policies, and other energy-saving mechanisms.
    - **Scalability**: Model the execution of thousands of compute nodes and applications in magnitudes faster than real time.


How does it work?
-----------------

Unlike other discrete event simulators for computer networks, LEAF models infrastructure and applications on a high
level based on graphs. Infrastructure is represented as a directed, weighted multigraph where vertices are compute nodes
such as data centers or sensors and edges are network links. Applications are represented as
`directed acyclic graphs (DAG) <https://en.wikipedia.org/wiki/Directed_acyclic_graph>`_, where vertices are tasks and edges are data flows between those tasks.

This allows for easy to configure and easy to analyze experiments that are fast to execute.

.. image:: ../_static/graph-model.png
    :width: 450px
    :align: center

The above example shows:

- an infrastructure graph with its resource constraints and power usage characteristics (black)
- a placed application with its resource requirements (orange)
- and its resulting power usage on the infrastructure components (green)


Bringing it to life
...................

Now, in order to enable dynamic components such as mobile nodes, we can **change** the configuration, quantity and placement of these graphs through events:

.. image:: ../_static/des.png
    :width: 400px
    :align: center

Of course, components can **read** from the graphs via events, too. Examples for this are algorithm that change their behaviour based on certain system states or power meters that periodically measure the power usage of a component.

For a more detailed explanation, read `our paper <[under review]>`_ :)


That's very theoretical...
--------------------------

To ease your start with LEAF, we provide some examples:

- The `simple <https://github.com/dos-group/leaf/blob/main/leaf/examples/simple/main.py>`_ scenario implements a data center,
  a fog node and a sensor that execute a simple application.
- The `smart city traffic <https://github.com/dos-group/leaf/blob/main/leaf/examples/simple/main.py>`_ scenario is a lot more complicated.
  It simulates the traffic of taxis and the execution of two different types of applications in a connected city center.
  You can read up on the setup and results of this scenario in `this paper <[under review]>`_.


Publications
------------

The paper behind LEAF is currently under review:

- Philipp Wiesner and Lauritz Thamsen. "LEAF: Simulating Large Energy-Aware Fog Computing Environments" [under review]


.. toctree::
    :hidden:

    self
    changelog
    reference/modules
