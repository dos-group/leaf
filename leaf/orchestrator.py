import logging
from abc import ABC, abstractmethod
from functools import partial
from typing import Callable, List

import networkx as nx

from leaf.application import ProcessingTask, Application, SourceTask, SinkTask
from leaf.infrastructure import Infrastructure, Node

ProcessingTaskPlacement = Callable[[ProcessingTask, Application, Infrastructure], Node]
DataFlowPath = Callable[[nx.Graph, str, str], List[str]]

logger = logging.getLogger(__name__)


class Orchestrator(ABC):
    def __init__(self, infrastructure: Infrastructure, shortest_path: DataFlowPath = None):
        """Orchestrator which is responsible for allocating/placing application tasks on the infrastructure.

        Args:
            infrastructure: The infrastructure graph which the orchestrator operates on.
            shortest_path: A function for determining shortest/optimal paths between nodes.
                This function is called for every data flow between nodes that have been placed on the infrastructure.
                It takes the infrastructure graph, the source node, and target node and maps it to the list of nodes
                on the path. Defaults to `networkx.shortest_path`. More algorithms can be found
                `here <https://networkx.org/documentation/stable/reference/algorithms/shortest_paths.html>`_.
        """
        self.infrastructure = infrastructure
        if shortest_path is None:
            self.shortest_path = partial(nx.shortest_path, weight="latency")

    def place(self, application: Application):
        """Place an application on the infrastructure."""
        logger.info(f"Placing {application}:")
        for task in application.tasks():
            if isinstance(task, (SourceTask, SinkTask)):
                node = task.bound_node
            elif isinstance(task, ProcessingTask):
                node = self._processing_task_placement(task, application)
            else:
                raise TypeError(f"Unknown task type {task}")
            logger.info(f"- {task} on {node}.")
            task.allocate(node)

        for src_task_id, dst_task_id, data_flow in application.graph.edges.data("data"):
            src_task = application.graph.nodes[src_task_id]["data"]
            dst_task = application.graph.nodes[dst_task_id]["data"]
            shortest_path = self.shortest_path(self.infrastructure.graph, src_task.node.name, dst_task.node.name)
            links = [self.infrastructure.graph.edges[a, b, 0]["data"] for a, b in nx.utils.pairwise(shortest_path)]
            logger.info(f"- {data_flow} on {links}.")
            data_flow.allocate(links)

    @abstractmethod
    def _processing_task_placement(self, processing_task: ProcessingTask, application: Application) -> Node:
        pass
