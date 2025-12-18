# MultiplayerLib — MIT License
# Copyright (c) 2025 griffingreat1
#
# This file is part of MultiplayerLib.
# You may use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of this file under the terms of the MIT License.
# See the LICENSE file in the repository root for full license text.

"""
:MultiplayerLib:\n
Multiplayerlib is a library designed to allow for easy creation of multiplayer games with any game
module. It is currently limited to only 2 player games where one player is the host and one player
connects, although there are plans for adding support for more than just 1v1 games.
"""
from GameUtils.MultiplayerLib.NetworkLib import *
from GameUtils.MultiplayerLib.NetworkConstants import *

def help():
    print("example packet:")
    getSamplePacketString()