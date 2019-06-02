from live.constants import CLIP_STATUS_PLAYING, CLIP_STATUS_STARTING
from live.object import LoggingObject
from live.clip import Clip
from live.exceptions import LiveInvalidOperationException

import re
import random

class Track(LoggingObject):
    """ Represents a single Track, either audio or MIDI.
    Resides within a Set, and contains one or more Device and Clip objects.
    May be contained within a Group.

    Properties:
    set -- The containing Set object
    index -- The numerical index of this Track within the Set
    name -- Human-readable name
    group -- (Optional) reference to containing Group object
    clips -- List of clips. Any empty slots will return None.
    devices -- List of contained Devices
    """

    def __init__(self, set, index, name, group = None):
        self.set = set
        self.index = index
        self.name = name
        self.group = group
        self.is_group = False

        self.clip_init = None
        self.clips = [ None ] * 256
        self.devices = []

    def __str__(self):
        if self.group:
            return "Track (%d,%d): %s" % (self.group.group_index, self.index, self.name)
        else:
            return "Track (%d): %s" % (self.index, self.name)

    @property
    def active_clips(self):
        """ Return a list of all non-empty clipslots. """
        active_clips = [n for n in self.clips if n is not None]
        return active_clips

    def create_clip(self, clip_index, length):
        if self.clips[clip_index] is not None:
            raise LiveInvalidOperationException("Clip [%d, %d] already exists" % (self.index, clip_index))
        else:
            self.set.create_clip(self.index, clip_index, length)
            self.clips[clip_index] = Clip(self, clip_index, length)

    def delete_clip(self, clip_index):
        if self.clips[clip_index] is None:
            raise LiveInvalidOperationException("Clip [%d, %d] does not exist" % (self.index, clip_index))
        else:
            self.set.delete_clip(self.index, clip_index)
            self.clips[clip_index] = None

    @property
    def scene_indexes(self):
        """ TODO: turn this into something that returns Scene objects (which don't yet exist) """
        indexes = []
        for clip in self.active_clips:
            indexes.append(clip.index)
        return indexes

    def stop(self):
        """ Immediately stop track from playing. """
        self.set.stop_track(self.index)

    @property
    def is_stopped(self):
        for clip in self.active_clips:
            if clip.state == CLIP_STATUS_PLAYING or clip.state == CLIP_STATUS_STARTING:
                return False
        return True

    @property
    def is_starting(self):
        for clip in self.active_clips:
            if clip.state == CLIP_STATUS_STARTING:
                return True
        return False

    @property
    def is_playing(self):
        return bool(self.clip_playing)

    @property
    def clip_playing(self):
        """ Return the currently playing Clip, or None. """
        for clip in self.active_clips:
            if clip.state == CLIP_STATUS_PLAYING:
                return clip
        return None

    def walk(self):
        """ Move forward or backwards between clips.
        TODO: Add count param to control forward/backwards/stride. """
        if not self.playing:
            if self.clip_init:
                self.log_info("walking to initial clip %d" % self.clip_init)
                self.play_clip(self.clip_init)
            else:
                self.log_warn("no clips found on track %d, returning" % self.index)
                return
        else:
            options = []
            if self.clip_playing - 1 in self.clips:
                options.append(self.clip_playing - 1)
            if self.clip_playing + 1 in self.clips:
                options.append(self.clip_playing + 1)

            if len(options) > 0:
                index = random.choice(options)
                self.log_info("walking from clip %d to %d" % (self.clip_playing, index))
                self.play_clip(index)
            else:
                self.log_info("walking to random clip")
                self.play_clip_random()

    def scan_clip_names(self):
        #--------------------------------------------------------------------------
        # scan for clip names.
        # is nice, but slows things down significantly -- so disable by default.
        #--------------------------------------------------------------------------
        for clip in self.active_clips:
            clip_name = self.set.get_clip_name(self.index, clip.index)
            clip.name = clip_name
            self.log_info("scan_clip_names: (%d, %d) -> %s" % (self.index, clip.index, clip.name))

    #------------------------------------------------------------------------
    # get/set: volume
    #------------------------------------------------------------------------

    def set_volume(self, value):
        self.set.set_track_volume(self.index, value)
    def get_volume(self):
        return self.set.get_track_volume(self.index)
    volume = property(get_volume, set_volume, None, "track volume (0..1)")

    #------------------------------------------------------------------------
    # get/set: pan
    #------------------------------------------------------------------------

    def set_pan(self, value):
        self.set.set_track_pan(self.index, value)
    def get_pan(self):
        return self.set.get_track_pan(self.index)
    pan = property(get_pan, set_pan, None, "track pan (-1..1)")

    #------------------------------------------------------------------------
    # get/set: mute
    #------------------------------------------------------------------------

    def set_mute(self, value):
        self.set.set_track_mute(self.index, value)
    def get_mute(self):
        return self.set.get_track_mute(self.index)
    mute = property(get_mute, set_mute, None, "track mute (0/1)")

    #------------------------------------------------------------------------
    # get/set: arm
    #------------------------------------------------------------------------

    def set_arm(self, value):
        self.set.set_track_arm(self.index, value)
    def get_arm(self):
        return self.set.get_track_arm(self.index)
    arm = property(get_arm, set_arm, None, "track armed to record (0/1)")

    #------------------------------------------------------------------------
    # get/set: solo
    #------------------------------------------------------------------------

    def set_solo(self, value):
        self.set.set_track_solo(self.index, value)
    def get_solo(self):
        return self.set.get_track_solo(self.index)
    solo = property(get_solo, set_solo, None, "track in solo mode (0/1)")

    #------------------------------------------------------------------------
    # get/set: send
    #------------------------------------------------------------------------

    def set_send(self, send_index, value):
        """ Set the send level of the given send_index (0..1) """
        self.set.set_track_send(self.index, send_index, value)
    def get_send(self, send_index):
        """ Get the send level of the given send_index (0..1) """
        return self.set.get_track_send(self.index, send_index)

    #------------------------------------------------------------------------
    # query devices
    #------------------------------------------------------------------------
    def get_device_named(self, name):
        """ Return the first device with a given name. """
        for device in self.devices:
            if device.name == name:
                return device
