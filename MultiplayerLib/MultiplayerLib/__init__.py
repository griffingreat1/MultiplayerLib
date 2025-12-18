"""
:MultiplayerLib:\n
Multiplayerlib is a library designed to allow for easy creation of multiplayer games with any game
module. It is currently limited to only 2 player games where one player is the host and one player
connects, although there are plans for adding support for more than just 1v1 games.
"""
from MultiplayerLib.NetworkLib import *
from MultiplayerLib.NetworkConstants import *

def help():
    print("example packet:")
    getSamplePacketString()