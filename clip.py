import live.query
import live.object

import random

class Clip(live.LoggingObject):
	""" An object representing a single clip in a Live set.

	Properties:
	track -- Track object this clip resides within.
	index -- index of this clip
	length -- length of cip, in beats
	name -- human-readable name
	state -- one of CLIP_STATE_EMPTY, CLIP_STATE_STOPPED, CLIP_STATE_PLAYING
	"""

	def __init__(self, track, index, length):
		""" Create a new clip.
		
		Arguments:
		track -- a Track object
		index -- index of this clip within the track
		length -- length of clip, in beats
		"""
		self.track = track
		self.index = index
		self.length = length
		self.looplen = length
		self.indent = 2
		self.state = None
		self.name = None

	def __str__(self):
		name = ": %s" % self.name if self.name else ""
		return "live.clip(%d,%d)%s" % (self.track.index, self.index, name)

	def dump(self):
		""" Output a human-readable description of this clip. """
		self.trace("(len = %d, looplen = %d)" % (self.length, self.looplen))

	@property
	def set(self):
		""" Helper method to obtain the Set that this clip resides within. """
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
		live.cmd("/live/clip/loopend", self.track.index, self.index, self.looplen)

	def reset(self):
		if self.looplen != self.length:
			self.trace("resetting loop length to %d" % self.length)
			live.cmd("/live/clip/loopend", self.track.index, self.index, self.looplen)

	def play(self):
		""" Start playing clip. """
		self.trace("playing")
		self.set.play_clip(self.track.index, self.index)

	def stop(self):
		""" Stop playing clip """
		self.trace("stopping")
		self.set.stop_clip(self.track.index, self.index)

