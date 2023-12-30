""" Unit tests for PyLive """

import pytest
import time
import live

from .shared import open_test_set, live_set

def setup_module():
    open_test_set()

@pytest.fixture(scope="module")
def clip(live_set):
    track = live_set.tracks[1]
    clip = track.clips[0]
    return clip

@pytest.fixture(scope="module")
def audio_clip(live_set):
    track = live_set.tracks[4]
    clip = track.clips[0]
    return clip

def test_clip_properties(clip, live_set):
    assert clip.track == live_set.tracks[1]
    assert clip.set == live_set
    assert clip.index == 0
    assert clip.length == 4.0
    assert clip.state == live.CLIP_STATUS_STOPPED
    assert clip.name == "one"

def test_clip_play_stop(clip):
    clip.play()
    time.sleep(0.2)
    assert clip.is_playing
    clip.stop()
    time.sleep(0.2)
    assert not clip.is_playing

def test_clip_pitch_coarse(audio_clip):
    assert audio_clip.pitch_coarse == 0
    audio_clip.pitch_coarse = -24
    assert audio_clip.pitch_coarse == -24
    audio_clip.pitch_coarse = 0
