""" Unit tests for PyLive """

import pytest
import live
import time
import os

from tests.shared import open_test_set

LIVE_TMP_SET_NAME = ".tmp_set"
LIVE_TMP_SET_PATH = "%s.pickle" % LIVE_TMP_SET_NAME

def setup_module():
    # open_test_set()
    pass

def test_set_connected():
    set = live.Set()
    assert set.is_connected

@pytest.mark.parametrize("tempo", [127.5, 80, 200])
def test_set_tempo(tempo):
    set = live.Set()
    set.tempo = tempo
    assert tempo == set.tempo

@pytest.mark.parametrize("quantization", [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13])
def test_set_quantization(quantization):
    set = live.Set()
    set.quantization = quantization
    assert quantization == set.quantization

@pytest.mark.parametrize("t", [0.0, 1.0, 2.5])
def test_set_time(t):
    set = live.Set()
    set.time = t
    #------------------------------------------------------------------------
    # Time update does not happen instantly. Wait briefly.
    #------------------------------------------------------------------------
    time.sleep(0.1)
    assert t == set.time

def test_set_play():
    set = live.Set()
    set.time = 0.0
    set.quantization = 4

    #------------------------------------------------------------------------
    # Play with reset
    #------------------------------------------------------------------------
    set.play(reset=True)
    time.sleep(0.1)
    set.stop()
    assert set.time > 0.0

    #------------------------------------------------------------------------
    # Play without reset
    #------------------------------------------------------------------------
    t0 = set.time
    set.play(reset=False)
    time.sleep(0.1)
    set.stop()
    assert set.time > t0

def test_set_stop():
    set = live.Set()
    set.play(reset=True)
    time.sleep(0.1)
    set.stop()
    time.sleep(0.1)
    t0 = set.time
    time.sleep(0.1)
    assert set.time == t0

def test_set_num_tracks():
    set = live.Set()
    assert set.num_tracks == 6

def test_set_num_scenes():
    set = live.Set()
    assert set.num_scenes == 8

def test_get_master_volume():
    set = live.Set()
    assert set.master_volume == pytest.approx(0.85)

def test_set_master_volume():
    set = live.Set()
    set.master_volume = 0.5
    assert set.master_volume == pytest.approx(0.5)

def test_get_master_pan():
    set = live.Set()
    assert set.master_pan == pytest.approx(0.0)

def test_set_master_pan():
    set = live.Set()
    set.master_pan = 0.1
    assert set.master_pan == pytest.approx(0.1)

def test_set_scan():
    set = live.Set()
    assert set.scanned == False
    assert len(set.tracks) == 0
    set.scan()
    assert set.scanned == True
    assert len(set.tracks) == 6

def test_set_load():
    if os.path.exists(LIVE_TMP_SET_PATH):
        os.unlink(LIVE_TMP_SET_PATH)
    set = live.Set()

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

def test_set_save():
    set = live.Set()

    set.save(LIVE_TMP_SET_NAME)
    set.load(LIVE_TMP_SET_NAME)
    assert len(set.tracks) == 0

    set.scan()
    assert len(set.tracks) == 6
    set.save(LIVE_TMP_SET_NAME)
    set.load(LIVE_TMP_SET_NAME)
    assert len(set.tracks) == 6

    os.unlink(LIVE_TMP_SET_PATH)

def test_set_get_track_named():
    set = live.Set()
    set.scan()

    track = set.get_track_named("2-Operator")
    assert track == set.tracks[1]

    track = set.get_track_named("Nonexistent")
    assert track is None

def test_set_get_group_named():
    set = live.Set()
    set.scan()

    group = set.get_group_named("1. Group")
    assert group == set.groups[0]

    group = set.get_group_named("Nonexistent")
    assert group is None

@pytest.mark.timeout(1.0)
def test_set_wait_for_next_beat():
    set = live.Set()
    set.tempo = 120.0
    set.play()
    set.wait_for_next_beat()
    set.stop()
    assert True

def test_set_currently_open():
    set = live.Set()
    assert set.currently_open().endswith("Tests.als")
