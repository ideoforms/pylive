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
    set.scan(scan_devices = True)
    return set

def test_track_get_clips(live_set):
    track = live_set.tracks[1]
    assert len(track.clips) == 5

def test_track_get_active_clips(live_set):
    track = live_set.tracks[1]
    assert len(track.active_clips) == 4

def test_track_get_devices(live_set):
    track = live_set.tracks[1]
    assert len(track.devices) == 1

def test_track_scene_indexes(live_set):
    track = live_set.tracks[1]
    scene_indexes = track.scene_indexes
    assert scene_indexes == [ 0, 1, 2, 4 ]

def test_track_states(live_set):
    # is_stopped
    # is_starting
    # is_playing
    track = live_set.tracks[1]
    live_set.quantization = 5
    assert track.is_stopped
    live_set.play()
    time.sleep(0.1)
    track.clips[0].play()
    time.sleep(0.2)
    assert track.is_starting
    time.sleep(1.0)
    assert track.is_playing
    track.stop()
    time.sleep(1.0)
    assert track.is_stopped

def test_track_stop(live_set):
    live_set.quantization = 0
    track = live_set.tracks[1]
    track.clips[0].play()
    time.sleep(0.2)
    assert track.is_playing
    track.stop()
    time.sleep(0.2)
    assert track.is_stopped

def test_track_volume(live_set):
    track = live_set.tracks[2]
    assert track.volume == pytest.approx(0.85)
    track.volume = 0.0
    assert track.volume == 0.0
    track.volume = 0.85

def test_track_pan(live_set):
    track = live_set.tracks[2]
    assert track.pan == 0
    track.pan = 1
    assert track.pan == 1
    track.pan = 0

def test_track_mute(live_set):
    track = live_set.tracks[2]
    assert track.mute == 0
    track.mute = 1
    assert track.mute == 1
    track.mute = 0

def test_track_arm(live_set):
    track = live_set.tracks[2]
    assert track.arm == 0
    track.arm = 1
    assert track.arm == 1
    track.arm = 0

def test_track_solo(live_set):
    track = live_set.tracks[2]
    assert track.solo == 0
    track.solo = 1
    assert track.solo == 1
    track.solo = 0

def test_track_send(live_set):
    track = live_set.tracks[2]
    assert track.get_send(0) == pytest.approx(0.0)
    track.set_send(0, 1.0)
    assert track.get_send(0) == 1.0
    track.set_send(0, 0.0)

def test_track_device_named(live_set):
    track = live_set.tracks[2]
    device = track.get_device_named("Operator")
    assert device is not None
    assert device == track.devices[0]
