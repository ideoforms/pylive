from live.object import *

class Group (LoggingObject):
	def __init__(self, track_index, group_index, name):
		self.indent = 1
		self.track_index = track_index
		self.group_index = group_index
		self.name = name
		self.tracks = []
		self.scene_first = None
		self.scene_last = None

	def __str__(self):
		string = "live.group(%s): %s" % (self.group_index, self.name)
		if len(self.tracks):
			string = string + " [tracks %d-%d]" % (self.tracks[0].index, self.tracks[len(self.tracks) - 1].index)
		if self.scene_first:
			string = string + " [scenes %d-%d]" % (self.scene_first, self.scene_last)
		return string

	def add_track(self, track):
		self.tracks.append(track)

	def dump(self):
		self.trace("%d tracks" % len(self.tracks))
		for track in self.tracks:
			track.dump()
