import logging
import random
from .device import Device
from .track import Track
from ..query import Query

class Parameter:
    """
    Represents a parameter of a Live device (either an instrument or
    effects unit.)
    """

    def __init__(self, device: Device, index: int, name: str, value: float):
        """
        Args:
            device: the Device object that this Parameter belongs to
            index: numerical index
            name: name, as specified by the device
            value: current value, within a parameter-specific range
        """
        self.device = device
        self.index = index
        self.name = name
        self._value = value
        self.min = 0.0
        self.max = 1.0
        self.is_quantized = False
        self.indent = 3
        self.logger = logging.getLogger(__name__)

    @property
    def live(self):
        return Query()

    def __str__(self):
        return "Parameter (%d,%d,%d): %s (range %.3f-%.3f)" % (self.device.track.index, self.device.index, self.index, self.name, self.min, self.max)

    @property
    def set(self):
        """ Returns the Set that this parameter resides within. """
        return self.device.track.set

    @property
    def track(self) -> Track:
        """ Returns the Track that this parameter resides within. """
        return self.device.track

    def dump(self) -> None:
        self.logger.info(str(self))

    def set_value(self, value: float) -> None:
        """
        Set the value of this parameter.

        Args:
            value (float): The value to set.
        """
        self._value = value
        self.live.cmd("/live/device/set/parameter/value",
                      (self.device.track.index, self.device.index, self.index, value))

    def get_value(self) -> float:
        """
        Query the value of this parameter.

        Returns:
            The parameter's current value in Live.
        """
        return self.live.query("/live/device/get/parameter/value",
                               (self.device.track.index, self.device.index, self.index))

    value = property(get_value, set_value, doc="Query or set the value of this parameter")

    def randomise(self) -> None:
        """
        Set the parameter's value to a uniformly random value within
        [min, max]
        """

        if self.is_quantized:
            value = random.randint(self.min, self.max)
        else:
            value = random.uniform(self.min, self.max)
        self.value = value
