import live.query
import live.object

import random

class Clip(live.LoggingObject):
	def __init__(self, track, index, length):
		self.track = track
		self.index = index
		self.length = length
		self.looplen = length
		self.indent = 2
		self.state = None
		self.name = None

	def __str__(self):
		# group_index = self.track.group.group_index if self.track.group else "_"
		name = ": %s" % self.name if self.name else ""
		return "live.clip(%d,%d)%s" % (self.track.index, self.index, name)

	def dump(self):
		self.trace("(len = %d, looplen = %d)" % (self.length, self.looplen))

	@property
	def set(self):
		return self.track.set

	def syncopate(self):
		looplen_old = self.looplen
		if self.looplen == self.length:
			self.looplen -= 1
		elif self.looplen == 1:
			self.looplen += 1
		else:
			self.looplen += random.choice([ -1, 1 ])
		self.trace("syncopating loop length from %d to %d (total length %d)" % (looplen_old, self.looplen, self.length))
		live = live.Query()
		live.cmd("/live/clip/loopend", self.track.index, self.index, self.looplen)

	def reset(self):
		if self.looplen != self.length:
			self.trace("resetting loop length to %d" % self.length)
			live = live.Query()
			live.cmd("/live/clip/loopend", self.track.index, self.index, self.looplen)

	def play(self):
		self.trace("playing")
		self.set.play_clip(self.track.index, self.index)

	def stop(self):
		self.trace("stopping")
		self.set.stop_clip(self.track.index, self.index)

