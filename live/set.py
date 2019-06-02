# -*- coding: utf-8 -*-

from .constants import CLIP_STATUS_STOPPED
from .exceptions import LiveIOError, LiveConnectionError
from .object import LoggingObject, name_cache
from .query import Query
from .track import Track
from .group import Group
from .clip import Clip
from .scene import Scene
from .device import Device
from .parameter import Parameter

import os
import re
import sys
import glob
import time
import pickle
import threading

try:
    import urllib.parse
except ImportError:
    # Python 2 support
    import urllib

class Set (LoggingObject):
    """ Set represents an entire running Live set. It communicates via a
    live.Query object to the Live instance, which must be running LiveOSC
    as an active control surface.

    A Set contains a number of Track objects, which may optionally have a
    parent Group. Each Track object contains one or more Clip objects, and
    one or more Devices, each of which possess Parameters.

    A Set object is initially unpopulated, and must interrogate the Live set
    for its contents by calling the scan() method.

    Properties:
    tempo -- tempo in BPM
    time -- time position, in beats
    overdub -- global overdub setting
    """

    def __init__(self, address = ("localhost", 9000)):
        self.scanned = False

        """ Set caching to True to avoid re-querying properties such as tempo each
        time they are requested. Increases efficiency in cases where no other
        processes are going to modify Live's state. """
        self.caching = False

        self.max_tracks_per_query = 256

        #--------------------------------------------------------------------------
        # create mutexes and events for inter-thread handling (to catch on-beat
        # events, etc)
        #--------------------------------------------------------------------------
        self._add_mutexes()

        #--------------------------------------------------------------------------
        # add handlers to catch any state changes in the set, so we
        # remain up-to-date with whether clips are playing, etc...
        #--------------------------------------------------------------------------
        self._add_handlers()

        self.reset()

    def __str__(self):
        return "Set"

    def reset(self):
        self.groups = []
        self.tracks = []
        self.scenes = []

    def open(self, filename, wait=True):
        """ Open an Ableton project, either by the path to the Project directory or
        to an .als file. Will search in the current directory and the contents of
        the LIVE_ROOT environmental variable.

        Will only work with OS X right now as it presupposes an /Applications/*.app
        format for the Live app.

        wait = True: block until the set is loaded (waits for a LiveOSC trigger) """

        paths = ["."]
        if "LIVE_ROOT" in os.environ:
            paths.append(os.environ["LIVE_ROOT"])
        
        #------------------------------------------------------------------------
        # Iterate through each path searching for the project file.
        #------------------------------------------------------------------------
        for root in paths:
            path = os.path.join(root, filename)
            if os.path.exists(path):
                break
            if os.path.exists("%s.als" % path):
                path = "%s.als" % path
                break
            if os.path.exists("%s Project/%s.als" % (path, path)):
                path = "%s Project/%s.als" % (path, path)
                break

        current = self.currently_open()
        path = os.path.abspath(path)
        if current and current == path:
            self.log_info("Project '%s' is already open" % os.path.basename(path))
            return

        if not os.path.exists(path):
            raise LiveIOError("Couldn't find project file '%s'. Have you set the LIVE_ROOT environmental variable?")

        #------------------------------------------------------------------------
        # Assume that the alphabetically-last Ableton binary is the one we 
        # want (ie, greatest version number.)
        #------------------------------------------------------------------------
        ableton = sorted(glob.glob("/Applications/Ableton*.app"))[-1]
        cmd = "open -a '%s' '%s'" % (ableton, path)
        os.system(cmd)

        if wait:
            self.wait_for_startup()
        return True

    def _get_last_opened_set_filename(self):
        #------------------------------------------------------------------------
        # Use Log.txt corresponding to latest Live version. eg:
        # ~/Library/Preferences/Ableton/Live\ 9.0.6/Log.txt 
        #------------------------------------------------------------------------
        root = os.path.expanduser("~/Library/Preferences/Ableton")
        logfiles = glob.glob("%s/Live */Log.txt" % root)
        open_regexp = r"file://.*\.als$"

        if logfiles:
            logfiles = list(sorted(logfiles, key=lambda a: os.path.getmtime(a)))
            logfile = logfiles[-1]
            contents = open(logfile).readlines()
            projects = [line for line in contents if re.search(open_regexp, line)]

            #------------------------------------------------------------------------
            # Some log entries mentioning an .als file are referring to the
            # default live template, meaning we've currently got an empty document.
            # Check that this is not the case by matching against a file open RE.
            #------------------------------------------------------------------------
            if projects:
                project = projects[-1].strip()
                try:
                    project = urllib.parse.unquote(project)
                except AttributeError:
                    # Python 2 support
                    project = urllib.unquote(project)

                project = project.replace("file://", "")
                #------------------------------------------------------------------------
                # Create canonical path, flattening (e.g.) double-slashes.
                #------------------------------------------------------------------------
                project = os.path.realpath(project)
                return project

        return None

    def currently_open(self):
        """ Retrieve filename of currently-open Ableton Live set
        based on inspecting Live's last Log.txt, or None if Live not open. """

        #------------------------------------------------------------------------
        # If Live is not running at all, return None.
        #------------------------------------------------------------------------
        is_running = os.system("ps axc -o command  | grep -q ^Live$") == 0
        if is_running:
            return self._get_last_opened_set_filename()
        else:
            return None

    @property
    def live(self):
        return Query()

    @property
    def is_connected(self):
        """ Test whether we can connect to Live """
        try:
            return bool(self.tempo)
        except Exception as e:
            return False

    #------------------------------------------------------------------------
    # /live/tempo
    #------------------------------------------------------------------------

    @name_cache
    def get_tempo(self):
        return self.live.query("/live/tempo")[0]

    @name_cache
    def set_tempo(self, value):
        self.live.cmd("/live/tempo", value)

    tempo = property(get_tempo, set_tempo, doc="Global tempo")
    
    #------------------------------------------------------------------------
    # /live/quantization
    #------------------------------------------------------------------------

    @name_cache
    def get_quantization(self):
        return self.live.query("/live/quantization")[0]

    @name_cache
    def set_quantization(self, value):
        self.live.cmd("/live/quantization", value)

    quantization = property(get_quantization, set_quantization, doc="Global quantization")
    
    #------------------------------------------------------------------------
    # /live/time
    #------------------------------------------------------------------------

    def get_time(self):
        """ Return the current time position in the Arrangement view, in beats. """
        return self.live.query("/live/time")[0]

    def set_time(self, value):
        """ Set the current time position in the Arrangement view, in beats. """
        self.live.cmd("/live/time", value)

    time = property(get_time, set_time, doc="Current time position (beats)")

    #------------------------------------------------------------------------
    # /live/overdub
    # (uses /live/state to query)
    #------------------------------------------------------------------------

    def get_overdub(self):
        """ Return the global overdub setting. """
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
        """ Return the global state tuple: (tempo, overdub) """
        return self.live.query("/live/state")

    #------------------------------------------------------------------------
    # /live/undo
    # /live/redo
    #------------------------------------------------------------------------

    def undo(self):
        """ Undo the last operation. """
        self.live.cmd("/live/undo")

    def redo(self):
        """ Redo the last undone operation. """
        self.live.cmd("/live/redo")

    #------------------------------------------------------------------------
    # /live/prev/cue
    # /live/next/cue
    #------------------------------------------------------------------------

    def prev_cue(self):
        """ Jump to the previous cue. """
        self.live.cmd("/live/prev/cue")

    def next_cue(self):
        """ Jump to the next cue. """
        self.live.cmd("/live/next/cue")

    #------------------------------------------------------------------------
    # /live/play
    # /live/play/continue
    # /live/play/selection
    # /live/play/clip
    # /live/play/clipslot
    # /live/play/scene
    #------------------------------------------------------------------------

    def play(self, reset=False):
        """ Start the song playing. If reset is given, begin at the cue point. """
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
        """ Return the total number of scenes present (even if empty). """
        return self.live.query("/live/scenes")[0]

    #------------------------------------------------------------------------
    # /live/tracks
    #------------------------------------------------------------------------

    @property
    def num_tracks(self):
        """ Return the total number of tracks. """
        return self.live.query("/live/tracks")[0]

    #------------------------------------------------------------------------
    # /live/scene
    #------------------------------------------------------------------------

    def get_current_scene(self):
        """ Return the index of the currently-selected scene index. """
        return self.live.query("/live/scene")[0]

    def set_current_scene(self, value):
        """ Set the currently-selected scene index. """
        self.live.cmd("/live/scene", value)

    current_scene = property(get_current_scene, set_current_scene)

    #------------------------------------------------------------------------
    # /live/name/scene
    #------------------------------------------------------------------------

    @property
    def scene_names(self):
        """ Return a list of all scene names."""
        #------------------------------------------------------------------------
        # /live/name/scene breaks over a certain number of scenes but 
        # sceneblock seems resilient - so use that instead.
        #------------------------------------------------------------------------
        scene_count = self.num_scenes
        rv = self.live.query("/live/name/sceneblock", 0, scene_count)
        return rv
    get_scene_names = scene_names

    def get_scene_name(self, index):
        """ Return the name of the scene given by index. """
        return self.live.query("/live/name/scene", index)

    def set_scene_name(self, index, name):
        """ Set the name of a scene. """
        self.live.cmd("/live/name/scene", index, name)

    #------------------------------------------------------------------------
    # /live/name/track
    # /live/name/trackblock
    #------------------------------------------------------------------------

    def get_track_names(self, offset=None, count=None):
        """ Return all track names. If offset and count are given, return names
        within this range. """
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
        """ Return a list of all track names. """
        return self.get_track_names()

    def get_track_name(self, index):
        """ Return a given track's name. """
        return self.live.query("/live/name/track", index)

    def set_track_name(self, index, value):
        """ Set a given track's name. """
        self.live.cmd("/live/name/track", index, value)

    #------------------------------------------------------------------------
    # /live/name/clip
    # /live/name/clipblock
    #------------------------------------------------------------------------

    def get_clip_names(self, track, offset, count):
        """ Return a list of a given set of clip names. """
        return self.live.query("/live/name/clipblock", track, offset, 1, count)

    def get_clip_name(self, track, index):
        """ Return a specific clip name. """
        return self.live.query("/live/name/clip", track, index)[2]

    def set_clip_name(self, track, index, name):
        """ Set a given clip's name. """
        self.live.cmd("/live/name/clip", track, index, name)


    #------------------------------------------------------------------------
    # /live/arm
    #------------------------------------------------------------------------

    def get_track_arm(self, track_index):
        """ Return the armed status of the given track index. """
        return self.live.query("/live/arm", track_index)[1]

    def set_track_arm(self, track_index, arm):
        """ Set the armed status of the given track index. """
        self.live.cmd("/live/arm", track_index, arm)

    #------------------------------------------------------------------------
    # /live/mute
    #------------------------------------------------------------------------

    def get_track_mute(self, track_index):
        return self.live.query("/live/mute", track_index)[1]

    def set_track_mute(self, track_index, mute):
        self.live.cmd("/live/mute", track_index, mute)

    #------------------------------------------------------------------------
    # /live/solo
    #------------------------------------------------------------------------

    def get_track_solo(self, track_index):
        return self.live.query("/live/solo", track_index)[1]

    def set_track_solo(self, track_index, solo):
        self.live.cmd("/live/solo", track_index, solo)

    #------------------------------------------------------------------------
    # /live/volume
    #------------------------------------------------------------------------

    def get_track_volume(self, track_index):
        """ Return the volume of the given track index (0..1). """
        return self.live.query("/live/volume", track_index)[1]

    def set_track_volume(self, track_index, volume):
        """ Set the volume of the given track index (0..1). """
        self.live.cmd("/live/volume", track_index, volume)

    #------------------------------------------------------------------------
    # /live/pan
    #------------------------------------------------------------------------

    def get_track_pan(self, track_index):
        """ Return the pan level of the given track index (-1..1). """
        return self.live.query("/live/pan", track_index)[1]

    def set_track_pan(self, track_index, pan):
        """ Set the pan level of the given track index (-1..1). """
        self.live.cmd("/live/pan", track_index, pan)

    #------------------------------------------------------------------------
    # /live/pan
    #------------------------------------------------------------------------

    def get_track_send(self, track_index, send_index):
        """ Return the send level of send send_index """
        return self.live.query("/live/send", track_index, send_index)[2]

    def set_track_send(self, track_index, send_index, value):
        """ Set send level of send send_index """
        self.live.cmd("/live/send", track_index, send_index, value)

    #------------------------------------------------------------------------
    # /live/pitch
    #------------------------------------------------------------------------

    def get_clip_pitch(self, track_index, clip_index):
        """ Return pitch level of pitch_index for track_index.

        Note that the LiveOSC callback for pitch does not include
        track/clip numbers, so doesn't need slicing. """
        return self.live.query("/live/pitch", track_index, clip_index)

    def set_clip_pitch(self, track_index, pitch_index, coarse, fine):
        """ Set pitch level of pitch_index for track_index. """
        self.live.cmd("/live/pitch", track_index, pitch_index, coarse, fine)

    #------------------------------------------------------------------------
    # /live/master/volume
    # /live/master/pan
    #------------------------------------------------------------------------

    def get_master_volume(self):
        return self.live.query("/live/master/volume")[0]

    def set_master_volume(self, value):
        self.live.cmd("/live/master/volume", value)

    master_volume = property(get_master_volume, set_master_volume, doc="Master volume (0..1)")

    def get_master_pan(self):
        """ Return the master pan level (-1..1). """
        return self.live.query("/live/master/pan")[0]

    def set_master_pan(self, value):
        """ Set the master pan level (-1..1). """
        self.live.cmd("/live/master/pan", value)

    master_pan = property(get_master_pan, set_master_pan, doc="Master pan level (-1..1)")

    #------------------------------------------------------------------------
    # /live/track/info
    #------------------------------------------------------------------------

    def get_track_info(self, track_index):
        """ Return track and clip information for the given track.
        Return value is a tuple of the form:

        (track_index, foldable, armed, (clip_index, state, length), ... )
        """

        return self.live.query("/live/track/info", track_index)

    #------------------------------------------------------------------------
    # /live/clip/info
    # /live/clip/loopend
    #------------------------------------------------------------------------

    def get_clip_info(self, track_index, clip_index):
        return self.live.query("/live/clip/info", track_index, clip_index)

    def set_clip_loop_end(self, track_index, clip_index, loop_end):
        self.live.cmd("/live/clip/loopend", track_index, clip_index, loop_end)

    #------------------------------------------------------------------------
    # /live/clip/mute
    #------------------------------------------------------------------------

    def set_clip_mute(self, track_index, clip_index, mute):
        self.live.cmd("/live/clip/mute", track_index, clip_index, mute)
    def get_clip_mute(self, track_index, clip_index):
        return self.live.query("/live/clip/mute", track_index, clip_index)[2]

    #------------------------------------------------------------------------
    # /live/clip/create
    # /live/clip/delete
    #------------------------------------------------------------------------

    def create_clip(self, track_index, clip_index, length):
        self.live.cmd("/live/clip/create", track_index, clip_index, length)
    def delete_clip(self, track_index, clip_index):
        self.live.cmd("/live/clip/delete", track_index, clip_index)

    #------------------------------------------------------------------------
    # /live/clip/add_note
    # /live/clip/note
    #------------------------------------------------------------------------

    def add_clip_note(self, track_index, clip_index, note, position, duration, velocity, mute):
        self.live.cmd("/live/clip/add_note", track_index, clip_index, note, position, duration, velocity, mute)
    def get_clip_notes(self, track_index, clip_index):
        return self.live.query("/live/clip/notes", track_index, clip_index, response_address="/live/clip/note")

    #------------------------------------------------------------------------
    # /live/devicelist
    # /live/device
    # /live/device/range
    #------------------------------------------------------------------------

    def get_device_list(self, track_index):
        return self.live.query("/live/devicelist", track_index)

    def get_device_parameters(self, track_index, device_index):
        return self.live.query("/live/device", track_index, device_index, response_address="/live/device/allparam")

    def get_device_param(self, track_index, device_index, param_index):
        return self.live.query("/live/device", track_index, device_index, param_index, response_address="/live/device/param")

    def set_device_param(self, track_index, device_index, param_index, value):
        self.live.cmd("/live/device", track_index, device_index, param_index, value)

    def get_device_parameter_ranges(self, track_index, device_index):
        return self.live.query("/live/device/range", track_index, device_index)

    def get_device_parameter_range(self, track_index, device_index, parameter_index):
        return self.live.query("/live/device/range", track_index, device_index, parameter_index)


    #------------------------------------------------------------------------
    # RETURNS
    #------------------------------------------------------------------------

    def get_return_volume(self, return_index):
        """ Return the volume of the given return indkex (0..1). """
        return self.live.query("/live/return/volume", return_index)[1]

    def set_return_volume(self, return_index, volume):
        """ Set the volume of the given return index (0..1). """
        self.live.cmd("/live/return/volume", return_index, volume)



    #------------------------------------------------------------------------
    # SCAN
    #------------------------------------------------------------------------

    def scan(self, scan_scenes=False, scan_devices=False, scan_clip_names=False):
        """ Interrogates the currently open Ableton Live set for its structure:
        number of tracks, clips, scenes, etc.

        For speed, certain elements are not scanned by default:

        scan_scenes -- queries scenes
        scan_devices -- queries tracks for devices and their corresponding parameters
        scan_clip_names -- queries clips for their human-readable names
        """

        #------------------------------------------------------------------------
        # force stop playback before scanning
        #------------------------------------------------------------------------
        self.stop()

        #------------------------------------------------------------------------
        # initialise to empty set of tracks and groups
        #------------------------------------------------------------------------
        self.tracks = []
        self.groups = []

        track_count = self.num_tracks
        if not track_count:
            raise LiveConnectionError("Couldn't connect to Ableton Live! (obj: %s)" % self.live)

        self.log_info("scan_layout: Scanning %d tracks" % track_count)

        #------------------------------------------------------------------------
        # some kind of limit seems to prevent us querying over 535ish track
        # names... let's do them 256 at a time.
        #------------------------------------------------------------------------
        track_index = 0
        track_names = []
        while track_index < track_count:
            tracks_remaining = self.max_tracks_per_query if track_count > track_index + self.max_tracks_per_query else track_count - track_index
            self.log_debug("  (querying from %d, count %d)" % (track_index, tracks_remaining))
            track_names = track_names + self.get_track_names(track_index, tracks_remaining)
            track_index += self.max_tracks_per_query

        self.log_info("scan_layout: Got %d track names" % len(track_names))
        assert(track_count == len(track_names))
        current_group = None

        for track_index in range(track_count):
            track_name = track_names[track_index]
            self.log_info("scan_layout: Track %d (%s)" % (track_index, track_name))
            track_info = self.get_track_info(track_index)
            is_group = track_info[1]
            if is_group:
                self.log_info("scan_layout: - is group")
                group_index = len(self.groups)
                group = Group(self, track_index, group_index, track_name)
                current_group = group
                self.groups.append(group)

                #------------------------------------------------------------------------
                # we also need to add this group to the tracks list, as live's events
                # assume that groups are tracks and address their indices accordingly.
                #------------------------------------------------------------------------
                self.tracks.append(group)

            else:
                track = Track(self, track_index, track_name, current_group)
                if current_group is not None:
                    current_group.tracks.append(track)
                self.tracks.append(track)

                clip_info = track_info[3:]

                if scan_clip_names:
                    clip_names = self.get_clip_names
                for n in range(0, len(clip_info), 3):
                    clip_index = int(n / 3)
                    state = clip_info[n + 1]
                    length = clip_info[n + 2]
                    if state > 0:
                        track.clips[clip_index] = Clip(track, clip_index, length)
                        track.clips[clip_index].state = state
                        track.clips[clip_index].indent = 3 if track.group else 2

                        #--------------------------------------------------------------------------
                        # if this track is in a group, create a Clip object inside the group
                        # that can be triggered to play group scenes.
                        #--------------------------------------------------------------------------
                        if current_group:
                            while len(current_group.clips) <= clip_index:
                                current_group.clips.append(None)
                            current_group.clips[clip_index] = Clip(current_group, clip_index, length)
                            current_group.clips[clip_index].state = state

                        if not track.clip_init:
                            track.clip_init = clip_index
    
                        #--------------------------------------------------------------------------
                        # scan for clip names.
                        # is nice, but slows things down significantly -- so disable by default.
                        #--------------------------------------------------------------------------
                        if scan_clip_names:
                            clip_name = self.get_clip_name(track.index, clip_index)
                            track.clips[clip_index].name = clip_name
                            self.log_info("scan_layout:  - Clip %d: %s" % (clip_index, clip_name))

                #--------------------------------------------------------------------------
                # query each track for its device list, and any parameters belonging to
                # each device.
                #--------------------------------------------------------------------------
                if scan_devices:
                    devices = self.get_device_list(track.index)
                    self.log_info("scan_layout: Devices %s" % devices)
                    devices = devices[1:]
                    for i in range(0, len(devices), 2):
                        index = devices[i]
                        name = devices[i + 1]
                        device = Device(track, index, name)
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
                            param = Parameter(device, index, name, value)
                            param.minimum = minimum
                            param.maximum = maximum
                            device.parameters.append(param)

        #--------------------------------------------------------------------------
        # now scan scenes
        #--------------------------------------------------------------------------
        scene_count = self.num_scenes
        scene_names = self.scene_names
        for index, scene_name in enumerate(scene_names):
            scene = Scene(self, index)
            scene.name = scene_name
            self.scenes.append(scene)
        
        self.scanned = True

    def load_or_scan(self, filename="set", **kwargs):
        """ From from file; if file does not exist, scan, then save. """
        try:
            set_file = self.currently_open()
            if set_file:
                set_file_mtime = os.path.getmtime(set_file)
                cache_file_mtime = os.path.getmtime("%s.pickle" % filename)
                if cache_file_mtime < set_file_mtime:
                    self.log_info("Set file modified since cache, forcing rescan")
                    raise Exception
            else:
                self.log_info("Couldn't establish currently open set")

            self.load(filename)
            if len(self.tracks) != self.num_tracks:
                self.log_info("Loaded %d tracks, but found %d - looks like set has changed" % (len(self.tracks), self.num_tracks))
                self.reset()
                raise Exception
        except Exception as e:
            self.scan(**kwargs)
            self.save(filename)

    def load(self, filename="set"):
        """ Read a saved Set structure from disk. """
        filename = "%s.pickle" % filename
        try:
            data = pickle.load(open(filename, "rb"))
        except pickle.UnpicklingError:
            raise LiveIOError
        except KeyError:
            # Python 2 throws a KeyError
            raise LiveIOError

        for key, value in list(data.items()):
            setattr(self, key, value)
        self.log_info("load: Set loaded OK (%d tracks)" % (len(self.tracks)))

        #------------------------------------------------------------------------
        # After loading, set all active clip states to stopped.
        # Otherwise, if we scanned during playback, it will erroneously appear
        # as if stopped clips are playing.
        #------------------------------------------------------------------------
        self._reset_clip_states()

        #------------------------------------------------------------------------
        # re-add unserialisable mutexes.
        #------------------------------------------------------------------------
        self._add_mutexes()

    def save(self, filename="set"):
        """ Save the current Set structure to disk.
        Use to avoid the lengthy scan() process.
        TODO: Add a __reduce__ function to do this in an idiomatic way. """
        filename = "%s.pickle" % filename
        fd = open(filename, "wb")
        self._delete_mutexes()
        data = vars(self)

        pickle.dump(data, fd)

        #------------------------------------------------------------------------
        # Restore the unpickleables
        #------------------------------------------------------------------------
        self._add_mutexes()

        self.log_info("save: Set saved OK (%s)" % filename)

    def dump(self):
        """ Dump the current Set structure to stdout, showing the hierarchy of
        Group, Track, Clip, Device and Parameter objects. """
        if len(self.tracks) == 0:
            self.log_info("dump: currently empty, performing scan")
            self.scan()

        print("────────────────────────────────────────────────────────")
        print("Live set with %d tracks in %d groups, total %d clips" %
            (len(self.tracks), len(self.groups), sum(len(track.clips) for track in self.tracks)))
        print("────────────────────────────────────────────────────────")
        current_group = None

        for track in self.tracks:
            if track.is_group:
                print("────────────────────────────────────────")
                print(str(track))
                current_group = track
            else:
                print(" - %s" % str(track))
                if track.devices:
                    for device in track.devices:
                        print("    - %s" % device)
                if track.active_clips:
                    for clip in track.active_clips:
                        print("    - %s" % clip)

        print("────────────────────────────────────────────────────────")
        print("Scenes")
        print("────────────────────────────────────────────────────────")

        for scene in self.scenes:
            print(" - %s" % scene)

    def get_track_named(self, name):
        """ Returns the Track with the specified name, or None if not found. """
        for track in self.tracks:
            if track.name == name:
                return track
        return None

    def get_group_named(self, name):
        """ Returns the Group with the specified name, or None if not found. """
        for group in self.groups:
            if group.name == name:
                return group
        return None

    def _next_beat_callback(self, beats):
        self._next_beat_event.set()
    
    def wait_for_next_beat(self):
        #------------------------------------------------------------------------
        # we need to use events to prevent lockup -- if we call a callback
        # directly from the Live thread that makes another query to the Live
        # server, the first event will never become unlocked and we'll block
        # forever.
        #------------------------------------------------------------------------
        self._next_beat_event.clear()
        self.live.beat_callback = self._next_beat_callback

        #------------------------------------------------------------------------
        # don't want to use .wait() as it prevents response to keyboard input
        # so ctrl-c will not work.
        #------------------------------------------------------------------------
        while not self._next_beat_event.is_set():
            time.sleep(0.01)

        return

    def set_beat_callback(self, callback):
        self.live.beat_callback = callback

    def startup_callback(self):
        self._startup_event.set()

    def wait_for_startup(self):
        self._startup_event.clear()
        self.live.startup_callback = self.startup_callback

        # don't want to use .wait() as it prevents response to keyboard input
        # so ctrl-c will not work.
        try:
            #------------------------------------------------------------------------
            # if we can query tempo, the set is running
            #------------------------------------------------------------------------
            tempo = self.live.query("/live/tempo", timeout=0.1)
        except LiveConnectionError:
            #------------------------------------------------------------------------
            # otherwise, wait for set startup
            #------------------------------------------------------------------------
            while not self._startup_event.is_set():
                time.sleep(0.01)

        return

    def _add_mutexes(self):
        self._next_beat_event = threading.Event()
        self._startup_event = threading.Event()

    def _delete_mutexes(self):
        self._next_beat_event = None
        self._startup_event = None

    def _add_handlers(self):
        self.live.add_handler("/live/clip/info", self._update_clip_state)
        self.live.add_handler("/live/tempo", self._update_tempo)

    def _update_tempo(self, tempo):
        self.set_tempo(tempo, cache_only = True)
    
    def _reset_clip_states(self):
        for track in self.tracks:
            for clip in track.active_clips:
                clip.state = CLIP_STATUS_STOPPED

    def _update_clip_state(self, track_index, clip_index, state):
        if not self.scanned:
            return
        track = self.tracks[track_index]

        # can get a clip_info for clips outside of our clip range
        # (eg updating the status of a "stop" clip when we play a whole scene)
        if clip_index < len(track.clips):
            clip = track.clips[clip_index]
            if clip:
                clip.state = state
