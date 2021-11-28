import logging
import math
from abc import ABC, abstractmethod
from functools import reduce
from typing import List, Union, Collection, Callable, Optional, Iterable

import simpy

logger = logging.getLogger(__name__)
_unnamed_power_meters_created = 0


class PowerMeasurement:
    def __init__(self, dynamic: float, static: float):
        """Power measurement of one or more entities at a certain point in time.

        Args:
            dynamic: Dynamic (load-dependent) power usage in Watt
            static: Static (load-independent) power usage in Watt
        """
        self.dynamic = dynamic
        self.static = static

    @classmethod
    def sum(cls, measurements: Iterable["PowerMeasurement"]):
        dynamic, static = reduce(lambda acc, cur: (acc[0] + cur.dynamic, acc[1] + cur.static), measurements, (0, 0))
        return PowerMeasurement(dynamic, static)

    def __repr__(self):
        return f"PowerMeasurement(dynamic={self.dynamic}W, static={self.static}W)"

    def __float__(self) -> float:
        return float(self.dynamic + self.static)

    def __add__(self, other):
        return PowerMeasurement(self.dynamic + other.dynamic, self.static + other.static)

    def __radd__(self, other):  # Required for sum()
        if other == 0:
            return self
        else:
            return self.__add__(other)

    def __sub__(self, other):
        return PowerMeasurement(self.dynamic - other.dynamic, self.static - other.static)

    def multiply(self, factor: float):
        return PowerMeasurement(self.dynamic * factor, self.static * factor)

    def total(self) -> float:
        return float(self)


class PowerModel(ABC):
    """Abstract base class for power models."""

    # TODO: Validator! Only one power model per entity

    @abstractmethod
    def measure(self) -> PowerMeasurement:
        """Return the current power usage."""

    @abstractmethod
    def set_parent(self, parent):
        """Set the entity which the power model is responsible for.

        Should be called in the parent's `__init__()`.
        """


class PowerModelNode(PowerModel):
    def __init__(self, max_power: float, static_power: float):
        """Power model for compute nodes with static and dynamic power usage.

        Power usage is scaled linearly with resource usage.

        Example:
            A computer which constantly uses 10 Watt even when being idle (`static_power=10`) but can consume
            up to 150 Watt when under full load (`max_power=150`).

        Args:
            max_power: Maximum power usage of the node under full load.
            static_power: Idle power usage of the node without any load.
        """
        self.max_power = max_power
        self.static_power = static_power
        self.node = None

    def measure(self) -> PowerMeasurement:
        dynamic_power = (self.max_power - self.static_power) * self.node.utilization()
        return PowerMeasurement(dynamic=dynamic_power, static=self.static_power)

    def set_parent(self, parent):
        self.node = parent


class PowerModelNodeShared(PowerModel):
    def __init__(self, power_per_mips: float):
        """Power model for shared infrastructure.

        For nodes such as data centers we may know neither the static nor max power usage and hence define only the
        incremental power usage.


        Args:
            power_per_mips: Incremental power per million instructions per seconds in W/MIPS (or J/MIP)
        """
        self.power_per_mips = power_per_mips
        self.node = None

    def measure(self) -> PowerMeasurement:
        dynamic_power = self.power_per_mips * self.node.used_mips
        return PowerMeasurement(dynamic=dynamic_power, static=0)

    def set_parent(self, parent):
        self.node = parent


class PowerModelLink(PowerModel):
    def __init__(self, energy_per_bit: float):
        """Power model for network links.

        Args:
            energy_per_bit: Incremental energy per bit in J/bit (or W/(bit/s))
        """
        self.energy_per_bit = energy_per_bit
        self.link = None

    def measure(self) -> PowerMeasurement:
        dynamic_power = self.energy_per_bit * self.link.used_bandwidth
        return PowerMeasurement(dynamic=dynamic_power, static=0)

    def set_parent(self, parent):
        self.link = parent


class PowerModelLinkWirelessTx(PowerModel):
    def __init__(self, energy_per_bit: float, amplifier_dissipation: float):
        """Power model for transmitting on wireless network links.

        TODO Explain

        Note:
            If you don't know the amplifier dissipation or distance of nodes or if you are concerned with performance,
            you can also just use the regular :class:`PowerModelLink`

        Args:
            energy_per_bit: Incremental energy per bit in J/bit (or W/(bit/s))
            amplifier_dissipation: Amplifier energy dissipation in free space channel in J/bit/m^2
        """
        self.energy_per_bit = energy_per_bit
        self.amplifier_dissipation = amplifier_dissipation
        self.link = None

    def measure(self) -> PowerMeasurement:
        distance = self.link.src.distance(self.link.dst)
        dissipation_energy_per_bit = self.amplifier_dissipation * distance ** 2
        dynamic_power = (self.energy_per_bit + dissipation_energy_per_bit) * self.link.used_bandwidth
        return PowerMeasurement(dynamic=dynamic_power, static=0)

    def set_parent(self, parent):
        self.link = parent


class PowerAware(ABC):
    """Abstract base class for entites whose power can be measured.

    This may be parts of the infrastructure as well as applications.
    """

    @abstractmethod
    def measure_power(self) -> PowerMeasurement:
        """Returns the power that is currently used by the entity."""


class PowerMeter:
    """Convenience class that wraps power_meter()."""
    def __init__(self, env, entities, **kwargs):
        self.measurements = []
        env.process(power_meter(env, entities, callback=lambda m: self.measurements.append(m), **kwargs))


def power_meter(env: simpy.Environment,
                entities: Union[PowerAware, Collection[PowerAware], Callable[[], Collection[PowerAware]]],
                callback: Callable[[PowerMeasurement], None],
                name: Optional[str] = None,
                measurement_interval: Optional[float] = 1,
                delay: Optional[float] = 0):
    """Power meter with measures and saves the power of one or more entites in regular intervals.

    Args:
        env: Simpy environment (for timing the measurements)
        entities: Can be either (1) a single :class:`PowerAware` entity (2) a list of :class:`PowerAware` entities
            (3) a function which returns a list of :class:`PowerAware` entities, if the number of these entities
            changes during the simulation.
        callback: TODO
        name: Name of the power meter for logging and reporting
        measurement_interval: The measurement interval.
        delay: The delay after which the measurements shall be conducted. For some scenarios it makes sense to e.g.
            include a tiny delay to make sure that all events at a previous time step were processed before the
            measurement is conducted.
    """
    if name is None:
        global _unnamed_power_meters_created
        name = f"power_meter_{_unnamed_power_meters_created}"
        _unnamed_power_meters_created += 1

    yield env.timeout(delay)
    while True:
        if isinstance(entities, PowerAware):
            measurement = entities.measure_power()
        else:
            if isinstance(entities, Collection):
                entities = entities
            elif isinstance(entities, Callable):
                entities = entities()
            else:
                raise ValueError(f"{name}: Unsupported type {type(entities)} for observable={entities}.")
            measurement = PowerMeasurement.sum(entity.measure_power() for entity in entities)
        callback(measurement)
        logger.debug(f"{env.now}: {name}: {measurement}")
        yield env.timeout(measurement_interval)
