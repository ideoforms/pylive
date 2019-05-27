from live.constants import *

import live.query
import live.object

import random

class Clip(live.LoggingObject):
    """ An object representing a single clip in a Live set.

    Properties:
    track -- Track object this clip resides within.
    index -- index of this clip
    length -- length of cip, in beats
    name -- human-readable name
    state -- one of CLIP_STATUS_EMPTY, CLIP_STATUS_STOPPED, CLIP_STATUS_PLAYING
    """

    def __init__(self, track, index, length = 4):
        """ Create a new clip.
        
        Arguments:
        track -- a Track or Group object
        index -- index of this clip within the track
        length -- length of clip, in beats
        """
        self.track = track
        self.index = index
        self.length = length
        self.looplen = length
        self.state = CLIP_STATUS_STOPPED
        self.name = None

    def __str__(self):
        name = ": %s" % self.name if self.name else ""
        state_symbols = {
            CLIP_STATUS_EMPTY : " ",
            CLIP_STATUS_STOPPED : "-",
            CLIP_STATUS_PLAYING : ">",
            CLIP_STATUS_STARTING : "*"
        }
        state_symbol = state_symbols[self.state]
        
        return "Clip (%d,%d)%s [%s]" % (self.track.index, self.index, name, state_symbol)

    @property
    def set(self):
        """ Helper method to obtain the Set that this clip resides within. """
        return self.track.set

    def reset(self):
        if self.looplen != self.length:
            self.log_info("Resetting loop length to %d" % self.length)
            self.set.set_clip_loop_end(self.track.index, self.index, self.looplen)

    def play(self):
        """ Start playing clip. """
        self.log_info("Playing")
        self.set.play_clip(self.track.index, self.index)
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
        """ Stop playing clip """
        self.log_info("stopping")
        self.set.stop_clip(self.track.index, self.index)
        self.track.playing = False
    
    def get_pitch(self):
        return tuple(self.set.get_clip_pitch(self.track.index, self.index))
    def set_pitch(self, pitch):
        """ pitch must be a tuple of (coarse, fine), where
        coarse is in range [-48, +48]
        fine   is in range [-50, +50 ]
        """
        self.set.set_clip_pitch(self.track.index, self.index, pitch[0], pitch[1])
    pitch = property(get_pitch, set_pitch, doc = "Pitch (coarse [-48,48], fine [-50,50])")

    def get_muted(self):
        return bool(self.set.get_clip_mute(self.track.index, self.index))
    def set_muted(self, muted=True):
        self.set.set_clip_mute(self.track.index, self.index, int(muted))
    muted = property(get_muted, set_muted, doc = "Muted (boolean)")

    def get_next_clip(self, wrap=False, allow_gaps=True):
        """ Return the next clip in the track, or None if not found.
        wrap -- If set, will wrap from (N-1) to 0 and vice versa.
        allow_gaps -- If unset, requires that clip slots must be contiguous.
        """
        clips = self.track.clips
        index = clips.index(self)
        clip_range = []
        for n in range(index, len(clips)):
            if clips[n] is None:
                if not allow_gaps:
                    break
            else:
                clip_range.append(clips[n])
        for n in reversed(list(range(0, index))):
            if clips[n] is None:
                if not allow_gaps:
                    break
            else:
                clip_range.insert(0, clips[n])

        index = clip_range.index(self)
        next_index = index + 1
        if wrap:
            next_index = next_index % len(clip_range)
        if next_index < len(clip_range):
            return clip_range[next_index]
        return None

    def get_prev_clip(self, wrap=False, allow_gaps=True):
        """ Return the previous clip in the track, or None if not found.
        wrap -- If set, will wrap from (N-1) to 0 and vice versa.
        allow_gaps -- If unset, requires that clip slots must be contiguous.
        """
        clips = self.track.clips
        index = clips.index(self)
        clip_range = []
        for n in range(index, len(clips)):
            if clips[n] is None:
                if not allow_gaps:
                    break
            else:
                clip_range.append(clips[n])
        for n in reversed(list(range(0, index))):
            if clips[n] is None:
                if not allow_gaps:
                    break
            else:
                clip_range.insert(0, clips[n])

        index = clip_range.index(self)
        prev_index = index - 1
        if wrap and prev_index < 0:
            prev_index += len(clip_range)
        if prev_index >= 0:
            return clip_range[prev_index]
        return None

    def add_note(self, note, position, duration, velocity):
        """
        :param note:      (int)    MIDI note index
        :param position:  (float)  Position, in beats
        :param duration:  (float)  Duration, in beats
        :param velocity:  (int)    MIDI note velocity
        """
        self.set.add_clip_note(self.track.index, self.index, note, position, duration, velocity, 0)

    def get_notes(self):
        """ TODO: get_clip_notes does not always return all of the notes,
        as it may return before the entire OSC bundle has been processed.
        Rethink bundle processing so that the event is not triggered
        until end of bundle. """
        notes = self.set.get_clip_notes(self.track.index, self.index)
        notes = [ notes[n+2:n+7] for n in range(0, len(notes), 7) ]
        return notes
