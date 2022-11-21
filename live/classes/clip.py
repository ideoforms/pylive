import logging

import live.query
import live.object
from live.constants import *

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
        self.index = index
        self.name = name
        self.length = length
        self.state = CLIP_STATUS_STOPPED
        self.logger = logging.getLogger(__name__)

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

    def play(self):
        """
        Start playing clip.
        """
        self.live.cmd("/live/clip/fire", (self.track.index, self.index))
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