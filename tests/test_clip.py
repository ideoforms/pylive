""" Unit tests for PyLive """

import pytest
import time
import live

from tests.shared import open_test_set

def setup_module():
    open_test_set()

@pytest.fixture(scope="module")
def live_set():
    set = live.Set()
    set.scan(scan_devices=True, scan_clip_names=True)
    return set

@pytest.fixture(scope="module")
def clip(live_set):
    track = live_set.tracks[1]
    clip = track.clips[0]
    return clip

def test_clip_properties(clip, live_set):
    assert clip.track == live_set.tracks[1]
    assert clip.set == live_set
    assert clip.index == 0
    assert clip.length == 4
    assert clip.looplen == 4
    assert clip.state == live.CLIP_STATUS_STOPPED
    assert clip.name == "one"
