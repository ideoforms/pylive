import live.query
import live.object

import random

class Parameter(live.LoggingObject):
    """ Represents a parameter of a Live device (either an instrument or
    effects unit.

    Properties:
    device -- the Device object that this Parameter belongs to
    index -- numerical index
    name -- name, as specified by the device 
    value -- current value, within a parameter-specific range

    minimum -- minimum value (float or int)
    maximum -- maximum value (float or int)
    """

    def __init__(self, device, index, name, value):
        self.device = device
        self.index = index
        self.name = name
        self.value = value
        self.minimum = 0.0
        self.maximum = 1.0
        self.indent = 3

    def __str__(self):
        return "Parameter (%d,%d,%d): %s (range %.3f-%.3f)" % (self.device.track.index, self.device.index, self.index, self.name, self.minimum, self.maximum)

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
        self.log_info()

    def set_value(self, value):
        self.set.set_device_param(self.device.track.index, self.device.index, self.index, value)
    def get_value(self):
        return self.device.track.set.get_device_param(self.device.track.index, self.device.index, self.index)
    value = property(get_value, set_value)

    def randomise(self):
        """ Set the parameter's value to a uniformly random value within
        [minimum, maximum] """

        if self.is_integer():
            value = random.randint(self.minimum, self.maximum)
        else:
            value = random.uniform(self.minimum, self.maximum)
        self.value = value
