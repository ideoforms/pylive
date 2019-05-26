""" Unit tests for PyLive """

import pytest
import live

from tests.shared import open_test_set

def setup_module():
    open_test_set()

@pytest.fixture(scope="module")
def live_set():
    set = live.Set()
    set.scan()
    return set

def test_track_get_clips(live_set):
    """ set and query tempo """
    track = live_set.tracks[1]
    clips = track.clips
    assert len(clips) == 3

def test_track_arm(live_set):
    """ set and query tempo """
    track = live_set.tracks[2]
    assert track.arm == 0
    track.arm = 1
    assert track.arm == 1
    track.arm = 0
