import live.query
import live.object

import random

class Device(live.LoggingObject):
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
		self.indent = 2

	def __str__(self):
		return "live.device(%d,%d): %s (%d parameters)" % (self.track.index, self.index, self.name, len(self.parameters))

	def dump(self):
		self.trace()

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
