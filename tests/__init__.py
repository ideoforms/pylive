#------------------------------------------------------------------------
# This file is included so that pytest can find the package
# root and import the `live` module from a local relative path.
#
# https://docs.pytest.org/en/latest/goodpractices.html#test-package-name
#------------------------------------------------------------------------
import pytest

from live.set import Set

@pytest.fixture
def set() -> Set:
    return Set()
