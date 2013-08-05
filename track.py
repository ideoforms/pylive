from live.object import *
from live.clip import *
from live.query import *

import re
import random

TYPE_MELODY = 0 
TYPE_RHYTHM = 1
TYPE_TEXTURE = 2

TYPE_NAMES = [ "Melody", "Rhythm", "Texture" ]

# UNTESTED
STATUS_STOPPED = 0
STATUS_PLAYING = 2

class Track(LoggingObject):
	def __init__(self, set, index, name, group = None):
		self.set = set
		self.index = index
		self.name = name
		self.group = group
		self.indent = 2 if self.group else 1

		#--------------------------------------------------------------------------
		# extract track type.
		# scheme: <MOVEMENT_NUMBER><TYPE><AUDIO/MIDI><fIXED/aLGORITHMIC>
		# where MOVEMENT_NUMBER may be a wormhole letter!
		#--------------------------------------------------------------------------
		match = re.match("^(\d+|[ABCDEFGHIJKL])([MTR])", name)
		if match:
			type = match.group(2)
			if type == "M":
				self.type = TYPE_MELODY
			elif type == "R":
				self.type = TYPE_RHYTHM
			elif type == "T":
				self.type = TYPE_TEXTURE

			self.trace("type %s (name %s)" % (self.index, TYPE_NAMES[self.type], name))
		else:
			# print "**** UH OH, can't identify track %s - assuming texture" % name
			self.type = TYPE_TEXTURE

		self.clip_init = None
		self.clip_playing = None
		self.clips = {}
		self.devices = []

	def __str__(self):
		if self.group:
			return "live.track(%d): %s" % (self.group.group_index, self.index, self.name)
		else:
			return "live.track(%d): %s" % (self.index, self.name)

	def dump(self):
		self.trace()
		if self.devices:
			for device in self.devices:
				device.dump()
		for index, clip in self.clips.items():
			clip.dump()

	def clips_between(self, index_start, index_finish):
		clips = []
		for n in range(index_start, index_finish):
			if n in self.clips:
				clips.append(self.clips[n])
		return clips

	def play_clip(self, index):
		self.playing = True
		self.clip_playing = index
		clip = self.clips[index]
		clip.play()

	def play_clip_random(self):
		if len(self.clips.keys()) == 0:
			self.warn("no clips found on track, returning")
			return
		index = random.choice(self.clips.keys())
		self.play_clip(index)

	def stop(self):
		self.playing = False
		self.clip_playing = None
		self.set.stop_track(self.index)

	def syncopate(self):
		if self.clip_playing is not None:
			self.clips[self.clip_playing].syncopate()
		else:
			self.warn("asked to syncopate but not yet playing!")

	def has_clip(self, index):
		return self.clips.has_key(index)

	def get_clips(self):
		return self.clips

	def sync(self):
		# XXX: why is this needed?
		live = live.Query()
		info = live.query("/live/track/info")
		print "track %d: info %s" % (self.index, info[0])
		self.playing = True if info[0] > 1 else False

	def walk(self):
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

	def is_melody(self):
		return self.type == TYPE_MELODY

	def is_rhythm(self):
		return self.type == TYPE_RHYTHM

	def is_texture(self):
		return self.type == TYPE_TEXTURE

	#------------------------------------------------------------------------
	# get/set: volume
	#------------------------------------------------------------------------
	def set_volume(self, value):
		self.set.set_track_volume(self.index, value)
	def get_volume(self):
		return self.set.get_track_volume(self.index)
	volume = property(get_volume, set_volume)

	#------------------------------------------------------------------------
	# get/set: pan
	#------------------------------------------------------------------------
	def set_pan(self, value):
		self.set.set_track_pan(self.index, value)
	def get_pan(self):
		return self.set.get_track_pan(self.index)
	pan = property(get_pan, set_pan)

	#------------------------------------------------------------------------
	# get/set: mute
	#------------------------------------------------------------------------
	def set_mute(self, value):
		self.set.set_track_mute(self.index, value)
	def get_mute(self):
		return self.set.get_track_mute(self.index)
	mute = property(get_mute, set_mute)

	#------------------------------------------------------------------------
	# get/set: arm
	#------------------------------------------------------------------------
	def set_arm(self, value):
		self.set.set_track_arm(self.index, value)
	def get_arm(self):
		return self.set.get_track_arm(self.index)
	arm = property(get_arm, set_arm)

	#------------------------------------------------------------------------
	# get/set: solo
	#------------------------------------------------------------------------
	def set_solo(self, value):
		self.set.set_track_solo(self.index, value)
	def get_solo(self):
		return self.set.get_track_solo(self.index)
	solo = property(get_solo, set_solo)

	#------------------------------------------------------------------------
	# get/set: send
	#------------------------------------------------------------------------
	def set_send(self, send_index, value):
		self.set.set_track_send(self.index, send_index, value)
	def get_send(self, send_index):
		return self.set.get_track_send(self.index, send_index)

