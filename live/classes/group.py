from __future__ import annotations

import logging
from .track import Track

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .clip import Clip

class Group(Track):
    """
    Represents a grouped set of Track objects.
    """

    def __init__(self, set, track_index: int, group_index: int, name: str, group: Group):
        Track.__init__(self, set, track_index, name, group)

        self.track_index = track_index
        self.group_index = group_index

        # needed so that Clip objects can call the 'index' method on Group and Track accordingly
        # TODO: rename 'index' to 'track_index' on Track objects too
        self.index = track_index
        self.is_group = True
        self.group: Group = None

        self.tracks: list[Track] = []
        self.logger = logging.getLogger(__name__)

    def __str__(self):
        string = "Group (%d): %s" % (self.group_index, self.name)
        if len(self.tracks):
            string = string + " [tracks %d-%d]" % (self.tracks[0].index, self.tracks[len(self.tracks) - 1].index)
        return string

    def __iter__(self):
        return iter(self.tracks)

    def __getstate__(self):
        return {
            **super().__getstate__(),
            "track_index": self.track_index,
            "group_index": self.group_index,
            "tracks": self.tracks,
        }

    def __setstate__(self, d: dict):
        super().__setstate__(d)
        self.track_index = d["track_index"]
        self.group_index = d["group_index"]
        self.tracks = d["tracks"]

    def dump(self):
        self.logger.info("%d tracks" % len(self.tracks))
        for track in self.tracks:
            track.dump()

    @property
    def active_clips(self) -> list[Clip]:
        """ Return a dictionary of all non-empty clipslots: { index : Clip, ... } """
        active_clips = [n for n in self.clips if n is not None]
        return active_clips

    @property
    def is_playing(self):
        return any(track.is_playing for track in self.tracks)