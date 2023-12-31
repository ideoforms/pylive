""" Unit tests for PyLive """

import pytest
import time
import live

from .shared import open_test_set, live_set

def setup_module():
    open_test_set()

@pytest.fixture(scope="module")
def track():
    set = live.Set(scan=True)
    return set.tracks[1]

def test_track_get_clips(track):
    assert len(track.clips) == 1024
    assert len(list(filter(lambda n: n is not None, track.clips))) == 4

def test_track_get_active_clips(track):
    assert len(track.active_clips) == 4

def test_track_get_devices(track):
    assert len(track.devices) == 1

def test_track_create_delete_clip(track):
    # create a clip where one already exists
    with pytest.raises(live.LiveInvalidOperationException) as excinfo:
        track.create_clip(0, 1.0)

    # delete a clip where one does not exist
    with pytest.raises(live.LiveInvalidOperationException) as excinfo:
        track.delete_clip(6)

    # create and delete a clip
    track.create_clip(6, 1.0)
    track.delete_clip(6)

def test_track_states(track):
    # Set quantization to 1/2 bar, and ensure track states are passed through as expected:
    #  - stopped
    #  - starting
    #  - playing
    #  - stopped
    track.set.clip_trigger_quantization = 5
    assert track.is_stopped
    track.set.start_playing()
    time.sleep(0.25)
    track.clips[0].play()
    time.sleep(0.25)
    assert track.is_starting
    time.sleep(0.5)
    assert track.is_playing
    track.stop()
    time.sleep(0.2)
    assert track.is_stopped
    track.set.stop_playing()
    track.set.clip_trigger_quantization = 0

def test_track_stop(track):
    track.set.quantization = 0
    time.sleep(0.1)
    track.clips[0].play()
    time.sleep(0.2)
    assert track.is_playing
    track.stop()
    time.sleep(0.2)
    assert track.is_stopped
    track.set.stop_playing()

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

def test_track_type(live_set):
    assert live_set.tracks[1].is_midi_track
    assert not (live_set.tracks[1].is_audio_track)
    assert live_set.tracks[2].is_midi_track
    assert not (live_set.tracks[2].is_audio_track)
    assert live_set.tracks[4].is_audio_track
    assert not (live_set.tracks[4].is_midi_track)
    assert live_set.tracks[5].is_audio_track
    assert not (live_set.tracks[5].is_midi_track)