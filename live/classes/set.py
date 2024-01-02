import re
import os
import sys
import math
import glob
import json
import time
import pickle
import logging
import tempfile
import threading
import subprocess
from typing import Optional

from .clip import Clip
from .track import Track
from .group import Group
from .scene import Scene
from .device import Device
from .parameter import Parameter
from ..query import Query
from ..constants import CLIP_STATUS_STOPPED
from ..exceptions import LiveIOError, LiveConnectionError

def make_getter(class_identifier, prop):
    # TODO: Replacement for name_cache
    def fn(self):
        return self.live.query("/live/%s/get/%s" % (class_identifier, prop))[0]

    return fn

def make_setter(class_identifier, prop):
    def fn(self, value):
        self.live.cmd("/live/%s/set/%s" % (class_identifier, prop), (value,))

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

    def __init__(self, scan: bool = False):
        """
        Create a new Set object.
        If scan is True, automatically connects to Live and queries the full set of tracks,
        clips and devices in the set.

        Args:
            scan: If True, automatically scans the contents of the set.
        """
        # --------------------------------------------------------------------------
        # Indicates whether the set has been synchronised with Live
        # --------------------------------------------------------------------------
        self.scanned = False

        # --------------------------------------------------------------------------
        # Set caching to True to avoid re-querying properties such as tempo each
        # time they are requested. Increases efficiency in cases where no other
        # processes are going to modify Live's state.
        # --------------------------------------------------------------------------
        self.caching = False

        # --------------------------------------------------------------------------
        # For batch queries, limit the max number of tracks to query.
        # --------------------------------------------------------------------------
        self.max_tracks_per_query = 256

        # --------------------------------------------------------------------------
        # Create mutexes and events for inter-thread handling (to catch on-beat
        # events, etc)
        # --------------------------------------------------------------------------
        self._add_mutexes()

        self.logger = logging.getLogger(__name__)
        self.live = Query()

        self.groups: list[Group] = []
        self.tracks: list[Track] = []
        self.scenes: list[Scene] = []
        self.reset()

        if scan:
            self.scan()

        self.start_beat_listener()

    def __str__(self):
        return "Set"

    def __getstate__(self):
        return {
            "groups": self.groups,
            "tracks": self.tracks,
            "scenes": self.scenes,
        }

    def __setstate__(self, d: dict):
        self.groups = d["groups"]
        self.tracks = d["tracks"]
        self.scenes = d["scenes"]

    def reset(self):
        self.groups = []
        self.tracks = []
        self.scenes = []

    # --------------------------------------------------------------------------------
    # SCAN
    # --------------------------------------------------------------------------------

    def scan(self, mode: str = "auto") -> None:
        """
        Queries the currently-open Live set and populates this Set's list of
        tracks, clips, devices etc.

        Args:
            mode: Can be one of "auto", "file" or "network".
                  "file" exports the set's contents using a local .json file.
                         This is the fastest approach, but does not work if Live is running on a different computer.
                  "network" queries the set's contents via OSC.
                         This is slower, but can be used if Live is on a different computer.
                  "auto" uses "file" for a local install, and "network" for a remote instance.
        """

        if mode == "auto" or mode == "local":
            self._scan_via_file()
        elif mode == "network":
            self._scan_via_network()
        else:
            raise ValueError("Invalid value for 'mode': %s" % mode)

    def _scan_via_network(self,
                          scan_device_parameters: bool = False) -> None:
        """
        Interrogates the currently open Ableton Live set for its structure:
        number of tracks, clips, scenes, etc.

        For speed, certain elements are not scanned by default.

        Args:
            scan_device_parameters: Queries tracks for devices and their corresponding parameters
        """

        # --------------------------------------------------------------------------------
        # Stop playback before scanning, and clear existing tracks/groups
        # --------------------------------------------------------------------------------
        self.stop_playing()
        self.tracks = []
        self.groups = []

        # --------------------------------------------------------------------------------
        # Determine total number of tracks/scenes
        # --------------------------------------------------------------------------------
        num_tracks = self.num_tracks
        num_scenes = self.num_scenes
        if num_tracks is None or num_scenes is None:
            raise LiveConnectionError("Couldn't connect to Ableton Live! (obj: %s)" % self.live)

        self.logger.info("scan: Scanning %d tracks" % num_tracks)

        tracks_per_block = 1
        num_track_blocks = int(math.ceil(num_tracks / tracks_per_block))

        # --------------------------------------------------------------------------------
        # Scan tracks
        # --------------------------------------------------------------------------------
        for track_block_index in range(num_track_blocks):
            track_index_min = track_block_index * tracks_per_block
            track_index_max = min(track_index_min + tracks_per_block, num_tracks)
            tracks_in_block = track_index_max - track_index_min

            self.logger.debug(" - Scanning tracks %d-%d" % (track_index_min, track_index_max))
            rv = self.live.query("/live/song/get/track_data", (
                track_index_min, track_index_max, "track.name", "track.is_foldable", "track.group_track"))
            for track_index_in_block in range(tracks_in_block):
                track_index = track_index_min + track_index_in_block
                track_offset = track_index_in_block * 3
                track_name, track_is_group, track_group_track = rv[track_offset:track_offset + 3]
                track_group = self.tracks[track_group_track] if track_group_track is not None else None
                if track_is_group:
                    group_index = len(self.groups)
                    group = Group(self, track_index, group_index, track_name, track_group)
                    self.tracks.append(group)
                    self.groups.append(group)
                else:
                    track = Track(self, track_index, track_name, track_group)
                    self.tracks.append(track)
                    if track_group:
                        track_group.tracks.append(track)

            # --------------------------------------------------------------------------------
            # Scan clips
            # --------------------------------------------------------------------------------
            self.logger.debug(" - Scanning tracks %d-%d: clips" % (track_index_min, track_index_max))
            rv = self.live.query("/live/song/get/track_data",
                                 (track_index_min, track_index_max, "clip.name", "clip.length"))
            for track_index_in_block in range(tracks_in_block):
                track_index = track_index_min + track_index_in_block
                track = self.tracks[track_index]
                clips_data = rv[(track_index_in_block * 2 * num_scenes):((track_index_in_block + 1) * 2 * num_scenes)]
                clip_names = clips_data[0:num_scenes]
                clip_lengths = clips_data[num_scenes:num_scenes * 2]
                for clip_index, (clip_name, clip_length) in enumerate(zip(clip_names, clip_lengths)):
                    if clip_name is not None:
                        clip = Clip(track, clip_index, clip_name, clip_length)
                        track.clips[clip_index] = clip
                        if track.group is not None and track.group.clips[clip_index] is None:
                            track.group.clips[clip_index] = Clip(track.group, clip_index, "", clip_length)

            # --------------------------------------------------------------------------------
            # Scan devices
            # --------------------------------------------------------------------------------
            self.logger.debug(" - Scanning tracks %d-%d: devices" % (track_index_min, track_index_max))
            rv = self.live.query("/live/song/get/track_data",
                                 (track_index_min, track_index_max, "track.num_devices", "device.name"))
            rv_index = 0
            for track_index_in_block in range(tracks_in_block):
                track_index = track_index_min + track_index_in_block
                track = self.tracks[track_index]
                device_count = rv[rv_index]
                rv_index += 1
                for device_index in range(device_count):
                    device_name = rv[rv_index]
                    rv_index += 1
                    device = Device(track, device_index, device_name)

                    if scan_device_parameters:
                        rv_num_params = self.live.query("/live/device/get/num_parameters", (track_index, device_index))[2:]
                        rv_param_names = self.live.query("/live/device/get/parameters/name", (track_index, device_index))[2:]
                        rv_param_values = self.live.query("/live/device/get/parameters/value", (track_index, device_index))[2:]
                        rv_param_min = self.live.query("/live/device/get/parameters/min", (track_index, device_index))[2:]
                        rv_param_max = self.live.query("/live/device/get/parameters/max", (track_index, device_index))[2:]
                        rv_param_quantized = self.live.query("/live/device/get/parameters/is_quantized",
                                                             (track_index, device_index))[2:]

                        all_parameters = []

                        for i in range(rv_num_params[0]):
                            all_parameters.append({
                                "name": rv_param_names[i],
                                "value": rv_param_values[i],
                                "min": rv_param_min[i],
                                "max": rv_param_max[i],
                                "is_quantized": rv_param_quantized[i]
                            })

                        device.parameters = []
                        for parameter_index, parameter_data in enumerate(all_parameters):
                            parameter = Parameter(device, parameter_index, parameter_data["name"], parameter_data["value"])
                            parameter.min = parameter_data["min"]
                            parameter.max = parameter_data["max"]
                            parameter.is_quantized = parameter_data["is_quantized"]
                            device.parameters.append(parameter)

                    track.devices.append(device)

        self.scanned = True

    def _scan_via_file(self) -> None:
        """
        Scans the contents of the Live set by exporting the song structure to a local .json file.
        Note that this will not work if the Live set is running on another system, i.e. over a network.
        """
        rv = self.live.query("/live/song/export/structure")
        assert rv[0] == 1

        self.tracks = []
        self.groups = []

        if sys.platform == "darwin":
            #--------------------------------------------------------------------------------
            # On macOS, tempfile.gettempdir() uses a process-specific directory.
            # Use global temp dir (/tmp) as this is the directory used by AbletonOSC.
            #--------------------------------------------------------------------------------
            tempdir = "/tmp"
        else:
            tempdir = tempfile.gettempdir()
        json_path = os.path.join(tempdir, "abletonosc-song-structure.json")

        with open(json_path, "r") as fd:
            data = json.load(fd)
            tracks = data["tracks"]
            for track_data in tracks:
                track_group = self.tracks[track_data["group_track"]] if track_data["group_track"] is not None else None
                if track_data["is_foldable"]:
                    group_index = len(self.groups)
                    group = Group(self, track_data["index"], group_index, track_data["name"], track_group)
                    self.tracks.append(group)
                    self.groups.append(group)
                else:
                    track = Track(self, track_data["index"], track_data["name"], track_group)
                    self.tracks.append(track)
                    if track_group:
                        track_group.tracks.append(track)

                for clip_data in track_data["clips"]:
                    clip = Clip(track, clip_data["index"], clip_data["name"], clip_data["length"])
                    track.clips[clip.index] = clip
                    if track.group is not None and track.group.clips[clip.index] is None:
                        track.group.clips[clip.index] = Clip(track.group, clip.index, "", clip.length)

                for device_index, device_data in enumerate(track_data["devices"]):
                    device = Device(track, device_index, device_data["name"])
                    device.parameters = []
                    for parameter_index, parameter_data in enumerate(device_data["parameters"]):
                        parameter = Parameter(device, parameter_index, parameter_data["name"], parameter_data["value"])
                        parameter.min = parameter_data["min"]
                        parameter.max = parameter_data["max"]
                        parameter.is_quantized = parameter_data["is_quantized"]
                        device.parameters.append(parameter)
                    track.devices.append(device)

        self.scanned = True

        num_tracks = len(self.tracks)
        num_clips = sum([len(track.active_clips) for track in self.tracks])
        self.logger.info("Discovered %d clips in %d tracks" % (num_clips, num_tracks))

    def load_or_scan(self, filename: str = "set", **kwargs):
        """
        Load from file; if file does not exist, scan, then save.
        """
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
                self.logger.info(
                    "Loaded %d tracks, but found %d - looks like set has changed" % (len(self.tracks), self.num_tracks))
                self.reset()
                raise LiveIOError
        except (EOFError, LiveIOError) as e:
            self.scan(**kwargs)
            self.save(filename)

    def load(self, filename: str = "set"):
        """
        Read a saved Set structure from disk.
        """
        filename = "%s.pickle" % filename
        try:
            data = pickle.load(open(filename, "rb"))
        except (pickle.UnpicklingError, FileNotFoundError):
            raise LiveIOError

        self.__setstate__(data.__dict__)
        self.logger.info("load: Set loaded OK (%d tracks)" % (len(self.tracks)))

        # ------------------------------------------------------------------------
        # After loading, set all active clip states to stopped.
        # Otherwise, if we scanned during playback, it will erroneously appear
        # as if stopped clips are playing.
        # ------------------------------------------------------------------------
        self._reset_clip_states()

        # ------------------------------------------------------------------------
        # re-add unserialisable mutexes.
        # ------------------------------------------------------------------------
        self._add_mutexes()

    def save(self, filename: str = "set"):
        """
        Save the current Set structure to disk.
        Use to avoid the lengthy scan() process.
        TODO: Add a __reduce__ function to do this in an idiomatic way.
        TODO: Do we still need this now scanning is fast?
        """
        filename = "%s.pickle" % filename
        with open(filename, "wb") as fd:
            pickle.dump(self, fd)

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
              (len(self.tracks), len(self.groups), sum(len(track.active_clips) for track in self.tracks)))
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
        # ------------------------------------------------------------------------
        # we need to use events to prevent lockup -- if we call a callback
        # directly from the Live thread that makes another query to the Live
        # server, the first event will never become unlocked and we'll block
        # forever.
        # ------------------------------------------------------------------------
        self._next_beat_event.clear()
        self.live.beat_callback = self._next_beat_callback

        # ------------------------------------------------------------------------
        # don't want to use .wait() as it prevents response to keyboard input
        # so ctrl-c will not work.
        # ------------------------------------------------------------------------
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
            # ------------------------------------------------------------------------
            # if we can query tempo, the set is running
            # ------------------------------------------------------------------------
            tempo = self.live.query("/live/song/get/tempo", timeout=0.1)
        except LiveConnectionError:
            # ------------------------------------------------------------------------
            # otherwise, wait for set startup
            # ------------------------------------------------------------------------
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

    def open(self, filename: str, wait_for_startup: bool = True):
        """
        Open an Ableton project, either by the path to the Project directory or
        to an .als file. Will search in the current directory and the contents of
        the LIVE_ROOT environmental variable.

        Will only work with OS X right now as it presupposes an /Applications/*.app
        format for the Live app.

        wait_for_startup = True: block until the set is loaded (waits for a LiveOSC trigger)
        """

        paths = ["."]
        if "LIVE_ROOT" in os.environ:
            paths.append(os.environ["LIVE_ROOT"])

        # ------------------------------------------------------------------------
        # Iterate through each path searching for the project file.
        # ------------------------------------------------------------------------
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

        if not os.path.exists(path):
            raise LiveIOError("Couldn't find project file '%s'" % path)

        path_abs = os.path.abspath(path)
        path_current = self.get_open_set_filename()
        if path_abs is not None and path_current == path_abs:
            self.logger.info("Project '%s' is already open" % os.path.basename(path))
            return

        # ------------------------------------------------------------------------
        # Assume that the alphabetically-last Ableton binary is the one we 
        # want (ie, greatest version number.)
        # ------------------------------------------------------------------------
        ableton = sorted(glob.glob("/Applications/Ableton*.app"))[-1]
        subprocess.call(["open", "-a", ableton, path])

        if wait_for_startup:
            self.wait_for_startup()
        return True

    def _get_last_opened_set_filename(self) -> Optional[str]:
        """
        Parse Live's Log.txt to obtain the pathname of the last-opened set.
        Tested on Live 11.2.

        Returns:
            str: The absolute path to the last-opened set, or None if no log entry
                 is found. Note that the set may not still be open!
        """
        root = os.path.expanduser("~/Library/Preferences/Ableton")
        log_path_wildcard = os.path.join(root, "Live *", "Log.txt")
        log_paths = glob.glob(log_path_wildcard)

        if log_paths:
            log_paths = list(sorted(log_paths, key=lambda a: os.path.getmtime(a)))
            log_path = log_paths[-1]

            # Match any document-load events that are *not* loads of MIDI Track (etc) defaults
            pattern = r'Loading document "([^"]+)"'
            antipattern = r"/Defaults/"
            with open(log_path, "r") as fd:
                for line in reversed(fd.readlines()):
                    match = re.search(pattern, line)
                    if match and not re.search(antipattern, line):
                        return match.group(1)

        return None

    def get_open_set_filename(self) -> Optional[str]:
        """
        Returns the absolute path to the currently-open Ableton Live set
        based on inspecting Live's Log.txt, or None if Live not open.

        Only presently supported on macOS, fixes welcomed.

        Returns:
            str: The absolute pathname, or None if Live is not running.
        """

        # TODO: This is macOS-only. Need a Windows equivalent.
        is_running = os.system("ps axc -o command  | grep -q ^Live$") == 0
        if is_running:
            return self._get_last_opened_set_filename()
        else:
            return None

    @property
    def is_connected(self) -> bool:
        """
        Test whether we can connect to Live.

        Returns:
            bool: True if Live currently appears to be running, False otherwise.
        """
        try:
            return bool(self.tempo)
        except Exception as e:
            return False

    # ------------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------------

    tempo = property(fget=make_getter("song", "tempo"),
                     fset=make_setter("song", "tempo"),
                     doc="Global tempo, in beats per minute (float)")

    metronome = property(fget=make_getter("song", "metronome"),
                         fset=make_setter("song", "metronome"),
                         doc="Global metronome setting, on/off (float)")

    clip_trigger_quantization = property(fget=make_getter("song", "clip_trigger_quantization"),
                                         fset=make_setter("song", "clip_trigger_quantization"),
                                         doc="Global quantization")

    current_song_time = property(fget=make_getter("song", "current_song_time"),
                                 fset=make_setter("song", "current_song_time"),
                                 doc="Current song time (in beats)")

    arrangement_overdub = property(fget=make_getter("song", "arrangement_overdub"),
                                   fset=make_setter("song", "arrangement_overdub"),
                                   doc="Arrangement overdub")

    # --------------------------------------------------------------------------------
    # Start/stop playback
    # --------------------------------------------------------------------------------

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

    def start_beat_listener(self) -> None:
        self.live.cmd("/live/song/start_listen/beat")

    def stop_beat_listener(self) -> None:
        self.live.cmd("/live/song/stop_listen/beat")

    # --------------------------------------------------------------------------------
    # Undo/redo
    # --------------------------------------------------------------------------------

    can_undo = property(fget=make_getter("song", "can_undo"),
                        doc="Whether an undo operation is possible")
    can_redo = property(fget=make_getter("song", "can_redo"),
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

    # --------------------------------------------------------------------------------
    # Tracks
    # --------------------------------------------------------------------------------

    num_tracks = property(fget=make_getter("song", "num_tracks"),
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

    # --------------------------------------------------------------------------------
    # Scenes
    # --------------------------------------------------------------------------------

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

    # --------------------------------------------------------------------------------
    # Cues
    # TODO: Refactor cues
    # --------------------------------------------------------------------------------
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

    # --------------------------------------------------------------------------------
    # Log level
    # --------------------------------------------------------------------------------
    log_level = property(fget=make_getter("api", "log_level"),
                         fset=make_setter("api", "log_level"),
                         doc="Log level (can be one of: debug, info, warning, error, critical)")

    back_to_arranger = property(fget=make_getter("song", "back_to_arranger"),
                                fset=make_setter("song", "back_to_arranger"),
                                doc="Set back to arranger")

    @property
    def average_process_usage(self):
        return self.live.query("/live/application/get/average_process_usage")[0]
