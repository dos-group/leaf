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
        return f"PowerMeasurement(dynamic={self.dynamic:.2f}W, static={self.static:.2f}W)"

    def __float__(self) -> float:
        return float(self.dynamic + self.static)

    def __int__(self) -> float:
        return int(self.dynamic + self.static)

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
    def __init__(self, max_power: float = None, power_per_cu: float = None, static_power: float = 0):
        """Power model for compute nodes with static and dynamic power usage.

        Power usage is scaled linearly with resource usage.

        Example:
            A computer which constantly uses 10 Watt even when being idle (`static_power=10`) but can consume
            up to 150 Watt when under full load (`max_power=150`).

        Args:
            max_power: Maximum power usage of the node under full load. Cannot be combined with `power_per_cu`.
            power_per_cu: Incremental power usage for each used compute unit. Cannot be combined with `max_power`.
            static_power: Idle power usage of the node without any load.
        """
        if max_power is None and power_per_cu is None:
            raise ValueError("Either `max_power` or `power_per_cu` have to be stated.")
        if max_power is not None and power_per_cu is not None:
            raise ValueError("The parameters `max_power` or `power_per_cu` cannot be combined.")
        self.max_power = max_power
        self.power_per_cu = power_per_cu
        self.static_power = static_power
        self.node = None

    def measure(self) -> PowerMeasurement:
        if self.max_power is not None:
            dynamic_power = (self.max_power - self.static_power) * self.node.utilization()
        elif self.power_per_cu is not None:
            dynamic_power = self.power_per_cu * self.node.used_cu
        else:
            raise RuntimeError("Invalid state of PowerModelNode: `max_power` and `power_per_cu` are undefined.")
        return PowerMeasurement(dynamic=dynamic_power, static=self.static_power)

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
    """Power meter that stores the power of one or more entites in regular intervals.

    Args:
        entities: Can be either (1) a single :class:`PowerAware` entity (2) a list of :class:`PowerAware` entities
            (3) a function which returns a list of :class:`PowerAware` entities, if the number of these entities
            changes during the simulation.
        name: Name of the power meter for logging and reporting
        measurement_interval: The freequency in which measurement take place.
        callback: A function which will be called with the PowerMeasurement result after each conducted measurement.
    """
    def __init__(self,
                 entities: Union[PowerAware, Collection[PowerAware], Callable[[], Collection[PowerAware]]],
                 name: Optional[str] = None,
                 measurement_interval: Optional[float] = 1,
                 callback: Optional[Callable[[PowerMeasurement], None]] = None):
        self.entities = entities
        if name is None:
            global _unnamed_power_meters_created
            self.name = f"power_meter_{_unnamed_power_meters_created}"
            _unnamed_power_meters_created += 1
        else:
            self.name = name
        self.measurement_interval = measurement_interval
        self.callback = callback
        self.measurements = []

    def run(self, env: simpy.Environment, delay: Optional[float] = 0):
        """Starts the power meter process.

        Args:
            env: Simpy environment (for timing the measurements)
            delay: The delay after which the measurements shall be conducted. For some scenarios it makes sense to e.g.
            include a tiny delay to make sure that all events at a previous time step were processed before the
            measurement is conducted.

        Returns:
            sim
        """
        yield env.timeout(delay)
        while True:
            if isinstance(self.entities, PowerAware):
                measurement = self.entities.measure_power()
            else:
                if isinstance(self.entities, Collection):
                    entities = self.entities
                elif isinstance(self.entities, Callable):
                    entities = self.entities()
                else:
                    raise ValueError(f"{self.name}: Unsupported type {type(self.entities)} for observable={self.entities}.")
                measurement = PowerMeasurement.sum(entity.measure_power() for entity in entities)
            self.measurements.append(measurement)
            self.callback(measurement)
            logger.debug(f"{env.now}: {self.name}: {measurement}")
            yield env.timeout(self.measurement_interval)
