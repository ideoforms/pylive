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
    set.quantization = 0
    set.tracks[4].stop()
    time.sleep(0.2)
    return set

@pytest.fixture(scope="module")
def clip(live_set):
    track = live_set.tracks[4]
    clip = track.clips[0]
    return clip

def test_clip_properties(clip, live_set):
    assert clip.track == live_set.tracks[4]
    assert clip.set == live_set
    assert clip.index == 0
    assert clip.length == 4
    assert clip.looplen == 4
    assert clip.state == live.CLIP_STATUS_STOPPED
    assert clip.name == "one"

def test_clip_play_stop(clip):
    clip.play()
    time.sleep(0.2)
    assert clip.state == live.CLIP_STATUS_PLAYING
    clip.stop()
    time.sleep(0.2)
    assert clip.state == live.CLIP_STATUS_STOPPED

def test_clip_pitch(clip):
    pitch = clip.pitch
    assert tuple(pitch) == (0, 0)

    clip.pitch = [ 1.0, 1.0 ]
    pitch = clip.pitch
    assert tuple(pitch) == (1, 1)
