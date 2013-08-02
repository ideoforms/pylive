import live.query
import live.object

import random

class Clip(live.LoggingObject):
	def __init__(self, track, index, state, length):
		self.track = track
		self.index = index
		self.track = track
		self.length = length
		self.looplen = length
		self.indent = 2

	def __str__(self):
		group_index = self.track.group.group_index if self.track.group else "_"
		return "live.clip(%s,%d,%d)" % (group_index, self.track.index, self.index)

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

	def dump(self):
		self.trace("%s (len = %d, looplen = %d)" % (self, self.length, self.looplen))

	def play(self):
		self.trace("playing")
		lq = live.Query()
		lq.cmd("/live/play/clip", self.track.index, self.index)
