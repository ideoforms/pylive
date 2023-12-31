""" Unit tests for pylive """

import pytest
import time
import os

import live
from live import Set
from .shared import open_test_set

LIVE_TMP_SET_NAME = ".tmp_set"
LIVE_TMP_SET_PATH = "%s.pickle" % LIVE_TMP_SET_NAME

@pytest.fixture
def set() -> Set:
    set = Set(scan=True)
    return set

def setup_module():
    open_test_set()

def test_set_connected(set: Set):
    assert set.is_connected

@pytest.mark.parametrize("tempo", [127.5, 80, 200])
def test_set_tempo(set: Set, tempo: float):
    set.tempo = tempo
    assert tempo == set.tempo

@pytest.mark.parametrize("quantization", [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13])
def test_set_quantization(set: Set, quantization: int):
    set.quantization = quantization
    assert quantization == set.quantization

@pytest.mark.parametrize("t", [0.0, 1.0, 2.5])
def test_set_time(set: Set, t: float):
    set.time = t
    #------------------------------------------------------------------------
    # Time update does not happen instantly. Wait briefly.
    #------------------------------------------------------------------------
    time.sleep(0.1)
    assert t == set.time

def test_set_play(set: Set):
    set.time = 0.0
    set.quantization = 4

    #------------------------------------------------------------------------
    # Play with reset
    #------------------------------------------------------------------------
    set.start_playing()
    time.sleep(0.1)
    set.stop_playing()
    assert set.current_song_time > 0.0

    #------------------------------------------------------------------------
    # Play without reset
    #------------------------------------------------------------------------
    t0 = set.time
    set.continue_playing()
    time.sleep(0.1)
    set.stop_playing()
    assert set.current_song_time > t0

def test_set_stop(set: Set):
    set.start_playing()
    time.sleep(0.1)
    set.stop_playing()
    time.sleep(0.1)
    t0 = set.current_song_time
    time.sleep(0.1)
    assert set.current_song_time == t0

def test_set_num_tracks(set: Set):
    assert set.num_tracks == 6
    set.create_midi_track(-1)
    assert set.num_tracks == 7
    set.delete_track(6)
    assert set.num_tracks == 6

def test_set_num_scenes(set: Set):
    assert set.num_scenes == 8
    set.create_scene(-1)
    assert set.num_scenes == 9
    set.delete_scene(8)
    assert set.num_scenes == 8

@pytest.mark.skip
def test_get_master_volume(set: Set):
    assert set.master_volume == pytest.approx(0.85)

@pytest.mark.skip
def test_set_master_volume(set: Set):
    set.master_volume = 0.5
    assert set.master_volume == pytest.approx(0.5)

@pytest.mark.skip
def test_get_master_pan(set: Set):
    assert set.master_pan == pytest.approx(0.0)

@pytest.mark.skip
def test_set_master_pan(set: Set):
    set.master_pan = 0.1
    assert set.master_pan == pytest.approx(0.1)

@pytest.mark.skip
def test_set_scan(set: Set):
    assert set.scanned == False
    assert len(set.tracks) == 0
    set.scan()
    assert set.scanned == True
    assert len(set.tracks) == 6

@pytest.mark.skip
def test_set_load(set: Set):
    if os.path.exists(LIVE_TMP_SET_PATH):
        os.unlink(LIVE_TMP_SET_PATH)

    #------------------------------------------------------------------------
    # Load nonexistent file
    #------------------------------------------------------------------------
    with pytest.raises(IOError) as excinfo:
        set.load(LIVE_TMP_SET_NAME)
    assert excinfo

    #------------------------------------------------------------------------
    # Load file containing invalid data
    #------------------------------------------------------------------------
    with open(LIVE_TMP_SET_PATH, "w") as fd:
        fd.write("foo")
    with pytest.raises(live.LiveIOError) as excinfo:
        set.load(LIVE_TMP_SET_NAME)

    #------------------------------------------------------------------------
    # Load valid file
    #------------------------------------------------------------------------
    set.save(LIVE_TMP_SET_NAME)
    set.load(LIVE_TMP_SET_NAME)

    os.unlink(LIVE_TMP_SET_PATH)

@pytest.mark.skip
def test_set_save(set: Set):
    set.save(LIVE_TMP_SET_NAME)
    set.load(LIVE_TMP_SET_NAME)
    assert len(set.tracks) == 0

    set.scan()
    assert len(set.tracks) == 6
    set.save(LIVE_TMP_SET_NAME)
    set.load(LIVE_TMP_SET_NAME)
    assert len(set.tracks) == 6

    os.unlink(LIVE_TMP_SET_PATH)

def test_set_get_track_named(set: Set):
    track = set.get_track_named("5-Conga")
    assert track == set.tracks[4]

    track = set.get_track_named("Nonexistent")
    assert track is None

def test_set_get_group_named(set: Set):
    group = set.get_group_named("1. Group")
    assert group == set.groups[0]

    group = set.get_group_named("Nonexistent")
    assert group is None

@pytest.mark.timeout(1.0)
def test_set_wait_for_next_beat(set: Set):
    set.tempo = 120.0
    set.start_playing()
    set.wait_for_next_beat()
    set.stop_playing()
    assert True

def test_set_currently_open(set: Set):
    assert set.get_open_set_filename().endswith("Tests.als")
