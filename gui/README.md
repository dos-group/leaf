# Leaf Gui - 1.0.0

Install LEAF as described in the main README.

Run the GUI via:

```
$ python gui/app.py
```


# TODOs

## Simulation -> GUI

Find uniform way to generate data for visualizations
- define the Python interface that translates the simulated entities to the visualization [done]

What's the input to the visualization?
1. Live during visualization [TBD]
2. Based on CSV files after simulation (generated by the same Python interface) [done]

What's a sensible datastructure for visualizing the graph over time?
- nodes and links need to be unique [done]
- files will get huge ...


## GUI

Infrastructure graph
- place nodes based on coordinates (if available) [done]
- customize visualization (e.g. icons, dashed lines, ...) and behaviour (e.g. clickable) per node and link type
- toggle nodes by type
- toggle links by type
- show statistics on current state of graph: e.g. number of nodes per type, energy consumption per type

Node/Link selector
- select on graph directly
- button to select all nodes/link
- button to select all per type?
- button to by other criteria?

Time selector
- we want some kind of slider to go visualize the simulation at a certain time
- Q: will energy consumption plots just show the state from start till <now>?

Energy consumption graphs
- Q: visualize general overview metrics at all times?
  - infrastructure power usage chart by type
- Q: add/remove visualization sets?
  - Out of scope: Save these configs
- Q: How to we visualize multiple nodes/links?
  - Do we add up the static and dynamic power usage?
  - Do we show all entities individually?
  - Do we group by nodes/links?
  - Do we group by type?
  - Do we make this fully configurable?
    - E.g. how about a tool that lets users add (i) new lineplots and (ii) lines to plots? 
- toggle static visualization


## Things that would be cool but are probably out of scope

- Everything application placement related
- Information about selected node(s) and link(s) like latency etc.
- Metrics like CPU usage, bandwidth usage, ...
- Other high-level metrics like number of nodes; over time; ...
- Translate simulation time to other time scale

Live visualization mode
- Start/Stop the visualization
- Real-time/steady-time mode?
  - How often can/should we update the plots?