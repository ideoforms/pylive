""" Unit tests for PyLive """

import pytest
import live

from tests.shared import open_test_set

def setup_module():
    open_test_set()

def test_track_get_clips():
    """ set and query tempo """
    set = live.Set()
    set.scan()
    track = set.tracks[1]
    clips = track.clips
    assert len(clips) == 3
