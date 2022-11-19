# -*- coding: utf-8 -*-

import os
import glob
import time
import pickle
import logging
import threading
import subprocess
from typing import Optional

from .clip import Clip
from .query import Query
from .track import Track
from .group import Group
from .scene import Scene
from .device import Device
from .parameter import Parameter
from .constants import CLIP_STATUS_STOPPED
from .exceptions import LiveIOError, LiveConnectionError

def make_getter(class_identifier, prop):
    # TODO: Replacement for name_cache
    def fn(self):
        return self.live.query("/live/%s/get/%s" % (class_identifier, prop))[0]

    return fn

def make_setter(class_identifier, prop):
    def fn(self, value):
        self.live.cmd("/live/%s/set/%s" % (class_identifier, prop), value)

    return fn

class Set:
    """
    Set represents an entire Live set. It communicates via OSC to Live,
    which must be running AbletonOSC as an active control surface.

    A Set contains a number of Track objects, which may optionally have a
    parent Group. Each Track object contains one or more Clip objects, and
    one or more Devices, each of which possess Parameters.

    A Set object is initially unpopulated, and must interrogate the Live set
    for its contents by calling the scan() method.
    """

    def __init__(self):
        #--------------------------------------------------------------------------
        # Indicates whether the set has been synchronised with Live
        #--------------------------------------------------------------------------
        self.scanned = False

        #--------------------------------------------------------------------------
        # Set caching to True to avoid re-querying properties such as tempo each
        # time they are requested. Increases efficiency in cases where no other
        # processes are going to modify Live's state.
        #--------------------------------------------------------------------------
        self.caching = False

        #--------------------------------------------------------------------------
        # For batch queries, limit the max number of tracks to query.
        #--------------------------------------------------------------------------
        self.max_tracks_per_query = 256

        #--------------------------------------------------------------------------
        # Create mutexes and events for inter-thread handling (to catch on-beat
        # events, etc)
        #--------------------------------------------------------------------------
        self._add_mutexes()

        self.logger = logging.getLogger(__name__)

        self.groups: list[Group] = []
        self.tracks: list[Track] = []
        self.scenes: list[Scene] = []
        self.reset()

    def __str__(self):
        return "Set"

    def reset(self):
        self.groups = []
        self.tracks = []
        self.scenes = []

    def open(self, filename: str, wait_for_startup: bool = True):
        """
        Open an Ableton project, either by the path to the Project directory or
        to an .als file. Will search in the current directory and the contents of
        the LIVE_ROOT environmental variable.

        Will only work with OS X right now as it presupposes an /Applications/*.app
        format for the Live app.

        wait = True: block until the set is loaded (waits for a LiveOSC trigger)
        """

        paths = ["."]
        if "LIVE_ROOT" in os.environ:
            paths.append(os.environ["LIVE_ROOT"])

        #------------------------------------------------------------------------
        # Iterate through each path searching for the project file.
        #------------------------------------------------------------------------
        path = None
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
            self.logger.info("Project '%s' is already open" % os.path.basename(path))
            return

        if not os.path.exists(path):
            raise LiveIOError("Couldn't find project file '%s'. Have you set the LIVE_ROOT environmental variable?")

        #------------------------------------------------------------------------
        # Assume that the alphabetically-last Ableton binary is the one we 
        # want (ie, greatest version number.)
        #------------------------------------------------------------------------
        ableton = sorted(glob.glob("/Applications/Ableton*.app"))[-1]
        subprocess.call(["open", "-a", ableton, path])

        if wait_for_startup:
            self.wait_for_startup()
        return True

    def _get_last_opened_set_filename(self) -> Optional[str]:
        #------------------------------------------------------------------------
        # Parse Live's CrashRecoveryInfo file to obtain the pathname of
        # the currently-open set.
        #------------------------------------------------------------------------
        root = os.path.expanduser("~/Library/Preferences/Ableton")
        logfiles = glob.glob("%s/Live */CrashRecoveryInfo.cfg" % root)

        if logfiles:
            logfiles = list(sorted(logfiles, key=lambda a: os.path.getmtime(a)))
            logfile = logfiles[-1]

            with open(logfile, "rb") as fd:
                data = fd.read()
                for i in range(len(data) - 4):
                    #------------------------------------------------------------------------
                    # Locate the array of bytes which indicates the start of the set
                    # pathname.
                    #------------------------------------------------------------------------
                    if data[i:i + 4] == bytes([0x44, 0x00, 0x12, 0x00]):
                        data = data[i + 5:]
                        data = data[:data.index(0x00)]
                        path = "/" + data.decode("utf8")
                        return path

        return None

    def currently_open(self) -> Optional[str]:
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
    def live(self) -> Query:
        return Query()

    @property
    def is_connected(self) -> bool:
        """ Test whether we can connect to Live """
        try:
            return bool(self.tempo)
        except Exception as e:
            return False

    #------------------------------------------------------------------------
    # Properties
    #------------------------------------------------------------------------

    tempo = property(make_getter("song", "tempo"),
                     make_setter("song", "tempo"),
                     doc="Global tempo")

    metronome = property(make_getter("song", "metronome"),
                         make_setter("song", "metronome"),
                         doc="Global metronome")

    clip_trigger_quantization = property(make_getter("song", "clip_trigger_quantization"),
                                         make_setter("song", "clip_trigger_quantization"),
                                         doc="Global quantization")

    current_song_time = property(make_getter("song", "current_song_time"),
                                 make_setter("song", "current_song_time"),
                                 doc="Current song time (in beats)")

    arrangement_overdub = property(make_getter("song", "arrangement_overdub"),
                                   make_setter("song", "arrangement_overdub"),
                                   doc="Arrangement overdub")

    #--------------------------------------------------------------------------------
    # Start/stop playback
    #--------------------------------------------------------------------------------

    def start_playing(self) -> None:
        self.live.cmd("/live/song/start_playing")

    def continue_playing(self) -> None:
        self.live.cmd("/live/song/continue_playing")

    def stop_playing(self) -> None:
        self.live.cmd("/live/song/stop_playing")

    def stop_all_clips(self) -> None:
        self.live.cmd("/live/song/stop_all_clips")

    is_playing = property(make_getter("song", "is_playing"),
                          doc="Whether the song is playing")

    #--------------------------------------------------------------------------------
    # Undo/redo
    #--------------------------------------------------------------------------------

    can_undo = property(make_getter("song", "can_undo"),
                        doc="Whether an undo operation is possible")
    can_redo = property(make_getter("song", "can_redo"),
                        doc="Whether a redo operation is possible")

    def undo(self) -> None:
        """
        Undo the last operation.
        """
        self.live.cmd("/live/undo")

    def redo(self) -> None:
        """
        Redo the last undone operation.
        """
        self.live.cmd("/live/redo")

    #--------------------------------------------------------------------------------
    # Tracks
    #--------------------------------------------------------------------------------

    num_tracks = property(make_getter("song", "num_tracks"),
                          doc="Number of tracks")

    def create_audio_track(self, track_index: int) -> None:
        """
        Creates a new audio track by index.

        Args:
            track_index: The index of the track to create. If -1, creates after the last existing track.
        """
        self.live.cmd("/live/song/create_audio_track", track_index)

    def create_midi_track(self, track_index: int) -> None:
        """
        Creates a new MIDI track by index.

        Args:
            track_index: The index of the track to create. If -1, creates after the last existing track.
        """
        self.live.cmd("/live/song/create_midi_track", track_index)

    def duplicate_track(self, track_index: int) -> None:
        """
        Duplicate a track.

        Args:
            track_index: The index of the track to delete.
        """
        self.live.cmd("/live/song/duplicate_track", track_index)

    def delete_track(self, track_index: int) -> None:
        """
        Delete track by index.

        Args:
            track_index: The index of the track to delete.
        """
        self.live.cmd("/live/song/delete_track", track_index)

    def delete_return_track(self, track_index: int) -> None:
        """
        Delete return track by index.

        Args:
            track_index: The index of the return track to delete.
        """
        self.live.cmd("/live/song/delete_return_track", track_index)

    def get_track_named(self, name: str) -> Optional[Track]:
        """
        Returns the Track with the specified name, or None if not found.

        Args:
            name: The name of the track to locate.
        """
        for track in self.tracks:
            if track.name == name:
                return track
        return None

    def get_group_named(self, name: str) -> Optional[Group]:
        """
        Returns the Group with the specified name, or None if not found.

        Args:
            name: The name of the group to locate.
        """
        for group in self.groups:
            if group.name == name:
                return group
        return None

    #--------------------------------------------------------------------------------
    # Scenes
    #--------------------------------------------------------------------------------

    num_scenes = property(make_getter("song", "num_scenes"),
                          doc="Number of scenes")

    def create_scene(self, scene_index: int) -> None:
        """
        Creates a new scene by an index.

        Args:
            scene_index: The index of the scene to create. If -1, the scene is created after the last scene.
        """
        self.live.cmd("/live/song/create_scene", scene_index)

    def delete_scene(self, scene_index: int) -> None:
        """
        Delete the scene at the specified index.

        Args:
            scene_index: The index of the scene to delete.
        """
        self.live.cmd("/live/song/delete_scene", scene_index)

    #------------------------------------------------------------------------
    # TODO: Master volume
    #------------------------------------------------------------------------

    master_volume = property(make_getter("song", "master_volume"),
                             make_setter("song", "master_volume"),
                             doc="Master volume (0..1)")
    master_pan = property(make_getter("song", "master_pan"),
                          make_setter("song", "master_pan"),
                          doc="Master pan (-1..1)")

    #--------------------------------------------------------------------------------
    # Cues
    # TODO: Refactor cues
    #--------------------------------------------------------------------------------
    def prev_cue(self):
        """
        Jump to the previous cue.
        """
        self.live.cmd("/live/prev/cue")

    def next_cue(self):
        """
        Jump to the next cue.
        """
        self.live.cmd("/live/next/cue")

    #------------------------------------------------------------------------
    # SCAN
    #------------------------------------------------------------------------

    def scan(self, scan_scenes: bool = False, scan_devices: bool = False, scan_clip_names: bool = False):
        """
        Interrogates the currently open Ableton Live set for its structure:
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

        self.logger.info("scan_layout: Scanning %d tracks" % track_count)

        #------------------------------------------------------------------------
        # some kind of limit seems to prevent us querying over 535ish track
        # names... let's do them 256 at a time.
        #------------------------------------------------------------------------
        track_index = 0
        track_names = []
        while track_index < track_count:
            tracks_remaining = self.max_tracks_per_query if track_count > track_index + self.max_tracks_per_query else track_count - track_index
            self.logger.debug("  (querying from %d, count %d)" % (track_index, tracks_remaining))
            track_names = track_names + self.get_track_names(track_index, tracks_remaining)
            track_index += self.max_tracks_per_query

        self.logger.info("scan_layout: Got %d track names" % len(track_names))
        assert (track_count == len(track_names))
        current_group = None

        for track_index in range(track_count):
            track_name = track_names[track_index]
            self.logger.info("scan_layout: Track %d (%s)" % (track_index, track_name))
            track_info = self.get_track_info(track_index)
            is_group = track_info[1]
            if is_group:
                self.logger.info("scan_layout: - is group")
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
                    clip_names = self.get_clip_names(track_index, 0, len(clip_info) // 3)
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
                        # Scan for clip names.
                        # Is nice, but slows things down somewhat -- so disable by default.
                        #--------------------------------------------------------------------------
                        if scan_clip_names:
                            track.clips[clip_index].name = clip_names[clip_index]
                            self.logger.info("scan_layout:  - Clip %d: %s" % (clip_index, track.clips[clip_index].name))

                #--------------------------------------------------------------------------
                # Query each track for its device list, and any parameters belonging to
                # each device.
                #--------------------------------------------------------------------------
                if scan_devices:
                    devices = self.get_device_list(track.index)
                    self.logger.info("scan_layout: Devices %s" % devices)
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
                            index = parameters[j + 0]
                            value = parameters[j + 1]
                            name = parameters[j + 2]
                            minimum = ranges[j + 1]
                            maximum = ranges[j + 2]
                            param = Parameter(device, index, name, value)
                            param.minimum = minimum
                            param.maximum = maximum
                            device.parameters.append(param)

        #--------------------------------------------------------------------------
        # now scan scenes
        #--------------------------------------------------------------------------
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
                    self.logger.info("Set file modified since cache, forcing rescan")
                    raise Exception
            else:
                self.logger.info("Couldn't establish currently open set")

            self.load(filename)
            if len(self.tracks) != self.num_tracks:
                self.logger.info("Loaded %d tracks, but found %d - looks like set has changed" % (len(self.tracks), self.num_tracks))
                self.reset()
                raise Exception
        except Exception as e:
            self.scan(**kwargs)
            self.save(filename)

    def load(self, filename: str = "set"):
        """
        Read a saved Set structure from disk.
        """
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
        self.logger.info("load: Set loaded OK (%d tracks)" % (len(self.tracks)))

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

    def save(self, filename: str = "set"):
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

        self.logger.info("save: Set saved OK (%s)" % filename)

    def dump(self):
        """
        Dump the current Set structure to stdout, showing the hierarchy of
        Group, Track, Clip, Device and Parameter objects.
        """
        if len(self.tracks) == 0:
            self.logger.info("dump: currently empty, performing scan")
            self.scan()

        print("────────────────────────────────────────────────────────")
        print("Live set with %d tracks in %d groups, total %d clips" %
              (len(self.tracks), len(self.groups), sum(len(track.clips) for track in self.tracks)))
        print("────────────────────────────────────────────────────────")

        for track in self.tracks:
            if track.is_group:
                print("────────────────────────────────────────")
                print(str(track))
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
            tempo = self.live.query("/live/song/get/tempo", timeout=0.1)
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

    def _update_tempo(self, tempo):
        pass
        # self.set_tempo(tempo, cache_only=True)

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
