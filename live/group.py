from live.object import *

class Group (LoggingObject):
	""" Represents a grouped set of Track objects.
	Because we can't programmatically query whether a track in Live is an
	individual or group track, the user must name groups using a special
	format which is passed to set.scan(group_re = RE)

	Properties:
	track_index -- The numerical track index of this group
	group_index -- Groups are auto-numbered from 0
	name -- Human-readable name
	tracks -- List of Track objects contained within this group
	"""

	def __init__(self, set, track_index, group_index, name):
		self.set = set
		self.track_index = track_index
		self.group_index = group_index

		# needed so that Clip objects can call the 'index' method on Group and Track accordingly
		# TODO: rename 'index' to 'track_index' on Track objects too
		self.index = track_index
		self.indent = 1
		self.name = name
		self.tracks = []
		self.clips = []

	def __str__(self):
		string = "live.group(%d): %s" % (self.group_index, self.name)
		if len(self.tracks):
			string = string + " [tracks %d-%d]" % (self.tracks[0].index, self.tracks[len(self.tracks) - 1].index)
		return string

	@property
	def scene_indexes(self):
		indexes = {}
		for track in self.tracks:
			for index in track.scene_indexes:
				indexes[index] = 1
		indexes = indexes.keys()
		indexes = sorted(indexes)
		return indexes

	def add_track(self, track):
		""" Append a new track to this group. Should probably only be called by Set.scan(). """
		self.tracks.append(track)

	def dump(self):
		self.trace("%d tracks" % len(self.tracks))
		for track in self.tracks:
			track.dump()

	def play_clip(self, clip_index):
		""" Start playing group clip. """
		self.set.play_clip(self.track_index, clip_index)

	@property
	def active_clips(self):
		""" Return a dictionary of all non-empty clipslots: { index : Clip, ... } """
		active_clips = filter(lambda n: n is not None, self.clips)
		return active_clips
	get_active_clips = active_clips

