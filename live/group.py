from live.object import *
from live.track import *

class Group (Track):
    """ Represents a grouped set of Track objects.

    Properties:
    track_index -- The numerical track index of this group
    group_index -- Groups are auto-numbered from 0
    name -- Human-readable name
    tracks -- List of Track objects contained within this group
    """

    def __init__(self, set, track_index, group_index, name):
        Track.__init__(self, set, track_index, name)

        self.track_index = track_index
        self.group_index = group_index

        # needed so that Clip objects can call the 'index' method on Group and Track accordingly
        # TODO: rename 'index' to 'track_index' on Track objects too
        self.index = track_index
        self.is_group = True
        self.group = None

        self.tracks = []

    def __str__(self):
        string = "Group (%d): %s" % (self.group_index, self.name)
        if len(self.tracks):
            string = string + " [tracks %d-%d]" % (self.tracks[0].index, self.tracks[len(self.tracks) - 1].index)
        return string

    @property
    def scene_indexes(self):
        indexes = {}
        for track in self.tracks:
            for index in track.scene_indexes:
                indexes[index] = 1
        indexes = list(indexes.keys())
        indexes = sorted(indexes)
        return indexes

    def dump(self):
        self.log_info("%d tracks" % len(self.tracks))
        for track in self.tracks:
            track.dump()
    
    @property
    def is_playing(self):
        for track in self.tracks:
            if track.is_playing:
                return True
        return False

    def stop(self):
        """ Immediately stop group from playing. """
        self.set.stop_track(self.track_index)

    @property
    def active_clips(self):
        """ Return a dictionary of all non-empty clipslots: { index : Clip, ... } """
        active_clips = [n for n in self.clips if n is not None]
        return active_clips
