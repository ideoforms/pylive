import logging
from live.query import Query


def make_getter(prop):
    def fn(self):
        return self.live.query(f"/live/view/get/{prop}")[0]

    return fn


def make_setter(prop):
    def fn(self, value):
        self.live.cmd(f"/live/view/set/{prop}", (value,))

    return fn


class View:

    @property
    def live(self):
        return Query()

    def __init__(self):
        self.name = "view"
        self.logger = logging.getLogger(__name__)

    def __str__(self):
        return self.name

    def __getstate__(self):
        return {
            "name": self.name,
        }

    def __setstate__(self, d: dict):
        self.name = d["name"]

    selected_scene = property(
        fget=make_getter("selected_scene"),
        fset=make_setter("selected_scene"),
        doc="current selected scene"
    )

    selected_track = property(
        fget=make_getter("selected_track"),
        fset=make_setter("selected_track"),
        doc="current selected track"
    )

    selected_clip = property(
        fget=make_getter("selected_clip"),
        fset=make_setter("selected_clip"),
        doc="current selected clip"
    )

    selected_device = property(
        fget=make_getter("selected_device"),
        fset=make_setter("selected_device"),
        doc="current selected device"
    )
