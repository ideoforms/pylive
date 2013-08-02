import live.query
import live.group
import live.track

import re
import sys

import pickle

@live.singleton
class Set (live.LoggingObject):
	def __init__(self):
		self.indent = 0
		self.groups = []
		self.tracks = []
		self.group_re = re.compile("^(\d+)\. (\S.+)")
		self.live = live.Query()
		self.scanned = False

	def __str__(self):
		return "live.set"

	#------------------------------------------------------------------------
	# /live/tempo
	#------------------------------------------------------------------------

	def get_tempo(self):
		return self.live.query("/live/tempo")[0]

	def set_tempo(self, value):
		self.live.cmd("/live/tempo", value)

	tempo = property(get_tempo, set_tempo)
	
	#------------------------------------------------------------------------
	# /live/time
	#------------------------------------------------------------------------

	def get_time(self):
		return self.live.query("/live/time")[0]

	def set_time(self, value):
		self.live.cmd("/live/time", value)

	time = property(get_time, set_time)

	#------------------------------------------------------------------------
	# /live/overdub
	# (uses /live/state to query)
	#------------------------------------------------------------------------

	def get_overdub(self):
		value = self.live.query("/live/state")
		return value[1]

	def set_overdub(self, value):
		self.live.cmd("/live/overdub", value)

	overdub = property(get_overdub, set_overdub)

	#------------------------------------------------------------------------
	# /live/state
	#------------------------------------------------------------------------

	@property
	def state(self):
		return self.live.query("/live/state")

	#------------------------------------------------------------------------
	# /live/undo
	# /live/redo
	#------------------------------------------------------------------------

	def undo(self):
		self.live.cmd("/live/undo")

	def redo(self):
		self.live.cmd("/live/redo")

	#------------------------------------------------------------------------
	# /live/prev/cue
	# /live/next/cue
	#------------------------------------------------------------------------

	def prev_cue(self):
		self.live.cmd("/live/prev/cue")
	def next_cue(self):
		self.live.cmd("/live/next/cue")

	#------------------------------------------------------------------------
	# /live/play
	# /live/play/continue
	# /live/play/selection
	#------------------------------------------------------------------------

	def play(self, reset = False):
		if reset:
			# play from start
			self.live.cmd("/live/play")
		else:
			# continue playing
			self.live.cmd("/live/play/continue")

	#------------------------------------------------------------------------
	# /live/stop
	#------------------------------------------------------------------------

	def stop(self):
		self.live.cmd("/live/stop")

	#------------------------------------------------------------------------
	# /live/scenes
	#------------------------------------------------------------------------

	@property
	def num_scenes(self):
		return self.live.query("/live/scenes")[0]

	#------------------------------------------------------------------------
	# /live/tracks
	#------------------------------------------------------------------------

	@property
	def num_tracks(self):
		return self.live.query("/live/tracks")[0]

	#------------------------------------------------------------------------
	# /live/scene
	#------------------------------------------------------------------------

	def get_scene(self):
		return self.live.query("/live/scene")[0]

	def set_scene(self, value):
		self.live.cmd("/live/scene", value)

	scene = property(get_scene, set_scene)

	#------------------------------------------------------------------------
	# /live/name/scene
	#------------------------------------------------------------------------

	@property
	def scene_names(self):
		rv = self.live.query("/live/name/scene")
		rv = [ rv[a] for a in range(1, len(rv), 2) ]
		return rv
	get_scene_names = scene_names

	def get_scene_name(self, index):
		return self.live.query("/live/name/scene", index)

	def set_scene_name(self, index, value):
		self.live.cmd("/live/name/scene", index, value)

	#------------------------------------------------------------------------
	# /live/name/track
	#------------------------------------------------------------------------

	@property
	def track_names(self):
		rv = self.live.query("/live/name/track")
		rv = [ rv[a] for a in range(1, len(rv), 2) ]
		return rv
	get_track_names = track_names

	def get_track_name(self, index):
		return self.live.query("/live/name/track", index)

	def set_track_name(self, index, value):
		self.live.cmd("/live/name/track", index, value)

	#------------------------------------------------------------------------
	# /live/arm
	#------------------------------------------------------------------------

	def get_track_arm(self, track):
		return self.live.query("/live/arm", track)[1]

	def set_track_arm(self, track, arm):
		self.live.cmd("/live/arm", track, arm)

	#------------------------------------------------------------------------
	# /live/mute
	#------------------------------------------------------------------------

	def get_track_mute(self, track):
		return self.live.query("/live/mute", track)[1]

	def set_track_mute(self, track, mute):
		self.live.cmd("/live/mute", track, mute)

	#------------------------------------------------------------------------
	# /live/solo
	#------------------------------------------------------------------------

	def get_track_solo(self, track):
		return self.live.query("/live/solo", track)[1]

	def set_track_solo(self, track, solo):
		self.live.cmd("/live/solo", track, solo)

	#------------------------------------------------------------------------
	# /live/volume
	#------------------------------------------------------------------------

	def get_track_volume(self, track):
		return self.live.query("/live/volume", track)[1]

	def set_track_volume(self, track, volume):
		print "setting %d to %.3f" % (track, volume)
		self.live.cmd("/live/volume", track, volume)

	#------------------------------------------------------------------------
	# /live/pan
	#------------------------------------------------------------------------

	def get_track_pan(self, track):
		return self.live.query("/live/pan", track)[1]

	def set_track_pan(self, track, pan):
		self.live.cmd("/live/pan", track, pan)

	#------------------------------------------------------------------------
	# /live/send
	#------------------------------------------------------------------------

	def get_track_send(self, track, send):
		return self.live.query("/live/send", track, send)[2]

	def set_track_send(self, track, send, value):
		self.live.cmd("/live/send", track, send, value)

	#------------------------------------------------------------------------
	# /live/master/volume
	# /live/master/pan
	#------------------------------------------------------------------------

	def get_master_volume(self):
		return self.live.query("/live/master/volume")[0]

	def set_master_volume(self, value):
		self.live.cmd("/live/master/volume", value)

	master_volume = property(get_master_volume, set_master_volume)

	def get_master_pan(self):
		return self.live.query("/live/master/pan")[0]

	def set_master_pan(self, value):
		self.live.cmd("/live/master/pan", value)

	master_pan = property(get_master_pan, set_master_pan)

	#------------------------------------------------------------------------
	#------------------------------------------------------------------------

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
				group = live.Group(track_index, group_index, group_name)
				current_group = group
				self.groups.append(group)
			else:
				# TODO: consistence between Group and Track constructors
				track_info = self.live.query("/live/track/info", track_index)
				clips = track_info[2:]
				track = live.Track(track_name, track_info, current_group)
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
