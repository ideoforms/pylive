import live

def open_test_set():
    set = live.Set()
    set.open("tests/Tests Project/Tests.als", wait=True)
    set.stop()
