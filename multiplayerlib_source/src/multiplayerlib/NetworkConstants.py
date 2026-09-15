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

BUFFER_SIZE = 1024
DEFAULT_PORT = 5000

DEFAULT_KEY = "encryptionKeyForFernetEncryption"
DEFAULT_SALT = 2815
PEER_TIMEOUT = 5