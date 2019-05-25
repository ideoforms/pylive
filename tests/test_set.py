""" Unit tests for PyLive """

import pytest
import live
import time
import os

from tests.shared import open_test_set

LIVE_TMP_SET_NAME = ".tmp_set"

def setup_module():
    open_test_set()

def test_set_connected():
    """ set and query tempo """
    set = live.Set()
    assert set.is_connected

@pytest.mark.parametrize("tempo", [ 127.5, 80, 200 ])
def test_set_tempo(tempo):
    """ set and query tempo """
    set = live.Set()
    set.tempo = tempo
    assert tempo == set.tempo

@pytest.mark.parametrize("quantization", [ 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13 ])
def test_set_quantization(quantization):
    """ set and query tempo """
    set = live.Set()
    set.quantization = quantization
    assert quantization == set.quantization

@pytest.mark.parametrize("t", [ 0.0, 1.0, 2.5 ])
def test_set_time(t):
    """ set and query tempo """
    set = live.Set()
    set.time = t
    #------------------------------------------------------------------------
    # Time update does not happen instantly. Wait briefly.
    #------------------------------------------------------------------------
    time.sleep(0.2)
    assert t == set.time

@pytest.mark.timeout(1.0)
def test_set_wait_for_next_beat():
    set = live.Set()
    set.tempo = 120.0
    set.play()
    set.wait_for_next_beat()
    set.stop()
    assert True

def test_set_load():
    LIVE_TMP_SET_PATH = "%s.pickle" % LIVE_TMP_SET_NAME
    if os.path.exists(LIVE_TMP_SET_PATH):
        os.unlink(LIVE_TMP_SET_PATH)
    set = live.Set()

    #------------------------------------------------------------------------
    # Load nonexistent file
    #------------------------------------------------------------------------
    with pytest.raises(FileNotFoundError) as excinfo:
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
