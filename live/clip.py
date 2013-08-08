from live.constants import *

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
		state_symbols = { CLIP_STATUS_EMPTY : " ", CLIP_STATUS_STOPPED : "-", CLIP_STATUS_PLAYING : ">", CLIP_STATUS_STARTING : "*" }
		state_symbol = state_symbols[self.state]
		
		return "live.clip(%d,%d)%s [%s]" % (self.track.index, self.index, name, state_symbol)

	def dump(self):
		""" Output a human-readable description of this clip. """
		self.trace("(len = %d, looplen = %d)" % (self.length, self.looplen))

	@property
	def set(self):
		""" Helper method to obtain the Set that this clip resides within. """
		return self.track.set

	def _syncopate(self):
		looplen_old = self.looplen
		if self.looplen == self.length:
			self.looplen -= 1
		elif self.looplen == 1:
			self.looplen += 1
		else:
			self.looplen += random.choice([ -1, 1 ])
		self.trace("syncopating loop length from %d to %d (total length %d)" % (looplen_old, self.looplen, self.length))
		self.set.set_clip_loop_end(self.track.index, self.index, self.looplen)

	def reset(self):
		if self.looplen != self.length:
			self.trace("resetting loop length to %d" % self.length)
			self.set.set_clip_loop_end(self.track.index, self.index, self.looplen)

	def play(self):
		""" Start playing clip. """
		self.trace("playing")
		self.set.play_clip(self.track.index, self.index)

	def stop(self):
		""" Stop playing clip """
		self.trace("stopping")
		self.set.stop_clip(self.track.index, self.index)

	def get_next_clip(self, wrap = False, allow_gaps = True):
		""" Return the next clip in the track, or None if not found.
		wrap -- If set, will wrap from (N-1) to 0 and vice versa.
		allow_gaps -- If unset, requires that clip slots must be contiguous.
		"""
		clips = self.track.clips
		index = clips.index(self)
		clip_range = []
		for n in range(index, len(clips)):
			if clips[n] is None:
				if not allow_gaps:
					break
			else:
				clip_range.append(clips[n])
		for n in reversed(range(0, index)):
			if clips[n] is None:
				if not allow_gaps:
					break
			else:
				clip_range.insert(0, clips[n])

		index = clip_range.index(self)
		next_index = index + 1
		if wrap:
			next_index = next_index % len(clip_range)
		if next_index < len(clip_range):
			return clip_range[next_index]
		return None

	def get_prev_clip(self, wrap = False, allow_gaps = True):
		""" Return the previous clip in the track, or None if not found.
		wrap -- If set, will wrap from (N-1) to 0 and vice versa.
		allow_gaps -- If unset, requires that clip slots must be contiguous.
		"""
		clips = self.track.clips
		index = clips.index(self)
		clip_range = []
		for n in range(index, len(clips)):
			if clips[n] is None:
				if not allow_gaps:
					break
			else:
				clip_range.append(clips[n])
		for n in reversed(range(0, index)):
			if clips[n] is None:
				if not allow_gaps:
					break
			else:
				clip_range.insert(0, clips[n])

		index = clip_range.index(self)
		prev_index = index - 1
		if wrap and prev_index < 0:
			prev_index += len(clip_range)
		if prev_index >= 0:
			return clip_range[prev_index]
		return None
