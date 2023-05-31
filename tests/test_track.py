""" Unit tests for PyLive """

import pytest
import time
import live

from tests.shared import open_test_set

def setup_module():
    #open_test_set()
    pass

@pytest.fixture(scope="module")
def track():
    set = live.Set()
    set.scan()
    set.tracks[1].stop()
    time.sleep(0.1)
    return set.tracks[1]

def test_track_get_clips(track):
    assert len(track.clips) == 256
    assert len(list(filter(lambda n: n is not None, track.clips))) == 4

def test_track_get_active_clips(track):
    assert len(track.active_clips) == 4

def test_track_get_devices(track):
    assert len(track.devices) == 1

def test_track_create_clip(track):
    with pytest.raises(live.LiveInvalidOperationException) as excinfo:
        track.create_clip(0, 1.0)
    track.create_clip(5, 1.0)

def test_track_delete_clip(track):
    with pytest.raises(live.LiveInvalidOperationException) as excinfo:
        track.delete_clip(6)
    track.delete_clip(5)

def test_track_states(track):
    # is_stopped
    # is_starting
    # is_playing
    track.set.clip_trigger_quantization = 7
    assert track.is_stopped
    track.set.start_playing()
    time.sleep(0.1)
    track.clips[0].play()
    time.sleep(0.2)
    assert track.is_starting
    time.sleep(0.5)
    assert track.is_playing
    track.stop()
    time.sleep(0.2)
    assert track.is_stopped
    track.set.stop_playing()

def test_track_stop(track):
    track.set.quantization = 0
    time.sleep(0.1)
    track.clips[0].play()
    time.sleep(0.2)
    assert track.is_playing
    track.stop()
    time.sleep(0.2)
    assert track.is_stopped

def test_track_scan_clip_names(track):
    assert track.active_clips[0].name == "one"
    assert track.active_clips[1].name == "two"
    assert track.active_clips[2].name == "three"
    assert track.active_clips[3].name == "four"

def test_track_volume(track):
    assert track.volume == pytest.approx(0.85)
    track.volume = 0.0
    assert track.volume == 0.0
    track.volume = 0.85

def test_track_panning(track):
    assert track.panning == 0
    track.panning = 1
    assert track.panning == 1
    track.panning = 0

def test_track_mute(track):
    assert track.mute == 0
    track.mute = 1
    assert track.mute == 1
    track.mute = 0

def test_track_arm(track):
    assert track.arm == 0
    track.arm = 1
    assert track.arm == 1
    track.arm = 0

def test_track_solo(track):
    assert track.solo == 0
    track.solo = 1
    assert track.solo == 1
    track.solo = 0

def test_track_send(track):
    assert track.get_send(0) == pytest.approx(0.0)
    track.set_send(0, 1.0)
    assert track.get_send(0) == 1.0
    track.set_send(0, 0.0)

def test_track_device_named(track):
    device = track.get_device_named("Operator")
    assert device is not None
    assert device == track.devices[0]
