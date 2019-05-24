""" Unit tests for PyLive """

import pytest
import live

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
    print("about to set q")
    set.quantization = quantization
    print("about to get q")
    assert quantization == set.quantization
