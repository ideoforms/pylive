from live.constants import *
from live.object import *
from live.clip import *
from live.query import *

import re
import random

class Track(LoggingObject):
	""" Represents a single Track, either audio or MIDI.
	Resides within a Set, and contains one or more Device and Clip objects.
	May be contained within a Group.

	Properties:
	set -- The containing Set object
	index -- The numerical index of this Track within the Set
	name -- Human-readable name
	group -- (Optional) reference to containing Group object
	clips -- Dictionary of contained Clips: { index : Clip }
	devices -- List of contained Devices
	"""

	def __init__(self, set, index, name, group = None):
		self.set = set
		self.index = index
		self.name = name
		self.group = group
		self.indent = 2 if self.group else 1

		self.clip_init = None
		self.clip_playing = None
		self.clips = []
		self.devices = []

	def __str__(self):
		if self.group:
			return "live.track(%d,%d): %s" % (self.group.group_index, self.index, self.name)
		else:
			return "live.track(%d): %s" % (self.index, self.name)

	def dump(self):
		self.trace()
		if self.devices:
			for device in self.devices:
				device.dump()
		active_clips = self.active_clips
		for clip in active_clips:
			clip.dump()

	@property
	def scene_indexes(self):
		""" TODO: turn this into something that returns Scene objects (which don't yet exist) """
		indexes = []
		for clip in self.active_clips:
			indexes.append(clip.index)
		return indexes

	def clips_between(self, index_start, index_finish):
		""" Returns a list of Clip objects between index_start and index_finish """
		clips = []
		for n in range(index_start, index_finish):
			if n in self.clips:
				clips.append(self.clips[n])
		return clips

	def play_clip(self, index):
		""" Plays clip of given index. """
		self.playing = True
		self.clip_playing = index
		clip = self.clips[index]
		clip.play()

	def play_clip_random(self):
		""" Plays a random clip. """
		if len(self.clips.keys()) == 0:
			self.warn("no clips found on track, returning")
			return
		index = random.choice(self.clips.keys())
		self.play_clip(index)

	def stop(self):
		""" Immediately stop track from playing. """
		self.playing = False
		self.clip_playing = None
		self.set.stop_track(self.index)

	def syncopate(self):
		if self.clip_playing is not None:
			self.clips[self.clip_playing].syncopate()
		else:
			self.warn("asked to syncopate but not yet playing!")

	def has_clip(self, index):
		""" Determine whether this track contains a clip at slot index. """
		return self.clips.has_key(index)

	def get_clips(self):
		return self.clips

	@property
	def active_clips(self):
		""" Return a dictionary of all non-empty clipslots: { index : Clip, ... } """
		active_clips = filter(lambda n: n is not None, self.clips)
		return active_clips
	get_active_clips = active_clips

	def clip_playing(self):
		""" Return the currently playing Clip, or None. """
		for clip in self.clips:
			if clip.state == CLIP_STATE_PLAYING:
				return clip
		return None

	def sync(self):
		# XXX: why is this needed?
		info = self.set.get_track_info()
		print "track %d: info %s" % (self.index, info[0])
		self.playing = True if info[0] > 1 else False

	def walk(self):
		""" Move forward or backwards between clips. """
		if not self.playing:
			if self.clip_init:
				self.trace("walking to initial clip %d" % self.clip_init)
				self.play_clip(self.clip_init)
			else:
				self.warn("no clips found on track %d, returning" % self.index)
				return
		else:
			options = []
			if self.clips.has_key(self.clip_playing - 1):
				options.append(self.clip_playing - 1)
			if self.clips.has_key(self.clip_playing + 1):
				options.append(self.clip_playing + 1)

			if len(options) > 0:
				index = random.choice(options)
				self.trace("walking from clip %d to %d" % (self.clip_playing, index))
				self.play_clip(index)
			else:
				self.trace("walking to random clip")
				self.play_clip_random()

	#------------------------------------------------------------------------
	# get/set: volume
	#------------------------------------------------------------------------

	def set_volume(self, value):
		self.set.set_track_volume(self.index, value)
	def get_volume(self):
		return self.set.get_track_volume(self.index)
	volume = property(get_volume, set_volume, None, "track volume (0..1)")

	#------------------------------------------------------------------------
	# get/set: pan
	#------------------------------------------------------------------------

	def set_pan(self, value):
		self.set.set_track_pan(self.index, value)
	def get_pan(self):
		return self.set.get_track_pan(self.index)
	pan = property(get_pan, set_pan, None, "track pan (-1..1)")

	#------------------------------------------------------------------------
	# get/set: mute
	#------------------------------------------------------------------------

	def set_mute(self, value):
		self.set.set_track_mute(self.index, value)
	def get_mute(self):
		return self.set.get_track_mute(self.index)
	mute = property(get_mute, set_mute, None, "track mute (0/1)")

	#------------------------------------------------------------------------
	# get/set: arm
	#------------------------------------------------------------------------

	def set_arm(self, value):
		self.set.set_track_arm(self.index, value)
	def get_arm(self):
		return self.set.get_track_arm(self.index)
	arm = property(get_arm, set_arm, None, "track armed to record (0.1)")

	#------------------------------------------------------------------------
	# get/set: solo
	#------------------------------------------------------------------------

	def set_solo(self, value):
		self.set.set_track_solo(self.index, value)
	def get_solo(self):
		return self.set.get_track_solo(self.index)
	solo = property(get_solo, set_solo, None, "track in solo mode (0/1)")

	#------------------------------------------------------------------------
	# get/set: send
	#------------------------------------------------------------------------

	def set_send(self, send_index, value):
		""" Set the send level of the given send_index (0..1) """
		self.set.set_track_send(self.index, send_index, value)
	def get_send(self, send_index):
		""" Get the send level of the given send_index (0..1) """
		return self.set.get_track_send(self.index, send_index)

