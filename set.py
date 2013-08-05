import live.query
import live.group
import live.track
import live.device

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

		self.max_tracks_per_query = 256

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
	# /live/play/clip
	# /live/play/clipslot
	# /live/play/scene
	#------------------------------------------------------------------------

	def play(self, reset = False):
		if reset:
			# play from start
			self.live.cmd("/live/play")
		else:
			# continue playing
			self.live.cmd("/live/play/continue")

	def play_clip(self, track_index, clip_index):
		self.live.cmd("/live/play/clipslot", track_index, clip_index)

	def play_scene(self, scene_index):
		self.live.cmd("/live/play/scene", scene_index)


	#------------------------------------------------------------------------
	# /live/stop
	# /live/stop/clip
	# /live/stop/track
	#------------------------------------------------------------------------

	def stop(self):
		self.live.cmd("/live/stop")

	def stop_clip(self, track_index, clip_index):
		self.live.cmd("/live/stop/clip", track_index, clip_index)

	def stop_track(self, track_index):
		self.live.cmd("/live/stop/track", track_index)

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
	# /live/name/trackblock
	#------------------------------------------------------------------------

	def get_track_names(self, offset = None, count = None):
		if count is None:
			rv = self.live.query("/live/name/track")
			rv = [ rv[a] for a in range(1, len(rv), 2) ]
			return rv
		else:
			# /live/name/trackblock does not return indices, just names.
			rv = self.live.query("/live/name/trackblock", offset, count)
			return rv

	@property
	def track_names(self):
		return self.get_track_names()

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
		# print "setting %d to %.3f" % (track, volume)
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
	# /live/track/info
	#------------------------------------------------------------------------

	def get_track_info(self, track_index):
		return self.live.query("/live/track/info", track_index)

	#------------------------------------------------------------------------
	# /live/devicelist

	#------------------------------------------------------------------------
	# /live/clip/info
	#------------------------------------------------------------------------

	def get_clip_info(self, track_index, clip_index):
		return self.live.query("/live/clip/info", track_index, clip_index)

	#------------------------------------------------------------------------
	# /live/devicelist
	# /live/device
	# /live/device/range
	#------------------------------------------------------------------------

	def get_device_list(self, track_index):
		return self.live.query("/live/devicelist", track_index)

	def get_device_parameters(self, track_index, device_index):
		return self.live.query("/live/device", track_index, device_index, response_address = "/live/device/allparam")

	def get_device_param(self, track_index, device_index, param_index):
		return self.live.query("/live/device", track_index, device_index, param_index, response_address = "/live/device/param")

	def set_device_param(self, track_index, device_index, param_index, value):
		self.live.cmd("/live/device", track_index, device_index, param_index, value)

	def get_device_parameter_ranges(self, track_index, device_index):
		return self.live.query("/live/device/range", track_index, device_index)

	def get_device_parameter_range(self, track_index, device_index, parameter_index):
		return self.live.query("/live/device/range", track_index, device_index, parameter_index)



	#------------------------------------------------------------------------
	# SCAN
	#------------------------------------------------------------------------

	def scan(self, scan_devices = False, scan_clip_names = False):
		track_count = self.num_tracks
		if not track_count:
			self.warn("couldn't connect to Ableton Live! (obj: %s)" % self.live)
			sys.exit()

		self.scanned = True

		self.trace("scan_layout: scanning %d tracks" % track_count)

		#------------------------------------------------------------------------
		# some kind of limit seems to prevent us querying over 535ish track
		# names... let's do them 256 at a time.
		#------------------------------------------------------------------------
		track_index = 0
		track_names = []
		while track_index < track_count:
			tracks_remaining = self.max_tracks_per_query if track_count > track_index + self.max_tracks_per_query else track_count - track_index
			# self.trace("  (querying from %d, count %d)" % (track_index, tracks_remaining))
			track_names = track_names + self.get_track_names(track_index, tracks_remaining)
			track_index += self.max_tracks_per_query

		self.trace("scan_layout: got %d track names" % len(track_names))
		assert(track_count == len(track_names))
		current_group = None

		for track_index in range(track_count):
			track_name = track_names[track_index]
			self.trace("scan_layout: track %d (%s)" % (track_index, track_name))
			match = re.search(self.group_re, track_name)
			#------------------------------------------------------------------------
			# if this track's name matches our Group regular expression, assume
			# it is a Group track. this is sadly necessary because the API does not
			# expose whether or not a track is a group track!
			#------------------------------------------------------------------------
			if match:
				group_index = int(match.group(1))
				group_name = match.group(2)
				group = live.Group(track_index, group_index, group_name)
				current_group = group
				self.groups.append(group)
			else:
				# TODO: consistence between Group and Track constructors
				track_info = self.get_track_info(track_index)
				clips = track_info[2:]
				track = live.Track(self, track_index, track_name, current_group)
				if current_group is not None:
					current_group.add_track(track)
				self.tracks.append(track)

				print "scanning devices for track %s (set %s)" % (track, track.set)
				clip_info = track_info[2:]

				for n in range(0, len(clip_info), 3):
					clip_index = n / 3
					state = clip_info[n + 1]
					length = clip_info[n + 2]
					if state > 0:
						track.clips[clip_index] = live.Clip(track, clip_index, length)
						track.clips[clip_index].state = state
						track.clips[clip_index].indent = 3 if track.group else 2

						if not track.clip_init:
							track.clip_init = clip_index
	
						#--------------------------------------------------------------------------
						# scan for clip names.
						# is nice, but slows things down significantly -- so disable by default.
						#--------------------------------------------------------------------------
						if scan_clip_names:
							name = live.query("/live/name/clip", track.index, clip_index)
							name = name[2]
							track.clips[clip_index].name = name

						# loop_start = live.query_one("/live/clip/loopstart", self.index, clip_index)
						# print "loop start = %d" % loop_start

				if scan_devices:
					# TODO: scan for devices
					devices = self.get_device_list(track.index)
					devices = devices[1:]
					for i in range(0, len(devices), 2):
						index = devices[i]
						name = devices[i + 1]
						device = live.Device(track, index, name)
						track.devices.append(device)
						parameters = self.get_device_parameters(track.index, device.index)
						parameters = parameters[2:]
						ranges = self.get_device_parameter_ranges(track.index, device.index)
						ranges = ranges[2:]
						for j in range(0, len(parameters), 3):
							index    = parameters[j + 0]
							value    = parameters[j + 1]
							name     = parameters[j + 2]
							minimum  = ranges[j + 1]
							maximum  = ranges[j + 2]
							param = live.Parameter(device, index, name, value)
							param.minimum = minimum
							param.maximum = maximum
							device.parameters.append(param)

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
				track.dump()

	def group_named(self, name):
		for group in self.groups:
			if group.name == name:
				return group
		return None
