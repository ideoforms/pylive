from live.object import *
from live.clip import *
from live.liveq import *

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
	def __init__(self, name, info, group = None):
		self.name = name
		self.movement = 0
		self.index = info[0]
		self.playing = True if info[1] == STATUS_PLAYING else False
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

		clipinfo = info[2:]

		live = LiveQuery()
		for n in range(0, len(clipinfo), 3):
			number = n / 3
			state = clipinfo[n + 1]
			length = clipinfo[n + 2]
			if state > 0:
				self.clips[number] = Clip(self, number, state, length)
				self.clips[number].indent = 3 if self.group else 2
				#--------------------------------------------------------------------------
				# would be nice, but slows things down fivefold.
				#--------------------------------------------------------------------------
				# name = live.query("/live/name/clip", self.index, number)
				# name = name[2]
				# self.clips[number].name = name
				loop_start = live.query_one("/live/clip/loopstart", self.index, number)
				print "loop start = %d" % loop_start
				self.clip_init = number

	def __str__(self):
		if self.group:
			return "live.track(%s,%d)" % (self.group.group_index, self.index)
		else:
			return "live.track(_,%d)" % (self.index)

	def dump(self):
		self.trace()
		for index, clip in self.clips.items():
			clip.dump()

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
		live = LiveQuery()
		live.cmd("/live/stop/track", self.index)

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
		live = LiveQuery()
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
