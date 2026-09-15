# this file is part of MultiplayerLib, which is under an MIT license.
# see LICENSE file at root of this repository for details.

"""
:MultiplayerLib:\n
Multiplayerlib is a library designed to allow for easy creation of multiplayer games with any game
module. It is currently limited to only 2 player games where one player is the host and one player
connects, although there are plans for adding support for more than just 1v1 games.
"""
from multiplayerlib.NetworkLib import *
from multiplayerlib.NetworkConstants import *
import urllib.request
import json
from importlib.metadata import version
from packaging import version

def checkForUpdates() -> bool:
    """
    checks if MultiplayerLib is on the latest version using the Python Package Index (PyPI) api.
    returns true if there is a new version available.
    """
    currentVersion = version("multiplayerlib")
    try:
        with urllib.request.urlopen(
            "https://pypi.org/pypi/multiplayerlib/json",
            timeout=2
        ) as response:
            latestVersion = json.load(response)["info"]["version"]
        if version(latestVersion) > version(currentVersion):
            return True
        return False
    except Exception:
        return False