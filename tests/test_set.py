""" Unit tests for PyLive """

import pytest
import live

@pytest.mark.parametrize("tempo", [ 127.5, 80, 200 ])
def test_set_tempo(tempo):
    """ set and query tempo """
    set = live.Set()
    set.tempo = tempo
    assert tempo == set.tempo
