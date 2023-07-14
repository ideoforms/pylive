import logging

import live.query
import live.object
from live.constants import *
from live.query import Query

def make_getter(class_identifier, prop):
    def fn(self):
        return self.live.query("/live/%s/get/%s" % (class_identifier, prop), (self.track.index, self.index,))[2]

    return fn

def make_setter(class_identifier, prop):
    def fn(self, value):
        self.live.cmd("/live/%s/set/%s" % (class_identifier, prop), (self.track.index, self.index, value))

    return fn

class Clip:
    """
    An object representing a single clip in a Live set.
    """

    def __init__(self, track, index: int, name: str, length: float = 4):
        """ Create a new clip.

        Args:
            track: A Track or Group object
            index: The index of this clip within the track
            name: The human-readable name of the clip
            length: Length of the clip, in beats
        """
        self.track = track
        self.set = self.track.set
        self.index = index
        self.name = name
        self.length = length
        self.state = CLIP_STATUS_STOPPED
        self.logger = logging.getLogger(__name__)
        # self.live = Query()

    @property
    def live(self):
        return Query()

    def __str__(self):
        name = ": %s" % self.name if self.name else ""
        state_symbols = {
            CLIP_STATUS_EMPTY: " ",
            CLIP_STATUS_STOPPED: "-",
            CLIP_STATUS_PLAYING: ">",
            CLIP_STATUS_STARTING: "*"
        }
        state_symbol = state_symbols[self.state]

        return "Clip (%d,%d)%s [%s]" % (self.track.index, self.index, name, state_symbol)

    def __getstate__(self):
        return {
            "track": self.track,
            "index": self.index,
            "name": self.name,
            "length": self.length,
        }

    def __setstate__(self, d: dict):
        self.track = d["track"]
        self.index = d["index"]
        self.name = d["name"]
        self.length = d["length"]

    def play(self):
        """
        Start playing clip.
        Must use clip_slot (not clip) as this is also used in group tracks, which have clip_slots without clips.
        """
        self.live.cmd("/live/clip_slot/fire", (self.track.index, self.index))
        self.track.playing = True
        if type(self.track) is live.Group:
            for track in self.track.tracks:
                #------------------------------------------------------------------------
                # when we trigger a group clip, it triggers each of the corresponding
                # clips in the tracks it contains. thus need to update the playing
                # status of each of our tracks, assuming that all clips/stop buttons
                # are enabled.
                #------------------------------------------------------------------------
                if self.index < len(track.clips) and track.clips[self.index] is not None:
                    track.playing = True
                else:
                    track.playing = False

    def stop(self):
        """
        Stop playing clip.
        """
        self.live.cmd("/live/clip/stop", (self.track.index, self.index))
        self.track.playing = False

    def add_note(self, pitch, start_time, duration, velocity, mute):
        self.live.cmd("/live/clip/add/notes", (self.track.index, self.index, pitch, start_time, duration, velocity, mute))


    pitch_coarse = property(fget=make_getter("clip", "pitch_coarse"),
                            fset=make_setter("clip", "pitch_coarse"),
                            doc="pitch_coarse")
    is_playing = property(fget=make_getter("clip", "is_playing"),
                          fset=make_setter("clip", "is_playing"),
                          doc="is_playing")
