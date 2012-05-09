from live.query import *
from live.group import *
from live.track import *

import re
import sys

import pickle

@singleton
class Set (LoggingObject):
	def __init__(self):
		self.indent = 0
		self.groups = []
		self.tracks = []
		self.group_re = re.compile("^(\d+)\. (\S.+)")
		self.live = LiveQuery()
		self.scanned = False

	def __str__(self):
		return "live.set"
	
	def scan(self):
		tracks = self.live.query("/live/tracks")
		if not tracks:
			self.warn("couldn't connect to Ableton Live! (obj: %s)" % self.live)
			sys.exit()

		track_count = tracks[0]
		self.scanned = True

		self.trace("scan_layout: scanning %d tracks" % track_count)

		#------------------------------------------------------------------------
		# some kind of limit seems to prevent us querying over 535ish track
		# names... let's do them 256 at a time.
		#------------------------------------------------------------------------
		track_index = 0
		track_names = []
		while track_index < track_count:
			tracks_remaining = 256 if track_count > track_index + 256 else track_count - track_index
			# self.trace("  (querying from %d, count %d)" % (track_index, tracks_remaining))
			track_names = track_names + self.live.query("/live/name/trackblock", track_index, tracks_remaining)
			track_index += 256

		self.trace("scan_layout: got %d track names" % len(track_names))
		assert(track_count == len(track_names))
		current_group = None

		for track_index in range(track_count):
			track_name = track_names[track_index]
			self.trace("scan_layout: track %d (%s)" % (track_index, track_name))
			match = re.search(self.group_re, track_name)
			if match:
				group_index = int(match.group(1))
				group_name = match.group(2)
				group = Group(track_index, group_index, group_name)
				current_group = group
				self.groups.append(group)
			else:
				# TODO: consistence between Group and Track constructors
				track_info = self.live.query("/live/track/info", track_index)
				clips = track_info[2:]
				track = Track(track_name, track_info, current_group)
				if current_group is not None:
					current_group.add_track(track)
				self.tracks.append(track)

		# now iterate through all tracks and clips, registering scenes in groups

	def load(self, filename = "set.pickle"):
		data = pickle.load(file(filename))
		for key, value in data.items():
			setattr(self, key, value)
		print "load: set loaded OK (%d tracks)" % (len(self.tracks))

	def save(self, filename = "set.pickle"):
		fd = file(filename, "w")
		data = vars(self)
		del data["live"]
		pickle.dump(data, fd)
		print "save: set saved OK (%s)" % filename

	def dump(self):
		if len(self.tracks) == 0:
			self.trace("dump: currently empty, performing scan")
			self.scan_layout()
		self.trace("dump: %d tracks in %d groups" % (len(self.tracks), len(self.groups)))
		current_group = None

		#------------------------------------------------------------------------
		# dump tracks and groups, displaying hierarchically 
		#------------------------------------------------------------------------
		for track in self.tracks:
			if track.group:
				if (not current_group) or (track.group != current_group):
					track.group.dump()
				current_group = track.group
			else:
				if current_group:
					current_group = None
					track.dump()

	def group_named(self, name):
		for group in self.groups:
			if group.name == name:
				return group
		return None
