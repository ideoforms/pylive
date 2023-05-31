import logging
import random
from ..query import Query

class Parameter:
    """
    Represents a parameter of a Live device (either an instrument or
    effects unit.)
    """

    def __init__(self, device, index, name, value):
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

    def is_integer(self):
        # TODO: fix for enums (such as Quality in Reverb unit). how?
        return self.name.endswith("On")

    @property
    def set(self):
        """ Helper function to return the Set that this parameter resides within. """
        return self.device.track.set

    @property
    def track(self):
        """ Helper function to return the Track that this parameter resides within. """
        return self.device.track

    def dump(self):
        self.logger.info()

    def set_value(self, value):
        self._value = value
        self.live.cmd("/live/device/set/parameter/value",
                      (self.device.track.index, self.device.index, self.index, value))

    def get_value(self):
        return self.live.query("/live/device/get/parameter/value",
                               (self.device.track.index, self.device.index, self.index))

    value = property(get_value, set_value)

    def randomise(self):
        """
        Set the parameter's value to a uniformly random value within
        [min, max]
        """

        if self.is_integer():
            value = random.randint(self.min, self.max)
        else:
            value = random.uniform(self.min, self.max)
        self.value = value
