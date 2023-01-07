from __future__ import annotations

from ..constants import CLIP_STATUS_PLAYING, CLIP_STATUS_STARTING
from ..exceptions import LiveInvalidOperationException
from ..query import Query
from .clip import Clip

import logging

def make_getter(class_identifier, prop):
    def fn(self):
        return self.live.query("/live/%s/get/%s" % (class_identifier, prop), (self.index,))[1]
    return fn

def make_setter(class_identifier, prop):
    def fn(self, value):
        self.live.cmd("/live/%s/set/%s" % (class_identifier, prop), (self.index, value))
    return fn

class Track:
    """
    Represents a single Track, either audio or MIDI.
    Resides within a Set, and contains one or more Device and Clip objects.
    May be contained within a Group.
    """

    def __init__(self, set, index: int, name: str, group: "Group" = None):
        """
        Args:
            set: The containing Set object
            index: The numerical index of this Track within the Set
            name: Human-readable name
            group: (Optional) reference to containing Group object
        """
        self.set = set
        self.index = index
        self.name = name
        self.group = group

        self.is_group = False
        self.clip_init = None
        self.clips = [None] * 256
        self.devices = []
        self.logger = logging.getLogger(__name__)
        self.live = Query()

    def __str__(self):
        if self.group:
            return "Track (%d,%d): %s" % (self.group.group_index, self.index, self.name)
        else:
            return "Track (%d): %s" % (self.index, self.name)

    def __iter__(self):
        return iter(self.clips)

    @property
    def active_clips(self):
        """
        Return a list of all non-null clips.
        """
        active_clips = [n for n in self.clips if n is not None]
        return active_clips

    def create_clip(self, clip_index: int, length: float):
        if self.clips[clip_index] is not None:
            raise LiveInvalidOperationException("Clip [%d, %d] already exists" % (self.index, clip_index))
        else:
            self.live.cmd("/live/clip_slot/create_clip", (self.index, clip_index, length))
            self.clips[clip_index] = Clip(self, clip_index, length)

    def delete_clip(self, clip_index):
        if self.clips[clip_index] is None:
            raise LiveInvalidOperationException("Clip [%d, %d] does not exist" % (self.index, clip_index))
        else:
            self.live.cmd("/live/clip_slot/delete_clip", (self.index, clip_index))
            self.clips[clip_index] = None

    def stop(self):
        """
        Immediately stop track from playing.
        """
        print("Index: %s" % self.index)
        self.live.cmd("/live/track/stop_all_clips", (self.index,))

    #------------------------------------------------------------------------
    # Query devices
    #------------------------------------------------------------------------
    def get_device_named(self, name: str):
        """
        Return the first device with a given name.
        """
        for device in self.devices:
            if device.name == name:
                return device

    @property
    def is_stopped(self):
        for clip in self.active_clips:
            if clip.state == CLIP_STATUS_PLAYING or clip.state == CLIP_STATUS_STARTING:
                return False
        return True

    @property
    def is_starting(self):
        return self.fired_slot_index >= 0

    @property
    def is_playing(self):
        return self.playing_slot_index >= 0

    @property
    def clip_playing(self):
        """
        Return the currently playing Clip, or None.
        """
        playing_slot_index = self.playing_slot_index
        if playing_slot_index >= 0:
            return self.clips[playing_slot_index]
        else:
            return None

    volume = property(fget=make_getter("track", "volume"),
                      fset=make_setter("track", "volume"),
                      doc="Volume (0..1)")
    panning = property(fget=make_getter("track", "panning"),
                       fset=make_setter("track", "panning"),
                       doc="Pan (0..1)")
    mute = property(fget=make_getter("track", "mute"),
                    fset=make_setter("track", "mute"),
                    doc="Mute state (0/1)")
    arm = property(fget=make_getter("track", "arm"),
                   fset=make_setter("track", "arm"),
                   doc="Arm state (0/1)")
    solo = property(fget=make_getter("track", "solo"),
                    fset=make_setter("track", "solo"),
                    doc="Solo state (0/1)")
    playing_slot_index = property(fget=make_getter("track", "playing_slot_index"),
                                  fset=make_setter("track", "playing_slot_index"),
                                  doc="Playing slot index")
    fired_slot_index = property(fget=make_getter("track", "fired_slot_index"),
                                fset=make_setter("track", "fired_slot_index"),
                                doc="Fired slot index")

    def get_send(self, send_index: int):
        return self.live.query("/live/track/get/send", (self.index, send_index))[1]

    def set_send(self, send_index: int, value: float):
        self.live.cmd("/live/track/set/send", (self.index, send_index, value))
