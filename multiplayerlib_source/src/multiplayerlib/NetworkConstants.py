# this file is part of MultiplayerLib, which is under an MIT license.
# see LICENSE file at root of this repository for details.
from typing import TypeAlias

JSONValue: TypeAlias = (
    bool
    | int
    | float
    | str
    | list["JSONValue"]
    | dict[str, "JSONValue"]
)

MPL_DEFAULT_BUFFER_SIZE = 1024
MPL_DEFAULT_PORT = 5000

MPL_DEFAULT_KEY = "encryptionKeyForFernetEncryption"
MPL_DEFAULT_SALT = 2815
MPL_DEFAULT_PEER_TIMEOUT = 5
MPL_DEFAULT_LOG_FILENAME = "MultiplayerLib_Logs"