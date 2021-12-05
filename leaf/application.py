from abc import ABC
from typing import List, Tuple, Type, Optional, TypeVar, Union

import networkx as nx

from leaf.infrastructure import Node, Link
from leaf.power import PowerAware, PowerMeasurement


class Task(PowerAware):
    def __init__(self, cu: float):
        """Task that can be placed on a :class:`Node`.

        Tasks _can_ be connected via :class:`Link`s to build an :class:`Application`.

        Args:
            cu: Amount of compute units (CU) required to execute the task. CUs a imaginary unit for computational
                power to express differences between hardware platforms.

            Million instructions per second required to execute the task.
        """
        self.id: Optional[int] = None
        self.cu = cu
        self.node: Optional[Node] = None

    def __repr__(self):
        return f"{self.__class__.__name__}(id={self.id}, cu={self.cu})"

    def allocate(self, node: Node):
        """Place the task on a certain node and allocate resources."""
        if self.node is not None:
            raise ValueError(f"Cannot place {self} on {node}: It was already placed on {self.node}.")
        self.node = node
        self.node._add_task(self)

    def deallocate(self):
        """Detache the task from the node it is currently placed on and deallocate resources."""
        if self.node is None:
            raise ValueError(f"{self} is not placed on any node.")
        self.node._remove_task(self)
        self.node = None

    def measure_power(self) -> PowerMeasurement:
        try:
            return self.node.measure_power().multiply(self.cu / self.node.used_cu)
        except ZeroDivisionError:
            return PowerMeasurement(0, 0)


class SourceTask(Task):
    def __init__(self, cu: float = 0, bound_node: Node = None):
        """Source task of an application that is bound to a certain node, e.g. a sensor generating data.

        Source tasks never have incoming and always have outgoing data flows.

        Args:
            cu: Million instructions per second required to execute the task.
            bound_node: The node which the task is bound to. Cannot be None.
        """
        super().__init__(cu)
        if bound_node is None:
            raise ValueError("bound_node for SourceTask cannot be None")
        self.bound_node = bound_node


class ProcessingTask(Task):
    def __init__(self, cu: float = 0):
        """Processing task of an application that can be freely placed on the infrastructure.

        Processing tasks always have incoming and outgoing data flows.

        Args:
            cu: Million instructions per second required to execute the task.
        """
        super().__init__(cu)


class SinkTask(Task):
    def __init__(self, cu: float = 0, bound_node: Node = None):
        """Sink task of an application that is bound to a certain node, e.g. a cloud server for storage.

        Args:
            cu: Million instructions per second required to execute the task.
            bound_node: The node which the task is bound to. Cannot be None.
        """
        super().__init__(cu)
        if bound_node is None:
            raise ValueError("bound_node for SourceTask cannot be None")
        self.bound_node = bound_node


class DataFlow(PowerAware):
    def __init__(self, bit_rate: float):
        """Data flow between two tasks of an application.

        Args:
            bit_rate: The bit rate of the data flow in bit/s
        """
        self.bit_rate = bit_rate
        self.links: Optional[List[Link]] = None

    def __repr__(self):
        return f"{self.__class__.__name__}(bit_rate={self.bit_rate})"

    def allocate(self, links: List[Link]):
        """Place the data flow on a path of links and allocate bandwidth."""
        if self.links is not None:
            raise ValueError(f"Cannot place {self} on {links}: It was already placed on path {self.links}.")
        self.links = links
        for link in self.links:
            link._add_data_flow(self)

    def deallocate(self):
        """Remove the data flow from the infrastructure and deallocate bandwidth."""
        if self.links is None:
            raise ValueError(f"{self} is not placed on any link.")
        for link in self.links:
            link._remove_data_flow(self)
        self.links = None

    def measure_power(self) -> PowerMeasurement:
        if self.links is None:
            raise RuntimeError("Cannot measure power: DataFlow was not placed on any links.")
        return PowerMeasurement.sum(link.measure_power().multiply(self.bit_rate / link.used_bandwidth)
                                    for link in self.links)


class Application(PowerAware):
    """Application consisting of one or more tasks forming a directed acyclic graph (DAG)."""
    _TTask = TypeVar("TTask", bound=Task)  # Generics
    _TDataFlow = TypeVar("TDataFlow", bound=DataFlow)  # Generics
    _TaskTypeFilter = Union[Type[_TTask], Tuple[Type[_TTask], ...]]
    _DataFlowTypeFilter = Union[Type[_TDataFlow], Tuple[Type[_TDataFlow], ...]]

    def __init__(self):
        self.graph = nx.DiGraph()

    def __repr__(self):
        return f"{self.__class__.__name__}(tasks={len(self.tasks())})"

    def add_task(self, task: Task, incoming_data_flows: List[Tuple[Task, float]] = None):
        """Add a task to the application graph.

        Args:
            task: The task to add
            incoming_data_flows: List of tuples (`src_task`, `bit_rate`) where every `src_task` is the source of a
                :class:`DataFlow` with a certain `bit_rate` to the added `task`
        """
        task.id = len(self.tasks())
        if isinstance(task, SourceTask):
            assert not incoming_data_flows, f"Source task '{task}' cannot have incoming_data_flows"
            self.graph.add_node(task.id, data=task)
        elif isinstance(task, ProcessingTask):
            assert len(incoming_data_flows) > 0, f"Processing task '{task}' has no incoming_data_flows"
            self.graph.add_node(task.id, data=task)
            for src_task, bit_rate in incoming_data_flows:
                assert not isinstance(src_task, SinkTask), f"Sink task '{task}' cannot have outgoing data flows"
                self.graph.add_edge(src_task.id, task.id, data=DataFlow(bit_rate))
        elif isinstance(task, SinkTask):
            assert len(incoming_data_flows) > 0, f"Sink task '{task}' has no incoming_data_flows"
            self.graph.add_node(task.id, data=task)
            for src_task, bit_rate in incoming_data_flows:
                assert not isinstance(src_task, SinkTask), f"Sink task '{task}' cannot have outgoing data flows"
                self.graph.add_edge(src_task.id, task.id, data=DataFlow(bit_rate))
            assert nx.is_directed_acyclic_graph(self.graph), f"Application '{self}' is no DAG"
        else:
            raise ValueError(f"Unknown task type '{type(task)}'")

    def tasks(self, type_filter: Optional[_TaskTypeFilter] = None) -> List[_TTask]:
        """Return all tasks in the application, optionally filtered by class."""
        task_iter = (task for _, task in self.graph.nodes.data("data"))
        if type_filter:
            task_iter = (task for task in task_iter if isinstance(task, type_filter))
        return list(task_iter)

    def data_flows(self, type_filter: Optional[_DataFlowTypeFilter] = None) -> List[_TDataFlow]:
        """Return all data flows in the application, optionally filtered by class."""
        df_iter = [v for _, _, v in self.graph.edges.data("data")]
        if type_filter:
            df_iter = (df for df in df_iter if isinstance(df, type_filter))
        return list(df_iter)

    def deallocate(self):
        """Detach/Unmap/Release an application from the infrastructure it is currently placed on."""
        for task in self.tasks():
            task.deallocate()
        for data_flow in self.data_flows():
            data_flow.deallocate()

    def measure_power(self) -> PowerMeasurement:
        measurements = [t.measure_power() for t in self.tasks()] + [df.measure_power() for df in self.data_flows()]
        return PowerMeasurement.sum(measurements)
