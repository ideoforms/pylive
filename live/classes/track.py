from __future__ import annotations

from ..constants import CLIP_STATUS_PLAYING, CLIP_STATUS_STARTING
from ..exceptions import LiveInvalidOperationException
from .clip import Clip

import logging

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
            self.set.create_clip(self.index, clip_index, length)
            self.clips[clip_index] = Clip(self, clip_index, length)

    def delete_clip(self, clip_index):
        if self.clips[clip_index] is None:
            raise LiveInvalidOperationException("Clip [%d, %d] does not exist" % (self.index, clip_index))
        else:
            self.set.delete_clip(self.index, clip_index)
            self.clips[clip_index] = None

    def stop(self):
        """
        Immediately stop track from playing.
        """
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
        for clip in self.active_clips:
            if clip.state == CLIP_STATUS_STARTING:
                return True
        return False

    @property
    def is_playing(self):
        return bool(self.clip_playing)

    @property
    def clip_playing(self):
        """
        Return the currently playing Clip, or None.
        """
        for clip in self.active_clips:
            if clip.state == CLIP_STATUS_PLAYING:
                return clip
        return None
