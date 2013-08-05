import live.query
import live.object

import random

class Parameter(live.LoggingObject):
	def __init__(self, device, index, name, value):
		self.device = device
		self.index = index
		self.name = name
		self.value = value
		self.minimum = 0.0
		self.maximum = 1.0
		self.indent = 3

	def __str__(self):
		return "live.parameter(%d,%d,%d): %s (range %.3f-%.3f)" % (self.device.track.index, self.device.index, self.index, self.name, self.minimum, self.maximum)

	def is_integer(self):
		# XXX: fix for enums (such as Quality in Reverb unit). how?
		return self.name.endswith("On")

	@property
	def set(self):
		return self.device.track.set

	def dump(self):
		self.trace()

	def set_value(self, value):
		self.set.set_device_param(self.device.track.index, self.device.index, self.index, value)

	def get_value(self):
		return self.device.track.set.get_device_param(self.device.track.index, self.device.index, self.index)

	value = property(get_value, set_value)

	def randomize(self):
		if self.is_integer():
			value = random.randint(self.minimum, self.maximum)
		else:
			value = random.uniform(self.minimum, self.maximum)
		self.value = value
