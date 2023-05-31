import logging

class Scene:
    """ An object representing a single scene in a Live set.

    Properties:
    index -- index of this scene
    name -- human-readable name
    """

    def __init__(self, set, index):
        """ Create a new scene.
        
        Arguments:
        index -- index of this scene
        """
        self.set = set
        self.index = index
        self.name = None
        self.logger = logging.getLogger(__name__)

    def __str__(self):
        name = ": %s" % self.name if self.name else ""

        return "Scene (%d)%s" % (self.index, name)

    def __getstate__(self):
        return {
            "index": self.index,
            "name": self.name,
        }

    def __setstate__(self, d: dict):
        self.index = d["index"]
        self.name = d["name"]

    def play(self):
        """ Start playing scene. """
        self.logger.info("playing")
        self.set.play_scene(self.index)
