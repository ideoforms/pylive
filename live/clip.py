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

	def __init__(self, track, index, length = 4):
		""" Create a new clip.
		
		Arguments:
		track -- a Track or Group object
		index -- index of this clip within the track
		length -- length of clip, in beats
		"""
		self.track = track
		self.index = index
		self.length = length
		self.looplen = length
		self.indent = 2
		self.state = CLIP_STATUS_STOPPED
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
		self.track.playing = True
		if type(self.track) is live.Group:
			for track in self.track.tracks:
				#------------------------------------------------------------------------
				# when we trigger a group clip, it triggers each of the corresponding
				# clips in the tracks it contains. thus need to update the playing
				# status of each of our tracks, assuming that all clips/stop buttons
				# are enabled.
				#------------------------------------------------------------------------
				if self.index < len(track.clips) and track.clips[self.index] is not None:
					track.playing = True
				else:
					track.playing = False

	def stop(self):
		""" Stop playing clip """
		self.trace("stopping")
		self.set.stop_clip(self.track.index, self.index)
		self.track.playing = False
	
	def get_pitch(self):
		return self.set.get_clip_pitch(self.track.index, self.index)
	def set_pitch(self, coarse, fine = 0):
		self.set.set_clip_pitch(self.track.index, self.index, coarse, fine)

	pitch = property(get_pitch, set_pitch, doc = "Pitch (coarse, fine)")

	def get_muted(self):
		return bool(self.set.get_clip_mute(self.track.index, self.index))
	def set_muted(self, muted = True):
		self.set.set_clip_mute(self.track.index, self.index, int(muted))

	muted = property(get_muted, set_muted, doc = "Muted (boolean)")

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
