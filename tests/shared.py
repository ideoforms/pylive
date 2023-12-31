import live
import pytest

def open_test_set():
    set = live.Set(scan=False)
    set.open("tests/Tests Project/Tests.als", wait_for_startup=True)
    set.clip_trigger_quantization = 0
    set.stop_playing()
    set.stop_playing()

@pytest.fixture(scope="module")
def live_set():
    set = live.Set(scan=True)
    return set