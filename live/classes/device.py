import logging

class Device:
    """ Represents an instrument or audio effect residing within a Track.
    Contains one one or more Parameters.

    Properties:
    track -- Track object that this Device resides within
    index -- Numeric index of this device
    name -- Human-readable name
    parameters -- List of Parameter objects
    """

    def __init__(self, track, index, name):
        self.track = track
        self.index = index
        self.name = name
        self.parameters = []
        self.logger = logging.getLogger(__name__)

    def __str__(self):
        return "Device (%d,%d): %s" % (self.track.index, self.index, self.name)

    def __getstate__(self):
        return {
            "track": self.track,
            "index": self.index,
            "name": self.name,
            "parameters": self.parameters,
        }

    def __setstate__(self, d: dict):
        self.track = d["track"]
        self.index = d["index"]
        self.name = d["name"]
        self.parameters = d["parameters"]

    @property
    def set(self):
        """ Helper function to return the Set that this Device resides within. """
        return self.track.set

    def set_parameter(self, index, value):
        if type(index) == int:
            parameter = self.parameters[index]
        else:
            parameter = next(p for p in self.parameters if p.name == index)
        parameter.value = value

    def get_parameter(self, index):
        if type(index) == int:
            parameter = self.parameters[index]
        else:
            parameter = next(p for p in self.parameters if p.name == index)
        return parameter.value
