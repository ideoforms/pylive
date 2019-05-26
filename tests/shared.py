import live

def open_test_set():
    set = live.Set()
    set.open("tests/Tests Project/Tests.als", wait=True)
    set.master_volume = 0.85
    set.master_pan = 0.0
    set.stop()
