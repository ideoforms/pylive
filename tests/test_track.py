""" Unit tests for PyLive """

import pytest
import live

def test_track_get_clips():
    """ set and query tempo """
    set = live.Set()
    set.scan()
    track = set.tracks[1]
    clips = track.clips
    assert len(clips) == 3
